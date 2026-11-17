from typing import cast

from aio_pika import ExchangeType
from pamqp.common import FieldTable
from pydantic import AmqpDsn, BaseModel, RedisDsn
from taskiq.middlewares.opentelemetry_middleware import OpenTelemetryMiddleware
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue
from taskiq_redis import RedisAsyncResultBackend

_CLIENT_BIND_ARGUMENTS: FieldTable = {"x-match": "all", "shiro-client": "never"}


class BrokerConfigForClient(BaseModel):
    broker_url: AmqpDsn
    result_backend_url: RedisDsn
    exchange_name: str
    result_ex_time_s: int = 3600


class BrokerConfigForWorker(BrokerConfigForClient):
    queue_name: str
    queue_bind_arguments: dict[str, str]


def create_broker(
    config: BrokerConfigForClient | BrokerConfigForWorker,
) -> AioPikaBroker:
    if isinstance(config, BrokerConfigForWorker):
        queue = Queue(
            name=config.queue_name,
            bind_arguments=cast(
                FieldTable, {"x-match": "all"} | config.queue_bind_arguments
            ),
        )
    else:
        queue = Queue(
            name=f"{config.exchange_name}.client",
            bind_arguments=_CLIENT_BIND_ARGUMENTS,
        )

    return (
        AioPikaBroker(
            url=str(config.broker_url),
            exchange=Exchange(
                name=config.exchange_name, type=ExchangeType.HEADERS
            ),
        )
        .with_queue(queue)
        .with_result_backend(
            RedisAsyncResultBackend(
                str(config.result_backend_url),
                result_ex_time=config.result_ex_time_s,
            )
        )
        .with_middlewares(OpenTelemetryMiddleware())
    )
