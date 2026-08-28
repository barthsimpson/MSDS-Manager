"""Run the minimal read-only application vertical slice."""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.application.use_cases import ListManufacturers
from app.infrastructure.config import ConfigurationError, load_settings
from app.infrastructure.db.repositories import SqlAlchemyManufacturerRepository
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)


def main() -> int:
    engine = None
    try:
        settings = load_settings()
        engine = create_engine_from_settings(settings)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            repository = SqlAlchemyManufacturerRepository(session)
            manufacturers = ListManufacturers(repository).execute()
    except (ConfigurationError, SQLAlchemyError, OSError, ImportError) as error:
        print(
            "Application smoke test: ERROR - "
            f"database or schema unavailable ({type(error).__name__})"
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()

    print("Application smoke test: OK")
    print(f"Manufacturers returned: {len(manufacturers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
