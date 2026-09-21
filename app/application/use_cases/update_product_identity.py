"""Use case for editing the identity fields of an existing product."""

from dataclasses import replace

from app.application.dto import UpdateProductIdentityInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class UpdateProductIdentity:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, data: UpdateProductIdentityInput) -> None:
        values = (
            data.product_id,
            data.product_name,
            data.manufacturer_product_code,
            data.manufacturer_name,
        )
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Nazwa, kod producenta i producent są wymagane.")

        normalized = replace(
            data,
            product_id=data.product_id.strip(),
            product_name=data.product_name.strip(),
            manufacturer_product_code=data.manufacturer_product_code.strip(),
            manufacturer_name=data.manufacturer_name.strip(),
        )
        if not self._repository.update_identity(normalized):
            raise EntityNotFoundError("Product", data.product_id)
