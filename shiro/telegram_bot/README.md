# Telegram bot python module

This is a python pkg that declares the notifications a service sends to the Telegram bot. The bot defines the tasks (it owns the texts and the chat), the services only kick them.

This module: `shiro.telegram_bot`.

# Broker

Module: `.broker`.

Broker config:

| Name                      | Fields            |
| ------------------------- | ----------------- |
| `TelegramBotBrokerConfig` | `broker_url: AmqpDsn` |

IMPORTANT: call `.broker.define_telegram_bot_broker_as_client` in a service that notifies the bot, or `.broker.define_telegram_bot_broker_as_worker` in the bot itself, before importing `.tasks`. Both build the same TOPIC broker and queue; the name says which side of the queue the process is.

Both sides declare `telegram_bot_exchange` and `telegram_bot_queue`, so neither has to start first: a message waits until the bot consumes it. There is no result backend — a notification is fire-and-forget, the sender does not wait for an answer.

# Models

Module: `.models`

| Name                        | Fields                                                                                                                                                   |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SubscriptionNotification`  | `telegram_id: TelegramID`<br/>`event: NotificationEvent`<br/>`name: str`<br/>`expired_at: datetime_utc`<br/>`balance: Decimal`                          |
| `TopupNotification`         | `telegram_id: TelegramID`<br/>`amount: Money`<br/>`balance: Decimal`<br/>`return_callback: str \| None`<br/>`method: str \| None`<br/>`platega_id: str`   |
| `ChargebackNotification`    | `telegram_id: TelegramID`<br/>`username: TelegramUsername \| None`<br/>`amount: Money`<br/>`platega_id: str`<br/>`paid_at: datetime_utc`                |
| `ReferralBonusNotification` | `telegram_id: TelegramID`<br/>`bonus: Decimal` ($\ge 0$)<br/>`balance: Decimal`                                                                          |

`NotificationEvent` is `renewed`, `disabled`, `expiring` or `renewing` — the last two differ in whether the subscription would renew itself if the balance stayed as it is now.

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
