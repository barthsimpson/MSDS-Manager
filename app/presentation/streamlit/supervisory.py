"""Read-only formatting and filtering of the supervisory application result."""

import streamlit as st

from app.application.dto import SupervisoryProductRow
from app.application.exceptions import SupervisoryReadError
from app.domain.enums import ProductUsageStatus
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError


READ_ERROR_MESSAGE = "Nie udało się odczytać danych widoku nadzorczego."


def _table_row(row: SupervisoryProductRow) -> dict[str, str]:
    if row.current_sds_id is None:
        sds = "BRAK CURRENT SDS"
    elif not row.current_sds_file_available:
        sds = "BRAK PLIKU SDS"
    else:
        sds = "CURRENT"
    return {
        "Produkt": row.product_name,
        "Producent": row.manufacturer_name,
        "Kod producenta": row.manufacturer_product_code,
        "Miejsca stosowania": "; ".join(row.usage_locations) or "—",
        "SDS": sds,
        "Data SDS": row.current_sds_issue_date.isoformat() if row.current_sds_issue_date else "—",
        "Rewizja SDS": row.current_sds_revision or "—",
        "Status produktu": row.usage_status.value,
        "BHP": (
            "BRAK DECYZJI" if row.current_bhp_decision_id is None
            else row.current_bhp_decision_status.value
        ),
        "Warunki / uwagi": row.current_bhp_notes or "—",
        "Wymaga działania": "; ".join(row.action_reasons) if row.requires_action else "OK",
    }


def render_supervisory(composition: ShellComposition) -> None:
    st.header("Widok nadzorczy")
    try:
        rows = composition.list_supervisory_products()
    except (SupervisoryReadError, ShellInitializationError):
        st.error(READ_ERROR_MESSAGE)
        return
    if not rows:
        st.info("Brak produktów do wyświetlenia.")
        return

    action = st.selectbox(
        "Wymaga działania", ("Wszystkie", "Wymagają działania"), key="supervisory-action"
    )
    status = st.selectbox(
        "Status produktu", (None, *ProductUsageStatus),
        format_func=lambda value: "Wszystkie" if value is None else value.value,
        key="supervisory-status",
    )
    location = st.selectbox(
        "Miejsce stosowania",
        (None, *sorted({place for row in rows for place in row.usage_locations})),
        format_func=lambda value: "Wszystkie" if value is None else value,
        key="supervisory-location",
    )
    visible = [
        _table_row(row) for row in rows
        if (action == "Wszystkie" or row.requires_action)
        and (status is None or row.usage_status == status)
        and (location is None or location in row.usage_locations)
    ]
    if not visible:
        st.info("Brak produktów spełniających wybrane filtry.")
        return
    st.dataframe(visible, hide_index=True)
