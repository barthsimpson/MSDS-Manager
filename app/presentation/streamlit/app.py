"""Minimal Streamlit entry point for MSDS Manager."""

import streamlit as st

from app.presentation.streamlit.composition import (
    ShellInitializationError,
    build_shell_composition,
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
            st.header("Produkty")
            st.info("Widok rejestru produktów zostanie udostępniony w kolejnym etapie.")
        else:
            st.header("Stanowiska")
            st.info("Obsługa stanowisk zostanie udostępniona w kolejnym etapie.")
    finally:
        composition.dispose()


if __name__ == "__main__":
    main()
