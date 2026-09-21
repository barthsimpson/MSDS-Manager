import pytest

from app.application.dto import UpdateProductIdentityInput
from app.application.exceptions import EntityNotFoundError
from app.application.use_cases import UpdateProductIdentity


class FakeRepository:
    def __init__(self, updated: bool = True) -> None:
        self.updated = updated
        self.received = None

    def update_identity(self, data: UpdateProductIdentityInput) -> bool:
        self.received = data
        return self.updated


def valid_input() -> UpdateProductIdentityInput:
    return UpdateProductIdentityInput(
        product_id=" product-id ",
        product_name=" New product ",
        manufacturer_product_code=" NEW-1 ",
        manufacturer_name=" New manufacturer ",
    )


def test_update_product_identity_normalizes_and_delegates() -> None:
    repository = FakeRepository()

    UpdateProductIdentity(repository).execute(valid_input())

    assert repository.received == UpdateProductIdentityInput(
        product_id="product-id",
        product_name="New product",
        manufacturer_product_code="NEW-1",
        manufacturer_name="New manufacturer",
    )


@pytest.mark.parametrize(
    "field",
    ["product_name", "manufacturer_product_code", "manufacturer_name"],
)
def test_update_product_identity_rejects_empty_required_fields(field: str) -> None:
    data = valid_input()
    object.__setattr__(data, field, " ")

    with pytest.raises(ValueError):
        UpdateProductIdentity(FakeRepository()).execute(data)


def test_update_product_identity_rejects_unknown_product() -> None:
    with pytest.raises(EntityNotFoundError):
        UpdateProductIdentity(FakeRepository(updated=False)).execute(valid_input())
