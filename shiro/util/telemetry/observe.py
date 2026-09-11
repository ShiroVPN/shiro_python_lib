import inspect
import time
from collections.abc import Awaitable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import (
    Annotated,
    Callable,
    ClassVar,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

from heliclockter import datetime_utc
from opentelemetry.trace import Status, StatusCode, format_trace_id
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    SerializerFunctionWrapHandler,
    WrapSerializer,
)
from pydantic_core import PydanticSerializationError

from .otel_setup import get_duration_histogram, get_logger, get_tracer

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


def serialize_exception(e: Exception) -> str:
    return f"{type(e).__name__}: {str(e)}"


def serialize_object(
    value: object, handler: SerializerFunctionWrapHandler
) -> str | object:
    try:
        return cast(object, handler(value))
    except PydanticSerializationError:
        return str(value)


SerializableException = Annotated[
    Exception,
    PlainSerializer(serialize_exception),
]

SerializableObject = Annotated[
    object,
    WrapSerializer(serialize_object),
]


class BasicLog(BaseModel):
    log_type: str
    call_id: str
    func_name: str
    trace_id: str
    timestamp: datetime_utc = Field(default_factory=datetime_utc.now)


class LogFunctionCall(BasicLog):
    call_args: tuple[SerializableObject, ...]
    call_kwargs: dict[str, SerializableObject]
    log_type: str = "function_call"


class ReturnValue(BaseModel):
    value: SerializableObject | None = None


class LogFunctionReturn(BasicLog):
    return_value: ReturnValue
    is_error: bool
    error: SerializableException | None
    time_elapsed_ms: float
    time_func_execution_ms: float
    log_type: str = "function_return"

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )


def time_ms(start_time: float) -> float:
    return (time.perf_counter() - start_time) * 1000


@contextmanager
def _observe_call(
    call_id: str,
    func: Callable[..., object],
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> Generator[ReturnValue]:
    time_wrapper_start = time.perf_counter()
    tracer = get_tracer(__name__)

    with tracer.start_as_current_span(call_id) as span:
        trace_id = format_trace_id(span.get_span_context().trace_id)
        logger = get_logger(__name__)
        args_str = ", ".join(
            [str(v) for v in args] + [f"{k}={v}" for k, v in kwargs.items()]
        )
        logger.info(
            f"function_call: {call_id}({args_str})",
            extra=LogFunctionCall(
                call_id=call_id,
                func_name=func.__name__,
                trace_id=trace_id,
                call_args=args,
                call_kwargs=kwargs,
            ).model_dump(mode="json"),
        )

        time_func_call_start = time.perf_counter()

        return_value = ReturnValue()

        try:
            yield return_value
            status = Status(StatusCode.OK)
            error = None
        except Exception as e:
            status = Status(StatusCode.ERROR, str(e))
            error = e

        result = return_value.value

        time_func_execution_ms = time_ms(time_func_call_start)
        span.set_status(status)

        get_duration_histogram().record(
            time_func_execution_ms, {"call_id": call_id}
        )

        logger.info(
            f"function_return: {call_id}({args_str}) -> {result if error is None else error}",
            extra=LogFunctionReturn(
                call_id=call_id,
                func_name=func.__name__,
                trace_id=trace_id,
                return_value=return_value,
                is_error=error is not None,
                error=error if error else None,
                time_elapsed_ms=time_ms(time_wrapper_start),
                time_func_execution_ms=time_func_execution_ms,
            ).model_dump(mode="json"),
        )

        if error is not None:
            raise error


def observe(call_id: str) -> Callable[[Callable[P, R]], Callable[P, R]]:

    @overload
    def inner(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...

    @overload
    def inner(func: Callable[P, T]) -> Callable[P, T]: ...

    def inner(
        func: Callable[P, T] | Callable[P, Awaitable[T]],
    ) -> Callable[P, T] | Callable[P, Awaitable[T]]:
        if inspect.iscoroutinefunction(func):
            func = cast(Callable[P, Awaitable[T]], func)

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                with _observe_call(call_id, func, args, kwargs) as rv:
                    value = await func(*args, **kwargs)
                    rv.value = value
                    return value

            return async_wrapper

        func = cast(Callable[P, T], func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with _observe_call(call_id, func, args, kwargs) as rv:
                value = func(*args, **kwargs)
                rv.value = value
                return value

        return wrapper

    return inner


def observe_decorator_with_prefix(
    prefix: str = "", sep: str = "."
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        call_id = func.__name__
        if prefix:
            call_id = f"{prefix}{sep}{call_id}"
        return observe(call_id)(func)

    return decorator
