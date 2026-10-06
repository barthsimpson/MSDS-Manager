"""Validate TASK-047 migration against a disposable PostgreSQL cluster."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.enums import ReviewStatus
from app.domain.models import PhysicalReview, PhysicalReviewItem
from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories import SqlAlchemyPhysicalReviewRepository


OLD = "d8f3a21c6046"
NEW = "9f62c4e8b7a1"
BUSINESS_TABLES = (
    "manufacturers", "products", "usage_locations", "unit_of_measure",
    "product_usage_locations", "product_history", "usage_location_history",
    "product_usage_location_history", "sds_documents", "bhp_decisions",
    "decision_evidence", "safety_profiles", "sds_components",
)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    operator_url = make_url(load_settings().database_url)
    assert operator_url.database == "msds_manager"
    test_db = f"task047_{uuid4().hex}"
    operator_engine = create_engine(operator_url, isolation_level="AUTOCOMMIT")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["DATABASE_URL"] = operator_url.set(database=test_db).render_as_string(hide_password=False)
    engine = None
    created = False

    def run(*args: str) -> str:
        completed = subprocess.run(
            args, cwd=repo, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120,
        )
        output = completed.stdout.decode("utf-8", errors="replace")
        if completed.returncode:
            raise RuntimeError(f"{' '.join(args[:4])} failed:\n{output}")
        return output

    def fingerprint() -> str:
        with engine.connect() as connection:
            rows = {}
            for table in BUSINESS_TABLES:
                # Fixed, migration-owned table names only.
                values = connection.execute(text(f"SELECT * FROM {table}")).all()
                rows[table] = sorted(tuple(str(value) for value in row) for row in values)
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision in (OLD, NEW)
        return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()

    def rejected(sql: str, params: dict | None = None) -> None:
        try:
            with engine.begin() as connection:
                connection.execute(text(sql), params or {})
        except IntegrityError:
            return
        raise AssertionError(f"Expected constraint rejection: {sql}")

    def verify_schema() -> None:
        inspector = inspect(engine)
        assert "physical_reviews" in inspector.get_table_names()
        assert "physical_review_items" in inspector.get_table_names()
        review_columns = {c["name"]: c for c in inspector.get_columns("physical_reviews")}
        item_columns = {c["name"]: c for c in inspector.get_columns("physical_review_items")}
        peak_column = next(c for c in inspector.get_columns("product_usage_locations")
                           if c["name"] == "peak_quantity_value")
        for name in ("baseline_max_quantity", "observed_quantity"):
            assert item_columns[name]["type"].precision == peak_column["type"].precision
            assert item_columns[name]["type"].scale == peak_column["type"].scale
        assert str(item_columns["product_id"]["type"]) == "VARCHAR"
        assert str(item_columns["location_id"]["type"]) == "VARCHAR"
        assert str(item_columns["baseline_unit_id"]["type"]) == "UUID"
        assert review_columns["created_at"]["type"].timezone is True
        assert review_columns["finalized_at"]["type"].timezone is True
        assert {f["name"] for f in inspector.get_foreign_keys("physical_review_items")} == {
            "fk_physical_review_items_review_id",
            "fk_physical_review_items_product_id",
            "fk_physical_review_items_location_id",
            "fk_physical_review_items_baseline_unit_id",
        }
        assert all(f["options"].get("ondelete") == "RESTRICT"
                   for f in inspector.get_foreign_keys("physical_review_items"))
        assert {i["name"] for i in inspector.get_indexes("physical_reviews")} == {
            "ix_physical_reviews_status", "ix_physical_reviews_date_finalized",
            "uq_physical_reviews_single_draft",
        }
        assert {i["name"] for i in inspector.get_indexes("physical_review_items")} >= {
            "ix_physical_review_items_review_id",
            "ix_physical_review_items_product_location_review",
        }
        with engine.connect() as connection:
            definition = connection.scalar(text(
                "SELECT indexdef FROM pg_indexes WHERE tablename='physical_reviews' "
                "AND indexname='uq_physical_reviews_single_draft'"
            ))
        assert "UNIQUE" in definition and "WHERE" in definition and "DRAFT" in definition

    try:
        print("Creating isolated PostgreSQL database", flush=True)
        with operator_engine.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{test_db}"')
        created = True
        run(sys.executable, "-m", "alembic", "upgrade", OLD)
        engine = create_engine(env["DATABASE_URL"])
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO manufacturers VALUES ('task047-mfr', 'Test manufacturer')"
            ))
            connection.execute(text(
                "INSERT INTO products (product_id, product_name, manufacturer_product_code, "
                "manufacturer_id, use_description, use_restriction, usage_status) "
                "VALUES ('task047-product', 'Test', 'T47', 'task047-mfr', '', '', 'ACTIVE')"
            ))
            connection.execute(text(
                "INSERT INTO usage_locations (location_id, location_code, location_name, status) "
                "VALUES ('task047-location', 'T47', 'Test', 'ACTIVE')"
            ))
            connection.execute(text(
                "INSERT INTO product_usage_locations "
                "(product_id, location_id, peak_quantity_value, peak_quantity_unit_id) "
                "SELECT 'task047-product', 'task047-location', 2.5, unit_id "
                "FROM unit_of_measure WHERE code='kg'"
            ))
        original = fingerprint()
        run(sys.executable, "-m", "alembic", "upgrade", NEW)
        verify_schema()
        assert fingerprint() == original
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM physical_reviews")) == 0
            assert connection.scalar(text("SELECT count(*) FROM physical_review_items")) == 0

        first, second = str(uuid4()), str(uuid4())
        def draft(review_id: str) -> str:
            return ("INSERT INTO physical_reviews "
                    "(review_id, review_date, status, created_at) "
                    f"VALUES ('{review_id}', CURRENT_DATE, 'DRAFT', CURRENT_TIMESTAMP)")
        with engine.begin() as connection:
            connection.execute(text(draft(first)))
        rejected(draft(second))
        rejected("INSERT INTO physical_reviews (review_id, review_date, status, created_at) "
                 "VALUES (:id, CURRENT_DATE, 'BAD', CURRENT_TIMESTAMP)", {"id": str(uuid4())})
        rejected("INSERT INTO physical_reviews (review_id, review_date, status, created_at) "
                 "VALUES (:id, CURRENT_DATE, 'FINAL', CURRENT_TIMESTAMP)", {"id": str(uuid4())})
        rejected("UPDATE physical_reviews SET finalized_at=CURRENT_TIMESTAMP "
                 "WHERE review_id=:id", {"id": first})

        item = str(uuid4())
        insert_item = (
            "INSERT INTO physical_review_items "
            "(review_item_id, review_id, product_id, location_id, baseline_max_quantity, "
            "baseline_unit_id, observed_quantity) "
            "SELECT :item, :review, :product, :location, :baseline, unit_id, :observed "
            "FROM unit_of_measure WHERE code='kg'"
        )
        valid = dict(item=item, review=first, product="task047-product",
                     location="task047-location", baseline=2.5, observed=None)
        with engine.begin() as connection:
            connection.execute(text(insert_item), valid)
        rejected(insert_item, {**valid, "item": str(uuid4())})  # duplicate review/product/location
        rejected(insert_item, {**valid, "item": str(uuid4()), "baseline": -1})
        rejected(insert_item, {**valid, "item": str(uuid4()), "observed": -1})
        rejected(insert_item, {**valid, "item": str(uuid4()), "product": "missing"})
        rejected(insert_item, {**valid, "item": str(uuid4()), "location": "missing"})
        rejected(insert_item, {**valid, "item": str(uuid4()), "review": str(uuid4())})
        rejected("UPDATE physical_review_items SET baseline_unit_id=:unit WHERE review_item_id=:item",
                 {"unit": str(uuid4()), "item": item})
        rejected("DELETE FROM products WHERE product_id='task047-product'")
        rejected("DELETE FROM usage_locations WHERE location_id='task047-location'")
        with engine.begin() as connection:
            connection.execute(text(
                "UPDATE physical_review_items SET observed_quantity=0 WHERE review_item_id=:item"
            ), {"item": item})
            assert connection.scalar(text(
                "SELECT observed_quantity FROM physical_review_items WHERE review_item_id=:item"
            ), {"item": item}) == 0
            connection.execute(text(
                "UPDATE physical_reviews SET status='FINAL', finalized_at=CURRENT_TIMESTAMP "
                "WHERE review_id=:id"
            ), {"id": first})
            connection.execute(text(draft(second)))
        print("Isolated schema, constraints, FK and indexes: PASS", flush=True)

        run(sys.executable, "-m", "alembic", "downgrade", OLD)
        assert fingerprint() == original
        assert "physical_reviews" not in inspect(engine).get_table_names()
        run(sys.executable, "-m", "alembic", "upgrade", NEW)
        verify_schema()
        assert fingerprint() == original
        print(run(sys.executable, "-m", "alembic", "check").strip(), flush=True)
        review_id = str(uuid4())
        with Session(engine) as session:
            unit_id = session.scalar(text("SELECT unit_id FROM unit_of_measure WHERE code='kg'"))
            SqlAlchemyPhysicalReviewRepository(session).add_snapshot(
                PhysicalReview(
                    review_id=review_id, review_date=date(2026, 10, 6),
                    status=ReviewStatus.DRAFT, created_at=datetime.now(timezone.utc),
                ),
                [PhysicalReviewItem(
                    review_item_id=str(uuid4()), review_id=review_id,
                    product_id="task047-product", location_id="task047-location",
                    baseline_max_quantity=Decimal("2.5"),
                    baseline_unit_id=str(unit_id),
                )],
            )
            session.commit()
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT count(*) FROM physical_review_items WHERE review_id=:id"
            ), {"id": review_id}) == 1
        print("Repository snapshot insert: PASS", flush=True)
        print("Isolated upgrade, downgrade, re-upgrade: PASS", flush=True)
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with operator_engine.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{test_db}" WITH (FORCE)')
        operator_engine.dispose()


if __name__ == "__main__":
    main()
