# Telegram bot python module

This is a python pkg that declares the notifications a service sends to the Telegram bot. The bot defines the tasks (it owns the texts and the chat), the services only kick them.

This module: `shiro.telegram_bot`.

# Broker

Module: `.broker`.

Broker configs:

| Name                               | Fields                                                                                                    |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `TelegramBotBrokerConfigForClient` | `broker_url: AmqpDsn`<br/>`result_backend_url: RedisDsn`<br/>`exchange_name: str` (default `telegram_bot_exchange`) |
| `TelegramBotBrokerConfigForWorker` | `TelegramBotBrokerConfigForClient`<br/>+ `queue_name: str` (default `telegram_bot_queue`)<br/>+ `queue_bind_arguments: dict[str, str]` (default `{}`) |

IMPORTANT: call `.broker.define_telegram_bot_broker_as_client` in a service that notifies the bot, or `.broker.define_telegram_bot_broker_as_worker` in the bot itself, before importing `.tasks`.

Both go through `shiro.util.broker.create_broker`, as `main_api` and `peerhub` do: HEADERS `telegram_bot_exchange`, the sender's queue `telegram_bot_exchange.client` bound with `{"x-match": "all", "shiro-client": "never"}` and the bot's queue `telegram_bot_queue` bound with `{"x-match": "all"}`, a Redis result backend with `result_ex_time_s` (default 3600) and the OpenTelemetry middleware. A notification returns `None` and nobody reads its result: the backend is the shared builder's shape, not an answer anyone waits for.

Neither builder sets `is_worker_process`: consuming is the process's own state, not a property of the config. `taskiq worker` sets it in its CLI before importing tasks; the bot, which runs the receiver in its own process, passes `run_startup=True` to `run_receiver_task`, and the receiver sets the flag before `Receiver.listen` calls `startup()`. Without the flag `AioPikaBroker.startup()` opens no read channel and `listen()` raises `NoStartupError` — the process stays up and consumes nothing.

# Models

Module: `.models`

| Name                        | Fields                                                                                                                                                   |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SubscriptionNotification`  | `telegram_id: TelegramID`<br/>`event: NotificationEvent`<br/>`name: str`<br/>`expired_at: datetime_utc`<br/>`balance: Decimal`                          |
| `TopupNotification`         | `telegram_id: TelegramID`<br/>`amount: Money`<br/>`balance: Decimal`<br/>`return_callback: str \| None`<br/>`method: str \| None`<br/>`platega_id: str`   |
| `ChargebackNotification`    | `telegram_id: TelegramID`<br/>`username: TelegramUsername \| None`<br/>`amount: Money`<br/>`platega_id: str`<br/>`paid_at: datetime_utc`                |
| `ReferralBonusNotification` | `telegram_id: TelegramID`<br/>`bonus: Decimal` ($\ge 0$)<br/>`balance: Decimal`                                                                          |

`NotificationEvent` is `renewed`, `disabled`, `expiring` or `renewing` — the last two differ in whether the subscription would renew itself if the balance stayed as it is now.

`TopupNotification.return_callback` is the bot's own data from `main_api.create_payment`; `method` is Platega's name (`SBPQR` and the like), `None` until the payer picks one.

`ChargebackNotification` arrives weeks or months after the payment: the payer's bank took the money back, the balance stays as it is and the bot tells the client and the admins.

`ReferralBonusNotification` means the invited friend paid for the first time and the bonus is already on the inviter's balance.

`TelegramID`, `TelegramUsername` and `Money` are shared pydantic aliases from `shiro.util.types`: a Telegram id ($\ge 0$, $\lt 2^{63}$), a Telegram @username (`[A-Za-z0-9_]{1,32}`, without `@`) and a positive ruble amount with at most two decimals.

# Tasks

Module: `.tasks`

| Name                                 | Input                       | Output |
| ------------------------------------ | --------------------------- | ------ |
| `telegram_bot.notify_subscription`   | `SubscriptionNotification`  | None   |
| `telegram_bot.notify_topup`          | `TopupNotification`         | None   |
| `telegram_bot.notify_chargeback`     | `ChargebackNotification`    | None   |
| `telegram_bot.notify_referral_bonus` | `ReferralBonusNotification` | None   |

The bot implements them with `shiro.util.define_task` on the broker from `.broker`; their taskiq dependencies (the `Bot`, the settings) are the bot's own and are not part of this contract.
