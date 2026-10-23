"""TASK-053 controlled commit on disposable PostgreSQL and SDS storage."""

import os
import json
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.dto.sds import SdsSafetyProfileDraft
from app.application.use_cases.controlled_evidence_import import (
    ControlledEvidenceImport, ImportPlanError, SAFETY_STATUS_FIELDS, approve_import_plan,
)
from app.application.use_cases.import_sds import ImportSds
from app.domain.enums import SafetyInformationStatus, SdsDocumentStatus
from app.domain.enums import ProductUsageStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.controlled_evidence_registration import SqlAlchemyControlledEvidenceRegistration
from app.infrastructure.db.models import ManufacturerModel, ProductModel, SdsDocumentModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


RAW_JSON = Path("docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json").read_bytes()
PDF = b"%PDF-1.4\n%%EOF\n"
APPROVAL = HumanApproval("isolated-test-reviewer", True, True, True, True, True)


@pytest.fixture
def isolated_database():
    operator_url = make_url(load_settings().database_url)
    if operator_url.database != "msds_manager":
        pytest.skip("TASK-053 requires configured msds_manager as isolated DB parent")
    name = f"task053_{uuid4().hex}"
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
        yield sessionmaker(bind=engine, expire_on_commit=False)
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


def _safety():
    # Values are explicitly supplied by this isolated test's simulated reviewer.
    return SdsSafetyProfileDraft(**{
        field: SafetyInformationStatus.NO_DATA for field in SAFETY_STATUS_FIELDS
    })


def _approve(session_factory, manufacturer, product, *, raw_json=RAW_JSON, pdf=PDF):
    with session_factory() as session:
        return approve_import_plan(
            raw_json, "DOC-001", SqlAlchemyEvidenceIdentityRead(session),
            manufacturer, product,
            use_description="Isolated test use", use_restriction="Isolated test restriction",
            safety_profile=_safety(), original_filename="selected-alucynk.pdf",
            pdf_bytes=pdf, approval=APPROVAL,
        )


def _committer(session_factory, root):
    return ControlledEvidenceImport(
        SqlAlchemyControlledEvidenceRegistration(session_factory, root),
        ImportSds(SdsPdfStorage(root)),
    )


def test_alucynk_create_then_explicit_link_revision(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    committer = _committer(session_factory, root)
    create_manufacturer = IdentityDecision("CREATE", "CX80 POLSKA")
    create_product = IdentityDecision("CREATE", "ALUCYNK")
    plan = _approve(session_factory, create_manufacturer, create_product)
    first_sds_id = committer.execute(plan, RAW_JSON, PDF)

    with session_factory() as session:
        manufacturers = session.scalars(select(ManufacturerModel)).all()
        products = session.scalars(select(ProductModel)).all()
        sds_rows = session.scalars(select(SdsDocumentModel)).all()
        assert len(manufacturers) == len(products) == len(sds_rows) == 1
        assert manufacturers[0].manufacturer_name == "CX80 POLSKA"
        assert products[0].product_name == "ALUCYNK"
        assert products[0].manufacturer_product_code is None
        assert sds_rows[0].sds_id == first_sds_id
        assert sds_rows[0].document_status == SdsDocumentStatus.CURRENT
        assert sds_rows[0].original_filename == "selected-alucynk.pdf"
        assert sds_rows[0].relative_path.startswith("imported/")
        assert (root / sds_rows[0].relative_path).is_file()
        manufacturer_id = manufacturers[0].manufacturer_id
        product_id = products[0].product_id
        first_path = sds_rows[0].relative_path

    link_manufacturer = IdentityDecision("LINK", "CX80 POLSKA", selected_id=manufacturer_id,
                                         manufacturer_link_confirmed=True)
    link_product = IdentityDecision(
        "LINK", "ALUCYNK", selected_id=product_id, null_code_link_confirmed=True,
    )
    revision_plan = _approve(session_factory, link_manufacturer, link_product)
    second_sds_id = committer.execute(revision_plan, RAW_JSON, PDF)
    with session_factory() as session:
        documents = session.scalars(select(SdsDocumentModel).order_by(SdsDocumentModel.sds_id)).all()
        assert len(documents) == 2
        assert {row.document_status for row in documents} == {
            SdsDocumentStatus.CURRENT, SdsDocumentStatus.ARCHIVED,
        }
        assert next(row for row in documents if row.sds_id == second_sds_id).document_status == SdsDocumentStatus.CURRENT
        assert (root / first_path).is_file()
        assert all((root / row.relative_path).is_file() for row in documents)


def test_stale_create_and_changed_source_leave_no_artifacts(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    committer = _committer(session_factory, root)
    create_manufacturer = IdentityDecision("CREATE", "CX80 POLSKA")
    create_product = IdentityDecision("CREATE", "ALUCYNK")
    plan = _approve(session_factory, create_manufacturer, create_product)
    with pytest.raises(ImportPlanError, match="SOURCE_CHANGED"):
        committer.execute(plan, RAW_JSON + b" ", PDF)
    assert not list(root.rglob("*.pdf"))
    committer.execute(plan, RAW_JSON, PDF)
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        committer.execute(plan, RAW_JSON, PDF)
    with session_factory() as session:
        assert len(session.scalars(select(SdsDocumentModel)).all()) == 1
        assert len(session.scalars(select(ManufacturerModel)).all()) == 1
        assert len(session.scalars(select(ProductModel)).all()) == 1
    # The original registered PDF remains; failed import's newly created file is removed.
    assert len(list(root.rglob("*.pdf"))) == 1


def test_manufacturer_link_product_create_and_known_code_null_link(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    committer = _committer(session_factory, root)
    coded = json.loads(RAW_JSON)
    code_field = coded["documents"][0]["product"]["manufacturer_product_code"]
    code_field.update(
        value="CODE-1", state="FOUND",
        evidence=coded["documents"][0]["product"]["product_name"]["evidence"],
    )
    coded_raw = json.dumps(coded, ensure_ascii=False).encode()
    first_plan = _approve(
        session_factory, IdentityDecision("CREATE", "CX80 POLSKA"),
        IdentityDecision("CREATE", "ALUCYNK", manufacturer_product_code="CODE-1"),
        raw_json=coded_raw,
    )
    committer.execute(first_plan, coded_raw, PDF)
    with session_factory() as session:
        manufacturer_id = session.scalar(select(ManufacturerModel.manufacturer_id))
        product_id = session.scalar(select(ProductModel.product_id))
    manufacturer_link = IdentityDecision("LINK", "CX80 POLSKA", selected_id=manufacturer_id,
                                         manufacturer_link_confirmed=True)

    second = json.loads(RAW_JSON)
    second["documents"][0]["product"]["product_name"]["value"] = "SECOND PRODUCT"
    second_raw = json.dumps(second, ensure_ascii=False).encode()
    second_plan = _approve(
        session_factory, manufacturer_link, IdentityDecision("CREATE", "SECOND PRODUCT"),
        raw_json=second_raw,
    )
    committer.execute(second_plan, second_raw, PDF)

    null_link = _approve(
        session_factory, manufacturer_link,
        IdentityDecision("LINK", "ALUCYNK", selected_id=product_id,
                         null_code_link_confirmed=True),
    )
    committer.execute(null_link, RAW_JSON, PDF)
    with session_factory() as session:
        products = session.scalars(select(ProductModel)).all()
        assert len(products) == 2
        assert next(item for item in products if item.product_id == product_id).manufacturer_product_code == "CODE-1"
        assert len(session.scalars(select(ManufacturerModel)).all()) == 1
        assert len(session.scalars(select(SdsDocumentModel)).all()) == 3


def test_missing_link_target_stops_before_pdf_write(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    with session_factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="m1", manufacturer_name="CX80 POLSKA"))
        session.add(ProductModel(
            product_id="p1", product_name="ALUCYNK", manufacturer_product_code=None,
            manufacturer_id="m1", use_description="", use_restriction="",
            usage_status=ProductUsageStatus.ACTIVE,
        ))
    plan = _approve(
        session_factory, IdentityDecision("LINK", "CX80 POLSKA", selected_id="m1",
                                          manufacturer_link_confirmed=True),
        IdentityDecision("LINK", "ALUCYNK", selected_id="p1",
                         null_code_link_confirmed=True),
    )
    with session_factory.begin() as session:
        session.delete(session.get(ProductModel, "p1"))
    with pytest.raises(ValueError, match="Selected product does not exist"):
        _committer(session_factory, root).execute(plan, RAW_JSON, PDF)
    assert not list(root.rglob("*.pdf"))


def test_db_failure_rolls_back_and_compensates_pdf(isolated_database, tmp_path, monkeypatch):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    plan = _approve(
        session_factory, IdentityDecision("CREATE", "CX80 POLSKA"),
        IdentityDecision("CREATE", "ALUCYNK"),
    )
    original = SqlAlchemySdsAcceptanceRepository._persist_sds

    def fail_after_flush(self, product, data):
        original(self, product, data)
        raise RuntimeError("injected DB failure after SDS flush")

    monkeypatch.setattr(SqlAlchemySdsAcceptanceRepository, "_persist_sds", fail_after_flush)
    with pytest.raises(RuntimeError, match="injected DB failure"):
        _committer(session_factory, root).execute(plan, RAW_JSON, PDF)
    with session_factory() as session:
        assert session.scalars(select(ManufacturerModel)).all() == []
        assert session.scalars(select(ProductModel)).all() == []
        assert session.scalars(select(SdsDocumentModel)).all() == []
    assert not list(root.rglob("*.pdf"))


def test_stale_product_create_stops_without_sds_or_pdf(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    with session_factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="m1", manufacturer_name="CX80 POLSKA"))
    plan = _approve(
        session_factory, IdentityDecision("LINK", "CX80 POLSKA", selected_id="m1",
                                          manufacturer_link_confirmed=True),
        IdentityDecision("CREATE", "ALUCYNK"),
    )
    with session_factory.begin() as session:
        session.add(ProductModel(
            product_id="p1", product_name="ALUCYNK", manufacturer_product_code=None,
            manufacturer_id="m1", use_description="", use_restriction="",
            usage_status=ProductUsageStatus.ACTIVE,
        ))
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        _committer(session_factory, root).execute(plan, RAW_JSON, PDF)
    with session_factory() as session:
        assert session.scalars(select(SdsDocumentModel)).all() == []
        assert len(session.scalars(select(ProductModel)).all()) == 1
    assert not list(root.rglob("*.pdf"))


def test_null_code_link_detects_changed_known_db_code(isolated_database, tmp_path):
    session_factory = isolated_database
    root = tmp_path / "sds"
    root.mkdir()
    with session_factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id="m1", manufacturer_name="CX80 POLSKA"))
        session.add(ProductModel(
            product_id="p1", product_name="ALUCYNK", manufacturer_product_code="KNOWN-A",
            manufacturer_id="m1", use_description="", use_restriction="",
            usage_status=ProductUsageStatus.ACTIVE,
        ))
    plan = _approve(
        session_factory, IdentityDecision("LINK", "CX80 POLSKA", selected_id="m1",
                                          manufacturer_link_confirmed=True),
        IdentityDecision("LINK", "ALUCYNK", selected_id="p1",
                         null_code_link_confirmed=True),
    )
    with session_factory.begin() as session:
        session.get(ProductModel, "p1").manufacturer_product_code = "KNOWN-B"
    with pytest.raises(ImportPlanError, match="STALE_RESOLUTION"):
        _committer(session_factory, root).execute(plan, RAW_JSON, PDF)
    assert not list(root.rglob("*.pdf"))
