"""Application DTOs for existing products and their usage locations."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import ProductUsageStatus, UsageLocationStatus


@dataclass(frozen=True, slots=True)
class ProductListItem:
    product_id: str
    product_name: str
    manufacturer_product_code: str
    manufacturer_id: str
    manufacturer_name: str
    usage_status: ProductUsageStatus
    use_description: str
    use_restriction: str
    waste_type: str | None
    waste_code: str | None


@dataclass(frozen=True, slots=True)
class ProductUsageLocationDetails:
    location_id: str
    location_name: str
    location_status: UsageLocationStatus
    peak_quantity_value: Decimal
    peak_quantity_unit: str
    monthly_consumption_value: Decimal | None
    monthly_consumption_unit: str | None


@dataclass(frozen=True, slots=True)
class ProductDetails(ProductListItem):
    usage_locations: tuple[ProductUsageLocationDetails, ...]


@dataclass(frozen=True, slots=True)
class UpdateProductAdministrativeDataInput:
    product_id: str
    use_description: str
    use_restriction: str
    waste_type: str | None
    waste_code: str | None
