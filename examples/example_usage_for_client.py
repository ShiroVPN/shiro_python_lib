from uuid import uuid4

from pydantic import AmqpDsn, HttpUrl, RedisDsn

from shiro.peerhub.broker import (
    BrokerConfigForClient,
    define_broker,
    route_task_to_peerhub,
)
from shiro.util.telemetry import OtelConfig, observe, set_up_otel

set_up_otel(
    OtelConfig(
        otel_collector_endpoint=HttpUrl("http://otel-collector:4317"),
        otel_service_name="broker_client",
    )
)

# `set_up_otel` before `define_broker`.

broker = define_broker(
    BrokerConfigForClient(
        broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
        result_backend_url=RedisDsn("redis://localhost:6379/0"),
    )
)

_ = broker.startup()

# import tasks after define_broker was called
# kiq tasks after broker startup

from shiro.peerhub.models import Peer
from shiro.peerhub.tasks import get_peer


@observe("client.main")
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
