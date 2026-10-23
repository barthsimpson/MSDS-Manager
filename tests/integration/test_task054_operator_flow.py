"""TASK-054 wiring on disposable PostgreSQL and a temporary SDS root."""

import json
import os
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.dto.sds import SdsSafetyProfileDraft
from app.application.use_cases.controlled_evidence_import import SAFETY_STATUS_FIELDS
from app.domain.enums import SafetyInformationStatus, SdsDocumentStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import ManufacturerModel, ProductModel, SdsDocumentModel
from app.presentation.streamlit.composition import ShellComposition


@pytest.fixture
def isolated_database():
    operator_url = make_url(load_settings().database_url)
    if operator_url.database != "msds_manager":
        pytest.skip("Isolated PostgreSQL parent must be msds_manager")
    name = f"task054_{uuid4().hex}"
    maintenance = create_engine(operator_url, isolation_level="AUTOCOMMIT")
    isolated_url = operator_url.set(database=name)
    previous = os.environ.get("DATABASE_URL")
    engine = None
    created = False
    try:
        with maintenance.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created = True
        os.environ["DATABASE_URL"] = isolated_url.render_as_string(hide_password=False)
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_engine(isolated_url)
        yield engine, sessionmaker(bind=engine, expire_on_commit=False)
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        if engine is not None:
            engine.dispose()
        if created:
            with maintenance.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        maintenance.dispose()


def test_alucynk_like_review_plan_commit_and_product_card(isolated_database, tmp_path):
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

    dry_run = composition.dry_run_evidence_json(payload)
    assert len(dry_run) == 1
    assert dry_run[0].mapped_product_name == "ALUCYNK"
    assert dry_run[0].mapped_manufacturer_product_code is None
    assert dry_run[0].manufacturer_resolution.status == "CREATE_CANDIDATE"
    exact, similar, products = composition.evidence_candidates("CX80 POLSKA", "ALUCYNK", None, None)
    assert exact == similar == products == ()

    safety = SdsSafetyProfileDraft(**{
        field: SafetyInformationStatus.NO for field in SAFETY_STATUS_FIELDS
    })
    approved = composition.approve_evidence_import(
        raw, "DOC-001", IdentityDecision("CREATE", "CX80 POLSKA"),
        IdentityDecision("CREATE", "ALUCYNK"),
        "Test use from simulated reviewer", "Test restriction from simulated reviewer",
        safety, "chosen.pdf", pdf,
        HumanApproval("isolated-test-reviewer", True, True, True, True, True),
    )
    assert approved.product_decision.manufacturer_product_code is None
    sds_id = composition.commit_evidence_import(approved, raw, pdf)
    product_id, status, filename = composition.evidence_import_result(sds_id)
    assert status == SdsDocumentStatus.CURRENT.value
    assert filename == "chosen.pdf"
    details = composition.get_product_details(product_id)
    assert details.product_name == "ALUCYNK"
    with factory() as session:
        assert len(session.scalars(select(ManufacturerModel)).all()) == 1
        assert len(session.scalars(select(ProductModel)).all()) == 1
        document = session.scalar(select(SdsDocumentModel))
        assert document.sds_id == sds_id
        assert (root / document.relative_path).is_file()
