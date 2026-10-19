"""Human-approved Evidence JSON import through existing SDS use cases."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from typing import Callable, Protocol

from app.application.dto.approved_import import ApprovedImportPlan, HumanApproval, IdentityDecision
from app.application.dto.sds import AcceptSdsInput, AddSdsRevisionInput, SdsSafetyProfileDraft
from app.application.ports.evidence_identity_read import EvidenceIdentityReadPort
from app.application.use_cases.accept_sds import AcceptSds
from app.application.use_cases.add_sds_revision import AddSdsRevision
from app.application.use_cases.import_sds import ImportSds
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport
from app.domain.enums import SafetyInformationStatus


SAFETY_STATUS_FIELDS = (
    "hazardous_classification_status", "pbt_status", "vpvb_status",
    "carcinogenicity_status", "germ_cell_mutagenicity_status",
    "reproductive_toxicity_status", "endocrine_section_2_status",
    "endocrine_section_11_status", "skin_sensitization_status",
    "respiratory_sensitization_status",
)


class ImportPlanError(ValueError):
    """A controlled import cannot proceed with this approval or source."""


def _safety_fingerprint(profile: SdsSafetyProfileDraft) -> str:
    encoded = json.dumps(asdict(profile), sort_keys=True, default=lambda value: value.value).encode()
    return sha256(encoded).hexdigest()


def _require_safety(profile: SdsSafetyProfileDraft) -> None:
    if not isinstance(profile, SdsSafetyProfileDraft) or any(
        not isinstance(getattr(profile, field), SafetyInformationStatus)
        for field in SAFETY_STATUS_FIELDS
    ):
        raise ImportPlanError("INCOMPLETE_SAFETY_DATA")


def _chosen_plan(payload: dict, document_key: str, read: EvidenceIdentityReadPort):
    plans = PlanEvidenceJsonImport(read).execute(payload)
    matches = [item for item in plans if item.document_key == document_key]
    if len(matches) != 1 or matches[0].validation_status != "VALID":
        raise ImportPlanError("INVALID_EVIDENCE_JSON")
    return matches[0]


def _require_decisions(
    dry_run, read: EvidenceIdentityReadPort,
    manufacturer: IdentityDecision, product: IdentityDecision,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, str | None], ...]]:
    if (manufacturer.action not in {"CREATE", "LINK"} or product.action not in {"CREATE", "LINK"}
            or product.name != dry_run.mapped_product_name
            or product.manufacturer_product_code != dry_run.mapped_manufacturer_product_code):
        raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    if "MANUFACTURER_PRODUCT_CODE_REQUIRES_HUMAN_REVIEW" in dry_run.blockers:
        raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    if dry_run.manufacturer_resolution.status != "HUMAN_REVIEW":
        if manufacturer.name != dry_run.manufacturer_resolution.canonical_name:
            raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    elif (dry_run.manufacturer_resolution.canonical_name is None
          or not isinstance(manufacturer.name, str) or not manufacturer.name.strip()):
        raise ImportPlanError("MANUFACTURER_REQUIRES_HUMAN_REVIEW")
    manufacturer_ids = tuple(row.record_id for row in read.manufacturers_named(manufacturer.name))
    if manufacturer.action == "CREATE":
        if manufacturer_ids or manufacturer.selected_id is not None:
            raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    elif manufacturer.selected_id not in manufacturer_ids:
        raise ImportPlanError("LINK_TARGET_NOT_APPROVED")
    if product.action == "LINK" and manufacturer.action != "LINK":
        raise ImportPlanError("PRODUCT_LINK_REQUIRES_MANUFACTURER_LINK")
    product_rows = (
        read.products_for_manufacturer(
            product.name, manufacturer.selected_id, product.manufacturer_product_code,
        ) if manufacturer.action == "LINK" else ()
    )
    product_ids = tuple(row.record_id for row in product_rows)
    if product.action == "CREATE":
        if product_ids or product.selected_id is not None:
            raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    elif product.selected_id not in product_ids:
        raise ImportPlanError("LINK_TARGET_NOT_APPROVED")
    if product.action == "LINK" and product.manufacturer_product_code is None and not product.null_code_link_confirmed:
        raise ImportPlanError("NULL_CODE_LINK_CONFIRMATION_REQUIRED")
    return manufacturer_ids, product_ids, tuple(
        (row.record_id, row.manufacturer_product_code) for row in product_rows
    )


def approve_import_plan(
    raw_json: bytes, document_key: str, read: EvidenceIdentityReadPort,
    manufacturer: IdentityDecision, product: IdentityDecision,
    *, use_description: str, use_restriction: str,
    safety_profile: SdsSafetyProfileDraft, original_filename: str,
    pdf_bytes: bytes, approval: HumanApproval,
) -> ApprovedImportPlan:
    """Construct a plan only from explicit human decisions and a fresh dry run."""
    try:
        payload = json.loads(raw_json)
    except (TypeError, ValueError) as error:
        raise ImportPlanError("INVALID_EVIDENCE_JSON") from error
    dry_run = _chosen_plan(payload, document_key, read)
    if "EXTRACTION_VALIDATION_BLOCKED" in dry_run.blockers:
        raise ImportPlanError("INVALID_EVIDENCE_JSON")
    manufacturer_ids, product_ids, product_codes = _require_decisions(
        dry_run, read, manufacturer, product,
    )
    if (not isinstance(approval, HumanApproval) or not approval.approved_by.strip()
            or not all((approval.manufacturer_confirmed, approval.product_confirmed,
                        approval.manual_inputs_confirmed, approval.safety_confirmed,
                        approval.pdf_confirmed))):
        raise ImportPlanError("HUMAN_CONFIRMATION_REQUIRED")
    if not isinstance(use_description, str) or not use_description.strip():
        raise ImportPlanError("PLAN_NOT_READY: use_description")
    if not isinstance(use_restriction, str) or not use_restriction.strip():
        raise ImportPlanError("PLAN_NOT_READY: use_restriction")
    _require_safety(safety_profile)
    if (not isinstance(original_filename, str) or not original_filename.lower().endswith(".pdf")
            or any(character in original_filename for character in ("/", "\\", ":"))
            or original_filename in {".", ".."}
            or not isinstance(pdf_bytes, bytes) or not pdf_bytes.startswith(b"%PDF-")):
        raise ImportPlanError("PDF_REQUIRED")
    return ApprovedImportPlan(
        source_json_fingerprint=sha256(raw_json).hexdigest(), document_key=document_key,
        source_filename=dry_run.source_filename,
        manufacturer_decision=manufacturer, product_decision=product,
        expected_manufacturer_candidates=manufacturer_ids,
        expected_product_candidates=product_ids,
        expected_product_codes=product_codes,
        issue_date=dry_run.mapped_issue_date, revision=dry_run.mapped_revision,
        original_filename=original_filename,
        use_description=use_description.strip(), use_restriction=use_restriction.strip(),
        safety_profile=safety_profile, safety_fingerprint=_safety_fingerprint(safety_profile),
        pdf_fingerprint=sha256(pdf_bytes).hexdigest(), human_approval=approval,
    )


class ControlledRegistrationPort(Protocol):
    def register(self, operation: Callable) -> str: ...
    def verify_product(self, product_id: str) -> None: ...


class ControlledEvidenceImport:
    def __init__(self, registration: ControlledRegistrationPort, import_sds: ImportSds) -> None:
        self._registration = registration
        self._import_sds = import_sds

    def execute(self, plan: ApprovedImportPlan, raw_json: bytes, pdf_bytes: bytes) -> str:
        if sha256(raw_json).hexdigest() != plan.source_json_fingerprint:
            raise ImportPlanError("SOURCE_CHANGED")
        if sha256(pdf_bytes).hexdigest() != plan.pdf_fingerprint:
            raise ImportPlanError("PDF_CHANGED")
        if _safety_fingerprint(plan.safety_profile) != plan.safety_fingerprint:
            raise ImportPlanError("SAFETY_PAYLOAD_CHANGED")
        _require_safety(plan.safety_profile)
        try:
            payload = json.loads(raw_json)
        except (TypeError, ValueError) as error:
            raise ImportPlanError("SOURCE_CHANGED") from error
        if (not isinstance(plan.human_approval, HumanApproval)
                or not plan.human_approval.approved_by.strip() or not all((
            plan.human_approval.manufacturer_confirmed, plan.human_approval.product_confirmed,
            plan.human_approval.manual_inputs_confirmed, plan.human_approval.safety_confirmed,
            plan.human_approval.pdf_confirmed,
        ))):
            raise ImportPlanError("HUMAN_CONFIRMATION_REQUIRED")
        if not plan.use_description.strip() or not plan.use_restriction.strip():
            raise ImportPlanError("PLAN_NOT_READY")

        if plan.product_decision.action == "CREATE":
            registration_data = AcceptSdsInput(
                source_relative_path="", original_filename=plan.original_filename,
                product_name=plan.product_decision.name,
                manufacturer_product_code=plan.product_decision.manufacturer_product_code,
                manufacturer_name=plan.manufacturer_decision.name,
                use_description=plan.use_description, use_restriction=plan.use_restriction,
                issue_date=plan.issue_date, revision=plan.revision,
                safety_profile=plan.safety_profile,
                controlled_manufacturer_decision=plan.manufacturer_decision,
                controlled_product_decision=plan.product_decision,
            )
            verify_product = None
        else:
            registration_data = AddSdsRevisionInput(
                product_id=plan.product_decision.selected_id,
                source_relative_path="", original_filename=plan.original_filename,
                issue_date=plan.issue_date, revision=plan.revision,
                safety_profile=plan.safety_profile,
            )
            verify_product = self._registration.verify_product

        def register(data):
            def operation(read, repository, validator):
                current = _chosen_plan(payload, plan.document_key, read)
                if (current.source_filename != plan.source_filename
                        or current.mapped_product_name != plan.product_decision.name
                        or current.mapped_manufacturer_product_code != plan.product_decision.manufacturer_product_code
                        or current.mapped_issue_date != plan.issue_date
                        or current.mapped_revision != plan.revision):
                    raise ImportPlanError("STALE_RESOLUTION")
                try:
                    manufacturer_ids, product_ids, product_codes = _require_decisions(
                        current, read, plan.manufacturer_decision, plan.product_decision,
                    )
                except ImportPlanError as error:
                    raise ImportPlanError("STALE_RESOLUTION") from error
                if (manufacturer_ids != plan.expected_manufacturer_candidates
                        or product_ids != plan.expected_product_candidates
                        or product_codes != plan.expected_product_codes):
                    raise ImportPlanError("STALE_RESOLUTION")
                if isinstance(data, AcceptSdsInput):
                    return AcceptSds(repository, validator).execute(data)
                return AddSdsRevision(repository, validator).execute(data)

            return self._registration.register(operation)

        return self._import_sds.execute(
            registration_data, plan.original_filename, pdf_bytes, register,
            verify_product=verify_product,
        )
