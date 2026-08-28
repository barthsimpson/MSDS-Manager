"""Product catalog and factory usage domain models."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import ProductUsageStatus


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


@dataclass(frozen=True, slots=True)
class UsageLocation:
    location_id: str
    location_name: str
    status: str


@dataclass(frozen=True, slots=True)
class ProductUsageLocation:
    product_id: str
    location_id: str
    quantity_value: Decimal
    quantity_unit: str
