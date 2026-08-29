__all__ = ["peer_not_found", "peer_exists"]


from uuid import UUID


class peer_not_found(Exception):
    id: UUID

    def __init__(self, id: UUID) -> None:
        self.id = id
        super().__init__(f"Peer not found: id = {self.id}")


class peer_exists(Exception):
    id: UUID

    def __init__(self, id: UUID) -> None:
        self.id = id
        super().__init__(f"Peer exists: id = {self.id}")
