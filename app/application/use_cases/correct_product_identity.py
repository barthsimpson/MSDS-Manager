"""Explicit correction of erroneously registered product identity."""

from dataclasses import replace

from app.application.dto import CorrectProductIdentityInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class CorrectProductIdentity:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, data: CorrectProductIdentityInput) -> None:
        required = (data.product_id, data.product_name, data.manufacturer_name)
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("Identyfikator, nazwa produktu i producent są wymagane.")
        code = data.manufacturer_product_code
        if code is not None and not isinstance(code, str):
            raise ValueError("Kod producenta musi być tekstem albo brakiem wartości.")
        normalized = replace(
            data,
            product_id=data.product_id.strip(),
            product_name=data.product_name.strip(),
            manufacturer_product_code=(code.strip() or None) if code is not None else None,
            manufacturer_name=data.manufacturer_name.strip(),
        )
        if not self._repository.correct_identity(normalized):
            raise EntityNotFoundError("Product", normalized.product_id)
