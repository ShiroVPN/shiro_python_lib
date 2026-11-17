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
    global _broker
    _broker = b.create_broker(config)
    return _broker


def define_peerhub_broker_as_worker(
    config: PeerhubBrokerConfigForWorker,
) -> AioPikaBroker:
    global _broker
    _broker = b.create_broker(config)
    return _broker


def declare_task(task_name: str):
    global _broker
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper


C = TypeVar("C", bound=Coroutine[object, object, object])
P = ParamSpec("P")


def route_task_to_peerhub(
    task: AsyncTaskiqDecoratedTask[P, C],
    peerhub_id: UUID,
) -> AsyncKicker[P, C]:
    return task.kicker().with_labels(peerhub_id=str(peerhub_id))
