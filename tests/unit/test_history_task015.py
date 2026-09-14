from datetime import datetime
from decimal import Decimal

import pytest

from app.application.use_cases import (
    AssignProductUsageLocation,
    DeactivateUsageLocation,
    ReactivateUsageLocation,
    UpdateProductAdministrativeData,
    UpdateProductUsageLocation,
)
from app.application.dto import (
    AssignProductUsageLocationInput,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.domain.models import ProductHistory, ProductUsageLocationHistory, UsageLocationHistory
from app.domain.models import ProductUsageLocation, UsageLocation


class FakeProductRepository:
    def __init__(self, product_details):
        self.product_details = product_details
        self.updated = None

    def get_details(self, product_id):
        if self.product_details is None or self.product_details.product_id != product_id:
            return None
        return self.product_details

    def update_administrative_data(self, data):
        if self.product_details is None or self.product_details.product_id != data.product_id:
            return False
        self.updated = data
        return True


class FakeHistoryRepository:
    def __init__(self):
        self.snapshots = []

    def add(self, snapshot):
        self.snapshots.append(snapshot)


class FakeUsageLocationRepository:
    def __init__(self, location):
        self.location = location

    def get_by_id(self, location_id):
        if self.location.location_id == location_id:
            return self.location
        return None

    def update_status(self, location):
        self.location = location


class FakeProductUsageLocationRepository:
    def __init__(self):
        self.assignment = None

    def add(self, assignment):
        self.assignment = assignment

    def update_quantities(self, assignment):
        self.assignment = assignment
        return True


@pytest.fixture
def product_details():
    return type(
        "ProductDetails",
        (),
        {
            "product_id": "product-1",
            "product_name": "Cleaner",
            "manufacturer_product_code": "C-100",
            "manufacturer_id": "manufacturer-1",
            "manufacturer_name": "Example Chemicals",
            "usage_status": ProductUsageStatus.ACTIVE,
            "use_description": "Cleaning",
            "use_restriction": "Professional use",
            "waste_type": None,
            "waste_code": None,
        },
    )()


def test_product_history_snapshot_is_created_for_admin_update(product_details):
    history_repo = FakeHistoryRepository()
    repository = FakeProductRepository(product_details)

    UpdateProductAdministrativeData(repository, history_repo).execute(
        UpdateProductAdministrativeDataInput(
            product_id="product-1",
            use_description="Updated use",
            use_restriction="Updated restriction",
            waste_type="Solvent waste",
            waste_code="14 06 03*",
        )
    )

    assert len(history_repo.snapshots) == 1
    snapshot = history_repo.snapshots[0]
    assert isinstance(snapshot, ProductHistory)
    assert snapshot.product_id == "product-1"
    assert snapshot.usage_status is ProductUsageStatus.ACTIVE
    assert snapshot.use_description == "Updated use"
    assert snapshot.use_restriction == "Updated restriction"
    assert snapshot.waste_type == "Solvent waste"
    assert snapshot.waste_code == "14 06 03*"
    assert isinstance(snapshot.changed_at, datetime)


def test_usage_location_status_history_records_state_transition():
    active = UsageLocation("location-1", "Mixing line")
    history_repo = FakeHistoryRepository()

    DeactivateUsageLocation(FakeUsageLocationRepository(active), history_repo).execute(
        "location-1"
    )
    ReactivateUsageLocation(FakeUsageLocationRepository(active), history_repo).execute(
        "location-1"
    )

    assert len(history_repo.snapshots) == 2
    assert all(isinstance(snapshot, UsageLocationHistory) for snapshot in history_repo.snapshots)
    assert history_repo.snapshots[0].status is UsageLocationStatus.INACTIVE
    assert history_repo.snapshots[1].status is UsageLocationStatus.ACTIVE
    assert history_repo.snapshots[0].location_id == "location-1"


def test_assignment_and_quantity_history_keep_decimal_and_optional_values():
    history_repo = FakeHistoryRepository()
    location = UsageLocation("location-1", "Mixing line")
    assignment_repo = FakeProductUsageLocationRepository()

    AssignProductUsageLocation(
        assignment_repo,
        FakeUsageLocationRepository(location),
        history_repo,
    ).execute(
        AssignProductUsageLocationInput(
            product_id="product-1",
            location_id="location-1",
            peak_quantity_value=Decimal("0"),
            peak_quantity_unit="kg",
            monthly_consumption_value=None,
            monthly_consumption_unit=None,
        )
    )
    UpdateProductUsageLocation(assignment_repo, history_repo).execute(
        UpdateProductUsageLocationInput(
            product_id="product-1",
            location_id="location-1",
            peak_quantity_value=Decimal("4.5"),
            peak_quantity_unit="kg",
            monthly_consumption_value=Decimal("0"),
            monthly_consumption_unit="l",
        )
    )

    assert len(history_repo.snapshots) == 2
    assignment_snapshot, quantity_snapshot = history_repo.snapshots
    assert isinstance(assignment_snapshot, ProductUsageLocationHistory)
    assert assignment_snapshot.peak_quantity_value == Decimal("0")
    assert assignment_snapshot.monthly_consumption_value is None
    assert quantity_snapshot.peak_quantity_value == Decimal("4.5")
    assert quantity_snapshot.monthly_consumption_value == Decimal("0")
    assert quantity_snapshot.monthly_consumption_unit == "l"
