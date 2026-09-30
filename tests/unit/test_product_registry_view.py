from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

import pytest
from streamlit.testing.v1 import AppTest

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    SupervisoryProductRow,
)
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus, UnitCategory, UnitStatus, UsageLocationStatus
from app.domain.models import UnitOfMeasure
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

    def list_active_units(self):
        return active_units()

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


def unit_id(code: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"msds-manager/unit-of-measure/{code}"))


def active_units() -> tuple[UnitOfMeasure, ...]:
    return (
        UnitOfMeasure(unit_id("kg"), "kg", "kilogram", UnitCategory.MASS, UnitStatus.ACTIVE),
        UnitOfMeasure(unit_id("l"), "l", "litr", UnitCategory.VOLUME, UnitStatus.ACTIVE),
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
                monthly_consumption_unit=None,
                peak_quantity_unit_id=unit_id("kg"),
            ),
            ProductUsageLocationDetails(
                location_id="location-b",
                location_name="Magazyn B",
                location_status=UsageLocationStatus.INACTIVE,
                peak_quantity_value=Decimal("12.50"),
                peak_quantity_unit="l",
                monthly_consumption_value=Decimal("0"),
                monthly_consumption_unit="kg",
                peak_quantity_unit_id=unit_id("l"),
                monthly_consumption_unit_id=unit_id("kg"),
            ),
        ),
    )


def _app(composition: FakeComposition):
    def render(current_composition):
        from app.presentation.streamlit.product_registry import render_product_registry

        render_product_registry(current_composition)

    app = AppTest.from_function(render, args=(composition,))
    app.default_timeout = 10
    return app


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
        "Produkt", "Kod producenta", "Producent", "Status", "SDS", "Rewizja SDS", "BHP"
    ]
    assert "product_id" not in app.dataframe[0].value.columns
    assert app.dataframe[0].value["Rewizja SDS"].tolist() == ["—", "—"]
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
            "Jednostka zużycia": "kg",
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


@pytest.mark.parametrize("revision, expected", [("2", "2"), (None, "—")])
def test_registry_presents_existing_sds_bhp_and_preserves_domain_status(
    monkeypatch: pytest.MonkeyPatch, revision: str | None, expected: str,
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
        current_sds_revision=revision,
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
        "SDS": "CURRENT", "Rewizja SDS": expected, "BHP": "Zatwierdzona",
    }]
    assert "sds-id" not in app.dataframe[0].value.to_string()
    assert product.usage_status is ProductUsageStatus.ACTIVE


@pytest.mark.parametrize("uploaded", [False, True])
@pytest.mark.parametrize("document_date", [None, date(2026, 2, 3)])
@pytest.mark.parametrize("document_revision", [None, "2.0"])
def test_revision_action_passes_selected_product_id(
    monkeypatch: pytest.MonkeyPatch, document_date: date | None,
    document_revision: str | None, uploaded: bool,
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
        def file_uploader(_label: str, **_kwargs):
            return SimpleNamespace(name="local.pdf", getvalue=lambda: b"%PDF-1.4\n") if uploaded else None

        @staticmethod
        def caption(_message: str) -> None:
            pass

        @staticmethod
        def selectbox(_label: str, options, **_kwargs):
            return options[0]

        @staticmethod
        def text_input(label: str, *_args, **_kwargs) -> str:
            assert label == "Rewizja SDS"
            return document_revision or ""

        @staticmethod
        def date_input(label: str, **kwargs) -> date | None:
            assert label == "Data wydania / rewizji SDS"
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
            self.imported = None

        @staticmethod
        def list_sds_files() -> tuple[str, ...]:
            return ("revisions/new.pdf",)

        def accept_sds_revision(self, data) -> str:
            self.accepted = data
            return "new-sds-id"

        def import_sds_revision(self, data, filename, contents) -> str:
            self.imported = (data, filename, contents)
            return "new-sds-id"

    composition = RevisionComposition()
    monkeypatch.setattr(product_registry, "st", FakeStreamlit())

    product = make_product("existing-product", "Manufacturer")
    current_sds = SimpleNamespace(
        current_sds_id="sds-1", current_sds_filename="current.pdf",
        current_sds_revision="1",
    )
    product_registry._render_revision(composition, make_details(product), current_sds)

    accepted = composition.imported[0] if uploaded else composition.accepted
    assert accepted is not None
    assert accepted.product_id == "existing-product"
    assert accepted.source_relative_path == "revisions/new.pdf"
    assert accepted.issue_date == document_date
    assert accepted.revision == document_revision
    if uploaded:
        assert composition.imported[1:] == ("local.pdf", b"%PDF-1.4\n")
        assert composition.accepted is None
    assert "Produkt: Solvent" in FakeStreamlit.shown_text
    assert "Aktualny SDS: current.pdf; rewizja SDS: 1" in FakeStreamlit.shown_text
    assert FakeStreamlit.messages == [
        "Nowa rewizja została zapisana. Produkt oczekuje na decyzję BHP."
    ]


def test_revision_app_shows_upload_without_existing_sds_files() -> None:
    product = make_product("existing-product", "Manufacturer")

    class RevisionComposition:
        @staticmethod
        def list_sds_files() -> tuple[str, ...]:
            return ()

    def render(composition, details) -> None:
        from app.presentation.streamlit.product_registry import _render_revision

        _render_revision(composition, details)

    app = AppTest.from_function(render, args=(RevisionComposition(), make_details(product))).run()
    app.button(key="add-revision-existing-product").click().run()

    assert app.exception == []
    assert app.file_uploader[0].label == "Wybierz plik PDF z komputera"
    assert app.button(key="save-revision-existing-product")


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

        def list_active_units(self):
            return active_units()

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
    assert set(app.selectbox(key="add-location-p1-peak-unit").options) == {"kg", "l"}
    assert "add-location-p1-peak-unit" not in {item.key for item in app.text_input}
    app.selectbox(key="add-location-p1-peak-unit").set_value("l")
    app.checkbox(key="add-location-p1-monthly-enabled").check().run()
    app.text_input(key="add-location-p1-monthly").set_value("0")
    app.selectbox(key="add-location-p1-monthly-unit").set_value("l")
    app.button(key="assign-p1").click().run()
    assert not app.exception
    assert composition.assigned.product_id == "p1"
    assert composition.assigned.location_id == "location-c"
    assert composition.assigned.peak_quantity_value == Decimal("25")
    assert composition.assigned.peak_quantity_unit_id == unit_id("l")
    assert composition.assigned.monthly_consumption_value == Decimal("0")
    assert composition.assigned.monthly_consumption_unit_id == unit_id("l")

    app.button(key="edit-location-p1").click().run()
    assert not app.exception
    assert "Dodaj miejsce stosowania" not in {item.value for item in app.subheader}
    assert app.text_input(key="edit-location-p1-location-b-peak").value == "12.50"
    assert set(app.selectbox(key="edit-location-p1-location-b-peak-unit").options) == {"kg", "l"}
    app.button(key="quantity-p1-location-b").click().run()
    assert not app.exception
    assert composition.updated.product_id == "p1"
    assert composition.updated.location_id == "location-b"
    assert composition.updated.monthly_consumption_value == Decimal("0")
    assert composition.updated.peak_quantity_unit_id == unit_id("l")
    assert composition.updated.monthly_consumption_unit_id == unit_id("kg")


def test_add_requires_selected_units_and_preserves_empty_monthly():
    details = ProductDetails(**asdict(make_product("p2", "Manufacturer")), usage_locations=())

    class Composition:
        assigned = None

        def list_usage_locations(self):
            return [SimpleNamespace(
                location_id="location-c", location_name="Hala C",
                status=UsageLocationStatus.ACTIVE,
            )]

        def list_active_units(self):
            return active_units()

        def assign_product_usage_location(self, data):
            self.assigned = data

    composition = Composition()

    def render(current_composition, current_details):
        from app.presentation.streamlit.product_registry import _render_product_operations
        _render_product_operations(current_composition, current_details, None)

    app = AppTest.from_function(render, args=(composition, details))
    app.default_timeout = 10
    app.run().button(key="add-location-p2").click().run()
    assert app.selectbox(key="add-location-p2-peak-unit").value is None
    assert all(str(unit_id("kg")) not in option for option in
               app.selectbox(key="add-location-p2-peak-unit").options)
    app.button(key="assign-p2").click().run()
    assert composition.assigned is None
    assert "Jednostka maksymalnej ilości" in app.error[0].value

    app.selectbox(key="add-location-p2-peak-unit").set_value("kg").run()
    app.checkbox(key="add-location-p2-monthly-enabled").check().run()
    app.text_input(key="add-location-p2-monthly").set_value("0")
    app.button(key="assign-p2").click().run()
    assert composition.assigned is None
    assert "Jednostka zużycia miesięcznego" in app.error[0].value

    app.checkbox(key="add-location-p2-monthly-enabled").uncheck().run()
    app.button(key="assign-p2").click().run()
    assert composition.assigned.peak_quantity_unit_id == unit_id("kg")
    assert composition.assigned.monthly_consumption_value is None
    assert composition.assigned.monthly_consumption_unit_id is None


def test_inactive_existing_unit_is_readable_but_not_editable():
    product = make_product("p3", "Manufacturer")
    inactive_location = replace(
        make_details(product).usage_locations[0],
        peak_quantity_unit="g",
        peak_quantity_unit_id=unit_id("g"),
    )
    details = ProductDetails(**asdict(product), usage_locations=(inactive_location,))

    class Composition:
        updated = None

        def list_active_units(self):
            return active_units()

        def update_product_usage_location(self, data):
            self.updated = data

    composition = Composition()
    selection = SimpleNamespace(selection=SimpleNamespace(rows=[0]))

    def render(current_composition, current_details, current_selection):
        from app.presentation.streamlit.product_registry import _render_product_operations
        _render_product_operations(current_composition, current_details, current_selection)

    app = AppTest.from_function(render, args=(composition, details, selection))
    app.default_timeout = 10
    app.run().button(key="edit-location-p3").click().run()
    peak = app.selectbox(key="edit-location-p3-location-a-peak-unit")
    assert peak.options == ["kg", "l"]
    assert peak.value is None
    app.button(key="quantity-p3-location-a").click().run()
    assert composition.updated is None
    assert "Jednostka maksymalnej ilości" in app.error[0].value
    app.selectbox(key="edit-location-p3-location-a-peak-unit").set_value("kg").run()
    app.button(key="quantity-p3-location-a").click().run()
    assert composition.updated.peak_quantity_unit_id == unit_id("kg")
    assert product_registry._location_row(inactive_location)["Jednostka"] == "g"
