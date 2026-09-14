"""SQLAlchemy adapter for product-location history snapshots."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports import ProductUsageLocationHistoryRepositoryPort
from app.domain.models import ProductUsageLocationHistory
from app.infrastructure.db.models import ProductUsageLocationHistoryModel


class SqlAlchemyProductUsageLocationHistoryRepository(
    ProductUsageLocationHistoryRepositoryPort
):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: ProductUsageLocationHistory) -> None:
        self._session.add(
            ProductUsageLocationHistoryModel(
                history_id=snapshot.history_id,
                product_id=snapshot.product_id,
                location_id=snapshot.location_id,
                peak_quantity_value=snapshot.peak_quantity_value,
                peak_quantity_unit=snapshot.peak_quantity_unit,
                monthly_consumption_value=snapshot.monthly_consumption_value,
                monthly_consumption_unit=snapshot.monthly_consumption_unit,
                changed_at=snapshot.changed_at,
            )
        )

    def get_by_product_id(self, product_id: str) -> list[ProductUsageLocationHistory]:
        rows = self._session.execute(
            select(ProductUsageLocationHistoryModel)
            .where(ProductUsageLocationHistoryModel.product_id == product_id)
            .order_by(
                ProductUsageLocationHistoryModel.changed_at.asc(),
                ProductUsageLocationHistoryModel.history_id.asc(),
            )
        ).scalars().all()
        return [
            ProductUsageLocationHistory(
                product_id=row.product_id,
                location_id=row.location_id,
                peak_quantity_value=row.peak_quantity_value,
                peak_quantity_unit=row.peak_quantity_unit,
                monthly_consumption_value=row.monthly_consumption_value,
                monthly_consumption_unit=row.monthly_consumption_unit,
                history_id=row.history_id,
                changed_at=row.changed_at,
            )
            for row in rows
        ]

    def get_by_location_id(self, location_id: str) -> list[ProductUsageLocationHistory]:
        rows = self._session.execute(
            select(ProductUsageLocationHistoryModel)
            .where(ProductUsageLocationHistoryModel.location_id == location_id)
            .order_by(
                ProductUsageLocationHistoryModel.changed_at.asc(),
                ProductUsageLocationHistoryModel.history_id.asc(),
            )
        ).scalars().all()
        return [
            ProductUsageLocationHistory(
                product_id=row.product_id,
                location_id=row.location_id,
                peak_quantity_value=row.peak_quantity_value,
                peak_quantity_unit=row.peak_quantity_unit,
                monthly_consumption_value=row.monthly_consumption_value,
                monthly_consumption_unit=row.monthly_consumption_unit,
                history_id=row.history_id,
                changed_at=row.changed_at,
            )
            for row in rows
        ]

    def get_by_product_and_location(
        self, product_id: str, location_id: str
    ) -> list[ProductUsageLocationHistory]:
        rows = self._session.execute(
            select(ProductUsageLocationHistoryModel)
            .where(
                ProductUsageLocationHistoryModel.product_id == product_id,
                ProductUsageLocationHistoryModel.location_id == location_id,
            )
            .order_by(
                ProductUsageLocationHistoryModel.changed_at.asc(),
                ProductUsageLocationHistoryModel.history_id.asc(),
            )
        ).scalars().all()
        return [
            ProductUsageLocationHistory(
                product_id=row.product_id,
                location_id=row.location_id,
                peak_quantity_value=row.peak_quantity_value,
                peak_quantity_unit=row.peak_quantity_unit,
                monthly_consumption_value=row.monthly_consumption_value,
                monthly_consumption_unit=row.monthly_consumption_unit,
                history_id=row.history_id,
                changed_at=row.changed_at,
            )
            for row in rows
        ]
