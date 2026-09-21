import pytest

from app.application.exceptions import EntityNotFoundError
from app.application.use_cases import DeleteProduct


class FakeRepository:
    def __init__(self, deleted: bool = True) -> None:
        self.deleted = deleted
        self.product_id = None

    def delete_product(self, product_id: str) -> bool:
        self.product_id = product_id
        return self.deleted


def test_delete_product_delegates_selected_id() -> None:
    repository = FakeRepository()

    DeleteProduct(repository).execute("product-id")

    assert repository.product_id == "product-id"


def test_delete_product_rejects_unknown_product() -> None:
    with pytest.raises(EntityNotFoundError):
        DeleteProduct(FakeRepository(deleted=False)).execute("missing-product")


def test_delete_product_rejects_empty_id() -> None:
    with pytest.raises(ValueError):
        DeleteProduct(FakeRepository()).execute("")
