"""Minimal read query for a product and its CURRENT SDS file reference."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.exceptions import SupervisoryReadError
from app.application.use_cases.get_current_sds_file import CurrentSdsReference
from app.domain.enums import SdsDocumentStatus
from app.infrastructure.db.models import ProductModel, SdsDocumentModel


class SqlAlchemyCurrentSdsQuery:
    def __init__(self, session: Session) -> None:
        self._session = session

    def product_exists(self, product_id: str) -> bool:
        with self._session.no_autoflush:
            return self._session.scalar(
                select(ProductModel.product_id).where(ProductModel.product_id == product_id)
            ) is not None

    def get_current(self, product_id: str) -> CurrentSdsReference | None:
        with self._session.no_autoflush:
            rows = self._session.execute(
                select(SdsDocumentModel.original_filename, SdsDocumentModel.relative_path)
                .where(
                    SdsDocumentModel.product_id == product_id,
                    SdsDocumentModel.document_status == SdsDocumentStatus.CURRENT,
                )
                .limit(2)
            ).all()
        if len(rows) > 1:
            raise SupervisoryReadError(f"Ambiguous CURRENT SDS for PRODUCT: {product_id}")
        if not rows:
            return None
        return CurrentSdsReference(rows[0].original_filename, rows[0].relative_path)
