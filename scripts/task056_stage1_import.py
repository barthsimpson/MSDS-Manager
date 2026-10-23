"""Precheck or import one batch-approved Stage 1 Evidence JSON."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.orm import Session

from app.application.use_cases.automatic_stage1_import import AutomaticStage1Import, BatchStage1Decision
from app.application.use_cases.controlled_evidence_import import ControlledEvidenceImport, ImportPlanError
from app.application.use_cases.import_sds import ImportSds
from app.infrastructure.config import load_settings
from app.infrastructure.db.controlled_evidence_registration import SqlAlchemyControlledEvidenceRegistration
from app.infrastructure.db.models import ProductModel, SdsDocumentModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.filesystem.evidence_source_pdf import resolve_source_pdf
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


def _source(
    evidence_json: Path, manifest: Path, decision: BatchStage1Decision,
    source_root: Path | None = None,
) -> tuple[bytes, bytes, str]:
    raw = evidence_json.read_bytes()
    if evidence_json.name != decision.evidence_json or sha256(raw).hexdigest() != decision.json_sha256:
        raise ImportPlanError("SOURCE_CHANGED")
    try:
        payload = json.loads(raw)
        manifest_data = json.loads(manifest.read_bytes())
    except (TypeError, ValueError) as error:
        raise ImportPlanError("INVALID_SOURCE_CONTEXT") from error
    if not isinstance(payload, dict):
        raise ImportPlanError("INVALID_EVIDENCE_JSON")
    if not isinstance(manifest_data, dict) or manifest_data.get("batch") != decision.batch:
        raise ImportPlanError("BATCH_MISMATCH")
    files = manifest_data.get("files")
    if not isinstance(files, list):
        raise ImportPlanError("MANIFEST_MISMATCH")
    entries = [item for item in files
               if isinstance(item, dict) and item.get("json") == evidence_json.name]
    if (len(entries) != 1 or not evidence_json.stem.endswith("_" + decision.document_key)
            or entries[0].get("logical_sds_count") != 1
            or entries[0].get("source_file")
            != payload.get("source", {}).get("original_filename")
            or entries[0].get("sha256") != decision.source_pdf_sha256):
        raise ImportPlanError("MANIFEST_MISMATCH")
    binding = resolve_source_pdf(manifest, evidence_json.name, payload,
                                 source_root=source_root)
    if binding.status == "PDF_MISMATCH":
        raise ImportPlanError("PDF_MISMATCH")
    if binding.status != "AUTO_BOUND" or binding.content is None or binding.filename is None:
        raise ImportPlanError(f"SOURCE_PDF_UNAVAILABLE: {binding.status}")
    return raw, binding.content, binding.filename


def _migration_precheck(engine) -> None:
    config = Config("alembic.ini")
    head = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect().execution_options(postgresql_readonly=True) as connection:
        current = MigrationContext.configure(connection).get_current_revision()
        connection.rollback()
    if current != head:
        raise ImportPlanError(f"ALEMBIC_NOT_AT_HEAD: {current}")
    command.check(config)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_json", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--source-root", type=Path,
                        help="Override only the manifest input_directory for this run")
    parser.add_argument("--commit", action="store_true", help="Commit this one prepared item after PASS precheck")
    args = parser.parse_args()

    decision = BatchStage1Decision.from_json(args.decision.read_bytes())
    raw, pdf, filename = _source(args.evidence_json, args.manifest, decision,
                                 args.source_root)
    settings = load_settings()
    engine = create_engine_from_settings(settings)
    try:
        _migration_precheck(engine)
        factory = create_session_factory(engine)
        with engine.connect().execution_options(postgresql_readonly=True) as connection:
            with Session(bind=connection) as session:
                plan = AutomaticStage1Import().prepare(
                    raw, args.evidence_json.name, pdf, decision,
                    SqlAlchemyEvidenceIdentityRead(session),
                )
        summary = {
            "status": "PASS", "action": "CREATE_PRODUCT_AND_SDS",
            "json_sha256": plan.source_json_fingerprint,
            "pdf_sha256": plan.pdf_fingerprint, "pdf_filename": filename,
            "manufacturer_id": plan.manufacturer_decision.selected_id,
            "manufacturer_name": plan.manufacturer_selected_name,
            "product_name": plan.product_decision.name,
            "manufacturer_product_code": plan.product_decision.manufacturer_product_code,
            "use_description": plan.use_description,
            "use_restriction": plan.use_restriction,
            "issue_date": plan.issue_date.isoformat() if plan.issue_date else None,
            "revision": plan.revision,
            "safety_readiness": plan.safety_readiness,
        }
        print(json.dumps(summary, ensure_ascii=False))
        if not args.commit:
            return
        sds_id = ControlledEvidenceImport(
            SqlAlchemyControlledEvidenceRegistration(factory, settings.sds_root_path),
            ImportSds(SdsPdfStorage(settings.sds_root_path)),
        ).execute(plan, raw, pdf)
        with engine.connect().execution_options(postgresql_readonly=True) as connection:
            with Session(bind=connection) as session:
                sds = session.get(SdsDocumentModel, sds_id)
                product = session.get(ProductModel, sds.product_id)
                result = {
                    "status": "COMMITTED", "product_id": product.product_id,
                    "sds_id": sds_id, "manufacturer_id": product.manufacturer_id,
                    "manufacturer_name": plan.manufacturer_selected_name,
                    "pdf_relative_path": sds.relative_path,
                    "document_status": sds.document_status.value,
                }
        print(json.dumps(result, ensure_ascii=False))
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except ImportPlanError as error:
        raise SystemExit(f"PRECHECK STOP: {error}") from None
