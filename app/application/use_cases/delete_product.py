"""Use case for explicitly deleting one selected product aggregate."""

from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class DeleteProduct:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, product_id: str) -> None:
        if not product_id:
            raise ValueError("Product is required.")
        if not self._repository.delete_product(product_id):
            raise EntityNotFoundError("Product", product_id)
