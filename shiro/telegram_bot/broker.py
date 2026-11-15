__all__ = [
    "BROKER_TELEGRAM_BOT_QUEUE_NAME",
    "BROKER_TELEGRAM_BOT_EXCHANGE_NAME",
    "TelegramBotBrokerConfig",
    "define_broker",
    "declare_task",
]

from typing import TypeVar

from pydantic import AmqpDsn, BaseModel
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue

import shiro.util.tasks as t

BROKER_TELEGRAM_BOT_QUEUE_NAME = "telegram_bot_queue"
BROKER_TELEGRAM_BOT_EXCHANGE_NAME = "telegram_bot_exchange"


class TelegramBotBrokerConfig(BaseModel):
    # Notifications are fire-and-forget: nothing reads a result back.
    broker_url: AmqpDsn


_broker: AioPikaBroker | None = None


def define_broker(config: TelegramBotBrokerConfig) -> AioPikaBroker:
    """
    Function: `shiro.telegram_bot.broker.define_broker`.
    Call this function before importing `shiro.telegram_bot.tasks`.
    The bot and every service that notifies it declare the same queue, so
    neither side has to start first: messages wait for the bot to consume
    them.
    """
    global _broker
    _broker = AioPikaBroker(
        url=str(config.broker_url),
        exchange=Exchange(name=BROKER_TELEGRAM_BOT_EXCHANGE_NAME),
    ).with_queue(Queue(name=BROKER_TELEGRAM_BOT_QUEUE_NAME))
    return _broker


T = TypeVar("T")


def declare_task(task_name: str):
    """
    - Used in the services that notify the bot to declare tasks.
    (declared functions don't have bodies).
    - Do not use this function to define tasks.
    (defined functions have bodies).
    - To define tasks use `shiro.util.define_task`.

    ```python
    @declare_task(task_name="name")
    async def foo(...) -> None: ...
    ```
    """
    global _broker
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper
