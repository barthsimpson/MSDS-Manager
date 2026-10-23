"""Validate Evidence JSON and build read-only identity plans per logical SDS."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.dto.evidence_json import IdentityResolution, SdsJsonImportPlan
from app.application.ports.evidence_identity_read import EvidenceIdentityReadPort
from app.application.manufacturer_identity import manufacturer_candidates


STATES = frozenset({"FOUND", "NOT_FOUND", "AMBIGUOUS", "UNREADABLE"})
PARTY_ROLES = frozenset({
    "MANUFACTURER", "MANUFACTURER_EXPORTER", "SUPPLIER", "IMPORTER",
    "DISTRIBUTOR", "EU_REPRESENTATIVE", "OTHER",
})
GOLDEN_MANUFACTURERS = {
    "CX80 POLSKA, CX80 GmbH": "CX80 POLSKA",
    "CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA": "CX80 POLSKA",
}


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def _nonempty(value: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected nonempty string")
        return None
    return value


def _field(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    field = _object(value, path, errors)
    state = field.get("state")
    if not isinstance(state, str) or state not in STATES:
        errors.append(f"{path}.state: invalid state")
        return field
    item = field.get("domain_value") if "domain_value" in field else field.get("value")
    evidence = field.get("evidence")
    if not isinstance(evidence, list):
        errors.append(f"{path}.evidence: expected list")
        evidence = []
    if state == "FOUND":
        if item is None or isinstance(item, str) and not item.strip():
            errors.append(f"{path}: FOUND requires value")
        if not evidence:
            errors.append(f"{path}: FOUND requires evidence")
    elif item is not None:
        errors.append(f"{path}: {state} requires null value")
    for index, raw in enumerate(evidence):
        proof = _object(raw, f"{path}.evidence[{index}]", errors)
        if not isinstance(proof.get("page"), int) or isinstance(proof.get("page"), bool) or proof["page"] < 1:
            errors.append(f"{path}.evidence[{index}].page: invalid")
        _nonempty(proof.get("source_text"), f"{path}.evidence[{index}].source_text", errors)
    return field


def _validate_document(document: Any, source: dict[str, Any], index: int) -> tuple[str, ...]:
    errors: list[str] = []
    path = f"documents[{index}]"
    doc = _object(document, path, errors)
    _nonempty(doc.get("document_key"), f"{path}.document_key", errors)
    pages = _object(doc.get("page_range"), f"{path}.page_range", errors)
    start, end = pages.get("from"), pages.get("to")
    count = source.get("page_count")
    if (not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int)
            or isinstance(end, bool) or start < 1 or end < start
            or isinstance(count, int) and end > count):
        errors.append(f"{path}.page_range: invalid")
    if not isinstance(doc.get("review_status"), str) or doc["review_status"] not in {"PENDING_REVIEW", "APPROVED", "REJECTED"}:
        errors.append(f"{path}.review_status: invalid")
    product = _object(doc.get("product"), f"{path}.product", errors)
    for key in ("product_name", "manufacturer_product_code"):
        _field(product.get(key), f"{path}.product.{key}", errors)
        candidate = _importable(product.get(key))
        if candidate is not None and (not isinstance(candidate, str) or not candidate.strip()):
            errors.append(f"{path}.product.{key}.value: expected nonempty string")
    metadata = _object(doc.get("document_metadata"), f"{path}.document_metadata", errors)
    for key in ("issue_date", "revision"):
        _field(metadata.get(key), f"{path}.document_metadata.{key}", errors)
    issue = _importable(metadata.get("issue_date"))
    if issue is not None:
        try:
            date.fromisoformat(issue)
        except (TypeError, ValueError):
            errors.append(f"{path}.document_metadata.issue_date.value: invalid ISO date")
    revision = _importable(metadata.get("revision"))
    if revision is not None and (not isinstance(revision, str) or not revision.strip()):
        errors.append(f"{path}.document_metadata.revision.value: expected nonempty string")
    parties = doc.get("parties")
    if not isinstance(parties, list):
        errors.append(f"{path}.parties: expected list")
    else:
        for number, raw_party in enumerate(parties):
            party = _object(raw_party, f"{path}.parties[{number}]", errors)
            if not isinstance(party.get("role"), str) or party["role"] not in PARTY_ROLES:
                errors.append(f"{path}.parties[{number}].role: invalid")
            _field(party.get("name"), f"{path}.parties[{number}].name", errors)
    validation = _object(doc.get("validation"), f"{path}.validation", errors)
    if not isinstance(validation.get("status"), str) or validation["status"] not in {
        "READY_FOR_HUMAN_REVIEW", "REQUIRES_HUMAN_REVIEW", "BLOCKED"
    }:
        errors.append(f"{path}.validation.status: invalid")
    if not isinstance(validation.get("issues"), list):
        errors.append(f"{path}.validation.issues: expected list")
    for section in ("safety_profile", "components"):
        content = doc.get(section)
        if not isinstance(content, dict if section == "safety_profile" else list):
            errors.append(f"{path}.{section}: invalid")
        elif section == "safety_profile":
            for key, value in content.items():
                _field(value, f"{path}.safety_profile.{key}", errors)
    return tuple(errors)


def _importable(field: Any) -> Any:
    return field.get("value") if isinstance(field, dict) and field.get("state") == "FOUND" else None


def _resolution(records, *, canonical_name=None, confirmation=False, conditional=False):
    status = "CREATE_CANDIDATE" if not records else "LINK_CANDIDATE" if len(records) == 1 else "HUMAN_REVIEW"
    return IdentityResolution(
        status=status, candidate_ids=tuple(row.record_id for row in records),
        canonical_name=canonical_name,
        human_confirmation_required=confirmation or status == "HUMAN_REVIEW",
        conditional_on_manufacturer=conditional,
    )


def _invalid_envelope(message: str) -> tuple[SdsJsonImportPlan, ...]:
    invalid = IdentityResolution("INVALID")
    return (SdsJsonImportPlan(
        "INVALID-ENVELOPE", None, "INVALID", (message,), None, None, None, None,
        invalid, invalid, (), (), (message,), "NOT_READY",
    ),)


class PlanEvidenceJsonImport:
    def __init__(self, identity_read: EvidenceIdentityReadPort) -> None:
        self._identity_read = identity_read

    def execute(self, payload: dict[str, Any]) -> tuple[SdsJsonImportPlan, ...]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return _invalid_envelope("Evidence JSON envelope must be an object")
        if payload.get("schema") != "SDS-JSON-001" or payload.get("schema_version") != "0.1":
            errors.append("schema/schema_version: unsupported")
        source = _object(payload.get("source"), "source", errors)
        filename = _nonempty(source.get("original_filename"), "source.original_filename", errors)
        sha = source.get("file_sha256")
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in sha):
            errors.append("source.file_sha256: invalid")
        if not isinstance(source.get("page_count"), int) or isinstance(source.get("page_count"), bool) or source["page_count"] < 1:
            errors.append("source.page_count: invalid")
        if not isinstance(source.get("readability_status"), str) or source["readability_status"] not in {"READABLE", "PARTIALLY_READABLE", "UNREADABLE"}:
            errors.append("source.readability_status: invalid")
        if not isinstance(source.get("language"), str) or not source["language"].strip():
            errors.append("source.language: invalid")
        documents = payload.get("documents")
        if not isinstance(documents, list) or not documents:
            return _invalid_envelope("Evidence JSON documents must be a nonempty list")
        keys = [doc.get("document_key") for doc in documents if isinstance(doc, dict)
                and isinstance(doc.get("document_key"), str)]
        if len(keys) != len(set(keys)):
            errors.append("documents.document_key: duplicate")
        report = _object(payload.get("extraction_report"), "extraction_report", errors)
        if report.get("logical_sds_count") != len(documents):
            errors.append("extraction_report.logical_sds_count: mismatch")
        if not isinstance(report.get("warnings"), list) or not isinstance(report.get("errors"), list):
            errors.append("extraction_report: warnings/errors must be lists")
        source_warnings = tuple(
            item for item in report.get("warnings", []) if isinstance(item, str)
        ) if isinstance(report.get("warnings"), list) else ()
        return tuple(
            self._plan_document(doc, source, filename, index, errors, source_warnings)
            for index, doc in enumerate(documents)
        )

    def _plan_document(self, doc, source, filename, index, envelope_errors, source_warnings):
        document = doc if isinstance(doc, dict) else {}
        errors = tuple(envelope_errors) + _validate_document(doc, source, index)
        key = document.get("document_key") if isinstance(document.get("document_key"), str) else f"INVALID-{index + 1}"
        invalid = IdentityResolution("INVALID")
        if errors:
            return SdsJsonImportPlan(
                key, filename, "INVALID", errors, None, None, None, None,
                invalid, invalid, (), (), errors, "NOT_READY",
            )

        product = document["product"]
        metadata = document["document_metadata"]
        name = _importable(product["product_name"])
        code = _importable(product["manufacturer_product_code"])
        issue_raw = _importable(metadata["issue_date"])
        revision = _importable(metadata["revision"])
        warnings: list[str] = list(source_warnings)
        blockers: list[str] = []
        issue_date = None
        if issue_raw is not None:
            try:
                issue_date = date.fromisoformat(issue_raw)
            except (TypeError, ValueError):
                blockers.append("INVALID_ISSUE_DATE")
        if not isinstance(name, str) or not name.strip():
            blockers.append("PRODUCT_NAME_REQUIRES_HUMAN_REVIEW")
        uncertain_code = product["manufacturer_product_code"]["state"] in {"AMBIGUOUS", "UNREADABLE"}
        if uncertain_code:
            blockers.append("MANUFACTURER_PRODUCT_CODE_REQUIRES_HUMAN_REVIEW")
        manufacturers = [party for party in document["parties"] if party["role"] == "MANUFACTURER"]
        raw = _importable(manufacturers[0]["name"]) if len(manufacturers) == 1 else None
        canonical = GOLDEN_MANUFACTURERS.get(raw, raw) if isinstance(raw, str) else None
        if len(manufacturers) != 1 or canonical is None:
            blockers.append("MANUFACTURER_REQUIRES_HUMAN_REVIEW")
            manufacturer_resolution = IdentityResolution("HUMAN_REVIEW")
        else:
            exact, similar = manufacturer_candidates(self._identity_read, canonical)
            if raw not in GOLDEN_MANUFACTURERS:
                manufacturer_resolution = IdentityResolution(
                    "HUMAN_REVIEW", tuple(row.record_id for row in exact), canonical,
                    similar, True,
                )
                blockers.append("UNAPPROVED_MANUFACTURER_RAW_VALUE")
            else:
                manufacturer_resolution = _resolution(
                    exact, canonical_name=canonical,
                    confirmation=bool(similar) and not exact,
                )
            manufacturer_resolution = IdentityResolution(
                manufacturer_resolution.status, manufacturer_resolution.candidate_ids,
                canonical, similar, manufacturer_resolution.human_confirmation_required,
            )
            if similar and not exact:
                warnings.append("SIMILAR_MANUFACTURERS_REQUIRE_HUMAN_CONFIRMATION")
        if (not isinstance(name, str) or not name.strip() or uncertain_code
                or manufacturer_resolution.status == "HUMAN_REVIEW"):
            product_resolution = IdentityResolution("HUMAN_REVIEW")
        elif manufacturer_resolution.status == "LINK_CANDIDATE":
            matches = self._identity_read.products_for_manufacturer(
                name, manufacturer_resolution.candidate_ids[0], code
            )
            product_resolution = _resolution(matches, confirmation=code is None and len(matches) == 1)
        else:
            # With no manufacturer_id, CREATE is only a conditional proposal when
            # the product name is absent globally. No existing ID is guessed.
            named = self._identity_read.products_named(name)
            product_resolution = (
                _resolution((), conditional=True) if not named
                else IdentityResolution("PENDING_MANUFACTURER", tuple(row.record_id for row in named),
                                        human_confirmation_required=True, conditional_on_manufacturer=True)
            )
            if named:
                blockers.append("PRODUCT_PENDING_MANUFACTURER")
        if document["validation"]["status"] == "BLOCKED":
            blockers.append("EXTRACTION_VALIDATION_BLOCKED")
        elif document["validation"]["status"] == "REQUIRES_HUMAN_REVIEW":
            blockers.append("EXTRACTION_REQUIRES_HUMAN_REVIEW")
        if document["review_status"] != "APPROVED":
            blockers.append("DOCUMENT_HUMAN_APPROVAL_REQUIRED")
        if document["safety_profile"]:
            warnings.append("SAFETY_DATA_DEFERRED_TO_STAGE_2")
        manual = ("use_description", "use_restriction")
        return SdsJsonImportPlan(
            key, filename, "VALID", (), name, code, issue_date, revision,
            manufacturer_resolution, product_resolution, manual, tuple(warnings),
            tuple(blockers), "NOT_READY",
        )
