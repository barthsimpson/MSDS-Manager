"""TASK-059 closure on disposable PostgreSQL and temporary PDFs."""

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.domain.enums import FileAvailabilityStatus, ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, ManufacturerModel, ProductIdentityChangeModel, ProductModel,
    SafetyProfileModel, SdsComponentModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.product import SqlAlchemyProductRepository
from scripts.task059_close_reviews import (
    CURRENT, LEGACY, P012, P012_SDS, P037, TARGET,
    commit_correction, load_sources, validate_database,
)
from tests.integration.test_task054_operator_flow import isolated_database


BATCH = Path("docs/sds_bootstrap/BATCH-001_CX")


def _fixture(tmp_path, factory):
    batch = tmp_path / "batch"
    (batch / "json").mkdir(parents=True)
    source_root = tmp_path / "source"
    source_root.mkdir()
    sds_root = tmp_path / "sds"
    sds_root.mkdir()
    original = json.loads((BATCH / "BATCH-001_MANIFEST.json").read_text(encoding="utf8"))
    entries = []
    data = {}
    for entry in original["files"]:
        if entry["id"] not in {"B001-P012", "B001-P037"}:
            continue
        pdf = ("%PDF-1.4\n" + entry["id"] + "\n%%EOF\n").encode()
        data[entry["id"]] = pdf
        (source_root / entry["source_file"]).write_bytes(pdf)
        payload = json.loads((BATCH / "json" / entry["json"]).read_text(encoding="utf8"))
        payload["source"]["file_sha256"] = sha256(pdf).hexdigest()
        (batch / "json" / entry["json"]).write_text(json.dumps(payload), encoding="utf8")
        entries.append({**entry, "sha256": sha256(pdf).hexdigest()})
    (batch / "BATCH-001_MANIFEST.json").write_text(json.dumps({"files": entries}), encoding="utf8")

    def add_sds(session, sid, pid, pdf, status, issued, revision):
        relative = f"imported/{sid}.pdf"
        target = sds_root / relative
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(pdf)
        session.add(SdsDocumentModel(
            sds_id=sid, product_id=pid, original_filename=f"{sid}.pdf",
            relative_path=relative, document_status=status,
            issue_date=issued, revision=revision, registered_at=datetime.now(timezone.utc),
            file_status=FileAvailabilityStatus.AVAILABLE,
        ))

    with factory.begin() as session:
        session.add_all([
            ManufacturerModel(manufacturer_id=TARGET, manufacturer_name="CX80 Polska"),
            ManufacturerModel(manufacturer_id=LEGACY, manufacturer_name="Cx80"),
        ])
        session.add_all([
            ProductModel(product_id=P012, product_name="Cleaner prof",
                         manufacturer_product_code=None, manufacturer_id=TARGET,
                         use_description=None, use_restriction=None,
                         usage_status=ProductUsageStatus.PENDING_APPROVAL),
            ProductModel(product_id=P037, product_name="XBRAKE CLEANER",
                         manufacturer_product_code="CX80 XBRAKE CLEANER", manufacturer_id=LEGACY,
                         use_description=None, use_restriction=None,
                         usage_status=ProductUsageStatus.PENDING_APPROVAL),
        ])
        session.flush()
        add_sds(session, P012_SDS, P012, data["B001-P012"],
                SdsDocumentStatus.CURRENT, date(2023, 1, 23), "2.0")
        add_sds(session, CURRENT, P037, b"%PDF-1.4\nCURRENT\n%%EOF\n",
                SdsDocumentStatus.CURRENT, date(2026, 9, 1), "test delete")
        for sid in ("3e8346e132bf4bb69016fc5524434472",
                    "ecba2904093f40bf96e2762b6a9ebf09"):
            add_sds(session, sid, P037, b"%PDF-1.4\nARCHIVED\n%%EOF\n",
                    SdsDocumentStatus.ARCHIVED, date(2025, 1, 15), "03")
    return batch, source_root, sds_root


def test_exact_link_and_historical_skip_with_atomic_correction(isolated_database, tmp_path,
                                                                monkeypatch):
    _, factory = isolated_database
    batch, source_root, sds_root = _fixture(tmp_path, factory)
    sources = load_sources(batch, source_root)
    with factory() as session:
        assert validate_database(session, sds_root, sources) == "READY_CORRECTION"

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("injected audit failure")

    with monkeypatch.context() as patch:
        patch.setattr(SqlAlchemyProductRepository, "_record_identity_change", fail_audit)
        with pytest.raises(RuntimeError, match="injected audit failure"):
            commit_correction(factory, sds_root, sources)
    with factory() as session:
        assert session.get(ProductModel, P037).manufacturer_id == LEGACY
        assert session.scalars(select(ProductIdentityChangeModel)).all() == []

    change_id = commit_correction(factory, sds_root, sources)
    assert commit_correction(factory, sds_root, sources) == change_id
    with factory() as session:
        product = session.get(ProductModel, P037)
        assert (product.product_name, product.manufacturer_product_code, product.manufacturer_id) == (
            "XBRAKE CLEANER", "CX80 XBRAKE CLEANER", TARGET)
        changes = session.scalars(select(ProductIdentityChangeModel)).all()
        assert len(changes) == 1 and changes[0].change_id == change_id
        assert changes[0].change_kind == "CORRECTION"
        assert changes[0].old_manufacturer_id == LEGACY
        assert changes[0].new_manufacturer_id == TARGET
        docs = session.scalars(select(SdsDocumentModel)).all()
        assert len(docs) == 4
        assert {d.sds_id for d in docs if d.document_status == SdsDocumentStatus.CURRENT} == {
            CURRENT, P012_SDS}
        assert session.get(SdsDocumentModel, CURRENT).issue_date == date(2026, 9, 1)
        assert len(session.scalars(select(ProductModel)).all()) == 2
        assert len(session.scalars(select(ManufacturerModel)).all()) == 2
        assert session.scalars(select(SafetyProfileModel)).all() == []
        assert session.scalars(select(SdsComponentModel)).all() == []
        assert session.scalars(select(BhpDecisionModel)).all() == []
    assert len(list(sds_root.rglob("*.pdf"))) == 4


def test_similar_p012_name_without_exact_pdf_blocks_link(isolated_database, tmp_path):
    _, factory = isolated_database
    batch, source_root, sds_root = _fixture(tmp_path, factory)
    sources = load_sources(batch, source_root)
    (sds_root / f"imported/{P012_SDS}.pdf").write_bytes(b"%PDF-1.4\nDIFFERENT\n%%EOF\n")
    with factory() as session:
        with pytest.raises(ValueError, match="BLOCKED_P012"):
            validate_database(session, sds_root, sources)
    assert len(list(sds_root.rglob("*.pdf"))) == 4
