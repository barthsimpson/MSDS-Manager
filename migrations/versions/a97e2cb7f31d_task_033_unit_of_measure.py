"""Add the controlled unit of measure dictionary and quantity references.

Revision ID: a97e2cb7f31d
Revises: e0dd7d6468bf
"""

from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa


revision = "a97e2cb7f31d"
down_revision = "e0dd7d6468bf"
branch_labels = None
depends_on = None


_SEED = (
    ("l", "litr", "VOLUME"),
    ("ml", "mililitr", "VOLUME"),
    ("kg", "kilogram", "MASS"),
    ("g", "gram", "MASS"),
    ("szt", "sztuka", "COUNT"),
)


def _require_empty_usage_tables() -> None:
    connection = op.get_bind()
    for table_name in ("product_usage_locations", "product_usage_location_history"):
        # Fixed migration-owned names; no user input is interpolated.
        has_rows = connection.scalar(sa.text(f"SELECT EXISTS (SELECT 1 FROM {table_name})"))
        if has_rows:
            raise RuntimeError(
                f"TASK-033 requires an empty {table_name}; existing unit text cannot be mapped automatically."
            )


def upgrade() -> None:
    _require_empty_usage_tables()

    op.create_table(
        "unit_of_measure",
        sa.Column("unit_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.UniqueConstraint("code", name="uq_unit_of_measure_code"),
        sa.CheckConstraint(
            "category IN ('VOLUME', 'MASS', 'COUNT')",
            name="ck_unit_of_measure_category",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_unit_of_measure_status",
        ),
    )
    seed_table = sa.table(
        "unit_of_measure",
        sa.column("unit_id", sa.Uuid(as_uuid=False)),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("category", sa.String()),
        sa.column("status", sa.String()),
    )
    op.bulk_insert(
        seed_table,
        [
            {
                "unit_id": str(uuid5(NAMESPACE_URL, f"msds-manager/unit-of-measure/{code}")),
                "code": code,
                "name": name,
                "category": category,
                "status": "ACTIVE",
            }
            for code, name, category in _SEED
        ],
    )

    op.add_column(
        "product_usage_locations",
        sa.Column("peak_quantity_unit_id", sa.Uuid(as_uuid=False), nullable=False),
    )
    op.add_column(
        "product_usage_locations",
        sa.Column("monthly_consumption_unit_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.add_column(
        "product_usage_location_history",
        sa.Column("peak_quantity_unit_id", sa.Uuid(as_uuid=False), nullable=False),
    )
    op.add_column(
        "product_usage_location_history",
        sa.Column("monthly_consumption_unit_id", sa.Uuid(as_uuid=False), nullable=True),
    )

    op.drop_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations",
        type_="check",
    )
    op.create_foreign_key(
        "fk_product_usage_locations_peak_quantity_unit_id",
        "product_usage_locations", "unit_of_measure",
        ["peak_quantity_unit_id"], ["unit_id"],
    )
    op.create_foreign_key(
        "fk_product_usage_locations_monthly_consumption_unit_id",
        "product_usage_locations", "unit_of_measure",
        ["monthly_consumption_unit_id"], ["unit_id"],
    )
    op.create_foreign_key(
        "fk_product_usage_location_history_peak_quantity_unit_id",
        "product_usage_location_history", "unit_of_measure",
        ["peak_quantity_unit_id"], ["unit_id"],
    )
    op.create_foreign_key(
        "fk_product_usage_location_history_monthly_consumption_unit_id",
        "product_usage_location_history", "unit_of_measure",
        ["monthly_consumption_unit_id"], ["unit_id"],
    )
    op.create_check_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations",
        "(monthly_consumption_value IS NULL AND monthly_consumption_unit_id IS NULL) "
        "OR (monthly_consumption_value IS NOT NULL AND monthly_consumption_unit_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_product_usage_location_history_monthly_consumption_pair",
        "product_usage_location_history",
        "(monthly_consumption_value IS NULL AND monthly_consumption_unit_id IS NULL) "
        "OR (monthly_consumption_value IS NOT NULL AND monthly_consumption_unit_id IS NOT NULL)",
    )
    op.drop_column("product_usage_locations", "peak_quantity_unit")
    op.drop_column("product_usage_locations", "monthly_consumption_unit")
    op.drop_column("product_usage_location_history", "peak_quantity_unit")
    op.drop_column("product_usage_location_history", "monthly_consumption_unit")


def downgrade() -> None:
    for table_name in ("product_usage_locations", "product_usage_location_history"):
        op.add_column(table_name, sa.Column("peak_quantity_unit", sa.String(), nullable=True))
        op.add_column(table_name, sa.Column("monthly_consumption_unit", sa.String(), nullable=True))
        op.execute(sa.text(
            f"UPDATE {table_name} AS usage SET "
            "peak_quantity_unit = (SELECT code FROM unit_of_measure "
            "WHERE unit_id = usage.peak_quantity_unit_id), "
            "monthly_consumption_unit = (SELECT code FROM unit_of_measure "
            "WHERE unit_id = usage.monthly_consumption_unit_id)"
        ))
        op.alter_column(table_name, "peak_quantity_unit", nullable=False)

    op.drop_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations", type_="check",
    )
    op.drop_constraint(
        "ck_product_usage_location_history_monthly_consumption_pair",
        "product_usage_location_history", type_="check",
    )
    for table_name in ("product_usage_locations", "product_usage_location_history"):
        for column_name in ("peak_quantity_unit_id", "monthly_consumption_unit_id"):
            op.drop_constraint(
                f"fk_{table_name}_{column_name}", table_name, type_="foreignkey"
            )
            op.drop_column(table_name, column_name)
    op.create_check_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations",
        "(monthly_consumption_value IS NULL AND monthly_consumption_unit IS NULL) "
        "OR (monthly_consumption_value IS NOT NULL AND monthly_consumption_unit IS NOT NULL)",
    )
    op.drop_table("unit_of_measure")
