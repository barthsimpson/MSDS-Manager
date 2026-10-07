"""Presentation of the approved current-state analytics dashboard."""

from datetime import date
from decimal import Decimal
from uuid import UUID

import streamlit as st

from app.application.dto.analytics import (
    AnalyticsBhpStatus, AnalyticsDashboardDto, AnalyticsFileAvailability,
    AnalyticsFilters, AnalyticsSdsStatus, ProductLocationAnalyticsRow,
)
from app.application.dto.physical_review import PhysicalReviewDetails, PhysicalReviewSummary
from app.application.use_cases.physical_review import (
    EmptyReviewPopulationError, FinalReviewImmutableError,
    InvalidObservedQuantityError, ReviewAlreadyFinalError,
    ReviewDraftAlreadyExistsError, ReviewNotFoundError,
)
from app.domain.enums import UsageLocationStatus
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError


READ_ERROR_MESSAGE = "Nie udało się odczytać danych analitycznych. Spróbuj ponownie."

SDS_OPTIONS = (
    ("Wszystkie", None),
    ("Ma CURRENT SDS", AnalyticsSdsStatus.CURRENT_PRESENT),
    ("Brak CURRENT SDS", AnalyticsSdsStatus.CURRENT_MISSING),
)
BHP_OPTIONS = (
    ("Wszystkie", None),
    ("Dopuszczony", AnalyticsBhpStatus.APPROVED),
    ("Odrzucony", AnalyticsBhpStatus.REJECTED),
    ("Brak decyzji", AnalyticsBhpStatus.NO_DECISION),
)
PRODUCT_STATUS_LABELS = {
    "ACTIVE": "Aktywny",
    "PENDING_APPROVAL": "Oczekuje na BHP",
    "REJECTED": "Odrzucony",
    "INACTIVE": "Nieaktywny",
}
BHP_LABELS = {
    AnalyticsBhpStatus.APPROVED: "Dopuszczony",
    AnalyticsBhpStatus.REJECTED: "Odrzucony",
    AnalyticsBhpStatus.NO_DECISION: "Brak decyzji",
    AnalyticsBhpStatus.NOT_APPLICABLE_NO_CURRENT_SDS: "Brak CURRENT SDS",
}


def _style() -> None:
    st.markdown("""
<style>
.st-key-analytics-module-head h2 { margin-top: 0; margin-bottom: .1rem; }
.st-key-analytics-nav { margin-top: -.1rem; margin-bottom: .15rem; }
.st-key-analytics-nav button {
  min-height: 2.25rem !important; height: 2.25rem !important;
  padding: .2rem .8rem !important; border-radius: .65rem !important;
  background: #f8fafd !important; border-color: #dbe2eb !important;
  color: #405168 !important;
}
.st-key-analytics-nav button p {
  font-size: 1.02rem !important; font-weight: 500 !important;
  color: inherit !important;
}
.st-key-analytics-nav-active button {
  background: #e9eef5 !important; border-color: #aab8cc !important;
  color: #24364e !important; box-shadow: inset 0 -2px 0 #526985 !important;
}
.st-key-analytics-nav-active button:hover { background: #e2eaf4 !important; }
.st-key-analytics-view-head h3 { margin-top: .1rem; margin-bottom: .05rem; }
.st-key-analytics-view-head [data-testid="stCaptionContainer"] { margin-top: 0; }
.st-key-analytics-filters { margin-bottom: .25rem; }
.st-key-analytics-filters [data-testid="stWidgetLabel"] { margin-bottom: .15rem; }
.analytics-kpi {
  min-height: 112px; padding: 12px 16px; background: #fff;
  border: 1px solid #e7ebf1; border-radius: 16px;
  box-shadow: 0 3px 16px rgba(27, 43, 72, .045);
}
.analytics-kpi-label { color: #536278; font-size: .88rem; font-weight: 600; }
.analytics-kpi-value { color: #18253a; font-size: 1.95rem; font-weight: 720;
  line-height: 1.2; margin-top: 6px; }
.analytics-kpi-note { color: #718096; font-size: .78rem; margin-top: 3px; }
.analytics-attention { padding: 11px 15px; border: 1px solid #e8eaf1;
  border-radius: 14px; background: #fafbfe; min-height: 84px; }
.analytics-attention-label { color: #59667a; font-size: .84rem; }
.analytics-attention-value { color: #28354a; font-size: 1.5rem;
  font-weight: 700; margin-top: 4px; }
.analytics-section-note { color: #768397; font-size: .86rem; }
</style>
""", unsafe_allow_html=True)


def _filters(composition: ShellComposition) -> AnalyticsFilters | None:
    manufacturers = sorted(composition.list_manufacturers(),
                           key=lambda item: (item.manufacturer_name, item.manufacturer_id))
    locations = sorted(
        (item for item in composition.list_usage_locations()
         if item.status == UsageLocationStatus.ACTIVE),
        key=lambda item: (item.location_name, item.location_id),
    )
    today = date.today()
    with st.container(key="analytics-filters", gap="small"):
        period_col, manufacturer_col, sds_col, bhp_col, location_col = st.columns(
            [1.7, 1.4, 1.1, 1.1, 1.5], gap="small"
        )
        with period_col:
            period = st.date_input(
                "Okres SDS", (date(today.year, 1, 1), today),
                key="analytics-date-range",
            )
        with manufacturer_col:
            manufacturer = st.selectbox(
                "Producent", (None, *manufacturers),
                format_func=lambda item: "Wszyscy producenci" if item is None else item.manufacturer_name,
                key="analytics-manufacturer",
            )
        sds_label = sds_col.selectbox("SDS", [label for label, _ in SDS_OPTIONS],
                                      key="analytics-sds")
        bhp_label = bhp_col.selectbox("BHP", [label for label, _ in BHP_OPTIONS],
                                      key="analytics-bhp")
        location = location_col.selectbox(
            "Lokalizacja", (None, *locations, "no-active"),
            format_func=lambda item: (
                "Wszystkie lokalizacje" if item is None else
                "Brak aktywnej lokalizacji" if item == "no-active" else item.location_name
            ),
            key="analytics-location",
        )
    if not isinstance(period, tuple) or len(period) != 2:
        st.info("Wybierz początek i koniec okresu SDS.")
        return None
    trend_from, trend_to = period
    return AnalyticsFilters(
        trend_date_from=trend_from, trend_date_to=trend_to,
        manufacturer_id=UUID(manufacturer.manufacturer_id) if manufacturer else None,
        sds_status=dict(SDS_OPTIONS)[sds_label], bhp_status=dict(BHP_OPTIONS)[bhp_label],
        usage_location_id=UUID(location.location_id) if location not in (None, "no-active") else None,
        include_no_active_location=location == "no-active",
    )


def _kpi_card(label: str, value: int, note: str) -> None:
    # The only interpolated values are Application-owned numbers and static labels.
    st.markdown(
        f'<div class="analytics-kpi"><div class="analytics-kpi-label">{label}</div>'
        f'<div class="analytics-kpi-value">{int(value)}</div>'
        f'<div class="analytics-kpi-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def _render_kpis(dashboard: AnalyticsDashboardDto) -> None:
    kpi = dashboard.kpi
    cards = (
        ("Produkty ogółem", kpi.products_total, "W aktualnym zakresie"),
        ("SDS CURRENT", kpi.current_sds_count, "Produkty z bieżącym SDS"),
        ("BHP zatwierdzone", kpi.bhp_approved_count, "Decyzje dla CURRENT SDS"),
        ("Braki / do uzupełnienia", kpi.attention_products_count, "Unikalne produkty"),
        ("Stanowiska aktywne", kpi.active_locations_count, "Unikalne lokalizacje"),
    )
    for column, (label, value, note) in zip(st.columns(5), cards):
        with column:
            _kpi_card(label, value, note)


def _render_charts(dashboard: AnalyticsDashboardDto) -> None:
    manufacturer_col, bhp_col, trend_col = st.columns([1.25, 1, 1.4])
    with manufacturer_col, st.container(border=True):
        st.markdown("#### Produkty wg producenta")
        if dashboard.manufacturer_summary:
            data = [{"Producent": row.manufacturer_name, "Produkty": row.products_count}
                    for row in dashboard.manufacturer_summary]
            st.vega_lite_chart(data, {
                "mark": {"type": "bar", "cornerRadiusEnd": 5, "color": "#7c9ce0"},
                "encoding": {
                    "y": {"field": "Producent", "type": "nominal", "sort": "-x", "title": None},
                    "x": {"field": "Produkty", "type": "quantitative", "title": None,
                          "axis": {"tickMinStep": 1}},
                    "tooltip": ["Producent", "Produkty"],
                },
                "height": max(200, len(data) * 28),
            }, width="stretch")
        else:
            st.info("Brak danych o producentach dla wybranych filtrów.")
    with bhp_col, st.container(border=True):
        st.markdown("#### Status BHP")
        distribution = dashboard.bhp_status
        if distribution.approved + distribution.rejected + distribution.no_decision:
            data = [
                {"Status": "Dopuszczony", "Produkty": distribution.approved},
                {"Status": "Odrzucony", "Produkty": distribution.rejected},
                {"Status": "Brak decyzji", "Produkty": distribution.no_decision},
            ]
            st.vega_lite_chart(data, {
                "mark": {"type": "arc", "innerRadius": 68},
                "encoding": {
                    "theta": {"field": "Produkty", "type": "quantitative"},
                    "color": {"field": "Status", "type": "nominal",
                              "scale": {"domain": ["Dopuszczony", "Odrzucony", "Brak decyzji"],
                                        "range": ["#74c7a7", "#e4a5a5", "#e8c884"]}},
                    "tooltip": ["Status", "Produkty"],
                },
                "height": 200,
            }, width="stretch")
        else:
            st.info("Brak produktów z CURRENT SDS dla wybranych filtrów.")
    with trend_col, st.container(border=True):
        st.markdown("#### Nowe / zaktualizowane SDS")
        if dashboard.sds_trend:
            data = [
                {"Miesiąc": point.period_start.isoformat(), "Seria": label, "Liczba": value}
                for point in dashboard.sds_trend
                for label, value in (("Nowe SDS", point.new_sds_count),
                                     ("Zaktualizowane SDS", point.updated_sds_count))
            ]
            st.vega_lite_chart(data, {
                "mark": {"type": "line", "point": {"filled": True, "size": 60},
                         "strokeWidth": 3},
                "encoding": {
                    "x": {"field": "Miesiąc", "type": "temporal", "timeUnit": "yearmonth",
                          "title": None},
                    "y": {"field": "Liczba", "type": "quantitative", "title": None,
                          "axis": {"tickMinStep": 1}},
                    "color": {"field": "Seria", "type": "nominal",
                              "scale": {"domain": ["Nowe SDS", "Zaktualizowane SDS"],
                                        "range": ["#6c9add", "#b29adf"]}},
                    "tooltip": ["Miesiąc", "Seria", "Liczba"],
                },
                "height": 200,
            }, width="stretch")
        else:
            st.info("Brak zarejestrowanych SDS w wybranym okresie.")


def _render_attention(dashboard: AnalyticsDashboardDto) -> None:
    st.subheader("Wymaga uwagi")
    attention = dashboard.attention
    items = (
        ("Brak CURRENT SDS", attention.no_current_sds_count),
        ("Brak decyzji BHP", attention.no_bhp_decision_count),
        ("Brak aktywnego miejsca stosowania", attention.no_active_location_count),
        ("Niedostępny dokument", attention.missing_source_file_count),
    )
    for column, (label, value) in zip(st.columns(4), items):
        with column:
            st.markdown(
                f'<div class="analytics-attention">'
                f'<div class="analytics-attention-label">{label}</div>'
                f'<div class="analytics-attention-value">{int(value)}</div></div>',
                unsafe_allow_html=True,
            )
    if any(
        fact.current_sds_availability == AnalyticsFileAvailability.CHECK_FAILED
        or fact.current_evidence_availability == AnalyticsFileAvailability.CHECK_FAILED
        for fact in dashboard.product_facts
    ):
        st.caption("Dostępności części dokumentów nie udało się sprawdzić.")


def _render_manufacturers(dashboard: AnalyticsDashboardDto) -> None:
    st.subheader("Podsumowanie producentów")
    if not dashboard.manufacturer_summary:
        st.info("Brak danych do podsumowania.")
        return
    st.dataframe([{
        "Producent": row.manufacturer_name,
        "Produkty": row.products_count,
        "SDS CURRENT": row.current_sds_count,
        "BHP OK": row.bhp_approved_count,
        "Braki": row.attention_products_count,
        "Ostatni SDS": (row.latest_sds_registered_at.date().isoformat()
                         if row.latest_sds_registered_at else "—"),
    } for row in dashboard.manufacturer_summary], hide_index=True,
                 width="stretch")


def _quantity(value: Decimal | None, unit: str | None) -> str:
    return "—" if value is None else f"{format(value.normalize(), 'f')} {unit or ''}".strip()


def _difference(value: Decimal | None, unit: str | None) -> str:
    if value is None:
        return "—"
    prefix = "+" if value > 0 else ""
    return prefix + _quantity(value, unit)


def _sds_detail(row: ProductLocationAnalyticsRow) -> str:
    parts = []
    if row.current_sds_revision:
        parts.append(f"Rewizja {row.current_sds_revision}")
    if row.current_sds_issue_date:
        parts.append(row.current_sds_issue_date.isoformat())
    return " · ".join(parts) if parts else "—"


def _detail_row(row: ProductLocationAnalyticsRow) -> dict[str, str]:
    return {
        "Produkt": row.product_name,
        "Producent": row.manufacturer_name,
        "Lokalizacja": row.location_name or "Brak",
        "MAX": _quantity(row.peak_quantity_value, row.peak_quantity_unit_code),
        "Stan na dzień": _quantity(row.review_observed_quantity, row.review_unit_code),
        "Różnica +/-": _difference(row.review_difference, row.review_unit_code),
        "Miesięczne zużycie": _quantity(row.monthly_consumption_value,
                                         row.monthly_consumption_unit_code),
        "Status produktu": PRODUCT_STATUS_LABELS[row.product_usage_status.value],
        "SDS / rewizja": _sds_detail(row),
        "Status BHP": BHP_LABELS[row.bhp_category],
    }


def _render_dashboard(composition: ShellComposition) -> None:
    with st.container(key="analytics-view-head", gap="small"):
        st.subheader("Dashboard")
        st.caption("Bieżący stan produktów, SDS, decyzji BHP i miejsc stosowania.")
    try:
        filters = _filters(composition)
    except (ShellInitializationError, ValueError):
        st.error(READ_ERROR_MESSAGE)
        return
    if filters is None:
        return
    if filters.trend_date_from > filters.trend_date_to:
        st.error("Początek okresu trendu SDS nie może być późniejszy niż koniec.")
        return
    try:
        with st.spinner("Wczytywanie analiz..."):
            dashboard = composition.get_analytics_dashboard(filters)
    except ShellInitializationError:
        st.error(READ_ERROR_MESSAGE)
        return
    if not dashboard.product_facts:
        st.info("Brak produktów dla wybranych filtrów.")
    _render_kpis(dashboard)
    _render_charts(dashboard)
    _render_attention(dashboard)
    _render_manufacturers(dashboard)


def _render_detail_view(composition: ShellComposition) -> None:
    with st.container(key="analytics-view-head", gap="small"):
        st.subheader("Zestawienie zbiorcze")
        st.caption("Szczegółowe PRODUCT × USAGE_LOCATION. MAX oznacza ilość szczytową.")
    try:
        filters = _filters(composition)
    except (ShellInitializationError, ValueError):
        st.error(READ_ERROR_MESSAGE)
        return
    if filters is None:
        return
    if filters.trend_date_from > filters.trend_date_to:
        st.error("Początek okresu trendu SDS nie może być późniejszy niż koniec.")
        return
    try:
        with st.spinner("Wczytywanie zestawienia..."):
            rows = composition.list_analytics_product_locations(filters)
    except ShellInitializationError:
        st.error(READ_ERROR_MESSAGE)
        return
    if not rows:
        st.info("Brak szczegółów dla wybranych filtrów.")
        return
    st.dataframe([_detail_row(row) for row in rows], hide_index=True, width="stretch")


def _review_rows(review: PhysicalReviewDetails) -> list[dict[str, str]]:
    return [{
        "Produkt": item.product_name,
        "Lokalizacja": f"{item.location_code} · {item.location_name}",
        "MAX": _quantity(item.baseline_max_quantity, item.unit_code),
        "Stan na dzień": ("" if item.observed_quantity is None
                          else format(item.observed_quantity, "f")),
        "Różnica": _difference(item.difference, item.unit_code),
    } for item in review.items]


def _parse_observed(value: object) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        quantity = Decimal(str(value).strip())
    except (ValueError, ArithmeticError) as error:
        raise InvalidObservedQuantityError("Podaj nieujemną liczbę lub zostaw pole puste.") from error
    if not quantity.is_finite() or quantity < 0:
        raise InvalidObservedQuantityError("Podaj nieujemną liczbę lub zostaw pole puste.")
    return quantity


def _render_review_details(composition: ShellComposition, review: PhysicalReviewDetails) -> None:
    st.caption(f"Data przeglądu: {review.summary.review_date.isoformat()}")
    st.write(
        f"Pozycje: {review.total_items} · Sprawdzone: {review.observed_items} "
        f"· Niesprawdzone: {review.unobserved_items}"
    )
    rows = _review_rows(review)
    if review.summary.status.value == "FINAL":
        st.caption("Zatwierdzony przegląd — tylko do odczytu.")
        st.dataframe(rows, hide_index=True, width="stretch")
        return

    st.caption("Wpisz ilość w jednostce MAX. Puste pole oznacza pozycję niesprawdzoną.")
    edited = st.data_editor(
        rows, hide_index=True, width="stretch", key="review-items-editor",
        disabled=["Produkt", "Lokalizacja", "MAX", "Różnica"],
        num_rows="fixed",
    )
    if st.button("Zapisz stany", key="review-save"):
        edited_rows = edited.to_dict("records") if hasattr(edited, "to_dict") else edited
        try:
            values = [_parse_observed(row["Stan na dzień"]) for row in edited_rows]
            for item, value in zip(review.items, values, strict=True):
                if value != item.observed_quantity:
                    composition.update_review_observed_quantity(item.review_item_id, value)
        except InvalidObservedQuantityError as error:
            st.error(str(error))
        except (ShellInitializationError, FinalReviewImmutableError, ReviewNotFoundError):
            st.error("Nie udało się zapisać stanów przeglądu. Odśwież widok i spróbuj ponownie.")
        else:
            st.success("Stany zapisane.")
            st.rerun()

    if review.unobserved_items:
        st.warning(f"Niesprawdzone pozycje: {review.unobserved_items}. FINAL zachowa je bez wyniku.")
        confirmed = st.checkbox(
            "Potwierdzam zatwierdzenie przeglądu z niesprawdzonymi pozycjami",
            key="review-confirm-incomplete",
        )
    else:
        confirmed = True
    finalize_col, discard_col = st.columns(2)
    with finalize_col:
        if st.button("Zatwierdź przegląd", key="review-finalize", disabled=not confirmed):
            try:
                composition.finalize_physical_review(review.summary.review_id)
            except (ShellInitializationError, ReviewAlreadyFinalError, ReviewNotFoundError):
                st.error("Nie udało się zatwierdzić przeglądu. Odśwież widok i spróbuj ponownie.")
            else:
                st.success("Przegląd zatwierdzony.")
                st.rerun()
    with discard_col:
        if st.button("Odrzuć draft", key="review-discard"):
            try:
                composition.discard_physical_review_draft(review.summary.review_id)
            except (ShellInitializationError, FinalReviewImmutableError, ReviewNotFoundError):
                st.error("Nie udało się odrzucić draftu. Odśwież widok i spróbuj ponownie.")
            else:
                st.success("Draft odrzucony.")
                st.rerun()


def _review_label(review: PhysicalReviewSummary) -> str:
    finalized = (review.finalized_at.strftime("%Y-%m-%d %H:%M")
                 if review.finalized_at else "")
    return f"{review.review_date.isoformat()} · zatwierdzono {finalized}"


def _render_review_view(composition: ShellComposition) -> None:
    with st.container(key="analytics-view-head", gap="small"):
        st.subheader("Raport przeglądu")
        st.caption("Stan fizyczny na wybrany dzień, zapisany jako historyczny przegląd.")
    try:
        draft = composition.get_active_physical_review_draft()
        finals = [review for review in composition.list_physical_reviews()
                  if review.status.value == "FINAL"]
        details = composition.get_physical_review(draft.review_id) if draft else None
    except (ShellInitializationError, ReviewNotFoundError):
        st.error(READ_ERROR_MESSAGE)
        return

    if details is None:
        review_date = st.date_input("Data przeglądu", value=date.today(),
                                    key="review-date")
        if st.button("Utwórz przegląd", key="review-create"):
            try:
                composition.create_physical_review(review_date)
            except EmptyReviewPopulationError:
                st.warning("Brak przypisań do aktywnych lokalizacji. Przegląd nie powstał.")
            except ReviewDraftAlreadyExistsError:
                st.warning("Istnieje już rozpoczęty przegląd. Odśwież widok.")
            except ShellInitializationError:
                st.error("Nie udało się utworzyć przeglądu. Spróbuj ponownie.")
            else:
                st.rerun()
    else:
        st.markdown("#### Rozpoczęty przegląd")
        _render_review_details(composition, details)

    if finals:
        st.markdown("#### Zatwierdzone przeglądy")
        selected = st.selectbox("Przegląd", finals, format_func=_review_label,
                                key="review-final-selection")
        try:
            _render_review_details(composition, composition.get_physical_review(selected.review_id))
        except (ShellInitializationError, ReviewNotFoundError):
            st.error(READ_ERROR_MESSAGE)


def _select_view(view: str) -> None:
    st.session_state["analytics-view"] = view


def render_analytics(composition: ShellComposition) -> None:
    _style()
    views = ("Dashboard", "Zestawienie zbiorcze", "Raport przeglądu")
    active = st.session_state.setdefault("analytics-view", "Dashboard")
    if active not in views:
        active = "Dashboard"
        st.session_state["analytics-view"] = active
    with st.container(key="analytics-module-head", gap="small"):
        st.header("Analizy")
        with st.container(key="analytics-nav", gap="small"):
            for column, view in zip(st.columns(3), views):
                with column, st.container(key=(
                    "analytics-nav-active" if active == view
                    else f"analytics-nav-idle-{view}"
                )):
                    st.button(view, key=f"analytics-view-{view}",
                              type="secondary", width="stretch",
                              on_click=_select_view, args=(view,))
    if active == "Dashboard":
        _render_dashboard(composition)
    elif active == "Zestawienie zbiorcze":
        _render_detail_view(composition)
    else:
        _render_review_view(composition)
