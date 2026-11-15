__all__ = [
    "Peer",
    "PeerAdd",
    "PeerUsage",
    "Success",
    "WgConfig",
    "XuiConfig",
]

from uuid import UUID

from heliclockter import datetime_utc
from pydantic import BaseModel, Field


class PeerAdd(BaseModel):
    name: str
    id: UUID


class Peer(BaseModel):
    id: UUID
    name: str
    enabled: bool


class PeerUsage(BaseModel):
    """Items of `peerhub.get_usage`: the node's live counters for one peer."""

    id: UUID
    enabled: bool
    rx: int = Field(ge=0)
    tx: int = Field(ge=0)
    latest_handshake_at: datetime_utc | None


class Success(BaseModel):
    ok: bool = True


class WgConfig(BaseModel):
    """`peerhub.get_config` answered by a wg-easy peerhub: `.conf` body."""

    config: str


class XuiConfig(BaseModel):
    """`peerhub.get_config` answered by a 3x-ui peerhub: subscription URL."""

    sub_url: str
