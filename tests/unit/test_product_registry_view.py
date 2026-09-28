from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    SupervisoryProductRow,
)
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus, UsageLocationStatus
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

    def list_supervisory_products(self):
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


def _app(composition: FakeComposition):
    def render(current_composition):
        from app.presentation.streamlit.product_registry import render_product_registry

        render_product_registry(current_composition)

    return AppTest.from_function(render, args=(composition,))


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
    real_dataframe = product_registry.st.dataframe

    def select_second_row(data, **kwargs):
        result = real_dataframe(data, **kwargs)
        if kwargs.get("key") == "product-registry":
            return SimpleNamespace(selection=SimpleNamespace(rows=[1]))
        return result

    monkeypatch.setattr(product_registry.st, "dataframe", select_second_row)
    app = _app(composition).run()

    assert app.exception == []
    assert composition.requested_ids == ["product-2"]
    assert app.dataframe[0].value.columns.tolist() == [
        "Produkt", "Kod producenta", "Producent", "Status", "SDS", "BHP"
    ]
    assert "product_id" not in app.dataframe[0].value.columns
    assert app.dataframe[1].value.to_dict("records") == [
        {
            "Lokalizacja": "Linia A",
            "Maksymalna ilość": "0",
            "Jednostka": "kg",
            "Zużycie miesięczne": "—",
            "Jednostka zużycia": "—",
        },
        {
            "Lokalizacja": "Magazyn B",
            "Maksymalna ilość": "12.50",
            "Jednostka": "l",
            "Zużycie miesięczne": "0",
            "Jednostka zużycia": "kg/month",
        },
    ]
    assert any(item.value == "Producent: Manufacturer B" for item in app.text)
    assert any(item.value == "Status użytkowania: Aktywny" for item in app.text)
    assert {"Edytuj dane produktu", "Dodaj nową rewizję SDS", "Usuń produkt"}.issubset(
        {button.label for button in app.button}
    )


def test_registry_empty_and_no_selection_have_controlled_states() -> None:
    empty = FakeComposition((), {}, "", [])
    app = _app(empty).run()
    assert app.exception == []
    assert app.info[0].value == "Brak produktów w rejestrze."
    assert not app.dataframe

    product = make_product("product-1", "Manufacturer")
    composition = FakeComposition((product,), {}, "", [])
    app = _app(composition).run()
    assert app.exception == []
    assert app.info[0].value.startswith("Wybierz produkt w tabeli")
    assert composition.requested_ids == []


def test_registry_presents_existing_sds_bhp_and_preserves_domain_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = make_product("product-1", "Manufacturer")
    row = SupervisoryProductRow(
        product_id=product.product_id,
        product_name=product.product_name,
        manufacturer_name=product.manufacturer_name,
        manufacturer_product_code=product.manufacturer_product_code,
        usage_status=product.usage_status,
        use_description=product.use_description,
        use_restriction=product.use_restriction,
        usage_location_name=None, peak_quantity_value=None, peak_quantity_unit=None,
        monthly_consumption_value=None, monthly_consumption_unit=None,
        current_sds_id="sds-id",
        current_sds_filename="current.pdf",
        current_sds_issue_date=None,
        current_sds_revision="2",
        current_sds_file_available=True,
        current_bhp_decision_id="decision-id",
        current_bhp_decision_status=BhpDecisionStatus.APPROVED,
        current_bhp_registered_at=None,
        current_bhp_notes=None,
        current_bhp_evidence_relative_path=None,
        current_bhp_evidence_available=False,
    )
    composition = FakeComposition((product,), {}, "", [])
    monkeypatch.setattr(composition, "list_supervisory_products", lambda: [row])
    app = _app(composition).run()

    assert app.exception == []
    assert app.dataframe[0].value.to_dict("records") == [{
        "Produkt": "Solvent", "Kod producenta": "CODE-product-1",
        "Producent": "Manufacturer", "Status": "Aktywny",
        "SDS": "CURRENT", "BHP": "Zatwierdzona",
    }]
    assert product.usage_status is ProductUsageStatus.ACTIVE


@pytest.mark.parametrize("document_date", [None, date(2026, 2, 3)])
def test_revision_action_passes_selected_product_id(
    monkeypatch: pytest.MonkeyPatch, document_date: date | None
) -> None:
    class FakeStreamlit:
        session_state = {}
        messages = []
        shown_text = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        @staticmethod
        def button(label: str, **_kwargs) -> bool:
            return label in {"Dodaj nową rewizję SDS", "Zapisz nową rewizję"}

        @staticmethod
        def subheader(_label: str) -> None:
            pass

        @classmethod
        def text(cls, value: str) -> None:
            cls.shown_text.append(value)

        @staticmethod
        def info(_message: str) -> None:
            pass

        @staticmethod
        def selectbox(_label: str, options, **_kwargs):
            return options[0]

        @staticmethod
        def text_input(_label: str, *_args, **_kwargs) -> str:
            return "2.0"

        @staticmethod
        def date_input(_label: str, **kwargs) -> date | None:
            assert kwargs["value"] is None
            return document_date

        @staticmethod
        def columns(_count: int):
            return (FakeStreamlit(), FakeStreamlit())

        @classmethod
        def success(cls, message: str) -> None:
            cls.messages.append(message)

        @staticmethod
        def error(_message: str) -> None:
            raise AssertionError(_message)

        @staticmethod
        def rerun() -> None:
            raise AssertionError("unexpected rerun")

    class RevisionComposition:
        def __init__(self) -> None:
            self.accepted = None

        @staticmethod
        def list_sds_files() -> tuple[str, ...]:
            return ("revisions/new.pdf",)

        def accept_sds_revision(self, data) -> str:
            self.accepted = data
            return "new-sds-id"

    composition = RevisionComposition()
    monkeypatch.setattr(product_registry, "st", FakeStreamlit())

    product = make_product("existing-product", "Manufacturer")
    current_sds = SimpleNamespace(
        current_sds_id="sds-1", current_sds_filename="current.pdf",
        current_sds_revision="1",
    )
    product_registry._render_revision(composition, make_details(product), current_sds)

    assert composition.accepted is not None
    assert composition.accepted.product_id == "existing-product"
    assert composition.accepted.source_relative_path == "revisions/new.pdf"
    assert composition.accepted.issue_date == document_date
    assert "Produkt: Solvent" in FakeStreamlit.shown_text
    assert "Aktualny SDS: current.pdf; rewizja: 1" in FakeStreamlit.shown_text
    assert FakeStreamlit.messages == [
        "Nowa rewizja została zapisana. Produkt oczekuje na decyzję BHP."
    ]


def test_identity_edit_action_passes_selected_product_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeStreamlit:
        session_state = {}

        @staticmethod
        def button(label: str, **_kwargs) -> bool:
            return label in {"Edytuj dane produktu", "Zapisz zmiany"}

        @staticmethod
        def subheader(_label: str) -> None:
            pass

        @staticmethod
        def text_input(label: str, *_args, **_kwargs) -> str:
            return {
                "Nazwa produktu": "Edited product",
                "Kod produktu producenta": "EDITED-1",
                "Producent": "Edited manufacturer",
            }[label]

        @staticmethod
        def columns(_count: int):
            return (FakeStreamlit(), FakeStreamlit())

        @staticmethod
        def success(_message: str) -> None:
            pass

        @staticmethod
        def error(_message: str) -> None:
            raise AssertionError(_message)

        @staticmethod
        def rerun() -> None:
            raise AssertionError("unexpected rerun")

    class IdentityComposition:
        def __init__(self) -> None:
            self.updated = None

        def update_product_identity(self, data) -> None:
            self.updated = data

    composition = IdentityComposition()
    monkeypatch.setattr(product_registry, "st", FakeStreamlit())

    product_registry._render_identity_edit(
        composition, make_details(make_product("existing-product", "Manufacturer"))
    )

    assert composition.updated is not None
    assert composition.updated.product_id == "existing-product"
    assert composition.updated.product_name == "Edited product"


def test_delete_action_requires_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeStreamlit:
        session_state = {}

        @staticmethod
        def button(label: str, **_kwargs) -> bool:
            return label in {"Usuń produkt", "Usuń produkt trwale"}

        @staticmethod
        def warning(message: str) -> None:
            assert "SDS: 0" in message
            assert "decyzje BHP: 0" in message

        @staticmethod
        def checkbox(_label: str, **_kwargs) -> bool:
            return False

        @staticmethod
        def error(message: str) -> None:
            assert "potwierdzenie" in message

    class DeleteComposition:
        def __init__(self) -> None:
            self.deleted = False

        def delete_product(self, _product_id: str) -> None:
            self.deleted = True

    composition = DeleteComposition()
    monkeypatch.setattr(product_registry, "st", FakeStreamlit())

    product_registry._render_delete_product(
        composition, make_details(make_product("existing-product", "Manufacturer"))
    )

    assert composition.deleted is False


def test_usage_assignments_empty_state_and_closed_forms():
    product = make_product("empty", "Manufacturer")
    details = ProductDetails(**asdict(product), usage_locations=())

    class Composition:
        def list_usage_locations(self):
            return []

    def render(current_details, current_composition):
        from app.presentation.streamlit.product_registry import _render_details
        _render_details(current_composition, current_details, None)

    app = AppTest.from_function(render, args=(details, Composition())).run()
    assert not app.exception
    assert any(item.value == "Brak przypisanych miejsc stosowania." for item in app.info)
    assert "+ Dodaj miejsce stosowania" in {button.label for button in app.button}
    assert "Maksymalna ilość na stanowisku" not in {item.label for item in app.text_input}


def test_one_usage_assignment_is_one_table_row():
    details = make_details(make_product("single", "Manufacturer"))
    details = replace(details, usage_locations=details.usage_locations[:1])

    def render(current_details):
        from app.presentation.streamlit.product_registry import _render_details
        _render_details(None, current_details, None)

    app = AppTest.from_function(render, args=(details,)).run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert app.dataframe[0].value["Lokalizacja"].tolist() == ["Linia A"]


def test_add_and_edit_assignment_use_distinct_forms_and_existing_use_cases():
    product = make_product("p1", "Manufacturer")
    details = make_details(product)

    class Composition:
        assigned = None
        updated = None

        def list_usage_locations(self):
            return [SimpleNamespace(location_id="location-c", location_name="Hala C",
                                    status=UsageLocationStatus.ACTIVE)]

        def assign_product_usage_location(self, data):
            self.assigned = data

        def update_product_usage_location(self, data):
            self.updated = data

    composition = Composition()
    selection = SimpleNamespace(selection=SimpleNamespace(rows=[1]))

    def render(current_composition, current_details, current_selection):
        from app.presentation.streamlit.product_registry import _render_product_operations
        _render_product_operations(current_composition, current_details, current_selection)

    app = AppTest.from_function(render, args=(composition, details, selection)).run()
    assert not app.exception
    assert "Maksymalna ilość na stanowisku" not in {item.label for item in app.text_input}
    app.button(key="add-location-p1").click().run()
    assert not app.exception
    assert "Edytuj przypisanie" not in {item.value for item in app.subheader}
    app.text_input(key="add-location-p1-peak").set_value("25")
    app.text_input(key="add-location-p1-peak-unit").set_value("l")
    app.checkbox(key="add-location-p1-monthly-enabled").check().run()
    app.text_input(key="add-location-p1-monthly").set_value("0")
    app.text_input(key="add-location-p1-monthly-unit").set_value("l")
    app.button(key="assign-p1").click().run()
    assert not app.exception
    assert composition.assigned.product_id == "p1"
    assert composition.assigned.location_id == "location-c"
    assert composition.assigned.peak_quantity_value == Decimal("25")
    assert composition.assigned.monthly_consumption_value == Decimal("0")

    app.button(key="edit-location-p1").click().run()
    assert not app.exception
    assert "Dodaj miejsce stosowania" not in {item.value for item in app.subheader}
    assert app.text_input(key="edit-location-p1-location-b-peak").value == "12.50"
    app.button(key="quantity-p1-location-b").click().run()
    assert not app.exception
    assert composition.updated.product_id == "p1"
    assert composition.updated.location_id == "location-b"
    assert composition.updated.monthly_consumption_value == Decimal("0")
