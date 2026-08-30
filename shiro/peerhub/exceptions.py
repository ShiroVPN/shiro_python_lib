__all__ = ["peer_not_found", "peer_exists"]


from uuid import UUID


class peer_not_found(Exception):
    peer_id: UUID

    def __init__(self, peer_id: UUID) -> None:
        self.peer_id = peer_id
        super().__init__(f"Peer not found: id = {peer_id}")


class peer_exists(Exception):
    peer_id: UUID

    def __init__(self, peer_id: UUID) -> None:
        self.peer_id = peer_id
        super().__init__(f"Peer exists: id = {peer_id}")
