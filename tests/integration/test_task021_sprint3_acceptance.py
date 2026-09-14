from collections.abc import Iterator
from pathlib import Path
from shutil import copyfile
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from streamlit.testing.v1 import AppTest

from app.domain.enums import ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    SafetyProfileModel,
    SdsComponentModel,
    SdsDocumentModel,
)
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.presentation.streamlit.composition import ShellComposition


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT_ROOT / "docs" / "tasks" / (
    "30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf"
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


def _app(composition: ShellComposition) -> AppTest:
    def render(current_composition) -> None:
        from app.presentation.streamlit.add_sds import render_add_sds

        render_add_sds(current_composition)

    return AppTest.from_function(render, args=(composition,))


def _cleanup(session_factory: sessionmaker[Session], product_name: str) -> None:
    with session_factory.begin() as session:
        product_ids = session.scalars(
            select(ProductModel.product_id).where(
                ProductModel.product_name == product_name
            )
        ).all()
        if not product_ids:
            return
        sds_ids = session.scalars(
            select(SdsDocumentModel.sds_id).where(
                SdsDocumentModel.product_id.in_(product_ids)
            )
        ).all()
        session.execute(
            delete(SdsComponentModel).where(SdsComponentModel.sds_id.in_(sds_ids))
        )
        session.execute(
            delete(SafetyProfileModel).where(SafetyProfileModel.sds_id.in_(sds_ids))
        )
        session.execute(
            delete(SdsDocumentModel).where(SdsDocumentModel.sds_id.in_(sds_ids))
        )
        session.execute(
            delete(ProductHistoryModel).where(
                ProductHistoryModel.product_id.in_(product_ids)
            )
        )
        manufacturer_ids = session.scalars(
            select(ProductModel.manufacturer_id).where(
                ProductModel.product_id.in_(product_ids)
            )
        ).all()
        session.execute(delete(ProductModel).where(ProductModel.product_id.in_(product_ids)))
        session.execute(
            delete(ManufacturerModel).where(
                ManufacturerModel.manufacturer_id.in_(manufacturer_ids)
            )
        )


def test_task021_real_sds_ui_to_postgresql_and_second_current(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    suffix = uuid4().hex
    product_name = "IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO"
    manufacturer_name = f"TASK-021 manual manufacturer {suffix}"
    test_root = tmp_path / "sds-root"
    first_relative = "30470-first.pdf"
    second_relative = "30470-second.pdf"
    test_root.mkdir()
    copyfile(FIXTURE, test_root / first_relative)
    copyfile(FIXTURE, test_root / second_relative)
    engine = session_factory.kw["bind"]
    composition = ShellComposition(
        engine=engine,
        session_factory=session_factory,
        products=(),
        sds_root_path=test_root,
    )

    try:
        with session_factory() as session:
            assert session.scalar(
                select(ProductModel).where(ProductModel.product_name == product_name)
            ) is None
        app = _app(composition).run()
        assert app.header[0].value == "Dodaj SDS"
        assert set(app.selectbox[0].options) == {first_relative, second_relative}

        app.selectbox[0].set_value(first_relative).run()
        app.button(key="read-sds").click().run()
        assert app.text_input(key="sds-product-name").value == product_name
        assert app.text_input(key="sds-product-code").value == "30470"
        assert app.text_input(key="sds-use-description").value == "Farba lub inna podobna substancja."
        assert app.text_input(key="sds-use-restriction").value == "Jedynie do stosowania przemysłowego."
        assert app.text_input(key="sds-revision").value == "10.02"
        assert app.date_input(key="sds-issue-date").value.isoformat() == "2025-10-03"
        assert any(component.cas_number == "111-76-2" for component in app.session_state["add_sds_draft"].components)

        app.text_input(key="sds-manufacturer").set_value(manufacturer_name)
        app.button(key="accept-sds").click().run()
        assert app.success
        assert "add_sds_draft" not in app.session_state

        with session_factory() as session:
            product = session.scalar(
                select(ProductModel).where(ProductModel.product_name == product_name)
            )
            assert product is not None
            assert product.manufacturer_product_code == "30470"
            assert product.usage_status == ProductUsageStatus.PENDING_APPROVAL
            first_documents = session.scalars(
                select(SdsDocumentModel).where(
                    SdsDocumentModel.product_id == product.product_id
                )
            ).all()
            assert len(first_documents) == 1
            assert first_documents[0].document_status == SdsDocumentStatus.CURRENT
            assert session.get(SafetyProfileModel, first_documents[0].sds_id) is not None
            assert session.scalars(
                select(SdsComponentModel).where(
                    SdsComponentModel.sds_id == first_documents[0].sds_id
                )
            ).all()
            assert len(session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product.product_id)).all()) == 1

        app.selectbox[0].set_value(second_relative).run()
        app.button(key="read-sds").click().run()
        app.text_input(key="sds-manufacturer").set_value(manufacturer_name)
        app.text_input(key="sds-revision").set_value("10.03")
        app.button(key="accept-sds").click().run()

        with session_factory() as session:
            product = session.scalar(
                select(ProductModel).where(ProductModel.product_name == product_name)
            )
            assert product is not None
            documents = session.scalars(
                select(SdsDocumentModel).where(
                    SdsDocumentModel.product_id == product.product_id
                ).order_by(SdsDocumentModel.registered_at)
            ).all()
            assert len(documents) == 2
            assert documents[0].document_status == SdsDocumentStatus.ARCHIVED
            assert documents[1].document_status == SdsDocumentStatus.CURRENT
            assert sum(document.document_status == SdsDocumentStatus.CURRENT for document in documents) == 1
            assert len(session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product.product_id)).all()) == 2

        app.selectbox[0].set_value(first_relative).run()
        app.button(key="read-sds").click().run()
        app.button(key="cancel-sds").click().run()
        assert "add_sds_draft" not in app.session_state

        app.selectbox[0].set_value(first_relative).run()
        app.button(key="read-sds").click().run()
        app.text_input(key="sds-manufacturer").set_value("")
        app.button(key="accept-sds").click().run()
        assert app.error
        assert not app.success
        assert "add_sds_draft" in app.session_state
    finally:
        composition.dispose()
        _cleanup(session_factory, product_name)
        (test_root / first_relative).unlink(missing_ok=True)
        (test_root / second_relative).unlink(missing_ok=True)
        assert not (test_root / first_relative).exists()
        assert not (test_root / second_relative).exists()