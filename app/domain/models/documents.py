"""SDS document, BHP decision, and decision evidence domain models."""

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    SdsDocumentStatus,
)


@dataclass(frozen=True, slots=True)
class SdsDocument:
    sds_id: str
    product_id: str
    original_filename: str
    relative_path: str
    document_status: SdsDocumentStatus
    registered_at: datetime
    file_status: FileAvailabilityStatus
    issue_date: date | None = None
    revision: str | None = None


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    evidence_id: str
    relative_path: str
    evidence_type: EvidenceType
    file_format: EvidenceFileFormat
    file_status: FileAvailabilityStatus


@dataclass(frozen=True, slots=True)
class BhpDecision:
    decision_id: str
    product_id: str
    sds_id: str
    decision_status: BhpDecisionStatus
    registered_at: datetime
    record_status: DecisionRecordStatus
    evidence_id: str
    notes: str | None = None
