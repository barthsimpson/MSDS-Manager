"""AppTest coverage of the TASK-042 dashboard without operator data writes."""

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from streamlit.testing.v1 import AppTest

from app.application.dto.analytics import (
    AnalyticsBhpStatus as Bhp, AnalyticsDashboardDto, AnalyticsFileAvailability,
    AnalyticsKpiDto,
    AttentionSummaryDto, BhpStatusDistributionDto, ManufacturerSummaryRow,
    ProductAnalyticsFact, ProductLocationAnalyticsRow, SdsTrendPoint,
)
from app.domain.enums import ProductUsageStatus, UsageLocationStatus
from app.presentation.streamlit.composition import ShellInitializationError


MANUFACTURER_ID = "d60b317a-f0e1-4f62-b8fa-01f185390913"
LOCATION_ID = "287af288-51e8-4304-949e-99abdb5d56a9"


def _dashboard(empty=False):
    facts = () if empty else (ProductAnalyticsFact(
        product_id="hidden-product-id", product_name="Lakier",
        usage_status=ProductUsageStatus.ACTIVE,
        manufacturer_id=MANUFACTURER_ID, manufacturer_name="Producent A",
        has_current_sds=True, current_sds_id="hidden-sds-id",
        current_sds_original_filename="source.pdf",
        current_sds_relative_path="source.pdf",
        current_sds_registered_at=datetime(2026, 9, 4),
        bhp_category=Bhp.APPROVED, current_bhp_decision_id="hidden-decision-id",
        current_evidence_id="hidden-evidence-id",
        current_evidence_original_filename="decision.pdf",
        current_evidence_relative_path="decision.pdf",
        active_location_count=1, has_active_location=True,
        latest_sds_registered_at=datetime(2026, 9, 4),
    ),)
    return AnalyticsDashboardDto(
        product_facts=facts,
        kpi=AnalyticsKpiDto(0, 0, 0, 0, 0) if empty else AnalyticsKpiDto(1, 1, 1, 0, 1),
        bhp_status=BhpStatusDistributionDto(0, 0, 0) if empty else
                   BhpStatusDistributionDto(1, 0, 0),
        sds_trend=() if empty else (SdsTrendPoint(date(2026, 9, 1), 1, 0),),
        manufacturer_summary=() if empty else (ManufacturerSummaryRow(
            manufacturer_id=MANUFACTURER_ID, manufacturer_name="Producent A",
            products_count=1, current_sds_count=1, bhp_approved_count=1,
            attention_products_count=0,
            latest_sds_registered_at=datetime(2026, 9, 4),
        ),),
        attention=AttentionSummaryDto(0, 0, 0, 0, {}),
    )


class FakeComposition:
    def __init__(self, *, empty=False, error=False, check_failed=False):
        self.empty = empty
        self.error = error
        self.check_failed = check_failed
        self.filters = []
        self.detail_calls = []

    def list_manufacturers(self):
        return [SimpleNamespace(manufacturer_id=MANUFACTURER_ID,
                                manufacturer_name="Producent A")]

    def list_usage_locations(self):
        return [
            SimpleNamespace(location_id=LOCATION_ID, location_name="Hala A",
                            status=UsageLocationStatus.ACTIVE),
            SimpleNamespace(location_id="376b03d7-bc61-4885-8952-df21d61c89fd",
                            location_name="Nieaktywna", status=UsageLocationStatus.INACTIVE),
        ]

    def get_analytics_dashboard(self, filters):
        self.filters.append(filters)
        if self.error:
            raise ShellInitializationError("secret postgresql path")
        dashboard = _dashboard(self.empty)
        if self.check_failed:
            dashboard = replace(dashboard, product_facts=(replace(
                dashboard.product_facts[0],
                current_sds_availability=AnalyticsFileAvailability.CHECK_FAILED,
            ),))
        return dashboard

    def list_analytics_product_locations(self, filters):
        self.detail_calls.append(filters)
        return [ProductLocationAnalyticsRow(
            product_id="hidden-product-id", product_name="Lakier",
            manufacturer_name="Producent A", location_id=LOCATION_ID,
            location_name="Hala A", peak_quantity_value=Decimal("0"),
            peak_quantity_unit_code="kg", monthly_consumption_value=Decimal("0"),
            monthly_consumption_unit_code="kg",
            product_usage_status=ProductUsageStatus.ACTIVE,
            current_sds_revision="2", current_sds_issue_date=date(2026, 8, 1),
            bhp_category=Bhp.APPROVED,
        ), ProductLocationAnalyticsRow(
            product_id="hidden-other-id", product_name="Bez stanowiska",
            manufacturer_name="Producent A", location_id=None,
            location_name=None, peak_quantity_value=None,
            peak_quantity_unit_code=None, monthly_consumption_value=None,
            monthly_consumption_unit_code=None,
            product_usage_status=ProductUsageStatus.PENDING_APPROVAL,
            current_sds_revision=None, current_sds_issue_date=None,
            bhp_category=Bhp.NO_DECISION,
        )]


def _app(composition):
    def render(composition):
        from app.presentation.streamlit.analytics import render_analytics
        render_analytics(composition)

    app = AppTest.from_function(render, args=(composition,), default_timeout=10).run()
    assert not app.exception
    return app


def test_dashboard_cards_charts_filters_and_local_navigation():
    composition = FakeComposition()
    app = _app(composition)
    assert app.header[0].value == "Analizy"
    assert app.subheader[0].value == "Dashboard"
    assert [app.button(key=f"analytics-view-{name}").label for name in (
        "Dashboard", "Zestawienie zbiorcze", "Raport przeglądu"
    )] == ["Dashboard", "Zestawienie zbiorcze", "Raport przeglądu"]
    assert app.button(key="analytics-view-Dashboard").proto.type == "secondary"
    scoped_style = app.markdown[0].value
    assert ".st-key-analytics-nav-active button" in scoped_style
    assert "background: #e9eef5" in scoped_style
    assert "font-size: 1.02rem" in scoped_style
    assert "height: 2.25rem" in scoped_style
    assert not any(item.value == "**Filtry**" for item in app.markdown)
    assert len(app.date_input) == 1
    assert app.date_input[0].label == "Okres SDS"
    assert [item.label for item in app.selectbox] == [
        "Producent", "SDS", "BHP", "Lokalizacja",
    ]
    assert [
        next(item.label for item in column.children.values() if hasattr(item, "label"))
        for column in app.get("column")[3:8]
    ] == ["Okres SDS", "Producent", "SDS", "BHP", "Lokalizacja"]
    assert app.selectbox(key="analytics-sds").options == [
        "Wszystkie", "Ma CURRENT SDS", "Brak CURRENT SDS",
    ]
    assert app.selectbox(key="analytics-bhp").options == [
        "Wszystkie", "Dopuszczony", "Odrzucony", "Brak decyzji",
    ]
    assert not any(button.label == "Eksport" for button in app.button)
    assert len(app.get("vega_lite_chart")) == 3
    assert len([m for m in app.markdown if '<div class="analytics-kpi">' in m.value]) == 5
    assert len([m for m in app.markdown if '<div class="analytics-attention">' in m.value]) == 4
    assert app.dataframe[0].value["Ostatni SDS"].tolist() == ["2026-09-04"]
    assert composition.detail_calls == []
    assert not app.get("expander")
    assert not any(button.label == "Pokaż zestawienie szczegółowe" for button in app.button)
    assert "hidden-product-id" not in " ".join(item.value for item in app.markdown)

    app.selectbox(key="analytics-manufacturer").set_value(
        composition.list_manufacturers()[0]
    )
    app.selectbox(key="analytics-sds").set_value("Ma CURRENT SDS")
    app.selectbox(key="analytics-bhp").set_value("Dopuszczony")
    app.selectbox(key="analytics-location").set_value(composition.list_usage_locations()[0]).run()
    assert not app.exception
    selected = composition.filters[-1]
    assert selected.manufacturer_id == UUID(MANUFACTURER_ID)
    assert selected.usage_location_id == UUID(LOCATION_ID)
    assert selected.sds_status.value == "CURRENT_PRESENT"
    assert selected.bhp_status == Bhp.APPROVED

    earlier_kpis = [m.value for m in app.markdown if '<div class="analytics-kpi">' in m.value]
    app.date_input(key="analytics-date-range").set_value(
        (date(2025, 1, 1), date(2025, 12, 31))
    ).run()
    assert [m.value for m in app.markdown if '<div class="analytics-kpi">' in m.value] == earlier_kpis
    assert composition.filters[-1].trend_date_from == date(2025, 1, 1)
    assert composition.filters[-1].trend_date_to == date(2025, 12, 31)

    dashboard_reads = len(composition.filters)
    app.button(key="analytics-view-Zestawienie zbiorcze").click().run()
    assert app.subheader[0].value == "Zestawienie zbiorcze"
    assert app.button(key="analytics-view-Zestawienie zbiorcze").proto.type == "secondary"
    assert len(app.date_input) == 1
    assert [app.date_input[0].label, *[item.label for item in app.selectbox]] == [
        "Okres SDS", "Producent", "SDS", "BHP", "Lokalizacja",
    ]
    assert not any(button.label == "Eksport" for button in app.button)
    assert len(composition.filters) == dashboard_reads
    assert len(composition.detail_calls) == 1
    assert composition.detail_calls[-1].trend_date_from == date(2025, 1, 1)
    assert composition.detail_calls[-1].trend_date_to == date(2025, 12, 31)
    assert len(app.dataframe) == 1
    assert not app.get("vega_lite_chart")
    assert app.dataframe[0].value["MAX"].tolist() == ["0 kg", "—"]
    assert app.dataframe[0].value["Miesięczne zużycie"].tolist() == ["0 kg", "—"]
    assert app.dataframe[0].value["SDS / rewizja"].tolist() == ["Rewizja 2 · 2026-08-01", "—"]
    assert app.dataframe[0].value["Lokalizacja"].tolist() == ["Hala A", "Brak"]

    app.selectbox(key="analytics-location").set_value("no-active").run()
    assert composition.detail_calls[-1].include_no_active_location is True
    assert composition.detail_calls[-1].usage_location_id is None

    reads_before = len(composition.filters)
    app.date_input(key="analytics-date-range").set_value((date(2025, 1, 1),)).run()
    assert app.info[0].value == "Wybierz początek i koniec okresu SDS."
    assert len(composition.filters) == reads_before

    app.button(key="analytics-view-Raport przeglądu").click().run()
    assert app.subheader[0].value == "Raport przeglądu"
    assert app.info[0].value == "Funkcja zostanie uruchomiona w kolejnym etapie."
    assert not any(button.label == "Eksport" for button in app.button)
    assert not app.dataframe
    assert not app.get("vega_lite_chart")
    assert len(composition.filters) == reads_before
    assert len(composition.detail_calls) == 2  # date change reran the detail view

    app.button(key="analytics-view-Dashboard").click().run()
    assert app.subheader[0].value == "Dashboard"
    assert len(app.get("vega_lite_chart")) == 3


def test_empty_and_controlled_error_states():
    app = _app(FakeComposition(empty=True))
    assert any(item.value == "Brak produktów dla wybranych filtrów." for item in app.info)
    assert any(item.value == "Brak zarejestrowanych SDS w wybranym okresie."
               for item in app.info)
    assert any(item.value == "Brak danych do podsumowania." for item in app.info)
    assert not app.get("vega_lite_chart")
    assert not app.dataframe

    app = _app(FakeComposition(check_failed=True))
    assert any(item.value == "Dostępności części dokumentów nie udało się sprawdzić."
               for item in app.caption)
    assert any('<div class="analytics-attention-value">0</div>' in item.value
               for item in app.markdown)

    app = _app(FakeComposition(error=True))
    assert app.error[0].value == "Nie udało się odczytać danych analitycznych. Spróbuj ponownie."
    assert "secret" not in app.error[0].value
    assert not app.get("vega_lite_chart")
