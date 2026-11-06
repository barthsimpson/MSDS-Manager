"""Validate the explicit operator choice before one atomic invalidation."""

from typing import Protocol

from app.application.dto.sds_invalidation import InvalidateSdsInput
from app.domain.enums import SdsDocumentStatus


class SdsInvalidationPort(Protocol):
    def invalidate(self, data: InvalidateSdsInput) -> str: ...


class InvalidateSds:
    def __init__(self, repository: SdsInvalidationPort) -> None:
        self._repository = repository

    def execute(self, data: InvalidateSdsInput) -> str:
        if not data.product_id or not data.invalidated_sds_id:
            raise ValueError("Produkt i SDS są wymagane.")
        if not data.reason or not data.reason.strip():
            raise ValueError("Podaj powód wycofania SDS.")
        if data.expected_status is SdsDocumentStatus.CURRENT:
            if data.expected_current_sds_id != data.invalidated_sds_id:
                raise ValueError("STALE_STATE: bieżący SDS zmienił się.")
            if data.mode == "RESTORE_ARCHIVED":
                if not data.restored_sds_id or data.restored_sds_id == data.invalidated_sds_id:
                    raise ValueError("Wybierz konkretny ARCHIVED SDS do przywrócenia.")
            elif data.mode == "NO_CURRENT":
                if data.restored_sds_id is not None:
                    raise ValueError("Wariant bez CURRENT nie przyjmuje zamiennika.")
            else:
                raise ValueError("Wybierz sposób wycofania bieżącego SDS.")
        elif data.expected_status is SdsDocumentStatus.ARCHIVED:
            if data.mode != "ARCHIVED_ONLY" or data.restored_sds_id is not None:
                raise ValueError("ARCHIVED SDS nie wymaga zamiennika.")
        else:
            raise ValueError("Wycofać można tylko CURRENT lub ARCHIVED SDS.")
        return self._repository.invalidate(data)
