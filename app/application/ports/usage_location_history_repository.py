"""Application-facing persistence for usage-location history snapshots."""

from typing import Protocol

from app.domain.models import UsageLocationHistory


class UsageLocationHistoryRepositoryPort(Protocol):
    def add(self, snapshot: UsageLocationHistory) -> None: ...

    def get_by_location_id(self, location_id: str) -> list[UsageLocationHistory]: ...
