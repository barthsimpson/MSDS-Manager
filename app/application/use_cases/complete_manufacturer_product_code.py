"""Explicit first completion of a missing manufacturer product code."""

from app.application.dto import CompleteManufacturerProductCodeInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class CompleteManufacturerProductCode:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, data: CompleteManufacturerProductCodeInput) -> None:
        if not isinstance(data.product_id, str) or not data.product_id.strip():
            raise ValueError("Identyfikator produktu jest wymagany.")
        if not isinstance(data.manufacturer_product_code, str) or not data.manufacturer_product_code.strip():
            raise ValueError("Kod producenta jest wymagany.")
        product_id = data.product_id.strip()
        code = data.manufacturer_product_code.strip()
        if not self._repository.complete_manufacturer_product_code(product_id, code):
            raise EntityNotFoundError("Product", product_id)
