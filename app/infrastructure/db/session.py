"""SQLAlchemy engine and session factories."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    """Create an Engine without opening a database connection."""

    return create_engine(settings.database_url)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a SQLAlchemy 2.x session factory for an existing Engine."""

    return sessionmaker(bind=engine, expire_on_commit=False)
