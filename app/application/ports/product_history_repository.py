"""Application-facing persistence for product history snapshots."""

from typing import Protocol

from app.domain.models import ProductHistory


class ProductHistoryRepositoryPort(Protocol):
    def add(self, snapshot: ProductHistory) -> None: ...

    def get_by_product_id(self, product_id: str) -> list[ProductHistory]: ...
