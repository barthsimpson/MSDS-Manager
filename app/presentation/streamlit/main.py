"""Minimal Streamlit entry point for MSDS Manager."""

import streamlit as st

from app.presentation.streamlit.composition import (
    ShellInitializationError,
    build_shell_composition,
)
from app.presentation.streamlit.product_registry import (
    PRODUCT_CARD_KEY,
    render_product_registry,
    render_usage_locations,
)
from app.presentation.streamlit.add_sds import render_add_sds
from app.presentation.streamlit.bhp_decision import render_bhp_decision
from app.presentation.streamlit.supervisory import render_supervisory
from app.presentation.streamlit.analytics import render_analytics


SECTIONS = ("Produkty", "Dodaj SDS", "Decyzja BHP", "Stanowiska", "Widok nadzorczy", "Analizy")
SECTION_ICONS = {
    "Produkty": ":material/inventory_2:",
    "Dodaj SDS": ":material/note_add:",
    "Decyzja BHP": ":material/verified_user:",
    "Stanowiska": ":material/settings:",
    "Widok nadzorczy": ":material/visibility:",
    "Analizy": ":material/bar_chart:",
}
SIDEBAR_STYLE = """
<style>
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-size: 15px;
    font-weight: 600;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 44px;
    padding-top: 7px;
    padding-bottom: 7px;
    align-items: center;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
    font-size: 16px;
    line-height: 1.35;
}
[data-testid="stSidebar"] [role="radiogroup"] .material-symbols-rounded {
    font-size: 19px;
}
</style>
"""


def _section_label(section: str) -> str:
    return f"{SECTION_ICONS[section]}  {section}"


def main() -> None:
    st.set_page_config(page_title="MSDS Manager", page_icon="📋", layout="wide")
    st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)
    st.title("MSDS Manager")

    try:
        composition = build_shell_composition()
    except ShellInitializationError as error:
        st.error(str(error))
        return

    try:
        section = st.sidebar.radio("Sekcja", SECTIONS, format_func=_section_label)
        if section != "Produkty":
            st.session_state.pop(PRODUCT_CARD_KEY, None)
        if section == "Analizy" and st.session_state.get("shell-previous-section") != "Analizy":
            st.session_state["analytics-view"] = "Dashboard"
        st.session_state["shell-previous-section"] = section
        if section == "Produkty":
            render_product_registry(composition)
        elif section == "Dodaj SDS":
            render_add_sds(composition)
        elif section == "Decyzja BHP":
            render_bhp_decision(composition)
        elif section == "Widok nadzorczy":
            render_supervisory(composition)
        elif section == "Analizy":
            render_analytics(composition)
        else:
            render_usage_locations(composition)
    finally:
        composition.dispose()


if __name__ == "__main__":
    main()
