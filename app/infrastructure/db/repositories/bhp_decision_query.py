"""Read adapter for the Streamlit BHP decision view."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto import BhpDecisionProduct, CurrentBhpDecision
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ManufacturerModel,
    ProductModel,
    SdsDocumentModel,
)


class SqlAlchemyBhpDecisionQuery:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_products(self) -> tuple[BhpDecisionProduct, ...]:
        rows = self._session.execute(
            select(ProductModel, ManufacturerModel, SdsDocumentModel)
            .join(ManufacturerModel, ProductModel.manufacturer_id == ManufacturerModel.manufacturer_id)
            .join(SdsDocumentModel, SdsDocumentModel.product_id == ProductModel.product_id)
            .where(SdsDocumentModel.document_status == "CURRENT")
            .order_by(ProductModel.product_name, ProductModel.product_id)
        ).all()
        return tuple(
            BhpDecisionProduct(
                product_id=product.product_id,
                product_name=product.product_name,
                manufacturer_product_code=product.manufacturer_product_code,
                manufacturer_name=manufacturer.manufacturer_name,
                usage_status=product.usage_status,
                sds_id=sds.sds_id,
                sds_filename=sds.original_filename,
                sds_issue_date=sds.issue_date,
                sds_revision=sds.revision,
            )
            for product, manufacturer, sds in rows
        )

    def get_current_decision(self, sds_id: str) -> CurrentBhpDecision | None:
        row = self._session.execute(
            select(BhpDecisionModel, DecisionEvidenceModel)
            .join(DecisionEvidenceModel, BhpDecisionModel.evidence_id == DecisionEvidenceModel.evidence_id)
            .where(
                BhpDecisionModel.sds_id == sds_id,
                BhpDecisionModel.record_status == "CURRENT",
            )
        ).one_or_none()
        if row is None:
            return None
        decision, evidence = row
        return CurrentBhpDecision(
            decision_status=decision.decision_status,
            registered_at=decision.registered_at,
            notes=decision.notes,
            evidence_relative_path=evidence.relative_path,
        )