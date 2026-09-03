from pathlib import Path

from sqlalchemy import MetaData, create_engine, func, select
from streamlit.testing.v1 import AppTest

from app.infrastructure.config import load_settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = PROJECT_ROOT / "app" / "presentation" / "streamlit" / "app.py"


def business_row_count() -> int:
    engine = create_engine(load_settings().database_url)
    try:
        metadata = MetaData()
        metadata.reflect(engine)
        with engine.connect() as connection:
            return sum(
                connection.execute(select(func.count()).select_from(table)).scalar_one()
                for name, table in metadata.tables.items()
                if name != "alembic_version"
            )
    finally:
        engine.dispose()


def test_streamlit_shell_navigation_on_empty_database_is_read_only() -> None:
    rows_before = business_row_count()

    app = AppTest.from_file(str(APP_PATH)).run(timeout=10)

    assert app.exception == []
    assert app.title[0].value == "MSDS Manager"
    assert app.header[0].value == "Produkty"
    assert app.info[0].value == "Brak produktów w rejestrze."
    assert app.radio[0].options == ["Produkty", "Stanowiska"]
    assert app.selectbox == []
    assert app.button == []
    assert rows_before == 0

    app.radio[0].set_value("Stanowiska").run(timeout=10)

    assert app.exception == []
    assert app.header[0].value == "Stanowiska"
    assert any(button.label == "Dodaj lokalizację" for button in app.button)
    assert business_row_count() == rows_before


def test_streamlit_shell_displays_secret_free_initialization_error(
    monkeypatch,
) -> None:
    secret = "invalid-database-address-super-secret"
    monkeypatch.setenv("DATABASE_URL", secret)

    app = AppTest.from_file(str(APP_PATH)).run(timeout=10)

    assert app.exception == []
    assert app.title[0].value == "MSDS Manager"
    assert app.error[0].value == (
        "Nie udało się uruchomić aplikacji. "
        "Sprawdź konfigurację i połączenie z bazą."
    )
    assert secret not in app.error[0].value
