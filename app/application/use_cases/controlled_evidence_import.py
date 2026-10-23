"""Human-approved Evidence JSON import through existing SDS use cases."""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from typing import Callable, Protocol

from app.application.dto.approved_import import ApprovedImportPlan, HumanApproval, IdentityDecision
from app.application.manufacturer_identity import manufacturer_candidates
from app.application.dto.sds import AcceptSdsInput, AddSdsRevisionInput, SdsSafetyProfileDraft, Stage1SdsInput
from app.application.ports.evidence_identity_read import EvidenceIdentityReadPort
from app.application.use_cases.accept_sds import AcceptSds
from app.application.use_cases.add_sds_revision import AddSdsRevision
from app.application.use_cases.import_sds import ImportSds
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport
from app.application.use_cases.register_stage1_sds import RegisterStage1Sds
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
) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...], tuple[tuple[str, str | None], ...]]:
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
    exact, similar = manufacturer_candidates(read, manufacturer.name)
    manufacturer_rows = (*exact, *similar)
    manufacturer_snapshot = tuple((row.record_id, row.name) for row in manufacturer_rows)
    if manufacturer.action == "CREATE":
        if exact or manufacturer.selected_id is not None or manufacturer.selected_record_name is not None:
            raise ImportPlanError("DECISION_DOES_NOT_MATCH_DRY_RUN")
    else:
        selected = next((row for row in manufacturer_rows
                         if row.record_id == manufacturer.selected_id), None)
        if selected is None:
            raise ImportPlanError("LINK_TARGET_NOT_APPROVED")
        if not manufacturer.manufacturer_link_confirmed:
            raise ImportPlanError("MANUFACTURER_LINK_CONFIRMATION_REQUIRED")
        if (manufacturer.selected_record_name is not None
                and manufacturer.selected_record_name != selected.name):
            raise ImportPlanError("STALE_MANUFACTURER_SNAPSHOT")
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
    return manufacturer_snapshot, product_ids, tuple(
        (row.record_id, row.manufacturer_product_code) for row in product_rows
    )


def approve_import_plan(
    raw_json: bytes, document_key: str, read: EvidenceIdentityReadPort,
    manufacturer: IdentityDecision, product: IdentityDecision,
    *, use_description: str | None, use_restriction: str | None,
    safety_profile: SdsSafetyProfileDraft | None, original_filename: str,
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
    manufacturer_snapshot, product_ids, product_codes = _require_decisions(
        dry_run, read, manufacturer, product,
    )
    selected_manufacturer = next((name for record_id, name in manufacturer_snapshot
                                  if record_id == manufacturer.selected_id), None)
    approved_manufacturer = (replace(manufacturer, selected_record_name=selected_manufacturer)
                             if manufacturer.action == "LINK" else manufacturer)
    manual_confirmation_required = (safety_profile is not None or use_description is not None
                                    or use_restriction is not None)
    if (not isinstance(approval, HumanApproval) or not approval.approved_by.strip()
            or not all((approval.manufacturer_confirmed, approval.product_confirmed,
                        approval.pdf_confirmed))
            or manual_confirmation_required and not approval.manual_inputs_confirmed
            or safety_profile is not None and not approval.safety_confirmed):
        raise ImportPlanError("HUMAN_CONFIRMATION_REQUIRED")
    for name, value in (("use_description", use_description),
                        ("use_restriction", use_restriction)):
        if value is None and safety_profile is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ImportPlanError(f"PLAN_NOT_READY: {name}")
    if safety_profile is not None:
        _require_safety(safety_profile)
    if (not isinstance(original_filename, str) or not original_filename.lower().endswith(".pdf")
            or any(character in original_filename for character in ("/", "\\", ":"))
            or original_filename in {".", ".."}
            or not isinstance(pdf_bytes, bytes) or not pdf_bytes.startswith(b"%PDF-")):
        raise ImportPlanError("PDF_REQUIRED")
    if safety_profile is None and (
        original_filename != payload.get("source", {}).get("original_filename")
        or sha256(pdf_bytes).hexdigest() != payload.get("source", {}).get("file_sha256")
    ):
        raise ImportPlanError("PDF_MISMATCH")
    return ApprovedImportPlan(
        source_json_fingerprint=sha256(raw_json).hexdigest(), document_key=document_key,
        source_filename=dry_run.source_filename,
        manufacturer_decision=approved_manufacturer, product_decision=product,
        expected_manufacturer_candidates=tuple(record_id for record_id, _ in manufacturer_snapshot),
        expected_product_candidates=product_ids,
        expected_product_codes=product_codes,
        issue_date=dry_run.mapped_issue_date, revision=dry_run.mapped_revision,
        original_filename=original_filename,
        use_description=use_description.strip() if use_description is not None else None,
        use_restriction=use_restriction.strip() if use_restriction is not None else None,
        safety_profile=safety_profile,
        safety_fingerprint=_safety_fingerprint(safety_profile) if safety_profile is not None else None,
        pdf_fingerprint=sha256(pdf_bytes).hexdigest(), human_approval=approval,
        safety_readiness=("SAFETY_ENRICHMENT_PENDING" if safety_profile is None
                          else "SAFETY_ENRICHMENT_COMPLETE"),
        manufacturer_selected_name=selected_manufacturer,
        expected_manufacturer_snapshot=manufacturer_snapshot,
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
        if plan.safety_profile is not None:
            if _safety_fingerprint(plan.safety_profile) != plan.safety_fingerprint:
                raise ImportPlanError("SAFETY_PAYLOAD_CHANGED")
            _require_safety(plan.safety_profile)
        elif plan.safety_fingerprint is not None:
            raise ImportPlanError("SAFETY_PAYLOAD_CHANGED")
        try:
            payload = json.loads(raw_json)
        except (TypeError, ValueError) as error:
            raise ImportPlanError("SOURCE_CHANGED") from error
        manual_confirmation_required = (plan.safety_profile is not None
                                        or plan.use_description is not None
                                        or plan.use_restriction is not None)
        if (not isinstance(plan.human_approval, HumanApproval)
                or not plan.human_approval.approved_by.strip() or not all((
            plan.human_approval.manufacturer_confirmed, plan.human_approval.product_confirmed,
            plan.human_approval.pdf_confirmed,
        )) or manual_confirmation_required and not plan.human_approval.manual_inputs_confirmed
                or plan.safety_profile is not None and not plan.human_approval.safety_confirmed):
            raise ImportPlanError("HUMAN_CONFIRMATION_REQUIRED")
        for value in (plan.use_description, plan.use_restriction):
            if value is None and plan.safety_profile is None:
                continue
            if not isinstance(value, str) or not value.strip():
                raise ImportPlanError("PLAN_NOT_READY")
        if plan.manufacturer_selected_name != plan.manufacturer_decision.selected_record_name:
            raise ImportPlanError("STALE_RESOLUTION")

        if plan.safety_profile is None:
            registration_data = Stage1SdsInput(
                source_relative_path="", original_filename=plan.original_filename,
                product_name=plan.product_decision.name,
                manufacturer_product_code=plan.product_decision.manufacturer_product_code,
                manufacturer_name=plan.manufacturer_decision.name,
                use_description=plan.use_description, use_restriction=plan.use_restriction,
                issue_date=plan.issue_date, revision=plan.revision,
                controlled_manufacturer_decision=plan.manufacturer_decision,
                controlled_product_decision=plan.product_decision,
                product_id=(plan.product_decision.selected_id
                            if plan.product_decision.action == "LINK" else None),
            )
            verify_product = (self._registration.verify_product
                              if registration_data.product_id else None)
        elif plan.product_decision.action == "CREATE":
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
                    manufacturer_snapshot, product_ids, product_codes = _require_decisions(
                        current, read, plan.manufacturer_decision, plan.product_decision,
                    )
                except ImportPlanError as error:
                    raise ImportPlanError("STALE_RESOLUTION") from error
                if (manufacturer_snapshot != plan.expected_manufacturer_snapshot
                        or tuple(record_id for record_id, _ in manufacturer_snapshot)
                        != plan.expected_manufacturer_candidates
                        or product_ids != plan.expected_product_candidates
                        or product_codes != plan.expected_product_codes):
                    raise ImportPlanError("STALE_RESOLUTION")
                if isinstance(data, AcceptSdsInput):
                    return AcceptSds(repository, validator).execute(data)
                if isinstance(data, Stage1SdsInput):
                    return RegisterStage1Sds(repository, validator).execute(data)
                return AddSdsRevision(repository, validator).execute(data)

            return self._registration.register(operation)

        return self._import_sds.execute(
            registration_data, plan.original_filename, pdf_bytes, register,
            verify_product=verify_product,
        )
