"""SQLAlchemy adapter for product history snapshots."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports import ProductHistoryRepositoryPort
from app.domain.models import ProductHistory
from app.infrastructure.db.models import ProductHistoryModel


class SqlAlchemyProductHistoryRepository(ProductHistoryRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: ProductHistory) -> None:
        self._session.add(
            ProductHistoryModel(
                history_id=snapshot.history_id,
                product_id=snapshot.product_id,
                usage_status=snapshot.usage_status,
                use_description=snapshot.use_description,
                use_restriction=snapshot.use_restriction,
                waste_type=snapshot.waste_type,
                waste_code=snapshot.waste_code,
                changed_at=snapshot.changed_at,
            )
        )

    def get_by_product_id(self, product_id: str) -> list[ProductHistory]:
        rows = self._session.execute(
            select(ProductHistoryModel)
            .where(ProductHistoryModel.product_id == product_id)
            .order_by(ProductHistoryModel.changed_at.asc(), ProductHistoryModel.history_id.asc())
        ).scalars().all()
        return [
            ProductHistory(
                product_id=row.product_id,
                usage_status=row.usage_status,
                use_description=row.use_description,
                use_restriction=row.use_restriction,
                waste_type=row.waste_type,
                waste_code=row.waste_code,
                history_id=row.history_id,
                changed_at=row.changed_at,
            )
            for row in rows
        ]
