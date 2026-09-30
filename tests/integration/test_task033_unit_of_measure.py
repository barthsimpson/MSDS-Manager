"""Focused PostgreSQL checks for TASK-033's dictionary and quantity references."""

from collections.abc import Iterator
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from sqlalchemy import Connection, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.dto import AssignProductUsageLocationInput, UpdateProductUsageLocationInput
from app.application.use_cases import AssignProductUsageLocation, UpdateProductUsageLocation
from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories import (
    SqlAlchemyProductUsageLocationHistoryRepository,
    SqlAlchemyProductUsageLocationRepository,
    SqlAlchemyUnitOfMeasureRepository,
    SqlAlchemyUsageLocationRepository,
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


def expect_integrity_error(connection: Connection, statement: str, **parameters: object) -> None:
    savepoint = connection.begin_nested()
    try:
        with pytest.raises(IntegrityError):
            connection.execute(text(statement), parameters)
    finally:
        savepoint.rollback()


def seed_product_and_location(connection: Connection) -> tuple[str, str]:
    suffix = uuid4().hex
    manufacturer_id = f"task033-manufacturer-{suffix}"
    product_id = f"task033-product-{suffix}"
    location_id = f"task033-location-{suffix}"
    connection.execute(
        text("INSERT INTO manufacturers (manufacturer_id, manufacturer_name) VALUES (:id, 'TASK-033')"),
        {"id": manufacturer_id},
    )
    connection.execute(
        text("""INSERT INTO products (
            product_id, product_name, manufacturer_product_code, manufacturer_id,
            use_description, use_restriction, usage_status
        ) VALUES (:product_id, 'TASK-033', :product_id, :manufacturer_id, '', '', 'ACTIVE')"""),
        {"product_id": product_id, "manufacturer_id": manufacturer_id},
    )
    connection.execute(
        text("INSERT INTO usage_locations (location_id, location_name, status) "
             "VALUES (:id, 'TASK-033', 'ACTIVE')"),
        {"id": location_id},
    )
    return product_id, location_id


def test_seed_repository_and_dictionary_constraints(connection: Connection) -> None:
    rows = connection.execute(text(
        "SELECT unit_id, code, name, category, status FROM unit_of_measure ORDER BY code"
    )).all()
    assert [(row.code, row.name, row.category, row.status) for row in rows] == [
        ("g", "gram", "MASS", "ACTIVE"),
        ("kg", "kilogram", "MASS", "ACTIVE"),
        ("l", "litr", "VOLUME", "ACTIVE"),
        ("ml", "mililitr", "VOLUME", "ACTIVE"),
        ("szt", "sztuka", "COUNT", "ACTIVE"),
    ]
    assert {str(row.unit_id) for row in rows} == {unit_id(row.code) for row in rows}
    with Session(bind=connection) as session:
        repository = SqlAlchemyUnitOfMeasureRepository(session)
        assert {unit.code for unit in repository.list_active()} == {"l", "ml", "kg", "g", "szt"}
        assert repository.get_by_id(unit_id("kg")).name == "kilogram"

    connection.execute(text(
        "INSERT INTO unit_of_measure (unit_id, code, name, category, status) "
        "VALUES (:id, 'inactive-test', 'inactive test', 'COUNT', 'INACTIVE')"
    ), {"id": str(uuid4())})
    with Session(bind=connection) as session:
        assert "inactive-test" not in {
            unit.code for unit in SqlAlchemyUnitOfMeasureRepository(session).list_active()
        }
    expect_integrity_error(
        connection,
        "INSERT INTO unit_of_measure (unit_id, code, name, category, status) "
        "VALUES (:id, 'kg', 'duplicate', 'MASS', 'ACTIVE')",
        id=str(uuid4()),
    )
    for category, status in (("LENGTH", "ACTIVE"), ("MASS", "UNKNOWN")):
        expect_integrity_error(
            connection,
            "INSERT INTO unit_of_measure (unit_id, code, name, category, status) "
            "VALUES (:id, :code, 'invalid', :category, :status)",
            id=str(uuid4()), code=f"invalid-{uuid4().hex}", category=category, status=status,
        )


def test_current_and_history_store_unit_ids_and_monthly_zero(connection: Connection) -> None:
    product_id, location_id = seed_product_and_location(connection)
    with Session(bind=connection) as session:
        current = SqlAlchemyProductUsageLocationRepository(session)
        history = SqlAlchemyProductUsageLocationHistoryRepository(session)
        units = SqlAlchemyUnitOfMeasureRepository(session)
        AssignProductUsageLocation(
            current, SqlAlchemyUsageLocationRepository(session), history,
            unit_repository=units,
        ).execute(AssignProductUsageLocationInput(
            product_id, location_id, Decimal("0"), unit_id("kg")
        ))
        session.flush()
        UpdateProductUsageLocation(
            current, history, unit_repository=units,
        ).execute(UpdateProductUsageLocationInput(
            product_id, location_id, Decimal("2.5"), unit_id("l"),
            Decimal("0"), unit_id("ml"),
        ))
        session.flush()
        snapshots = history.get_by_product_and_location(product_id, location_id)
        assert len(snapshots) == 2
        assert snapshots[0].peak_quantity_unit_id == unit_id("kg")
        assert snapshots[0].monthly_consumption_value is None
        assert snapshots[0].monthly_consumption_unit_id is None
        assert snapshots[1].peak_quantity_unit_id == unit_id("l")
        assert snapshots[1].monthly_consumption_value == Decimal("0")
        assert snapshots[1].monthly_consumption_unit_id == unit_id("ml")
    current_row = connection.execute(text(
        "SELECT peak_quantity_unit_id, monthly_consumption_unit_id, monthly_consumption_value "
        "FROM product_usage_locations WHERE product_id = :id"
    ), {"id": product_id}).one()
    assert str(current_row.peak_quantity_unit_id) == unit_id("l")
    assert str(current_row.monthly_consumption_unit_id) == unit_id("ml")
    assert current_row.monthly_consumption_value == Decimal("0")


def test_database_fk_pair_and_schema_constraints(connection: Connection) -> None:
    product_id, location_id = seed_product_and_location(connection)
    inspector = inspect(connection)
    for table in ("product_usage_locations", "product_usage_location_history"):
        unit_fks = {
            fk["constrained_columns"][0]
            for fk in inspector.get_foreign_keys(table)
            if fk["referred_table"] == "unit_of_measure"
        }
        assert unit_fks == {"peak_quantity_unit_id", "monthly_consumption_unit_id"}
        columns = {column["name"]: column for column in inspector.get_columns(table)}
        assert not columns["peak_quantity_unit_id"]["nullable"]
        assert columns["monthly_consumption_unit_id"]["nullable"]
        assert "peak_quantity_unit" not in columns
        assert "monthly_consumption_unit" not in columns
    current_sql = (
        "INSERT INTO product_usage_locations (product_id, location_id, peak_quantity_value, "
        "peak_quantity_unit_id, monthly_consumption_value, monthly_consumption_unit_id) "
        "VALUES (:product_id, :location_id, 0, :peak_id, :monthly_value, :monthly_id)"
    )
    base = {"product_id": product_id, "location_id": location_id,
            "peak_id": unit_id("kg"), "monthly_value": None, "monthly_id": None}
    expect_integrity_error(connection, current_sql, **{**base, "peak_id": str(uuid4())})
    expect_integrity_error(connection, current_sql, **{**base, "monthly_id": unit_id("l")})
    expect_integrity_error(connection, current_sql, **{**base, "monthly_value": 0})
    connection.execute(text(current_sql), base)
    history_sql = (
        "INSERT INTO product_usage_location_history (history_id, product_id, location_id, "
        "peak_quantity_value, peak_quantity_unit_id, monthly_consumption_value, "
        "monthly_consumption_unit_id, changed_at) VALUES "
        "(:history_id, :product_id, :location_id, 0, :peak_id, :monthly_value, :monthly_id, now())"
    )
    history_base = {**base, "history_id": uuid4().hex}
    expect_integrity_error(connection, history_sql, **{**history_base, "peak_id": str(uuid4())})
    expect_integrity_error(connection, history_sql, **{**history_base, "monthly_id": unit_id("l")})
    connection.execute(text(history_sql), history_base)
