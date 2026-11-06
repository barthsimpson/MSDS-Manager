"""TASK-058 decisions and controlled correction on disposable PostgreSQL."""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.application.use_cases.controlled_evidence_import import ImportPlanError
from app.domain.enums import FileAvailabilityStatus, ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, ManufacturerModel, ProductHistoryModel, ProductIdentityChangeModel,
    ProductModel, SafetyProfileModel, SdsComponentModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from scripts.task058_resolve_review_identity import REVIEW_IDS, commit_ready, preflight_review
from tests.integration.test_task054_operator_flow import isolated_database


BATCH = Path("docs/sds_bootstrap/BATCH-001_CX")
MANUFACTURER_ID = "a11c4d78f64b41f89de6ec0196a9254b"
LEGACY_CX80 = "5a43d93166e845d597a296986f2798f7"
LEGACY_MIXED = "a635199aa44944bbbf31cb63808f58d3"
P023_ID = "e8d4fa16679240adb1bf094578367f05"
P037_ID = "833c0080c0a34bd1a40f5b2be18b82a6"


def _fixture(tmp_path, *, p023_date="2023-01-02"):
    source = tmp_path / "source"
    source.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    original_manifest = json.loads((BATCH / "BATCH-001_MANIFEST.json").read_text(encoding="utf8"))
    entries, pdfs = [], {}
    for original in original_manifest["files"]:
        manifest_id = original["id"]
        if manifest_id not in REVIEW_IDS:
            continue
        pdf = f"%PDF-1.4\n{manifest_id}\n%%EOF\n".encode()
        pdfs[manifest_id] = pdf
        (source / original["source_file"]).write_bytes(pdf)
        payload = json.loads((BATCH / "json" / original["json"]).read_text(encoding="utf8"))
        payload["source"]["file_sha256"] = sha256(pdf).hexdigest()
        if manifest_id == "B001-P023":
            payload["documents"][0]["document_metadata"]["issue_date"]["value"] = p023_date
        (json_dir / original["json"]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf8")
        entry = dict(original)
        entry["sha256"] = sha256(pdf).hexdigest()
        entries.append(entry)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"batch": "BATCH-001_CX", "input_directory": str(tmp_path / "absent"),
                                    "files": entries}), encoding="utf8")
    report = tmp_path / "batch_report.md"
    report.write_text("# TASK-057\n\n" + "\n".join(
        "| " + " | ".join([manifest_id] + ["—"] * 12 + ["REVIEW_IDENTITY"] + ["—"] * 4) + " |"
        for manifest_id in REVIEW_IDS
    ) + "\n", encoding="utf8")
    root = tmp_path / "sds"
    root.mkdir()
    return manifest, source, report, root, pdfs


def _seed_product(session, product_id, name, code, manufacturer_id):
    session.add(ProductModel(
        product_id=product_id, product_name=name,
        manufacturer_product_code=code, manufacturer_id=manufacturer_id,
        use_description=None, use_restriction=None,
        usage_status=ProductUsageStatus.PENDING_APPROVAL,
    ))
    session.flush()


def _seed_sds(session, root, product_id, sds_id, pdf, issued, revision, status):
    relative = f"imported/{sds_id}.pdf"
    target = root / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(pdf)
    session.add(SdsDocumentModel(
        sds_id=sds_id, product_id=product_id, original_filename=f"{sds_id}.pdf",
        relative_path=relative, issue_date=date.fromisoformat(issued),
        revision=revision, document_status=status,
        registered_at=datetime.now(timezone.utc),
        file_status=FileAvailabilityStatus.AVAILABLE,
    ))
    session.flush()


def _seed_manufacturers(factory):
    with factory.begin() as session:
        session.add_all([
            ManufacturerModel(manufacturer_id=MANUFACTURER_ID, manufacturer_name="CX80 Polska"),
            ManufacturerModel(manufacturer_id=LEGACY_CX80, manufacturer_name="CX80"),
            ManufacturerModel(manufacturer_id=LEGACY_MIXED, manufacturer_name="Cx80"),
        ])


def _paths(manifest, source, report):
    return (manifest, source, BATCH / "BATCH-001_STAGE1_REVIEW_DECISIONS.json",
            BATCH / "BATCH-001_STAGE1_BATCH_DECISION.json", report)


def _preflight(factory, manifest, source, report, root):
    with factory() as session:
        return preflight_review(*_paths(manifest, source, report), session, root)


def test_eleven_decisions_create_correct_and_preserve_reviews(isolated_database, tmp_path):
    engine, factory = isolated_database
    manifest, source, report, root, pdfs = _fixture(tmp_path)
    _seed_manufacturers(factory)
    with factory.begin() as session:
        _seed_product(session, "cleaner", "Cleaner prof", None, MANUFACTURER_ID)
        _seed_sds(session, root, "cleaner", "cleaner-sds", pdfs["B001-P012"],
                  "2023-01-23", "2.0", SdsDocumentStatus.CURRENT)
        _seed_product(session, P023_ID, "CX80 Płyn Konserwująco Naprawczy",
                      "0300-F0DT-500F-GJ25", LEGACY_CX80)
        _seed_sds(session, root, P023_ID, "p023-sds", pdfs["B001-P023"],
                  "2023-01-02", "1.0", SdsDocumentStatus.CURRENT)
        _seed_product(session, P037_ID, "XBRAKE CLEANER", "CX80 XBRAKE CLEANER", LEGACY_MIXED)
        _seed_sds(session, root, P037_ID, "p028-archived", pdfs["B001-P028"],
                  "2025-01-15", "3.0", SdsDocumentStatus.ARCHIVED)
        _seed_sds(session, root, P037_ID, "p037-current", b"%PDF-1.4\ncurrent\n%%EOF\n",
                  "2026-09-01", "test delete", SdsDocumentStatus.CURRENT)
    rows = _preflight(factory, manifest, source, report, root)
    status = {row.item.manifest_id: row.item.classification for row in rows}
    assert list(status.values()).count("READY_CREATE") == 8
    assert status["B001-P023"] == "READY_IDENTITY_CORRECTION_ONLY"
    assert status["B001-P012"] == "REVIEW_IDENTITY"
    assert status["B001-P037"] == "REVIEW_SOURCE_CONFLICT"
    assert commit_ready(rows, *_paths(manifest, source, report), engine, root) is None
    actions = {row.item.manifest_id: row.item.action for row in rows}
    assert list(actions.values()).count("COMMITTED") == 8
    assert actions["B001-P023"] == "CORRECTED_ONLY"
    assert actions["B001-P012"] == actions["B001-P037"] == "NOT_ATTEMPTED"
    with factory() as session:
        products = session.scalars(select(ProductModel)).all()
        documents = session.scalars(select(SdsDocumentModel)).all()
        histories = session.scalars(select(ProductHistoryModel)).all()
        changes = session.scalars(select(ProductIdentityChangeModel)).all()
        assert len(products) == 11
        assert len(documents) == 12
        assert len(histories) == 8
        assert len(changes) == 1
        assert changes[0].change_kind == "CORRECTION"
        assert changes[0].product_id == P023_ID
        assert changes[0].old_manufacturer_id == LEGACY_CX80
        assert changes[0].new_manufacturer_id == MANUFACTURER_ID
        assert changes[0].old_manufacturer_product_code == changes[0].new_manufacturer_product_code == "0300-F0DT-500F-GJ25"
        assert session.get(ProductModel, P023_ID).manufacturer_id == MANUFACTURER_ID
        assert session.get(ProductModel, P037_ID).manufacturer_id == LEGACY_MIXED
        created_p028 = next(row for row in products if row.product_name == "XBRAKE CLEANER liquid")
        assert created_p028.product_id != P037_ID
        assert created_p028.manufacturer_product_code is None
        assert all((history.use_description, history.use_restriction) == (None, None)
                   for history in histories)
        assert session.scalars(select(SafetyProfileModel)).all() == []
        assert session.scalars(select(SdsComponentModel)).all() == []
        assert session.scalars(select(BhpDecisionModel)).all() == []
    assert len(list(root.rglob("*.pdf"))) == 12


def test_correction_revision_is_atomic_and_compensates_failure(isolated_database, tmp_path,
                                                               monkeypatch):
    engine, factory = isolated_database
    manifest, source, report, root, pdfs = _fixture(tmp_path, p023_date="2025-01-02")
    _seed_manufacturers(factory)
    with factory.begin() as session:
        _seed_product(session, P023_ID, "CX80 Płyn Konserwująco Naprawczy",
                      "0300-F0DT-500F-GJ25", LEGACY_CX80)
        _seed_sds(session, root, P023_ID, "old-sds", b"%PDF-1.4\nold\n%%EOF\n",
                  "2023-01-02", "1.0", SdsDocumentStatus.CURRENT)
    with factory() as session:
        rows = preflight_review(*_paths(manifest, source, report), session, root,
                                manifest_ids={"B001-P023"})
    assert rows[0].item.classification == "READY_IDENTITY_CORRECTION_AND_ADD_REVISION"
    original = SqlAlchemySdsAcceptanceRepository._persist_sds

    def fail_after_flush(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        raise RuntimeError("injected revision failure")

    with monkeypatch.context() as patcher:
        patcher.setattr(SqlAlchemySdsAcceptanceRepository, "_persist_sds", fail_after_flush)
        failure = commit_ready(rows, *_paths(manifest, source, report), engine, root)
    assert isinstance(failure, RuntimeError)
    assert rows[0].item.action == "FAILED_DURING_COMMIT"
    with factory() as session:
        assert session.get(ProductModel, P023_ID).manufacturer_id == LEGACY_CX80
        assert session.get(SdsDocumentModel, "old-sds").document_status == SdsDocumentStatus.CURRENT
        assert len(session.scalars(select(SdsDocumentModel)).all()) == 1
        assert session.scalars(select(ProductIdentityChangeModel)).all() == []
    assert len(list(root.rglob("*.pdf"))) == 1

    rows = None
    with factory() as session:
        rows = preflight_review(*_paths(manifest, source, report), session, root,
                                manifest_ids={"B001-P023"})
    assert commit_ready(rows, *_paths(manifest, source, report), engine, root) is None
    with factory() as session:
        product = session.get(ProductModel, P023_ID)
        documents = session.scalars(select(SdsDocumentModel)).all()
        changes = session.scalars(select(ProductIdentityChangeModel)).all()
        assert product.manufacturer_id == MANUFACTURER_ID
        assert product.manufacturer_product_code == "0300-F0DT-500F-GJ25"
        assert len(documents) == 2
        assert session.get(SdsDocumentModel, "old-sds").document_status == SdsDocumentStatus.ARCHIVED
        new, = [row for row in documents if row.sds_id != "old-sds"]
        assert new.document_status == SdsDocumentStatus.CURRENT
        assert sha256((root / new.relative_path).read_bytes()).hexdigest() == sha256(pdfs["B001-P023"]).hexdigest()
        assert len(changes) == 1 and changes[0].change_kind == "CORRECTION"
        assert session.scalars(select(SafetyProfileModel)).all() == []
    assert len(list(root.rglob("*.pdf"))) == 2


def test_same_metadata_different_source_is_review_without_write(isolated_database, tmp_path):
    engine, factory = isolated_database
    manifest, source, report, root, _ = _fixture(tmp_path)
    _seed_manufacturers(factory)
    with factory.begin() as session:
        _seed_product(session, P023_ID, "CX80 Płyn Konserwująco Naprawczy",
                      "0300-F0DT-500F-GJ25", LEGACY_CX80)
        _seed_sds(session, root, P023_ID, "old-sds", b"%PDF-1.4\nDifferent\n%%EOF\n",
                  "2023-01-02", "1.0", SdsDocumentStatus.CURRENT)
    with factory() as session:
        rows = preflight_review(*_paths(manifest, source, report), session, root,
                                manifest_ids={"B001-P023"})
    assert rows[0].item.classification == "REVIEW_SOURCE_CONFLICT"
    assert commit_ready(rows, *_paths(manifest, source, report), engine, root) is None
    with factory() as session:
        assert session.get(ProductModel, P023_ID).manufacturer_id == LEGACY_CX80
        assert len(session.scalars(select(SdsDocumentModel)).all()) == 1
        assert session.scalars(select(ProductIdentityChangeModel)).all() == []
    assert len(list(root.rglob("*.pdf"))) == 1


def test_hash_mismatch_blocks_all_ready_writes(isolated_database, tmp_path):
    engine, factory = isolated_database
    manifest, source, report, root, _ = _fixture(tmp_path)
    _seed_manufacturers(factory)
    filename = next(entry["source_file"] for entry in json.loads(manifest.read_text())["files"]
                    if entry["id"] == "B001-P031")
    (source / filename).write_bytes(b"%PDF-1.4\nTampered\n")
    rows = _preflight(factory, manifest, source, report, root)
    assert next(row.item.classification for row in rows if row.item.manifest_id == "B001-P031") == "BLOCKED_SOURCE"
    with pytest.raises(ImportPlanError, match="TASK058_PREFLIGHT_BLOCKED"):
        commit_ready(rows, *_paths(manifest, source, report), engine, root)
    with factory() as session:
        assert session.scalars(select(ProductModel)).all() == []
        assert session.scalars(select(SdsDocumentModel)).all() == []
    assert list(root.rglob("*.pdf")) == []
