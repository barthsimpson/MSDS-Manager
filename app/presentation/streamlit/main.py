"""Minimal Streamlit entry point for MSDS Manager."""

import streamlit as st

from app.presentation.streamlit.composition import (
    ShellInitializationError,
    build_shell_composition,
)
from app.presentation.streamlit.product_registry import (
    render_product_registry,
    render_usage_locations,
)
from app.presentation.streamlit.add_sds import render_add_sds
from app.presentation.streamlit.bhp_decision import render_bhp_decision
from app.presentation.streamlit.supervisory import render_supervisory
from app.presentation.streamlit.analytics import render_analytics


SECTIONS = ("Produkty", "Dodaj SDS", "Decyzja BHP", "Stanowiska", "Widok nadzorczy", "Analizy")


def main() -> None:
    st.set_page_config(page_title="MSDS Manager", page_icon="📋", layout="wide")
    st.title("MSDS Manager")

    try:
        composition = build_shell_composition()
    except ShellInitializationError as error:
        st.error(str(error))
        return

    try:
        section = st.sidebar.radio("Sekcja", SECTIONS)
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
