import pytest

from app.application.dto import (
    CompleteManufacturerProductCodeInput, CorrectProductIdentityInput,
)
from app.application.exceptions import EntityNotFoundError
from app.application.use_cases import CompleteManufacturerProductCode, CorrectProductIdentity


class FakeRepository:
    def __init__(self, updated: bool = True) -> None:
        self.updated = updated
        self.received = None

    def correct_identity(self, data: CorrectProductIdentityInput) -> bool:
        self.received = data
        return self.updated

    def complete_manufacturer_product_code(self, product_id: str, code: str) -> bool:
        self.received = (product_id, code)
        return self.updated


def valid_input() -> CorrectProductIdentityInput:
    return CorrectProductIdentityInput(
        product_id=" product-id ",
        product_name=" New product ",
        manufacturer_product_code=" NEW-1 ",
        manufacturer_name=" New manufacturer ",
    )


def test_correct_product_identity_normalizes_and_delegates() -> None:
    repository = FakeRepository()

    CorrectProductIdentity(repository).execute(valid_input())

    assert repository.received == CorrectProductIdentityInput(
        product_id="product-id",
        product_name="New product",
        manufacturer_product_code="NEW-1",
        manufacturer_name="New manufacturer",
    )


@pytest.mark.parametrize(
    "field",
    ["product_name", "manufacturer_name"],
)
def test_correct_product_identity_rejects_empty_required_fields(field: str) -> None:
    data = valid_input()
    object.__setattr__(data, field, " ")

    with pytest.raises(ValueError):
        CorrectProductIdentity(FakeRepository()).execute(data)


def test_correct_product_identity_rejects_unknown_product() -> None:
    with pytest.raises(EntityNotFoundError):
        CorrectProductIdentity(FakeRepository(updated=False)).execute(valid_input())


def test_correction_normalizes_blank_code_to_none() -> None:
    repository = FakeRepository()
    data = valid_input()
    object.__setattr__(data, "manufacturer_product_code", "  ")
    CorrectProductIdentity(repository).execute(data)
    assert repository.received.manufacturer_product_code is None


def test_code_completion_requires_nonempty_code_and_delegates() -> None:
    repository = FakeRepository()
    CompleteManufacturerProductCode(repository).execute(
        CompleteManufacturerProductCodeInput(" product-id ", " CODE-1 ")
    )
    assert repository.received == ("product-id", "CODE-1")
    with pytest.raises(ValueError):
        CompleteManufacturerProductCode(repository).execute(
            CompleteManufacturerProductCodeInput("product-id", "   ")
        )
