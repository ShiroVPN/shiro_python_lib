__all__ = [
    "PeerhubBrokerConfigForClient",
    "PeerhubBrokerConfigForWorker",
    "get_peerhub_broker_as_client",
    "get_peerhub_broker_as_worker",
    "route_task_kicker_to_peerhub",
]

from collections.abc import Coroutine
from typing import ParamSpec, TypeVar
from uuid import UUID

from pydantic import model_validator
from taskiq.kicker import AsyncKicker
from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b

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


def get_peerhub_broker_as_client(
    config: PeerhubBrokerConfigForClient,
) -> AioPikaBroker:
    return b.create_broker(config)


def get_peerhub_broker_as_worker(
    config: PeerhubBrokerConfigForWorker,
) -> AioPikaBroker:
    return b.create_broker(config)


C = TypeVar("C", bound=Coroutine[object, object, object])
P = ParamSpec("P")


def route_task_kicker_to_peerhub(
    task: AsyncKicker[P, C],
    peerhub_id: UUID,
) -> AsyncKicker[P, C]:
    return task.with_labels(peerhub_id=str(peerhub_id))
