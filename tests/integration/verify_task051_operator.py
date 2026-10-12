"""Apply TASK-051-R1 schema change while checking operator PRODUCT data."""

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.config import load_settings
from app.infrastructure.db.models import ProductIdentityChangeModel, ProductModel


OLD = "9f62c4e8b7a1"
NEW = "c6a8f1d2940e"


def _product_snapshot(engine) -> tuple[tuple, ...]:
    with Session(engine) as session:
        products = session.scalars(select(ProductModel).order_by(ProductModel.product_id)).all()
        return tuple((
            product.product_id, product.product_name, product.manufacturer_product_code,
            product.manufacturer_id, product.use_description, product.use_restriction,
            product.usage_status, product.waste_type, product.waste_code,
        ) for product in products)


def main() -> None:
    settings = load_settings()
    url = make_url(settings.database_url)
    if url.database != "msds_manager":
        raise RuntimeError("Refusing to migrate a database other than msds_manager.")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
        if current != OLD:
            raise RuntimeError(f"Expected operator revision {OLD}; found {current!r}.")
        inspector = inspect(engine)
        code_column = next(column for column in inspector.get_columns("products")
                           if column["name"] == "manufacturer_product_code")
        if code_column["nullable"] or "product_identity_changes" in inspector.get_table_names():
            raise RuntimeError("Operator schema differs from the expected pre-migration state.")
        before = _product_snapshot(engine)
        print(f"PRECHECK: {len(before)} PRODUCT rows; revision {current}; code NOT NULL")

        command.upgrade(Config("alembic.ini"), "head")

        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
        if current != NEW:
            raise RuntimeError(f"Unexpected post-migration revision: {current!r}.")
        inspector = inspect(engine)
        code_column = next(column for column in inspector.get_columns("products")
                           if column["name"] == "manufacturer_product_code")
        if not code_column["nullable"] or "product_identity_changes" not in inspector.get_table_names():
            raise RuntimeError("Post-migration schema validation failed.")
        after = _product_snapshot(engine)
        if after != before:
            raise RuntimeError("Existing PRODUCT data changed during schema migration.")
        with Session(engine) as session:
            history_count = session.scalar(select(func.count()).select_from(ProductIdentityChangeModel))
        if history_count != 0:
            raise RuntimeError("New identity history table was not empty.")
        print(f"POSTCHECK: {len(after)} PRODUCT rows unchanged; empty identity history; revision {current}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
