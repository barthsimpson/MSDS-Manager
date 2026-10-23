"""TASK-057 batch orchestration on disposable PostgreSQL and SDS storage."""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.use_cases.controlled_evidence_import import ImportPlanError
from app.domain.enums import FileAvailabilityStatus, ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, ManufacturerModel, ProductHistoryModel, ProductModel,
    SafetyProfileModel, SdsComponentModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from scripts.task057_stage1_batch_import import (
    BatchManufacturerDecision, commit_ready, preflight, report_text,
)
from tests.integration.test_task054_operator_flow import isolated_database


DECISION = BatchManufacturerDecision(
    "BATCH-001_CX", "CX80 POLSKA", "CX80 Polska", "TASK-057 isolated test",
)
TEMPLATE = json.loads(Path(
    "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
).read_text(encoding="utf8"))


def _item(tmp_path, number: int, name: str, *, pdf: bytes | None = None,
          issued: str = "2023-01-23", revision: str = "2.0") -> dict:
    pdf = pdf if pdf is not None else f"%PDF-1.4\nItem {number}\n%%EOF\n".encode()
    entry_id = f"B001-P{number:03d}"
    filename = f"{entry_id}.pdf"
    payload = json.loads(json.dumps(TEMPLATE, ensure_ascii=False))
    payload["source"]["original_filename"] = filename
    payload["source"]["file_sha256"] = sha256(pdf).hexdigest()
    document = payload["documents"][0]
    document["product"]["product_name"]["value"] = name
    document["product"]["product_name"]["evidence"][0]["source_text"] = (
        f"1.1. Identyfikator produktu {name}"
    )
    document["document_metadata"]["issue_date"]["value"] = issued
    document["document_metadata"]["revision"]["value"] = revision
    for field in ("issue_date", "revision"):
        document["document_metadata"][field]["evidence"][0]["source_text"] = (
            f"Data aktualizacji {issued} Numer wersji {revision}"
        )
    json_dir = tmp_path / "json"
    json_dir.mkdir(exist_ok=True)
    json_file = f"{entry_id}_DOC-001.json"
    (json_dir / json_file).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf8")
    source_root = tmp_path / "source"
    source_root.mkdir(exist_ok=True)
    (source_root / filename).write_bytes(pdf)
    return {"id": entry_id, "json": json_file, "source_file": filename,
            "sha256": sha256(pdf).hexdigest(), "logical_sds_count": 1,
            "status": "COMPLETE"}


def _manifest(tmp_path, entries):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "batch": "BATCH-001_CX", "input_directory": str(tmp_path / "absent"),
        "files": entries,
    }), encoding="utf8")
    return path


def _seed_product(session, product_id: str, name: str, manufacturer_id: str):
    session.add(ProductModel(
        product_id=product_id, product_name=name, manufacturer_id=manufacturer_id,
        manufacturer_product_code=None, use_description=None, use_restriction=None,
        usage_status=ProductUsageStatus.PENDING_APPROVAL,
    ))
    session.flush()


def _seed_sds(session, root, product_id, sds_id, pdf, *, issued, revision):
    relative = f"imported/{sds_id}.pdf"
    target = root / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(pdf)
    session.add(SdsDocumentModel(
        sds_id=sds_id, product_id=product_id, original_filename=f"{sds_id}.pdf",
        relative_path=relative, issue_date=date.fromisoformat(issued),
        revision=revision, document_status=SdsDocumentStatus.CURRENT,
        registered_at=datetime.now(timezone.utc),
        file_status=FileAvailabilityStatus.AVAILABLE,
    ))
    session.flush()


def _readiness(factory, manifest, tmp_path, root):
    with factory() as session:
        return preflight(manifest, tmp_path / "json", tmp_path / "source",
                         DECISION, session, root)


def test_full_mixed_batch_commits_only_ready_items(isolated_database, tmp_path):
    engine, factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    entries = [
        _item(tmp_path, 1, "EXACT EXISTING"),
        _item(tmp_path, 2, "NEW ALPHA"),
        _item(tmp_path, 3, "NEW BETA"),
        _item(tmp_path, 4, "REVISION PRODUCT", issued="2024-01-23", revision="3.0"),
        _item(tmp_path, 5, "REVIEW PRODUCT"),
        _item(tmp_path, 6, "NEW ALPHA", pdf=(tmp_path / "source" / "B001-P002.pdf").read_bytes()),
    ]
    manifest = _manifest(tmp_path, entries)
    with factory.begin() as session:
        session.add_all([
            ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"),
            ManufacturerModel(manufacturer_id="variant", manufacturer_name="Cx80"),
        ])
        session.flush()
        _seed_product(session, "exact", "EXACT EXISTING", "approved")
        _seed_sds(session, root, "exact", "existing-sds",
                  (tmp_path / "source" / "B001-P001.pdf").read_bytes(),
                  issued="2023-01-23", revision="2.0")
        _seed_product(session, "revision", "REVISION PRODUCT", "approved")
        _seed_sds(session, root, "revision", "old-sds", b"%PDF-1.4\nOlder\n%%EOF\n",
                  issued="2023-01-23", revision="2.0")
        _seed_product(session, "variant-product", "REVIEW PRODUCT", "variant")
    rows = _readiness(factory, manifest, tmp_path, root)
    assert [row.classification for row in rows] == [
        "SKIP_EXACT_EXISTING", "READY_CREATE", "READY_CREATE",
        "READY_ADD_REVISION", "REVIEW_IDENTITY", "SKIP_DUPLICATE_SOURCE",
    ]
    assert rows[0].sds_id == "existing-sds"
    assert rows[4].existing_product_candidates[0]["manufacturer_id"] == "variant"
    assert "Status: **PREFLIGHT" in report_text(rows, phase="PREFLIGHT PASS")
    assert commit_ready(rows, manifest, tmp_path / "json", tmp_path / "source",
                        DECISION, engine, root) is None
    assert [row.action for row in rows] == [
        "SKIPPED", "COMMITTED", "COMMITTED", "COMMITTED",
        "NOT_ATTEMPTED", "SKIPPED",
    ]
    with factory() as session:
        products = session.scalars(select(ProductModel)).all()
        documents = session.scalars(select(SdsDocumentModel)).all()
        histories = session.scalars(select(ProductHistoryModel)).all()
        assert len(products) == 5
        assert len(documents) == 5
        assert len(histories) == 3
        assert len(session.scalars(select(ManufacturerModel)).all()) == 2
        assert session.get(SdsDocumentModel, "old-sds").document_status == SdsDocumentStatus.ARCHIVED
        assert session.get(SdsDocumentModel, "existing-sds").document_status == SdsDocumentStatus.CURRENT
        assert all(row.document_status == SdsDocumentStatus.CURRENT
                   for row in documents if row.sds_id not in {"old-sds", "existing-sds"})
        assert all((product.use_description, product.use_restriction) == (None, None)
                   for product in products)
        assert all((history.use_description, history.use_restriction) == (None, None)
                   for history in histories)
        assert session.scalars(select(SafetyProfileModel)).all() == []
        assert session.scalars(select(SdsComponentModel)).all() == []
        assert session.scalars(select(BhpDecisionModel)).all() == []
    assert len(list(root.rglob("*.pdf"))) == 5


def test_hash_mismatch_stops_before_any_write(isolated_database, tmp_path):
    engine, factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    entries = [_item(tmp_path, 1, "NEW ALPHA"), _item(tmp_path, 2, "NEW BETA")]
    manifest = _manifest(tmp_path, entries)
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    (tmp_path / "source" / "B001-P002.pdf").write_bytes(b"%PDF-1.4\nTampered\n")
    rows = _readiness(factory, manifest, tmp_path, root)
    assert [row.classification for row in rows] == ["READY_CREATE", "BLOCKED_SOURCE"]
    with pytest.raises(ImportPlanError, match="BATCH_PREFLIGHT_BLOCKED"):
        commit_ready(rows, manifest, tmp_path / "json", tmp_path / "source",
                     DECISION, engine, root)
    with factory() as session:
        assert session.scalars(select(ProductModel)).all() == []
        assert session.scalars(select(SdsDocumentModel)).all() == []
    assert list(root.rglob("*.pdf")) == []


def test_item_failure_rolls_back_and_stops_later_items(isolated_database, tmp_path,
                                                       monkeypatch):
    engine, factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    entries = [_item(tmp_path, index, f"NEW {index}") for index in range(1, 4)]
    manifest = _manifest(tmp_path, entries)
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    rows = _readiness(factory, manifest, tmp_path, root)
    assert all(row.classification == "READY_CREATE" for row in rows)
    original = SqlAlchemySdsAcceptanceRepository._persist_sds
    calls = 0

    def fail_second(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        value = original(self, *args, **kwargs)
        if calls == 2:
            raise RuntimeError("injected second item failure")
        return value

    with monkeypatch.context() as patcher:
        patcher.setattr(SqlAlchemySdsAcceptanceRepository, "_persist_sds", fail_second)
        failure = commit_ready(rows, manifest, tmp_path / "json", tmp_path / "source",
                               DECISION, engine, root)
    assert isinstance(failure, RuntimeError)
    assert [row.action for row in rows] == [
        "COMMITTED", "FAILED_DURING_COMMIT", "NOT_ATTEMPTED",
    ]
    with factory() as session:
        products = session.scalars(select(ProductModel)).all()
        documents = session.scalars(select(SdsDocumentModel)).all()
        histories = session.scalars(select(ProductHistoryModel)).all()
        assert len(products) == len(documents) == len(histories) == 1
        assert products[0].product_name == "NEW 1"
    assert len(list(root.rglob("*.pdf"))) == 1
