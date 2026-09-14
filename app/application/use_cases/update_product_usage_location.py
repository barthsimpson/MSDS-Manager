"""Use case for updating assignment quantities without changing identity."""

from datetime import datetime, timezone

from app.application.dto import UpdateProductUsageLocationInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import (
    ProductUsageLocationHistoryRepositoryPort,
    ProductUsageLocationRepositoryPort,
)
from app.domain.models import ProductUsageLocation, ProductUsageLocationHistory


class UpdateProductUsageLocation:
    def __init__(
        self,
        repository: ProductUsageLocationRepositoryPort,
        history_repository: ProductUsageLocationHistoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._history_repository = history_repository

    def execute(
        self, data: UpdateProductUsageLocationInput
    ) -> ProductUsageLocation:
        assignment = ProductUsageLocation(
            product_id=data.product_id,
            location_id=data.location_id,
            peak_quantity_value=data.peak_quantity_value,
            peak_quantity_unit=data.peak_quantity_unit,
            monthly_consumption_value=data.monthly_consumption_value,
            monthly_consumption_unit=data.monthly_consumption_unit,
        )
        if not self._repository.update_quantities(assignment):
            assignment_id = f"{data.product_id}/{data.location_id}"
            raise EntityNotFoundError("ProductUsageLocation", assignment_id)
        if self._history_repository is not None:
            self._history_repository.add(
                ProductUsageLocationHistory(
                    product_id=data.product_id,
                    location_id=data.location_id,
                    peak_quantity_value=data.peak_quantity_value,
                    peak_quantity_unit=data.peak_quantity_unit,
                    monthly_consumption_value=data.monthly_consumption_value,
                    monthly_consumption_unit=data.monthly_consumption_unit,
                    changed_at=datetime.now(timezone.utc),
                )
            )
        return assignment
