"""Controlled legacy usage-location code assignment contract."""

import pytest

from app.application.dto import AssignLegacyUsageLocationCodeInput
from app.application.exceptions import (
    DuplicateLocationCodeError,
    EntityNotFoundError,
    LocationCodeAlreadyAssignedError,
)
from app.application.use_cases import AssignLegacyUsageLocationCode
from app.domain.enums import UsageLocationStatus
from app.domain.models import UsageLocation


class FakeRepository:
    def __init__(self, *locations: UsageLocation) -> None:
        self.locations = {location.location_id: location for location in locations}
        self.assigned: list[tuple[str, str]] = []
        self.update_succeeds = True

    def get_by_id(self, location_id: str) -> UsageLocation | None:
        return self.locations.get(location_id)

    def get_by_code(self, location_code: str) -> UsageLocation | None:
        return next((row for row in self.locations.values()
                     if row.location_code == location_code), None)

    def assign_legacy_code(self, location_id: str, location_code: str) -> bool:
        if not self.update_succeeds:
            return False
        location = self.locations[location_id]
        self.locations[location_id] = UsageLocation(
            location.location_id, location.location_name, location.status, location_code
        )
        self.assigned.append((location_id, location_code))
        return True


def test_assign_only_selected_legacy_row_and_preserve_lifecycle() -> None:
    target = UsageLocation("target", "Workshop", UsageLocationStatus.INACTIVE)
    other = UsageLocation("other", "Store", location_code="STORE")
    repository = FakeRepository(target, other)

    result = AssignLegacyUsageLocationCode(repository).execute(
        AssignLegacyUsageLocationCodeInput("target", " mzt ")
    )

    assert result == UsageLocation("target", "Workshop", UsageLocationStatus.INACTIVE, "MZT")
    assert repository.assigned == [("target", "MZT")]
    assert repository.get_by_id("other") == other
    assert result.reactivate().location_code == "MZT"


@pytest.mark.parametrize("code", ["", "  ", "-MZT", "mzt space", "Ą", "A" * 33])
def test_assign_rejects_invalid_code(code: str) -> None:
    repository = FakeRepository(UsageLocation("legacy", "Line"))
    with pytest.raises(ValueError, match="location_code"):
        AssignLegacyUsageLocationCode(repository).execute(
            AssignLegacyUsageLocationCodeInput("legacy", code)
        )
    assert repository.assigned == []


def test_assign_rejects_missing_duplicate_and_existing_code() -> None:
    repository = FakeRepository(
        UsageLocation("legacy", "Line"),
        UsageLocation("coded", "Other", location_code="MZT"),
    )
    use_case = AssignLegacyUsageLocationCode(repository)
    with pytest.raises(EntityNotFoundError):
        use_case.execute(AssignLegacyUsageLocationCodeInput("missing", "NEW"))
    with pytest.raises(DuplicateLocationCodeError):
        use_case.execute(AssignLegacyUsageLocationCodeInput("legacy", "mzt"))
    with pytest.raises(LocationCodeAlreadyAssignedError):
        use_case.execute(AssignLegacyUsageLocationCodeInput("coded", "NEW"))
    assert repository.assigned == []


def test_assign_rejects_concurrent_change() -> None:
    repository = FakeRepository(UsageLocation("legacy", "Line"))
    repository.update_succeeds = False
    with pytest.raises(LocationCodeAlreadyAssignedError):
        AssignLegacyUsageLocationCode(repository).execute(
            AssignLegacyUsageLocationCodeInput("legacy", "NEW")
        )
    assert repository.assigned == []
