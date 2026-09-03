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


SECTIONS = ("Produkty", "Stanowiska")


def main() -> None:
    st.set_page_config(page_title="MSDS Manager", page_icon="📋")
    st.title("MSDS Manager")

    try:
        composition = build_shell_composition()
    except ShellInitializationError as error:
        st.error(str(error))
        return

    try:
        section = st.sidebar.radio("Sekcja", SECTIONS)
        if section == "Produkty":
            render_product_registry(composition)
        else:
            render_usage_locations(composition)
    finally:
        composition.dispose()


if __name__ == "__main__":
    main()
