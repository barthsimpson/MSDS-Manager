from collections.abc import Iterator
from decimal import Decimal
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import (
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
)
from app.application.exceptions import EntityNotFoundError, InactiveUsageLocationError
from app.application.use_cases import (
    AssignProductUsageLocation,
    CreateUsageLocation,
    DeactivateUsageLocation,
    GetProductDetails,
    ListProducts,
    ListUsageLocations,
    ReactivateUsageLocation,
    UpdateProductAdministrativeData,
    UpdateProductUsageLocation,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.domain.models import ProductUsageLocation, UsageLocation
from app.infrastructure.config import load_settings
from app.infrastructure.db import PersistenceError, TransactionExecutor
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductModel,
    ProductUsageLocationModel,
    UsageLocationModel,
)
from app.infrastructure.db.repositories import (
    SqlAlchemyProductRepository,
    SqlAlchemyProductUsageLocationRepository,
    SqlAlchemyUsageLocationRepository,
)
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)


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


def ids() -> tuple[str, str, str]:
    suffix = uuid4().hex
    return (
        f"task010-manufacturer-{suffix}",
        f"task010-product-{suffix}",
        f"task010-location-{suffix}",
    )


def seed_product(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
) -> None:
    with session_factory.begin() as session:
        session.add(
            ManufacturerModel(
                manufacturer_id=manufacturer_id,
                manufacturer_name="TASK-010 Manufacturer",
            )
        )
        session.add(
            ProductModel(
                product_id=product_id,
                product_name="TASK-010 Product",
                manufacturer_product_code="TASK010",
                manufacturer_id=manufacturer_id,
                use_description="Original use",
                use_restriction="Original restriction",
                usage_status=ProductUsageStatus.ACTIVE,
                waste_type=None,
                waste_code=None,
            )
        )


def cleanup(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
    *location_ids: str,
) -> None:
    with session_factory.begin() as session:
        session.execute(
            delete(ProductUsageLocationModel).where(
                (ProductUsageLocationModel.product_id == product_id)
                | (ProductUsageLocationModel.location_id.in_(location_ids))
            )
        )
        session.execute(delete(ProductModel).where(ProductModel.product_id == product_id))
        if location_ids:
            session.execute(
                delete(UsageLocationModel).where(
                    UsageLocationModel.location_id.in_(location_ids)
                )
            )
        session.execute(
            delete(ManufacturerModel).where(
                ManufacturerModel.manufacturer_id == manufacturer_id
            )
        )


def test_list_products_returns_empty_list_on_empty_database(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        assert ListProducts(SqlAlchemyProductRepository(session)).execute() == []


def test_product_repository_reads_details_and_commits_only_admin_fields(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)
    try:
        executor.execute(
            lambda session: SqlAlchemyUsageLocationRepository(session).add(
                UsageLocation(location_id, "TASK-010 Line")
            )
        )
        executor.execute(
            lambda session: SqlAlchemyProductUsageLocationRepository(session).add(
                ProductUsageLocation(
                    product_id=product_id,
                    location_id=location_id,
                    peak_quantity_value=Decimal("2.50"),
                    peak_quantity_unit="kg",
                    monthly_consumption_value=Decimal("10"),
                    monthly_consumption_unit="l",
                )
            )
        )

        with session_factory() as session:
            repository = SqlAlchemyProductRepository(session)
            listed = ListProducts(repository).execute()
            details = GetProductDetails(repository).execute(product_id)

        assert len(listed) == 1
        assert listed[0].manufacturer_name == "TASK-010 Manufacturer"
        assert listed[0].usage_status is ProductUsageStatus.ACTIVE
        assert listed[0].waste_type is None
        assert listed[0].waste_code is None
        assert details.usage_locations[0].location_name == "TASK-010 Line"
        assert details.usage_locations[0].peak_quantity_value == Decimal("2.50")
        assert isinstance(details.usage_locations[0].peak_quantity_value, Decimal)

        update_data = UpdateProductAdministrativeDataInput(
            product_id=product_id,
            use_description="Updated use",
            use_restriction="Updated restriction",
            waste_type="Solvent waste",
            waste_code="14 06 03*",
        )
        identity_before = (
            details.product_name,
            details.manufacturer_product_code,
            details.manufacturer_id,
            details.usage_status,
        )
        executor.execute(
            lambda session: UpdateProductAdministrativeData(
                SqlAlchemyProductRepository(session)
            ).execute(update_data)
        )

        with session_factory() as verification_session:
            updated_details = GetProductDetails(
                SqlAlchemyProductRepository(verification_session)
            ).execute(product_id)
            model = verification_session.get(ProductModel, product_id)
            assert model is not None
            assert model.use_description == "Updated use"
            assert model.use_restriction == "Updated restriction"
            assert model.waste_type == "Solvent waste"
            assert model.waste_code == "14 06 03*"
            assert model.product_name == "TASK-010 Product"
            assert model.manufacturer_product_code == "TASK010"
            assert model.manufacturer_id == manufacturer_id
            assert model.usage_status is ProductUsageStatus.ACTIVE
            assert (
                updated_details.product_name,
                updated_details.manufacturer_product_code,
                updated_details.manufacturer_id,
                updated_details.usage_status,
            ) == identity_before

        with pytest.raises(EntityNotFoundError):
            executor.execute(
                lambda session: GetProductDetails(
                    SqlAlchemyProductRepository(session)
                ).execute("missing-product")
            )
    finally:
        cleanup(session_factory, manufacturer_id, product_id, location_id)


def test_usage_location_vertical_slice_commits_lifecycle_and_lists_both_statuses(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    second_location_id = f"{location_id}-second"
    executor = TransactionExecutor(session_factory)
    try:
        created = executor.execute(
            lambda session: CreateUsageLocation(
                SqlAlchemyUsageLocationRepository(session),
                id_factory=lambda: location_id,
            ).execute(CreateUsageLocationInput("TASK-010 Active line"))
        )
        executor.execute(
            lambda session: CreateUsageLocation(
                SqlAlchemyUsageLocationRepository(session),
                id_factory=lambda: second_location_id,
            ).execute(CreateUsageLocationInput("TASK-010 Lifecycle line"))
        )
        inactive = executor.execute(
            lambda session: DeactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session)
            ).execute(second_location_id)
        )

        with session_factory() as session:
            locations = ListUsageLocations(
                SqlAlchemyUsageLocationRepository(session)
            ).execute()
        selected = {
            location.location_id: location
            for location in locations
            if location.location_id in {location_id, second_location_id}
        }

        assert created.status is UsageLocationStatus.ACTIVE
        assert inactive.status is UsageLocationStatus.INACTIVE
        assert selected[location_id].status is UsageLocationStatus.ACTIVE
        assert selected[second_location_id].status is UsageLocationStatus.INACTIVE

        reactivated = executor.execute(
            lambda session: ReactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session)
            ).execute(second_location_id)
        )
        assert reactivated.location_id == second_location_id
        assert reactivated.status is UsageLocationStatus.ACTIVE

        with session_factory() as verification_session:
            stored = verification_session.get(UsageLocationModel, second_location_id)
            assert stored is not None
            assert stored.status is UsageLocationStatus.ACTIVE
    finally:
        cleanup(
            session_factory,
            manufacturer_id,
            product_id,
            location_id,
            second_location_id,
        )


def test_assignment_vertical_slice_preserves_decimal_and_composite_identity(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)
    try:
        executor.execute(
            lambda session: SqlAlchemyUsageLocationRepository(session).add(
                UsageLocation(location_id, "TASK-010 Assignment line")
            )
        )
        assigned = executor.execute(
            lambda session: AssignProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyUsageLocationRepository(session),
            ).execute(
                AssignProductUsageLocationInput(
                    product_id=product_id,
                    location_id=location_id,
                    peak_quantity_value=Decimal("0"),
                    peak_quantity_unit="kg",
                )
            )
        )
        assert assigned.peak_quantity_value == Decimal("0")
        assert assigned.monthly_consumption_value is None

        updated = executor.execute(
            lambda session: UpdateProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session)
            ).execute(
                UpdateProductUsageLocationInput(
                    product_id=product_id,
                    location_id=location_id,
                    peak_quantity_value=Decimal("3.25"),
                    peak_quantity_unit="kg",
                    monthly_consumption_value=Decimal("0"),
                    monthly_consumption_unit="l",
                )
            )
        )

        with session_factory() as verification_session:
            stored = verification_session.get(
                ProductUsageLocationModel, (product_id, location_id)
            )
            assert stored is not None
            assert (stored.product_id, stored.location_id) == (
                product_id,
                location_id,
            )
            assert stored.peak_quantity_value == Decimal("3.25")
            assert isinstance(stored.peak_quantity_value, Decimal)
            assert stored.peak_quantity_unit == "kg"
            assert stored.monthly_consumption_value == Decimal("0")
            assert stored.monthly_consumption_unit == "l"
            assert updated.product_id == stored.product_id
            assert updated.location_id == stored.location_id
    finally:
        cleanup(session_factory, manufacturer_id, product_id, location_id)


def test_product_can_be_assigned_to_multiple_active_locations(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    second_location_id = f"{location_id}-second"
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)
    try:
        for current_location_id, location_name in (
            (location_id, "TASK-011 Location A"),
            (second_location_id, "TASK-011 Location B"),
        ):
            executor.execute(
                lambda session, current_location_id=current_location_id,
                location_name=location_name: CreateUsageLocation(
                    SqlAlchemyUsageLocationRepository(session),
                    id_factory=lambda: current_location_id,
                ).execute(CreateUsageLocationInput(location_name))
            )

        inputs = (
            AssignProductUsageLocationInput(
                product_id=product_id,
                location_id=location_id,
                peak_quantity_value=Decimal("1.25"),
                peak_quantity_unit="kg",
                monthly_consumption_value=None,
                monthly_consumption_unit=None,
            ),
            AssignProductUsageLocationInput(
                product_id=product_id,
                location_id=second_location_id,
                peak_quantity_value=Decimal("4"),
                peak_quantity_unit="l",
                monthly_consumption_value=Decimal("12.5"),
                monthly_consumption_unit="kg",
            ),
        )
        for data in inputs:
            executor.execute(
                lambda session, data=data: AssignProductUsageLocation(
                    SqlAlchemyProductUsageLocationRepository(session),
                    SqlAlchemyUsageLocationRepository(session),
                ).execute(data)
            )

        with session_factory() as session:
            details = GetProductDetails(SqlAlchemyProductRepository(session)).execute(
                product_id
            )

        assert {item.location_id for item in details.usage_locations} == {
            location_id,
            second_location_id,
        }
        second = next(
            item
            for item in details.usage_locations
            if item.location_id == second_location_id
        )
        assert second.peak_quantity_value == Decimal("4")
        assert second.monthly_consumption_value == Decimal("12.5")
        assert second.peak_quantity_unit == "l"
        assert second.monthly_consumption_unit == "kg"
    finally:
        cleanup(
            session_factory,
            manufacturer_id,
            product_id,
            location_id,
            second_location_id,
        )


def test_assignment_to_inactive_location_is_rejected_before_repository_write(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)
    try:
        executor.execute(
            lambda session: SqlAlchemyUsageLocationRepository(session).add(
                UsageLocation(
                    location_id,
                    "TASK-010 Inactive line",
                    UsageLocationStatus.INACTIVE,
                )
            )
        )

        with pytest.raises(InactiveUsageLocationError):
            executor.execute(
                lambda session: AssignProductUsageLocation(
                    SqlAlchemyProductUsageLocationRepository(session),
                    SqlAlchemyUsageLocationRepository(session),
                ).execute(
                    AssignProductUsageLocationInput(
                        product_id=product_id,
                        location_id=location_id,
                        peak_quantity_value=Decimal("1"),
                        peak_quantity_unit="kg",
                    )
                )
            )

        with session_factory() as verification_session:
            assert (
                verification_session.get(
                    ProductUsageLocationModel, (product_id, location_id)
                )
                is None
            )
    finally:
        cleanup(session_factory, manufacturer_id, product_id, location_id)


def test_missing_location_and_assignment_use_application_not_found_errors(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    executor = TransactionExecutor(session_factory)

    with pytest.raises(EntityNotFoundError):
        executor.execute(
            lambda session: DeactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session)
            ).execute(location_id)
        )

    with pytest.raises(EntityNotFoundError):
        executor.execute(
            lambda session: ReactivateUsageLocation(
                SqlAlchemyUsageLocationRepository(session)
            ).execute(location_id)
        )

    with pytest.raises(EntityNotFoundError):
        executor.execute(
            lambda session: UpdateProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session)
            ).execute(
                UpdateProductUsageLocationInput(
                    product_id=product_id,
                    location_id=location_id,
                    peak_quantity_value=Decimal("1"),
                    peak_quantity_unit="kg",
                )
            )
        )


def test_transaction_rolls_back_earlier_valid_change_after_integrity_failure(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)

    def failing_operation(session: Session) -> None:
        UpdateProductAdministrativeData(SqlAlchemyProductRepository(session)).execute(
            UpdateProductAdministrativeDataInput(
                product_id=product_id,
                use_description="Must roll back",
                use_restriction="Must roll back",
                waste_type=None,
                waste_code=None,
            )
        )
        repository = SqlAlchemyUsageLocationRepository(session)
        repository.add(UsageLocation(location_id, "Duplicate A"))
        repository.add(UsageLocation(location_id, "Duplicate B"))

    try:
        with pytest.raises(PersistenceError) as error_info:
            executor.execute(failing_operation)
        assert isinstance(error_info.value.__cause__, SQLAlchemyError)
        assert str(error_info.value) == "Database operation failed."

        with session_factory() as verification_session:
            product = verification_session.get(ProductModel, product_id)
            assert product is not None
            assert product.use_description == "Original use"
            assert product.use_restriction == "Original restriction"
            assert verification_session.get(UsageLocationModel, location_id) is None
    finally:
        cleanup(session_factory, manufacturer_id, product_id, location_id)


def test_postgresql_quantity_check_rejects_invalid_repository_write_and_rolls_back(
    session_factory: sessionmaker[Session],
) -> None:
    manufacturer_id, product_id, location_id = ids()
    seed_product(session_factory, manufacturer_id, product_id)
    executor = TransactionExecutor(session_factory)

    invalid_assignment = cast(
        ProductUsageLocation,
        SimpleNamespace(
            product_id=product_id,
            location_id=location_id,
            peak_quantity_value=Decimal("-1"),
            peak_quantity_unit="kg",
            monthly_consumption_value=None,
            monthly_consumption_unit=None,
        ),
    )

    def failing_operation(session: Session) -> None:
        SqlAlchemyUsageLocationRepository(session).add(
            UsageLocation(location_id, "Must roll back")
        )
        SqlAlchemyProductUsageLocationRepository(session).add(invalid_assignment)

    try:
        with pytest.raises(PersistenceError):
            executor.execute(failing_operation)

        with session_factory() as verification_session:
            assert verification_session.get(UsageLocationModel, location_id) is None
            assert (
                verification_session.get(
                    ProductUsageLocationModel, (product_id, location_id)
                )
                is None
            )
    finally:
        cleanup(session_factory, manufacturer_id, product_id, location_id)
