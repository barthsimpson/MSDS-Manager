"""Application input DTOs for product-to-location assignments."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class AssignProductUsageLocationInput:
    product_id: str
    location_id: str
    peak_quantity_value: Decimal
    peak_quantity_unit: str
    monthly_consumption_value: Decimal | None = None
    monthly_consumption_unit: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateProductUsageLocationInput:
    product_id: str
    location_id: str
    peak_quantity_value: Decimal
    peak_quantity_unit: str
    monthly_consumption_value: Decimal | None = None
    monthly_consumption_unit: str | None = None
