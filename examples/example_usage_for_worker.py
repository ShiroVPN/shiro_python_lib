from pydantic import AmqpDsn, HttpUrl, RedisDsn

from shiro.main_api.broker import (
    BrokerConfigForWorker,
    define_broker,
)
from shiro.util.telemetry import OtelConfig, set_up_otel

set_up_otel(
    OtelConfig(
        otel_collector_endpoint=HttpUrl("http://otel-collector:4317"),
        otel_service_name="broker_client",
    )
)

# `set_up_otel` before `define_broker`.

broker = define_broker(
    BrokerConfigForWorker(
        broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
        result_backend_url=RedisDsn("redis://localhost:6379/0"),
    )
)

# import tasks after `define_broker` was called

from typing import Annotated

from taskiq import TaskiqDepends

from shiro.main_api.models import Client, ClientGet
from shiro.main_api.tasks import get_client
from shiro.util import define_task
from shiro.util.telemetry import observe_decorator_with_prefix

db_observer = observe_decorator_with_prefix("worker.Database")


class Database:
    @db_observer
    async def get_client(self, telegram_id: int) -> Client:
        print(telegram_id)
        raise NotImplemented()


def get_database():
    yield Database()


db_dependency = Annotated[Database, TaskiqDepends(get_database)]


@define_task(get_client)
async def get_client_impl(client_data: ClientGet, db: db_dependency) -> Client:
    return await db.get_client(client_data.telegram_id)


if __name__ == "__main__":
    print("Success!")
