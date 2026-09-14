from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from streamlit.testing.v1 import AppTest

from app.application.dto import RegisterBhpDecisionInput
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SdsDocumentStatus,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db import TransactionExecutor
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    SdsDocumentModel,
)
from app.infrastructure.db.repositories import SqlAlchemyBhpDecisionRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.filesystem.bhp_evidence_validator import BhpEvidenceValidator
from app.presentation.streamlit.composition import ShellComposition


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
        from app.presentation.streamlit.bhp_decision import render_bhp_decision

        render_bhp_decision(current_composition)

    return AppTest.from_function(render, args=(composition,))


def _seed(session_factory: sessionmaker[Session], suffix: str) -> tuple[str, str, str, str]:
    manufacturer_id = f"task025-manufacturer-{suffix}"
    product_id = f"task025-product-{suffix}"
    current_sds_id = f"task025-current-sds-{suffix}"
    archived_sds_id = f"task025-archived-sds-{suffix}"
    with session_factory.begin() as session:
        session.add(
            ManufacturerModel(
                manufacturer_id=manufacturer_id,
                manufacturer_name=f"TASK-025 Manufacturer {suffix}",
            )
        )
        session.add(
            ProductModel(
                product_id=product_id,
                product_name=f"TASK-025 Product {suffix}",
                manufacturer_product_code="TASK025",
                manufacturer_id=manufacturer_id,
                use_description="Test use",
                use_restriction="Test restriction",
                usage_status=ProductUsageStatus.PENDING_APPROVAL,
            )
        )
        for sds_id, status in (
            (current_sds_id, SdsDocumentStatus.CURRENT),
            (archived_sds_id, SdsDocumentStatus.ARCHIVED),
        ):
            session.add(
                SdsDocumentModel(
                    sds_id=sds_id,
                    product_id=product_id,
                    original_filename=f"{sds_id}.pdf",
                    relative_path=f"{sds_id}.pdf",
                    document_status=status,
                    registered_at=datetime.now(timezone.utc),
                    file_status=FileAvailabilityStatus.AVAILABLE,
                )
            )
    return manufacturer_id, product_id, current_sds_id, archived_sds_id


def _cleanup(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
    sds_ids: tuple[str, ...],
) -> None:
    with session_factory.begin() as session:
        evidence_ids = session.scalars(
            select(BhpDecisionModel.evidence_id).where(
                BhpDecisionModel.sds_id.in_(sds_ids)
            )
        ).all()
        session.execute(
            delete(BhpDecisionModel).where(BhpDecisionModel.sds_id.in_(sds_ids))
        )
        if evidence_ids:
            session.execute(
                delete(DecisionEvidenceModel).where(
                    DecisionEvidenceModel.evidence_id.in_(evidence_ids)
                )
            )
        session.execute(
            delete(ProductHistoryModel).where(
                ProductHistoryModel.product_id == product_id
            )
        )
        session.execute(
            delete(SdsDocumentModel).where(SdsDocumentModel.sds_id.in_(sds_ids))
        )
        session.execute(delete(ProductModel).where(ProductModel.product_id == product_id))
        session.execute(
            delete(ManufacturerModel).where(
                ManufacturerModel.manufacturer_id == manufacturer_id
            )
        )


def test_task025_bhp_ui_postgresql_acceptance(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    suffix = uuid4().hex
    manufacturer_id, product_id, current_sds_id, archived_sds_id = _seed(
        session_factory, suffix
    )
    evidence_root = tmp_path / "bhp-evidence"
    evidence_root.mkdir()
    for filename in ("approved.pdf", "correction.msg", "rejected.jpg"):
        (evidence_root / filename).write_bytes(b"technical evidence fixture")
    engine = session_factory.kw["bind"]
    composition = ShellComposition(
        engine=engine,
        session_factory=session_factory,
        products=(),
        sds_root_path=tmp_path / "sds-root",
        bhp_evidence_root_path=evidence_root,
    )

    try:
        with session_factory() as session:
            assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.PENDING_APPROVAL

        app = _app(composition).run()
        assert app.header[0].value == "Decyzja BHP"
        assert set(app.selectbox[1].options) == {"approved.pdf", "correction.msg", "rejected.jpg"}

        app.selectbox[1].set_value("approved.pdf").run()
        app.text_area(key="bhp-notes").set_value("Approved by BHP")
        app.button(key="save-bhp-decision").click().run()
        assert any("ACTIVE" in item.value for item in app.success)
        assert any("Istniejąca decyzja CURRENT" in item.value for item in app.info)

        with session_factory() as session:
            product = session.get(ProductModel, product_id)
            assert product.usage_status is ProductUsageStatus.ACTIVE
            decision = session.scalar(select(BhpDecisionModel).where(BhpDecisionModel.sds_id == current_sds_id))
            assert decision is not None
            assert decision.decision_status is BhpDecisionStatus.APPROVED
            assert decision.record_status is DecisionRecordStatus.CURRENT
            evidence = session.get(DecisionEvidenceModel, decision.evidence_id)
            assert evidence is not None
            assert evidence.relative_path == "approved.pdf"
            assert decision.notes == "Approved by BHP"
            assert session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id)).all()[-1].usage_status is ProductUsageStatus.ACTIVE

        app.selectbox[1].set_value("correction.msg").run()
        app.radio(key="bhp-decision-status").set_value("REJECTED")
        app.text_area(key="bhp-notes").set_value("Correction decision")
        app.button(key="save-bhp-decision").click().run()
        assert any("REJECTED" in item.value for item in app.success)

        with session_factory() as session:
            decisions = session.scalars(
                select(BhpDecisionModel)
                .where(BhpDecisionModel.sds_id == current_sds_id)
                .order_by(BhpDecisionModel.registered_at)
            ).all()
            assert len(decisions) == 2
            assert decisions[0].record_status is DecisionRecordStatus.SUPERSEDED
            assert decisions[1].record_status is DecisionRecordStatus.CURRENT
            assert decisions[1].decision_status is BhpDecisionStatus.REJECTED
            assert session.get(DecisionEvidenceModel, decisions[0].evidence_id) is not None
            assert session.get(DecisionEvidenceModel, decisions[1].evidence_id) is not None
            assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.REJECTED
            history = session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id)).all()
            assert [item.usage_status for item in history] == [ProductUsageStatus.ACTIVE, ProductUsageStatus.REJECTED]

        empty_composition = ShellComposition(
            engine=engine,
            session_factory=session_factory,
            products=(),
            sds_root_path=tmp_path / "sds-root",
            bhp_evidence_root_path=tmp_path / "empty-evidence",
        )
        (tmp_path / "empty-evidence").mkdir()
        empty_app = _app(empty_composition).run()
        assert any(
            item.value == "Brak dostępnych dowodów decyzji w BHP_EVIDENCE_ROOT_PATH."
            for item in empty_app.info
        )
        assert empty_app.button(key="save-bhp-decision")
        empty_composition.dispose()

        with pytest.raises(ValueError, match="not CURRENT"):
            TransactionExecutor(session_factory).execute(
                lambda session: RegisterBhpDecisionForTest(
                    session, evidence_root
                ).execute(
                    RegisterBhpDecisionInput(
                        product_id=product_id,
                        sds_id=archived_sds_id,
                        decision_status=BhpDecisionStatus.APPROVED,
                        evidence_relative_path="rejected.jpg",
                    )
                )
            )

        class FailingRepository(SqlAlchemyBhpDecisionRepository):
            def _after_evidence_created(self) -> None:
                raise RuntimeError("TASK-025 rollback")

        with pytest.raises(RuntimeError, match="rollback"):
            TransactionExecutor(session_factory).execute(
                lambda session: RegisterBhpDecisionForTest(
                    session, evidence_root, FailingRepository
                ).execute(
                    RegisterBhpDecisionInput(
                        product_id=product_id,
                        sds_id=current_sds_id,
                        decision_status=BhpDecisionStatus.APPROVED,
                        evidence_relative_path="rejected.jpg",
                    )
                )
            )
        with session_factory() as session:
            current = session.scalars(
                select(BhpDecisionModel)
                .where(
                    BhpDecisionModel.sds_id == current_sds_id,
                    BhpDecisionModel.record_status == DecisionRecordStatus.CURRENT,
                )
            ).one()
            assert current.decision_status is BhpDecisionStatus.REJECTED
            assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.REJECTED
    finally:
        composition.dispose()
        _cleanup(session_factory, manufacturer_id, product_id, (current_sds_id, archived_sds_id))


class RegisterBhpDecisionForTest:
    def __init__(self, session: Session, evidence_root: Path, repository_type=None) -> None:
        from app.application.use_cases import RegisterBhpDecision

        self._use_case = RegisterBhpDecision(
            BhpEvidenceValidator(evidence_root),
            (repository_type or SqlAlchemyBhpDecisionRepository)(session),
        )

    def execute(self, data: RegisterBhpDecisionInput):
        return self._use_case.execute(data)