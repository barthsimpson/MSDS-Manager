"""Conditional legacy code update on disposable PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.application.dto import AssignLegacyUsageLocationCodeInput
from app.application.exceptions import DuplicateLocationCodeError, LocationCodeAlreadyAssignedError
from app.application.use_cases import AssignLegacyUsageLocationCode
from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories import SqlAlchemyUsageLocationRepository


def test_conditional_assignment_preserves_other_data_and_rejects_duplicate() -> None:
    engine = create_engine(load_settings().database_url)
    assert engine.dialect.name == "postgresql"
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            first_id, second_id = str(uuid4()), str(uuid4())
            connection.execute(text(
                "INSERT INTO usage_locations (location_id, location_name, status) "
                "VALUES (:id, 'Legacy line', 'INACTIVE')"
            ), {"id": first_id})
            connection.execute(text(
                "INSERT INTO usage_locations (location_id, location_name, status) "
                "VALUES (:id, 'Another line', 'ACTIVE')"
            ), {"id": second_id})
            history_before = connection.scalar(text("SELECT count(*) FROM usage_location_history"))
            assignments_before = connection.scalar(text("SELECT count(*) FROM product_usage_locations"))
            with Session(bind=connection) as session:
                repository = SqlAlchemyUsageLocationRepository(session)
                use_case = AssignLegacyUsageLocationCode(repository)
                result = use_case.execute(AssignLegacyUsageLocationCodeInput(first_id, " mzt "))
                assert result.location_code == "MZT"
                with pytest.raises(LocationCodeAlreadyAssignedError):
                    use_case.execute(AssignLegacyUsageLocationCodeInput(first_id, "OTHER"))
                with pytest.raises(DuplicateLocationCodeError):
                    use_case.execute(AssignLegacyUsageLocationCodeInput(second_id, "mzt"))
                with pytest.raises(DuplicateLocationCodeError):
                    with session.begin_nested():
                        repository.assign_legacy_code(second_id, "MZT")
            rows = connection.execute(text(
                "SELECT location_id, location_name, status, location_code "
                "FROM usage_locations WHERE location_id IN (:first, :second) ORDER BY location_id"
            ), {"first": first_id, "second": second_id}).all()
            by_id = {row.location_id: row for row in rows}
            assert (by_id[first_id].location_name, by_id[first_id].status,
                    by_id[first_id].location_code) == ("Legacy line", "INACTIVE", "MZT")
            assert (by_id[second_id].location_name, by_id[second_id].status,
                    by_id[second_id].location_code) == ("Another line", "ACTIVE", None)
            assert connection.scalar(text("SELECT count(*) FROM usage_location_history")) == history_before
            assert connection.scalar(text("SELECT count(*) FROM product_usage_locations")) == assignments_before
        finally:
            transaction.rollback()
    engine.dispose()
