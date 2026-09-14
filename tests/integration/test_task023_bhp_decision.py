from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import RegisterBhpDecisionInput
from app.application.use_cases import RegisterBhpDecision
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    FileAvailabilityStatus,
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


def _seed(session_factory: sessionmaker[Session]) -> tuple[str, str, str, str]:
    suffix = uuid4().hex
    manufacturer_id = f"task023-manufacturer-{suffix}"
    product_id = f"task023-product-{suffix}"
    sds_id = f"task023-sds-{suffix}"
    other_sds_id = f"task023-other-sds-{suffix}"
    with session_factory.begin() as session:
        session.add(
            ManufacturerModel(
                manufacturer_id=manufacturer_id,
                manufacturer_name=f"TASK-023 Manufacturer {suffix}",
            )
        )
        session.add(
            ProductModel(
                product_id=product_id,
                product_name=f"TASK-023 Product {suffix}",
                manufacturer_product_code="TASK023",
                manufacturer_id=manufacturer_id,
                use_description="Test use",
                use_restriction="Test restriction",
                usage_status="PENDING_APPROVAL",
            )
        )
        for document_id, status in (
            (sds_id, SdsDocumentStatus.CURRENT),
            (other_sds_id, SdsDocumentStatus.ARCHIVED),
        ):
            session.add(
                SdsDocumentModel(
                    sds_id=document_id,
                    product_id=product_id,
                    original_filename=f"{document_id}.pdf",
                    relative_path=f"{document_id}.pdf",
                    document_status=status,
                    registered_at=datetime.now(timezone.utc),
                    file_status=FileAvailabilityStatus.AVAILABLE,
                )
            )
    return manufacturer_id, product_id, sds_id, other_sds_id


def _cleanup(
    session_factory: sessionmaker[Session],
    manufacturer_id: str,
    product_id: str,
    sds_ids: tuple[str, ...],
) -> None:
    with session_factory.begin() as session:
        decision_ids = session.scalars(
            select(BhpDecisionModel.decision_id).where(
                BhpDecisionModel.sds_id.in_(sds_ids)
            )
        ).all()
        evidence_ids = session.scalars(
            select(BhpDecisionModel.evidence_id).where(
                BhpDecisionModel.sds_id.in_(sds_ids)
            )
        ).all()
        if decision_ids:
            session.execute(
                delete(BhpDecisionModel).where(
                    BhpDecisionModel.decision_id.in_(decision_ids)
                )
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


def _input(product_id: str, sds_id: str, evidence_path: str, status: BhpDecisionStatus):
    return RegisterBhpDecisionInput(
        product_id=product_id,
        sds_id=sds_id,
        decision_status=status,
        evidence_relative_path=evidence_path,
        notes="Decision notes",
    )


def test_bhp_decision_persistence_and_superseding(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    manufacturer_id, product_id, sds_id, archived_sds_id = _seed(session_factory)
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    (evidence_root / "approved.pdf").write_bytes(b"approved")
    (evidence_root / "rejected.pdf").write_bytes(b"rejected")
    validator = BhpEvidenceValidator(evidence_root)
    executor = TransactionExecutor(session_factory)

    try:
        approved = executor.execute(
            lambda session: RegisterBhpDecision(
                validator, SqlAlchemyBhpDecisionRepository(session)
            ).execute(_input(product_id, sds_id, "approved.pdf", BhpDecisionStatus.APPROVED))
        )
        rejected = executor.execute(
            lambda session: RegisterBhpDecision(
                validator, SqlAlchemyBhpDecisionRepository(session)
            ).execute(_input(product_id, sds_id, "rejected.pdf", BhpDecisionStatus.REJECTED))
        )

        with session_factory() as session:
            product = session.get(ProductModel, product_id)
            assert product is not None
            assert product.usage_status.value == "REJECTED"
            decisions = session.scalars(
                select(BhpDecisionModel)
                .where(BhpDecisionModel.sds_id == sds_id)
                .order_by(BhpDecisionModel.registered_at)
            ).all()
            assert [decision.decision_id for decision in decisions] == [
                approved.decision_id,
                rejected.decision_id,
            ]
            assert [decision.record_status for decision in decisions] == [
                DecisionRecordStatus.SUPERSEDED,
                DecisionRecordStatus.CURRENT,
            ]
            assert session.get(DecisionEvidenceModel, approved.evidence_relative_path) is None
            assert len(session.scalars(select(DecisionEvidenceModel)).all()) == 2
            history = session.scalars(
                select(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id)
            ).all()
            assert [item.usage_status.value for item in history] == ["ACTIVE", "REJECTED"]
    finally:
        _cleanup(session_factory, manufacturer_id, product_id, (sds_id, archived_sds_id))


def test_archived_sds_is_rejected_without_changes(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    manufacturer_id, product_id, sds_id, archived_sds_id = _seed(session_factory)
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "decision.pdf").write_bytes(b"decision")
    try:
        with pytest.raises(ValueError, match="not CURRENT"):
            TransactionExecutor(session_factory).execute(
                lambda session: RegisterBhpDecision(
                    BhpEvidenceValidator(root), SqlAlchemyBhpDecisionRepository(session)
                ).execute(_input(product_id, archived_sds_id, "decision.pdf", BhpDecisionStatus.APPROVED))
            )
        with session_factory() as session:
            assert session.scalars(select(BhpDecisionModel)).all() == []
            assert session.get(ProductModel, product_id).usage_status.value == "PENDING_APPROVAL"
    finally:
        _cleanup(session_factory, manufacturer_id, product_id, (sds_id, archived_sds_id))


def test_failure_after_evidence_rolls_back_everything(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    manufacturer_id, product_id, sds_id, archived_sds_id = _seed(session_factory)
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "decision.pdf").write_bytes(b"decision")

    class FailingRepository(SqlAlchemyBhpDecisionRepository):
        def _after_evidence_created(self) -> None:
            raise RuntimeError("failure after evidence")

    try:
        with pytest.raises(RuntimeError, match="after evidence"):
            TransactionExecutor(session_factory).execute(
                lambda session: RegisterBhpDecision(
                    BhpEvidenceValidator(root), FailingRepository(session)
                ).execute(_input(product_id, sds_id, "decision.pdf", BhpDecisionStatus.APPROVED))
            )
        with session_factory() as session:
            assert session.scalars(select(DecisionEvidenceModel)).all() == []
            assert session.scalars(select(BhpDecisionModel)).all() == []
            assert session.get(ProductModel, product_id).usage_status.value == "PENDING_APPROVAL"
            assert session.scalars(select(ProductHistoryModel)).all() == []
    finally:
        _cleanup(session_factory, manufacturer_id, product_id, (sds_id, archived_sds_id))


def test_failure_while_correcting_restores_previous_current(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    manufacturer_id, product_id, sds_id, archived_sds_id = _seed(session_factory)
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "first.pdf").write_bytes(b"first")
    (root / "second.pdf").write_bytes(b"second")
    executor = TransactionExecutor(session_factory)
    try:
        executor.execute(
            lambda session: RegisterBhpDecision(
                BhpEvidenceValidator(root), SqlAlchemyBhpDecisionRepository(session)
            ).execute(_input(product_id, sds_id, "first.pdf", BhpDecisionStatus.APPROVED))
        )

        class FailingRepository(SqlAlchemyBhpDecisionRepository):
            def _after_evidence_created(self) -> None:
                raise RuntimeError("correction failure")

        with pytest.raises(RuntimeError, match="correction"):
            executor.execute(
                lambda session: RegisterBhpDecision(
                    BhpEvidenceValidator(root), FailingRepository(session)
                ).execute(_input(product_id, sds_id, "second.pdf", BhpDecisionStatus.REJECTED))
            )
        with session_factory() as session:
            decision = session.scalar(select(BhpDecisionModel))
            assert decision is not None
            assert decision.record_status is DecisionRecordStatus.CURRENT
            assert decision.decision_status is BhpDecisionStatus.APPROVED
            assert len(session.scalars(select(DecisionEvidenceModel)).all()) == 1
            assert session.get(ProductModel, product_id).usage_status.value == "ACTIVE"
    finally:
        _cleanup(session_factory, manufacturer_id, product_id, (sds_id, archived_sds_id))


def test_sds_belonging_to_other_product_is_rejected(
    session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    manufacturer_id, product_id, sds_id, archived_sds_id = _seed(session_factory)
    other_product_id = f"task023-other-product-{uuid4().hex}"
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "decision.pdf").write_bytes(b"decision")
    try:
        with session_factory.begin() as session:
            session.add(
                ProductModel(
                    product_id=other_product_id,
                    product_name=f"TASK-023 Other Product {uuid4().hex}",
                    manufacturer_product_code="TASK023-OTHER",
                    manufacturer_id=manufacturer_id,
                    use_description="Other use",
                    use_restriction="Other restriction",
                    usage_status="PENDING_APPROVAL",
                )
            )
        with pytest.raises(ValueError, match="does not belong"):
            TransactionExecutor(session_factory).execute(
                lambda session: RegisterBhpDecision(
                    BhpEvidenceValidator(root), SqlAlchemyBhpDecisionRepository(session)
                ).execute(_input(other_product_id, sds_id, "decision.pdf", BhpDecisionStatus.APPROVED))
            )
        with session_factory() as session:
            assert session.scalars(select(BhpDecisionModel)).all() == []
            assert session.get(ProductModel, other_product_id).usage_status.value == "PENDING_APPROVAL"
    finally:
        with session_factory.begin() as session:
            session.execute(delete(ProductModel).where(ProductModel.product_id == other_product_id))
        _cleanup(session_factory, manufacturer_id, product_id, (sds_id, archived_sds_id))