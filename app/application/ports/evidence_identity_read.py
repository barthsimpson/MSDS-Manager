"""Read-only identity queries for Evidence JSON planning."""

from typing import Protocol

from app.application.dto.evidence_json import IdentityRecord


class EvidenceIdentityReadPort(Protocol):
    def manufacturers_named(self, name: str) -> tuple[IdentityRecord, ...]: ...

    def similar_manufacturers(self, name: str) -> tuple[IdentityRecord, ...]: ...

    def products_named(self, name: str) -> tuple[IdentityRecord, ...]: ...

    def products_for_manufacturer(
        self, name: str, manufacturer_id: str, code: str | None
    ) -> tuple[IdentityRecord, ...]: ...
