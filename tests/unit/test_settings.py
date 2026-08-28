from pathlib import Path

import pytest

from app.infrastructure.config.settings import (
    ConfigurationError,
    load_settings,
    read_env_file,
)


def test_reads_simple_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL = postgresql+psycopg://local/db\n"
        "SDS_ROOT_PATH = C:\\SDS\n"
        "BHP_EVIDENCE_ROOT_PATH=C:\\BHP\n",
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file, environ={})

    assert settings.database_url == "postgresql+psycopg://local/db"
    assert settings.sds_root_path == Path("C:\\SDS")
    assert settings.bhp_evidence_root_path == Path("C:\\BHP")


def test_ignores_comments_and_empty_lines(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n# local configuration\n\n KEY = value \n",
        encoding="utf-8",
    )

    assert read_env_file(env_file) == {"KEY": "value"}


def test_missing_required_variable_raises_clear_error(tmp_path: Path) -> None:
    secret = "postgresql+psycopg://user:top-secret@localhost/msds_manager"
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={secret}\nSDS_ROOT_PATH=C:\\SDS\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError) as error_info:
        load_settings(env_file=env_file, environ={})

    message = str(error_info.value)
    assert "BHP_EVIDENCE_ROOT_PATH" in message
    assert secret not in message
    assert "top-secret" not in message


def test_process_environment_overrides_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+psycopg://from-file/db\n"
        "SDS_ROOT_PATH=C:\\SDS\n"
        "BHP_EVIDENCE_ROOT_PATH=C:\\BHP\n",
        encoding="utf-8",
    )

    settings = load_settings(
        env_file=env_file,
        environ={"DATABASE_URL": "postgresql+psycopg://from-process/db"},
    )

    assert settings.database_url == "postgresql+psycopg://from-process/db"
