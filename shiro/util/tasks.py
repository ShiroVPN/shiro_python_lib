__all__ = ["define_task", "get_declare_task_wrapper", "send_task"]

from types import CoroutineType
from typing import Callable, ParamSpec, TypeVar

from taskiq import AsyncTaskiqDecoratedTask
from taskiq_aio_pika import AioPikaBroker

from shiro.util.telemetry import observe

T = TypeVar("T")
P = ParamSpec("P")
PD = ParamSpec("PD")  # P with dependencies


def get_declare_task_wrapper(broker: AioPikaBroker | None, task_name: str):
    def wrapper(func: Callable[P, CoroutineType[object, object, T]]):
        if broker is None:
            raise RuntimeError(f"""[{task_name}]: \
                You can not declare tasks before setting up broker. \
                Use 'define_broker'.""")
        new_task = broker.register_task(func, task_name)
        return new_task

    return wrapper


def define_task(
    task: AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]],
):
    """
    Function: `shiro.util[.tasks].define_task`
    - Use this function to define tasks on TaskIQ worker.
    (defined functions have bodies).

    ```python
    from shiro.peerhub.broker import (
        BrokerConfigForWorker,
        define_broker,
    )
    broker = define_broker(BrokerConfigForWorker(...))

    from shiro.peerhub.workers import get_peer
    from shiro.peerhub.models import Peer
    from shiro.util import define_task

    @define_task(get_peer)
    async def get_peer_implementation(id: UUID, db: db_dependency) -> Peer:
        return db.get_peer(id)
    ```

    `taskiq worker your_peerhub_worker:broker`
    """

    def wrapper(func: Callable[PD, CoroutineType[object, object, T]]):
        func = observe(task.task_name)(func)
        new_task = task.broker.register_task(func, task.task_name)
        return new_task

    return wrapper


def send_task(
    task: AsyncTaskiqDecoratedTask[P, CoroutineType[object, object, T]],
    *,
    wait_result_check_interval: float = 0.01,
    wait_result_timeout: float = 1,
):
    """
    - kiq task and wait for result.
    - OpenTelemetryMiddleware adds trace for `kiq`.
    - Adds trace for `wait_result`."""

    async def inner(
        *task_args: P.args,
        **task_kwargs: P.kwargs,
    ) -> T:
        kiqed_task = await task.kiq(*task_args, **task_kwargs)
        observable_wait_result = observe(f"wait_result/{task.task_name}")(
            kiqed_task.wait_result
        )
        result = await observable_wait_result(
            timeout=wait_result_timeout,
            check_interval=wait_result_check_interval,
        )
        if result.error is not None:
            raise result.error
        return result.return_value

    return inner
