"""Application orchestration for BHP evidence import and read access."""

from collections.abc import Callable, Mapping

from app.application.dto import (
    BhpEvidenceOption,
    NewBhpDecisionInput,
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)
from app.application.ports import BhpEvidenceStoragePort
from app.application.use_cases.register_bhp_decision import RegisterBhpDecision


class BhpEvidenceCleanupError(RuntimeError):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        super().__init__(f"Zapis decyzji nieudany; osierocony plik dowodu: {relative_path}")


class ImportBhpEvidence:
    def __init__(self, storage: BhpEvidenceStoragePort) -> None:
        self._storage = storage

    def execute(
        self,
        data: NewBhpDecisionInput,
        verify_scope: Callable[[str, str], None],
        register: Callable[[RegisterBhpDecisionInput], RegisterBhpDecisionResult],
    ) -> RegisterBhpDecisionResult:
        pending = RegisterBhpDecisionInput(
            product_id=data.product_id,
            sds_id=data.sds_id,
            decision_status=data.decision_status,
            evidence_relative_path="pending.pdf",
            notes=data.notes,
            original_filename=data.original_filename,
        )
        RegisterBhpDecision._validate(pending)
        verify_scope(data.product_id, data.sds_id)
        self._storage.validate_new_evidence(data.original_filename, data.content)
        relative_path = self._storage.store_new_evidence(data.original_filename, data.content)
        try:
            self._storage.confirm_exists(relative_path)
            return register(RegisterBhpDecisionInput(
                product_id=data.product_id,
                sds_id=data.sds_id,
                decision_status=data.decision_status,
                evidence_relative_path=relative_path,
                notes=data.notes,
                original_filename=data.original_filename,
            ))
        except Exception:
            try:
                self._storage.remove_unregistered_evidence(relative_path)
            except Exception as cleanup_error:
                raise BhpEvidenceCleanupError(relative_path) from cleanup_error
            raise


class ListBhpEvidence:
    def __init__(self, storage: BhpEvidenceStoragePort) -> None:
        self._storage = storage

    def execute(self, registered_names: Mapping[str, str | None]) -> tuple[BhpEvidenceOption, ...]:
        return tuple(
            BhpEvidenceOption(relative_path=path, original_filename=registered_names.get(path) or name)
            for path, name in self._storage.list_existing_evidence()
            if not path.startswith("imported/") or path in registered_names
        )


class ReadBhpEvidence:
    def __init__(self, storage: BhpEvidenceStoragePort) -> None:
        self._storage = storage

    def execute(self, relative_path: str) -> bytes:
        return self._storage.read_existing_evidence(relative_path)

    def available(self, relative_path: str) -> bool:
        return self._storage.check_availability(relative_path)
