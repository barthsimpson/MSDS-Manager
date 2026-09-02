import importlib

import pytest

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
            importlib.import_module("app.presentation.streamlit.app")
        )

        assert callable(app_module.main)
        assert app_module.SECTIONS == ("Produkty", "Stanowiska")

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
