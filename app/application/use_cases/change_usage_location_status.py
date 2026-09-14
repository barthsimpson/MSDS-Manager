"""Use cases for approved usage-location lifecycle transitions."""

from datetime import datetime, timezone

from app.application.exceptions import EntityNotFoundError
from app.application.ports import UsageLocationHistoryRepositoryPort, UsageLocationRepositoryPort
from app.domain.models import UsageLocation, UsageLocationHistory


class DeactivateUsageLocation:
    def __init__(
        self,
        repository: UsageLocationRepositoryPort,
        history_repository: UsageLocationHistoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._history_repository = history_repository

    def execute(self, location_id: str) -> UsageLocation:
        location = self._repository.get_by_id(location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", location_id)
        inactive_location = location.deactivate()
        self._repository.update_status(inactive_location)
        if self._history_repository is not None:
            self._history_repository.add(
                UsageLocationHistory(
                    location_id=location_id,
                    status=inactive_location.status,
                    changed_at=datetime.now(timezone.utc),
                )
            )
        return inactive_location


class ReactivateUsageLocation:
    def __init__(
        self,
        repository: UsageLocationRepositoryPort,
        history_repository: UsageLocationHistoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._history_repository = history_repository

    def execute(self, location_id: str) -> UsageLocation:
        location = self._repository.get_by_id(location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", location_id)
        active_location = location.reactivate()
        self._repository.update_status(active_location)
        if self._history_repository is not None:
            self._history_repository.add(
                UsageLocationHistory(
                    location_id=location_id,
                    status=active_location.status,
                    changed_at=datetime.now(timezone.utc),
                )
            )
        return active_location
