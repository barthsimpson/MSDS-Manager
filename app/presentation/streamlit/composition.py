"""Composition root for the minimal Streamlit shell."""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.use_cases import ListProducts
from app.infrastructure.config import ConfigurationError, Settings, load_settings
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)


INITIALIZATION_ERROR_MESSAGE = (
    "Nie udało się uruchomić aplikacji. Sprawdź konfigurację i połączenie z bazą."
)


class ShellInitializationError(RuntimeError):
    """Controlled, secret-free error exposed to the Streamlit view."""


@dataclass(slots=True)
class ShellComposition:
    """Ready read-only dependencies owned by the presentation layer."""

    engine: Engine
    session_factory: sessionmaker[Session]
    product_count: int

    def dispose(self) -> None:
        self.engine.dispose()


def build_shell_composition(
    settings_loader: Callable[[], Settings] = load_settings,
    engine_factory: Callable[[Settings], Engine] = create_engine_from_settings,
    session_factory_builder: Callable[
        [Engine], sessionmaker[Session]
    ] = create_session_factory,
) -> ShellComposition:
    """Build dependencies and verify a minimal read through Application."""

    engine: Engine | None = None
    try:
        settings = settings_loader()
        engine = engine_factory(settings)
        session_factory = session_factory_builder(engine)
        with session_factory() as session:
            products = ListProducts(SqlAlchemyProductRepository(session)).execute()
        return ShellComposition(
            engine=engine,
            session_factory=session_factory,
            product_count=len(products),
        )
    except (ConfigurationError, SQLAlchemyError, OSError, ImportError) as error:
        if engine is not None:
            engine.dispose()
        raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error
