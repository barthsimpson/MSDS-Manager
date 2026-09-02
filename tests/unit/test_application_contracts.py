from dataclasses import fields
from decimal import Decimal

import pytest

import app.application.use_cases as public_use_cases
from app.application.dto import (
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
)
from app.application.exceptions import EntityNotFoundError, InactiveUsageLocationError
from app.application.use_cases import (
    AssignProductUsageLocation,
    CreateUsageLocation,
    DeactivateUsageLocation,
    GetProductDetails,
    ListManufacturers,
    ListProducts,
    ListUsageLocations,
    ReactivateUsageLocation,
    UpdateProductAdministrativeData,
    UpdateProductUsageLocation,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.domain.models import Manufacturer, ProductUsageLocation, UsageLocation


class FakeProductRepository:
    def __init__(self, details: ProductDetails | None) -> None:
        self.details = details
        self.updated: UpdateProductAdministrativeDataInput | None = None

    def list_all(self) -> list[ProductListItem]:
        return [] if self.details is None else [self.details]

    def get_details(self, product_id: str) -> ProductDetails | None:
        if self.details is None or self.details.product_id != product_id:
            return None
        return self.details

    def update_administrative_data(
        self, data: UpdateProductAdministrativeDataInput
    ) -> bool:
        if self.details is None or self.details.product_id != data.product_id:
            return False
        self.updated = data
        return True


class FakeUsageLocationRepository:
    def __init__(self, *locations: UsageLocation) -> None:
        self.locations = {location.location_id: location for location in locations}
        self.added: list[UsageLocation] = []
        self.status_updates: list[UsageLocation] = []

    def list_all(self) -> list[UsageLocation]:
        return list(self.locations.values())

    def get_by_id(self, location_id: str) -> UsageLocation | None:
        return self.locations.get(location_id)

    def add(self, location: UsageLocation) -> None:
        self.locations[location.location_id] = location
        self.added.append(location)

    def update_status(self, location: UsageLocation) -> None:
        self.locations[location.location_id] = location
        self.status_updates.append(location)


class FakeProductUsageLocationRepository:
    def __init__(self, update_succeeds: bool = True) -> None:
        self.added: list[ProductUsageLocation] = []
        self.updated: list[ProductUsageLocation] = []
        self.update_succeeds = update_succeeds

    def add(self, assignment: ProductUsageLocation) -> None:
        self.added.append(assignment)

    def update_quantities(self, assignment: ProductUsageLocation) -> bool:
        self.updated.append(assignment)
        return self.update_succeeds


class FakeManufacturerRepository:
    def list_all(self) -> list[Manufacturer]:
        return [Manufacturer("manufacturer-1", "Example Chemicals")]


@pytest.fixture
def product_details() -> ProductDetails:
    usage = ProductUsageLocationDetails(
        location_id="location-1",
        location_name="Mixing line",
        location_status=UsageLocationStatus.ACTIVE,
        peak_quantity_value=Decimal("4.5"),
        peak_quantity_unit="kg",
        monthly_consumption_value=Decimal("12"),
        monthly_consumption_unit="l",
    )
    return ProductDetails(
        product_id="product-1",
        product_name="Cleaner",
        manufacturer_product_code="C-100",
        manufacturer_id="manufacturer-1",
        manufacturer_name="Example Chemicals",
        usage_status=ProductUsageStatus.ACTIVE,
        use_description="Cleaning",
        use_restriction="Professional use",
        waste_type=None,
        waste_code=None,
        usage_locations=(usage,),
    )


def test_list_products_returns_application_dto_without_orm(
    product_details: ProductDetails,
) -> None:
    result = ListProducts(FakeProductRepository(product_details)).execute()

    assert result == [product_details]
    assert isinstance(result[0], ProductListItem)
    assert not type(result[0]).__module__.startswith("app.infrastructure")


def test_get_product_details_returns_manufacturer_and_usage_locations(
    product_details: ProductDetails,
) -> None:
    result = GetProductDetails(FakeProductRepository(product_details)).execute(
        "product-1"
    )

    assert result.manufacturer_name == "Example Chemicals"
    assert result.usage_locations[0].location_name == "Mixing line"
    assert result.usage_locations[0].peak_quantity_value == Decimal("4.5")


def test_get_product_details_uses_application_not_found_error() -> None:
    with pytest.raises(EntityNotFoundError):
        GetProductDetails(FakeProductRepository(None)).execute("missing-product")


def test_administrative_update_exposes_only_approved_mutable_fields(
    product_details: ProductDetails,
) -> None:
    assert {field.name for field in fields(UpdateProductAdministrativeDataInput)} == {
        "product_id",
        "use_description",
        "use_restriction",
        "waste_type",
        "waste_code",
    }
    data = UpdateProductAdministrativeDataInput(
        product_id="product-1",
        use_description="Updated use",
        use_restriction="Updated restriction",
        waste_type="Solvent waste",
        waste_code="14 06 03*",
    )
    repository = FakeProductRepository(product_details)

    UpdateProductAdministrativeData(repository).execute(data)

    assert repository.updated == data


def test_public_api_has_no_product_manufacturer_or_status_bypass_commands() -> None:
    assert not hasattr(public_use_cases, "CreateProduct")
    assert not hasattr(public_use_cases, "CreateManufacturer")
    assert not hasattr(public_use_cases, "SetProductStatus")


def test_existing_list_manufacturers_contract_still_works() -> None:
    assert ListManufacturers(FakeManufacturerRepository()).execute() == [
        Manufacturer("manufacturer-1", "Example Chemicals")
    ]


def test_list_usage_locations_includes_active_and_inactive() -> None:
    active = UsageLocation("active", "Active location")
    inactive = UsageLocation(
        "inactive", "Inactive location", UsageLocationStatus.INACTIVE
    )

    assert ListUsageLocations(
        FakeUsageLocationRepository(active, inactive)
    ).execute() == [active, inactive]


def test_create_usage_location_uses_domain_active_default() -> None:
    repository = FakeUsageLocationRepository()
    data = CreateUsageLocationInput(location_name="New line")

    result = CreateUsageLocation(repository, id_factory=lambda: "location-new").execute(
        data
    )

    assert result == UsageLocation("location-new", "New line")
    assert result.status is UsageLocationStatus.ACTIVE
    assert repository.added == [result]


def test_deactivate_and_reactivate_update_status_without_delete() -> None:
    active = UsageLocation("location-1", "Mixing line")
    repository = FakeUsageLocationRepository(active)

    inactive = DeactivateUsageLocation(repository).execute(active.location_id)
    reactivated = ReactivateUsageLocation(repository).execute(active.location_id)

    assert inactive.status is UsageLocationStatus.INACTIVE
    assert reactivated.status is UsageLocationStatus.ACTIVE
    assert reactivated.location_id == active.location_id
    assert repository.status_updates == [inactive, reactivated]
    assert not hasattr(repository, "delete")


def test_assign_product_to_active_location() -> None:
    assignment_repository = FakeProductUsageLocationRepository()
    location_repository = FakeUsageLocationRepository(
        UsageLocation("location-1", "Mixing line")
    )
    data = AssignProductUsageLocationInput(
        product_id="product-1",
        location_id="location-1",
        peak_quantity_value=Decimal("0"),
        peak_quantity_unit="kg",
        monthly_consumption_value=None,
        monthly_consumption_unit=None,
    )

    result = AssignProductUsageLocation(
        assignment_repository, location_repository
    ).execute(data)

    assert result.peak_quantity_value == Decimal("0")
    assert result.monthly_consumption_value is None
    assert assignment_repository.added == [result]


def test_assign_product_to_inactive_location_is_rejected() -> None:
    assignment_repository = FakeProductUsageLocationRepository()
    location_repository = FakeUsageLocationRepository(
        UsageLocation("location-1", "Old line", UsageLocationStatus.INACTIVE)
    )
    data = AssignProductUsageLocationInput(
        product_id="product-1",
        location_id="location-1",
        peak_quantity_value=Decimal("1"),
        peak_quantity_unit="kg",
    )

    with pytest.raises(InactiveUsageLocationError):
        AssignProductUsageLocation(
            assignment_repository, location_repository
        ).execute(data)

    assert assignment_repository.added == []


def test_assignment_accepts_monthly_zero_and_independent_units() -> None:
    assignment_repository = FakeProductUsageLocationRepository()
    location_repository = FakeUsageLocationRepository(
        UsageLocation("location-1", "Mixing line")
    )
    data = AssignProductUsageLocationInput(
        product_id="product-1",
        location_id="location-1",
        peak_quantity_value=Decimal("2.5"),
        peak_quantity_unit="kg",
        monthly_consumption_value=Decimal("0"),
        monthly_consumption_unit="l",
    )

    result = AssignProductUsageLocation(
        assignment_repository, location_repository
    ).execute(data)

    assert result.peak_quantity_unit == "kg"
    assert result.monthly_consumption_unit == "l"
    assert result.monthly_consumption_value == Decimal("0")


@pytest.mark.parametrize(
    ("peak", "monthly", "monthly_unit", "error_type"),
    [
        (Decimal("-0.01"), None, None, ValueError),
        (Decimal("1"), Decimal("-0.01"), "kg", ValueError),
        (Decimal("1"), Decimal("1"), None, ValueError),
        (Decimal("1"), None, "kg", ValueError),
        (1.0, None, None, TypeError),
    ],
)
def test_assignment_uses_existing_domain_quantity_validation(
    peak: Decimal,
    monthly: Decimal | None,
    monthly_unit: str | None,
    error_type: type[Exception],
) -> None:
    assignment_repository = FakeProductUsageLocationRepository()
    location_repository = FakeUsageLocationRepository(
        UsageLocation("location-1", "Mixing line")
    )
    data = AssignProductUsageLocationInput(
        product_id="product-1",
        location_id="location-1",
        peak_quantity_value=peak,
        peak_quantity_unit="kg",
        monthly_consumption_value=monthly,
        monthly_consumption_unit=monthly_unit,
    )

    with pytest.raises(error_type):
        AssignProductUsageLocation(
            assignment_repository, location_repository
        ).execute(data)

    assert assignment_repository.added == []


def test_update_assignment_preserves_composite_identity() -> None:
    repository = FakeProductUsageLocationRepository()
    data = UpdateProductUsageLocationInput(
        product_id="product-1",
        location_id="location-1",
        peak_quantity_value=Decimal("3"),
        peak_quantity_unit="kg",
        monthly_consumption_value=Decimal("7"),
        monthly_consumption_unit="l",
    )

    result = UpdateProductUsageLocation(repository).execute(data)

    assert (result.product_id, result.location_id) == ("product-1", "location-1")
    assert repository.updated == [result]
