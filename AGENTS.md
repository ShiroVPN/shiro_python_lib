# shiro_python_lib

The contract library of the ShiroVPN stack. Every module here declares one
service's taskiq task surface and the pydantic models that cross the queue;
the services implement those tasks and import the models — they never declare
their own. Consumers: `main_api_worker`, `BotV2`, `peerhub_wireguard_worker`,
`peerhub_3xui_worker`, `peerhub_heartbeat`, `shiro_tests`.

The main idea: this repository *is* the contract. A name, a field or a queue
here is a wire fact other repositories pin by tag, so nothing in it is private
convenience — it is published, versioned and slower to change than the code
that consumes it.

Per-field tables and per-task semantics live in the module READMEs
(`shiro/main_api/README.md`, `shiro/peerhub/README.md`,
`shiro/telegram_bot/README.md`) and in the root `README.md`. This file holds the
rules a change has to satisfy.

# Writing code, code requirements

I will go through all the code that you write. I will reject it if it's bad.

- Make it readable
- Try not to write comments. Only write in comments what code can not say.
- Use best practices
- Look at my code, this will increase your chances of passing.
- Don't use global variables or constants. Try to put them in config or env settings (see pydantic).

## Comments and docstrings

- No `#` comments in Python. Tool directives (`# pyright:
  reportUnusedParameter=false`, `# noqa`) stay — they are instructions to a
  tool, not prose.
- No docstrings either. A docstring counts as a comment here, including the
  model and helper ones.
- A fact the code cannot express goes into this file or into a module README,
  never back into a comment. When a comment is deleted, its fact moves there in
  the same change.
- `examples/*.py` keeps its walkthrough comments: those files are the usage
  documentation, not library code.

## Contract ownership

- A task, a request model, a result model or an error class is declared here
  first, then the version is bumped and the consumers follow. They do not
  declare a local stand-in, a `TypedDict` shaped like a model, or a subclass
  that shadows a contract name.
- A task name is an explicit string, `<service>.<name>` (`main_api.get_client`,
  `peerhub.get_usage`, `telegram_bot.notify_topup`). Never derive it from the
  module path: the colon form taskiq builds is a rename hazard, and these names
  are matched across repositories.
- Exchange names, queue names, bind arguments and task names are the wire
  identity: another repository matches `main_api_queue` by hand, so they stay
  module constants. They are not tunables — a value an operator may change is a
  config field instead.
- A declared task may have no implementation yet (`main_api.notify_client` is
  declared and the worker does not implement it). Declaring is not a promise;
  the module README says which ones are live.

## Models

- Every model is a pydantic `BaseModel`. No `TypedDict`, no dataclass for a
  shape that crosses the queue.
- Field names are the wire names (`telegram_id`, `sub_url`, `platega_id`). No
  alias generator, no snake_case mapping.
- A constraint is expressed in the type: `Field(ge=0)`, `Field(gt=0, le=31)`,
  `StringConstraints(pattern=...)`. A bare `str` or `int` means "anything" and
  is a decision, not a default.
- A constraint repeated across modules is one alias in `shiro/util/types.py`
  (`TelegramID`, `TelegramUsername`, `Money`) and every matching field uses it.
- A closed set of values is a `Literal` (`PaymentStatus`, `NotificationEvent`,
  `AnnounceGet.audience`). The branch for an unknown value does not exist on
  either side; the validator refuses it before a handler runs.
- One payload model per operation. A `Post` model is not reused as an update
  body with a different meaning.
- A model the code assembles itself is built with its keyword constructor.
  `model_validate` stays for data from outside: the wire, YAML, the
  environment.
- Task arguments and results cross the queue as JSON primitives: a `Decimal`
  arrives as a string, a `datetime` as ISO with an offset, a model leaves as a
  dict. A caller revalidates the dict it gets; `WgConfig | XuiConfig` is
  exactly that case.

## Errors

- A business error is a class with `status_code` and `error_code` as
  `ClassVar`s, named in snake_case (`client_not_found`,
  `balance_will_be_negative`). The `main_api` set lives in
  `shiro/main_api/exceptions.py` under `AppException` and includes
  `operation_in_progress` (482); `peerhub` has its two plain exceptions in
  `shiro/peerhub/exceptions.py`, which carry `error_code` but no `status_code`.
- Every `error_code` is a member of `shiro.util.errors.ErrorCode`, never a
  literal string. The member does not travel: taskiq rebuilds the class from
  `exc_module`, `exc_type` and `exc_args`, so a caller that holds an exception
  from the queue reads `error_code_of(error)` — the message first
  (`AppException` puts the code into `args`), the class name second
  (`peer_not_found`'s message is the human text).
- `error_code` is the wire name consumers match; `status_code` is the HTTP-ish
  number a consumer maps to its own response. Neither is renumbered casually.
- A task raises an error class. A model never raises one, and a helper does not
  invent a text where a class exists.

## Module layout

- `shiro/<service>/models.py` — the request and result models, `__all__` on
  top, nothing else.
- `shiro/<service>/tasks.py` — bodyless stubs decorated with
  `declare_task(task_name=...)`, `__all__` listing them, and the
  `# pyright: reportUnusedParameter=false` line that lets a stub take arguments
  it never reads.
- `shiro/<service>/broker.py` — the exchange and queue names, the
  `*BrokerConfigForClient` / `*BrokerConfigForWorker` pair, the
  `define_<service>_broker_as_client` / `_as_worker` builders and
  `declare_task`.
- `shiro/<service>/exceptions.py` — that service's error classes, where the
  service has them.
- `shiro/util/` — the shared broker factory (`broker.py`), the task helpers a
  worker uses (`tasks.py`: `define_task`, `TaskRunner`, `TaskSender`), the
  settings models (`env.py`), telemetry (`telemetry/`), the error codes
  (`errors.py`: `ErrorCode`, `error_code_of`) and the shared aliases
  (`types.py`).
- `shiro/<service>/README.md` — the human table of models, tasks and errors. A
  change to any of them updates that README in the same change.

## Brokers

- A new broker is built by `shiro/util/broker.create_broker`. A service module
  only names its exchange and queue; it does not open an `AioPikaBroker` of its
  own unless the traffic pattern is deliberately different, and then it says so
  in the README.
- The `define_*` name says which side of the queue the process is, and the
  config type it accepts says the same: `_as_client` takes the client config
  and builds a queue nothing routes into, `_as_worker` takes the worker config
  and consumes its queue.
- A tasks module is imported only after a `define_*` call: `declare_task` reads
  the module-level `_broker` and raises `RuntimeError` when there is none. A
  broker module never imports `.tasks` — the order belongs to the service.
- A field that identifies a hub is derived, not passed by hand:
  `PeerhubBrokerConfigForWorker.peerhub_id` produces `queue_name` and
  `queue_bind_arguments` in a `model_validator(mode="after")`.
- Two wire facts that look like style and are not: a headers exchange ignores
  any bind key starting with `x-`, so a matching key must never start with it;
  and a client queue is needed even though nothing routes into it, or
  taskiq-aio-pika declares a catch-all `taskiq` queue and takes the routing key
  from that.

## Settings

- A value that changes per deployment is an `EnvConfig` field, not a module
  constant. `BrokerEnvConfig` carries `broker_url` and
  `broker_result_backend_url`, `OtelEnvConfig` carries
  `otel_collector_endpoint` and `otel_service_name`, and a service inherits
  `EnvConfig` rather than a bare `BaseEnvConfig`.
- A required field is `required_field("var_name")`: it fails at start-up naming
  the variable instead of defaulting to something plausible.
- Telemetry is optional. `otel_collector_endpoint` unset means off; the
  `OpenTelemetryMiddleware` is attached unconditionally because it is a no-op
  until `set_up_otel` installs providers.
- `result_ex_time_s` (3600 by default) is a config field on the client config
  and is set by whoever runs the broker, not a constant.
- Related knobs stay together and a field names the state it measures and its
  unit, not `timeout` or `limit`.
- A fixed set of names is a `StrEnum` beside the setting that accepts it, so an
  unknown name fails the load instead of quietly doing nothing.

## Types and lint

- `poetry run basedpyright` must print `0 errors, 0 warnings`.
  `reportMissingTypeStubs` is off in `pyproject.toml`: the one package without
  stubs is `opentelemetry.instrumentation.logging`, and a warning that always
  stands stops being a signal.
- No `# pyright: ignore` and no relaxed rules. The directive line at the top of
  each `tasks.py` is the exception: it is what makes a bodyless stub type-check.
- An unused result is written `_ = ...` — `reportUnusedCallResult` is on, and
  `_ = broker.startup()` in the examples is the shape.
- A repeated long signature becomes a `TypeAlias` instead of being spelled out
  twice.
- A field or value with a known shape gets that shape; `object`, `Any` and
  `dict[str, Any]` are not neutral choices.
- A call with several parameters passes them by keyword.
- No implicit string concatenation: assemble the value in a local, then build
  one f-string.

## Checks, tools and git

- Dependencies go through `poetry add`, never a hand edit of `pyproject.toml`.
  A dependency change ends with `poetry lock` and `poetry check --lock`; the
  deprecation warnings about `[tool.poetry.readme/license/authors/repository]`
  are noise.
- `poetry run black` and `poetry run isort` over `shiro/` and `examples/`
  (line length 80, isort profile `black`).
- There is no `tests/` here; consumers own the integration suite. Do not add a
  test tree as a side effect of another change.
- Staging, commits, tags and pushes are the user's. Hand over the commands
  (`git add -A`, `git commit -m "<subject>"`, `git push origin <branch>`) with
  a subject-only message; a version bump is a `poetry version` line in the
  report, not an edit made silently.
- Python 3.14, poetry, pydantic 2 and `pydantic-settings` 2.

## Global state

- `_broker` in each `broker.py` is the one mutable module-level name allowed,
  and `global` appears only in the `define_*` builders and `declare_task` that
  write and read it: the decorator runs at import and has to find the process's
  single broker.
- No other module-level mutable state and no second cache: a per-call value is
  an argument, a per-process value is a field of the object that owns it.
- `_state` in `shiro/util/telemetry/otel_setup.py` is the other declared
  exception — the providers are process-wide by definition, and `set_up_otel`
  refuses a second call.

# Broker topology

| Service | Exchange | Queue | Result backend |
| --- | --- | --- | --- |
| `main_api` | HEADERS `main_api_exchange` | `main_api_queue` | Redis, `result_ex_time_s` |
| `peerhub` | HEADERS `peerhub_exchange` | `peerhub_queue.<peerhub_id>`, bound with `peerhub_id` | Redis, `result_ex_time_s` |
| `telegram_bot` | TOPIC `telegram_bot_exchange` | `telegram_bot_queue`, declared by both sides | none |

- `main_api` and `peerhub` are request/response: `_as_client` declares
  `<exchange>.client` with `{"x-match": "all", "shiro-client": "never"}`, so a
  client starts before any worker has declared its queue. `_as_worker` binds
  `{"x-match": "all"} | queue_bind_arguments`.
- `peerhub` is one queue per hub. A shared queue with per-hub bindings would
  let any worker consume a task addressed to another hub; `route_task_to_peerhub`
  labels the message with `peerhub_id` instead of building a queue name.
- `telegram_bot` is fire-and-forget: notifications return `None`, nobody reads
  a result, so there is no result backend and no middleware. Both
  `define_telegram_bot_broker_as_client` and `_as_worker` build the same broker
  and queue; `_as_worker` also sets `is_worker_process`, because aio-pika opens
  the read channel in `startup()` only for a worker, and the consumer starts the
  broker itself.
- Results expire so a WireGuard config with a private key (`get_config`,
  `get_connection_config`) and an unread heartbeat do not stay in Redis.
- Telemetry: `observe(call_id, log_values=False)` records a span, call/return
  records and a duration histogram. `log_values=True` also records arguments
  and the return value — never on anything that carries a private key or a
  token.

# Task surface

- `main_api` (`shiro/main_api/tasks.py`): client lifecycle, subscriptions and
  renewals, balances and transactions, connection config, referral info, beta
  testers, announcements, payments through Platega, and four sweeps
  (`expire_subscriptions`, `poll_payments`, `poll_chargebacks`,
  `warn_expiring_subscriptions`). Every argument is a payload model from
  `shiro/main_api/models.py`; every answer is a contract model or a primitive
  the README names.
- The sweeps are not kicked by the bot: the worker registers them on the
  broker with a taskiq `schedule` label and its scheduler kicks them. A
  scheduled task therefore never goes through `define_task`, which carries no
  labels.
- `peerhub` (`shiro/peerhub/tasks.py`): `get_peer`, `add_peer`,
  `enable_peer`, `disable_peer`, `delete_peer`, `get_config`, `get_usage`. A
  peerhub worker implements them; callers reach them through
  `route_task_to_peerhub`.
- `telegram_bot` (`shiro/telegram_bot/tasks.py`): the four notifications the
  bot implements in its own process — `notify_subscription`, `notify_topup`,
  `notify_chargeback`, `notify_referral_bonus`. The bot owns the texts and the
  chat; a sender only kicks.
- One notification carries one payload model from
  `shiro/telegram_bot/models.py`. `SubscriptionNotification.event` is
  `renewed`, `disabled`, `expiring` or `renewing`; the last two differ in
  whether the subscription would renew itself at the balance it has now.
  `TopupNotification.return_callback` is the bot's own string from
  `main_api.create_payment`, and `method` is Platega's payment name (`SBPQR`
  and the like), `None` until the payer picks one.
  `ChargebackNotification` arrives weeks or months after the payment and the
  balance stays as it is; the bot tells the client and the admins.
- `get_config` and `get_connection_config` answer `WgConfig` (a `.conf` body,
  wg-easy) or `XuiConfig` (a subscription URL, 3x-ui). The union never mixes
  them, and a reader validates the shape it got.
- `get_stats` answers `BackendStats`, whose `usage` defaults to `None` because a
  backend older than the field sends none; `top` and `low_traffic` hold
  `UsagePeer`, and a node that does not answer counts in `hubs_failed`.
- A caller waits with `TaskRunner` / `TaskSender`: `wait_result_timeout` bounds
  the wait, `wait_result_check_interval` is the poll, and a failed task raises
  the error the worker returned instead of yielding a value.

# Consumers and versioning

- A consumer pins a git tag:
  `poetry add "git+https://github.com/ShiroVPN/shiro_python_lib.git@vX.Y.Z"`.
  The tag is the release a consumer gets.
- Renaming or removing a published name is a breaking change: bump the version,
  add an `## Upgrading from X.Y` section to `README.md` with the old → new
  table, and keep exchanges, queue names and task names stable so an old worker
  and a new one talk to each other while a fleet is rolled out.
- A consumer that needs a new task or model adds it here first. The bot and the
  worker both need a release on the same version before they use it, because a
  notification carries one payload model.
- The user owns the version bump and the tag; the agent reports what the change
  makes stale in the consumers and stops there.
