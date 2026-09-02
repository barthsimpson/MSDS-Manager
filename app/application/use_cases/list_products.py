"""Use case for listing existing products."""

from app.application.dto import ProductListItem
from app.application.ports import ProductRepositoryPort


class ListProducts:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[ProductListItem]:
        return self._repository.list_all()
