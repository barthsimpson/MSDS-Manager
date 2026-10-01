"""Application contracts for registering BHP decisions."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import BhpDecisionStatus, DecisionRecordStatus, ProductUsageStatus


@dataclass(frozen=True, slots=True)
class RegisterBhpDecisionInput:
    product_id: str
    sds_id: str
    decision_status: BhpDecisionStatus
    evidence_relative_path: str
    notes: str | None = None
    original_filename: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterBhpDecisionResult:
    decision_id: str
    product_id: str
    sds_id: str
    decision_status: BhpDecisionStatus
    product_usage_status: ProductUsageStatus
    registered_at: datetime
    evidence_relative_path: str


@dataclass(frozen=True, slots=True)
class BhpDecisionProduct:
    product_id: str
    product_name: str
    manufacturer_product_code: str
    manufacturer_name: str
    usage_status: ProductUsageStatus
    sds_id: str
    sds_filename: str
    sds_issue_date: object | None
    sds_revision: str | None


@dataclass(frozen=True, slots=True)
class CurrentBhpDecision:
    decision_status: BhpDecisionStatus
    registered_at: datetime
    notes: str | None
    evidence_relative_path: str
    evidence_original_filename: str | None = None


@dataclass(frozen=True, slots=True)
class NewBhpDecisionInput:
    product_id: str
    sds_id: str
    decision_status: BhpDecisionStatus
    original_filename: str
    content: bytes
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class BhpEvidenceOption:
    relative_path: str
    original_filename: str


@dataclass(frozen=True, slots=True)
class BhpDecisionHistoryItem:
    decision_id: str
    decision_status: BhpDecisionStatus
    record_status: DecisionRecordStatus
    registered_at: datetime
    notes: str | None
    evidence_relative_path: str
    evidence_original_filename: str | None
