from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

from app.application.use_cases import ListManufacturers
from app.domain.models import Manufacturer
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import ManufacturerModel
from app.infrastructure.db.repositories import SqlAlchemyManufacturerRepository
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)


def test_application_vertical_slice_uses_postgresql_and_rolls_back() -> None:
    settings = load_settings()
    assert make_url(settings.database_url).database == "msds_manager"
    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    manufacturer_ids = [
        f"task007-manufacturer-a-{uuid4().hex}",
        f"task007-manufacturer-b-{uuid4().hex}",
    ]
    expected = {
        Manufacturer(manufacturer_ids[0], "TASK-007 Manufacturer A"),
        Manufacturer(manufacturer_ids[1], "TASK-007 Manufacturer B"),
    }

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                assert connection.execute(text("SELECT 1")).scalar_one() == 1
                with session_factory(bind=connection) as session:
                    session.add_all(
                        [
                            ManufacturerModel(
                                manufacturer_id=manufacturer_ids[0],
                                manufacturer_name="TASK-007 Manufacturer A",
                            ),
                            ManufacturerModel(
                                manufacturer_id=manufacturer_ids[1],
                                manufacturer_name="TASK-007 Manufacturer B",
                            ),
                        ]
                    )
                    session.flush()

                    repository = SqlAlchemyManufacturerRepository(session)
                    result = ListManufacturers(repository).execute()

                    assert set(result) == expected
                    assert all(isinstance(item, Manufacturer) for item in result)
                    assert not any(isinstance(item, ManufacturerModel) for item in result)
            finally:
                if transaction.is_active:
                    transaction.rollback()

        with engine.connect() as verification_connection:
            remaining = verification_connection.scalar(
                select(func.count())
                .select_from(ManufacturerModel)
                .where(ManufacturerModel.manufacturer_id.in_(manufacturer_ids))
            )
            assert remaining == 0
    finally:
        engine.dispose()
