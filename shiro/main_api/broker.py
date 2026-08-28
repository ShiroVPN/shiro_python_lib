__all__ = [
    "BrokerConfigForClient",
    "BrokerConfigForWorker",
    "define_broker",
]


from typing import TypeVar

from taskiq_aio_pika import AioPikaBroker

import shiro.util as b


class BrokerConfigForClient(b.BrokerConfigForClient):
    pass


class BrokerConfigForWorker(b.BrokerConfigForWorker):
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
