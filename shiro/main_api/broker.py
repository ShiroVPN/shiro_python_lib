__all__ = [
    "MainApiBrokerConfigForClient",
    "MainApiBrokerConfigForWorker",
    "define_main_api_broker_as_client",
    "define_main_api_broker_as_worker",
]


from typing import TypeVar

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
    """
    Function: `shiro.main_api.broker.define_main_api_broker_as_client`.
    Call this function before importing `shiro.main_api.tasks`.
    Use it in a service that only kicks `main_api` tasks.
    """
    global _broker
    _broker = b.create_broker(config)
    return _broker


def define_main_api_broker_as_worker(
    config: MainApiBrokerConfigForWorker,
) -> AioPikaBroker:
    """
    Function: `shiro.main_api.broker.define_main_api_broker_as_worker`.
    Call this function before importing `shiro.main_api.tasks`.
    Use it in the process that consumes `main_api_queue`.
    """
    global _broker
    _broker = b.create_broker(config)
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
    wrapper = t.get_declare_task_wrapper(_broker, task_name)
    return wrapper
