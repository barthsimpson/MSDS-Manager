"""Application-facing persistence for product-location history snapshots."""

from typing import Protocol

from app.domain.models import ProductUsageLocationHistory


class ProductUsageLocationHistoryRepositoryPort(Protocol):
    def add(self, snapshot: ProductUsageLocationHistory) -> None: ...

    def get_by_product_id(
        self, product_id: str
    ) -> list[ProductUsageLocationHistory]: ...

    def get_by_location_id(
        self, location_id: str
    ) -> list[ProductUsageLocationHistory]: ...

    def get_by_product_and_location(
        self, product_id: str, location_id: str
    ) -> list[ProductUsageLocationHistory]: ...
