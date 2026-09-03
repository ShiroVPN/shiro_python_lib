__all__ = [
    "BrokerConfigForClient",
    "BrokerConfigForWorker",
    "define_broker",
    "route_task_to_peerhub",
]

from collections.abc import Coroutine
from typing import ParamSpec, TypeVar
from uuid import UUID

from pydantic import model_validator
from taskiq import AsyncTaskiqDecoratedTask
from taskiq.kicker import AsyncKicker
from taskiq_aio_pika import AioPikaBroker

import shiro.util as b

BROKER_PEERHUB_QUEUE_NAME = "peerhub_queue"
BROKER_PEERHUB_EXCHANGE_NAME = "peerhub_exchange"


class BrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_PEERHUB_EXCHANGE_NAME
    queue_name: str = BROKER_PEERHUB_QUEUE_NAME


class BrokerConfigForWorker(b.BrokerConfigForWorker, BrokerConfigForClient):
    peerhub_id: UUID
    queue_bind_arguments: dict[str, str] = {}

    @model_validator(mode="after")
    def set_queue_bind_arguments(self) -> "BrokerConfigForWorker":
        self.queue_bind_arguments = {"peerhub_id": str(self.peerhub_id)}
        return self


_broker: AioPikaBroker | None = None


def define_broker(
    config: BrokerConfigForClient | BrokerConfigForWorker,
) -> AioPikaBroker:
    """
    Function: `shiro.peerhub.broker.define_broker`.
    Call this function before importing `shiro.peerhub.workers`.
    """
    global _broker
    value = b.create_broker(config)
    _broker = value
    return _broker


T = TypeVar("T")


def declare_task(task_name: str):
    """
    - Used in `shiro.peerhub.workers` to declare tasks.
    (declared functions don't have bodies).
    - Do not use this function to define tasks.
    (defined functions have bodies).
    - To define tasks use `shiro.util.define_task`.

    ```python
    @declare_task(task_name="name")
    async def foo(...) -> Bar: ...
    ```
    """
    global _broker
    wrapper = b.get_declare_task_wrapper(_broker, task_name)
    return wrapper


C = TypeVar("C", bound=Coroutine[object, object, object])
P = ParamSpec("P")


def route_task_to_peerhub(
    task: AsyncTaskiqDecoratedTask[P, C],
    peerhub_id: UUID,
) -> AsyncKicker[P, C]:
    """
    Use this function to route peerhub tasks to peerhub.
    ```python
    from shiro.peerhub.broker import (
        BrokerConfigForClient,
        define_broker,
        route_task_to_peerhub,
    )
    broker = define_broker(BrokerConfigForClient(...))
    broker.startup()
    from shiro.peerhub.workers import get_peer
    routed_task = route_task_to_peerhub(get_peer, peerhub_id)
    routed_task.kiq(peer_id)
    ```
    """
    return task.kicker().with_labels(peerhub_id=str(peerhub_id))
