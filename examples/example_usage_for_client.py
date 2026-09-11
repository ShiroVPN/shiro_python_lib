from uuid import uuid4

from pydantic import AmqpDsn, HttpUrl, RedisDsn

from shiro.peerhub.broker import (
    BrokerConfigForClient,
    define_broker,
    route_task_to_peerhub,
)
from shiro.util.env import EnvConfig
from shiro.util.tasks import TaskRunner
from shiro.util.telemetry import OtelConfig, observe, set_up_otel


class MyEnvConfig(EnvConfig):
    worker_wait_result_timeout: float = 0.1
    worker_wait_result_check_interval: float = 0.01


env_config = MyEnvConfig(
    broker_url=AmqpDsn("amqp://user:password@localhost:5672"),
    broker_result_backend_url=RedisDsn("redis://localhost:6379/0"),
    otel_collector_endpoint=HttpUrl("http://otel-collector:4317"),
    otel_service_name="broker_client",
)

set_up_otel(
    OtelConfig(
        otel_collector_endpoint=env_config.otel_collector_endpoint,
        otel_service_name=env_config.otel_service_name,
    )
)

# `set_up_otel` before `define_broker`.

broker = define_broker(
    BrokerConfigForClient(
        broker_url=env_config.broker_url,
        result_backend_url=env_config.broker_result_backend_url,
    )
)

_ = broker.startup()

# import tasks after define_broker was called
# kiq tasks after broker startup

from shiro.peerhub.models import Peer
from shiro.peerhub.tasks import get_peer

task_sender = TaskRunner(
    wait_result_timeout=env_config.worker_wait_result_timeout,
    wait_result_check_interval=env_config.worker_wait_result_check_interval,
)


@observe("client.main")
async def main():
    peerhub_id = uuid4()
    peer_id = uuid4()

    routed_get_peer = route_task_to_peerhub(get_peer, peerhub_id)

    runner = task_sender.runner(routed_get_peer)
    peer: Peer = await runner.send(peer_id)

    print(peer)


if __name__ == "__main__":
    print("Success!")
