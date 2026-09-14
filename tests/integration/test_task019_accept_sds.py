from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import AcceptSdsInput, SdsComponentDraft
from app.application.use_cases import AcceptSds
from app.domain.enums import ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db import TransactionExecutor
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    SafetyProfileModel,
    SdsComponentModel,
    SdsDocumentModel,
)
from app.infrastructure.db.repositories import SqlAlchemySdsAcceptanceRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator


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


def _input(path: str, suffix: str) -> AcceptSdsInput:
    return AcceptSdsInput(
        source_relative_path=path,
        product_name=f"TASK-019 Product {suffix}",
        manufacturer_product_code=f"TASK019-{suffix}",
        manufacturer_name=f"TASK-019 Manufacturer {suffix}",
        use_description="Industrial use",
        use_restriction="Professional use",
        detected_language="PL",
        language_valid=True,
        components=[
            SdsComponentDraft(
                component_name="Test component",
                cas_number="111-11-1",
                hazard_statements=["H315"],
            )
        ],
    )


def _write_pdf(root: Path, name: str) -> str:
    relative = f"task019/{name}.pdf"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4 TASK-019")
    return relative


def _cleanup(session_factory: sessionmaker[Session], prefix: str) -> None:
    with session_factory.begin() as session:
        product_ids = session.scalars(
            select(ProductModel.product_id).where(ProductModel.product_name.like(f"{prefix}%"))
        ).all()
        if product_ids:
            sds_ids = session.scalars(
                select(SdsDocumentModel.sds_id).where(SdsDocumentModel.product_id.in_(product_ids))
            ).all()
            if sds_ids:
                session.execute(delete(SdsComponentModel).where(SdsComponentModel.sds_id.in_(sds_ids)))
                session.execute(delete(SafetyProfileModel).where(SafetyProfileModel.sds_id.in_(sds_ids)))
                session.execute(delete(SdsDocumentModel).where(SdsDocumentModel.sds_id.in_(sds_ids)))
            session.execute(delete(ProductHistoryModel).where(ProductHistoryModel.product_id.in_(product_ids)))
            manufacturer_ids = session.scalars(
                select(ProductModel.manufacturer_id).where(ProductModel.product_id.in_(product_ids))
            ).all()
            session.execute(delete(ProductModel).where(ProductModel.product_id.in_(product_ids)))
            session.execute(delete(ManufacturerModel).where(ManufacturerModel.manufacturer_id.in_(manufacturer_ids)))


def test_accept_sds_persists_and_archives_current(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    settings = load_settings()
    suffix = uuid4().hex
    prefix = f"TASK-019 Product {suffix}"
    first = _input(_write_pdf(settings.sds_root_path, f"first-{suffix}"), suffix)
    second = _input(_write_pdf(settings.sds_root_path, f"second-{suffix}"), suffix)
    validator = SdsFileValidator(settings.sds_root_path)
    executor = TransactionExecutor(session_factory)

    try:
        first_id = executor.execute(
            lambda session: AcceptSds(
                SqlAlchemySdsAcceptanceRepository(session), validator
            ).execute(first)
        )
        second_id = executor.execute(
            lambda session: AcceptSds(
                SqlAlchemySdsAcceptanceRepository(session), validator
            ).execute(second)
        )
        with session_factory() as session:
            product = session.scalar(select(ProductModel).where(ProductModel.product_name == first.product_name))
            assert product is not None
            assert len(session.scalars(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == first.manufacturer_name)).all()) == 1
            assert product.usage_status == ProductUsageStatus.PENDING_APPROVAL
            documents = session.scalars(
                select(SdsDocumentModel).where(SdsDocumentModel.product_id == product.product_id)
            ).all()
            assert {document.sds_id for document in documents} == {first_id, second_id}
            assert sum(document.document_status == SdsDocumentStatus.CURRENT for document in documents) == 1
            profile = session.get(SafetyProfileModel, second_id)
            assert profile is not None
            assert session.scalars(select(SdsComponentModel).where(SdsComponentModel.sds_id == second_id)).one().cas_number == "111-11-1"
            assert session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product.product_id)).all()
    finally:
        _cleanup(session_factory, prefix)


def test_accept_sds_rolls_back_after_repository_failure(
    session_factory: sessionmaker[Session],
) -> None:
    settings = load_settings()
    suffix = uuid4().hex
    input_data = _input(_write_pdf(settings.sds_root_path, f"rollback-{suffix}"), suffix)

    class FailingRepository(SqlAlchemySdsAcceptanceRepository):
        def accept(self, data: AcceptSdsInput) -> str:
            result = super().accept(data)
            raise RuntimeError("controlled TASK-019 failure")

    try:
        with pytest.raises(RuntimeError):
            TransactionExecutor(session_factory).execute(
                lambda session: AcceptSds(
                    FailingRepository(session), SdsFileValidator(settings.sds_root_path)
                ).execute(input_data)
            )
        with session_factory() as session:
            assert session.scalar(select(ProductModel).where(ProductModel.product_name == input_data.product_name)) is None
            assert session.scalar(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == input_data.manufacturer_name)) is None
    finally:
        _cleanup(session_factory, f"TASK-019 Product {suffix}")