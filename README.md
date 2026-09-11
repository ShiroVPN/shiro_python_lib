# Shiro python module

This module defines TaskIQ tasks for workers `peerhub` and `main_api`. For more information see README files:

- [main_api](shiro/main_api/README.md)
- [peerhub](shiro/peerhub/README.md)

It also has useful functions for defining brokers and tasks.

# Usage example on client

```python
from uuid import uuid4

from pydantic import AmqpDsn, HttpUrl, RedisDsn

from shiro.peerhub.broker import (
    BrokerConfigForClient,
    define_broker,
    route_task_to_peerhub,
)
from shiro.util.env import EnvConfig
from shiro.util.tasks import TaskRunner
from shiro.util.telemetry import OtelConfig, observe, set_up_otel


class MyEnvConfig(EnvConfig):
    worker_wait_result_timeout: float = 0.1
    worker_wait_result_check_interval: float = 0.01


env_config = MyEnvConfig(
    broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
    broker_result_backend_url=RedisDsn("redis://localhost:6379/0"),
    otel_collector_endpoint=HttpUrl("http://otel-collector:4317"),
    otel_service_name="broker_client",
)

set_up_otel(
    OtelConfig(
        otel_collector_endpoint=env_config.otel_collector_endpoint,
        otel_service_name=env_config.otel_service_name,
    )
)

# `set_up_otel` before `define_broker`.

broker = define_broker(
    BrokerConfigForClient(
        broker_url=env_config.broker_url,
        result_backend_url=env_config.broker_result_backend_url,
    )
)

_ = broker.startup()

# import tasks after define_broker was called
# kiq tasks after broker startup

from shiro.peerhub.models import Peer
from shiro.peerhub.tasks import get_peer

task_sender = TaskRunner(
    wait_result_timeout=env_config.worker_wait_result_timeout,
    wait_result_check_interval=env_config.worker_wait_result_check_interval,
)


@observe("client.main")
async def main():
    peerhub_id = uuid4()
    peer_id = uuid4()

    routed_get_peer = route_task_to_peerhub(get_peer, peerhub_id)

    runner = task_sender.runner(routed_get_peer)
    peer: Peer = await runner.send(peer_id)

    print(peer)


if __name__ == "__main__":
    print("Success!")
```

# Usage example on worker

```python
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

set_up_otel(
    OtelConfig(
        otel_collector_endpoint=env_config.otel_collector_endpoint,
        otel_service_name=env_config.otel_service_name,
    )
)

# `set_up_otel` before `define_broker`.

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
```
