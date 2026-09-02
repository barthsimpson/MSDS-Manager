"""Rules for aggregating product quantities across usage locations."""

from collections.abc import Iterable
from decimal import Decimal

from app.domain.exceptions import MixedQuantityUnitsError
from app.domain.models import ProductUsageLocation


def sum_product_quantity(usages: Iterable[ProductUsageLocation]) -> Decimal:
    """Sum peak quantities when every usage has exactly the same peak unit.

    Unit names are compared as provided. No unit conversion is attempted.
    """

    total = Decimal("0")
    expected_unit: str | None = None

    for usage in usages:
        if expected_unit is None:
            expected_unit = usage.peak_quantity_unit
        elif usage.peak_quantity_unit != expected_unit:
            raise MixedQuantityUnitsError(
                "Cannot sum product quantities expressed in different units."
            )
        total += usage.peak_quantity_value

    return total
