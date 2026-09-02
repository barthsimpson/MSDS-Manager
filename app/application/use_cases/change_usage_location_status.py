"""Use cases for approved usage-location lifecycle transitions."""

from app.application.exceptions import EntityNotFoundError
from app.application.ports import UsageLocationRepositoryPort
from app.domain.models import UsageLocation


class DeactivateUsageLocation:
    def __init__(self, repository: UsageLocationRepositoryPort) -> None:
        self._repository = repository

    def execute(self, location_id: str) -> UsageLocation:
        location = self._repository.get_by_id(location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", location_id)
        inactive_location = location.deactivate()
        self._repository.update_status(inactive_location)
        return inactive_location


class ReactivateUsageLocation:
    def __init__(self, repository: UsageLocationRepositoryPort) -> None:
        self._repository = repository

    def execute(self, location_id: str) -> UsageLocation:
        location = self._repository.get_by_id(location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", location_id)
        active_location = location.reactivate()
        self._repository.update_status(active_location)
        return active_location
