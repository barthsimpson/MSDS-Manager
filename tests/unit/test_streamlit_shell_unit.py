import importlib

import pytest
from streamlit.testing.v1 import AppTest

from app.infrastructure.config import ConfigurationError
from app.presentation.streamlit.composition import (
    INITIALIZATION_ERROR_MESSAGE,
    ShellInitializationError,
    build_shell_composition,
)


def test_streamlit_modules_are_importable_without_starting_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition_module = importlib.import_module(
        "app.presentation.streamlit.composition"
    )

    def forbidden_build():
        raise AssertionError("composition must not run during module import")

    with monkeypatch.context() as context:
        context.setattr(
            composition_module, "build_shell_composition", forbidden_build
        )
        app_module = importlib.reload(
            importlib.import_module("app.presentation.streamlit.main")
        )

        assert callable(app_module.main)
        assert app_module.SECTIONS == (
            "Produkty",
            "Dodaj SDS",
            "Decyzja BHP",
            "Stanowiska",
            "Widok nadzorczy",
            "Analizy",
        )

    importlib.reload(app_module)


def test_configuration_error_is_controlled_and_does_not_expose_secret() -> None:
    secret = "postgresql+psycopg://user:super-secret@localhost/database"

    def failing_settings_loader():
        raise ConfigurationError(secret)

    with pytest.raises(ShellInitializationError) as error_info:
        build_shell_composition(settings_loader=failing_settings_loader)

    assert str(error_info.value) == INITIALIZATION_ERROR_MESSAGE
    assert "super-secret" not in str(error_info.value)
    assert secret not in str(error_info.value)


def test_sidebar_icons_keep_section_values_selectable() -> None:
    from app.presentation.streamlit.main import SECTIONS, SECTION_ICONS, _section_label

    def render() -> None:
        import streamlit as st
        from app.presentation.streamlit.main import SECTIONS, _section_label

        st.sidebar.radio("Sekcja", SECTIONS, format_func=_section_label)

    app = AppTest.from_function(render).run()
    assert app.exception == []
    assert app.sidebar.radio[0].value == "Produkty"
    assert all(_section_label(section).endswith(section) for section in SECTIONS)
    assert all(SECTION_ICONS[section].startswith(":material/") for section in SECTIONS)

    for section in SECTIONS[1:]:
        app.sidebar.radio[0].set_value(section).run()
        assert app.exception == []
        assert app.sidebar.radio[0].value == section
