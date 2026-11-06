"""Atomic SDS invalidation and product SDS history read."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.dto.sds_invalidation import InvalidateSdsInput, SdsHistoryItem
from app.domain.enums import DecisionRecordStatus, ProductUsageStatus, SdsDocumentStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, ProductHistoryModel, ProductModel,
    SdsDocumentModel, SdsInvalidationModel,
)


class SqlAlchemySdsInvalidationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_product(self, product_id: str) -> tuple[SdsHistoryItem, ...]:
        rows = self._session.execute(
            select(SdsDocumentModel, SdsInvalidationModel)
            .outerjoin(
                SdsInvalidationModel,
                SdsInvalidationModel.invalidated_sds_id == SdsDocumentModel.sds_id,
            )
            .where(SdsDocumentModel.product_id == product_id)
            .order_by(SdsDocumentModel.registered_at.desc(), SdsDocumentModel.sds_id)
        ).all()
        return tuple(
            SdsHistoryItem(
                sds_id=sds.sds_id, product_id=sds.product_id,
                original_filename=sds.original_filename, relative_path=sds.relative_path,
                issue_date=sds.issue_date, revision=sds.revision,
                document_status=sds.document_status, registered_at=sds.registered_at,
                invalidated_at=audit.invalidated_at if audit else None,
                invalidation_reason=audit.reason if audit else None,
                invalidated_from_status=audit.invalidated_from_status if audit else None,
                restored_sds_id=audit.restored_sds_id if audit else None,
            )
            for sds, audit in rows
        )

    def invalidate(self, data: InvalidateSdsInput) -> str:
        product = self._session.scalar(
            select(ProductModel).where(ProductModel.product_id == data.product_id).with_for_update()
        )
        if product is None:
            raise ValueError("STALE_STATE: produkt nie istnieje.")
        documents = self._session.scalars(
            select(SdsDocumentModel)
            .where(SdsDocumentModel.product_id == data.product_id)
            .order_by(SdsDocumentModel.sds_id)
            .with_for_update()
        ).all()
        by_id = {document.sds_id: document for document in documents}
        target = by_id.get(data.invalidated_sds_id)
        current = next(
            (document.sds_id for document in documents
             if document.document_status is SdsDocumentStatus.CURRENT), None
        )
        if target is None or target.document_status is not data.expected_status:
            raise ValueError("STALE_STATE: SDS zmienił status albo nie istnieje.")
        if current != data.expected_current_sds_id:
            raise ValueError("STALE_STATE: bieżący SDS zmienił się.")
        if self._session.scalar(select(SdsInvalidationModel.invalidation_id).where(
            SdsInvalidationModel.invalidated_sds_id == target.sds_id
        )) is not None:
            raise ValueError("SDS został już wycofany.")
        replacement = None
        if data.mode == "RESTORE_ARCHIVED":
            replacement = by_id.get(data.restored_sds_id)
            if replacement is None or replacement.document_status is not SdsDocumentStatus.ARCHIVED:
                raise ValueError("STALE_STATE: wybrany SDS nie jest już ARCHIVED.")
        now = datetime.now(timezone.utc)
        target.document_status = SdsDocumentStatus.INVALIDATED
        self._session.flush()
        if replacement is not None:
            replacement.document_status = SdsDocumentStatus.CURRENT
        if data.expected_status is SdsDocumentStatus.CURRENT:
            if product.usage_status is not ProductUsageStatus.PENDING_APPROVAL:
                product.usage_status = ProductUsageStatus.PENDING_APPROVAL
                self._session.add(ProductHistoryModel(
                    history_id=uuid4().hex, product_id=product.product_id,
                    usage_status=product.usage_status,
                    use_description=product.use_description,
                    use_restriction=product.use_restriction,
                    waste_type=product.waste_type, waste_code=product.waste_code,
                    changed_at=now,
                ))
            affected_ids = [target.sds_id]
            if replacement is not None:
                affected_ids.append(replacement.sds_id)
            self._session.execute(
                update(BhpDecisionModel)
                .where(
                    BhpDecisionModel.sds_id.in_(affected_ids),
                    BhpDecisionModel.record_status == DecisionRecordStatus.CURRENT,
                )
                .values(record_status=DecisionRecordStatus.SUPERSEDED)
            )
        invalidation_id = uuid4().hex
        self._session.add(SdsInvalidationModel(
            invalidation_id=invalidation_id, product_id=product.product_id,
            invalidated_sds_id=target.sds_id,
            invalidated_from_status=data.expected_status.value,
            restored_sds_id=replacement.sds_id if replacement else None,
            reason=data.reason.strip(), invalidated_at=now,
        ))
        self._session.flush()
        return invalidation_id
