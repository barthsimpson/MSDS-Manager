"""TASK-051-R1 identity operations on a disposable PostgreSQL database."""

from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.application.dto import (
    CompleteManufacturerProductCodeInput, CorrectProductIdentityInput,
)
from app.application.use_cases import CompleteManufacturerProductCode, CorrectProductIdentity
from app.domain.enums import ProductUsageStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    ManufacturerModel, ProductIdentityChangeModel, ProductModel,
)
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.db.transactions import TransactionExecutor


@pytest.fixture
def database():
    settings = load_settings()
    if not make_url(settings.database_url).database.startswith("task051_"):
        pytest.skip("TASK-051 integration requires an isolated task051_ PostgreSQL database")
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _seed(factory, code: str | None = None) -> tuple[str, str]:
    manufacturer_id = uuid4().hex
    product_id = uuid4().hex
    with factory.begin() as session:
        session.add(ManufacturerModel(
            manufacturer_id=manufacturer_id, manufacturer_name=f"TASK-051 {manufacturer_id}"
        ))
        session.add(ProductModel(
            product_id=product_id, product_name="Original product",
            manufacturer_product_code=code, manufacturer_id=manufacturer_id,
            use_description="Use", use_restriction="Restriction",
            usage_status=ProductUsageStatus.ACTIVE,
        ))
    return product_id, manufacturer_id


def test_null_code_completion_and_explicit_correction(database) -> None:
    _, factory = database
    product_id, manufacturer_id = _seed(factory)
    executor = TransactionExecutor(factory)

    executor.execute(lambda session: CompleteManufacturerProductCode(
        SqlAlchemyProductRepository(session)
    ).execute(CompleteManufacturerProductCodeInput(product_id, " CODE-1 ")))

    with factory() as session:
        product = session.get(ProductModel, product_id)
        changes = session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        )).all()
        assert product.product_id == product_id
        assert product.manufacturer_product_code == "CODE-1"
        assert product.product_name == "Original product"
        assert product.manufacturer_id == manufacturer_id
        assert len(changes) == 1
        assert changes[0].change_kind == "CODE_COMPLETION"
        assert changes[0].old_manufacturer_product_code is None
        assert changes[0].new_manufacturer_product_code == "CODE-1"
        assert changes[0].old_product_name == changes[0].new_product_name == "Original product"
        assert changes[0].old_manufacturer_id == changes[0].new_manufacturer_id == manufacturer_id

    executor.execute(lambda session: CorrectProductIdentity(
        SqlAlchemyProductRepository(session)
    ).execute(CorrectProductIdentityInput(
        product_id, "Corrected product", "CODE-2", f"TASK-051 {manufacturer_id}"
    )))

    with factory() as session:
        product = session.get(ProductModel, product_id)
        changes = session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        ).order_by(ProductIdentityChangeModel.changed_at)).all()
        assert product.product_id == product_id
        assert product.manufacturer_product_code == "CODE-2"
        assert product.product_name == "Corrected product"
        assert len(changes) == 2
        correction = next(change for change in changes if change.change_kind == "CORRECTION")
        assert (correction.old_product_name, correction.new_product_name) == (
            "Original product", "Corrected product"
        )
        assert (correction.old_manufacturer_product_code,
                correction.new_manufacturer_product_code) == ("CODE-1", "CODE-2")
        assert correction.old_manufacturer_id == correction.new_manufacturer_id == manufacturer_id


def test_reject_known_code_and_roll_back_on_history_failure(database) -> None:
    engine, factory = database
    product_id, manufacturer_id = _seed(factory)
    executor = TransactionExecutor(factory)

    def fail_history(_mapper, _connection, _target) -> None:
        raise RuntimeError("synthetic identity history failure")

    event.listen(ProductIdentityChangeModel, "before_insert", fail_history)
    try:
        with pytest.raises(RuntimeError, match="history failure"):
            executor.execute(lambda session: CompleteManufacturerProductCode(
                SqlAlchemyProductRepository(session)
            ).execute(CompleteManufacturerProductCodeInput(product_id, "CODE-1")))
    finally:
        event.remove(ProductIdentityChangeModel, "before_insert", fail_history)

    with Session(engine) as session:
        assert session.get(ProductModel, product_id).manufacturer_product_code is None
        assert session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        )).all() == []

    executor.execute(lambda session: CompleteManufacturerProductCode(
        SqlAlchemyProductRepository(session)
    ).execute(CompleteManufacturerProductCodeInput(product_id, "CODE-1")))
    with pytest.raises(ValueError, match="już znany"):
        executor.execute(lambda session: CompleteManufacturerProductCode(
            SqlAlchemyProductRepository(session)
        ).execute(CompleteManufacturerProductCodeInput(product_id, "CODE-2")))
    with Session(engine) as session:
        assert session.get(ProductModel, product_id).manufacturer_product_code == "CODE-1"
        assert len(session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        )).all()) == 1

    event.listen(ProductIdentityChangeModel, "before_insert", fail_history)
    try:
        with pytest.raises(RuntimeError, match="history failure"):
            executor.execute(lambda session: CorrectProductIdentity(
                SqlAlchemyProductRepository(session)
            ).execute(CorrectProductIdentityInput(
                product_id, "Incorrect correction", "CODE-2", f"TASK-051 {manufacturer_id}"
            )))
    finally:
        event.remove(ProductIdentityChangeModel, "before_insert", fail_history)

    with Session(engine) as session:
        product = session.get(ProductModel, product_id)
        assert product.product_name == "Original product"
        assert product.manufacturer_product_code == "CODE-1"
        assert len(session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        )).all()) == 1


def test_missing_code_cannot_be_silently_classified_as_correction(database) -> None:
    engine, factory = database
    product_id, manufacturer_id = _seed(factory)
    with pytest.raises(ValueError, match="osobną operacją"):
        TransactionExecutor(factory).execute(lambda session: CorrectProductIdentity(
            SqlAlchemyProductRepository(session)
        ).execute(CorrectProductIdentityInput(
            product_id, "Original product", "CODE-1", f"TASK-051 {manufacturer_id}"
        )))
    with Session(engine) as session:
        assert session.get(ProductModel, product_id).manufacturer_product_code is None
        assert session.scalars(select(ProductIdentityChangeModel).where(
            ProductIdentityChangeModel.product_id == product_id
        )).all() == []
