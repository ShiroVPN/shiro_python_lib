__all__ = [
    "Peer",
    "PeerAdd",
    "Success",
    "WgConfig",
    "XuiConfig",
]

from uuid import UUID

from pydantic import BaseModel


class PeerAdd(BaseModel):
    name: str
    id: UUID


class Peer(BaseModel):
    id: UUID
    name: str
    enabled: bool


class Success(BaseModel):
    ok: bool = True


class WgConfig(BaseModel):
    """`peerhub.get_config` answered by a wg-easy peerhub: `.conf` body."""

    config: str


class XuiConfig(BaseModel):
    """`peerhub.get_config` answered by a 3x-ui peerhub: subscription URL."""

    sub_url: str
