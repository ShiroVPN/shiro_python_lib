__all__ = ["define_task", "get_declare_task_wrapper"]

from types import CoroutineType
from typing import Callable, ParamSpec, TypeVar

from taskiq import AsyncTaskiqDecoratedTask
from taskiq_aio_pika import AioPikaBroker

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
        new_task = task.broker.register_task(func, task.task_name)
        return new_task

    return wrapper
