__all__ = [
    "TelegramBotBrokerConfigForClient",
    "TelegramBotBrokerConfigForWorker",
    "define_telegram_bot_broker_as_client",
    "define_telegram_bot_broker_as_worker",
]


from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b
import shiro.util.tasks as t

BROKER_TELEGRAM_BOT_QUEUE_NAME = "telegram_bot_queue"
BROKER_TELEGRAM_BOT_EXCHANGE_NAME = "telegram_bot_exchange"


class TelegramBotBrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_TELEGRAM_BOT_EXCHANGE_NAME


class TelegramBotBrokerConfigForWorker(
    TelegramBotBrokerConfigForClient, b.BrokerConfigForWorker
):
    queue_name: str = BROKER_TELEGRAM_BOT_QUEUE_NAME
    queue_bind_arguments: dict[str, str] = {}


_broker: AioPikaBroker | None = None


def define_telegram_bot_broker_as_client(
    config: TelegramBotBrokerConfigForClient,
) -> AioPikaBroker:
    global _broker
    _broker = b.create_broker(config)
    return _broker


def define_telegram_bot_broker_as_worker(
    config: TelegramBotBrokerConfigForWorker,
) -> AioPikaBroker:
    global _broker
    _broker = b.create_broker(config)
    return _broker


def declare_task(task_name: str):
    global _broker
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper
