__all__ = [
    "PeerhubBrokerConfigForClient",
    "PeerhubBrokerConfigForWorker",
    "define_peerhub_broker_as_client",
    "define_peerhub_broker_as_worker",
    "route_task_to_peerhub",
]

from collections.abc import Coroutine
from typing import ParamSpec, TypeVar
from uuid import UUID

from pydantic import model_validator
from taskiq import AsyncTaskiqDecoratedTask
from taskiq.kicker import AsyncKicker
from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b
import shiro.util.tasks as t

BROKER_PEERHUB_QUEUE_NAME = "peerhub_queue"
BROKER_PEERHUB_EXCHANGE_NAME = "peerhub_exchange"


class PeerhubBrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_PEERHUB_EXCHANGE_NAME


class PeerhubBrokerConfigForWorker(
    PeerhubBrokerConfigForClient, b.BrokerConfigForWorker
):
    peerhub_id: UUID
    # One queue per peerhub. A shared queue with per-hub bindings would let
    # any worker consume tasks addressed to another hub.
    queue_name: str = ""
    queue_bind_arguments: dict[str, str] = {}

    @model_validator(mode="after")
    def set_queue_for_peerhub(self) -> "PeerhubBrokerConfigForWorker":
        if not self.queue_name:
            self.queue_name = f"{BROKER_PEERHUB_QUEUE_NAME}.{self.peerhub_id}"
        self.queue_bind_arguments = {"peerhub_id": str(self.peerhub_id)}
        return self


_broker: AioPikaBroker | None = None


def define_peerhub_broker_as_client(
    config: PeerhubBrokerConfigForClient,
) -> AioPikaBroker:
    """
    Function: `shiro.peerhub.broker.define_peerhub_broker_as_client`.
    Call this function before importing `shiro.peerhub.tasks`.
    Use it in a service that only kicks `peerhub` tasks.
    """
    global _broker
    _broker = b.create_broker(config)
    return _broker


def define_peerhub_broker_as_worker(
    config: PeerhubBrokerConfigForWorker,
) -> AioPikaBroker:
    """
    Function: `shiro.peerhub.broker.define_peerhub_broker_as_worker`.
    Call this function before importing `shiro.peerhub.tasks`.
    Use it in the process that consumes the queue of its own `peerhub_id`.
    """
    global _broker
    _broker = b.create_broker(config)
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
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
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
        PeerhubBrokerConfigForClient,
        define_peerhub_broker_as_client,
        route_task_to_peerhub,
    )
    broker = define_peerhub_broker_as_client(PeerhubBrokerConfigForClient(...))
    broker.startup()
    from shiro.peerhub.workers import get_peer
    routed_task = route_task_to_peerhub(get_peer, peerhub_id)
    routed_task.kiq(peer_id)
    ```
    """
    return task.kicker().with_labels(peerhub_id=str(peerhub_id))
