from typing import cast

from aio_pika import ExchangeType
from pamqp.common import FieldTable
from pydantic import AmqpDsn, BaseModel, RedisDsn
from taskiq.middlewares.opentelemetry_middleware import OpenTelemetryMiddleware
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue
from taskiq_redis import RedisAsyncResultBackend

# taskiq-aio-pika needs exactly one task queue on the client side too: it
# takes the routing key from it, and without one it declares a catch-all
# "taskiq" queue. A client's queue is bound with a header no message ever
# carries, so the HEADERS exchange never routes anything into it, and the
# client no longer depends on a worker having declared its queue first.
# The key must not start with "x-": a headers exchange ignores such keys
# when matching, and {"x-match": "all"} alone matches every message.
_CLIENT_BIND_ARGUMENTS: FieldTable = {"x-match": "all", "shiro-client": "never"}


class BrokerConfigForClient(BaseModel):
    broker_url: AmqpDsn
    result_backend_url: RedisDsn
    exchange_name: str
    # Results are read once, right after the task. Unread ones (heartbeats)
    # and WireGuard configs must not stay in Redis forever.
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

    # The middleware is a no-op until set_up_otel() installs providers, so
    # it is safe to attach it whether or not telemetry is configured.
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
