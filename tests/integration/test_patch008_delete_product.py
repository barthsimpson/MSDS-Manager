from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.application.use_cases import DeleteProduct
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SdsDocumentStatus,
    SafetyInformationStatus,
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
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory


def test_delete_product_removes_owned_records_and_preserves_shared_data() -> None:
    settings = load_settings()
    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    suffix = uuid4().hex
    manufacturer_id = f"patch008-manufacturer-{suffix}"
    product_id = f"patch008-delete-product-{suffix}"
    other_product_id = f"patch008-other-product-{suffix}"
    location_id = f"patch008-location-{suffix}"
    sds_id = f"patch008-sds-{suffix}"
    component_id = f"patch008-component-{suffix}"
    evidence_id = f"patch008-evidence-{suffix}"
    decision_id = f"patch008-decision-{suffix}"
    source_name = "Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf"
    evidence_name = "Zrzut ekranu 2026-09-21 093145.png"
    now = datetime.now(timezone.utc)

    try:
        with session_factory.begin() as session:
            session.add_all(
                [
                    ManufacturerModel(
                        manufacturer_id=manufacturer_id,
                        manufacturer_name=f"PATCH-008 Manufacturer {suffix}",
                    ),
                    ProductModel(
                        product_id=product_id,
                        product_name=f"PATCH-008 Delete {suffix}",
                        manufacturer_product_code="DELETE-1",
                        manufacturer_id=manufacturer_id,
                        use_description="Use",
                        use_restriction="Restriction",
                        usage_status=ProductUsageStatus.ACTIVE,
                    ),
                    ProductModel(
                        product_id=other_product_id,
                        product_name=f"PATCH-008 Other {suffix}",
                        manufacturer_product_code="OTHER-1",
                        manufacturer_id=manufacturer_id,
                        use_description="Use",
                        use_restriction="Restriction",
                        usage_status=ProductUsageStatus.ACTIVE,
                    ),
                    SdsDocumentModel(
                        sds_id=sds_id,
                        product_id=product_id,
                        original_filename=source_name,
                        relative_path=source_name,
                        document_status=SdsDocumentStatus.CURRENT,
                        registered_at=now,
                        file_status=FileAvailabilityStatus.AVAILABLE,
                    ),
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
                        approved_at=now,
                    ),
                    SdsComponentModel(
                        component_id=component_id,
                        sds_id=sds_id,
                        component_name="Owned component",
                        hazard_statements=[],
                    ),
                    UsageLocationModel(
                        location_id=location_id,
                        location_name="Shared location",
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
                    ProductUsageLocationModel(
                        product_id=other_product_id,
                        location_id=location_id,
                        peak_quantity_value=Decimal("5"),
                        peak_quantity_unit="l",
                        monthly_consumption_value=None,
                        monthly_consumption_unit=None,
                    ),
                    DecisionEvidenceModel(
                        evidence_id=evidence_id,
                        relative_path=f"patch008/{evidence_name}",
                        evidence_type=EvidenceType.PHOTO_SCAN,
                        file_format=EvidenceFileFormat.PNG,
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
            session.add(
                ProductHistoryModel(
                    history_id=f"patch008-history-{suffix}",
                    product_id=product_id,
                    usage_status=ProductUsageStatus.ACTIVE,
                    use_description="Use",
                    use_restriction="Restriction",
                    changed_at=now,
                )
            )

        TransactionExecutor(session_factory).execute(
            lambda session: DeleteProduct(
                SqlAlchemyProductRepository(session)
            ).execute(product_id)
        )

        with session_factory() as session:
            assert session.get(ProductModel, product_id) is None
            assert session.get(SdsDocumentModel, sds_id) is None
            assert session.get(SafetyProfileModel, sds_id) is None
            assert session.get(SdsComponentModel, component_id) is None
            assert session.get(BhpDecisionModel, decision_id) is None
            assert session.get(DecisionEvidenceModel, evidence_id) is None
            assert session.get(ProductUsageLocationModel, (product_id, location_id)) is None
            assert session.get(ProductHistoryModel, f"patch008-history-{suffix}") is None
            assert session.get(ProductModel, other_product_id) is not None
            assert session.get(ManufacturerModel, manufacturer_id) is not None
            assert session.get(UsageLocationModel, location_id) is not None
            assert session.get(ProductUsageLocationModel, (other_product_id, location_id)) is not None
            assert (settings.sds_root_path / source_name).is_file()
            assert (settings.bhp_evidence_root_path / evidence_name).is_file()
    finally:
        with session_factory.begin() as session:
            session.execute(delete(BhpDecisionModel).where(BhpDecisionModel.product_id.in_([product_id, other_product_id])))
            session.execute(delete(DecisionEvidenceModel).where(DecisionEvidenceModel.evidence_id == evidence_id))
            session.execute(delete(SdsComponentModel).where(SdsComponentModel.sds_id == sds_id))
            session.execute(delete(SafetyProfileModel).where(SafetyProfileModel.sds_id == sds_id))
            session.execute(delete(SdsDocumentModel).where(SdsDocumentModel.sds_id == sds_id))
            session.execute(delete(ProductUsageLocationHistoryModel).where(ProductUsageLocationHistoryModel.product_id.in_([product_id, other_product_id])))
            session.execute(delete(ProductUsageLocationModel).where(ProductUsageLocationModel.product_id.in_([product_id, other_product_id])))
            session.execute(delete(ProductHistoryModel).where(ProductHistoryModel.product_id.in_([product_id, other_product_id])))
            session.execute(delete(UsageLocationHistoryModel).where(UsageLocationHistoryModel.location_id == location_id))
            session.execute(delete(ProductModel).where(ProductModel.product_id.in_([product_id, other_product_id])))
            session.execute(delete(UsageLocationModel).where(UsageLocationModel.location_id == location_id))
            session.execute(delete(ManufacturerModel).where(ManufacturerModel.manufacturer_id == manufacturer_id))
        engine.dispose()


def test_delete_product_rolls_back_after_repository_failure() -> None:
    engine = create_engine_from_settings(load_settings())
    session_factory = create_session_factory(engine)
    suffix = uuid4().hex
    manufacturer_id = f"patch008-rollback-manufacturer-{suffix}"
    product_id = f"patch008-rollback-product-{suffix}"

    class FailingRepository(SqlAlchemyProductRepository):
        def delete_product(self, selected_id: str) -> bool:
            result = super().delete_product(selected_id)
            raise RuntimeError("controlled delete failure")

    try:
        with session_factory.begin() as session:
            session.add(
                ManufacturerModel(
                    manufacturer_id=manufacturer_id,
                    manufacturer_name=f"PATCH-008 Rollback {suffix}",
                )
            )
            session.add(
                ProductModel(
                    product_id=product_id,
                    product_name="Rollback product",
                    manufacturer_product_code="ROLLBACK-1",
                    manufacturer_id=manufacturer_id,
                    use_description="Use",
                    use_restriction="Restriction",
                    usage_status=ProductUsageStatus.PENDING_APPROVAL,
                )
            )

        with pytest.raises(RuntimeError):
            TransactionExecutor(session_factory).execute(
                lambda session: DeleteProduct(FailingRepository(session)).execute(product_id)
            )
        with session_factory() as session:
            assert session.get(ProductModel, product_id) is not None
    finally:
        with session_factory.begin() as session:
            session.execute(delete(ProductModel).where(ProductModel.product_id == product_id))
            session.execute(delete(ManufacturerModel).where(ManufacturerModel.manufacturer_id == manufacturer_id))
        engine.dispose()
