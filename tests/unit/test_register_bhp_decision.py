from datetime import datetime, timezone

import pytest

from app.application.dto import (
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)
from app.application.exceptions import BhpDecisionValidationError
from app.application.use_cases import RegisterBhpDecision
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus


class FakeEvidenceValidator:
    def __init__(self, normalized_path: str = "evidence/decision.pdf") -> None:
        self.normalized_path = normalized_path
        self.paths: list[str] = []
        self.error: Exception | None = None

    def validate(self, evidence_relative_path: str) -> str:
        self.paths.append(evidence_relative_path)
        if self.error is not None:
            raise self.error
        return self.normalized_path


class FakeBhpDecisionRepository:
    def __init__(self) -> None:
        self.inputs: list[RegisterBhpDecisionInput] = []
        self.result = RegisterBhpDecisionResult(
            decision_id="decision-1",
            product_id="product-1",
            sds_id="sds-1",
            decision_status=BhpDecisionStatus.APPROVED,
            product_usage_status=ProductUsageStatus.ACTIVE,
            registered_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
            evidence_relative_path="evidence/decision.pdf",
        )
        self.error: Exception | None = None

    def register(self, data: RegisterBhpDecisionInput) -> RegisterBhpDecisionResult:
        self.inputs.append(data)
        if self.error is not None:
            raise self.error
        return self.result


def decision_input(status: BhpDecisionStatus) -> RegisterBhpDecisionInput:
    return RegisterBhpDecisionInput(
        product_id="product-1",
        sds_id="sds-1",
        decision_status=status,
        evidence_relative_path="incoming/decision.pdf",
        notes="  Reviewed by BHP  ",
    )


@pytest.mark.parametrize(
    "status",
    [BhpDecisionStatus.APPROVED, BhpDecisionStatus.REJECTED],
)
def test_register_bhp_decision_validates_evidence_and_delegates(status) -> None:
    validator = FakeEvidenceValidator()
    repository = FakeBhpDecisionRepository()

    result = RegisterBhpDecision(validator, repository).execute(decision_input(status))

    assert result.decision_id == "decision-1"
    assert validator.paths == ["incoming/decision.pdf"]
    assert len(repository.inputs) == 1
    assert repository.inputs[0].decision_status is status
    assert repository.inputs[0].evidence_relative_path == "evidence/decision.pdf"
    assert repository.inputs[0].notes == "Reviewed by BHP"


def test_invalid_status_does_not_call_validator_or_repository() -> None:
    validator = FakeEvidenceValidator()
    repository = FakeBhpDecisionRepository()
    data = decision_input(BhpDecisionStatus.APPROVED)
    data = RegisterBhpDecisionInput(
        product_id=data.product_id,
        sds_id=data.sds_id,
        decision_status="PENDING",  # type: ignore[arg-type]
        evidence_relative_path=data.evidence_relative_path,
        notes=data.notes,
    )

    with pytest.raises(BhpDecisionValidationError):
        RegisterBhpDecision(validator, repository).execute(data)

    assert validator.paths == []
    assert repository.inputs == []


def test_missing_evidence_path_does_not_call_repository() -> None:
    validator = FakeEvidenceValidator()
    repository = FakeBhpDecisionRepository()
    data = decision_input(BhpDecisionStatus.APPROVED)
    data = RegisterBhpDecisionInput(
        product_id=data.product_id,
        sds_id=data.sds_id,
        decision_status=data.decision_status,
        evidence_relative_path="   ",
        notes=data.notes,
    )

    with pytest.raises(BhpDecisionValidationError):
        RegisterBhpDecision(validator, repository).execute(data)

    assert validator.paths == []
    assert repository.inputs == []


def test_validator_error_is_propagated_and_repository_is_not_called() -> None:
    validator = FakeEvidenceValidator()
    validator.error = ValueError("evidence is outside root")
    repository = FakeBhpDecisionRepository()

    with pytest.raises(ValueError, match="outside root"):
        RegisterBhpDecision(validator, repository).execute(
            decision_input(BhpDecisionStatus.REJECTED)
        )

    assert repository.inputs == []


def test_persistence_error_is_propagated_without_false_success() -> None:
    validator = FakeEvidenceValidator()
    repository = FakeBhpDecisionRepository()
    repository.error = RuntimeError("database failure")

    with pytest.raises(RuntimeError, match="database failure"):
        RegisterBhpDecision(validator, repository).execute(
            decision_input(BhpDecisionStatus.APPROVED)
        )