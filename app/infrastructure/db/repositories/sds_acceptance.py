"""SQLAlchemy persistence for the atomic accepted-SDS workflow."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput
from app.application.ports import SdsAcceptanceRepositoryPort
from app.domain.enums import (
    FileAvailabilityStatus,
    ProductUsageStatus,
    SafetyInformationStatus,
    SdsDocumentStatus,
)
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    SafetyProfileModel,
    SdsComponentModel,
    SdsDocumentModel,
)


class SqlAlchemySdsAcceptanceRepository(SdsAcceptanceRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def accept(self, data: AcceptSdsInput) -> str:
        manufacturer = self._resolve_manufacturer(data.manufacturer_name)
        product = self._resolve_product(data, manufacturer.manufacturer_id)
        return self._persist_sds(product, data)

    def accept_revision(self, data: AddSdsRevisionInput) -> str:
        product = self._session.get(ProductModel, data.product_id)
        if product is None:
            raise ValueError("Selected product does not exist.")
        return self._persist_sds(product, data)

    def _persist_sds(
        self, product: ProductModel, data: AcceptSdsInput | AddSdsRevisionInput
    ) -> str:
        now = datetime.now(timezone.utc)
        self._session.execute(
            update(SdsDocumentModel)
            .where(
                SdsDocumentModel.product_id == product.product_id,
                SdsDocumentModel.document_status == SdsDocumentStatus.CURRENT,
            )
            .values(document_status=SdsDocumentStatus.ARCHIVED)
        )
        product.usage_status = ProductUsageStatus.PENDING_APPROVAL
        sds_id = uuid4().hex
        self._session.add(
            SdsDocumentModel(
                sds_id=sds_id,
                product_id=product.product_id,
                original_filename=Path(data.source_relative_path).name,
                relative_path=data.source_relative_path,
                issue_date=data.issue_date,
                revision=data.revision,
                document_status=SdsDocumentStatus.CURRENT,
                registered_at=now,
                file_status=FileAvailabilityStatus.AVAILABLE,
            )
        )
        self._session.add(self._profile_model(sds_id, data, now))
        self._session.add_all(
            SdsComponentModel(
                component_id=uuid4().hex,
                sds_id=sds_id,
                component_name=component.component_name,
                cas_number=component.cas_number,
                ec_number=component.ec_number,
                reach_registration_number=component.reach_registration_number,
                concentration_text=component.concentration_text,
                classification_text=component.classification_text,
                hazard_statements=component.hazard_statements,
            )
            for component in data.components
        )
        self._session.add(
            ProductHistoryModel(
                history_id=uuid4().hex,
                product_id=product.product_id,
                usage_status=product.usage_status,
                use_description=product.use_description,
                use_restriction=product.use_restriction,
                waste_type=product.waste_type,
                waste_code=product.waste_code,
                changed_at=now,
            )
        )
        self._session.flush()
        return sds_id

    def _resolve_manufacturer(self, name: str) -> ManufacturerModel:
        rows = self._session.scalars(
            select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == name)
        ).all()
        if len(rows) > 1:
            raise ValueError("Manufacturer identity is ambiguous.")
        if rows:
            return rows[0]
        manufacturer = ManufacturerModel(
            manufacturer_id=uuid4().hex, manufacturer_name=name
        )
        self._session.add(manufacturer)
        self._session.flush()
        return manufacturer

    def _resolve_product(self, data: AcceptSdsInput, manufacturer_id: str) -> ProductModel:
        product = self._session.scalar(
            select(ProductModel).where(
                ProductModel.product_name == data.product_name,
                ProductModel.manufacturer_product_code == data.manufacturer_product_code,
                ProductModel.manufacturer_id == manufacturer_id,
            )
        )
        if product is not None:
            product.use_description = data.use_description
            product.use_restriction = data.use_restriction
            return product
        product = ProductModel(
            product_id=uuid4().hex,
            product_name=data.product_name,
            manufacturer_product_code=data.manufacturer_product_code,
            manufacturer_id=manufacturer_id,
            use_description=data.use_description,
            use_restriction=data.use_restriction,
            usage_status=ProductUsageStatus.PENDING_APPROVAL,
        )
        self._session.add(product)
        self._session.flush()
        return product

    @staticmethod
    def _profile_model(
        sds_id: str,
        data: AcceptSdsInput | AddSdsRevisionInput,
        approved_at: datetime,
    ) -> SafetyProfileModel:
        profile = data.safety_profile
        no_data = SafetyInformationStatus.NO_DATA
        return SafetyProfileModel(
            sds_id=sds_id,
            product_definition=profile.product_definition,
            hazardous_classification_status=profile.hazardous_classification_status or no_data,
            clp_classification_text=profile.clp_classification_text,
            signal_word=profile.signal_word,
            hazard_statements=profile.hazard_statements,
            supplemental_hazard_statements=profile.supplemental_hazard_statements,
            pbt_status=profile.pbt_status or no_data,
            vpvb_status=profile.vpvb_status or no_data,
            carcinogenicity_status=profile.carcinogenicity_status or no_data,
            germ_cell_mutagenicity_status=profile.germ_cell_mutagenicity_status or no_data,
            reproductive_toxicity_status=profile.reproductive_toxicity_status or no_data,
            endocrine_section_2_status=profile.endocrine_section_2_status or no_data,
            endocrine_section_11_status=profile.endocrine_section_11_status or no_data,
            skin_sensitization_status=profile.skin_sensitization_status or no_data,
            respiratory_sensitization_status=profile.respiratory_sensitization_status or no_data,
            approved_at=approved_at,
            last_manual_edit_at=None,
        )
