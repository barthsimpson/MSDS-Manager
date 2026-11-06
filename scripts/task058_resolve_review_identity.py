"""Resolve only the eleven approved BATCH-001_CX Stage 1 review entries."""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.application.dto import CorrectProductIdentityInput
from app.application.dto.approved_import import IdentityDecision
from app.application.dto.sds import Stage1SdsInput
from app.application.use_cases.correct_and_register_stage1_sds import CorrectAndRegisterStage1Sds
from app.application.use_cases.correct_product_identity import CorrectProductIdentity
from app.application.use_cases.controlled_evidence_import import ControlledEvidenceImport, ImportPlanError
from app.application.use_cases.import_sds import ImportSds
from app.infrastructure.config import load_settings
from app.infrastructure.db.controlled_evidence_registration import SqlAlchemyControlledEvidenceRegistration
from app.infrastructure.db.models import ManufacturerModel, ProductIdentityChangeModel, ProductModel, SdsDocumentModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.repositories.product import SqlAlchemyProductRepository
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.db.transactions import TransactionExecutor
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator
from scripts.task057_stage1_batch_import import (
    BatchItem, BatchManufacturerDecision, _approve_item, _classify_identity,
    _schema_pass, _sds_state, preflight as source_preflight,
)


REVIEW_IDS = (
    "B001-P005", "B001-P008", "B001-P011", "B001-P012", "B001-P014",
    "B001-P023", "B001-P025", "B001-P026", "B001-P028", "B001-P031", "B001-P037",
)
READY = {"READY_CREATE", "READY_ADD_REVISION", "READY_IDENTITY_CORRECTION_ONLY",
         "READY_IDENTITY_CORRECTION_AND_ADD_REVISION"}
BLOCKED = {"BLOCKED_SOURCE", "BLOCKED_DATA"}
REPORT_MARKER = "## TASK-058 — Review identity resolution"


@dataclass
class Resolution:
    item: BatchItem
    manufacturer_decision_id: str
    manufacturer_plan_name: str
    product_decision: str
    correction: dict | None = None
    correction_change_id: str | None = None


def _review_ids_from_prior_report(path: Path) -> set[str]:
    historic = path.read_text(encoding="utf8").split(REPORT_MARKER, 1)[0]
    ids = set()
    for line in historic.splitlines():
        if not line.startswith("| B001-P"):
            continue
        fields = [part.strip() for part in line.strip("|").split("|")]
        if len(fields) == 18 and fields[13] == "REVIEW_IDENTITY":
            ids.add(fields[0])
    if ids != set(REVIEW_IDS):
        raise ImportPlanError("TASK057_REVIEW_SET_CHANGED")
    return ids


def _load_decisions(path: Path, base: BatchManufacturerDecision) -> tuple[dict, dict]:
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise ImportPlanError("INVALID_REVIEW_DECISIONS") from error
    if (payload.get("source_batch") != base.batch
            or not isinstance(payload.get("approved_by"), str)
            or not payload["approved_by"].strip()):
        raise ImportPlanError("INVALID_REVIEW_DECISIONS")
    manufacturers, products = {}, {}
    for decision in payload.get("manufacturer_decisions", []):
        if (decision.get("decision_id") not in {"M1", "M2", "M3"}
                or decision.get("source_batch") != base.batch
                or decision.get("canonical_target_name") != base.existing_manufacturer_name
                or decision.get("human_approved") is not True
                or decision.get("status") != "APPROVED_BATCH_DECISION"
                or not isinstance(decision.get("observed_value"), str)):
            raise ImportPlanError("INVALID_MANUFACTURER_DECISION")
        for manifest_id in decision.get("source_manifest_ids", []):
            if manifest_id in manufacturers:
                raise ImportPlanError("DUPLICATE_MANUFACTURER_DECISION")
            manufacturers[manifest_id] = decision
    if set(manufacturers) != set(REVIEW_IDS) - {"B001-P023", "B001-P028", "B001-P037"}:
        raise ImportPlanError("INCOMPLETE_MANUFACTURER_DECISIONS")
    targets = {row["canonical_target_id"] for row in manufacturers.values()}
    if len(targets) != 1:
        raise ImportPlanError("MANUFACTURER_TARGET_CONFLICT")
    for decision in payload.get("product_decisions", []):
        manifest_id = decision.get("manifest_id")
        expected_action = {
            "B001-P023": "CORRECT_EXISTING_PRODUCT",
            "B001-P028": "CREATE_DISTINCT_PRODUCT",
            "B001-P037": "CORRECT_EXISTING_PRODUCT",
        }.get(manifest_id)
        if (manifest_id in products or decision.get("human_approved") is not True
                or decision.get("status") != "APPROVED_BATCH_DECISION"
                or decision.get("new_manufacturer_id") not in targets
                or decision.get("action") != expected_action):
            raise ImportPlanError("INVALID_PRODUCT_DECISION")
        products[manifest_id] = decision
    if set(products) != {"B001-P023", "B001-P028", "B001-P037"}:
        raise ImportPlanError("INCOMPLETE_PRODUCT_DECISIONS")
    return manufacturers, products


def _classify_correction(resolution: Resolution, session: Session, target_id: str,
                         storage: SdsPdfStorage, decision: dict) -> None:
    item = resolution.item
    product = session.get(ProductModel, decision["product_id"])
    if (product is None or decision["action"] != "CORRECT_EXISTING_PRODUCT"
            or product.product_name != decision["preserve_name"]
            or product.manufacturer_product_code != decision["preserve_code"]
            or product.manufacturer_id != decision["old_manufacturer_id"]
            or decision["new_manufacturer_id"] != target_id
            or item.manufacturer_product_code is not None):
        item.classification, item.reason = "REVIEW_IDENTITY", "APPROVED_PRODUCT_SNAPSHOT_MISMATCH"
        return
    item.product_id = product.product_id
    item.existing_product_candidates = [{
        "product_id": product.product_id, "name": product.product_name,
        "code": product.manufacturer_product_code,
        "manufacturer_id": product.manufacturer_id,
    }]
    item.existing_current_sds, error = _sds_state(session, product.product_id, storage)
    if error:
        item.classification, item.reason = "BLOCKED_DATA", error
        return
    current = [row for row in item.existing_current_sds if row["status"] == "CURRENT"]
    if len(current) != 1:
        item.classification, item.reason = "REVIEW_SOURCE_CONFLICT", "CURRENT_SDS_NOT_UNIQUE"
        return
    same_metadata = [row for row in item.existing_current_sds
                     if row["issue_date"] == item.issue_date.isoformat()
                     and row["revision"] == item.revision]
    if any(row["sha256"] != item.source_sha_actual for row in same_metadata):
        item.classification, item.reason = "REVIEW_SOURCE_CONFLICT", "SDS_METADATA_SOURCE_CONFLICT"
        return
    same_pdf = [row for row in item.existing_current_sds
                if row["sha256"] == item.source_sha_actual]
    if same_metadata:
        item.sds_id = same_metadata[0]["sds_id"]
        item.classification, item.reason = (
            "READY_IDENTITY_CORRECTION_ONLY", "EXACT_EXISTING_SDS_CORRECT_MANUFACTURER",
        )
    elif same_pdf:
        item.classification, item.reason = "REVIEW_SOURCE_CONFLICT", "PDF_METADATA_CONFLICT"
    else:
        current_date = date.fromisoformat(current[0]["issue_date"]) if current[0]["issue_date"] else None
        if current_date is None or item.issue_date <= current_date:
            item.classification, item.reason = (
                "REVIEW_SOURCE_CONFLICT", "INCOMING_NOT_NEWER_THAN_CURRENT_SDS",
            )
        else:
            item.classification, item.reason = (
                "READY_IDENTITY_CORRECTION_AND_ADD_REVISION", "NEW_SDS_AFTER_CORRECTION",
            )
    if item.classification in READY:
        resolution.correction = decision


def preflight_review(manifest: Path, source_root: Path, review_decisions: Path,
                     batch_decision: Path, batch_report: Path,
                     session: Session, sds_root: Path,
                     manifest_ids: set[str] | None = None) -> list[Resolution]:
    base = BatchManufacturerDecision.from_bytes(batch_decision.read_bytes())
    _review_ids_from_prior_report(batch_report)
    manufacturers, products = _load_decisions(review_decisions, base)
    ids = set(REVIEW_IDS) if manifest_ids is None else manifest_ids
    if not ids <= set(REVIEW_IDS):
        raise ImportPlanError("OUT_OF_SCOPE_MANIFEST_ID")
    items = source_preflight(manifest, manifest.parent / "json", source_root,
                             base, session, sds_root, manifest_ids=ids)
    if {item.manifest_id for item in items} != ids:
        raise ImportPlanError("INCOMPLETE_REVIEW_PREFLIGHT")
    target_id = manufacturers["B001-P005"]["canonical_target_id"]
    target = session.get(ManufacturerModel, target_id)
    if target is None or target.manufacturer_name != base.existing_manufacturer_name:
        for item in items:
            item.classification, item.reason = "BLOCKED_DATA", "APPROVED_MANUFACTURER_MISSING"
        return [Resolution(item, "INVALID", "", "NONE") for item in items]
    storage = SdsPdfStorage(sds_root)
    result = []
    for item in items:
        manifest_id = item.manifest_id
        manufacturer = manufacturers.get(manifest_id)
        product_decision = products.get(manifest_id)
        decision_id = manufacturer["decision_id"] if manufacturer else "TASK-057"
        plan_name = (base.canonical_manufacturer if manufacturer is None
                     else base.existing_manufacturer_name)
        resolution = Resolution(item, decision_id, plan_name,
                                product_decision["action"] if product_decision else "RESOLVE_EXACT")
        result.append(resolution)
        if item.classification in BLOCKED:
            continue
        if (manufacturer and (item.manufacturer_canonical != manufacturer["observed_value"]
                              or manufacturer["canonical_target_id"] != target_id)
                or not manufacturer and item.manufacturer_canonical != base.canonical_manufacturer):
            item.classification, item.reason = "BLOCKED_DATA", "DECISION_SOURCE_MISMATCH"
            continue
        item.manufacturer_selected_id = target_id
        item.manufacturer_selected_name = target.manufacturer_name
        if product_decision and product_decision["action"] == "CORRECT_EXISTING_PRODUCT":
            _classify_correction(resolution, session, target_id, storage, product_decision)
            continue
        if product_decision and product_decision["action"] == "CREATE_DISTINCT_PRODUCT":
            if (item.product_name != product_decision["product_name"]
                    or item.manufacturer_product_code != product_decision["manufacturer_product_code"]):
                item.classification, item.reason = "BLOCKED_DATA", "PRODUCT_DECISION_SOURCE_MISMATCH"
                continue
        _classify_identity(item, session, target_id, storage)
        if item.existing_product_candidates and not item.existing_current_sds:
            for candidate in item.existing_product_candidates:
                candidate_sds, error = _sds_state(session, candidate["product_id"], storage)
                if error:
                    item.classification, item.reason = "BLOCKED_DATA", error
                    break
                item.existing_current_sds.extend({"product_id": candidate["product_id"], **row}
                                                 for row in candidate_sds)
        if item.classification in BLOCKED:
            continue
        if product_decision and product_decision["action"] == "CREATE_DISTINCT_PRODUCT" \
                and item.classification == "REVIEW_IDENTITY":
            selected_exact = [row for row in item.existing_product_candidates
                              if row["manufacturer_id"] == target_id
                              and row["name"] == item.product_name]
            if not selected_exact:
                item.classification, item.reason = "READY_CREATE", "APPROVED_DISTINCT_PRODUCT"
        if manifest_id == "B001-P012" and item.classification == "REVIEW_IDENTITY":
            item.reason = "CASE_VARIANT_PRODUCT_LINK_NOT_APPROVED"
        if item.classification == "BLOCKED_DATA" and item.reason == "SDS_METADATA_SOURCE_CONFLICT":
            item.classification = "REVIEW_SOURCE_CONFLICT"
        if item.classification in {"READY_CREATE", "READY_ADD_REVISION"}:
            read = SqlAlchemyEvidenceIdentityRead(session)
            approval = BatchManufacturerDecision(base.batch, plan_name,
                                                 base.existing_manufacturer_name,
                                                 "TASK-058 Architect decision")
            try:
                _approve_item(item, read, approval, target_id,
                              target.manufacturer_name, item.raw_json, item.pdf_bytes)
            except ImportPlanError as error:
                item.classification, item.reason = "BLOCKED_DATA", f"APPROVED_PLAN_INVALID:{error}"
    return result


def _fresh_resolution(expected: Resolution, manifest: Path, source_root: Path,
                      review_decisions: Path, batch_decision: Path,
                      batch_report: Path, session: Session,
                      sds_root: Path) -> Resolution:
    fresh, = preflight_review(manifest, source_root, review_decisions, batch_decision,
                              batch_report, session, sds_root,
                              manifest_ids={expected.item.manifest_id})
    before, after = expected.item, fresh.item
    if (after.classification != before.classification
            or after.source_sha_actual != before.source_sha_actual
            or sha256(after.raw_json).digest() != sha256(before.raw_json).digest()
            or after.product_id != before.product_id
            or after.existing_current_sds != before.existing_current_sds
            or after.existing_product_candidates != before.existing_product_candidates):
        raise ImportPlanError(f"STALE_RESOLUTION:{before.manifest_id}")
    return fresh


def _correction_input(resolution: Resolution, target_name: str) -> CorrectProductIdentityInput:
    decision = resolution.correction
    return CorrectProductIdentityInput(
        product_id=decision["product_id"], product_name=decision["preserve_name"],
        manufacturer_product_code=decision["preserve_code"],
        manufacturer_name=target_name,
    )


def _lock_for_correction(session: Session) -> None:
    # Consistent with the existing controlled importer; this is a lock, not business SQL.
    session.execute(sql_text(
        "LOCK TABLE manufacturers, products, sds_documents IN SHARE ROW EXCLUSIVE MODE"
    ))


def _correction_audit(session: Session, product_id: str, old_id: str,
                      new_id: str, name: str, code: str) -> str:
    changes = session.scalars(select(ProductIdentityChangeModel).where(
        ProductIdentityChangeModel.product_id == product_id,
        ProductIdentityChangeModel.change_kind == "CORRECTION",
        ProductIdentityChangeModel.old_manufacturer_id == old_id,
        ProductIdentityChangeModel.new_manufacturer_id == new_id,
        ProductIdentityChangeModel.old_product_name == name,
        ProductIdentityChangeModel.new_product_name == name,
        ProductIdentityChangeModel.old_manufacturer_product_code == code,
        ProductIdentityChangeModel.new_manufacturer_product_code == code,
    ).order_by(ProductIdentityChangeModel.changed_at.desc())).all()
    if len(changes) != 1:
        raise ImportPlanError("CORRECTION_AUDIT_NOT_UNIQUE")
    return changes[0].change_id


def _commit_correction_only(expected: Resolution, manifest: Path, source_root: Path,
                            review_decisions: Path, batch_decision: Path,
                            batch_report: Path, factory, sds_root: Path) -> str:
    def operation(session: Session) -> str:
        _lock_for_correction(session)
        fresh = _fresh_resolution(expected, manifest, source_root, review_decisions,
                                  batch_decision, batch_report, session, sds_root)
        correction = fresh.correction
        target_name = fresh.item.manufacturer_selected_name
        CorrectProductIdentity(SqlAlchemyProductRepository(session)).execute(
            _correction_input(fresh, target_name)
        )
        return _correction_audit(session, correction["product_id"],
                                 correction["old_manufacturer_id"],
                                 correction["new_manufacturer_id"],
                                 correction["preserve_name"], correction["preserve_code"])

    return TransactionExecutor(factory).execute(operation)


def _commit_correction_revision(expected: Resolution, manifest: Path, source_root: Path,
                                review_decisions: Path, batch_decision: Path,
                                batch_report: Path, factory, sds_root: Path) -> tuple[str, str]:
    item = expected.item
    if expected.correction is None:
        raise ImportPlanError("CORRECTION_NOT_APPROVED")
    storage = SdsPdfStorage(sds_root)
    importer = ImportSds(storage)
    target_name = item.manufacturer_selected_name
    correction = _correction_input(expected, target_name)
    stage1 = Stage1SdsInput(
        source_relative_path="", original_filename=item.source_pdf,
        product_name=correction.product_name,
        manufacturer_product_code=correction.manufacturer_product_code,
        manufacturer_name=target_name,
        use_description=None, use_restriction=None,
        issue_date=item.issue_date, revision=item.revision,
        controlled_manufacturer_decision=IdentityDecision(
            "LINK", target_name, selected_id=item.manufacturer_selected_id,
            selected_record_name=target_name, manufacturer_link_confirmed=True,
        ),
        controlled_product_decision=IdentityDecision(
            "LINK", correction.product_name, selected_id=correction.product_id,
            manufacturer_product_code=correction.manufacturer_product_code,
        ),
        product_id=correction.product_id,
    )

    def register(data: Stage1SdsInput) -> tuple[str, str]:
        def operation(session: Session) -> tuple[str, str]:
            _lock_for_correction(session)
            fresh = _fresh_resolution(expected, manifest, source_root, review_decisions,
                                      batch_decision, batch_report, session, sds_root)
            application = CorrectAndRegisterStage1Sds(
                SqlAlchemyProductRepository(session),
                SqlAlchemySdsAcceptanceRepository(session, allow_controlled=True),
                SdsFileValidator(sds_root),
            )
            sds_id = application.execute(_correction_input(fresh, target_name), data)
            decision = fresh.correction
            change_id = _correction_audit(session, decision["product_id"],
                                          decision["old_manufacturer_id"],
                                          decision["new_manufacturer_id"],
                                          decision["preserve_name"], decision["preserve_code"])
            return sds_id, change_id

        return TransactionExecutor(factory).execute(operation)

    return importer.execute(stage1, item.source_pdf, item.pdf_bytes, register,
                            verify_product=lambda product_id: _verify_product(factory, product_id))


def _verify_product(factory, product_id: str) -> None:
    with factory() as session:
        if session.get(ProductModel, product_id) is None:
            raise ImportPlanError("PRODUCT_MISSING")


def commit_ready(rows: list[Resolution], manifest: Path, source_root: Path,
                 review_decisions: Path, batch_decision: Path,
                 batch_report: Path, engine, sds_root: Path) -> Exception | None:
    if any(row.item.classification in BLOCKED for row in rows):
        raise ImportPlanError("TASK058_PREFLIGHT_BLOCKED")
    factory = create_session_factory(engine)
    controlled = ControlledEvidenceImport(
        SqlAlchemyControlledEvidenceRegistration(factory, sds_root),
        ImportSds(SdsPdfStorage(sds_root)),
    )
    for row in rows:
        item = row.item
        if item.classification not in READY:
            continue
        try:
            if item.classification == "READY_IDENTITY_CORRECTION_ONLY":
                row.correction_change_id = _commit_correction_only(
                    row, manifest, source_root, review_decisions, batch_decision,
                    batch_report, factory, sds_root,
                )
                item.action, item.reason = "CORRECTED_ONLY", "CORRECTION_AUDIT_OK"
            elif item.classification == "READY_IDENTITY_CORRECTION_AND_ADD_REVISION":
                sds_id, row.correction_change_id = _commit_correction_revision(
                    row, manifest, source_root, review_decisions, batch_decision,
                    batch_report, factory, sds_root,
                )
                item.sds_id = sds_id
                item.action, item.reason = "CORRECTED_AND_COMMITTED", "ATOMIC_CORRECTION_REVISION_OK"
            else:
                with engine.connect().execution_options(postgresql_readonly=True) as connection:
                    with Session(bind=connection) as session:
                        fresh = _fresh_resolution(row, manifest, source_root, review_decisions,
                                                  batch_decision, batch_report, session, sds_root)
                        base = BatchManufacturerDecision.from_bytes(batch_decision.read_bytes())
                        approval = BatchManufacturerDecision(
                            base.batch, fresh.manufacturer_plan_name,
                            base.existing_manufacturer_name, "TASK-058 Architect decision",
                        )
                        plan = _approve_item(fresh.item, SqlAlchemyEvidenceIdentityRead(session),
                                             approval, fresh.item.manufacturer_selected_id,
                                             fresh.item.manufacturer_selected_name,
                                             fresh.item.raw_json, fresh.item.pdf_bytes)
                sds_id = controlled.execute(plan, fresh.item.raw_json, fresh.item.pdf_bytes)
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
    return "—" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def review_report(rows: list[Resolution], phase: str, failure: Exception | None = None,
                  historical_counts: Counter | None = None) -> str:
    counts = Counter(row.item.classification for row in rows)
    actions = Counter(row.item.action for row in rows)
    lines = [
        REPORT_MARKER, "", f"Status: **{phase}**" + (f" — {failure}" if failure else ""), "",
        "Decyzje producenta M1/M2/M3 są zatwierdzone wyłącznie dla BATCH-001_CX; "
        "pozostałe trzy pozycje korzystają z zatwierdzonego powiązania TASK-057. "
        "Nie aktywowano globalnej reguły normalizacji.", "",
        "### Counts for the eleven review entries", "",
    ]
    for name in ("READY_CREATE", "READY_ADD_REVISION", "READY_IDENTITY_CORRECTION_AND_ADD_REVISION",
                 "READY_IDENTITY_CORRECTION_ONLY", "SKIP_EXACT_EXISTING", "REVIEW_IDENTITY",
                 "REVIEW_SOURCE_CONFLICT", "BLOCKED_SOURCE", "BLOCKED_DATA"):
        lines.append(f"- {name}: {counts[name]}")
    for name in ("COMMITTED", "CORRECTED_ONLY", "CORRECTED_AND_COMMITTED",
                 "FAILED_DURING_COMMIT", "NOT_ATTEMPTED"):
        lines.append(f"- {name}: {actions[name]}")
    new_sds = actions["COMMITTED"] + actions["CORRECTED_AND_COMMITTED"]
    lines.append(f"- New operator PDFs in TASK-058: {new_sds}.")
    if phase == "TASK-058 COMMIT COMPLETE" and historical_counts is not None:
        imported = (historical_counts["COMMITTED"] + historical_counts["SKIP_EXACT_EXISTING"]
                    + actions["COMMITTED"] + actions["CORRECTED_ONLY"]
                    + actions["CORRECTED_AND_COMMITTED"])
        exact = (historical_counts["SKIP_EXACT_EXISTING"] + actions["CORRECTED_ONLY"]
                 + actions["SKIPPED"])
        review = sum(row.item.classification in {"REVIEW_IDENTITY", "REVIEW_SOURCE_CONFLICT"}
                     and row.item.action == "NOT_ATTEMPTED" for row in rows)
        lines.extend(("", "### Final BATCH-001_CX counts", "",
                      f"- Imported/registered logical SDS: {imported}.",
                      f"- Exact existing/skipped source: {exact}.",
                      f"- Duplicate source: {historical_counts['SKIP_DUPLICATE_SOURCE']}.",
                      f"- Excluded non-SDS: {historical_counts['EXCLUDED_NON_SDS']}.",
                      f"- Remaining REVIEW: {review}."))
    lines.extend(("", "### Full read-only preflight and final outcome", "",
                  "| Manifest ID | JSON | PDF | Expected SHA-256 | Actual SHA-256 | Manufacturer decision | Product decision | Existing PRODUCT candidates | Existing SDS (status/date/revision/SHA) | Planned correction | Final classification | Planned action | Action | product_id | sds_id | correction change_id | Reason |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"))
    for resolution in rows:
        item = resolution.item
        candidates = ", ".join(f"{row['product_id']}:{row['name']}:{row['code']}:{row['manufacturer_id']}"
                               for row in item.existing_product_candidates)
        sds = ", ".join(f"{row['sds_id']}:{row['status']}:{row['issue_date']}:{row['revision']}:{row['sha256']}"
                        for row in item.existing_current_sds)
        correction = (f"{resolution.correction['product_id']}:"
                      f"{resolution.correction['old_manufacturer_id']}→"
                      f"{resolution.correction['new_manufacturer_id']}:"
                      f"preserve {resolution.correction['preserve_name']}/"
                      f"{resolution.correction['preserve_code']}"
                      if resolution.correction else None)
        planned = ("CORRECT_ONLY" if item.classification == "READY_IDENTITY_CORRECTION_ONLY"
                   else "CORRECT_AND_ADD_REVISION"
                   if item.classification == "READY_IDENTITY_CORRECTION_AND_ADD_REVISION"
                   else "CONTROLLED_COMMIT" if item.classification in {"READY_CREATE", "READY_ADD_REVISION"}
                   else "SKIP" if item.classification == "SKIP_EXACT_EXISTING"
                   else "REVIEW / NO WRITE")
        values = (
            item.manifest_id, item.json_file, item.source_pdf,
            item.source_sha_expected, item.source_sha_actual,
            f"{resolution.manufacturer_decision_id}: {item.manufacturer_canonical} → "
            f"{item.manufacturer_selected_id}/{item.manufacturer_selected_name}",
            resolution.product_decision, candidates or None, sds or None,
            correction, item.classification, planned, item.action,
            item.product_id, item.sds_id, resolution.correction_change_id, item.reason,
        )
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    lines.extend(("", "STOP after BATCH-001_CX. Paczka2 and Stage 2 were not started.", ""))
    return "\n".join(lines)


def _write_review_report(path: Path, rows: list[Resolution], phase: str,
                         failure: Exception | None = None) -> None:
    historic = path.read_text(encoding="utf8").split(REPORT_MARKER, 1)[0].rstrip()
    old = Counter()
    for line in historic.splitlines():
        if line.startswith("| B001-P"):
            fields = [part.strip() for part in line.strip("|").split("|")]
            if len(fields) == 18:
                old[fields[13]] += 1
                old[fields[14]] += 1
    path.write_text(historic + "\n\n" + review_report(rows, phase, failure, old),
                    encoding="utf8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--batch-decision", type=Path, required=True)
    parser.add_argument("--review-decisions", type=Path, required=True)
    parser.add_argument("--batch-report", type=Path, required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    existing_report = args.batch_report.read_text(encoding="utf8")
    if (REPORT_MARKER in existing_report
            and "Status: **TASK-058 COMMIT COMPLETE**" in existing_report.split(REPORT_MARKER, 1)[1]):
        raise ImportPlanError("TASK058_ALREADY_COMPLETED")
    settings = load_settings()
    engine = create_engine_from_settings(settings)
    try:
        _schema_pass(engine)
        with engine.connect().execution_options(postgresql_readonly=True) as connection:
            with Session(bind=connection) as session:
                rows = preflight_review(args.manifest, args.source_root,
                                        args.review_decisions, args.batch_decision,
                                        args.batch_report, session, settings.sds_root_path)
        blocked = [row for row in rows if row.item.classification in BLOCKED]
        if blocked or len(rows) != 11 or not args.source_root.is_dir():
            _write_review_report(args.batch_report, rows, "STOP BEFORE WRITES")
            raise ImportPlanError("TASK058_PREFLIGHT_BLOCKED")
        _write_review_report(args.batch_report, rows, "PREFLIGHT PASS / ZERO OPERATOR WRITES")
        print(json.dumps({"preflight": "PASS", "counts": dict(Counter(
            row.item.classification for row in rows))}))
        if not args.commit:
            return
        failure = commit_ready(rows, args.manifest, args.source_root,
                               args.review_decisions, args.batch_decision,
                               args.batch_report, engine, settings.sds_root_path)
        status = "TASK-058 COMMIT COMPLETE" if failure is None else "STOP AFTER ITEM FAILURE"
        _write_review_report(args.batch_report, rows, status, failure)
        print(json.dumps({"commit_status": status, "actions": dict(Counter(
            row.item.action for row in rows))}))
        if failure is not None:
            raise ImportPlanError("TASK058_COMMIT_STOPPED") from failure
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except ImportPlanError as error:
        raise SystemExit(f"TASK-058 STOP: {error}") from None
