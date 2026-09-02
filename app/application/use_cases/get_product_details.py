"""Use case for reading an existing product and declared usage locations."""

from app.application.dto import ProductDetails
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class GetProductDetails:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, product_id: str) -> ProductDetails:
        details = self._repository.get_details(product_id)
        if details is None:
            raise EntityNotFoundError("Product", product_id)
        return details
