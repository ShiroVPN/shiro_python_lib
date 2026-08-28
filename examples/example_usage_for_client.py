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
from shiro.peerhub.tasks import get_peer


async def main():
    peerhub_id = uuid4()
    peer_id = uuid4()

    routed_get_peer = route_task_to_peerhub(get_peer, peerhub_id)
    task = await routed_get_peer.kiq(peer_id)
    result = await task.wait_result()
    peer: Peer = result.return_value
    print(peer)


if __name__ == "__main__":
    print("Success!")
