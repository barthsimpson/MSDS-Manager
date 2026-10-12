"""Application-facing persistence needs for existing products."""

from typing import Protocol

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    UpdateProductAdministrativeDataInput,
    CorrectProductIdentityInput,
)


class ProductRepositoryPort(Protocol):
    def list_all(self) -> list[ProductListItem]: ...

    def get_details(self, product_id: str) -> ProductDetails | None: ...

    def update_administrative_data(
        self, data: UpdateProductAdministrativeDataInput
    ) -> bool: ...

    def complete_manufacturer_product_code(self, product_id: str, code: str) -> bool: ...

    def correct_identity(self, data: CorrectProductIdentityInput) -> bool: ...

    def delete_product(self, product_id: str) -> bool: ...
