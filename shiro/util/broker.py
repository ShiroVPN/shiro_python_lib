from typing import cast

from aio_pika import ExchangeType
from pamqp.common import FieldTable
from pydantic import AmqpDsn, BaseModel, RedisDsn
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue
from taskiq_redis import RedisAsyncResultBackend


class BrokerConfigForClient(BaseModel):
    broker_url: AmqpDsn
    result_backend_url: RedisDsn
    exchange_name: str


class BrokerConfigForWorker(BrokerConfigForClient):
    queue_name: str
    queue_bind_arguments: dict[str, str]


def create_broker(
    config: BrokerConfigForClient | BrokerConfigForWorker,
) -> AioPikaBroker:
    exchange = Exchange(name=config.exchange_name, type=ExchangeType.HEADERS)
    task_queues = None
    if isinstance(config, BrokerConfigForWorker):
        task_queues = [
            Queue(
                name=config.queue_name,
                bind_arguments=cast(
                    FieldTable, {"x-match": "all"} | config.queue_bind_arguments
                ),
            )
        ]
    broker = AioPikaBroker(
        url=str(config.broker_url),
        exchange=exchange,
        task_queues=task_queues,
    ).with_result_backend(
        RedisAsyncResultBackend(str(config.result_backend_url))
    )
    return broker
