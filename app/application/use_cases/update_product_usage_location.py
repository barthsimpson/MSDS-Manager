"""Use case for updating assignment quantities without changing identity."""

from datetime import datetime, timezone

from app.application.dto import UpdateProductUsageLocationInput
from app.application.exceptions import EntityNotFoundError, InactiveUnitOfMeasureError
from app.application.ports import (
    ProductUsageLocationHistoryRepositoryPort,
    ProductUsageLocationRepositoryPort,
    UnitOfMeasureRepositoryPort,
)
from app.domain.enums import UnitStatus
from app.domain.models import ProductUsageLocation, ProductUsageLocationHistory


class UpdateProductUsageLocation:
    def __init__(
        self,
        repository: ProductUsageLocationRepositoryPort,
        history_repository: ProductUsageLocationHistoryRepositoryPort | None = None,
        *,
        unit_repository: UnitOfMeasureRepositoryPort,
    ) -> None:
        self._repository = repository
        self._history_repository = history_repository
        self._unit_repository = unit_repository

    def _require_active_unit(self, unit_id: str) -> None:
        unit = self._unit_repository.get_by_id(unit_id)
        if unit is None:
            raise EntityNotFoundError("UnitOfMeasure", unit_id)
        if unit.status is not UnitStatus.ACTIVE:
            raise InactiveUnitOfMeasureError(unit_id)

    def execute(
        self, data: UpdateProductUsageLocationInput
    ) -> ProductUsageLocation:
        assignment = ProductUsageLocation(
            product_id=data.product_id,
            location_id=data.location_id,
            peak_quantity_value=data.peak_quantity_value,
            peak_quantity_unit_id=data.peak_quantity_unit_id,
            monthly_consumption_value=data.monthly_consumption_value,
            monthly_consumption_unit_id=data.monthly_consumption_unit_id,
        )
        self._require_active_unit(assignment.peak_quantity_unit_id)
        if assignment.monthly_consumption_unit_id is not None:
            self._require_active_unit(assignment.monthly_consumption_unit_id)
        if not self._repository.update_quantities(assignment):
            assignment_id = f"{data.product_id}/{data.location_id}"
            raise EntityNotFoundError("ProductUsageLocation", assignment_id)
        if self._history_repository is not None:
            self._history_repository.add(
                ProductUsageLocationHistory(
                    product_id=data.product_id,
                    location_id=data.location_id,
                    peak_quantity_value=data.peak_quantity_value,
                    peak_quantity_unit_id=data.peak_quantity_unit_id,
                    monthly_consumption_value=data.monthly_consumption_value,
                    monthly_consumption_unit_id=data.monthly_consumption_unit_id,
                    changed_at=datetime.now(timezone.utc),
                )
            )
        return assignment
