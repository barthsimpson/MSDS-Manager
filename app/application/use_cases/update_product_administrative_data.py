"""Use case for the approved administrative fields of an existing product."""

from app.application.dto import UpdateProductAdministrativeDataInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductRepositoryPort


class UpdateProductAdministrativeData:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self._repository = repository

    def execute(self, data: UpdateProductAdministrativeDataInput) -> None:
        if not self._repository.update_administrative_data(data):
            raise EntityNotFoundError("Product", data.product_id)
