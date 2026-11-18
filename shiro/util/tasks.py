from dataclasses import dataclass
from types import CoroutineType
from typing import Callable, ParamSpec, TypeVar

from taskiq import AsyncBroker, AsyncTaskiqDecoratedTask
from taskiq.kicker import AsyncKicker

from shiro.util.telemetry import observe

T = TypeVar("T")
P = ParamSpec("P")

type TaskFunc[**P, T] = Callable[P, CoroutineType[object, object, T]]


@dataclass(kw_only=True)
class TaskiqTask[**P, T]:
    name: str
    func: TaskFunc[P, T]


type TaskDecorator[**P, T] = Callable[[TaskFunc[P, T]], TaskiqTask[P, T]]
type TaskImplDecorator[**P, T] = Callable[
    [TaskFunc[P, T]],
    AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]],
]


def get_declare_task_wrapper(
    prefix: str,
) -> Callable[[str], TaskDecorator[P, T]]:
    def inner(task_name: str) -> TaskDecorator[P, T]:
        def wrapper(func: TaskFunc[P, T]) -> TaskiqTask[P, T]:
            return TaskiqTask(name=f"{prefix}.{task_name}", func=func)

        return wrapper

    return inner


def get_define_task_wrapper(
    broker: AsyncBroker,
) -> Callable[[TaskiqTask[P, T]], TaskImplDecorator[P, T]]:
    def inner(task: TaskiqTask[P, T]) -> TaskImplDecorator[P, T]:
        def wrapper(
            func: TaskFunc[P, T],
        ) -> AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]]:
            return broker.register_task(observe(task.name)(func), task.name)

        return wrapper

    return inner


def get_task_kicker(
    broker: AsyncBroker,
    task: TaskiqTask[P, T],
) -> AsyncKicker[P, CoroutineType[object, object, T]]:
    return AsyncKicker(
        task_name=task.name,
        broker=broker,
        labels={},
    )


@dataclass(kw_only=True)
class TaskSender[**P, T]:
    task: (
        AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]]
        | AsyncKicker[P, CoroutineType[object, object, T]]
    )
    wait_result_check_interval: float
    wait_result_timeout: float

    async def send(
        self,
        *task_args: P.args,
        **task_kwargs: P.kwargs,
    ) -> T:
        kiqed_task = await self.task.kiq(*task_args, **task_kwargs)
        observable_wait_result = observe(f"wait_result/{self.task.task_name}")(
            kiqed_task.wait_result
        )
        result = await observable_wait_result(
            timeout=self.wait_result_timeout,
            check_interval=self.wait_result_check_interval,
        )
        if result.error is not None:
            raise result.error
        return result.return_value


@dataclass(kw_only=True)
class TaskRunner:
    wait_result_check_interval: float
    wait_result_timeout: float

    def runner(
        self,
        task: (
            AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]]
            | AsyncKicker[P, CoroutineType[object, object, T]]
        ),
    ):
        return TaskSender(
            task=task,
            wait_result_check_interval=self.wait_result_check_interval,
            wait_result_timeout=self.wait_result_timeout,
        )
