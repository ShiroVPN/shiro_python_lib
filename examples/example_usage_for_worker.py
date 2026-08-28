from pydantic import AmqpDsn, RedisDsn

from shiro.main_api.broker import (
    BrokerConfigForWorker,
    define_broker,
)

broker = define_broker(
    BrokerConfigForWorker(
        broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
        result_backend_url=RedisDsn("redis://localhost:6379/0"),
        exchange_name="exchange_name",
        queue_name="queue_name",
    )
)

# import workers after define_broker was called

from shiro.main_api.models import Client, ClientGet
from shiro.main_api.tasks import get_client
from shiro.util import define_task

from .dependencies import db_dependency


@define_task(get_client)
async def get_client_impl(client_data: ClientGet, db: db_dependency) -> Client:
    return await db.get_client(client_data.telegram_id)  # pyright: ignore


if __name__ == "__main__":
    print("Success!")
