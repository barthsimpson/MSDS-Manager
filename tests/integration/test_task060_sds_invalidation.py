"""Isolated in-memory transaction tests; never connect to the operator database."""

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import InvalidateSdsInput, RegisterBhpDecisionInput
from app.application.use_cases import InvalidateSds, RegisterBhpDecision
from app.domain.enums import (
    BhpDecisionStatus, DecisionRecordStatus, EvidenceFileFormat, EvidenceType,
    FileAvailabilityStatus, ProductUsageStatus, SafetyInformationStatus,
    SdsDocumentStatus,
)
from app.infrastructure.db.models import (
    Base, BhpDecisionModel, DecisionEvidenceModel, ManufacturerModel,
    ProductHistoryModel, ProductModel, SafetyProfileModel, SdsComponentModel,
    SdsDocumentModel, SdsInvalidationModel,
)
from app.infrastructure.db.repositories import (
    SqlAlchemyBhpDecisionRepository, SqlAlchemyBhpDecisionQuery,
    SqlAlchemySdsInvalidationRepository,
)
from app.infrastructure.db.transactions import TransactionExecutor


@compiles(ARRAY, "sqlite")
def _sqlite_array(_type, _compiler, **_kwargs):
    return "TEXT"


@pytest.fixture
def factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table, index_name, predicate in (
        (SdsDocumentModel.__table__, "uq_sds_documents_one_current_per_product", "document_status = 'CURRENT'"),
        (BhpDecisionModel.__table__, "uq_bhp_decisions_one_current_per_sds", "record_status = 'CURRENT'"),
    ):
        next(index for index in table.indexes if index.name == index_name).dialect_options["sqlite"]["where"] = text(predicate)
    @event.listens_for(engine, "connect")
    def _sqlite_functions(connection, _):
        connection.create_function("btrim", 1, lambda value: value.strip())
        connection.execute("PRAGMA foreign_keys=ON")
    @event.listens_for(engine, "before_cursor_execute", retval=True)
    def _adapt_arrays(_connection, _cursor, statement, parameters, _context, executemany):
        def adapt(row):
            return tuple(json.dumps(value) if isinstance(value, list) else value for value in row)
        if isinstance(parameters, tuple):
            parameters = adapt(parameters)
        elif isinstance(parameters, list):
            parameters = [adapt(row) for row in parameters]
        return statement, parameters
    Base.metadata.create_all(engine, tables=[
        ManufacturerModel.__table__, ProductModel.__table__, SdsDocumentModel.__table__,
        DecisionEvidenceModel.__table__, BhpDecisionModel.__table__,
        SafetyProfileModel.__table__, SdsComponentModel.__table__,
        ProductHistoryModel.__table__, SdsInvalidationModel.__table__,
    ])
    result = sessionmaker(bind=engine, expire_on_commit=False)
    yield result
    engine.dispose()


def _seed(factory, *, with_decisions=False, with_safety=False):
    manufacturer_id, product_id, a_id, b_id = (uuid4().hex for _ in range(4))
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add(ManufacturerModel(manufacturer_id=manufacturer_id, manufacturer_name="TASK060"))
        session.add(ProductModel(
            product_id=product_id, product_name="Task 060 product",
            manufacturer_id=manufacturer_id, manufacturer_product_code=None,
            use_description="Use", use_restriction="Restriction",
            usage_status=ProductUsageStatus.ACTIVE,
        ))
        for sds_id, status in ((a_id, SdsDocumentStatus.ARCHIVED), (b_id, SdsDocumentStatus.CURRENT)):
            session.add(SdsDocumentModel(
                sds_id=sds_id, product_id=product_id, original_filename=f"{sds_id}.pdf",
                relative_path=f"{sds_id}.pdf", document_status=status,
                registered_at=now, file_status=FileAvailabilityStatus.AVAILABLE,
            ))
            if with_safety:
                session.add(SafetyProfileModel(
                    sds_id=sds_id, hazardous_classification_status=SafetyInformationStatus.NO_DATA,
                    pbt_status=SafetyInformationStatus.NO_DATA,
                    vpvb_status=SafetyInformationStatus.NO_DATA,
                    carcinogenicity_status=SafetyInformationStatus.NO_DATA,
                    germ_cell_mutagenicity_status=SafetyInformationStatus.NO_DATA,
                    reproductive_toxicity_status=SafetyInformationStatus.NO_DATA,
                    endocrine_section_2_status=SafetyInformationStatus.NO_DATA,
                    endocrine_section_11_status=SafetyInformationStatus.NO_DATA,
                    skin_sensitization_status=SafetyInformationStatus.NO_DATA,
                    respiratory_sensitization_status=SafetyInformationStatus.NO_DATA,
                    hazard_statements=[], supplemental_hazard_statements=[], approved_at=now,
                ))
            if with_decisions:
                evidence_id, decision_id = uuid4().hex, uuid4().hex
                session.add(DecisionEvidenceModel(
                    evidence_id=evidence_id, relative_path=f"{sds_id}-evidence.pdf",
                    evidence_type=EvidenceType.DOCUMENT, file_format=EvidenceFileFormat.PDF,
                    file_status=FileAvailabilityStatus.AVAILABLE,
                ))
                session.add(BhpDecisionModel(
                    decision_id=decision_id, product_id=product_id, sds_id=sds_id,
                    decision_status=BhpDecisionStatus.APPROVED, registered_at=now,
                    record_status=DecisionRecordStatus.CURRENT, evidence_id=evidence_id,
                ))
        session.add(SdsComponentModel(
            component_id=uuid4().hex, sds_id=b_id, component_name="Component",
            hazard_statements=[],
        ))
    return product_id, a_id, b_id


def _run(factory, product_id, target_id, status, current_id, mode, *, restored_id=None, reason="Bad registration"):
    return TransactionExecutor(factory).execute(lambda session: InvalidateSds(
        SqlAlchemySdsInvalidationRepository(session)
    ).execute(InvalidateSdsInput(
        product_id=product_id, invalidated_sds_id=target_id,
        expected_status=status, expected_current_sds_id=current_id,
        mode=mode, restored_sds_id=restored_id, reason=reason,
    )))


def test_archived_invalidation_keeps_current_product_and_bhp(factory):
    product_id, a_id, b_id = _seed(factory, with_decisions=True)
    _run(factory, product_id, a_id, SdsDocumentStatus.ARCHIVED, b_id, "ARCHIVED_ONLY")
    with factory() as session:
        assert session.get(SdsDocumentModel, a_id).document_status is SdsDocumentStatus.INVALIDATED
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.CURRENT
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.ACTIVE
        assert session.scalar(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id)) is None
        assert session.scalar(select(BhpDecisionModel.record_status).where(BhpDecisionModel.sds_id == b_id)) is DecisionRecordStatus.CURRENT
        assert session.scalar(select(BhpDecisionModel.record_status).where(BhpDecisionModel.sds_id == a_id)) is DecisionRecordStatus.CURRENT
        assert SqlAlchemyBhpDecisionQuery(session).get_current_decision(a_id) is None
        audit = session.scalar(select(SdsInvalidationModel))
        assert (audit.invalidated_from_status, audit.restored_sds_id, audit.reason) == ("ARCHIVED", None, "Bad registration")


def test_no_current_preserves_related_data_and_writes_audit(factory, tmp_path: Path):
    product_id, a_id, b_id = _seed(factory, with_decisions=True, with_safety=True)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4\nfixture")
    before = pdf.read_bytes()
    _run(factory, product_id, b_id, SdsDocumentStatus.CURRENT, b_id, "NO_CURRENT", reason="  Wrong SDS  ")
    with factory() as session:
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.INVALIDATED
        assert not session.scalars(select(SdsDocumentModel).where(SdsDocumentModel.document_status == SdsDocumentStatus.CURRENT)).all()
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.PENDING_APPROVAL
        assert session.scalar(select(ProductHistoryModel.usage_status)) is ProductUsageStatus.PENDING_APPROVAL
        assert session.scalar(select(BhpDecisionModel.record_status).where(BhpDecisionModel.sds_id == b_id)) is DecisionRecordStatus.SUPERSEDED
        assert session.get(SafetyProfileModel, b_id) is not None
        assert session.scalar(select(SdsComponentModel).where(SdsComponentModel.sds_id == b_id)) is not None
        assert session.scalar(select(DecisionEvidenceModel)) is not None
        assert session.get(SdsDocumentModel, b_id).relative_path == f"{b_id}.pdf"
        audit = session.scalar(select(SdsInvalidationModel))
        assert (audit.invalidated_from_status, audit.restored_sds_id, audit.reason) == ("CURRENT", None, "Wrong SDS")
    assert pdf.read_bytes() == before


def test_restore_supersedes_old_decisions_then_existing_register_works(factory):
    product_id, a_id, b_id = _seed(factory, with_decisions=True, with_safety=True)
    _run(factory, product_id, b_id, SdsDocumentStatus.CURRENT, b_id, "RESTORE_ARCHIVED", restored_id=a_id)
    with factory() as session:
        assert session.get(SdsDocumentModel, a_id).document_status is SdsDocumentStatus.CURRENT
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.INVALIDATED
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.PENDING_APPROVAL
        assert SqlAlchemyBhpDecisionQuery(session).get_current_decision(a_id) is None
        assert session.scalars(select(BhpDecisionModel.record_status).where(BhpDecisionModel.product_id == product_id)).all() == [DecisionRecordStatus.SUPERSEDED] * 2
        assert session.scalar(select(SdsInvalidationModel.restored_sds_id)) == a_id
        assert len(session.scalars(select(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id)).all()) == 1

    class Validator:
        def validate(self, path):
            return path

    new = TransactionExecutor(factory).execute(lambda session: RegisterBhpDecision(
        Validator(), SqlAlchemyBhpDecisionRepository(session)
    ).execute(RegisterBhpDecisionInput(
        product_id=product_id, sds_id=a_id, decision_status=BhpDecisionStatus.REJECTED,
        evidence_relative_path="new-evidence.pdf", original_filename="new-evidence.pdf",
    )))
    with factory() as session:
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.REJECTED
        decisions = session.scalars(select(BhpDecisionModel).where(BhpDecisionModel.sds_id == a_id)).all()
        assert len(decisions) == 2
        assert {item.record_status for item in decisions} == {DecisionRecordStatus.CURRENT, DecisionRecordStatus.SUPERSEDED}
        assert new.decision_id in {item.decision_id for item in decisions}


def test_invalid_inputs_and_stale_state_leave_database_unchanged(factory):
    product_id, a_id, b_id = _seed(factory)
    invalid = (
        (a_id, SdsDocumentStatus.ARCHIVED, b_id, "ARCHIVED_ONLY", None, "   "),
        (b_id, SdsDocumentStatus.CURRENT, b_id, "RESTORE_ARCHIVED", None, "reason"),
        (b_id, SdsDocumentStatus.CURRENT, a_id, "NO_CURRENT", None, "reason"),
        (b_id, SdsDocumentStatus.CURRENT, b_id, "RESTORE_ARCHIVED", b_id, "reason"),
        (a_id, SdsDocumentStatus.ARCHIVED, None, "ARCHIVED_ONLY", None, "reason"),
    )
    for target, status, current, mode, restored, reason in invalid:
        with pytest.raises(ValueError):
            _run(factory, product_id, target, status, current, mode, restored_id=restored, reason=reason)
    with factory() as session:
        assert session.get(SdsDocumentModel, a_id).document_status is SdsDocumentStatus.ARCHIVED
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.CURRENT
        assert session.scalar(select(SdsInvalidationModel)) is None
    _run(factory, product_id, a_id, SdsDocumentStatus.ARCHIVED, b_id, "ARCHIVED_ONLY")
    with pytest.raises(ValueError):
        _run(factory, product_id, a_id, SdsDocumentStatus.ARCHIVED, b_id, "ARCHIVED_ONLY")
    with factory() as session:
        assert len(session.scalars(select(SdsInvalidationModel)).all()) == 1


def test_replacement_from_another_product_is_rejected(factory):
    product_id, _, b_id = _seed(factory)
    _, foreign_sds_id, _ = _seed(factory)
    with pytest.raises(ValueError, match="ARCHIVED"):
        _run(factory, product_id, b_id, SdsDocumentStatus.CURRENT, b_id,
             "RESTORE_ARCHIVED", restored_id=foreign_sds_id)
    with factory() as session:
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.CURRENT
        assert session.scalar(select(SdsInvalidationModel)) is None


def test_audit_failure_rolls_back_every_change(factory):
    product_id, a_id, b_id = _seed(factory, with_decisions=True)
    @event.listens_for(Session, "before_flush")
    def fail_audit(session, *_):
        if any(isinstance(item, SdsInvalidationModel) for item in session.new):
            raise RuntimeError("audit failure")
    try:
        with pytest.raises(RuntimeError, match="audit failure"):
            _run(factory, product_id, b_id, SdsDocumentStatus.CURRENT, b_id,
                 "RESTORE_ARCHIVED", restored_id=a_id)
    finally:
        event.remove(Session, "before_flush", fail_audit)
    with factory() as session:
        assert session.get(SdsDocumentModel, a_id).document_status is SdsDocumentStatus.ARCHIVED
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.CURRENT
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.ACTIVE
        assert session.scalar(select(BhpDecisionModel.record_status).where(BhpDecisionModel.sds_id == b_id)) is DecisionRecordStatus.CURRENT
        assert session.scalar(select(ProductHistoryModel)) is None
        assert session.scalar(select(SdsInvalidationModel)) is None


def test_history_failure_rolls_back_every_change(factory):
    product_id, a_id, b_id = _seed(factory, with_decisions=True)
    @event.listens_for(Session, "before_flush")
    def fail_history(session, *_):
        if any(isinstance(item, ProductHistoryModel) for item in session.new):
            raise RuntimeError("history failure")
    try:
        with pytest.raises(RuntimeError, match="history failure"):
            _run(factory, product_id, b_id, SdsDocumentStatus.CURRENT, b_id,
                 "RESTORE_ARCHIVED", restored_id=a_id)
    finally:
        event.remove(Session, "before_flush", fail_history)
    with factory() as session:
        assert session.get(SdsDocumentModel, a_id).document_status is SdsDocumentStatus.ARCHIVED
        assert session.get(SdsDocumentModel, b_id).document_status is SdsDocumentStatus.CURRENT
        assert session.get(ProductModel, product_id).usage_status is ProductUsageStatus.ACTIVE
        assert session.scalar(select(SdsInvalidationModel)) is None
