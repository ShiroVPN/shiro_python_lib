__all__ = [
    "MainApiBrokerConfigForClient",
    "MainApiBrokerConfigForWorker",
    "get_main_api_broker_as_client",
    "get_main_api_broker_as_worker",
]


from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b

BROKER_MAIN_API_QUEUE_NAME = "main_api_queue"
BROKER_MAIN_API_EXCHANGE_NAME = "main_api_exchange"


class MainApiBrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_MAIN_API_EXCHANGE_NAME


class MainApiBrokerConfigForWorker(
    MainApiBrokerConfigForClient, b.BrokerConfigForWorker
):
    queue_name: str = BROKER_MAIN_API_QUEUE_NAME
    queue_bind_arguments: dict[str, str] = {}


def get_main_api_broker_as_client(
    config: MainApiBrokerConfigForClient,
) -> AioPikaBroker:
    return b.create_broker(config)


def get_main_api_broker_as_worker(
    config: MainApiBrokerConfigForWorker,
) -> AioPikaBroker:
    return b.create_broker(config)
