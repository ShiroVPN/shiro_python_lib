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
    id: UUID
    enabled: bool
    rx: int = Field(ge=0)
    tx: int = Field(ge=0)
    latest_handshake_at: datetime_utc | None


class Success(BaseModel):
    ok: bool = True


class WgConfig(BaseModel):
    config: str


class XuiConfig(BaseModel):
    sub_url: str
