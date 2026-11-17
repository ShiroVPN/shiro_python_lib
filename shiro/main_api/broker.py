__all__ = [
    "MainApiBrokerConfigForClient",
    "MainApiBrokerConfigForWorker",
    "define_main_api_broker_as_client",
    "define_main_api_broker_as_worker",
]


from taskiq_aio_pika import AioPikaBroker

import shiro.util.broker as b
import shiro.util.tasks as t

BROKER_MAIN_API_QUEUE_NAME = "main_api_queue"
BROKER_MAIN_API_EXCHANGE_NAME = "main_api_exchange"


class MainApiBrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_MAIN_API_EXCHANGE_NAME


class MainApiBrokerConfigForWorker(
    MainApiBrokerConfigForClient, b.BrokerConfigForWorker
):
    queue_name: str = BROKER_MAIN_API_QUEUE_NAME
    queue_bind_arguments: dict[str, str] = {}


_broker: AioPikaBroker | None = None


def define_main_api_broker_as_client(
    config: MainApiBrokerConfigForClient,
) -> AioPikaBroker:
    global _broker
    _broker = b.create_broker(config)
    return _broker


def define_main_api_broker_as_worker(
    config: MainApiBrokerConfigForWorker,
) -> AioPikaBroker:
    global _broker
    _broker = b.create_broker(config)
    return _broker


def declare_task(task_name: str):
    global _broker
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper
