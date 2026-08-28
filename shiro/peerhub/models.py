__all__ = [
    "Peer",
    "PeerAdd",
    "Success",
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
