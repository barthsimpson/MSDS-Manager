from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import AddSdsRevisionInput
from app.application.use_cases import AddSdsRevision
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SafetyInformationStatus,
    SdsDocumentStatus,
    UsageLocationStatus,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db import TransactionExecutor
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    ProductUsageLocationHistoryModel,
    ProductUsageLocationModel,
    SafetyProfileModel,
    SdsComponentModel,
    SdsDocumentModel,
    UsageLocationHistoryModel,
    UsageLocationModel,
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


def test_add_revision_preserves_product_usage_and_previous_bhp(
    session_factory: sessionmaker[Session],
) -> None:
    settings = load_settings()
    suffix = uuid4().hex
    manufacturer_id = f"patch006-manufacturer-{suffix}"
    product_id = f"patch006-product-{suffix}"
    location_id = f"patch006-location-{suffix}"
    sds_id = f"patch006-sds-{suffix}"
    evidence_id = f"patch006-evidence-{suffix}"
    decision_id = f"patch006-decision-{suffix}"
    product_name = f"PATCH-006 Product {suffix}"
    registered_at = datetime.now(timezone.utc)
    source = "Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf"
    revision_source = "CX 80 XBAKE CLEANER rew. 01-08-2015.pdf"

    try:
        with session_factory.begin() as session:
            session.add(ManufacturerModel(manufacturer_id=manufacturer_id, manufacturer_name=f"PATCH-006 Manufacturer {suffix}"))
            session.add(
                ProductModel(
                    product_id=product_id,
                    product_name=product_name,
                    manufacturer_product_code="PATCH-006",
                    manufacturer_id=manufacturer_id,
                    use_description="Industrial use",
                    use_restriction="Professional use",
                    usage_status=ProductUsageStatus.ACTIVE,
                )
            )
            session.add(
                SdsDocumentModel(
                    sds_id=sds_id,
                    product_id=product_id,
                    original_filename=source,
                    relative_path=source,
                    document_status=SdsDocumentStatus.CURRENT,
                    registered_at=registered_at,
                    file_status=FileAvailabilityStatus.AVAILABLE,
                )
            )
            session.add(
                SafetyProfileModel(
                    sds_id=sds_id,
                    hazardous_classification_status=SafetyInformationStatus.NO_DATA,
                    pbt_status=SafetyInformationStatus.NO_DATA,
                    vpvb_status=SafetyInformationStatus.NO_DATA,
                    carcinogenicity_status=SafetyInformationStatus.NO_DATA,
                    germ_cell_mutagenicity_status=SafetyInformationStatus.NO_DATA,
                    reproductive_toxicity_status=SafetyInformationStatus.NO_DATA,
                    endocrine_section_2_status=SafetyInformationStatus.NO_DATA,
                    endocrine_section_11_status=SafetyInformationStatus.NO_DATA,
                    skin_sensitization_status=SafetyInformationStatus.NO_DATA,
                    respiratory_sensitization_status=SafetyInformationStatus.NO_DATA,
                    hazard_statements=[],
                    supplemental_hazard_statements=[],
                    approved_at=registered_at,
                )
            )
            session.add(
                UsageLocationModel(
                    location_id=location_id,
                    location_name="PATCH-006 Location",
                    status=UsageLocationStatus.ACTIVE,
                )
            )
            session.add(
                ProductUsageLocationModel(
                    product_id=product_id,
                    location_id=location_id,
                    peak_quantity_value=Decimal("25"),
                    peak_quantity_unit="l",
                    monthly_consumption_value=Decimal("300"),
                    monthly_consumption_unit="l/month",
                )
            )
            session.add(
                DecisionEvidenceModel(
                    evidence_id=evidence_id,
                    relative_path="patch006/decision.pdf",
                    evidence_type=EvidenceType.DOCUMENT,
                    file_format=EvidenceFileFormat.PDF,
                    file_status=FileAvailabilityStatus.AVAILABLE,
                )
            )
            session.add(
                BhpDecisionModel(
                    decision_id=decision_id,
                    product_id=product_id,
                    sds_id=sds_id,
                    decision_status=BhpDecisionStatus.APPROVED,
                    notes="approved old revision",
                    registered_at=registered_at,
                    record_status=DecisionRecordStatus.CURRENT,
                    evidence_id=evidence_id,
                )
            )

        new_sds_id = TransactionExecutor(session_factory).execute(
            lambda session: AddSdsRevision(
                SqlAlchemySdsAcceptanceRepository(session),
                SdsFileValidator(settings.sds_root_path),
            ).execute(
                AddSdsRevisionInput(
                    product_id=product_id,
                    source_relative_path=revision_source,
                    revision="2.0",
                )
            )
        )

        with session_factory() as session:
            product = session.get(ProductModel, product_id)
            assert product is not None
            assert product.usage_status is ProductUsageStatus.PENDING_APPROVAL
            assert len(session.scalars(select(ProductModel).where(ProductModel.product_id == product_id)).all()) == 1
            documents = session.scalars(
                select(SdsDocumentModel).where(SdsDocumentModel.product_id == product_id)
            ).all()
            assert session.get(SdsDocumentModel, sds_id).document_status is SdsDocumentStatus.ARCHIVED
            assert session.get(SdsDocumentModel, new_sds_id).document_status is SdsDocumentStatus.CURRENT
            assert sum(document.document_status is SdsDocumentStatus.CURRENT for document in documents) == 1
            assignment = session.get(ProductUsageLocationModel, (product_id, location_id))
            assert assignment is not None
            assert assignment.peak_quantity_value == Decimal("25")
            assert assignment.monthly_consumption_value == Decimal("300")
            decisions = session.scalars(
                select(BhpDecisionModel).where(BhpDecisionModel.product_id == product_id)
            ).all()
            assert [(decision.sds_id, decision.evidence_id) for decision in decisions] == [
                (sds_id, evidence_id)
            ]
            assert session.scalars(
                select(BhpDecisionModel).where(BhpDecisionModel.sds_id == new_sds_id)
            ).all() == []
    finally:
        with session_factory.begin() as session:
            session.execute(delete(BhpDecisionModel).where(BhpDecisionModel.product_id == product_id))
            session.execute(delete(DecisionEvidenceModel).where(DecisionEvidenceModel.evidence_id == evidence_id))
            sds_ids = session.scalars(select(SdsDocumentModel.sds_id).where(SdsDocumentModel.product_id == product_id)).all()
            if sds_ids:
                session.execute(delete(SdsComponentModel).where(SdsComponentModel.sds_id.in_(sds_ids)))
                session.execute(delete(SafetyProfileModel).where(SafetyProfileModel.sds_id.in_(sds_ids)))
                session.execute(delete(SdsDocumentModel).where(SdsDocumentModel.sds_id.in_(sds_ids)))
            session.execute(delete(ProductUsageLocationHistoryModel).where(ProductUsageLocationHistoryModel.product_id == product_id))
            session.execute(delete(ProductUsageLocationModel).where(ProductUsageLocationModel.product_id == product_id))
            session.execute(delete(ProductHistoryModel).where(ProductHistoryModel.product_id == product_id))
            session.execute(delete(UsageLocationHistoryModel).where(UsageLocationHistoryModel.location_id == location_id))
            session.execute(delete(UsageLocationModel).where(UsageLocationModel.location_id == location_id))
            session.execute(delete(ProductModel).where(ProductModel.product_id == product_id))
            session.execute(delete(ManufacturerModel).where(ManufacturerModel.manufacturer_id == manufacturer_id))
