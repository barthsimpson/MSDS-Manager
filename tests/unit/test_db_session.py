from unittest.mock import Mock

from sqlalchemy import Engine

from app.infrastructure.config import Settings
from app.infrastructure.db import session as session_module


def test_engine_and_session_factory_do_not_connect_during_creation(
    tmp_path, monkeypatch
) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/msds_manager",
        sds_root_path=tmp_path,
        bhp_evidence_root_path=tmp_path,
    )
    engine = Mock(spec=Engine)
    create_engine = Mock(return_value=engine)
    monkeypatch.setattr(session_module, "create_engine", create_engine)

    created_engine = session_module.create_engine_from_settings(settings)
    session_factory = session_module.create_session_factory(created_engine)

    create_engine.assert_called_once_with(settings.database_url)
    assert created_engine is engine
    assert session_factory.kw["bind"] is engine
