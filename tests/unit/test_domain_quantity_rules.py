from decimal import Decimal

import pytest

from app.domain.exceptions import MixedQuantityUnitsError
from app.domain.models import ProductUsageLocation
from app.domain.rules import sum_product_quantity


def usage(location_id: str, value: str, unit: str) -> ProductUsageLocation:
    return ProductUsageLocation(
        product_id="product-1",
        location_id=location_id,
        quantity_value=Decimal(value),
        quantity_unit=unit,
    )


def test_sums_quantities_with_one_unit_without_precision_loss() -> None:
    usages = [usage("a", "0.1", "kg"), usage("b", "0.2", "kg")]

    assert sum_product_quantity(usages) == Decimal("0.3")


@pytest.mark.parametrize(
    "second_unit",
    ["g", "l", "ml"],
)
def test_rejects_different_units_without_conversion(second_unit: str) -> None:
    usages = [usage("a", "1", "kg"), usage("b", "1000", second_unit)]

    with pytest.raises(MixedQuantityUnitsError):
        sum_product_quantity(usages)
