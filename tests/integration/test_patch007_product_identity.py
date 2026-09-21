from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.application.dto import UpdateProductIdentityInput
from app.application.use_cases import UpdateProductIdentity
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SdsDocumentStatus,
    UsageLocationStatus,
)
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ManufacturerModel,
    ProductModel,
    ProductUsageLocationModel,
    SdsDocumentModel,
    UsageLocationModel,
)
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.config import load_settings


def test_product_identity_edit_preserves_sds_bhp_and_usage() -> None:
    engine = create_engine_from_settings(load_settings())
    session_factory = create_session_factory(engine)
    suffix = uuid4().hex
    old_manufacturer_id = f"patch007-old-manufacturer-{suffix}"
    new_manufacturer_id = f"patch007-new-manufacturer-{suffix}"
    product_id = f"patch007-product-{suffix}"
    sds_id = f"patch007-sds-{suffix}"
    location_id = f"patch007-location-{suffix}"
    evidence_id = f"patch007-evidence-{suffix}"
    decision_id = f"patch007-decision-{suffix}"
    now = datetime.now(timezone.utc)

    try:
        with session_factory() as session:
            transaction = session.begin()
            session.add_all(
                [
                    ManufacturerModel(
                        manufacturer_id=old_manufacturer_id,
                        manufacturer_name=f"PATCH-007 Old {suffix}",
                    ),
                    ManufacturerModel(
                        manufacturer_id=new_manufacturer_id,
                        manufacturer_name=f"PATCH-007 New {suffix}",
                    ),
                    ProductModel(
                        product_id=product_id,
                        product_name="Old product",
                        manufacturer_product_code="OLD-1",
                        manufacturer_id=old_manufacturer_id,
                        use_description="Use",
                        use_restriction="Restriction",
                        usage_status=ProductUsageStatus.ACTIVE,
                    ),
                    SdsDocumentModel(
                        sds_id=sds_id,
                        product_id=product_id,
                        original_filename="old.pdf",
                        relative_path="old.pdf",
                        document_status=SdsDocumentStatus.CURRENT,
                        registered_at=now,
                        file_status=FileAvailabilityStatus.AVAILABLE,
                    ),
                    UsageLocationModel(
                        location_id=location_id,
                        location_name="PATCH-007 Location",
                        status=UsageLocationStatus.ACTIVE,
                    ),
                    ProductUsageLocationModel(
                        product_id=product_id,
                        location_id=location_id,
                        peak_quantity_value=Decimal("25"),
                        peak_quantity_unit="l",
                        monthly_consumption_value=Decimal("300"),
                        monthly_consumption_unit="l/month",
                    ),
                    DecisionEvidenceModel(
                        evidence_id=evidence_id,
                        relative_path="patch007/evidence.pdf",
                        evidence_type=EvidenceType.DOCUMENT,
                        file_format=EvidenceFileFormat.PDF,
                        file_status=FileAvailabilityStatus.AVAILABLE,
                    ),
                    BhpDecisionModel(
                        decision_id=decision_id,
                        product_id=product_id,
                        sds_id=sds_id,
                        decision_status=BhpDecisionStatus.APPROVED,
                        notes="approved",
                        registered_at=now,
                        record_status=DecisionRecordStatus.CURRENT,
                        evidence_id=evidence_id,
                    ),
                ]
            )
            session.flush()

            UpdateProductIdentity(SqlAlchemyProductRepository(session)).execute(
                UpdateProductIdentityInput(
                    product_id=product_id,
                    product_name="Edited product",
                    manufacturer_product_code="NEW-1",
                    manufacturer_name=f"PATCH-007 New {suffix}",
                )
            )
            session.flush()

            product = session.get(ProductModel, product_id)
            assert product is not None
            assert product.product_id == product_id
            assert product.product_name == "Edited product"
            assert product.manufacturer_product_code == "NEW-1"
            assert product.manufacturer_id == new_manufacturer_id
            assert product.usage_status is ProductUsageStatus.ACTIVE
            assert session.scalars(
                select(SdsDocumentModel).where(SdsDocumentModel.product_id == product_id)
            ).all() == [session.get(SdsDocumentModel, sds_id)]
            assignment = session.get(ProductUsageLocationModel, (product_id, location_id))
            assert assignment is not None
            assert assignment.peak_quantity_value == Decimal("25")
            assert assignment.monthly_consumption_value == Decimal("300")
            decision = session.get(BhpDecisionModel, decision_id)
            assert decision is not None
            assert decision.sds_id == sds_id
            assert session.scalars(
                select(ManufacturerModel).where(
                    ManufacturerModel.manufacturer_name == f"PATCH-007 New {suffix}"
                )
            ).all() == [session.get(ManufacturerModel, new_manufacturer_id)]
            transaction.rollback()
    finally:
        engine.dispose()
