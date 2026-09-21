"""Application-facing persistence needs for existing products."""

from typing import Protocol

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    UpdateProductAdministrativeDataInput,
    UpdateProductIdentityInput,
)


class ProductRepositoryPort(Protocol):
    def list_all(self) -> list[ProductListItem]: ...

    def get_details(self, product_id: str) -> ProductDetails | None: ...

    def update_administrative_data(
        self, data: UpdateProductAdministrativeDataInput
    ) -> bool: ...

    def update_identity(self, data: UpdateProductIdentityInput) -> bool: ...
