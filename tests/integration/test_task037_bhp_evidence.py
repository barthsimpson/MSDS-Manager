"""TASK-037 evidence registration on an isolated PostgreSQL instance."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker, Session

from app.application.dto import NewBhpDecisionInput, RegisterBhpDecisionInput
from app.application.use_cases.bhp_evidence import ImportBhpEvidence
from app.application.use_cases.register_bhp_decision import RegisterBhpDecision
from app.domain.enums import (
    BhpDecisionStatus, DecisionRecordStatus, FileAvailabilityStatus, SdsDocumentStatus,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    BhpDecisionModel, DecisionEvidenceModel, ManufacturerModel, ProductHistoryModel,
    ProductModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.bhp_decision import SqlAlchemyBhpDecisionRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.db.transactions import TransactionExecutor
from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage
from app.presentation.streamlit.composition import ShellComposition


@pytest.fixture
def session_factory():
    engine = create_engine_from_settings(load_settings())
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def _seed(factory: sessionmaker[Session]) -> tuple[str, str]:
    suffix = uuid4().hex
    product_id = f"task037-product-{suffix}"
    sds_id = f"task037-sds-{suffix}"
    manufacturer_id = f"task037-manufacturer-{suffix}"
    with factory.begin() as session:
        session.add(ManufacturerModel(
            manufacturer_id=manufacturer_id,
            manufacturer_name=f"TASK-037 Manufacturer {suffix}",
        ))
        session.add(ProductModel(
            product_id=product_id, product_name=f"TASK-037 Product {suffix}",
            manufacturer_product_code="TASK037", manufacturer_id=manufacturer_id,
            use_description="Test", use_restriction="Test", usage_status="PENDING_APPROVAL",
        ))
        session.add(SdsDocumentModel(
            sds_id=sds_id, product_id=product_id,
            original_filename="source.pdf", relative_path="source.pdf",
            document_status=SdsDocumentStatus.CURRENT,
            registered_at=datetime.now(timezone.utc),
            file_status=FileAvailabilityStatus.AVAILABLE,
        ))
    return product_id, sds_id


@pytest.fixture
def scope_ids(session_factory):
    product_id, sds_id = _seed(session_factory)
    try:
        yield product_id, sds_id
    finally:
        with session_factory.begin() as session:
            product = session.get(ProductModel, product_id)
            evidence_ids = session.scalars(
                select(BhpDecisionModel.evidence_id).where(BhpDecisionModel.sds_id == sds_id)
            ).all()
            session.execute(delete(BhpDecisionModel).where(BhpDecisionModel.sds_id == sds_id))
            if evidence_ids:
                session.execute(delete(DecisionEvidenceModel).where(
                    DecisionEvidenceModel.evidence_id.in_(evidence_ids)
                ))
            session.execute(delete(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id))
            session.execute(delete(SdsDocumentModel).where(SdsDocumentModel.sds_id == sds_id))
            session.execute(delete(ProductModel).where(ProductModel.product_id == product_id))
            session.execute(delete(ManufacturerModel).where(
                ManufacturerModel.manufacturer_id == product.manufacturer_id
            ))


def _input(product_id: str, sds_id: str, filename: str, status: BhpDecisionStatus):
    return NewBhpDecisionInput(
        product_id=product_id, sds_id=sds_id,
        decision_status=status, original_filename=filename,
        content=f"contents of {filename}".encode(),
    )


def test_import_commit_correction_and_missing_history(session_factory, scope_ids, tmp_path: Path) -> None:
    product_id, sds_id = scope_ids
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    composition = ShellComposition(
        engine=session_factory.kw["bind"], session_factory=session_factory,
        products=(), sds_root_path=tmp_path, bhp_evidence_root_path=evidence_root,
    )
    first = composition.register_new_bhp_decision(
        _input(product_id, sds_id, "Original Approval.PDF", BhpDecisionStatus.APPROVED)
    )
    second = composition.register_new_bhp_decision(
        _input(product_id, sds_id, "Correction.MSG", BhpDecisionStatus.REJECTED)
    )
    assert first.evidence_relative_path != second.evidence_relative_path
    assert composition.read_bhp_evidence(first.evidence_relative_path) == b"contents of Original Approval.PDF"
    assert composition.read_bhp_evidence(second.evidence_relative_path) == b"contents of Correction.MSG"
    assert {item.original_filename for item in composition.list_bhp_evidence()} == {
        "Original Approval.PDF", "Correction.MSG"
    }
    with session_factory() as session:
        decisions = session.scalars(
            select(BhpDecisionModel).where(BhpDecisionModel.sds_id == sds_id)
            .order_by(BhpDecisionModel.registered_at)
        ).all()
        assert [item.record_status for item in decisions] == [
            DecisionRecordStatus.SUPERSEDED, DecisionRecordStatus.CURRENT
        ]
        assert [item.decision_status for item in decisions] == [
            BhpDecisionStatus.APPROVED, BhpDecisionStatus.REJECTED
        ]
        evidence = [session.get(DecisionEvidenceModel, item.evidence_id) for item in decisions]
        assert [item.original_filename for item in evidence] == [
            "Original Approval.PDF", "Correction.MSG"
        ]
        assert decisions[0].evidence_id != decisions[1].evidence_id
    (evidence_root / first.evidence_relative_path).unlink()  # Simulate external loss in isolated test data.
    assert not composition.bhp_evidence_available(first.evidence_relative_path)
    assert len(composition.list_bhp_decisions(sds_id)) == 2
    assert composition.get_current_bhp_decision(sds_id).decision_status is BhpDecisionStatus.REJECTED


def test_database_failure_rolls_back_and_compensates_file(session_factory, scope_ids, tmp_path: Path) -> None:
    product_id, sds_id = scope_ids
    root = tmp_path / "evidence"
    root.mkdir()
    storage = BhpEvidenceStorage(root)

    class FailingRepository(SqlAlchemyBhpDecisionRepository):
        def _after_evidence_created(self) -> None:
            raise RuntimeError("failure after evidence")

    def verify_scope(product_id: str, sds_id: str) -> None:
        with session_factory() as session:
            SqlAlchemyBhpDecisionRepository(session).verify_scope(product_id, sds_id)

    def register(data: RegisterBhpDecisionInput):
        return TransactionExecutor(session_factory).execute(
            lambda session: RegisterBhpDecision(storage, FailingRepository(session)).execute(data)
        )

    with pytest.raises(RuntimeError, match="failure after evidence"):
        ImportBhpEvidence(storage).execute(
            _input(product_id, sds_id, "Failed.pdf", BhpDecisionStatus.APPROVED),
            verify_scope, register,
        )
    assert list((root / "imported").iterdir()) == []
    with session_factory() as session:
        assert session.scalars(select(BhpDecisionModel).where(BhpDecisionModel.sds_id == sds_id)).all() == []
        assert session.scalars(select(DecisionEvidenceModel).where(
            DecisionEvidenceModel.relative_path.like("imported/%")
        )).all() == []


def test_filesystem_failure_creates_no_decision(session_factory, scope_ids, tmp_path: Path) -> None:
    product_id, sds_id = scope_ids
    class FailingStorage(BhpEvidenceStorage):
        def store_new_evidence(self, original_filename: str, content: bytes) -> str:
            raise OSError("write failed")
    storage = FailingStorage(tmp_path)
    with pytest.raises(OSError, match="write failed"):
        ImportBhpEvidence(storage).execute(
            _input(product_id, sds_id, "Failed.pdf", BhpDecisionStatus.APPROVED),
            lambda *_: None, lambda *_: pytest.fail("register must not run"),
        )
    with session_factory() as session:
        assert session.scalars(select(BhpDecisionModel).where(BhpDecisionModel.sds_id == sds_id)).all() == []
