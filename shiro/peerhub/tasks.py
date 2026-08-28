# pyright: reportUnusedParameter=false

__all__ = [
    "get_peer",
    "add_peer",
    "enable_peer",
    "disable_peer",
    "delete_peer",
    "get_config",
]

from uuid import UUID

from .broker import declare_task
from .models import Peer, PeerAdd, Success


@declare_task(task_name="peerhub.get_peer")
async def get_peer(id: UUID) -> Peer: ...


@declare_task(task_name="peerhub.add_peer")
async def add_peer(peer_data: PeerAdd) -> Peer: ...


@declare_task(task_name="peerhub.enable_peer")
async def enable_peer(id: UUID) -> Success: ...


@declare_task(task_name="peerhub.disable_peer")
async def disable_peer(id: UUID) -> Success: ...


@declare_task(task_name="peerhub.delete_peer")
async def delete_peer(id: UUID) -> Success: ...


@declare_task(task_name="peerhub.get_config")
async def get_config(id: UUID) -> str: ...
