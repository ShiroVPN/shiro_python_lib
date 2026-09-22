from typing import Annotated

from pydantic import AmqpDsn, HttpUrl, RedisDsn
from taskiq import TaskiqDepends

from shiro.main_api.broker import (
    BrokerConfigForWorker,
    define_broker,
)
from shiro.util.env import EnvConfig
from shiro.util.telemetry import (
    OtelConfig,
    observe_decorator_with_prefix,
    set_up_otel,
)

env_config = EnvConfig(
    broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
    broker_result_backend_url=RedisDsn("redis://localhost:6379/0"),
    otel_collector_endpoint=HttpUrl("http://otel-collector:4317"),
    otel_service_name="broker_client",
)

# Optional: without it the tracer and meter are no-ops.
if env_config.otel_collector_endpoint is not None:
    set_up_otel(
        OtelConfig(
            otel_collector_endpoint=env_config.otel_collector_endpoint,
            otel_service_name=env_config.otel_service_name,
        )
    )

broker = define_broker(
    BrokerConfigForWorker(
        broker_url=env_config.broker_url,
        result_backend_url=env_config.broker_result_backend_url,
    )
)

# import tasks after `define_broker` was called


from shiro.main_api.models import Client, ClientGet
from shiro.main_api.tasks import get_client
from shiro.util.tasks import define_task

db_observer = observe_decorator_with_prefix("worker.Database")


class Database:
    @db_observer
    async def get_client(self, telegram_id: int) -> Client:
        raise NotImplementedError(telegram_id)


def get_database():
    yield Database()


db_dependency = Annotated[Database, TaskiqDepends(get_database)]


@define_task(get_client)
async def get_client_impl(client_data: ClientGet, db: db_dependency) -> Client:
    return await db.get_client(client_data.telegram_id)


if __name__ == "__main__":
    print("Success!")
