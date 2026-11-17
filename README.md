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
  starts fine before any worker has declared its queue. taskiq-aio-pika needs a queue on the client
  side — without one it declares a catch-all `taskiq` queue and takes the routing key from it — and no
  bind key may start with `x-`, which a headers exchange ignores when matching.
- Task results live in Redis for `result_ex_time_s` (default 3600 s): they are read once, right after
  the task, and an unread result carries a WireGuard config with a private key.

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

# Usage examples

- [client](examples/example_usage_for_client.py) — a process that only kicks tasks.
- [worker](examples/example_usage_for_worker.py) — a process that consumes a queue and implements tasks with `define_task`.

A tasks module may only be imported after a broker exists: call `define_*_broker_as_client` or
`define_*_broker_as_worker` first, start the broker, and only then import `.tasks` and kick.
