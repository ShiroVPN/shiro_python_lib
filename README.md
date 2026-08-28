# Shiro python module

This module defines TaskIQ tasks for workers `peerhub` and `main_api`. For more information see README files:

- [main_api](shiro/main_api/README.md)
- [peerhub](shiro/peerhub/README.md)

It also has useful functions for defining brokers and tasks.

# Usage example on client

```python
from uuid import uuid4

from pydantic import AmqpDsn, RedisDsn

from shiro.peerhub.broker import (
    BrokerConfigForClient,
    define_broker,
    route_task_to_peerhub,
)

broker = define_broker(
    BrokerConfigForClient(
        broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
        result_backend_url=RedisDsn("redis://localhost:6379/0"),
        exchange_name="exchange_name",
    )
)
_ = broker.startup()

# import workers after define_broker was called
# kiq workers after broker was started

from shiro.peerhub.models import Peer
from shiro.peerhub.workers import get_peer


async def main():
    peerhub_id = uuid4()
    peer_id = uuid4()

    routed_get_peer = route_task_to_peerhub(get_peer, peerhub_id)
    task = await routed_get_peer.kiq(peer_id)
    result = await task.wait_result()
    peer: Peer = result.return_value
    print(peer)
```

# Usage example on worker

```python
from pydantic import AmqpDsn, RedisDsn

from shiro.main_api.broker import (
    BrokerConfigForWorker,
    define_broker,
)

broker = define_broker(
    BrokerConfigForWorker(
        broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
        result_backend_url=RedisDsn("redis://localhost:6379/0"),
        exchange_name="exchange_name",
        queue_name="queue_name",
    )
)

# import workers after define_broker was called

from shiro.main_api.models import Client, ClientGet
from shiro.main_api.workers import get_client
from shiro.util import define_task

from .dependencies import db_dependency


@define_task(get_client)
async def get_client_impl(client_data: ClientGet, db: db_dependency) -> Client:
    return await db.get_client(client_data.telegram_id)
```
