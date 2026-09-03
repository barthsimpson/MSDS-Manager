from dataclasses import asdict, dataclass
from decimal import Decimal

import pytest

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.presentation.streamlit import product_registry


@dataclass
class FakeComposition:
    products: tuple[ProductListItem, ...]
    details_by_id: dict[str, ProductDetails]
    selected_product_id: str
    requested_ids: list[str]

    def get_product_details(self, product_id: str) -> ProductDetails:
        self.requested_ids.append(product_id)
        return self.details_by_id[product_id]

    def list_usage_locations(self):
        return []


def make_product(product_id: str, manufacturer_name: str) -> ProductListItem:
    return ProductListItem(
        product_id=product_id,
        product_name="Solvent",
        manufacturer_product_code=f"CODE-{product_id}",
        manufacturer_id=f"manufacturer-{product_id}",
        manufacturer_name=manufacturer_name,
        usage_status=ProductUsageStatus.ACTIVE,
        use_description="Czyszczenie",
        use_restriction="Wentylowane pomieszczenie",
        waste_type=None,
        waste_code=None,
    )


def make_details(product: ProductListItem) -> ProductDetails:
    return ProductDetails(
        **asdict(product),
        usage_locations=(
            ProductUsageLocationDetails(
                location_id="location-a",
                location_name="Linia A",
                location_status=UsageLocationStatus.ACTIVE,
                peak_quantity_value=Decimal("0"),
                peak_quantity_unit="kg",
                monthly_consumption_value=None,
                monthly_consumption_unit="l/month",
            ),
            ProductUsageLocationDetails(
                location_id="location-b",
                location_name="Magazyn B",
                location_status=UsageLocationStatus.INACTIVE,
                peak_quantity_value=Decimal("12.50"),
                peak_quantity_unit="l",
                monthly_consumption_value=Decimal("0"),
                monthly_consumption_unit="kg/month",
            ),
        ),
    )


def test_product_registry_uses_product_id_and_renders_all_location_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = make_product("product-1", "Manufacturer A")
    second = make_product("product-2", "Manufacturer B")
    composition = FakeComposition(
        products=(first, second),
        details_by_id={second.product_id: make_details(second)},
        selected_product_id=second.product_id,
        requested_ids=[],
    )
    dataframes: list[list[dict[str, str]]] = []
    text_values: list[str] = []

    def capture_dataframe(data, **_kwargs) -> None:
        dataframes.append(data)

    monkeypatch.setattr(product_registry.st, "header", lambda _: None)
    monkeypatch.setattr(product_registry.st, "subheader", lambda _: None)
    monkeypatch.setattr(product_registry.st, "text", text_values.append)
    monkeypatch.setattr(product_registry.st, "dataframe", capture_dataframe)
    monkeypatch.setattr(
        product_registry.st,
        "selectbox",
        lambda _label, options, format_func: (
            assert_product_options(options, format_func, composition.selected_product_id)
        ),
    )

    product_registry.render_product_registry(composition)

    assert composition.requested_ids == ["product-2"]
    assert dataframes[1] == [
        {
            "Lokalizacja": "Linia A",
            "Status lokalizacji": "ACTIVE",
            "Peak wartość": "0",
            "Peak jednostka": "kg",
            "Monthly wartość": "Brak danych",
            "Monthly jednostka": "l/month",
        },
        {
            "Lokalizacja": "Magazyn B",
            "Status lokalizacji": "INACTIVE",
            "Peak wartość": "12.50",
            "Peak jednostka": "l",
            "Monthly wartość": "0",
            "Monthly jednostka": "kg/month",
        },
    ]
    assert "Producent: Manufacturer B" in text_values
    assert "Status użytkowania: ACTIVE" in text_values


def assert_product_options(
    options: list[str], format_func, selected_product_id: str
) -> str:
    assert options == ["product-1", "product-2"]
    assert format_func("product-1").startswith("Solvent")
    return selected_product_id