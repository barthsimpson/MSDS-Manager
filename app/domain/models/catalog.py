"""Product catalog and factory usage domain models."""

from dataclasses import dataclass, replace
from decimal import Decimal

from app.domain.enums import ProductUsageStatus, UsageLocationStatus


@dataclass(frozen=True, slots=True)
class Manufacturer:
    manufacturer_id: str
    manufacturer_name: str


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    product_name: str
    manufacturer_product_code: str
    manufacturer_id: str
    use_description: str
    use_restriction: str
    usage_status: ProductUsageStatus
    waste_type: str | None = None
    waste_code: str | None = None


@dataclass(frozen=True, slots=True)
class UsageLocation:
    location_id: str
    location_name: str
    status: UsageLocationStatus = UsageLocationStatus.ACTIVE

    def deactivate(self) -> "UsageLocation":
        return replace(self, status=UsageLocationStatus.INACTIVE)

    def reactivate(self) -> "UsageLocation":
        return replace(self, status=UsageLocationStatus.ACTIVE)


@dataclass(frozen=True, slots=True)
class ProductUsageLocation:
    product_id: str
    location_id: str
    peak_quantity_value: Decimal
    peak_quantity_unit: str
    monthly_consumption_value: Decimal | None = None
    monthly_consumption_unit: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.peak_quantity_value, Decimal):
            raise TypeError("peak_quantity_value must be a Decimal.")
        if self.peak_quantity_value < 0:
            raise ValueError("peak_quantity_value cannot be negative.")
        if self.peak_quantity_unit is None:
            raise ValueError("peak_quantity_unit is required.")

        monthly_value_is_set = self.monthly_consumption_value is not None
        monthly_unit_is_set = self.monthly_consumption_unit is not None
        if monthly_value_is_set != monthly_unit_is_set:
            raise ValueError(
                "monthly_consumption_value and monthly_consumption_unit "
                "must either both be set or both be None."
            )
        if monthly_value_is_set:
            if not isinstance(self.monthly_consumption_value, Decimal):
                raise TypeError("monthly_consumption_value must be a Decimal.")
            if self.monthly_consumption_value < 0:
                raise ValueError("monthly_consumption_value cannot be negative.")
