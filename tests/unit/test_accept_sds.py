from pathlib import Path

import pytest

from app.application.dto import AcceptSdsInput, SdsComponentDraft
from app.application.exceptions import SdsAcceptanceValidationError
from app.application.use_cases import AcceptSds
from app.domain.enums import SafetyInformationStatus


class FakeValidator:
    def validate_relative(self, relative_path: str) -> Path:
        return Path(relative_path)


class FakeRepository:
    def __init__(self) -> None:
        self.received = None

    def accept(self, data: AcceptSdsInput) -> str:
        self.received = data
        return "sds-id"


def valid_input() -> AcceptSdsInput:
    return AcceptSdsInput(
        source_relative_path="incoming/test.pdf",
        product_name="Product",
        manufacturer_product_code="P-1",
        manufacturer_name="Manufacturer",
        use_description="Use",
        use_restriction="Restriction",
        detected_language="PL",
        language_valid=True,
        components=[SdsComponentDraft(component_name="Component")],
    )


def test_accept_sds_validates_and_delegates() -> None:
    repository = FakeRepository()

    result = AcceptSds(repository, FakeValidator()).execute(valid_input())

    assert result == "sds-id"
    assert repository.received is not None


@pytest.mark.parametrize(
    "change",
    [
        lambda data: setattr(data, "detected_language", "EN"),
        lambda data: setattr(data.safety_profile, "pbt_status", "NO"),
        lambda data: setattr(data.components[0], "component_name", None),
    ],
)
def test_accept_sds_rejects_invalid_input(change) -> None:
    data = valid_input()
    change(data)

    with pytest.raises(SdsAcceptanceValidationError):
        AcceptSds(FakeRepository(), FakeValidator()).execute(data)


def test_missing_safety_status_is_allowed_for_manual_fallback() -> None:
    data = valid_input()
    data.safety_profile.pbt_status = SafetyInformationStatus.NO_DATA

    AcceptSds(FakeRepository(), FakeValidator()).execute(data)