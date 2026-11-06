"""usage_locations.location_code checks against a disposable PostgreSQL database at migration head."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.application.dto import CreateUsageLocationInput
from app.application.exceptions import DuplicateLocationCodeError
from app.application.use_cases import CreateUsageLocation, DeactivateUsageLocation, ReactivateUsageLocation
from app.domain.enums import UsageLocationStatus
from app.domain.models import UsageLocation
from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories import (
    SqlAlchemyUsageLocationHistoryRepository,
    SqlAlchemyUsageLocationRepository,
)


@pytest.fixture
def connection():
    engine = create_engine(load_settings().database_url)
    assert engine.dialect.name == "postgresql"
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            yield conn
        finally:
            transaction.rollback()
    engine.dispose()


def _reject_sql(connection, code: str | None) -> None:
    savepoint = connection.begin_nested()
    try:
        with pytest.raises((IntegrityError, DataError)):
            connection.execute(
                text("INSERT INTO usage_locations (location_id, location_code, location_name, status) "
                     "VALUES (:id, :code, 'invalid', 'ACTIVE')"),
                {"id": str(uuid4()), "code": code},
            )
    finally:
        savepoint.rollback()


def test_location_code_schema(connection) -> None:
    column = next(c for c in inspect(connection).get_columns("usage_locations")
                  if c["name"] == "location_code")
    assert column["nullable"] is False
    assert column["type"].length == 32
    assert "location_code" not in {
        column["name"] for column in inspect(connection).get_columns("usage_location_history")
    }
    _reject_sql(connection, None)
    _reject_sql(connection, "lower")
    _reject_sql(connection, "-START")
    _reject_sql(connection, "A" * 33)


def test_create_duplicate_lifecycle_and_history(connection) -> None:
    with Session(bind=connection) as session:
        locations = SqlAlchemyUsageLocationRepository(session)
        history = SqlAlchemyUsageLocationHistoryRepository(session)
        create = CreateUsageLocation(locations, id_factory=lambda: str(uuid4()))
        created = create.execute(CreateUsageLocationInput("New location", " mzt "))
        assert created.location_code == "MZT"
        session.flush()
        assert locations.get_by_id(created.location_id).location_code == "MZT"
        with pytest.raises(DuplicateLocationCodeError):
            create.execute(CreateUsageLocationInput("Other location", "mzt"))
        with pytest.raises(DuplicateLocationCodeError):
            with session.begin_nested():
                locations.add(UsageLocation(str(uuid4()), "Concurrent", location_code="MZT"))
        _reject_sql(connection, "MZT")

        inactive = DeactivateUsageLocation(locations, history).execute(created.location_id)
        active = ReactivateUsageLocation(locations, history).execute(created.location_id)
        assert inactive.status is UsageLocationStatus.INACTIVE
        assert active.status is UsageLocationStatus.ACTIVE
        assert active.location_id == created.location_id
        assert active.location_code == "MZT"
        snapshots = history.get_by_location_id(created.location_id)
        assert [row.status for row in snapshots] == [
            UsageLocationStatus.INACTIVE, UsageLocationStatus.ACTIVE
        ]
        assert all(not hasattr(row, "location_code") for row in snapshots)
