"""Prepare one batch-approved Stage 1 import without a manual form."""

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json

from app.application.dto.approved_import import ApprovedImportPlan, HumanApproval, IdentityDecision
from app.application.manufacturer_identity import manufacturer_candidates
from app.application.ports.evidence_identity_read import EvidenceIdentityReadPort
from app.application.use_cases.controlled_evidence_import import ImportPlanError, approve_import_plan
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport


@dataclass(frozen=True, slots=True)
class BatchStage1Decision:
    batch: str
    evidence_json: str
    document_key: str
    json_sha256: str
    source_pdf_sha256: str
    canonical_manufacturer: str
    existing_manufacturer_name: str
    product_name: str
    manufacturer_product_code: str | None
    issue_date: date
    revision: str
    approved_by: str
    approved: bool

    @classmethod
    def from_json(cls, raw: bytes) -> "BatchStage1Decision":
        try:
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Batch decision must be an object")
            result = cls(
                batch=value["batch"], evidence_json=value["evidence_json"],
                document_key=value["document_key"], json_sha256=value["json_sha256"],
                source_pdf_sha256=value["source_pdf_sha256"],
                canonical_manufacturer=value["canonical_manufacturer"],
                existing_manufacturer_name=value["existing_manufacturer_name"],
                product_name=value["product_name"],
                manufacturer_product_code=value["manufacturer_product_code"],
                issue_date=date.fromisoformat(value["issue_date"]),
                revision=value["revision"], approved_by=value["approved_by"],
                approved=value["approved"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ImportPlanError("INVALID_BATCH_DECISION") from error
        if (result.approved is not True or not all(
            isinstance(item, str) and item.strip() for item in (
                result.batch, result.evidence_json, result.document_key,
                result.canonical_manufacturer, result.existing_manufacturer_name,
                result.product_name, result.revision, result.approved_by,
            )
        ) or any(not isinstance(item, str) or len(item) != 64
                 or any(character not in "0123456789abcdef" for character in item)
                 for item in (result.json_sha256, result.source_pdf_sha256))
                or result.manufacturer_product_code is not None
                and (not isinstance(result.manufacturer_product_code, str)
                     or not result.manufacturer_product_code.strip())):
            raise ImportPlanError("INVALID_BATCH_DECISION")
        return result


class AutomaticStage1Import:
    """Resolve a frozen batch decision to one explicit existing manufacturer ID."""

    def prepare(
        self, raw_json: bytes, json_filename: str, pdf_bytes: bytes,
        decision: BatchStage1Decision, read: EvidenceIdentityReadPort,
    ) -> ApprovedImportPlan:
        if decision.approved is not True:
            raise ImportPlanError("BATCH_DECISION_NOT_APPROVED")
        if json_filename != decision.evidence_json or sha256(raw_json).hexdigest() != decision.json_sha256:
            raise ImportPlanError("SOURCE_CHANGED")
        if sha256(pdf_bytes).hexdigest() != decision.source_pdf_sha256:
            raise ImportPlanError("PDF_MISMATCH")
        try:
            payload = json.loads(raw_json)
        except (TypeError, ValueError) as error:
            raise ImportPlanError("INVALID_EVIDENCE_JSON") from error
        if not isinstance(payload, dict):
            raise ImportPlanError("INVALID_EVIDENCE_JSON")
        if payload.get("source", {}).get("file_sha256") != decision.source_pdf_sha256:
            raise ImportPlanError("PDF_MISMATCH")
        plans = PlanEvidenceJsonImport(read).execute(payload)
        if len(plans) != 1 or plans[0].document_key != decision.document_key:
            raise ImportPlanError("EXPECTED_ONE_SDS")
        candidate = plans[0]
        if (candidate.validation_status != "VALID"
                or "EXTRACTION_VALIDATION_BLOCKED" in candidate.blockers
                or candidate.mapped_product_name != decision.product_name
                or candidate.mapped_manufacturer_product_code != decision.manufacturer_product_code
                or candidate.mapped_issue_date != decision.issue_date
                or candidate.mapped_revision != decision.revision
                or candidate.manufacturer_resolution.canonical_name != decision.canonical_manufacturer):
            raise ImportPlanError("BATCH_DECISION_MISMATCH")
        matches = read.manufacturers_named(decision.existing_manufacturer_name)
        if len(matches) != 1:
            raise ImportPlanError("MANUFACTURER_NOT_UNIQUE")
        exact, similar = manufacturer_candidates(read, decision.canonical_manufacturer)
        selected = matches[0]
        if selected.record_id not in {row.record_id for row in (*exact, *similar)}:
            raise ImportPlanError("LINK_TARGET_NOT_APPROVED")
        if read.products_for_manufacturer(
            decision.product_name, selected.record_id, decision.manufacturer_product_code,
        ):
            raise ImportPlanError("STALE_RESOLUTION: product exists")
        return approve_import_plan(
            raw_json, decision.document_key, read,
            IdentityDecision(
                "LINK", decision.canonical_manufacturer, selected_id=selected.record_id,
                manufacturer_link_confirmed=True,
                selected_record_name=selected.name,
            ),
            IdentityDecision(
                "CREATE", decision.product_name,
                manufacturer_product_code=decision.manufacturer_product_code,
            ),
            use_description=None, use_restriction=None, safety_profile=None,
            original_filename=payload["source"]["original_filename"],
            pdf_bytes=pdf_bytes,
            approval=HumanApproval(decision.approved_by, True, True, False, False, True),
        )
