import pytest

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SafetyInformationStatus,
    SdsDocumentStatus,
)


@pytest.mark.parametrize(
    ("enum_type", "expected_values"),
    [
        (
            ProductUsageStatus,
            ["PENDING_APPROVAL", "ACTIVE", "REJECTED", "INACTIVE"],
        ),
        (SdsDocumentStatus, ["CURRENT", "ARCHIVED"]),
        (FileAvailabilityStatus, ["AVAILABLE", "MISSING"]),
        (BhpDecisionStatus, ["APPROVED", "REJECTED"]),
        (DecisionRecordStatus, ["CURRENT", "SUPERSEDED"]),
        (SafetyInformationStatus, ["YES", "NO", "NO_DATA", "NOT_APPLICABLE"]),
        (EvidenceType, ["EMAIL", "DOCUMENT", "PHOTO_SCAN"]),
        (EvidenceFileFormat, ["MSG", "PDF", "JPG", "JPEG", "PNG"]),
    ],
)
def test_enum_values_are_exact(enum_type, expected_values: list[str]) -> None:
    assert [member.value for member in enum_type] == expected_values


def test_safety_no_data_is_distinct_from_no() -> None:
    assert SafetyInformationStatus.NO_DATA is not SafetyInformationStatus.NO


def test_bhp_decision_has_no_pending_status() -> None:
    assert "PENDING" not in BhpDecisionStatus.__members__


def test_decision_record_supports_current_and_superseded() -> None:
    assert DecisionRecordStatus.CURRENT.value == "CURRENT"
    assert DecisionRecordStatus.SUPERSEDED.value == "SUPERSEDED"
