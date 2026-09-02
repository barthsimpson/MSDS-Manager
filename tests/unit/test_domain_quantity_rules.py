from decimal import Decimal

import pytest

from app.domain.exceptions import MixedQuantityUnitsError
from app.domain.models import ProductUsageLocation
from app.domain.rules import sum_product_quantity


def usage(
    location_id: str,
    peak_value: str,
    peak_unit: str,
    monthly_value: str | None = None,
    monthly_unit: str | None = None,
) -> ProductUsageLocation:
    return ProductUsageLocation(
        product_id="product-1",
        location_id=location_id,
        peak_quantity_value=Decimal(peak_value),
        peak_quantity_unit=peak_unit,
        monthly_consumption_value=(
            Decimal(monthly_value) if monthly_value is not None else None
        ),
        monthly_consumption_unit=monthly_unit,
    )


def test_sums_quantities_with_one_unit_without_precision_loss() -> None:
    usages = [
        usage("a", "0.1", "kg", "100", "l"),
        usage("b", "0.2", "kg", "200", "ml"),
    ]

    assert sum_product_quantity(usages) == Decimal("0.3")


def test_peak_zero_and_missing_monthly_consumption_are_valid() -> None:
    assignment = usage("a", "0", "kg")

    assert assignment.peak_quantity_value == Decimal("0")
    assert assignment.monthly_consumption_value is None
    assert assignment.monthly_consumption_unit is None
    assert sum_product_quantity([assignment]) == Decimal("0")


@pytest.mark.parametrize("monthly_value", ["0", "12.75"])
def test_monthly_consumption_with_unit_is_valid(monthly_value: str) -> None:
    assignment = usage("a", "1", "kg", monthly_value, "l")

    assert assignment.monthly_consumption_value == Decimal(monthly_value)
    assert assignment.monthly_consumption_unit == "l"


def test_rejects_negative_peak_quantity() -> None:
    with pytest.raises(ValueError, match="peak_quantity_value"):
        usage("a", "-0.01", "kg")


def test_rejects_negative_monthly_consumption() -> None:
    with pytest.raises(ValueError, match="monthly_consumption_value"):
        usage("a", "1", "kg", "-0.01", "kg")


def test_rejects_monthly_value_without_unit() -> None:
    with pytest.raises(ValueError, match="must either both be set"):
        usage("a", "1", "kg", "1", None)


def test_rejects_monthly_unit_without_value() -> None:
    with pytest.raises(ValueError, match="must either both be set"):
        usage("a", "1", "kg", None, "kg")


def test_monthly_consumption_does_not_affect_peak_aggregation() -> None:
    usages = [
        usage("a", "1", "kg", "500", "l"),
        usage("b", "2", "kg", "900", "ml"),
    ]

    assert sum_product_quantity(usages) == Decimal("3")


@pytest.mark.parametrize(
    "second_unit",
    ["g", "l", "ml"],
)
def test_rejects_different_units_without_conversion(second_unit: str) -> None:
    usages = [usage("a", "1", "kg"), usage("b", "1000", second_unit)]

    with pytest.raises(MixedQuantityUnitsError):
        sum_product_quantity(usages)
