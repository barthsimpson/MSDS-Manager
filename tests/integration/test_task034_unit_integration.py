"""TASK-034 quantity writes and code reads on PostgreSQL, always rolled back."""

from collections.abc import Iterator
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import AssignProductUsageLocationInput, UpdateProductUsageLocationInput
from app.application.exceptions import InactiveUnitOfMeasureError
from app.application.use_cases import (
    AssignProductUsageLocation, GetProductDetails, ListSupervisoryProducts,
    UpdateProductUsageLocation,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db import TransactionExecutor
from app.infrastructure.db.repositories import (
    SqlAlchemyProductRepository, SqlAlchemyProductUsageLocationHistoryRepository,
    SqlAlchemyProductUsageLocationRepository, SqlAlchemySupervisoryQuery,
    SqlAlchemyUnitOfMeasureRepository, SqlAlchemyUsageLocationRepository,
)


def unit_id(code: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"msds-manager/unit-of-measure/{code}"))


@pytest.fixture
def connection() -> Iterator[Connection]:
    engine = create_engine(load_settings().database_url)
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            yield conn
        finally:
            transaction.rollback()
    engine.dispose()


def test_active_write_history_and_inactive_read_models(connection: Connection) -> None:
    marker = uuid4().hex
    with Session(bind=connection) as session:
        session.execute(text(
            "INSERT INTO manufacturers (manufacturer_id, manufacturer_name) "
            "VALUES (:id, 'TASK-034')"
        ), {"id": marker})
        session.execute(text("""
            INSERT INTO products (
                product_id, product_name, manufacturer_product_code, manufacturer_id,
                use_description, use_restriction, usage_status
            ) VALUES (:id, 'TASK-034', :id, :id, '', '', 'ACTIVE')
        """), {"id": marker})
        session.execute(text(
            "INSERT INTO usage_locations (location_id, location_name, status) "
            "VALUES (:id, 'TASK-034', 'ACTIVE')"
        ), {"id": marker})

        current = SqlAlchemyProductUsageLocationRepository(session)
        history = SqlAlchemyProductUsageLocationHistoryRepository(session)
        units = SqlAlchemyUnitOfMeasureRepository(session)
        AssignProductUsageLocation(
            current, SqlAlchemyUsageLocationRepository(session), history,
            unit_repository=units,
        ).execute(AssignProductUsageLocationInput(
            marker, marker, Decimal("0"), unit_id("kg"),
        ))
        session.flush()
        UpdateProductUsageLocation(
            current, history, unit_repository=units,
        ).execute(UpdateProductUsageLocationInput(
            marker, marker, Decimal("2"), unit_id("kg"),
            Decimal("0"), unit_id("l"),
        ))
        session.flush()

        snapshots = history.get_by_product_and_location(marker, marker)
        assert [(row.peak_quantity_unit_id, row.monthly_consumption_unit_id)
                for row in snapshots] == [
                    (unit_id("kg"), None), (unit_id("kg"), unit_id("l")),
                ]
        assert snapshots[1].monthly_consumption_value == Decimal("0")

        session.execute(
            text("UPDATE unit_of_measure SET status = 'INACTIVE' WHERE code = 'kg'")
        )
        with pytest.raises(InactiveUnitOfMeasureError):
            UpdateProductUsageLocation(
                current, history, unit_repository=units,
            ).execute(UpdateProductUsageLocationInput(
                marker, marker, Decimal("3"), unit_id("kg"),
                Decimal("0"), unit_id("l"),
            ))
        session.flush()
        assert len(history.get_by_product_and_location(marker, marker)) == 2

        details = GetProductDetails(SqlAlchemyProductRepository(session)).execute(marker)
        assignment = details.usage_locations[0]
        assert assignment.peak_quantity_unit == "kg"
        assert assignment.peak_quantity_unit_id == unit_id("kg")
        assert assignment.monthly_consumption_unit == "l"
        assert assignment.monthly_consumption_unit_id == unit_id("l")
        rows = ListSupervisoryProducts(
            SqlAlchemySupervisoryQuery(session, settings=load_settings())
        ).execute()
        row = next(row for row in rows if row.product_id == marker)
        assert (row.peak_quantity_unit, row.monthly_consumption_unit) == ("kg", "l")
        assert row.monthly_consumption_value == Decimal("0")

        UpdateProductUsageLocation(
            current, history, unit_repository=units,
        ).execute(UpdateProductUsageLocationInput(
            marker, marker, Decimal("2"), unit_id("l"),
            Decimal("0"), unit_id("l"),
        ))
        session.flush()
        snapshots = history.get_by_product_and_location(marker, marker)
        assert [row.peak_quantity_unit_id for row in snapshots] == [
            unit_id("kg"), unit_id("kg"), unit_id("l"),
        ]


@pytest.mark.parametrize("operation", ["assign", "update"])
def test_history_write_failure_rolls_back_current_state(
    connection: Connection, operation: str
) -> None:
    marker = uuid4().hex
    connection.execute(text(
        "INSERT INTO manufacturers (manufacturer_id, manufacturer_name) "
        "VALUES (:id, 'TASK-035')"
    ), {"id": marker})
    connection.execute(text("""
        INSERT INTO products (
            product_id, product_name, manufacturer_product_code, manufacturer_id,
            use_description, use_restriction, usage_status
        ) VALUES (:id, 'TASK-035', :id, :id, '', '', 'ACTIVE')
    """), {"id": marker})
    connection.execute(text(
        "INSERT INTO usage_locations (location_id, location_name, status) "
        "VALUES (:id, 'TASK-035', 'ACTIVE')"
    ), {"id": marker})
    if operation == "update":
        connection.execute(text("""
            INSERT INTO product_usage_locations (
                product_id, location_id, peak_quantity_value, peak_quantity_unit_id
            ) VALUES (:id, :id, 1, :unit_id)
        """), {"id": marker, "unit_id": unit_id("kg")})

    class FailingHistory:
        def __init__(self, session: Session) -> None:
            self.session = session

        def add(self, _snapshot) -> None:
            self.session.flush()
            raise RuntimeError("history write failed")

    factory = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")

    def write(session: Session) -> None:
        current = SqlAlchemyProductUsageLocationRepository(session)
        history = FailingHistory(session)
        units = SqlAlchemyUnitOfMeasureRepository(session)
        if operation == "assign":
            AssignProductUsageLocation(
                current, SqlAlchemyUsageLocationRepository(session), history,
                unit_repository=units,
            ).execute(AssignProductUsageLocationInput(
                marker, marker, Decimal("2"), unit_id("l")
            ))
        else:
            UpdateProductUsageLocation(
                current, history, unit_repository=units,
            ).execute(UpdateProductUsageLocationInput(
                marker, marker, Decimal("2"), unit_id("l")
            ))

    with pytest.raises(RuntimeError, match="history write failed"):
        TransactionExecutor(factory).execute(write)

    row = connection.execute(text(
        "SELECT peak_quantity_value, peak_quantity_unit_id "
        "FROM product_usage_locations WHERE product_id = :id"
    ), {"id": marker}).one_or_none()
    if operation == "assign":
        assert row is None
    else:
        assert row.peak_quantity_value == Decimal("1")
        assert str(row.peak_quantity_unit_id) == unit_id("kg")
    assert connection.execute(text(
        "SELECT COUNT(*) FROM product_usage_location_history WHERE product_id = :id"
    ), {"id": marker}).scalar_one() == 0
