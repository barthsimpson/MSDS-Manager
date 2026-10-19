"""Read-only results for an Evidence JSON import dry run."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    record_id: str
    name: str
    manufacturer_product_code: str | None = None


@dataclass(frozen=True, slots=True)
class IdentityResolution:
    status: str
    candidate_ids: tuple[str, ...] = ()
    canonical_name: str | None = None
    similar_records: tuple[IdentityRecord, ...] = ()
    human_confirmation_required: bool = False
    conditional_on_manufacturer: bool = False


@dataclass(frozen=True, slots=True)
class SdsJsonImportPlan:
    document_key: str
    source_filename: str | None
    validation_status: str
    errors: tuple[str, ...]
    mapped_product_name: str | None
    mapped_manufacturer_product_code: str | None
    mapped_issue_date: date | None
    mapped_revision: str | None
    manufacturer_resolution: IdentityResolution
    product_resolution: IdentityResolution
    required_manual_inputs: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    commit_readiness: str
