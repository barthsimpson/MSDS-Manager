"""One-time, user-directed code assignment for a legacy usage location."""

from dataclasses import replace

from app.application.dto import AssignLegacyUsageLocationCodeInput
from app.application.exceptions import (
    DuplicateLocationCodeError,
    EntityNotFoundError,
    LocationCodeAlreadyAssignedError,
)
from app.application.ports import UsageLocationRepositoryPort
from app.application.use_cases.create_usage_location import normalize_location_code
from app.domain.models import UsageLocation


class AssignLegacyUsageLocationCode:
    def __init__(self, repository: UsageLocationRepositoryPort) -> None:
        self._repository = repository

    def execute(self, data: AssignLegacyUsageLocationCodeInput) -> UsageLocation:
        location = self._repository.get_by_id(data.location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", data.location_id)
        if location.location_code is not None:
            raise LocationCodeAlreadyAssignedError(data.location_id)

        location_code = normalize_location_code(data.location_code)
        if self._repository.get_by_code(location_code) is not None:
            raise DuplicateLocationCodeError(location_code)
        if not self._repository.assign_legacy_code(data.location_id, location_code):
            raise LocationCodeAlreadyAssignedError(data.location_id)
        return replace(location, location_code=location_code)
