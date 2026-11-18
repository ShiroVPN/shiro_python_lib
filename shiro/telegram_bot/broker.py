__all__ = [
    "TelegramBotBrokerConfigForClient",
    "TelegramBotBrokerConfigForWorker",
    "get_telegram_bot_broker_as_client",
    "get_telegram_bot_broker_as_worker",
]


from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b

BROKER_TELEGRAM_BOT_QUEUE_NAME = "telegram_bot_queue"
BROKER_TELEGRAM_BOT_EXCHANGE_NAME = "telegram_bot_exchange"


class TelegramBotBrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_TELEGRAM_BOT_EXCHANGE_NAME


class TelegramBotBrokerConfigForWorker(
    TelegramBotBrokerConfigForClient, b.BrokerConfigForWorker
):
    queue_name: str = BROKER_TELEGRAM_BOT_QUEUE_NAME
    queue_bind_arguments: dict[str, str] = {}


def get_telegram_bot_broker_as_client(
    config: TelegramBotBrokerConfigForClient,
) -> AioPikaBroker:
    return b.create_broker(config)


def get_telegram_bot_broker_as_worker(
    config: TelegramBotBrokerConfigForWorker,
) -> AioPikaBroker:
    return b.create_broker(config)
