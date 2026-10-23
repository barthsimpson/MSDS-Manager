"""TASK-055-R1 approved CX80 identity on disposable PostgreSQL."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.use_cases.controlled_evidence_import import ImportPlanError
from app.infrastructure.db.models import ManufacturerModel, ProductModel, SdsDocumentModel
from app.presentation.streamlit.composition import ShellComposition
from tests.integration.test_task054_operator_flow import isolated_database


def test_approved_cx80_polska_link_keeps_existing_manufacturers(isolated_database, tmp_path):
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
    expected_manufacturers = {
        "cx80": "CX80", "approved": "CX80 Polska", "mixed": "Cx80",
    }
    with factory.begin() as session:
        session.add_all(ManufacturerModel(manufacturer_id=key, manufacturer_name=name)
                        for key, name in expected_manufacturers.items())

    dry_run, = composition.dry_run_evidence_json(payload)
    assert dry_run.manufacturer_resolution.canonical_name == "CX80 POLSKA"
    assert dry_run.manufacturer_resolution.status == "CREATE_CANDIDATE"
    assert dry_run.manufacturer_resolution.candidate_ids == ()
    exact, similar, _ = composition.evidence_candidates("CX80 POLSKA", "ALUCYNK", None, None)
    assert exact == ()
    assert {row.record_id for row in similar} == {"cx80", "approved", "mixed"}

    product = IdentityDecision("CREATE", "ALUCYNK")
    approval = HumanApproval("test reviewer", True, True, True, False, True)
    args = (raw, "DOC-001", IdentityDecision(
        "LINK", "CX80 POLSKA", selected_id="approved",
    ), product, "Test use", "Test restriction", None,
            payload["source"]["original_filename"], pdf, approval)
    with pytest.raises(ImportPlanError, match="MANUFACTURER_LINK_CONFIRMATION_REQUIRED"):
        composition.approve_evidence_import(*args)
    with pytest.raises(ImportPlanError, match="LINK_TARGET_NOT_APPROVED"):
        composition.approve_evidence_import(
            raw, "DOC-001", IdentityDecision(
                "LINK", "CX80 POLSKA", selected_id="not-presented",
                manufacturer_link_confirmed=True,
            ), product, "Test use", "Test restriction", None,
            payload["source"]["original_filename"], pdf, approval,
        )
    plan = composition.approve_evidence_import(
        raw, "DOC-001", replace(args[2], manufacturer_link_confirmed=True),
        product, "Test use", "Test restriction", None,
        payload["source"]["original_filename"], pdf, approval,
    )
    assert plan.manufacturer_selected_name == "CX80 Polska"
    assert plan.manufacturer_decision.selected_record_name == "CX80 Polska"
    assert set(plan.expected_manufacturer_snapshot) == {
        ("cx80", "CX80"), ("approved", "CX80 Polska"), ("mixed", "Cx80"),
    }
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        composition.commit_evidence_import(
            replace(plan, manufacturer_decision=replace(
                plan.manufacturer_decision, selected_id="cx80")), raw, pdf,
        )
    assert not list(root.rglob("*.pdf"))

    with factory.begin() as session:
        session.get(ManufacturerModel, "approved").manufacturer_name = "CX80 Polska changed"
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        composition.commit_evidence_import(plan, raw, pdf)
    assert not list(root.rglob("*.pdf"))
    with factory.begin() as session:
        session.get(ManufacturerModel, "approved").manufacturer_name = "CX80 Polska"

    sds_id = composition.commit_evidence_import(plan, raw, pdf)
    with factory() as session:
        manufacturers = session.scalars(select(ManufacturerModel)).all()
        assert {row.manufacturer_id: row.manufacturer_name for row in manufacturers} == expected_manufacturers
        assert session.scalar(select(func.count()).select_from(ManufacturerModel)) == 3
        product_row = session.scalar(select(ProductModel).where(ProductModel.product_name == "ALUCYNK"))
        assert product_row.manufacturer_id == "approved"
        assert session.get(SdsDocumentModel, sds_id).product_id == product_row.product_id
