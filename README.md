# Shiro python module

This module defines TaskIQ tasks for workers `peerhub` and `main_api`, and the notifications a service sends to the Telegram bot. For more information see README files:

- [main_api](shiro/main_api/README.md)
- [peerhub](shiro/peerhub/README.md)
- [telegram_bot](shiro/telegram_bot/README.md)

It also has useful functions for defining brokers and tasks, and the shared pydantic types in `shiro.util.types` — `TelegramID`, `TelegramUsername` and `Money`.

# Brokers and queues

- `main_api`: HEADERS exchange `main_api_exchange`, worker queue `main_api_queue`.
- `peerhub`: HEADERS exchange `peerhub_exchange`, **one queue per peerhub** — `peerhub_queue.<PEERHUB_ID>`,
  bound with `peerhub_id=<PEERHUB_ID>`; clients route with `route_task_to_peerhub`.
- `telegram_bot`: TOPIC exchange `telegram_bot_exchange`, queue `telegram_bot_queue` — the bot consumes it
  in its own process, every service that notifies the bot only publishes. Messages are fire-and-forget:
  the broker has no result backend.
- Clients get their own queue `<exchange>.client`, bound with a header no message carries, so a client
  starts fine before any worker has declared its queue.
- Task results live in Redis for `result_ex_time_s` (default 3600 s).

Telemetry is optional: call `set_up_otel(...)` to export traces, metrics and logs over OTLP; without
it the tracer and meter are no-ops. `observe()` records call/return events and
durations but **not** argument or return values unless `log_values=True` — task results include
WireGuard configs with private keys.

## Upgrading from 0.5.x

Broker entry points are named after the service they belong to and split by the role the process plays.
The configurations keep their shape; what changes is the import and which builder the process calls.

| 0.5.x | 0.6.0 |
| --- | --- |
| `shiro.main_api.broker.BrokerConfigForClient` / `define_broker` | `MainApiBrokerConfigForClient` / `define_main_api_broker_as_client` |
| `shiro.main_api.broker.BrokerConfigForWorker` / `define_broker` | `MainApiBrokerConfigForWorker` / `define_main_api_broker_as_worker` |
| `shiro.peerhub.broker.BrokerConfigForClient` / `define_broker` | `PeerhubBrokerConfigForClient` / `define_peerhub_broker_as_client` |
| `shiro.peerhub.broker.BrokerConfigForWorker` / `define_broker` | `PeerhubBrokerConfigForWorker` / `define_peerhub_broker_as_worker` |
| `shiro.telegram_bot.broker.define_broker` — a service that notifies the bot | `define_telegram_bot_broker_as_client` |
| `shiro.telegram_bot.broker.define_broker` — the bot itself | `define_telegram_bot_broker_as_worker` |

`_as_client` declares the exchange and its own `<exchange>.client` queue, which nothing routes into: the
process only kicks tasks and never consumes. `_as_worker` declares the queue the process consumes. Both go
through `shiro.util.broker.create_broker`, which picks the queue from the config, so the name says which
role the process plays — and which config type it may pass.

`TelegramBotBrokerConfig`, `route_task_to_peerhub`, `declare_task` and `define_task` keep their names, and
`shiro.util.broker` keeps the generic `BrokerConfigForClient` / `BrokerConfigForWorker` and `create_broker`.
Exchanges, queue names, bindings and routing are untouched, so 0.5.x and 0.6.0 workers talk to each other
while a fleet is being upgraded.

## Upgrading from 0.3.x

`peerhub.get_config` now answers `WgConfig | XuiConfig` instead of a plain
string: a wg-easy peerhub returns `{config}` (the `.conf` body), a 3x-ui one
`{sub_url}` (the subscription URL). `main_api.get_connection_config` passes the
same union through, so a reader that used to expect a string must validate the
shape it got. Taskiq sends the result as JSON primitives, so validate the dict,
not a shared class.

## Upgrading from 0.1.x

Peerhub workers move from the shared `peerhub_queue` to `peerhub_queue.<PEERHUB_ID>`. On a RabbitMQ that
ran the old chain, in this order:

1. Upgrade `main_api_worker` (and every other peerhub *client*) to 0.2.0 first. Old clients require the
   old `peerhub_queue` to exist at startup; new ones do not.
2. Per hub: stop the old worker, then start the new one. Never run both for one hub: a headers exchange
   delivers each message to every matching queue, so the task would execute twice.
3. Delete the old queue, otherwise it keeps a copy of every peerhub message with nobody consuming:
   `rabbitmqctl delete_queue peerhub_queue`. Check for other stale bindings with
   `rabbitmqctl list_bindings source_name destination_name arguments | grep peerhub_exchange`
   — every destination must be a running hub's `peerhub_queue.<PEERHUB_ID>` or `peerhub_exchange.client`.
4. Results written by 0.1.x workers have no TTL. Once every worker is on 0.2.0, clear them:
   `redis-cli FLUSHDB` on the result database (nothing else lives there).

API changes: `queue_name` is no longer a client config field; `OTEL_COLLECTOR_ENDPOINT` is optional and
`OTEL_SERVICE_NAME` defaults to `shiro`; the `BROKER_RESULT_BACKEND_URL` error text names the variable;
`from shiro.util import define_task` (removed in 0.1.0) is `shiro.util.tasks.define_task`.

# Usage example on client

```python
from uuid import uuid4

from pydantic import AmqpDsn, HttpUrl, RedisDsn

from shiro.peerhub.broker import (
    PeerhubBrokerConfigForClient,
    define_peerhub_broker,
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

# Optional: without it the tracer and meter are no-ops.
if env_config.otel_collector_endpoint is not None:
    set_up_otel(
        OtelConfig(
            otel_collector_endpoint=env_config.otel_collector_endpoint,
            otel_service_name=env_config.otel_service_name,
        )
    )

broker = define_peerhub_broker(
    PeerhubBrokerConfigForClient(
        broker_url=env_config.broker_url,
        result_backend_url=env_config.broker_result_backend_url,
    )
)

_ = broker.startup()

# import tasks after define_peerhub_broker was called
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
    MainApiBrokerConfigForWorker,
    define_main_api_broker,
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

broker = define_main_api_broker(
    MainApiBrokerConfigForWorker(
        broker_url=env_config.broker_url,
        result_backend_url=env_config.broker_result_backend_url,
    )
)

# import tasks after `define_main_api_broker` was called


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
