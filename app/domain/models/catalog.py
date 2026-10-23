"""Product catalog and factory usage domain models."""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import ProductUsageStatus, UnitCategory, UnitStatus, UsageLocationStatus


def _validate_unit_id(unit_id: str, field_name: str) -> None:
    if not isinstance(unit_id, str):
        raise TypeError(f"{field_name} must be a UUID string.")
    try:
        UUID(unit_id)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a UUID string.") from error


@dataclass(frozen=True, slots=True)
class UnitOfMeasure:
    unit_id: str
    code: str
    name: str
    category: UnitCategory
    status: UnitStatus

    def __post_init__(self) -> None:
        _validate_unit_id(self.unit_id, "unit_id")
        if not self.code or not self.code.strip():
            raise ValueError("code is required.")
        if not self.name or not self.name.strip():
            raise ValueError("name is required.")
        if not isinstance(self.category, UnitCategory):
            raise ValueError("category is invalid.")
        if not isinstance(self.status, UnitStatus):
            raise ValueError("status is invalid.")


@dataclass(frozen=True, slots=True)
class Manufacturer:
    manufacturer_id: str
    manufacturer_name: str


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    product_name: str
    manufacturer_product_code: str | None
    manufacturer_id: str
    use_description: str | None
    use_restriction: str | None
    usage_status: ProductUsageStatus
    waste_type: str | None = None
    waste_code: str | None = None


@dataclass(frozen=True, slots=True)
class UsageLocation:
    location_id: str
    location_name: str
    status: UsageLocationStatus = UsageLocationStatus.ACTIVE
    location_code: str | None = None

    def deactivate(self) -> "UsageLocation":
        return replace(self, status=UsageLocationStatus.INACTIVE)

    def reactivate(self) -> "UsageLocation":
        return replace(self, status=UsageLocationStatus.ACTIVE)


@dataclass(frozen=True, slots=True)
class ProductUsageLocation:
    product_id: str
    location_id: str
    peak_quantity_value: Decimal
    peak_quantity_unit_id: str
    monthly_consumption_value: Decimal | None = None
    monthly_consumption_unit_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.peak_quantity_value, Decimal):
            raise TypeError("peak_quantity_value must be a Decimal.")
        if self.peak_quantity_value < 0:
            raise ValueError("peak_quantity_value cannot be negative.")
        _validate_unit_id(self.peak_quantity_unit_id, "peak_quantity_unit_id")

        monthly_value_is_set = self.monthly_consumption_value is not None
        monthly_unit_is_set = self.monthly_consumption_unit_id is not None
        if monthly_value_is_set != monthly_unit_is_set:
            raise ValueError(
                "monthly_consumption_value and monthly_consumption_unit_id "
                "must either both be set or both be None."
            )
        if monthly_value_is_set:
            _validate_unit_id(self.monthly_consumption_unit_id, "monthly_consumption_unit_id")
            if not isinstance(self.monthly_consumption_value, Decimal):
                raise TypeError("monthly_consumption_value must be a Decimal.")
            if self.monthly_consumption_value < 0:
                raise ValueError("monthly_consumption_value cannot be negative.")


@dataclass(frozen=True, slots=True)
class ProductHistory:
    product_id: str
    usage_status: ProductUsageStatus
    use_description: str | None
    use_restriction: str | None
    waste_type: str | None = None
    waste_code: str | None = None
    history_id: str = field(default_factory=lambda: uuid4().hex)
    changed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True, slots=True)
class ProductIdentityChange:
    product_id: str
    change_kind: str
    old_product_name: str
    new_product_name: str
    old_manufacturer_product_code: str | None
    new_manufacturer_product_code: str | None
    old_manufacturer_id: str
    new_manufacturer_id: str
    change_id: str = field(default_factory=lambda: uuid4().hex)
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.change_kind not in {"CODE_COMPLETION", "CORRECTION"}:
            raise ValueError("Invalid product identity change kind.")
        if self.change_kind == "CODE_COMPLETION" and (
            self.old_manufacturer_product_code is not None
            or not self.new_manufacturer_product_code
            or not self.new_manufacturer_product_code.strip()
            or self.old_product_name != self.new_product_name
            or self.old_manufacturer_id != self.new_manufacturer_id
        ):
            raise ValueError("Code completion must only fill a missing code for the same product.")


@dataclass(frozen=True, slots=True)
class UsageLocationHistory:
    location_id: str
    status: UsageLocationStatus
    history_id: str = field(default_factory=lambda: uuid4().hex)
    changed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True, slots=True)
class ProductUsageLocationHistory:
    product_id: str
    location_id: str
    peak_quantity_value: Decimal
    peak_quantity_unit_id: str
    monthly_consumption_value: Decimal | None = None
    monthly_consumption_unit_id: str | None = None
    history_id: str = field(default_factory=lambda: uuid4().hex)
    changed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        _validate_unit_id(self.peak_quantity_unit_id, "peak_quantity_unit_id")
        if (self.monthly_consumption_value is None) != (self.monthly_consumption_unit_id is None):
            raise ValueError("monthly consumption value and unit_id must both be set or both be None.")
        if self.monthly_consumption_unit_id is not None:
            _validate_unit_id(self.monthly_consumption_unit_id, "monthly_consumption_unit_id")
