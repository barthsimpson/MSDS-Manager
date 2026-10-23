"""TASK-056 on disposable PostgreSQL and temporary PDF storage."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import inspect, select

from app.application.dto.sds import AcceptSdsInput
from app.application.use_cases.accept_sds import AcceptSds
from app.application.use_cases.automatic_stage1_import import AutomaticStage1Import, BatchStage1Decision
from app.application.use_cases.controlled_evidence_import import ImportPlanError
from app.domain.enums import ProductUsageStatus, SafetyInformationStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, ManufacturerModel, ProductHistoryModel, ProductModel,
    SafetyProfileModel, SdsComponentModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.bhp_decision import SqlAlchemyBhpDecisionRepository
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from app.presentation.streamlit.composition import ShellComposition
from scripts.task056_stage1_import import _source, main
from tests.integration.test_task054_operator_flow import isolated_database


def _fixture(tmp_path):
    pdf = b"%PDF-1.4\nStage 1 isolated test\n%%EOF\n"
    payload = json.loads(Path(
        "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
    ).read_text(encoding="utf8"))
    payload["source"]["file_sha256"] = sha256(pdf).hexdigest()
    raw = json.dumps(payload, ensure_ascii=False).encode()
    evidence = tmp_path / "B001-P001_DOC-001.json"
    evidence.write_bytes(raw)
    source = tmp_path / payload["source"]["original_filename"]
    source.write_bytes(pdf)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "batch": "BATCH-001_CX", "input_directory": str(tmp_path),
        "files": [{"json": evidence.name, "source_file": source.name,
                   "sha256": sha256(pdf).hexdigest(), "logical_sds_count": 1}],
    }), encoding="utf8")
    decision = BatchStage1Decision.from_json(Path(
        "docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_DECISION.json"
    ).read_bytes())
    decision = replace(decision, json_sha256=sha256(raw).hexdigest(),
                       source_pdf_sha256=sha256(pdf).hexdigest())
    return evidence, manifest, decision, raw, pdf


def _prepare(factory, evidence, manifest, decision):
    raw, pdf, _ = _source(evidence, manifest, decision)
    with factory() as session:
        return AutomaticStage1Import().prepare(
            raw, evidence.name, pdf, decision, SqlAlchemyEvidenceIdentityRead(session),
        )


def test_migration_cycle_and_schema_match(isolated_database):
    engine, factory = isolated_database
    config = Config("alembic.ini")

    def nullable():
        inspector = inspect(engine)
        return {(table, column): next(item["nullable"] for item in inspector.get_columns(table)
                                       if item["name"] == column)
                for table in ("products", "product_history")
                for column in ("use_description", "use_restriction")}

    assert all(nullable().values())
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="preserved", manufacturer_name="Existing"))
        session.flush()
        session.add(ProductModel(
            product_id="preserved", product_name="Existing", manufacturer_id="preserved",
            manufacturer_product_code="CODE", use_description="Original use",
            use_restriction="Original restriction",
            usage_status=ProductUsageStatus.PENDING_APPROVAL,
        ))
        session.flush()
        session.add(ProductHistoryModel(
            history_id="preserved", product_id="preserved",
            usage_status=ProductUsageStatus.PENDING_APPROVAL,
            use_description="Original use", use_restriction="Original restriction",
            changed_at=datetime.now(timezone.utc),
        ))
    command.downgrade(config, "c6a8f1d2940e")
    assert not any(nullable().values())
    command.upgrade(config, "head")
    assert all(nullable().values())
    with factory() as session:
        assert session.get(ProductModel, "preserved").use_description == "Original use"
        assert session.get(ProductHistoryModel, "preserved").use_restriction == "Original restriction"
    command.check(config)


def test_automatic_stage1_commit_true_null_history_and_bhp_gate(isolated_database, tmp_path):
    engine, factory = isolated_database
    evidence, manifest, decision, raw, pdf = _fixture(tmp_path)
    with factory.begin() as session:
        session.add_all([
            ManufacturerModel(manufacturer_id="cx80", manufacturer_name="CX80"),
            ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"),
            ManufacturerModel(manufacturer_id="mixed", manufacturer_name="Cx80"),
        ])
    plan = _prepare(factory, evidence, manifest, decision)
    assert plan.manufacturer_decision.selected_id == "approved"
    assert plan.manufacturer_selected_name == "CX80 Polska"
    assert plan.use_description is None and plan.use_restriction is None
    assert not plan.human_approval.manual_inputs_confirmed
    assert plan.product_decision.action == "CREATE"
    root = tmp_path / "sds"
    root.mkdir()
    composition = ShellComposition(engine, factory, (), root)
    sds_id = composition.commit_evidence_import(plan, raw, pdf)
    with factory() as session:
        product, = session.scalars(select(ProductModel)).all()
        history, = session.scalars(select(ProductHistoryModel)).all()
        sds = session.get(SdsDocumentModel, sds_id)
        assert product.manufacturer_id == "approved"
        assert product.product_name == "ALUCYNK"
        assert product.manufacturer_product_code is None
        assert (product.use_description, product.use_restriction) == (None, None)
        assert (history.use_description, history.use_restriction) == (None, None)
        assert sds.document_status.value == "CURRENT"
        assert sds.issue_date.isoformat() == "2023-01-23"
        assert sds.revision == "2.0"
        assert (root / sds.relative_path).read_bytes() == pdf
        assert session.scalars(select(SafetyProfileModel)).all() == []
        assert session.scalars(select(SdsComponentModel)).all() == []
        assert session.scalars(select(BhpDecisionModel)).all() == []
        product_id = product.product_id
        with pytest.raises(ValueError, match="Dane bezpieczeństwa"):
            SqlAlchemyBhpDecisionRepository(session).verify_scope(product_id, sds_id)
    assert composition.get_current_sds_file(product_id).content == pdf
    assert composition.list_bhp_products()[0].administrative_data_pending

    # Even when Safety exists, either missing administrative field blocks BHP.
    statuses = {
        key: SafetyInformationStatus.NO_DATA for key in (
            "hazardous_classification_status", "pbt_status", "vpvb_status",
            "carcinogenicity_status", "germ_cell_mutagenicity_status",
            "reproductive_toxicity_status", "endocrine_section_2_status",
            "endocrine_section_11_status", "skin_sensitization_status",
            "respiratory_sensitization_status",
        )
    }
    with factory.begin() as session:
        session.add(SafetyProfileModel(
            sds_id=sds_id, hazard_statements=[], supplemental_hazard_statements=[],
            approved_at=datetime.now(timezone.utc), **statuses,
        ))
    with factory.begin() as session:
        repository = SqlAlchemyBhpDecisionRepository(session)
        with pytest.raises(ValueError, match="Dane zastosowania"):
            repository.verify_scope(product_id, sds_id)
        product = session.get(ProductModel, product_id)
        product.use_description = "Test use"
        session.flush()
        with pytest.raises(ValueError, match="Dane zastosowania"):
            repository.verify_scope(product_id, sds_id)
        product.use_restriction = "Test restriction"
        session.flush()
        repository.verify_scope(product_id, sds_id)


def test_precheck_blocks_duplicate_stale_and_pdf_mismatch(isolated_database, tmp_path):
    engine, factory = isolated_database
    evidence, manifest, decision, raw, pdf = _fixture(tmp_path)
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    plan = _prepare(factory, evidence, manifest, decision)
    root = tmp_path / "sds"
    root.mkdir()
    composition = ShellComposition(engine, factory, (), root)
    with pytest.raises(ImportPlanError, match="PDF_CHANGED"):
        composition.commit_evidence_import(plan, raw, pdf + b"modified")
    with factory.begin() as session:
        session.get(ManufacturerModel, "approved").manufacturer_name = "Changed"
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        composition.commit_evidence_import(plan, raw, pdf)
    assert not list(root.rglob("*.pdf"))
    with factory.begin() as session:
        session.get(ManufacturerModel, "approved").manufacturer_name = "CX80 Polska"
        session.add(ProductModel(
            product_id="existing", product_name="ALUCYNK", manufacturer_id="approved",
            manufacturer_product_code=None, use_description="Existing",
            use_restriction="Existing", usage_status="PENDING_APPROVAL",
        ))
    with pytest.raises(ImportPlanError, match="product exists"):
        _prepare(factory, evidence, manifest, decision)
    assert not list(root.rglob("*.pdf"))

    (tmp_path / "ALUCYNK 23.01.2023 rew. 2.0.pdf").write_bytes(pdf + b"tampered")
    with pytest.raises(ImportPlanError, match="PDF_MISMATCH"):
        _source(evidence, manifest, decision)


def test_manual_acceptance_still_requires_both_administrative_fields():
    with pytest.raises(ValueError, match="use_description"):
        AcceptSds._validate(AcceptSdsInput(
            source_relative_path="one.pdf", product_name="Manual",
            manufacturer_name="Manufacturer", use_description=None,
            use_restriction="Required",
        ))


def test_db_failure_rolls_back_null_product_and_compensates_pdf(isolated_database, tmp_path,
                                                                  monkeypatch):
    engine, factory = isolated_database
    evidence, manifest, decision, raw, pdf = _fixture(tmp_path)
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    plan = _prepare(factory, evidence, manifest, decision)
    root = tmp_path / "sds"
    root.mkdir()
    composition = ShellComposition(engine, factory, (), root)
    original = SqlAlchemySdsAcceptanceRepository._persist_sds

    def fail_after_flush(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError("injected DB failure")

    with monkeypatch.context() as patcher:
        patcher.setattr(SqlAlchemySdsAcceptanceRepository, "_persist_sds", fail_after_flush)
        with pytest.raises(RuntimeError, match="injected DB failure"):
            composition.commit_evidence_import(plan, raw, pdf)
    with factory() as session:
        assert session.scalars(select(ProductModel)).all() == []
        assert session.scalars(select(ProductHistoryModel)).all() == []
        assert session.scalars(select(SdsDocumentModel)).all() == []
        assert len(session.scalars(select(ManufacturerModel)).all()) == 1
    assert not list(root.rglob("*.pdf"))

    missing_root = tmp_path / "missing-sds-root"
    composition = ShellComposition(engine, factory, (), missing_root)
    with pytest.raises(OSError, match="SDS_ROOT_PATH"):
        composition.commit_evidence_import(plan, raw, pdf)
    with factory() as session:
        assert session.scalars(select(ProductModel)).all() == []


def test_cli_precheck_one_item_no_commit(isolated_database, tmp_path, monkeypatch, capsys):
    _, factory = isolated_database
    evidence, manifest, decision, _, _ = _fixture(tmp_path)
    manifest_data = json.loads(manifest.read_text(encoding="utf8"))
    manifest_data["input_directory"] = str(tmp_path / "unavailable")
    manifest.write_text(json.dumps(manifest_data), encoding="utf8")
    decision_data = asdict(decision)
    decision_data["issue_date"] = decision.issue_date.isoformat()
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision_data), encoding="utf8")
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    monkeypatch.setattr(sys, "argv", [
        "task056_stage1_import", str(evidence), "--manifest", str(manifest),
        "--decision", str(decision_path), "--source-root", str(tmp_path),
    ])
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PASS"
    assert result["action"] == "CREATE_PRODUCT_AND_SDS"
    assert result["manufacturer_id"] == "approved"
    assert result["use_description"] is None
    with factory() as session:
        assert session.scalars(select(ProductModel)).all() == []
        assert session.scalars(select(SdsDocumentModel)).all() == []


def test_source_root_changes_only_location_and_hash_is_required(tmp_path):
    evidence, manifest, decision, raw, pdf = _fixture(tmp_path)
    manifest_data = json.loads(manifest.read_text(encoding="utf8"))
    manifest_data["input_directory"] = str(tmp_path / "unavailable")
    manifest.write_text(json.dumps(manifest_data), encoding="utf8")
    with pytest.raises(ImportPlanError, match="SOURCE_PDF_UNAVAILABLE"):
        _source(evidence, manifest, decision)
    actual_raw, actual_pdf, filename = _source(evidence, manifest, decision, tmp_path)
    assert (actual_raw, actual_pdf, filename) == (
        raw, pdf, "ALUCYNK 23.01.2023 rew. 2.0.pdf",
    )
    (tmp_path / filename).write_bytes(pdf + b"tampered")
    with pytest.raises(ImportPlanError, match="PDF_MISMATCH"):
        _source(evidence, manifest, decision, tmp_path)


def test_cli_commits_exactly_one_item_in_isolation(isolated_database, tmp_path, monkeypatch,
                                                   capsys):
    _, factory = isolated_database
    evidence, manifest, decision, _, pdf = _fixture(tmp_path)
    decision_data = asdict(decision)
    decision_data["issue_date"] = decision.issue_date.isoformat()
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision_data), encoding="utf8")
    sds_root = tmp_path / "sds"
    sds_root.mkdir()
    monkeypatch.setenv("SDS_ROOT_PATH", str(sds_root))
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="approved", manufacturer_name="CX80 Polska"))
    monkeypatch.setattr(sys, "argv", [
        "task056_stage1_import", str(evidence), "--manifest", str(manifest),
        "--decision", str(decision_path), "--commit",
    ])
    main()
    precheck, committed = (json.loads(line) for line in capsys.readouterr().out.splitlines())
    assert precheck["status"] == "PASS"
    assert committed["status"] == "COMMITTED"
    assert committed["document_status"] == "CURRENT"
    with factory() as session:
        product, = session.scalars(select(ProductModel)).all()
        history, = session.scalars(select(ProductHistoryModel)).all()
        sds, = session.scalars(select(SdsDocumentModel)).all()
        assert product.product_id == committed["product_id"]
        assert (product.use_description, product.use_restriction) == (None, None)
        assert (history.use_description, history.use_restriction) == (None, None)
        assert sds.sds_id == committed["sds_id"]
        assert session.scalars(select(SafetyProfileModel)).all() == []
        assert session.scalars(select(SdsComponentModel)).all() == []
        assert session.scalars(select(BhpDecisionModel)).all() == []
        assert len(session.scalars(select(ManufacturerModel)).all()) == 1
        assert (sds_root / sds.relative_path).read_bytes() == pdf
