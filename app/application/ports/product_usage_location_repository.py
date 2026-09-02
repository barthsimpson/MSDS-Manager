"""Application-facing persistence needs for product usage assignments."""

from typing import Protocol

from app.domain.models import ProductUsageLocation


class ProductUsageLocationRepositoryPort(Protocol):
    def add(self, assignment: ProductUsageLocation) -> None: ...

    def update_quantities(self, assignment: ProductUsageLocation) -> bool: ...
