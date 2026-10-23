"""Stage 1 ALUCYNK fixture on disposable PostgreSQL and SDS storage."""

import json
from hashlib import sha256
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.dto.bhp_decisions import RegisterBhpDecisionInput
from app.domain.enums import BhpDecisionStatus
from app.infrastructure.db.models import (
    ManufacturerModel, ProductModel, SafetyProfileModel, SdsComponentModel,
    SdsDocumentModel,
)
from app.presentation.streamlit.composition import ShellComposition
from tests.integration.test_task054_operator_flow import isolated_database


def test_stage1_registers_identity_without_safety_and_blocks_bhp(isolated_database, tmp_path):
    engine, factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    composition = ShellComposition(engine, factory, (), root)
    pdf = b"%PDF-1.4\n%%EOF\n"
    payload = json.loads(Path(
        "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
    ).read_text(encoding="utf8"))
    payload["source"]["file_sha256"] = sha256(pdf).hexdigest()
    raw = json.dumps(payload, ensure_ascii=False).encode()
    with factory.begin() as session:
        session.add_all([
            ManufacturerModel(manufacturer_id="similar-1", manufacturer_name="CX80"),
            ManufacturerModel(manufacturer_id="similar-2", manufacturer_name="Cx80"),
        ])

    dry_run = composition.dry_run_evidence_json(payload)[0]
    assert dry_run.validation_status == "VALID"
    assert dry_run.mapped_product_name == "ALUCYNK"
    assert dry_run.mapped_manufacturer_product_code is None
    assert dry_run.manufacturer_resolution.canonical_name == "CX80 POLSKA"
    assert dry_run.manufacturer_resolution.human_confirmation_required
    assert len(dry_run.manufacturer_resolution.similar_records) == 2
    assert "INCOMPLETE_SAFETY_DATA" not in dry_run.blockers

    plan = composition.approve_evidence_import(
        raw, "DOC-001", IdentityDecision("CREATE", "CX80 POLSKA"),
        IdentityDecision("CREATE", "ALUCYNK"),
        "Test use", "Test restriction", None,
        payload["source"]["original_filename"], pdf,
        HumanApproval("test reviewer", True, True, True, False, True),
    )
    assert plan.registration_readiness == "IDENTITY_REGISTRATION_READY"
    assert plan.safety_readiness == "SAFETY_ENRICHMENT_PENDING"
    sds_id = composition.commit_evidence_import(plan, raw, pdf)
    with factory() as session:
        product = session.scalar(select(ProductModel).where(ProductModel.product_name == "ALUCYNK"))
        sds = session.get(SdsDocumentModel, sds_id)
        assert product.manufacturer_product_code is None
        assert session.get(ManufacturerModel, product.manufacturer_id).manufacturer_name == "CX80 POLSKA"
        assert session.scalar(select(func.count()).select_from(ManufacturerModel)) == 3
        assert sds.document_status.value == "CURRENT"
        assert sds.issue_date.isoformat() == "2023-01-23"
        assert sds.revision == "2.0"
        assert sds.original_filename == payload["source"]["original_filename"]
        assert session.scalar(select(func.count()).select_from(SafetyProfileModel)) == 0
        assert session.scalar(select(func.count()).select_from(SdsComponentModel)) == 0
        assert (root / sds.relative_path).read_bytes() == pdf
        product_id = product.product_id
    current_file = composition.get_current_sds_file(product_id)
    assert current_file is not None and current_file.content == pdf
    products = composition.list_bhp_products()
    assert next(row for row in products if row.product_id == product_id).safety_enrichment_pending
    with pytest.raises(ValueError, match="Dane bezpieczeństwa SDS"):
        composition.register_bhp_decision(RegisterBhpDecisionInput(
            product_id=product_id, sds_id=sds_id,
            decision_status=BhpDecisionStatus.APPROVED,
            evidence_relative_path="missing.pdf", original_filename="missing.pdf",
        ))
    with factory() as session:
        manufacturer_id = session.scalar(select(ProductModel).where(
            ProductModel.product_id == product_id)).manufacturer_id
    revision_plan = composition.approve_evidence_import(
        raw, "DOC-001", IdentityDecision("LINK", "CX80 POLSKA", selected_id=manufacturer_id,
                                          manufacturer_link_confirmed=True),
        IdentityDecision("LINK", "ALUCYNK", selected_id=product_id,
                         null_code_link_confirmed=True),
        "Test use", "Test restriction", None,
        payload["source"]["original_filename"], pdf,
        HumanApproval("test reviewer", True, True, True, False, True),
    )
    second_sds_id = composition.commit_evidence_import(revision_plan, raw, pdf)
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(ProductModel)) == 1
        assert session.get(SdsDocumentModel, sds_id).document_status.value == "ARCHIVED"
        assert session.get(SdsDocumentModel, second_sds_id).document_status.value == "CURRENT"
        assert session.scalar(select(func.count()).select_from(SafetyProfileModel)) == 0


def test_stage1_rejects_pdf_hash_mismatch(isolated_database, tmp_path):
    engine, factory = isolated_database
    composition = ShellComposition(engine, factory, (), tmp_path)
    payload = json.loads(Path(
        "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
    ).read_text(encoding="utf8"))
    raw = json.dumps(payload, ensure_ascii=False).encode()
    from app.application.use_cases.controlled_evidence_import import ImportPlanError
    with pytest.raises(ImportPlanError, match="PDF_MISMATCH"):
        composition.approve_evidence_import(
            raw, "DOC-001", IdentityDecision("CREATE", "CX80 POLSKA"),
            IdentityDecision("CREATE", "ALUCYNK"), "Test use", "Test restriction",
            None, payload["source"]["original_filename"], b"%PDF-fake",
            HumanApproval("test reviewer", True, True, True, False, True),
        )
