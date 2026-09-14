"""Application boundary for registering a future BHP decision."""

from app.application.dto import (
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)
from app.application.exceptions import BhpDecisionValidationError
from app.application.ports import BhpDecisionRepositoryPort, BhpEvidenceValidatorPort
from app.domain.enums import BhpDecisionStatus


class RegisterBhpDecision:
    def __init__(
        self,
        evidence_validator: BhpEvidenceValidatorPort,
        repository: BhpDecisionRepositoryPort,
    ) -> None:
        self._evidence_validator = evidence_validator
        self._repository = repository

    def execute(self, data: RegisterBhpDecisionInput) -> RegisterBhpDecisionResult:
        self._validate(data)
        normalized_evidence_path = self._evidence_validator.validate(
            data.evidence_relative_path
        )
        validated_data = RegisterBhpDecisionInput(
            product_id=data.product_id,
            sds_id=data.sds_id,
            decision_status=data.decision_status,
            evidence_relative_path=normalized_evidence_path,
            notes=data.notes.strip() or None if data.notes is not None else None,
        )
        return self._repository.register(validated_data)

    @staticmethod
    def _validate(data: RegisterBhpDecisionInput) -> None:
        if not data.product_id.strip():
            raise BhpDecisionValidationError("product_id is required.")
        if not data.sds_id.strip():
            raise BhpDecisionValidationError("sds_id is required.")
        if not data.evidence_relative_path.strip():
            raise BhpDecisionValidationError("evidence_relative_path is required.")
        if not isinstance(data.decision_status, BhpDecisionStatus):
            raise BhpDecisionValidationError(
                "decision_status must be APPROVED or REJECTED."
            )