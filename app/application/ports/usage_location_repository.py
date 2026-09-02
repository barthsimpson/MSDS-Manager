"""Application-facing persistence needs for usage locations."""

from typing import Protocol

from app.domain.models import UsageLocation


class UsageLocationRepositoryPort(Protocol):
    def list_all(self) -> list[UsageLocation]: ...

    def get_by_id(self, location_id: str) -> UsageLocation | None: ...

    def add(self, location: UsageLocation) -> None: ...

    def update_status(self, location: UsageLocation) -> None: ...
