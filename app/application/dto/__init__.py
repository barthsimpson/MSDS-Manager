"""Application data transfer objects package."""

from .product_usage_locations import (
    AssignProductUsageLocationInput,
    UpdateProductUsageLocationInput,
)
from .products import (
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    UpdateProductAdministrativeDataInput,
)
from .usage_locations import CreateUsageLocationInput

__all__ = [
    "AssignProductUsageLocationInput",
    "CreateUsageLocationInput",
    "ProductDetails",
    "ProductListItem",
    "ProductUsageLocationDetails",
    "UpdateProductAdministrativeDataInput",
    "UpdateProductUsageLocationInput",
]
