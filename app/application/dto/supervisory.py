"""Application DTO for the supervisory read model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import BhpDecisionStatus, ProductUsageStatus


@dataclass(frozen=True, slots=True)
class SupervisoryProductRow:
    product_id: str
    product_name: str
    manufacturer_name: str
    manufacturer_product_code: str
    usage_status: ProductUsageStatus
    use_description: str
    use_restriction: str
    usage_locations: tuple[str, ...]
    current_sds_id: str | None
    current_sds_filename: str | None
    current_sds_issue_date: date | None
    current_sds_revision: str | None
    current_sds_file_available: bool
    current_bhp_decision_id: str | None
    current_bhp_decision_status: BhpDecisionStatus | None
    current_bhp_registered_at: datetime | None
    current_bhp_notes: str | None
    current_bhp_evidence_relative_path: str | None
    current_bhp_evidence_available: bool
    # The query supplies facts; ListSupervisoryProducts assesses them.
    requires_action: bool = False
    action_reasons: tuple[str, ...] = ()
