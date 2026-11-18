# pyright: reportUnusedParameter=false

__all__ = [
    "PEERHUB_TASK_PREFIX",
    "PeerhubTaskName",
    "get_peer",
    "add_peer",
    "enable_peer",
    "disable_peer",
    "delete_peer",
    "get_config",
    "get_usage",
]

from enum import StrEnum
from uuid import UUID

from shiro.util.tasks import get_declare_task_wrapper

from .models import Peer, PeerAdd, PeerUsage, Success, WgConfig, XuiConfig

PEERHUB_TASK_PREFIX = "peerhub"


class PeerhubTaskName(StrEnum):
    get_peer = "get_peer"
    add_peer = "add_peer"
    enable_peer = "enable_peer"
    disable_peer = "disable_peer"
    delete_peer = "delete_peer"
    get_config = "get_config"
    get_usage = "get_usage"


declare_peerhub_task = get_declare_task_wrapper(PEERHUB_TASK_PREFIX)


@declare_peerhub_task(PeerhubTaskName.get_peer)
async def get_peer(id: UUID) -> Peer: ...


@declare_peerhub_task(PeerhubTaskName.add_peer)
async def add_peer(peer_data: PeerAdd) -> Peer: ...


@declare_peerhub_task(PeerhubTaskName.enable_peer)
async def enable_peer(id: UUID) -> Success: ...


@declare_peerhub_task(PeerhubTaskName.disable_peer)
async def disable_peer(id: UUID) -> Success: ...


@declare_peerhub_task(PeerhubTaskName.delete_peer)
async def delete_peer(id: UUID) -> Success: ...


@declare_peerhub_task(PeerhubTaskName.get_config)
async def get_config(id: UUID) -> WgConfig | XuiConfig: ...


@declare_peerhub_task(PeerhubTaskName.get_usage)
async def get_usage() -> list[PeerUsage]: ...
