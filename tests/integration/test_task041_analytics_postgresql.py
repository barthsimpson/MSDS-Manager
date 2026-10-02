"""TASK-041 read model on PostgreSQL; every inserted fixture is rolled back."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Engine, event, func, insert, select
from sqlalchemy.orm import Session

from app.application.dto.analytics import (
    AnalyticsBhpStatus as Bhp, AnalyticsFilters, AnalyticsSdsStatus,
)
from app.application.use_cases.get_analytics_dashboard import GetAnalyticsDashboard
from app.application.use_cases.list_analytics_product_locations import ListAnalyticsProductLocations
from app.domain.enums import (
    BhpDecisionStatus, DecisionRecordStatus, EvidenceFileFormat, EvidenceType,
    FileAvailabilityStatus, ProductUsageStatus, SdsDocumentStatus, UsageLocationStatus,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    BhpDecisionModel, DecisionEvidenceModel, ManufacturerModel, ProductModel,
    ProductUsageLocationModel, SdsDocumentModel, UnitOfMeasureModel, UsageLocationModel,
)
from app.infrastructure.db.repositories.analytics_query import SqlAlchemyAnalyticsQuery
from app.infrastructure.db.session import create_engine_from_settings
from app.infrastructure.filesystem.analytics_availability import AnalyticsFileAvailabilityAdapter
from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


@pytest.fixture(scope="module")
def engine():
    instance = create_engine_from_settings(load_settings())
    assert instance.dialect.name == "postgresql"
    try:
        yield instance
    finally:
        instance.dispose()


@pytest.fixture
def session(engine: Engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(connection) as session:
                yield session
        finally:
            if transaction.is_active:
                transaction.rollback()


def _id():
    return str(uuid4())


def _filters(manufacturer=None, **kwargs):
    return AnalyticsFilters(
        manufacturer_id=manufacturer,
        trend_date_from=date(2026, 1, 1), trend_date_to=date(2026, 12, 31),
        **kwargs,
    )


def _seed(session: Session):
    manufacturer_a, manufacturer_b = uuid4(), uuid4()
    for manufacturer in (manufacturer_a, manufacturer_b):
        session.execute(insert(ManufacturerModel).values(
            manufacturer_id=str(manufacturer), manufacturer_name=f"TASK041 {manufacturer}",
        ))

    def product(name, manufacturer=manufacturer_a, status=ProductUsageStatus.ACTIVE):
        product_id = _id()
        session.execute(insert(ProductModel).values(
            product_id=product_id, product_name=name,
            manufacturer_product_code=product_id,
            manufacturer_id=str(manufacturer), usage_status=status,
            use_description="Test", use_restriction="Test",
        ))
        return product_id

    no_sds = product("No SDS")
    approved = product("Approved")
    rejected = product("Rejected", status=ProductUsageStatus.REJECTED)
    no_decision = product("No decision", status=ProductUsageStatus.PENDING_APPROVAL)
    archived_only = product("Archived only", status=ProductUsageStatus.INACTIVE)
    other = product("Other manufacturer", manufacturer_b)

    def sds(product_id, *, current=True, at=datetime(2026, 2, 1), sds_id=None, revision=None):
        sds_id = sds_id or _id()
        session.execute(insert(SdsDocumentModel).values(
            sds_id=sds_id, product_id=product_id,
            original_filename="source.pdf", relative_path=f"{sds_id}.pdf",
            document_status=(SdsDocumentStatus.CURRENT if current else SdsDocumentStatus.ARCHIVED),
            registered_at=at, issue_date=date(2030, 1, 1) if not current else None,
            revision=revision, file_status=FileAvailabilityStatus.MISSING,
        ))
        return sds_id

    def decision(product_id, sds_id, *, result=BhpDecisionStatus.APPROVED,
                 record=DecisionRecordStatus.CURRENT):
        evidence_id, decision_id = _id(), _id()
        session.execute(insert(DecisionEvidenceModel).values(
            evidence_id=evidence_id, original_filename="decision.pdf",
            relative_path=f"{evidence_id}.pdf", evidence_type=EvidenceType.DOCUMENT,
            file_format=EvidenceFileFormat.PDF, file_status=FileAvailabilityStatus.MISSING,
        ))
        session.execute(insert(BhpDecisionModel).values(
            decision_id=decision_id, product_id=product_id, sds_id=sds_id,
            decision_status=result, record_status=record,
            evidence_id=evidence_id, registered_at=datetime(2026, 2, 2),
        ))
        return evidence_id

    # Same-time tie: lexical sds_id determines NEW, even if CURRENT has older issue_date.
    first = sds(approved, current=False, sds_id="a-" + _id())
    current = sds(approved, sds_id="b-" + _id(), revision="2")
    decision(approved, first, result=BhpDecisionStatus.REJECTED)
    decision(approved, current, result=BhpDecisionStatus.REJECTED,
             record=DecisionRecordStatus.SUPERSEDED)
    approved_evidence = decision(approved, current)
    rejected_sds = sds(rejected)
    decision(rejected, rejected_sds, result=BhpDecisionStatus.REJECTED)
    sds(no_decision)
    old = sds(archived_only, current=False)
    decision(archived_only, old)
    sds(other)

    active_a, active_b, inactive = uuid4(), uuid4(), uuid4()
    for location_id, status in (
        (active_a, UsageLocationStatus.ACTIVE),
        (active_b, UsageLocationStatus.ACTIVE),
        (inactive, UsageLocationStatus.INACTIVE),
    ):
        session.execute(insert(UsageLocationModel).values(
            location_id=str(location_id), location_name=str(location_id), status=status,
        ))
    unit = session.scalar(select(UnitOfMeasureModel.unit_id).where(UnitOfMeasureModel.code == "kg"))
    assert unit is not None
    for product_id, location_id, peak, monthly in (
        (approved, active_a, 0, 0), (approved, active_b, 2, None),
        (rejected, active_a, 3, None), (no_decision, inactive, 4, None),
    ):
        session.execute(insert(ProductUsageLocationModel).values(
            product_id=product_id, location_id=str(location_id),
            peak_quantity_value=peak, peak_quantity_unit_id=unit,
            monthly_consumption_value=monthly,
            monthly_consumption_unit_id=unit if monthly is not None else None,
        ))
    return {
        "manufacturer_a": manufacturer_a, "manufacturer_b": manufacturer_b,
        "no_sds": no_sds, "approved": approved, "rejected": rejected,
        "no_decision": no_decision, "archived_only": archived_only,
        "other": other, "current": current, "approved_evidence": approved_evidence,
        "active_a": active_a, "active_b": active_b,
    }


def test_dashboard_facts_filters_trend_and_query_count(session: Session, tmp_path: Path):
    ids = _seed(session)
    sds_root, evidence_root = tmp_path / "sds", tmp_path / "evidence"
    sds_root.mkdir()
    evidence_root.mkdir()
    (sds_root / f'{ids["current"]}.pdf').write_bytes(b"pdf")
    (evidence_root / f'{ids["approved_evidence"]}.pdf').write_bytes(b"evidence")
    query = SqlAlchemyAnalyticsQuery(session)
    files = AnalyticsFileAvailabilityAdapter(SdsPdfStorage(sds_root), BhpEvidenceStorage(evidence_root))
    filters = _filters(ids["manufacturer_a"])
    statements = []
    connection = session.connection()
    listener = lambda _conn, _cursor, sql, _params, _context, _many: statements.append(sql)
    event.listen(connection, "before_cursor_execute", listener)
    try:
        dashboard = GetAnalyticsDashboard(query, files).execute(filters)
    finally:
        event.remove(connection, "before_cursor_execute", listener)
    facts = {f.product_id: f for f in dashboard.product_facts}
    assert set(facts) == {ids[key] for key in (
        "no_sds", "approved", "rejected", "no_decision", "archived_only")}
    assert dashboard.kpi.products_total == 5
    assert dashboard.kpi.current_sds_count == 3
    assert dashboard.kpi.bhp_approved_count == 1
    assert dashboard.kpi.active_locations_count == 2  # shared location counted once
    assert facts[ids["approved"]].active_location_count == 2
    assert facts[ids["archived_only"]].bhp_category == Bhp.NOT_APPLICABLE_NO_CURRENT_SDS
    assert facts[ids["approved"]].bhp_category == Bhp.APPROVED
    assert facts[ids["rejected"]].bhp_category == Bhp.REJECTED
    assert facts[ids["no_decision"]].bhp_category == Bhp.NO_DECISION
    assert dashboard.bhp_status.no_decision == 1
    assert dashboard.attention.no_current_sds_count == 2
    assert dashboard.attention.no_bhp_decision_count == 1
    assert dashboard.attention.no_active_location_count == 2
    assert dashboard.attention.missing_source_file_count == 2
    assert dashboard.kpi.attention_products_count == 4
    assert len(dashboard.sds_trend) == 1
    assert (dashboard.sds_trend[0].new_sds_count,
            dashboard.sds_trend[0].updated_sds_count) == (4, 1)
    assert dashboard.manufacturer_summary[0].latest_sds_registered_at == datetime(2026, 2, 1)
    assert len(statements) == 3
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in statements)

    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], sds_status=AnalyticsSdsStatus.CURRENT_MISSING
    ))} == {ids["no_sds"], ids["archived_only"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], bhp_status=Bhp.APPROVED
    ))} == {ids["approved"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], bhp_status=Bhp.NO_DECISION
    ))} == {ids["no_decision"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], bhp_status=Bhp.REJECTED
    ))} == {ids["rejected"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], usage_location_id=ids["active_a"]
    ))} == {ids["approved"], ids["rejected"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], include_no_active_location=True
    ))} == {ids["no_sds"], ids["no_decision"], ids["archived_only"]}
    assert {f.product_id for f in query.list_product_facts(_filters(
        ids["manufacturer_a"], usage_location_id=ids["active_a"],
        include_no_active_location=True,
    ))} == {ids["approved"], ids["rejected"], ids["no_sds"],
           ids["no_decision"], ids["archived_only"]}
    assert query.get_active_location_count(_filters(ids["manufacturer_a"],
        usage_location_id=ids["active_a"]), (ids["approved"], ids["rejected"])) == 1
    assert query.get_active_location_count(_filters(), ()) == session.scalar(
        select(func.count()).select_from(UsageLocationModel).where(
            UsageLocationModel.status == UsageLocationStatus.ACTIVE
        )
    )

    detail = [row for row in ListAnalyticsProductLocations(query).execute(filters)
              if row.product_id in facts]
    assert len(detail) == 6
    assert {r.location_id for r in detail if r.product_id == ids["approved"]} == {
        str(ids["active_a"]), str(ids["active_b"])
    }
    no_active = [r for r in detail if r.product_id == ids["no_decision"]]
    assert len(no_active) == 1 and no_active[0].location_id is None
    zero = next(r for r in detail if r.product_id == ids["approved"]
                and r.location_id == str(ids["active_a"]))
    assert zero.peak_quantity_value == Decimal("0")
    assert zero.monthly_consumption_value == Decimal("0")
    assert zero.peak_quantity_unit_code == "kg"

    earlier = GetAnalyticsDashboard(query, files).execute(
        AnalyticsFilters(manufacturer_id=ids["manufacturer_a"],
                         trend_date_from=date(2025, 1, 1), trend_date_to=date(2025, 12, 31))
    )
    assert earlier.kpi == dashboard.kpi
    assert earlier.sds_trend == ()
