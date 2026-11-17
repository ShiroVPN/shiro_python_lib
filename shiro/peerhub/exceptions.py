__all__ = ["peer_not_found", "peer_exists"]


from typing import ClassVar
from uuid import UUID

from shiro.util.errors import ErrorCode


class peer_not_found(Exception):
    peer_id: UUID
    error_code: ClassVar[ErrorCode] = ErrorCode.PEER_NOT_FOUND

    def __init__(self, peer_id: UUID) -> None:
        self.peer_id = peer_id
        super().__init__(f"Peer not found: id = {peer_id}")


class peer_exists(Exception):
    peer_id: UUID
    error_code: ClassVar[ErrorCode] = ErrorCode.PEER_EXISTS

    def __init__(self, peer_id: UUID) -> None:
        self.peer_id = peer_id
        super().__init__(f"Peer exists: id = {peer_id}")
