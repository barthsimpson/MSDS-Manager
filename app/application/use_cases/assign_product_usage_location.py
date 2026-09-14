"""Use case for assigning an existing product to an active location."""

from datetime import datetime, timezone

from app.application.dto import AssignProductUsageLocationInput
from app.application.exceptions import EntityNotFoundError, InactiveUsageLocationError
from app.application.ports import (
    ProductUsageLocationHistoryRepositoryPort,
    ProductUsageLocationRepositoryPort,
    UsageLocationRepositoryPort,
)
from app.domain.enums import UsageLocationStatus
from app.domain.models import ProductUsageLocation, ProductUsageLocationHistory


class AssignProductUsageLocation:
    def __init__(
        self,
        repository: ProductUsageLocationRepositoryPort,
        location_repository: UsageLocationRepositoryPort,
        history_repository: ProductUsageLocationHistoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._location_repository = location_repository
        self._history_repository = history_repository

    def execute(
        self, data: AssignProductUsageLocationInput
    ) -> ProductUsageLocation:
        location = self._location_repository.get_by_id(data.location_id)
        if location is None:
            raise EntityNotFoundError("UsageLocation", data.location_id)
        if location.status is not UsageLocationStatus.ACTIVE:
            raise InactiveUsageLocationError(data.location_id)

        assignment = ProductUsageLocation(
            product_id=data.product_id,
            location_id=data.location_id,
            peak_quantity_value=data.peak_quantity_value,
            peak_quantity_unit=data.peak_quantity_unit,
            monthly_consumption_value=data.monthly_consumption_value,
            monthly_consumption_unit=data.monthly_consumption_unit,
        )
        self._repository.add(assignment)
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
