"""Validate TASK-051-R1 migration and focused tests in a disposable PostgreSQL DB."""

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.domain.enums import ProductUsageStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import ManufacturerModel, ProductModel


OLD = "9f62c4e8b7a1"
NEW = "c6a8f1d2940e"


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    operator_url = make_url(load_settings().database_url)
    if operator_url.database != "msds_manager":
        raise RuntimeError("Expected the configured operator database name msds_manager.")
    name = f"task051_{uuid4().hex}"
    isolated_url = operator_url.set(database=name)
    maintenance = create_engine(operator_url, isolation_level="AUTOCOMMIT")
    engine = None
    created = False
    environment = os.environ.copy()
    environment["DATABASE_URL"] = isolated_url.render_as_string(hide_password=False)
    environment["PYTHONUTF8"] = "1"

    def run(*arguments: str) -> str:
        completed = subprocess.run(
            arguments, cwd=repo, env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = completed.stdout.decode("utf-8", errors="replace")
        if completed.returncode:
            raise RuntimeError(f"Command failed: {arguments[:4]}\n{output}")
        return output

    try:
        with maintenance.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created = True
        engine = create_engine(isolated_url)

        print(run(sys.executable, "-m", "alembic", "heads").strip())
        print(run(sys.executable, "-m", "alembic", "upgrade", OLD).strip())

        manufacturer_id = uuid4().hex
        product_id = uuid4().hex
        with Session(engine) as session, session.begin():
            session.add(ManufacturerModel(
                manufacturer_id=manufacturer_id, manufacturer_name="TASK-051 migration baseline"
            ))
            session.add(ProductModel(
                product_id=product_id, product_name="Existing code",
                manufacturer_product_code="PRESERVED-001", manufacturer_id=manufacturer_id,
                use_description="Use", use_restriction="Restriction",
                usage_status=ProductUsageStatus.ACTIVE,
            ))

        print(run(sys.executable, "-m", "alembic", "upgrade", "head").strip())
        inspector = inspect(engine)
        columns = {column["name"]: column for column in inspector.get_columns("products")}
        assert columns["manufacturer_product_code"]["nullable"] is True
        assert "product_identity_changes" in inspector.get_table_names()
        history = {column["name"]: column for column in inspector.get_columns("product_identity_changes")}
        assert history["old_manufacturer_product_code"]["nullable"] is True
        assert history["new_manufacturer_product_code"]["nullable"] is True
        assert history["changed_at"]["nullable"] is False
        assert inspector.get_pk_constraint("product_identity_changes")["constrained_columns"] == ["change_id"]
        assert any(foreign_key["referred_table"] == "products" and
                   foreign_key["constrained_columns"] == ["product_id"]
                   for foreign_key in inspector.get_foreign_keys("product_identity_changes"))
        assert any("CODE_COMPLETION" in check["sqltext"] and "CORRECTION" in check["sqltext"]
                   for check in inspector.get_check_constraints("product_identity_changes"))
        with Session(engine) as session:
            assert session.scalar(select(ProductModel.manufacturer_product_code).where(
                ProductModel.product_id == product_id
            )) == "PRESERVED-001"
        print("UPGRADE_SCHEMA_AND_EXISTING_CODE: PASS")

        print(run(sys.executable, "-m", "alembic", "downgrade", OLD).strip())
        inspector = inspect(engine)
        assert "product_identity_changes" not in inspector.get_table_names()
        assert next(column for column in inspector.get_columns("products")
                    if column["name"] == "manufacturer_product_code")["nullable"] is False
        with Session(engine) as session:
            assert session.scalar(select(ProductModel.manufacturer_product_code).where(
                ProductModel.product_id == product_id
            )) == "PRESERVED-001"
        print("DOWNGRADE_SCHEMA_AND_EXISTING_CODE: PASS")

        print(run(sys.executable, "-m", "alembic", "upgrade", "head").strip())
        current = run(sys.executable, "-m", "alembic", "current")
        assert f"{NEW} (head)" in current
        print(current.strip())
        check = run(sys.executable, "-m", "alembic", "check")
        assert "No new upgrade operations detected" in check
        print(check.strip())
        print(run(
            sys.executable, "-m", "pytest", "-q",
            "tests/integration/test_task051_identity.py",
            "tests/integration/test_patch007_product_identity.py",
        ).strip())
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with maintenance.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        maintenance.dispose()


if __name__ == "__main__":
    main()
