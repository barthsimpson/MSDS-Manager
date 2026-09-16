from dataclasses import replace
from datetime import date
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from app.application.dto import SupervisoryProductRow
from app.application.exceptions import SupervisoryReadError
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus
from app.presentation.streamlit.supervisory import READ_ERROR_MESSAGE
from app.presentation.streamlit.composition import ShellInitializationError


@pytest.fixture
def row():
    return SupervisoryProductRow(
        product_id="p1", product_name="Produkt A", manufacturer_name="Producent A",
        manufacturer_product_code="A-1", usage_status=ProductUsageStatus.ACTIVE,
        use_description="", use_restriction="", usage_locations=("Hala A",),
        current_sds_id="s1", current_sds_filename="sds.pdf",
        current_sds_issue_date=date(2026, 1, 2), current_sds_revision="2",
        current_sds_file_available=True, current_bhp_decision_id="b1",
        current_bhp_decision_status=BhpDecisionStatus.APPROVED,
        current_bhp_registered_at=None, current_bhp_notes="Stosować wentylację.",
        current_bhp_evidence_relative_path="approved.pdf",
        current_bhp_evidence_available=True,
    )


def app_for(rows=(), error=None):
    def render(composition):
        from app.presentation.streamlit.supervisory import render_supervisory
        render_supervisory(composition)

    composition = Mock(spec=["list_supervisory_products"])
    composition.list_supervisory_products.return_value = rows
    composition.list_supervisory_products.side_effect = error
    app = AppTest.from_function(render, args=(composition,), default_timeout=10).run()
    assert not app.exception
    return app


def test_complete_active_row_and_read_only_controls(row):
    app = app_for([row])
    assert len(app.dataframe) == 1
    assert app.dataframe[0].value.to_dict("records") == [{
        "Produkt": "Produkt A", "Producent": "Producent A", "Kod producenta": "A-1",
        "Miejsca stosowania": "Hala A", "SDS": "CURRENT", "Data SDS": "2026-01-02",
        "Rewizja SDS": "2", "Status produktu": "ACTIVE", "BHP": "APPROVED",
        "Warunki / uwagi": "Stosować wentylację.", "Wymaga działania": "OK",
    }]
    assert len(app.selectbox) == 3
    assert not app.button
    assert not app.text_input
    assert not app.get("file_uploader")
    assert not app.get("download_button")


@pytest.mark.parametrize("reasons", [
    ("BRAK DECYZJI BHP",),
    ("BRAK DECYZJI BHP", "BRAK MIEJSCA STOSOWANIA", "BRAK PLIKU SDS"),
])
def test_action_reasons_are_displayed_without_recalculation(row, reasons):
    app = app_for([replace(row, requires_action=True, action_reasons=reasons)])
    assert app.dataframe[0].value.iloc[0]["Wymaga działania"] == "; ".join(reasons)


def test_multiple_locations_remain_one_row(row):
    app = app_for([replace(row, usage_locations=("Hala A", "Hala B"))])
    assert len(app.dataframe[0].value) == 1
    assert app.dataframe[0].value.iloc[0]["Miejsca stosowania"] == "Hala A; Hala B"


@pytest.mark.parametrize("key,value", [
    ("supervisory-action", "Wymagają działania"),
    ("supervisory-status", ProductUsageStatus.INACTIVE),
    ("supervisory-location", "Hala B"),
])
def test_filters(row, key, value):
    other = replace(row, product_id="p2", product_name="Produkt B",
                    usage_status=ProductUsageStatus.INACTIVE,
                    usage_locations=("Hala A", "Hala B"),
                    requires_action=True, action_reasons=("BRAK PLIKU SDS",))
    app = app_for([row, other])
    app.selectbox(key=key).set_value(value).run()
    assert not app.exception
    assert app.dataframe[0].value["Produkt"].tolist() == ["Produkt B"]


def test_combined_filters_and_reset(row):
    app = app_for([row])
    app.selectbox(key="supervisory-location").set_value("Hala A")
    app.selectbox(key="supervisory-status").set_value(ProductUsageStatus.INACTIVE).run()
    assert not app.dataframe
    assert app.info[0].value == "Brak produktów spełniających wybrane filtry."
    app.selectbox(key="supervisory-status").set_value(None).run()
    assert len(app.dataframe[0].value) == 1


def test_empty_database():
    app = app_for()
    assert app.info[0].value == "Brak produktów do wyświetlenia."
    assert not app.error
    assert not app.dataframe


@pytest.mark.parametrize("error_type", [SupervisoryReadError, ShellInitializationError])
def test_controlled_error(error_type):
    app = app_for(error=error_type("private technical details"))
    assert app.error[0].value == READ_ERROR_MESSAGE
    assert not app.dataframe
    assert not app.button


@pytest.mark.parametrize("changes,expected_sds,expected_bhp", [
    ({"current_sds_id": None, "current_sds_file_available": False,
      "current_bhp_decision_id": None, "current_bhp_decision_status": None},
     "BRAK CURRENT SDS", "BRAK DECYZJI"),
    ({"current_sds_file_available": False,
      "current_bhp_decision_status": BhpDecisionStatus.REJECTED},
     "BRAK PLIKU SDS", "REJECTED"),
])
def test_missing_values_and_status_formatting(row, changes, expected_sds, expected_bhp):
    app = app_for([replace(row, **changes, usage_locations=(), current_bhp_notes=None,
                           current_sds_issue_date=None, current_sds_revision=None)])
    values = app.dataframe[0].value.iloc[0]
    assert values["SDS"] == expected_sds
    assert values["BHP"] == expected_bhp
    for column in ("Miejsca stosowania", "Warunki / uwagi", "Data SDS", "Rewizja SDS"):
        assert values[column] == "—"
