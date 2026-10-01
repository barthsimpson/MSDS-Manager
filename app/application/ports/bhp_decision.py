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


class BhpEvidenceStoragePort(Protocol):
    def list_existing_evidence(self) -> tuple[tuple[str, str], ...]: ...

    def validate_new_evidence(self, original_filename: str, content: bytes) -> str: ...

    def store_new_evidence(self, original_filename: str, content: bytes) -> str: ...

    def confirm_exists(self, relative_path: str) -> None: ...

    def remove_unregistered_evidence(self, relative_path: str) -> None: ...

    def resolve_existing_evidence_path(self, relative_path: str) -> str: ...

    def read_existing_evidence(self, relative_path: str) -> bytes: ...

    def check_availability(self, relative_path: str) -> bool: ...
