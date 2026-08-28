# Peerhub python module

This is a python pkg that declares `peerhub` workers. It is used in `main_api` to manage peers and in `peerhub workers` to execute tasks.

This module: `shiro.peerhub`.

# Broker

Module: `.broker`.

Broker configs:

| Name                    | Fields                                                       |
| ----------------------- | ------------------------------------------------------------ |
| `BrokerConfigForClient` | `broker_url: AmqpDsn`<br/>`result_backend_url: RedisDsn`<br/>`exchange_name: str` |
| `BrokerConfigForWorker` | `BrokerConfigForClient`<br/>+ `queue_name: str`<br/>+ `peerhub_id: UUID` (to route to `peerhub`) |

IMPORTANT: call `.broker.define_broker` before importing `.tasks`.

To route task to `peerhub` use `.broker.route_task_to_peerhub(task, peerhub_id: UUID)`.

# Models

Module: `.models`

| Name      | Fields                                         |
| --------- | ---------------------------------------------- |
| `Peer`    | `id: UUID`<br/>`name: str`<br/>`enabled: bool` |
| `PeerAdd` | `name: str`<br/>`id: UUID`                     |
| `Success` | `ok: bool = True`                              |

# Tasks

Module: `.tasks`

| Name                   | Input     | Output    |
| ---------------------- | --------- | --------- |
| `peerhub.get_peer`     | `UUID`    | `Peer`    |
| `peerhub.add_peer`     | `PeerAdd` | `Peer`    |
| `peerhub.enable_peer`  | `UUID`    | `Success` |
| `peerhub.disable_peer` | `UUID`    | `Success` |
| `peerhub.delete_peer`  | `UUID`    | `Success` |
| `peerhub.get_config`   | `UUID`    | `str`     |

# Exceptions

Module: `.exceptions`

| Name             | Description                                 |
| ---------------- | ------------------------------------------- |
| `peer_not_found` | Raised if peer with given id was not found. |
