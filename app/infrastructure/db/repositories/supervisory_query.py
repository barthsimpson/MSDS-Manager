"""Read current Core facts in two bounded queries, without ORM side effects."""

from collections import defaultdict

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.application.dto import SupervisoryProductRow
from app.application.exceptions import SupervisoryReadError
from app.application.ports import SupervisoryQueryPort
from app.domain.enums import DecisionRecordStatus, SdsDocumentStatus, UsageLocationStatus
from app.infrastructure.config import Settings
from app.infrastructure.filesystem.file_availability import source_file_available
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ManufacturerModel,
    ProductModel,
    ProductUsageLocationModel,
    SdsDocumentModel,
    UsageLocationModel,
)


class SqlAlchemySupervisoryQuery(SupervisoryQueryPort):
    def __init__(self, session: Session, *, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def list_products(self) -> list[SupervisoryProductRow]:
        # A read must not flush unrelated pending changes in a shared session.
        with self._session.no_autoflush:
            return self._list_products()

    def _list_products(self) -> list[SupervisoryProductRow]:
        rows = self._session.execute(
            select(
                ProductModel.product_id,
                ProductModel.product_name,
                ManufacturerModel.manufacturer_name,
                ProductModel.manufacturer_product_code,
                ProductModel.usage_status,
                ProductModel.use_description,
                ProductModel.use_restriction,
                SdsDocumentModel.sds_id.label("current_sds_id"),
                SdsDocumentModel.original_filename.label("current_sds_filename"),
                SdsDocumentModel.issue_date.label("current_sds_issue_date"),
                SdsDocumentModel.revision.label("current_sds_revision"),
                SdsDocumentModel.relative_path.label("sds_relative_path"),
                BhpDecisionModel.decision_id.label("current_bhp_decision_id"),
                BhpDecisionModel.decision_status.label("current_bhp_decision_status"),
                BhpDecisionModel.registered_at.label("current_bhp_registered_at"),
                BhpDecisionModel.notes.label("current_bhp_notes"),
                DecisionEvidenceModel.relative_path.label(
                    "current_bhp_evidence_relative_path"
                ),
            )
            .select_from(ProductModel)
            .join(ManufacturerModel,
                  ProductModel.manufacturer_id == ManufacturerModel.manufacturer_id)
            .outerjoin(SdsDocumentModel, and_(
                SdsDocumentModel.product_id == ProductModel.product_id,
                SdsDocumentModel.document_status == SdsDocumentStatus.CURRENT,
            ))
            .outerjoin(BhpDecisionModel, and_(
                BhpDecisionModel.sds_id == SdsDocumentModel.sds_id,
                BhpDecisionModel.record_status == DecisionRecordStatus.CURRENT,
            ))
            .outerjoin(DecisionEvidenceModel,
                       DecisionEvidenceModel.evidence_id == BhpDecisionModel.evidence_id)
            .order_by(ProductModel.product_name,
                      ProductModel.manufacturer_product_code, ProductModel.product_id)
        ).mappings().all()

        seen_products: set[str] = set()
        for row in rows:
            if row["product_id"] in seen_products:
                raise SupervisoryReadError(
                    "Ambiguous CURRENT SDS/BHP decision for PRODUCT: "
                    + row["product_id"]
                )
            seen_products.add(row["product_id"])
        if not rows:
            return []

        locations: dict[str, list[dict]] = defaultdict(list)
        for location in self._session.execute(
            select(
                ProductUsageLocationModel.product_id,
                UsageLocationModel.location_name.label("usage_location_name"),
                ProductUsageLocationModel.peak_quantity_value,
                ProductUsageLocationModel.peak_quantity_unit,
                ProductUsageLocationModel.monthly_consumption_value,
                ProductUsageLocationModel.monthly_consumption_unit,
            )
            .join(UsageLocationModel,
                  ProductUsageLocationModel.location_id == UsageLocationModel.location_id)
            .where(UsageLocationModel.status == UsageLocationStatus.ACTIVE)
            .order_by(ProductUsageLocationModel.product_id,
                      UsageLocationModel.location_name, UsageLocationModel.location_id)
        ).mappings():
            locations[location["product_id"]].append({
                key: value for key, value in location.items() if key != "product_id"
            })

        result: list[SupervisoryProductRow] = []
        for row in rows:
            facts = dict(row)
            sds_relative_path = facts.pop("sds_relative_path")
            sds_available = source_file_available(
                self._settings.sds_root_path, sds_relative_path
            )
            evidence_available = source_file_available(
                self._settings.bhp_evidence_root_path,
                row["current_bhp_evidence_relative_path"],
            )
            for location in locations[row["product_id"]] or [{
                "usage_location_name": None,
                "peak_quantity_value": None,
                "peak_quantity_unit": None,
                "monthly_consumption_value": None,
                "monthly_consumption_unit": None,
            }]:
                result.append(SupervisoryProductRow(
                    **facts,
                    **location,
                    current_sds_file_available=sds_available,
                    current_bhp_evidence_available=evidence_available,
                ))
        return result
