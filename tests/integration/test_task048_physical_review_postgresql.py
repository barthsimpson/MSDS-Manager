"""TASK-048 lifecycle and Analytics-02 read on an isolated PostgreSQL database."""

import os
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, insert, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.analytics import AnalyticsFilters
from app.application.use_cases.physical_review import (
    CreatePhysicalReview, DiscardPhysicalReviewDraft, EmptyReviewPopulationError,
    FinalReviewImmutableError, FinalizePhysicalReview, InvalidObservedQuantityError,
    ReviewAlreadyFinalError, ReviewDraftAlreadyExistsError,
    UpdateReviewObservedQuantity,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    ManufacturerModel, PhysicalReviewItemModel, PhysicalReviewModel, ProductModel,
    ProductUsageLocationModel, UnitOfMeasureModel, UsageLocationModel,
)
from app.infrastructure.db.repositories import SqlAlchemyPhysicalReviewRepository
from app.infrastructure.db.repositories.analytics_query import SqlAlchemyAnalyticsQuery
from app.infrastructure.db.transactions import TransactionExecutor


@pytest.fixture(scope="module")
def isolated_database():
    operator_url = make_url(load_settings().database_url)
    assert operator_url.database == "msds_manager"
    database = f"task048_{uuid4().hex}"
    maintenance = create_engine(operator_url, isolation_level="AUTOCOMMIT")
    isolated_url = operator_url.set(database=database)
    original_url = os.environ.get("DATABASE_URL")
    engine = None
    created = False
    try:
        with maintenance.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{database}"')
        created = True
        os.environ["DATABASE_URL"] = isolated_url.render_as_string(hide_password=False)
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_engine(isolated_url)
        yield engine
    finally:
        if original_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_url
        if engine is not None:
            engine.dispose()
        if created:
            with maintenance.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{database}" WITH (FORCE)')
        maintenance.dispose()


def _seed(engine):
    manufacturer = str(uuid4())
    product = str(uuid4())
    inactive_product = str(uuid4())
    active_location = str(uuid4())
    inactive_location = str(uuid4())
    unit = str(uuid4())
    with Session(engine) as session, session.begin():
        session.execute(insert(ManufacturerModel).values(
            manufacturer_id=manufacturer, manufacturer_name="TASK-048",
        ))
        for product_id, status in ((product, "ACTIVE"), (inactive_product, "INACTIVE")):
            session.execute(insert(ProductModel).values(
                product_id=product_id, product_name=f"Produkt {product_id[:4]}",
                manufacturer_product_code=product_id, manufacturer_id=manufacturer,
                use_description="", use_restriction="", usage_status=status,
            ))
        for location_id, code, status in (
            (active_location, "T48-A", "ACTIVE"),
            (inactive_location, "T48-I", "INACTIVE"),
        ):
            session.execute(insert(UsageLocationModel).values(
                location_id=location_id, location_code=code,
                location_name=f"Lokalizacja {code}", status=status,
            ))
        session.execute(insert(UnitOfMeasureModel).values(
            unit_id=unit, code="task048-kg", name="Kilogram TASK-048",
            category="MASS", status="ACTIVE",
        ))
        for product_id, location_id, quantity in (
            (product, active_location, Decimal("10")),
            (inactive_product, active_location, Decimal("2")),
            (product, inactive_location, Decimal("99")),
        ):
            session.execute(insert(ProductUsageLocationModel).values(
                product_id=product_id, location_id=location_id,
                peak_quantity_value=quantity, peak_quantity_unit_id=unit,
            ))
    return product, inactive_product, active_location


def test_review_lifecycle_snapshot_latest_final_and_analytics(isolated_database, monkeypatch):
    engine = isolated_database
    executor = TransactionExecutor(sessionmaker(bind=engine, expire_on_commit=False))

    def write(use_case, *args):
        return executor.execute(lambda session: use_case(
            SqlAlchemyPhysicalReviewRepository(session)
        ).execute(*args))

    with pytest.raises(EmptyReviewPopulationError):
        write(CreatePhysicalReview, date(2026, 10, 1))
    with Session(engine) as session:
        assert session.scalar(select(PhysicalReviewModel.review_id)) is None

    product, inactive_product, location = _seed(engine)
    original_add = SqlAlchemyPhysicalReviewRepository.add_items
    def fail_after_header(self, items):
        raise RuntimeError("simulated item failure")
    monkeypatch.setattr(SqlAlchemyPhysicalReviewRepository, "add_items", fail_after_header)
    with pytest.raises(RuntimeError):
        write(CreatePhysicalReview, date(2026, 10, 1))
    monkeypatch.setattr(SqlAlchemyPhysicalReviewRepository, "add_items", original_add)
    with Session(engine) as session:
        assert session.scalar(select(PhysicalReviewModel.review_id)) is None

    first = write(CreatePhysicalReview, date(2026, 10, 1))
    with pytest.raises(ReviewDraftAlreadyExistsError):
        write(CreatePhysicalReview, date(2026, 10, 2))
    with Session(engine) as session:
        repository = SqlAlchemyPhysicalReviewRepository(session)
        detail = repository.get_review(first)
        assert detail is not None
        assert detail.total_items == 2  # inactive PRODUCT remains, inactive location excluded
        assert detail.unobserved_items == 2
        item = next(row for row in detail.items if row.product_id == product)
        assert item.baseline_max_quantity == Decimal("10")
        assert item.unit_code == "task048-kg"
        item_id = item.review_item_id

    with pytest.raises(InvalidObservedQuantityError):
        write(UpdateReviewObservedQuantity, item_id, Decimal("-1"))
    write(UpdateReviewObservedQuantity, item_id, Decimal("0"))
    with Session(engine) as session:
        detail = SqlAlchemyPhysicalReviewRepository(session).get_review(first)
        assert detail.observed_items == 1
        assert detail.unobserved_items == 1
        assert next(row for row in detail.items if row.product_id == product).difference == -10
    write(UpdateReviewObservedQuantity, item_id, None)
    with Session(engine) as session:
        assert SqlAlchemyPhysicalReviewRepository(session).get_review(first).unobserved_items == 2

    write(DiscardPhysicalReviewDraft, first)
    with Session(engine) as session:
        assert session.scalar(select(PhysicalReviewModel.review_id)) is None
        assert session.scalar(select(PhysicalReviewItemModel.review_item_id)) is None

    older = write(CreatePhysicalReview, date(2026, 9, 30))
    with Session(engine) as session:
        row = next(row for row in SqlAlchemyPhysicalReviewRepository(session).get_review(older).items
                   if row.product_id == product)
    write(UpdateReviewObservedQuantity, row.review_item_id, Decimal("7"))
    write(FinalizePhysicalReview, older)
    with pytest.raises(FinalReviewImmutableError):
        write(UpdateReviewObservedQuantity, row.review_item_id, Decimal("8"))
    with pytest.raises(FinalReviewImmutableError):
        write(DiscardPhysicalReviewDraft, older)
    with pytest.raises(ReviewAlreadyFinalError):
        write(FinalizePhysicalReview, older)

    with Session(engine) as session, session.begin():
        session.execute(update(ProductUsageLocationModel).where(
            ProductUsageLocationModel.product_id == product,
            ProductUsageLocationModel.location_id == location,
        ).values(peak_quantity_value=Decimal("20")))
    newer = write(CreatePhysicalReview, date(2026, 10, 2))
    with Session(engine) as session:
        detail = SqlAlchemyPhysicalReviewRepository(session).get_review(newer)
        assert next(row for row in detail.items if row.product_id == product).baseline_max_quantity == 20
    write(FinalizePhysicalReview, newer)  # latest NULL must hide older observed=7

    with Session(engine) as session:
        repo = SqlAlchemyPhysicalReviewRepository(session)
        latest = {(row.product_id, row.location_id): row
                  for row in repo.get_latest_final_items_for_analytics()}
        assert latest[(product, location)].observed_quantity is None
        assert latest[(product, location)].difference is None
        assert repo.get_review(older).items[0].baseline_max_quantity in (Decimal("10"), Decimal("2"))
        rows = SqlAlchemyAnalyticsQuery(session).list_product_location_rows(AnalyticsFilters(
            trend_date_from=date(2026, 1, 1), trend_date_to=date(2026, 12, 31),
        ))
        current = next(row for row in rows if row.product_id == product and row.location_id == location)
        assert current.peak_quantity_value == 20
        assert current.review_observed_quantity is None
        assert current.review_difference is None

    newest = write(CreatePhysicalReview, date(2026, 10, 2))
    with Session(engine) as session:
        row = next(row for row in SqlAlchemyPhysicalReviewRepository(session).get_review(newest).items
                   if row.product_id == product)
    write(UpdateReviewObservedQuantity, row.review_item_id, Decimal("23"))
    write(FinalizePhysicalReview, newest)
    with Session(engine) as session:
        latest = SqlAlchemyPhysicalReviewRepository(session).get_latest_final_items_for_analytics()
        result = next(row for row in latest if row.product_id == product)
        assert result.observed_quantity == 23
        assert result.difference == 3  # tied review_date, later finalized_at
        rows = SqlAlchemyAnalyticsQuery(session).list_product_location_rows(AnalyticsFilters(
            trend_date_from=date(2026, 1, 1), trend_date_to=date(2026, 12, 31),
        ))
        current = next(row for row in rows if row.product_id == product and row.location_id == location)
        assert current.review_observed_quantity == 23
        assert current.review_difference == 3
        assert current.review_unit_code == "task048-kg"
