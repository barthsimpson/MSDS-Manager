"""Application-facing ports for the future BHP decision workflow."""

from typing import Protocol

from app.application.dto import (
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)


class BhpEvidenceValidatorPort(Protocol):
    def validate(self, evidence_relative_path: str) -> str:
        """Validate and return the normalized relative evidence path."""


class BhpDecisionRepositoryPort(Protocol):
    def register(
        self, data: RegisterBhpDecisionInput
    ) -> RegisterBhpDecisionResult:
        """Atomically register one decision and its evidence reference."""