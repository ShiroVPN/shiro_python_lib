__all__ = [
    "BrokerConfigForClient",
    "BrokerConfigForWorker",
    "define_broker",
]


from typing import TypeVar

from taskiq_aio_pika import AioPikaBroker

import shiro.util as b

BROKER_MAIN_API_QUEUE_NAME = "main_api_queue"
BROKER_MAIN_API_EXCHANGE_NAME = "main_api_exchange"


class BrokerConfigForClient(b.BrokerConfigForClient):
    exchange_name: str = BROKER_MAIN_API_EXCHANGE_NAME
    queue_name: str = BROKER_MAIN_API_QUEUE_NAME


class BrokerConfigForWorker(BrokerConfigForClient, b.BrokerConfigForWorker):
    queue_bind_arguments: dict[str, str] = {}


_broker: AioPikaBroker | None = None


def define_broker(
    config: BrokerConfigForClient | BrokerConfigForWorker,
) -> AioPikaBroker:
    """
    Function: `shiro.main_api.broker.define_broker`.
    Call this function before importing `shiro.main_api.workers`.
    """
    global _broker
    value = b.create_broker(config)
    _broker = value
    return _broker


T = TypeVar("T")


def declare_task(task_name: str):
    """
    - Used in `shiro.main_api.workers` to declare tasks.
    (declared functions don't have bodies).
    - Do not use this function to define tasks.
    (defined functions have bodies).
    - To define tasks use `shiro.util.define_task`.

    ```python
    @declare_task(task_name="name")
    async def foo(...) -> Bar: ...
    ```
    """
    global _broker
    wrapper = b.get_declare_task_wrapper(_broker, task_name)
    return wrapper
