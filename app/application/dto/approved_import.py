"""Explicit human decisions for one controlled Evidence JSON import."""

from dataclasses import dataclass
from datetime import date

from app.application.dto.sds import SdsSafetyProfileDraft


@dataclass(frozen=True, slots=True)
class IdentityDecision:
    action: str
    name: str
    selected_id: str | None = None
    manufacturer_product_code: str | None = None
    null_code_link_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class HumanApproval:
    approved_by: str
    manufacturer_confirmed: bool
    product_confirmed: bool
    manual_inputs_confirmed: bool
    safety_confirmed: bool
    pdf_confirmed: bool


@dataclass(frozen=True, slots=True)
class ApprovedImportPlan:
    source_json_fingerprint: str
    document_key: str
    source_filename: str
    manufacturer_decision: IdentityDecision
    product_decision: IdentityDecision
    expected_manufacturer_candidates: tuple[str, ...]
    expected_product_candidates: tuple[str, ...]
    expected_product_codes: tuple[tuple[str, str | None], ...]
    issue_date: date | None
    revision: str | None
    original_filename: str
    use_description: str
    use_restriction: str
    safety_profile: SdsSafetyProfileDraft
    safety_fingerprint: str
    pdf_fingerprint: str
    human_approval: HumanApproval
