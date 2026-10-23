"""Preflight the whole approved batch, then commit only deterministic Stage 1 items."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.manufacturer_identity import manufacturer_candidates
from app.application.use_cases.controlled_evidence_import import (
    ControlledEvidenceImport, ImportPlanError, approve_import_plan,
)
from app.application.use_cases.import_sds import ImportSds
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport
from app.infrastructure.config import load_settings
from app.infrastructure.db.controlled_evidence_registration import SqlAlchemyControlledEvidenceRegistration
from app.infrastructure.db.models import ManufacturerModel, ProductModel, SdsDocumentModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.filesystem.evidence_source_pdf import resolve_source_pdf
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


CLASSIFICATIONS = (
    "READY_CREATE", "READY_ADD_REVISION", "SKIP_EXACT_EXISTING",
    "SKIP_DUPLICATE_SOURCE", "REVIEW_IDENTITY", "BLOCKED_SOURCE",
    "BLOCKED_DATA", "EXCLUDED_NON_SDS",
)
TECHNICAL_CARDS = {
    "B001-P032": "KT CX RC72-1 (1).pdf",
    "B001-P033": "KT CX RC72-1 (2).pdf",
}


@dataclass(frozen=True)
class BatchManufacturerDecision:
    batch: str
    canonical_manufacturer: str
    existing_manufacturer_name: str
    approved_by: str

    @classmethod
    def from_bytes(cls, raw: bytes):
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or data.get("approved") is not True:
                raise ValueError("Unapproved batch decision")
            fields = ("batch", "canonical_manufacturer", "existing_manufacturer_name",
                      "approved_by")
            if any(not isinstance(data.get(name), str) or not data[name].strip()
                   for name in fields):
                raise ValueError("Incomplete batch decision")
            return cls(*(data[name] for name in fields))
        except (TypeError, ValueError, KeyError) as error:
            raise ImportPlanError("INVALID_BATCH_DECISION") from error


@dataclass
class BatchItem:
    manifest_id: str
    json_file: str | None
    source_pdf: str
    source_sha_expected: str | None
    source_sha_actual: str | None = None
    product_name: str | None = None
    manufacturer_canonical: str | None = None
    manufacturer_selected_id: str | None = None
    manufacturer_selected_name: str | None = None
    manufacturer_product_code: str | None = None
    issue_date: date | None = None
    revision: str | None = None
    existing_product_candidates: list[dict] = field(default_factory=list)
    existing_current_sds: list[dict] = field(default_factory=list)
    classification: str = "BLOCKED_DATA"
    reason: str = "NOT_EVALUATED"
    action: str = "NOT_ATTEMPTED"
    product_id: str | None = None
    sds_id: str | None = None
    raw_json: bytes | None = field(default=None, repr=False)
    pdf_bytes: bytes | None = field(default=None, repr=False)


def _plain_name(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and value not in {".", ".."}
            and Path(value).name == value and PureWindowsPath(value).name == value)


def _actual_source_sha(source_root: Path, filename: object) -> str | None:
    if not _plain_name(filename) or not source_root.is_absolute() or not source_root.is_dir():
        return None
    root = source_root.resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return sha256(path.read_bytes()).hexdigest()


def _header_has_evidence(document: dict) -> bool:
    if not isinstance(document, dict):
        return False
    product = document.get("product", {})
    metadata = document.get("document_metadata", {})
    parties = document.get("parties", [])
    if not isinstance(product, dict) or not isinstance(metadata, dict) or not isinstance(parties, list):
        return False
    manufacturers = [party for party in parties if isinstance(party, dict)
                     and party.get("role") == "MANUFACTURER"]
    fields = (product.get("product_name"), metadata.get("issue_date"),
              metadata.get("revision"),
              manufacturers[0].get("name") if len(manufacturers) == 1 else None)
    if any(not isinstance(value, dict) or value.get("state") != "FOUND"
           or not value.get("evidence") for value in fields):
        return False
    code = product.get("manufacturer_product_code")
    return (isinstance(code, dict) and code.get("state") in {"FOUND", "NOT_FOUND"}
            and (code.get("state") != "FOUND" or bool(code.get("evidence"))))


def _name_may_match(left: str, right: str) -> bool:
    a, b = " ".join(left.casefold().split()), " ".join(right.casefold().split())
    return a == b or a.startswith(b + " ") or b.startswith(a + " ")


def _product_candidates(session: Session, name: str, selected_id: str) -> list[tuple[ProductModel, ManufacturerModel]]:
    rows = session.execute(
        select(ProductModel, ManufacturerModel)
        .join(ManufacturerModel, ProductModel.manufacturer_id == ManufacturerModel.manufacturer_id)
    ).all()
    normalized = " ".join(name.casefold().split())
    return [(product, manufacturer) for product, manufacturer in rows
            if " ".join(product.product_name.casefold().split()) == normalized
            or manufacturer.manufacturer_id != selected_id
            and _name_may_match(name, product.product_name)]


def _sds_state(session: Session, product_id: str, storage: SdsPdfStorage) -> tuple[list[dict], str | None]:
    documents = session.scalars(select(SdsDocumentModel).where(
        SdsDocumentModel.product_id == product_id,
    )).all()
    result = []
    for document in documents:
        try:
            stored_sha = sha256(storage.read_sds(document.relative_path)).hexdigest()
        except (OSError, ValueError) as error:
            return result, f"REGISTERED_PDF_UNAVAILABLE:{document.sds_id}:{type(error).__name__}"
        result.append({
            "sds_id": document.sds_id, "status": document.document_status.value,
            "issue_date": document.issue_date.isoformat() if document.issue_date else None,
            "revision": document.revision, "sha256": stored_sha,
        })
    return result, None


def _classify_identity(item: BatchItem, session: Session, selected_id: str,
                       storage: SdsPdfStorage) -> None:
    candidates = _product_candidates(session, item.product_name, selected_id)
    item.existing_product_candidates = [
        {"product_id": product.product_id, "name": product.product_name,
         "code": product.manufacturer_product_code,
         "manufacturer_id": manufacturer.manufacturer_id,
         "manufacturer_name": manufacturer.manufacturer_name}
        for product, manufacturer in candidates
    ]
    selected_exact_name = [product for product, manufacturer in candidates
                           if manufacturer.manufacturer_id == selected_id
                           and product.product_name == item.product_name]
    exact_identity = [product for product in selected_exact_name
                      if product.manufacturer_product_code == item.manufacturer_product_code]
    if len(exact_identity) > 1:
        item.classification, item.reason = "REVIEW_IDENTITY", "MULTIPLE_EXACT_PRODUCTS"
        return
    if len(exact_identity) == 0 and candidates:
        item.classification, item.reason = "REVIEW_IDENTITY", "SIMILAR_OR_CODE_CONFLICT_PRODUCT"
        return
    if not exact_identity:
        item.classification, item.reason = "READY_CREATE", "EXACT_PRODUCT_ABSENT"
        return

    product = exact_identity[0]
    item.product_id = product.product_id
    item.existing_current_sds, error = _sds_state(session, product.product_id, storage)
    if error:
        item.classification, item.reason = "BLOCKED_DATA", error
        return
    current = [row for row in item.existing_current_sds if row["status"] == "CURRENT"]
    if len(current) > 1:
        item.classification, item.reason = "BLOCKED_DATA", "MULTIPLE_CURRENT_SDS"
        return
    same_metadata = [row for row in item.existing_current_sds
                     if row["issue_date"] == item.issue_date.isoformat()
                     and row["revision"] == item.revision]
    if any(row["sha256"] != item.source_sha_actual for row in same_metadata):
        item.classification, item.reason = "BLOCKED_DATA", "SDS_METADATA_SOURCE_CONFLICT"
        return
    if same_metadata:
        item.sds_id = same_metadata[0]["sds_id"]
        item.classification, item.reason = "SKIP_EXACT_EXISTING", "EXACT_PRODUCT_SDS_PDF"
        item.action = "SKIPPED"
        return
    if not current:
        item.classification, item.reason = "REVIEW_IDENTITY", "NO_CURRENT_SDS_FOR_EXISTING_PRODUCT"
        return
    current_date = date.fromisoformat(current[0]["issue_date"]) if current[0]["issue_date"] else None
    if current_date is None or item.issue_date <= current_date:
        item.classification, item.reason = "REVIEW_IDENTITY", "REVISION_NOT_NEWER"
        return
    item.classification, item.reason = "READY_ADD_REVISION", "NEWER_ISSUE_DATE"


def preflight(
    manifest_path: Path, json_dir: Path, source_root: Path,
    decision: BatchManufacturerDecision, session: Session, sds_root: Path,
) -> list[BatchItem]:
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except (OSError, ValueError) as error:
        raise ImportPlanError("INVALID_MANIFEST") from error
    if not isinstance(manifest, dict) or manifest.get("batch") != decision.batch \
            or not isinstance(manifest.get("files"), list):
        raise ImportPlanError("MANIFEST_DECISION_MISMATCH")
    entries = manifest["files"]
    read = SqlAlchemyEvidenceIdentityRead(session)
    manufacturer_rows = read.manufacturers_named(decision.existing_manufacturer_name)
    selected = manufacturer_rows[0] if len(manufacturer_rows) == 1 else None
    storage = SdsPdfStorage(sds_root)
    rows: list[BatchItem] = []
    seen_hash: dict[str, BatchItem] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ImportPlanError("INVALID_MANIFEST_ENTRY")
        item = BatchItem(
            manifest_id=str(entry.get("id", "")), json_file=entry.get("json"),
            source_pdf=str(entry.get("source_file", "")),
            source_sha_expected=entry.get("sha256"),
        )
        rows.append(item)
        if (entry.get("status") == "FAILED" and entry.get("logical_sds_count") == 0
                and entry.get("json") is None
                and TECHNICAL_CARDS.get(item.manifest_id) == item.source_pdf):
            item.classification, item.reason, item.action = (
                "EXCLUDED_NON_SDS", "TECHNICAL_CARD_NOT_SDS", "EXCLUDED",
            )
            continue
        if (entry.get("logical_sds_count") != 1
                or entry.get("status") not in {"COMPLETE", "NEEDS_REVIEW"}
                or not _plain_name(item.json_file)
                or item.json_file != f"{item.manifest_id}_DOC-001.json"
                or not _plain_name(item.source_pdf)
                or not isinstance(item.source_sha_expected, str)
                or len(item.source_sha_expected) != 64):
            item.classification, item.reason = "BLOCKED_DATA", "INVALID_MANIFEST_ENTRY"
            continue
        item.source_sha_actual = _actual_source_sha(source_root, item.source_pdf)
        json_path = json_dir / item.json_file
        try:
            item.raw_json = json_path.read_bytes()
            payload = json.loads(item.raw_json)
        except (OSError, ValueError) as error:
            item.classification, item.reason = "BLOCKED_SOURCE", f"JSON_UNAVAILABLE:{type(error).__name__}"
            continue
        if not isinstance(payload, dict):
            item.classification, item.reason = "BLOCKED_DATA", "INVALID_JSON_ENVELOPE"
            continue
        source = payload.get("source", {})
        document_key = item.json_file.rsplit("_", 1)[-1].removesuffix(".json")
        if (not isinstance(source, dict) or source.get("original_filename") != item.source_pdf
                or source.get("file_sha256") != item.source_sha_expected
                or document_key != "DOC-001"):
            item.classification, item.reason = "BLOCKED_SOURCE", "MANIFEST_JSON_SOURCE_MISMATCH"
            continue
        binding = resolve_source_pdf(manifest_path, item.json_file, payload,
                                     source_root=source_root)
        if binding.status != "AUTO_BOUND" or binding.content is None:
            item.classification, item.reason = "BLOCKED_SOURCE", f"PDF_{binding.status}"
            continue
        item.pdf_bytes = binding.content
        if item.source_sha_actual != item.source_sha_expected:
            item.classification, item.reason = "BLOCKED_SOURCE", "PDF_SHA_MISMATCH"
            continue
        try:
            plans = PlanEvidenceJsonImport(read).execute(payload)
        except (TypeError, ValueError, KeyError) as error:
            item.classification, item.reason = (
                "BLOCKED_DATA", f"INVALID_EVIDENCE_JSON:{type(error).__name__}",
            )
            continue
        if len(plans) != 1 or plans[0].document_key != document_key:
            item.classification, item.reason = "BLOCKED_DATA", "EXPECTED_ONE_LOGICAL_SDS"
            continue
        plan = plans[0]
        item.product_name = plan.mapped_product_name
        item.manufacturer_canonical = plan.manufacturer_resolution.canonical_name
        item.manufacturer_product_code = plan.mapped_manufacturer_product_code
        item.issue_date, item.revision = plan.mapped_issue_date, plan.mapped_revision
        if (plan.validation_status != "VALID" or not isinstance(payload.get("documents"), list)
                or not payload["documents"] or "EXTRACTION_VALIDATION_BLOCKED" in plan.blockers
                or not _header_has_evidence(payload["documents"][0])
                or not item.product_name or not item.issue_date or not item.revision
                or "MANUFACTURER_PRODUCT_CODE_REQUIRES_HUMAN_REVIEW" in plan.blockers):
            item.classification, item.reason = "BLOCKED_DATA", "STAGE1_HEADER_INVALID_OR_UNPROVEN"
            continue
        identity = (item.product_name, item.manufacturer_product_code,
                    item.issue_date, item.revision, item.manufacturer_canonical)
        previous = seen_hash.get(item.source_sha_actual)
        if previous is not None:
            previous_identity = (previous.product_name, previous.manufacturer_product_code,
                                 previous.issue_date, previous.revision,
                                 previous.manufacturer_canonical)
            if identity == previous_identity:
                item.classification, item.reason, item.action = (
                    "SKIP_DUPLICATE_SOURCE", f"DUPLICATE_OF:{previous.manifest_id}", "SKIPPED",
                )
            else:
                item.classification, item.reason = "BLOCKED_DATA", "CONTRADICTORY_DUPLICATE_SOURCE"
                previous.classification, previous.reason = (
                    "BLOCKED_DATA", f"CONTRADICTORY_DUPLICATE_SOURCE:{item.manifest_id}",
                )
                previous.action = "NOT_ATTEMPTED"
            continue
        seen_hash[item.source_sha_actual] = item
        if selected is None:
            item.classification, item.reason = "BLOCKED_DATA", "MANUFACTURER_NOT_UNIQUE"
            continue
        item.manufacturer_selected_id = selected.record_id
        item.manufacturer_selected_name = selected.name
        if item.manufacturer_canonical != decision.canonical_manufacturer:
            item.classification, item.reason = "REVIEW_IDENTITY", "MANUFACTURER_CANONICAL_NOT_APPROVED"
            continue
        exact, similar = manufacturer_candidates(read, decision.canonical_manufacturer)
        if selected.record_id not in {row.record_id for row in (*exact, *similar)}:
            item.classification, item.reason = "BLOCKED_DATA", "MANUFACTURER_LINK_NOT_PRESENTED"
            continue
        _classify_identity(item, session, selected.record_id, storage)
        if item.classification in {"READY_CREATE", "READY_ADD_REVISION"}:
            try:
                _approve_item(item, read, decision, selected.record_id,
                              selected.name, item.raw_json, item.pdf_bytes)
            except ImportPlanError as error:
                item.classification, item.reason = "BLOCKED_DATA", f"APPROVED_PLAN_INVALID:{error}"
    if len({item.manifest_id for item in rows}) != len(rows):
        for item in rows:
            item.classification, item.reason, item.action = (
                "BLOCKED_DATA", "DUPLICATE_MANIFEST_ID", "NOT_ATTEMPTED",
            )
    return rows


def _approve_item(item: BatchItem, read: SqlAlchemyEvidenceIdentityRead,
                  decision: BatchManufacturerDecision, selected_id: str,
                  selected_name: str, raw: bytes, pdf: bytes):
    product_decision = (
        IdentityDecision("CREATE", item.product_name,
                         manufacturer_product_code=item.manufacturer_product_code)
        if item.classification == "READY_CREATE" else
        IdentityDecision("LINK", item.product_name, selected_id=item.product_id,
                         manufacturer_product_code=item.manufacturer_product_code,
                         null_code_link_confirmed=item.manufacturer_product_code is None)
    )
    return approve_import_plan(
        raw, item.json_file.rsplit("_", 1)[-1].removesuffix(".json"), read,
        IdentityDecision("LINK", decision.canonical_manufacturer,
                         selected_id=selected_id,
                         selected_record_name=selected_name,
                         manufacturer_link_confirmed=True),
        product_decision, use_description=None, use_restriction=None,
        safety_profile=None, original_filename=item.source_pdf,
        pdf_bytes=pdf,
        approval=HumanApproval(decision.approved_by, True, True, False, False, True),
    )


def _fresh_plan(item: BatchItem, manifest_path: Path, json_dir: Path, source_root: Path,
                decision: BatchManufacturerDecision, session: Session, sds_root: Path):
    raw = (json_dir / item.json_file).read_bytes()
    if sha256(raw).hexdigest() != sha256(item.raw_json).hexdigest():
        raise ImportPlanError("SOURCE_CHANGED")
    payload = json.loads(raw)
    binding = resolve_source_pdf(manifest_path, item.json_file, payload,
                                 source_root=source_root)
    if binding.status != "AUTO_BOUND" or binding.content is None \
            or sha256(binding.content).hexdigest() != item.source_sha_actual:
        raise ImportPlanError("PDF_CHANGED")
    read = SqlAlchemyEvidenceIdentityRead(session)
    selected = read.manufacturers_named(decision.existing_manufacturer_name)
    if len(selected) != 1 or selected[0].record_id != item.manufacturer_selected_id:
        raise ImportPlanError("STALE_RESOLUTION: manufacturer")
    current = BatchItem(item.manifest_id, item.json_file, item.source_pdf,
                        item.source_sha_expected, item.source_sha_actual,
                        item.product_name, item.manufacturer_canonical,
                        item.manufacturer_selected_id, item.manufacturer_selected_name,
                        item.manufacturer_product_code, item.issue_date, item.revision)
    _classify_identity(current, session, selected[0].record_id, SdsPdfStorage(sds_root))
    if current.classification != item.classification or current.product_id != item.product_id:
        raise ImportPlanError("STALE_RESOLUTION: product")
    plan = _approve_item(item, read, decision, selected[0].record_id,
                         selected[0].name, raw, binding.content)
    return plan, raw, binding.content


def commit_ready(rows: list[BatchItem], manifest_path: Path, json_dir: Path,
                 source_root: Path, decision: BatchManufacturerDecision,
                 engine, sds_root: Path) -> Exception | None:
    if any(item.classification in {"BLOCKED_SOURCE", "BLOCKED_DATA"} for item in rows):
        raise ImportPlanError("BATCH_PREFLIGHT_BLOCKED")
    factory = create_session_factory(engine)
    importer = ControlledEvidenceImport(
        SqlAlchemyControlledEvidenceRegistration(factory, sds_root),
        ImportSds(SdsPdfStorage(sds_root)),
    )
    for item in rows:
        if item.classification not in {"READY_CREATE", "READY_ADD_REVISION"}:
            continue
        try:
            with engine.connect().execution_options(postgresql_readonly=True) as connection:
                with Session(bind=connection) as session:
                    plan, raw, pdf = _fresh_plan(
                        item, manifest_path, json_dir, source_root, decision, session, sds_root,
                    )
            sds_id = importer.execute(plan, raw, pdf)
            with engine.connect().execution_options(postgresql_readonly=True) as connection:
                with Session(bind=connection) as session:
                    document = session.get(SdsDocumentModel, sds_id)
                    item.product_id, item.sds_id = document.product_id, sds_id
            item.action, item.reason = "COMMITTED", "CONTROLLED_COMMIT_OK"
        except Exception as error:
            item.action = "FAILED_DURING_COMMIT"
            item.reason = f"{type(error).__name__}:{error}"
            return error
    return None


def _cell(value) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def report_text(rows: list[BatchItem], *, phase: str, stopped_reason: str | None = None) -> str:
    counts = Counter(item.classification for item in rows)
    committed = sum(item.action == "COMMITTED" for item in rows)
    failed = sum(item.action == "FAILED_DURING_COMMIT" for item in rows)
    unattempted = sum(item.action == "NOT_ATTEMPTED" and item.classification in
                      {"READY_CREATE", "READY_ADD_REVISION"} for item in rows)
    lines = [
        "# BATCH-001_CX — Stage 1 Import Report", "",
        f"Status: **{phase}**" + (f" — {stopped_reason}" if stopped_reason else ""), "",
        "## Summary", "",
        f"- Manifest PDFs: {len(rows)}; logical SDS: {sum(item.json_file is not None for item in rows)}.",
    ]
    lines.extend(f"- {name}: {counts[name]}" for name in CLASSIFICATIONS)
    lines.extend((f"- COMMITTED: {committed}", f"- FAILED_DURING_COMMIT: {failed}",
                  f"- NOT_ATTEMPTED (ready items): {unattempted}",
                  f"- Operator DB rows from batch commits: PRODUCT={sum(item.action == 'COMMITTED' and item.classification == 'READY_CREATE' for item in rows)}, SDS={committed}, PRODUCT_HISTORY={committed}, MANUFACTURER=0, SAFETY_PROFILE=0, SDS_COMPONENT=0, BHP_DECISION=0.",
                  f"- New PDFs in operator SDS_ROOT_PATH from batch commits: {committed}.",
                  "", "## Preflight matrix and outcome", "",
                  "| Manifest ID | PDF | JSON | Expected SHA-256 | Actual SHA-256 | Product | Canonical manufacturer | Selected manufacturer ID/name | Code | Issue date | Revision | Existing product candidates | Existing SDS | Classification | Action | Product ID | SDS ID | Reason |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"))
    for item in rows:
        candidates = ", ".join(f"{row['product_id']}:{row['name']}:{row['code']}:{row['manufacturer_name']}"
                               for row in item.existing_product_candidates)
        existing = ", ".join(f"{row['sds_id']}:{row['status']}:{row['issue_date']}:{row['revision']}:{row['sha256']}"
                             for row in item.existing_current_sds)
        values = (
            item.manifest_id, item.source_pdf, item.json_file,
            item.source_sha_expected, item.source_sha_actual, item.product_name,
            item.manufacturer_canonical,
            f"{item.manufacturer_selected_id}/{item.manufacturer_selected_name}"
            if item.manufacturer_selected_id else None,
            item.manufacturer_product_code, item.issue_date, item.revision,
            candidates or None, existing or None, item.classification, item.action,
            item.product_id, item.sds_id, item.reason,
        )
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    lines.extend(("", "STOP after BATCH-001_CX. No Paczka2 or later sprint was started.", ""))
    return "\n".join(lines)


def _schema_pass(engine) -> None:
    config = Config("alembic.ini")
    head = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect().execution_options(postgresql_readonly=True) as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    if current != head or current != "b7d4a1f03962":
        raise ImportPlanError(f"ALEMBIC_NOT_AT_HEAD:{current}")
    command.check(config)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    decision = BatchManufacturerDecision.from_bytes(args.decision.read_bytes())
    settings = load_settings()
    engine = create_engine_from_settings(settings)
    try:
        _schema_pass(engine)
        with engine.connect().execution_options(postgresql_readonly=True) as connection:
            with Session(bind=connection) as session:
                rows = preflight(args.manifest, args.manifest.parent / "json",
                                 args.source_root, decision, session, settings.sds_root_path)
        manifest_count_ok = (len(rows) == 37 and sum(item.json_file is not None for item in rows) == 35
                             and sum(item.classification == "EXCLUDED_NON_SDS" for item in rows) == 2)
        blocked = [item for item in rows if item.classification in {"BLOCKED_SOURCE", "BLOCKED_DATA"}]
        if not manifest_count_ok or blocked or not args.source_root.is_dir():
            reason = "BATCH_PREFLIGHT_BLOCKED"
            args.report.write_text(report_text(rows, phase="STOP BEFORE WRITES", stopped_reason=reason),
                                   encoding="utf8")
            raise ImportPlanError(reason)
        args.report.write_text(report_text(rows, phase="PREFLIGHT PASS / ZERO OPERATOR WRITES"),
                               encoding="utf8")
        print(json.dumps({"preflight": "PASS", "counts": dict(Counter(row.classification for row in rows))}))
        if not args.commit:
            return
        failure = commit_ready(rows, args.manifest, args.manifest.parent / "json",
                               args.source_root, decision, engine, settings.sds_root_path)
        status = "BATCH COMMIT COMPLETE" if failure is None else "STOP AFTER ITEM FAILURE"
        args.report.write_text(report_text(rows, phase=status,
                                           stopped_reason=str(failure) if failure else None),
                               encoding="utf8")
        print(json.dumps({"commit_status": status, "committed": sum(
            item.action == "COMMITTED" for item in rows), "failed": sum(
            item.action == "FAILED_DURING_COMMIT" for item in rows)}))
        if failure is not None:
            raise ImportPlanError("BATCH_COMMIT_STOPPED") from failure
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except ImportPlanError as error:
        raise SystemExit(f"TASK-057 STOP: {error}") from None
