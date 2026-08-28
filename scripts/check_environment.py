"""Run read-only checks of local MSDS Manager infrastructure."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.config import ConfigurationError, load_settings
from app.infrastructure.db.session import create_engine_from_settings


def main() -> int:
    print("MSDS Manager environment check")
    print()

    try:
        settings = load_settings()
    except ConfigurationError as error:
        print(f"CONFIGURATION: ERROR - {error}")
        print("DATABASE: NOT CHECKED")
        print("SDS_ROOT_PATH: NOT CHECKED")
        print("BHP_EVIDENCE_ROOT_PATH: NOT CHECKED")
        print()
        print("RESULT: FAILED")
        return 1

    root_statuses = settings.root_path_statuses()
    database_ok = False
    engine = None

    try:
        engine = create_engine_from_settings(settings)
        with engine.connect() as connection:
            database_ok = connection.execute(text("SELECT 1")).scalar_one() == 1
        database_result = "OK" if database_ok else "ERROR - unexpected SELECT 1 result"
    except (SQLAlchemyError, OSError, ImportError) as error:
        database_result = f"ERROR - connection failed ({type(error).__name__})"
    finally:
        if engine is not None:
            engine.dispose()

    print(f"DATABASE: {database_result}")
    for name, exists in root_statuses.items():
        print(f"{name}: {'OK' if exists else 'MISSING'}")

    result_ok = database_ok and all(root_statuses.values())
    print()
    print(f"RESULT: {'OK' if result_ok else 'FAILED'}")
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
