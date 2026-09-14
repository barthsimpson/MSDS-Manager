from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from streamlit.testing.v1 import AppTest

from app.application.dto import (
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
)
from app.application.exceptions import InactiveUsageLocationError
from app.application.use_cases import (
    AssignProductUsageLocation,
    CreateUsageLocation,
    DeactivateUsageLocation,
    GetProductDetails,
    ReactivateUsageLocation,
    UpdateProductUsageLocation,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db import TransactionExecutor
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    ProductUsageLocationHistoryModel,
    ProductUsageLocationModel,
    UsageLocationHistoryModel,
    UsageLocationModel,
)
from app.infrastructure.db.repositories import (
    SqlAlchemyProductHistoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyProductUsageLocationHistoryRepository,
    SqlAlchemyProductUsageLocationRepository,
    SqlAlchemyUsageLocationHistoryRepository,
    SqlAlchemyUsageLocationRepository,
)
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)
from app.presentation.streamlit.composition import build_shell_composition


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = PROJECT_ROOT / "app" / "presentation" / "streamlit" / "app.py"


@pytest.fixture(scope="module")
def database_engine() -> Iterator[Engine]:
    engine = create_engine_from_settings(load_settings())
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(database_engine: Engine) -> sessionmaker[Session]:
    return create_session_factory(database_engine)


def _fixture_ids() -> tuple[str, str, str, str]:
    suffix = uuid4().hex
    return (
        f"task016-manufacturer-{suffix}",
        f"task016-product-{suffix}",
        f"task016-location-a-{suffix}",
        f"task016-location-b-{suffix}",
    )


def _seed_fixture(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
) -> None:
    with session_factory.begin() as session:
        session.add(
            ManufacturerModel(
                manufacturer_id=manufacturer_id,
                manufacturer_name="TASK-016 Fixture Manufacturer",
            )
        )
        session.add(
            ProductModel(
                product_id=product_id,
                product_name="TASK-016 Fixture Product",
                manufacturer_product_code="TASK016",
                manufacturer_id=manufacturer_id,
                use_description="Fixture use",
                use_restriction="Fixture restriction",
                usage_status=ProductUsageStatus.ACTIVE,
            )
        )


def _cleanup_fixture(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
    *location_ids: str,
) -> None:
    with session_factory.begin() as session:
        session.execute(
            delete(ProductUsageLocationHistoryModel).where(
                ProductUsageLocationHistoryModel.product_id == product_id
            )
        )
        session.execute(
            delete(ProductHistoryModel).where(
                ProductHistoryModel.product_id == product_id
            )
        )
        if location_ids:
            session.execute(
                delete(UsageLocationHistoryModel).where(
                    UsageLocationHistoryModel.location_id.in_(location_ids)
                )
            )
            session.execute(
                delete(ProductUsageLocationModel).where(
                    ProductUsageLocationModel.location_id.in_(location_ids)
                )
            )
            session.execute(
                delete(UsageLocationModel).where(
                    UsageLocationModel.location_id.in_(location_ids)
                )
            )
        session.execute(
            delete(ProductModel).where(ProductModel.product_id == product_id)
        )
        session.execute(
            delete(ManufacturerModel).where(
                ManufacturerModel.manufacturer_id == manufacturer_id
            )
        )


def test_task016_sprint2_end_to_end_acceptance(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_a, location_b = _fixture_ids()
    _seed_fixture(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)

    try:
        app = AppTest.from_file(str(APP_PATH)).run(timeout=10)
        assert app.exception == []
        assert app.header[0].value == "Produkty"
        assert any(product_id in str(frame.value) for frame in app.dataframe)
        assert any("TASK-016 Fixture Product" in item.value for item in app.text)

        composition = build_shell_composition()
        try:
            initial = composition.get_product_details(product_id)
            identity = (
                initial.product_name,
                initial.manufacturer_product_code,
                initial.manufacturer_id,
                initial.usage_status,
            )
            composition.update_product_administrative_data(
                UpdateProductAdministrativeDataInput(
                    product_id=product_id,
                    use_description="Updated TASK-016 use",
                    use_restriction="Updated TASK-016 restriction",
                    waste_type="Solvent waste",
                    waste_code="14 06 03*",
                )
            )
        finally:
            composition.dispose()

        for location_id, location_name in (
            (location_a, "TASK-016 Location A"),
            (location_b, "TASK-016 Location B"),
        ):
            executor.execute(
                lambda session, location_id=location_id, location_name=location_name: CreateUsageLocation(
                    SqlAlchemyUsageLocationRepository(session),
                    id_factory=lambda: location_id,
                ).execute(CreateUsageLocationInput(location_name))
            )

        executor.execute(
            lambda session: AssignProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyProductUsageLocationHistoryRepository(session),
            ).execute(
                AssignProductUsageLocationInput(
                    product_id, location_a, Decimal("0"), "kg", None, None
                )
            )
        )
        executor.execute(
            lambda session: AssignProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyProductUsageLocationHistoryRepository(session),
            ).execute(
                AssignProductUsageLocationInput(
                    product_id, location_b, Decimal("2.50"), "l", Decimal("0"), "kg"
                )
            )
        )

        with session_factory() as session:
            details = GetProductDetails(SqlAlchemyProductRepository(session)).execute(
                product_id
            )
            assert details.use_description == "Updated TASK-016 use"
            assert details.waste_code == "14 06 03*"
            assert (
                details.product_name,
                details.manufacturer_product_code,
                details.manufacturer_id,
                details.usage_status,
            ) == identity
            quantities = {item.location_id: item for item in details.usage_locations}
            assert quantities[location_a].monthly_consumption_value is None
            assert quantities[location_b].monthly_consumption_value == Decimal("0")

        executor.execute(
            lambda session: UpdateProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyProductUsageLocationHistoryRepository(session),
            ).execute(
                UpdateProductUsageLocationInput(
                    product_id, location_a, Decimal("3.25"), "kg", Decimal("0"), "l"
                )
            )
        )
        executor.execute(
            lambda session: DeactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyUsageLocationHistoryRepository(session),
            ).execute(location_b)
        )
        with pytest.raises(InactiveUsageLocationError):
            executor.execute(
                lambda session: AssignProductUsageLocation(
                    SqlAlchemyProductUsageLocationRepository(session),
                    SqlAlchemyUsageLocationRepository(session),
                    SqlAlchemyProductUsageLocationHistoryRepository(session),
                ).execute(
                    AssignProductUsageLocationInput(
                        product_id, location_b, Decimal("1"), "kg", None, None
                    )
                )
            )
        executor.execute(
            lambda session: ReactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyUsageLocationHistoryRepository(session),
            ).execute(location_b)
        )

        with session_factory() as session:
            product_history = SqlAlchemyProductHistoryRepository(session).get_by_product_id(
                product_id
            )
            location_history = SqlAlchemyUsageLocationHistoryRepository(session).get_by_location_id(
                location_b
            )
            quantity_history = SqlAlchemyProductUsageLocationHistoryRepository(
                session
            ).get_by_product_and_location(product_id, location_a)
            current = session.get(ProductUsageLocationModel, (product_id, location_a))
            stored_location = session.get(UsageLocationModel, location_b)

            assert len(product_history) == 1
            assert product_history[0].waste_code == "14 06 03*"
            assert [item.status for item in location_history] == [
                UsageLocationStatus.INACTIVE,
                UsageLocationStatus.ACTIVE,
            ]
            assert [item.peak_quantity_value for item in quantity_history] == [
                Decimal("0"),
                Decimal("3.25"),
            ]
            assert quantity_history[0].monthly_consumption_value is None
            assert quantity_history[1].monthly_consumption_value == Decimal("0")
            assert quantity_history[0].history_id != quantity_history[1].history_id
            assert (quantity_history[0].changed_at, quantity_history[0].history_id) < (
                quantity_history[1].changed_at,
                quantity_history[1].history_id,
            )
            assert current is not None
            assert current.peak_quantity_value == Decimal("3.25")
            assert stored_location is not None
            assert stored_location.status is UsageLocationStatus.ACTIVE
    finally:
        _cleanup_fixture(
            session_factory, manufacturer_id, product_id, location_a, location_b
        )
