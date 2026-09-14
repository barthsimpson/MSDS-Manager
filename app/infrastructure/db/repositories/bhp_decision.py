"""SQLAlchemy persistence for one atomic BHP decision registration."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.dto import (
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)
from app.application.ports import BhpDecisionRepositoryPort
from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SdsDocumentStatus,
)
from app.infrastructure.db.models import (
    BhpDecisionModel,
    DecisionEvidenceModel,
    ProductHistoryModel,
    ProductModel,
    SdsDocumentModel,
)


class SqlAlchemyBhpDecisionRepository(BhpDecisionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def register(
        self, data: RegisterBhpDecisionInput
    ) -> RegisterBhpDecisionResult:
        product = self._session.get(ProductModel, data.product_id)
        if product is None:
            raise ValueError(f"Product not found: {data.product_id}")

        sds = self._session.get(SdsDocumentModel, data.sds_id)
        if sds is None:
            raise ValueError(f"SDS not found: {data.sds_id}")
        if sds.product_id != data.product_id:
            raise ValueError("SDS does not belong to product.")
        if sds.document_status is not SdsDocumentStatus.CURRENT:
            raise ValueError("SDS is not CURRENT.")

        self._session.execute(
            update(BhpDecisionModel)
            .where(
                BhpDecisionModel.sds_id == data.sds_id,
                BhpDecisionModel.record_status == DecisionRecordStatus.CURRENT,
            )
            .values(record_status=DecisionRecordStatus.SUPERSEDED)
        )
        now = datetime.now(timezone.utc)
        evidence_id = uuid4().hex
        evidence_format, evidence_type = _evidence_metadata(
            data.evidence_relative_path
        )
        self._session.add(
            DecisionEvidenceModel(
                evidence_id=evidence_id,
                relative_path=data.evidence_relative_path,
                evidence_type=evidence_type,
                file_format=evidence_format,
                file_status=FileAvailabilityStatus.AVAILABLE,
            )
        )
        self._after_evidence_created()

        decision_id = uuid4().hex
        self._session.add(
            BhpDecisionModel(
                decision_id=decision_id,
                product_id=data.product_id,
                sds_id=data.sds_id,
                decision_status=data.decision_status,
                notes=data.notes,
                registered_at=now,
                record_status=DecisionRecordStatus.CURRENT,
                evidence_id=evidence_id,
            )
        )
        product.usage_status = (
            ProductUsageStatus.ACTIVE
            if data.decision_status is BhpDecisionStatus.APPROVED
            else ProductUsageStatus.REJECTED
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
        return RegisterBhpDecisionResult(
            decision_id=decision_id,
            product_id=product.product_id,
            sds_id=sds.sds_id,
            decision_status=data.decision_status,
            product_usage_status=product.usage_status,
            registered_at=now,
            evidence_relative_path=data.evidence_relative_path,
        )

    def _after_evidence_created(self) -> None:
        """Test hook; the transaction owner still controls rollback."""


def _evidence_metadata(path: str) -> tuple[EvidenceFileFormat, EvidenceType]:
    suffix = Path(path).suffix.lower()
    formats = {
        ".msg": (EvidenceFileFormat.MSG, EvidenceType.EMAIL),
        ".pdf": (EvidenceFileFormat.PDF, EvidenceType.DOCUMENT),
        ".jpg": (EvidenceFileFormat.JPG, EvidenceType.PHOTO_SCAN),
        ".jpeg": (EvidenceFileFormat.JPEG, EvidenceType.PHOTO_SCAN),
        ".png": (EvidenceFileFormat.PNG, EvidenceType.PHOTO_SCAN),
    }
    try:
        return formats[suffix]
    except KeyError as error:
        raise ValueError(f"Unsupported evidence file type: {suffix}") from error