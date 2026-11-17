__all__ = [
    "BROKER_TELEGRAM_BOT_QUEUE_NAME",
    "BROKER_TELEGRAM_BOT_EXCHANGE_NAME",
    "TelegramBotBrokerConfig",
    "define_telegram_bot_broker_as_client",
    "define_telegram_bot_broker_as_worker",
    "declare_task",
]

from typing import TypeVar

from pydantic import AmqpDsn, BaseModel
from taskiq_aio_pika import AioPikaBroker, Exchange, Queue

import shiro.util.tasks as t

BROKER_TELEGRAM_BOT_QUEUE_NAME = "telegram_bot_queue"
BROKER_TELEGRAM_BOT_EXCHANGE_NAME = "telegram_bot_exchange"


class TelegramBotBrokerConfig(BaseModel):
    broker_url: AmqpDsn


_broker: AioPikaBroker | None = None


def _create_broker(config: TelegramBotBrokerConfig) -> AioPikaBroker:
    return AioPikaBroker(
        url=str(config.broker_url),
        exchange=Exchange(name=BROKER_TELEGRAM_BOT_EXCHANGE_NAME),
    ).with_queue(Queue(name=BROKER_TELEGRAM_BOT_QUEUE_NAME))


def define_telegram_bot_broker_as_client(
    config: TelegramBotBrokerConfig,
) -> AioPikaBroker:
    global _broker
    _broker = _create_broker(config)
    return _broker


def define_telegram_bot_broker_as_worker(
    config: TelegramBotBrokerConfig,
) -> AioPikaBroker:
    global _broker
    _broker = _create_broker(config)
    return _broker


T = TypeVar("T")


def declare_task(task_name: str):
    global _broker
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper
