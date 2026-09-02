"""SQLAlchemy adapter for product-to-location assignment contracts."""

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.application.ports import ProductUsageLocationRepositoryPort
from app.domain.models import ProductUsageLocation
from app.infrastructure.db.models import ProductUsageLocationModel


class SqlAlchemyProductUsageLocationRepository(ProductUsageLocationRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, assignment: ProductUsageLocation) -> None:
        self._session.add(
            ProductUsageLocationModel(
                product_id=assignment.product_id,
                location_id=assignment.location_id,
                peak_quantity_value=assignment.peak_quantity_value,
                peak_quantity_unit=assignment.peak_quantity_unit,
                monthly_consumption_value=assignment.monthly_consumption_value,
                monthly_consumption_unit=assignment.monthly_consumption_unit,
            )
        )

    def update_quantities(self, assignment: ProductUsageLocation) -> bool:
        updated_product_id = self._session.scalar(
            update(ProductUsageLocationModel)
            .where(
                ProductUsageLocationModel.product_id == assignment.product_id,
                ProductUsageLocationModel.location_id == assignment.location_id,
            )
            .values(
                peak_quantity_value=assignment.peak_quantity_value,
                peak_quantity_unit=assignment.peak_quantity_unit,
                monthly_consumption_value=assignment.monthly_consumption_value,
                monthly_consumption_unit=assignment.monthly_consumption_unit,
            )
            .returning(ProductUsageLocationModel.product_id)
        )
        return updated_product_id is not None
