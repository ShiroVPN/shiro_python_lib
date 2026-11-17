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

This is the only documentation file besides the root `README.md`: the README is
the short human overview, and everything else — the rules a change has to
satisfy, the broker topology, the per-field tables and the upgrade notes — lives
here.

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
- A fact the code cannot express goes into this file, never back into a comment.
  When a comment is deleted, its fact moves there in the same change.
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
  the tables under `# Contract reference` say which ones are live.

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
- Documentation is two files at the root: `README.md`, short and for humans —
  what the project is and what it declares — and this `AGENTS.md`. A model, a
  task or an error that changes updates its table here in the same change; the
  README changes only when the overview itself does.

## Brokers

- A new broker is built by `shiro/util/broker.create_broker`. A service module
  only names its exchange and queue; it never opens an `AioPikaBroker` of its
  own.
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
| `telegram_bot` | HEADERS `telegram_bot_exchange` | `telegram_bot_queue` | Redis, `result_ex_time_s` |

- `main_api` and `peerhub` are request/response: `_as_client` declares
  `<exchange>.client` with `{"x-match": "all", "shiro-client": "never"}`, so a
  client starts before any worker has declared its queue. `_as_worker` binds
  `{"x-match": "all"} | queue_bind_arguments`.
- `peerhub` is one queue per hub. A shared queue with per-hub bindings would
  let any worker consume a task addressed to another hub; `route_task_to_peerhub`
  labels the message with `peerhub_id` instead of building a queue name.
- `telegram_bot` shares the request/response shape even though a notification
  returns `None`: both roles go through `create_broker`, so a sender declares
  `telegram_bot_exchange.client`, the bot consumes `telegram_bot_queue`, and the
  result backend is written and never read.
- A builder never sets `is_worker_process`; the process that consumes does.
  `taskiq worker` sets it in its CLI, and a process that runs the receiver
  itself passes `run_startup=True` to `run_receiver_task`, which sets the flag
  before `Receiver.listen` calls `startup()`. Without it aio-pika opens no read
  channel and `listen()` raises `NoStartupError`.
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
  the task table names.
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

# Contract reference

Per-field tables, per-task arguments and per-error codes of each module. A
change to any of them updates the table here in the same change.

## main_api

Manages VPN subscriptions, client balances and transactions, and uses
`peerhub` tasks to manage VPN connections.

### Broker

| Name | Fields |
| --- | --- |
| `MainApiBrokerConfigForClient` | `broker_url: AmqpDsn`<br/>`result_backend_url: RedisDsn`<br/>`exchange_name: str` (default `main_api_exchange`) |
| `MainApiBrokerConfigForWorker` | `MainApiBrokerConfigForClient`<br/>+ `queue_name: str` (default `main_api_queue`) |

Call `define_main_api_broker_as_client` (a service that only kicks `main_api`
tasks) or `define_main_api_broker_as_worker` (the process that consumes
`main_api_queue`) before importing `.tasks`.

### Models

| Name | Fields |
| --- | --- |
| `SubscriptionConfig` | `name: str`<br/>`cost: Decimal` ($\ge 0$)<br/>`timedelta_in_seconds: int` (> 0) |
| `Client` | `telegram_id: TelegramID`<br/>`balance: Decimal`<br/>`activated_trial: bool`<br/>`autoupdate_subscriptions: bool`<br/>`created_at: datetime_utc`<br/>`updated_at: datetime_utc` |
| `ClientGet` | `telegram_id: TelegramID` |
| `ClientPost` | inherits `ClientGet`<br/>`referrer_telegram_id: TelegramID \| None = None` |
| `ClientUsernamePost` | inherits `ClientGet`<br/>`username: TelegramUsername \| None = None` |
| `TransactionPost` | inherits `ClientGet`<br/>`delta: Decimal` |
| `Transaction` | `old_balance: Decimal`<br/>`new_balance: Decimal`<br/>`delta: Decimal` |
| `Subscription` | `subscription_config: SubscriptionConfig`<br/>`enabled: bool`<br/>`autoupdate: bool`<br/>`expired_at: datetime_utc`<br/>`created_at: datetime_utc` |
| `SubscriptionPost` | inherits `ClientGet`<br/>`subscription_option_name: str` |
| `SubscriptionDaysPost` | inherits `ClientGet`<br/>`days: int` (1–31) |
| `SubscriptionDiscountPost` | inherits `SubscriptionPost`<br/>`discount_percent: int` (1–50) |
| `ReferralInfo` | `enabled: bool`<br/>`bonus: Decimal` ($\ge 0$)<br/>`trial_name: str`<br/>`trial_seconds: int` (> 0)<br/>`invited: int` ($\ge 0$)<br/>`paid: int` ($\ge 0$) |
| `UsagePeer` | `telegram_id: TelegramID`<br/>`username: TelegramUsername \| None`<br/>`tx: int` ($\ge 0$)<br/>`rx: int` ($\ge 0$)<br/>`seconds_ago: float \| None` |
| `UsageStats` | `enabled_peers`, `connected`, `seen_24h`, `seen_7d`, `tx`, `rx`, `low_traffic_count`, `hubs_failed: int` ($\ge 0$)<br/>`top: list[UsagePeer]`<br/>`low_traffic: list[UsagePeer]` |
| `BackendStats` | `clients`, `active_trial`, `paying: int` ($\ge 0$)<br/>`usage: UsageStats \| None = None` |
| `BetaTester` | `telegram_id: TelegramID`<br/>`username: TelegramUsername \| None` |
| `BetaTesterPost` | `username: TelegramUsername`<br/>`beta_tester: bool` |
| `AnnounceGet` | `audience: "all" \| "active" \| "beta"` |
| `FeatureGet` | inherits `ClientGet`<br/>`feature: str` (not empty) |
| `PaymentGet` | `payment_id: UUID` |
| `PaymentPost` | inherits `ClientGet`<br/>`amount: Money`<br/>`return_callback: str \| None` (at most 64 chars) |
| `PeerHubHeartbeatData` | `hub_id: UUID`<br/>`server_name: str`<br/>`connection_type: str`<br/>`country: str`<br/>`last_seen_at: datetime_utc` |
| `Success` | `ok: bool = True` |

`TelegramID`, `TelegramUsername` and `Money` are shared pydantic aliases from
`shiro.util.types`: a Telegram id ($\ge 0$, $\lt 2^{63}$), a Telegram
@username (`[A-Za-z0-9_]{1,32}`, without `@`) and a positive ruble amount with
at most two decimals. `PaymentStatus` is `PENDING` | `CONFIRMED` | `CANCELED` |
`CHARGEBACKED`, the string `main_api.check_payment` answers with.

`PaymentPost.return_callback` is the bot's own data: it comes back untouched in
`telegram_bot.notify_topup`.

`BackendStats.usage` is read from the nodes' live counters, not a history: a
node that does not answer is counted in `hubs_failed` and its peers report
nothing.

### Tasks

| Name | Arguments | Returns | Business errors |
| --- | --- | --- | --- |
| `main_api.get_client` | `ClientGet` | `Client` | `client_not_found` |
| `main_api.post_client`<br />Links the client to `referrer_telegram_id` if that client exists and is not the new one; otherwise the referrer is dropped silently. | `ClientPost` | `Client` | `client_exists` |
| `main_api.post_transaction` | `TransactionPost` | `Transaction` | `client_not_found`, `balance_will_be_negative` |
| `main_api.get_subscription` | `ClientGet` | `Subscription` | `client_not_found`, `subscription_not_found` |
| `main_api.get_subscription_options`<br />Call this to select a subscription and add it with `main_api.post_new_subscription`. | (none) | `list[SubscriptionConfig]`<br />All options with positive cost. Does not include trial. | – |
| `main_api.get_trial_subscription_config`<br />The free trial `main_api.post_trial_subscription` gives. | (none) | `SubscriptionConfig` | – |
| `main_api.post_trial_subscription` | `ClientGet` | `Subscription` | `client_not_found`, `client_already_activated_trial`, `subscription_exists`, `alive_peerhub_not_found`, `trial_subscription_is_not_free` |
| `main_api.post_new_subscription`<br />Moves the client's subscription to the option, adding what is left of it; a client without one gets a new subscription. Either way `activated_trial` becomes true. | `SubscriptionPost` | `Subscription` | `client_not_found`, `subscription_option_not_found`, `balance_will_be_negative`, `alive_peerhub_not_found` |
| `main_api.renew_subscription` | `ClientGet` | `Subscription` | `client_not_found`, `subscription_not_found`, `subscription_option_not_found`, `balance_will_be_negative` |
| `main_api.update_subscription` | `ClientGet` | `Subscription` | `client_not_found`, `subscription_not_found`, `subscription_is_not_expired` |
| `main_api.get_connection_config` | `ClientGet` | `WgConfig \| XuiConfig` | `client_not_found`, `subscription_not_found` |
| `main_api.notify_client` | `ClientGet` | `Success` | – |
| `main_api.update_peerhub_heartbeat` | `PeerHubHeartbeatData` | `Success` | – |
| `main_api.set_client_username`<br />Syncs the @username Telegram shows; `None` — there is none or it was removed. Answers whether the stored value changed, `None` when there is no client yet. | `ClientUsernamePost` | `bool \| None` | – |
| `main_api.get_stats`<br />The bot's admin `/stats`; `usage` comes from the nodes' live counters and is absent from a backend older than this version. | (none) | `BackendStats` | – |
| `main_api.get_referral_info`<br />The invite program and the client's counters — zeros for a telegram_id with no client. | `ClientGet` | `ReferralInfo` | – |
| `main_api.has_feature`<br />Whether the bot may show a feature it gates itself: one not listed in the backend's `beta_features` is open to everyone, even a newcomer. | `FeatureGet` | `bool` | – |
| `main_api.set_beta_tester`<br />The bot's admin `/beta`: finds the client by the @username the bot synced. | `BetaTesterPost` | `int \| None` | – |
| `main_api.get_beta_testers` | (none) | `list[BetaTester]` | – |
| `main_api.get_announce_recipients`<br />The bot's admin `/announce`: `all` clients, those with a live subscription (`active`, trial included) or `beta` testers. | `AnnounceGet` | `list[int]` | – |
| `main_api.add_subscription_days`<br />Gifts days: to the subscription's end, or from now when it has expired, enabling it again. | `SubscriptionDaysPost` | `Subscription` | `client_not_found`, `subscription_not_found` |
| `main_api.post_discounted_subscription`<br />`post_new_subscription` at the discounted price, whole rubles off. | `SubscriptionDiscountPost` | `Subscription` | `client_not_found`, `subscription_option_not_found`, `balance_will_be_negative`, `alive_peerhub_not_found` |
| `main_api.create_payment`<br />A Platega payment link for the balance. Nothing is credited here: `check_payment` does it once Platega confirms. | `PaymentPost` | `str` (the link) | `client_not_found` |
| `main_api.check_payment`<br />Asks Platega instead of trusting the caller; each status move happens once, so it is safe to run any number of times at once. | `PaymentGet` | `PaymentStatus` | – |
| `main_api.expire_subscriptions`<br />Cron `*/5 * * * *`: one `update_subscription` per client whose subscription has expired. | (none) | `int` (clients swept) | – |
| `main_api.poll_payments`<br />Cron `* * * * *`: Platega export over the payments still pending — a fallback for lost callbacks. | (none) | `int` (payments checked) | – |
| `main_api.poll_chargebacks`<br />Cron `0 * * * *`: the same export over paid payments of the last 540 days. | (none) | `int` (payments checked) | – |
| `main_api.warn_expiring_subscriptions`<br />Cron `*/5 * * * *`: warnings for the subscriptions expiring in 3 and 1 days. | (none) | `int` (warnings sent) | – |

The tasks from `expire_subscriptions` on are not called by the bot: the
scheduler (`taskiq scheduler main_api_worker.scheduler:scheduler`) kicks them on
their cron labels, and `check_payment` is kicked by the worker's Platega webhook
and by the two poll tasks. `main_api.notify_client` is declared here but the
worker does not implement it.

`WgConfig` and `XuiConfig` are `shiro.peerhub.models`. A wg-easy peerhub answers
with `{config}` (the `.conf` body), a 3x-ui peerhub with `{sub_url}`; the union
never mixes them, because taskiq sends the result as JSON primitives and the
reader validates the shape it got.

### Exceptions

All inherit from `AppException`, and each `error_code` is a member of
`shiro.util.errors.ErrorCode`.

| Name | Description | Error code | Status code | How and where can rise? |
| --- | --- | --- | --- | --- |
| `client_exists` | Client with given Telegram ID already exists. | `CLIENT_EXISTS` | 499 | `main_api.post_client` |
| `client_not_found` | Client with given Telegram ID does not exist. | `CLIENT_NOT_FOUND` | 498 | Almost every task. |
| `client_already_activated_trial` | | `CLIENT_ALREADY_ACTIVATED_TRIAL` | 497 | `main_api.post_trial_subscription` |
| `client_did_not_activate_trial` | | `CLIENT_DID_NOT_ACTIVATE_TRIAL` | 496 | – |
| `subscription_exists` | Client has a subscription (sub is not marked deleted in DB). | `SUBSCRIPTION_EXISTS` | 495 | `main_api.post_trial_subscription` |
| `subscription_not_found` | Client has no subscription. | `SUBSCRIPTION_NOT_FOUND` | 494 | `main_api.renew_subscription`, `main_api.update_subscription`, `main_api.get_connection_config` |
| `balance_is_negative` | Balance cannot be negative. | `BALANCE_IS_NEGATIVE` | 493 | Should not rise (logic prevents negative balance). |
| `balance_will_be_negative` | Operation would result in negative balance. | `BALANCE_WILL_BE_NEGATIVE` | 492 | `main_api.post_transaction`, `main_api.post_new_subscription`, `main_api.renew_subscription` |
| `subscription_option_not_found` | `SubscriptionConfig` with given name is not in `Config`. | `SUBSCRIPTION_OPTION_NOT_FOUND` | 491 | `main_api.post_new_subscription`, `main_api.renew_subscription` |
| `subscription_option_exists` | | `SUBSCRIPTION_OPTION_EXISTS` | 483 | Should not rise. |
| `operation_in_progress` | Another task of this client already holds the client lock. | `OPERATION_IN_PROGRESS` | 482 | A second task that changes the subscription or spends the balance for the same client. |
| `trial_subscription_is_not_free` | Trial subscription cost must be zero. | `TRIAL_SUBSCRIPTION_IS_NOT_FREE` | 490 | `main_api.post_trial_subscription` (should not rise). |
| `subscription_is_expired` | | `SUBSCRIPTION_IS_EXPIRED` | 489 | Should not rise. |
| `subscription_is_not_expired` | | `SUBSCRIPTION_IS_NOT_EXPIRED` | 488 | `main_api.update_subscription` |
| `subscription_config_changed` | Subscription configuration has changed with time. F.e. client added this option when it cost 100, but now it costs 200. | `SUBSCRIPTION_CONFIG_CHANGED` | 485 | Not raised in any task (policy unused). |
| `subscription_config_did_not_change` | | `SUBSCRIPTION_CONFIG_DID_NOT_CHANGE` | 484 | Should not rise. |
| `alive_peerhub_not_found` | No active (alive) PeerHub instance available. | `ALIVE_PEERHUB_NOT_FOUND` | 599 | `main_api.post_trial_subscription`, `main_api.post_new_subscription` |

## peerhub

Declares the `peerhub` tasks: `main_api` uses them to manage peers, and a
`peerhub` worker implements them against one VPN node.

### Broker

| Name | Fields |
| --- | --- |
| `PeerhubBrokerConfigForClient` | `broker_url: AmqpDsn`<br/>`result_backend_url: RedisDsn`<br/>`exchange_name: str` (default `peerhub_exchange`) |
| `PeerhubBrokerConfigForWorker` | `PeerhubBrokerConfigForClient`<br/>+ `peerhub_id: UUID` (to route to `peerhub`)<br/>+ `queue_name: str`, default `peerhub_queue.<peerhub_id>` — one queue per peerhub |

Call `define_peerhub_broker_as_client` (a service that only kicks `peerhub`
tasks) or `define_peerhub_broker_as_worker` (the process that consumes the queue
of its own `peerhub_id`) before importing `.tasks`. To route a task to a peerhub
use `route_task_to_peerhub(task, peerhub_id: UUID)`.

### Models

| Name | Fields |
| --- | --- |
| `Peer` | `id: UUID`<br/>`name: str`<br/>`enabled: bool` |
| `PeerAdd` | `name: str`<br/>`id: UUID` |
| `PeerUsage` | `id: UUID`<br/>`enabled: bool`<br/>`rx: int` ($\ge 0$)<br/>`tx: int` ($\ge 0$)<br/>`latest_handshake_at: datetime_utc \| None` |
| `Success` | `ok: bool = True` |
| `WgConfig` | `config: str` |
| `XuiConfig` | `sub_url: str` |

Two kinds of peerhub answer `peerhub.get_config` with a different artifact: a
wg-easy node with the `.conf` body, a 3x-ui node with the subscription URL.
These models are never shared by reference: taskiq dumps a result to JSON-safe
primitives before pickling it, so a reader validates `{"config": ...}` or
`{"sub_url": ...}` into whichever model it needs.

### Tasks

| Name | Input | Output |
| --- | --- | --- |
| `peerhub.get_peer` | `UUID` | `Peer` |
| `peerhub.add_peer` | `PeerAdd` | `Peer` |
| `peerhub.enable_peer` | `UUID` | `Success` |
| `peerhub.disable_peer` | `UUID` | `Success` |
| `peerhub.delete_peer` | `UUID` | `Success` |
| `peerhub.get_config` | `UUID` | `WgConfig \| XuiConfig` |
| `peerhub.get_usage` | (none) | `list[PeerUsage]` |

`peerhub.get_usage` reports the node's live counters, not a history: a node
restart resets them, a disabled peer is absent from a wg-easy answer while 3x-ui
keeps reporting its last traffic, and `latest_handshake_at` is `None` until the
peer's first connection.

### Exceptions

| Name | Description | Error code |
| --- | --- | --- |
| `peer_not_found` | Raised if peer with given id was not found. | `PEER_NOT_FOUND` |
| `peer_exists` | Raised if a peer with given id already exists. | `PEER_EXISTS` |

Both carry `error_code` from `shiro.util.errors.ErrorCode` and no
`status_code`: a peerhub error is matched by code, not mapped to an HTTP number.
`str(error)` is the human text (`Peer not found: id = …`), not the code, so a
caller reads `error_code_of(error)`, which falls back to the class name.

## telegram_bot

Declares the notifications a service sends to the Telegram bot. The bot defines
the tasks (it owns the texts and the chat), the services only kick them.

### Broker

| Name | Fields |
| --- | --- |
| `TelegramBotBrokerConfigForClient` | `broker_url: AmqpDsn`<br/>`result_backend_url: RedisDsn`<br/>`exchange_name: str` (default `telegram_bot_exchange`) |
| `TelegramBotBrokerConfigForWorker` | `TelegramBotBrokerConfigForClient`<br/>+ `queue_name: str` (default `telegram_bot_queue`)<br/>+ `queue_bind_arguments: dict[str, str]` (default `{}`) |

Call `define_telegram_bot_broker_as_client` in a service that notifies the bot,
or `define_telegram_bot_broker_as_worker` in the bot itself, before importing
`.tasks`.

Neither builder sets `is_worker_process`: consuming is the process's own state,
not a property of the config.

### Models

| Name | Fields |
| --- | --- |
| `SubscriptionNotification` | `telegram_id: TelegramID`<br/>`event: NotificationEvent`<br/>`name: str`<br/>`expired_at: datetime_utc`<br/>`balance: Decimal` |
| `TopupNotification` | `telegram_id: TelegramID`<br/>`amount: Money`<br/>`balance: Decimal`<br/>`return_callback: str \| None`<br/>`method: str \| None`<br/>`platega_id: str` |
| `ChargebackNotification` | `telegram_id: TelegramID`<br/>`username: TelegramUsername \| None`<br/>`amount: Money`<br/>`platega_id: str`<br/>`paid_at: datetime_utc` |
| `ReferralBonusNotification` | `telegram_id: TelegramID`<br/>`bonus: Decimal` ($\ge 0$)<br/>`balance: Decimal` |

`NotificationEvent` is `renewed`, `disabled`, `expiring` or `renewing` — the
last two differ in whether the subscription would renew itself if the balance
stayed as it is now.

`TopupNotification.return_callback` is the bot's own data from
`main_api.create_payment`; `method` is Platega's name (`SBPQR` and the like),
`None` until the payer picks one.

`ChargebackNotification` arrives weeks or months after the payment: the payer's
bank took the money back, the balance stays as it is and the bot tells the
client and the admins.

`ReferralBonusNotification` means the invited friend paid for the first time and
the bonus is already on the inviter's balance.

`TelegramID`, `TelegramUsername` and `Money` are the shared aliases from
`shiro.util.types`, described under `main_api`.

### Tasks

| Name | Input | Output |
| --- | --- | --- |
| `telegram_bot.notify_subscription` | `SubscriptionNotification` | None |
| `telegram_bot.notify_topup` | `TopupNotification` | None |
| `telegram_bot.notify_chargeback` | `ChargebackNotification` | None |
| `telegram_bot.notify_referral_bonus` | `ReferralBonusNotification` | None |

The bot implements them with `shiro.util.define_task` on the broker from
`.broker`; their taskiq dependencies (the `Bot`, the settings) are the bot's own
and are not part of this contract.

# Upgrading

## Upgrading from 0.6.x

`telegram_bot` now goes through `shiro.util.broker.create_broker` like the other
two services: a HEADERS exchange instead of TOPIC, a queue of its own on the
sending side, a result backend and the telemetry middleware. That topology
cannot be rolled over a running 0.6.x pair, so on a RabbitMQ that ran 0.6.x:

1. Upgrade every sender and the bot together: a 0.6.x sender publishes to the
   TOPIC exchange and a 0.7.0 worker consumes the HEADERS one, so the two do not
   meet.
2. Delete the old exchange before the first 0.7.0 process declares it, otherwise
   the declaration fails with `PRECONDITION_FAILED` — an exchange type cannot
   change in place: `rabbitmqctl delete_exchange telegram_bot_exchange`.
3. `telegram_bot_queue` keeps its name and is bound with `{"x-match": "all"}`;
   the sender's queue is `telegram_bot_exchange.client`, which nothing routes
   into. Results go to `BROKER_RESULT_BACKEND_URL` and expire after
   `result_ex_time_s`, as for the other services.
4. No builder sets `is_worker_process` any more, so the bot drops its own
   `await broker.startup()` and passes `run_startup=True` to
   `run_receiver_task`: the receiver sets the flag and starts the broker itself.
   A bot that calls `startup()` before the receiver starts listening without the
   flag will open no read channel and consume nothing.

| 0.6.x | 0.7.0 |
| --- | --- |
| `shiro.telegram_bot.broker.TelegramBotBrokerConfig` | `TelegramBotBrokerConfigForClient` / `TelegramBotBrokerConfigForWorker` |
| `broker_url` only | `result_backend_url` is required, as for the other services |

Business error codes are unchanged: every code keeps its string, and an
`ErrorCode` member compares equal to it, so a consumer that matches
`"CLIENT_NOT_FOUND"` keeps working. New in 0.7.0:
`shiro.util.errors.ErrorCode` lists the codes, `error_code_of(error)` recovers
one from an exception that came back through taskiq, and
`main_api.exceptions.operation_in_progress` (482) is declared here — a worker
that declared its own class drops it and imports this one.

## Upgrading from 0.5.x

Broker entry points are named after the service they belong to and split by the
role the process plays. The configurations keep their shape; what changes is the
import and which builder the process calls.

| 0.5.x | 0.6.0 |
| --- | --- |
| `shiro.main_api.broker.BrokerConfigForClient` / `define_broker` | `MainApiBrokerConfigForClient` / `define_main_api_broker_as_client` |
| `shiro.main_api.broker.BrokerConfigForWorker` / `define_broker` | `MainApiBrokerConfigForWorker` / `define_main_api_broker_as_worker` |
| `shiro.peerhub.broker.BrokerConfigForClient` / `define_broker` | `PeerhubBrokerConfigForClient` / `define_peerhub_broker_as_client` |
| `shiro.peerhub.broker.BrokerConfigForWorker` / `define_broker` | `PeerhubBrokerConfigForWorker` / `define_peerhub_broker_as_worker` |
| `shiro.telegram_bot.broker.define_broker` — a service that notifies the bot | `define_telegram_bot_broker_as_client` |
| `shiro.telegram_bot.broker.define_broker` — the bot itself | `define_telegram_bot_broker_as_worker` |

`_as_client` declares the exchange and its own `<exchange>.client` queue, which
nothing routes into: the process only kicks tasks and never consumes. `_as_worker`
declares the queue the process consumes. `main_api` and `peerhub` go through
`shiro.util.broker.create_broker`, which picks the queue from the config, so the
name says which role the process plays — and which config type it may pass.
`telegram_bot` built its own TOPIC broker in 0.6.0 and joined the shared builder
in 0.7.0.

`TelegramBotBrokerConfig`, `route_task_to_peerhub`, `declare_task` and
`define_task` keep their names, and `shiro.util.broker` keeps the generic
`BrokerConfigForClient` / `BrokerConfigForWorker` and `create_broker`. Exchanges,
queue names, bindings and routing are untouched, so 0.5.x and 0.6.0 workers talk
to each other while a fleet is being upgraded.

## Upgrading from 0.3.x

`peerhub.get_config` now answers `WgConfig | XuiConfig` instead of a plain
string: a wg-easy peerhub returns `{config}` (the `.conf` body), a 3x-ui one
`{sub_url}` (the subscription URL). `main_api.get_connection_config` passes the
same union through, so a reader that used to expect a string must validate the
shape it got. Taskiq sends the result as JSON primitives, so validate the dict,
not a shared class.

## Upgrading from 0.1.x

Peerhub workers move from the shared `peerhub_queue` to `peerhub_queue.<PEERHUB_ID>`.
On a RabbitMQ that ran the old chain, in this order:

1. Upgrade `main_api_worker` (and every other peerhub *client*) to 0.2.0 first.
   Old clients require the old `peerhub_queue` to exist at startup; new ones do
   not.
2. Per hub: stop the old worker, then start the new one. Never run both for one
   hub: a headers exchange delivers each message to every matching queue, so the
   task would execute twice.
3. Delete the old queue, otherwise it keeps a copy of every peerhub message with
   nobody consuming: `rabbitmqctl delete_queue peerhub_queue`. Check for other
   stale bindings with
   `rabbitmqctl list_bindings source_name destination_name arguments | grep peerhub_exchange`
   — every destination must be a running hub's `peerhub_queue.<PEERHUB_ID>` or
   `peerhub_exchange.client`.
4. Results written by 0.1.x workers have no TTL. Once every worker is on 0.2.0,
   clear them: `redis-cli FLUSHDB` on the result database (nothing else lives
   there).

API changes: `queue_name` is no longer a client config field;
`OTEL_COLLECTOR_ENDPOINT` is optional and `OTEL_SERVICE_NAME` defaults to
`shiro`; the `BROKER_RESULT_BACKEND_URL` error text names the variable;
`from shiro.util import define_task` (removed in 0.1.0) is
`shiro.util.tasks.define_task`.

# Consumers and versioning

- A consumer pins a git tag:
  `poetry add "git+https://github.com/ShiroVPN/shiro_python_lib.git@vX.Y.Z"`.
  The tag is the release a consumer gets.
- Renaming or removing a published name is a breaking change: bump the version,
  add an `## Upgrading from X.Y` subsection under `# Upgrading` here with the
  old → new table, and keep exchanges, queue names and task names stable so an
  old worker and a new one talk to each other while a fleet is rolled out.
- A consumer that needs a new task or model adds it here first. The bot and the
  worker both need a release on the same version before they use it, because a
  notification carries one payload model.
- The user owns the version bump and the tag; the agent reports what the change
  makes stale in the consumers and stops there.
