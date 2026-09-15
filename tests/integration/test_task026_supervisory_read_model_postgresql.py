"""TASK-026 on real PostgreSQL; fixtures are always rolled back, never committed."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Engine, event, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.use_cases import ListSupervisoryProducts
from app.domain.enums import (
    BhpDecisionStatus, DecisionRecordStatus, EvidenceFileFormat, EvidenceType,
    FileAvailabilityStatus, ProductUsageStatus, SdsDocumentStatus, UsageLocationStatus,
)
from app.infrastructure.config import Settings, load_settings
from app.infrastructure.db.models import (
    BhpDecisionModel, DecisionEvidenceModel, ManufacturerModel, ProductModel,
    ProductUsageLocationModel, SdsDocumentModel, UsageLocationModel,
)
from app.infrastructure.db.repositories import SqlAlchemySupervisoryQuery
from app.infrastructure.db.session import create_engine_from_settings


NOW = datetime(2026, 9, 15, 12, 0)


@pytest.fixture(scope="module")
def database_engine() -> Iterator[Engine]:
    engine = create_engine_from_settings(load_settings())
    assert engine.dialect.name == "postgresql"
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session(database_engine) -> Iterator[Session]:
    with database_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(connection) as session:
                yield session
        finally:
            if transaction.is_active:
                transaction.rollback()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    sds_root = tmp_path / "sds"
    evidence_root = tmp_path / "evidence"
    sds_root.mkdir()
    evidence_root.mkdir()
    return replace(load_settings(), sds_root_path=sds_root,
                   bhp_evidence_root_path=evidence_root)


def product(session, *, name="Paint", code="001", status=ProductUsageStatus.ACTIVE):
    manufacturer_id, product_id = uuid4().hex, uuid4().hex
    session.execute(insert(ManufacturerModel).values(
        manufacturer_id=manufacturer_id, manufacturer_name="TASK-026 Manufacturer"
    ))
    session.execute(insert(ProductModel).values(
        product_id=product_id, product_name=name, manufacturer_product_code=code,
        manufacturer_id=manufacturer_id, usage_status=status,
        use_description="Painting", use_restriction="Professional use",
    ))
    return product_id


def sds(session, product_id, *, status=SdsDocumentStatus.CURRENT,
        issue_date=date(2025, 1, 1), revision="1"):
    sds_id = uuid4().hex
    session.execute(insert(SdsDocumentModel).values(
        sds_id=sds_id, product_id=product_id, original_filename="original.pdf",
        relative_path=f"{sds_id}.pdf", document_status=status,
        registered_at=NOW, issue_date=issue_date, revision=revision,
        file_status=FileAvailabilityStatus.MISSING,
    ))
    return sds_id


def decision(session, product_id, sds_id, *, status=DecisionRecordStatus.CURRENT,
             result=BhpDecisionStatus.APPROVED, notes=None):
    decision_id, evidence_id = uuid4().hex, uuid4().hex
    session.execute(insert(DecisionEvidenceModel).values(
        evidence_id=evidence_id, relative_path=f"{decision_id}.pdf",
        evidence_type=EvidenceType.DOCUMENT, file_format=EvidenceFileFormat.PDF,
        file_status=FileAvailabilityStatus.MISSING,
    ))
    session.execute(insert(BhpDecisionModel).values(
        decision_id=decision_id, product_id=product_id, sds_id=sds_id,
        decision_status=result, record_status=status, evidence_id=evidence_id,
        registered_at=NOW, notes=notes,
    ))
    return decision_id


def location(session, product_id, name, *, status=UsageLocationStatus.ACTIVE,
             monthly=None):
    location_id = uuid4().hex
    session.execute(insert(UsageLocationModel).values(
        location_id=location_id, location_name=name, status=status,
    ))
    session.execute(insert(ProductUsageLocationModel).values(
        product_id=product_id, location_id=location_id, peak_quantity_value=0,
        peak_quantity_unit="kg", monthly_consumption_value=monthly,
        monthly_consumption_unit="kg" if monthly is not None else None,
    ))


def read(session, settings):
    return ListSupervisoryProducts(
        SqlAlchemySupervisoryQuery(session, settings=settings)
    ).execute()


def test_empty_database_returns_empty_list(session, settings):
    # Fail safely if the caller supplied a nonempty database; never erase it.
    assert session.scalar(select(ProductModel.product_id).limit(1)) is None
    assert read(session, settings) == []


@pytest.mark.parametrize("status", [ProductUsageStatus.ACTIVE, ProductUsageStatus.INACTIVE])
def test_one_product_many_locations_current_metadata_and_no_false_issues(
    session, settings, status
):
    product_id = product(session, status=status)
    current = sds(session, product_id)
    current_decision = decision(session, product_id, current, notes=None)
    # History has newer dates/revisions and the opposite BHP result.
    archived = sds(session, product_id, status=SdsDocumentStatus.ARCHIVED,
                   issue_date=date(2030, 1, 1), revision="99")
    decision(session, product_id, archived, result=BhpDecisionStatus.REJECTED)
    decision(session, product_id, current, status=DecisionRecordStatus.SUPERSEDED,
             result=BhpDecisionStatus.REJECTED, notes="Historical note")
    location(session, product_id, "Workshop B", monthly=Decimal("0"))
    location(session, product_id, "Workshop A", monthly=None)
    location(session, product_id, "Closed", status=UsageLocationStatus.INACTIVE)
    (settings.sds_root_path / f"{current}.pdf").write_bytes(b"source pdf")
    (settings.bhp_evidence_root_path / f"{current_decision}.pdf").write_bytes(b"evidence")

    rows = read(session, settings)
    assert len(rows) == 1
    [row] = rows
    assert row.product_id == product_id
    assert row.product_name == "Paint"
    assert row.manufacturer_name == "TASK-026 Manufacturer"
    assert row.manufacturer_product_code == "001"
    assert row.usage_status == status
    assert row.use_description == "Painting"
    assert row.use_restriction == "Professional use"
    assert row.usage_locations == ("Workshop A", "Workshop B")
    assert row.current_sds_id == current
    assert row.current_sds_filename == "original.pdf"
    assert row.current_sds_issue_date == date(2025, 1, 1)
    assert row.current_sds_revision == "1"
    assert row.current_sds_file_available is True
    assert row.current_bhp_decision_id == current_decision
    assert row.current_bhp_decision_status == BhpDecisionStatus.APPROVED
    assert row.current_bhp_registered_at == NOW
    assert row.current_bhp_notes is None
    assert row.current_bhp_evidence_relative_path == f"{current_decision}.pdf"
    assert row.current_bhp_evidence_available is True
    assert row.action_reasons == ()
    assert row.requires_action is False


@pytest.mark.parametrize("has_current", [True, False])
def test_archived_sds_decision_never_supplies_current_decision(
    session, settings, has_current
):
    product_id = product(session, status=ProductUsageStatus.PENDING_APPROVAL)
    archived = sds(session, product_id, status=SdsDocumentStatus.ARCHIVED)
    old_decision = decision(session, product_id, archived)
    (settings.sds_root_path / f"{archived}.pdf").write_bytes(b"old source")
    (settings.bhp_evidence_root_path / f"{old_decision}.pdf").write_bytes(b"old evidence")
    current = sds(session, product_id, issue_date=None, revision=None) if has_current else None
    if current:
        # A SUPERSEDED-only decision for the new SDS must also be ignored.
        decision(session, product_id, current, status=DecisionRecordStatus.SUPERSEDED)
        (settings.sds_root_path / f"{current}.pdf").write_bytes(b"current source")
    location(session, product_id, "Closed", status=UsageLocationStatus.INACTIVE)

    [row] = read(session, settings)
    assert row.current_sds_id == current
    assert row.current_sds_issue_date is None
    assert row.current_sds_revision is None
    assert row.current_bhp_decision_id is None
    assert row.current_bhp_decision_status is None
    assert row.current_bhp_registered_at is None
    assert row.current_bhp_notes is None
    assert row.current_bhp_evidence_relative_path is None
    assert row.current_bhp_evidence_available is False
    assert row.usage_locations == ()
    expected = ["BRAK DECYZJI BHP"]
    if not has_current:
        assert row.current_sds_filename is None
        assert row.current_sds_file_available is False
        expected.append("BRAK CURRENT SDS")
    expected.append("BRAK MIEJSCA STOSOWANIA")
    assert row.action_reasons == tuple(expected)
    assert row.requires_action is True


def test_live_file_availability_and_rules_do_not_write_core(session, settings):
    product_id = product(session, status=ProductUsageStatus.REJECTED)
    current = sds(session, product_id)
    current_decision = decision(session, product_id, current,
                                result=BhpDecisionStatus.REJECTED, notes="Do not use")
    [facts] = SqlAlchemySupervisoryQuery(session, settings=settings).list_products()
    assert facts.usage_status == ProductUsageStatus.REJECTED
    assert facts.current_sds_file_available is False
    assert facts.action_reasons == ()  # Infrastructure supplies facts only.
    assert facts.requires_action is False
    statements = []
    connection = session.connection()

    def record_sql(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(connection, "before_cursor_execute", record_sql)
    try:
        [missing] = read(session, settings)
        # Creating source files between reads changes availability without a DB update.
        (settings.sds_root_path / f"{current}.pdf").write_bytes(b"source")
        (settings.bhp_evidence_root_path / f"{current_decision}.pdf").write_bytes(b"evidence")
        [available] = read(session, settings)
    finally:
        event.remove(connection, "before_cursor_execute", record_sql)
    assert missing.action_reasons == (
        "PRODUKT ODRZUCONY", "BRAK PLIKU SDS", "BRAK MIEJSCA STOSOWANIA",
        "BRAK PLIKU DOWODU BHP",
    )
    assert available.action_reasons == ("PRODUKT ODRZUCONY", "BRAK MIEJSCA STOSOWANIA")
    assert available.current_bhp_notes == "Do not use"
    assert len(statements) == 4
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in statements)
    assert not any("safety_profiles" in sql or "sds_components" in sql for sql in statements)
    assert session.scalar(select(SdsDocumentModel.file_status)) == FileAvailabilityStatus.MISSING
    assert session.scalar(select(DecisionEvidenceModel.file_status)) == FileAvailabilityStatus.MISSING


def test_multiple_products_stable_order_and_no_autoflush(session, settings):
    ids = [product(session, name=name, code=code) for name, code in (
        ("Zinc", "001"), ("Paint", "002"), ("Paint", "001"), ("Paint", "001")
    )]
    stored = session.get(ProductModel, ids[0])
    stored.product_name = "Unflushed change"
    pending = ManufacturerModel(manufacturer_id=uuid4().hex, manufacturer_name="Unflushed")
    session.add(pending)
    rows = read(session, settings)
    expected = sorted(ids[2:]) + [ids[1], ids[0]]
    assert [row.product_id for row in rows] == expected
    assert rows[-1].product_name == "Zinc"
    assert pending in session.new
    assert stored in session.dirty


@pytest.mark.parametrize("entity", ["SDS", "BHP"])
def test_postgresql_prevents_ambiguous_current(session, settings, entity):
    product_id = product(session)
    current = sds(session, product_id)
    decision(session, product_id, current)
    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            if entity == "SDS":
                sds(session, product_id)
            else:
                decision(session, product_id, current)
    expected = ("uq_sds_documents_one_current_per_product" if entity == "SDS"
                else "uq_bhp_decisions_one_current_per_sds")
    assert error.value.orig.diag.constraint_name == expected
    assert len(read(session, settings)) == 1
