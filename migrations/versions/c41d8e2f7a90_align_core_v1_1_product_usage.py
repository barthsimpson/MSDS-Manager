"""align core v1.1 product usage

Revision ID: c41d8e2f7a90
Revises: bae33dc76391
Create Date: 2026-08-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c41d8e2f7a90"
down_revision: Union[str, None] = "bae33dc76391"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("waste_type", sa.String(), nullable=True))
    op.add_column("products", sa.Column("waste_code", sa.String(), nullable=True))

    op.alter_column(
        "product_usage_locations",
        "quantity_value",
        new_column_name="peak_quantity_value",
    )
    op.alter_column(
        "product_usage_locations",
        "quantity_unit",
        new_column_name="peak_quantity_unit",
    )
    op.add_column(
        "product_usage_locations",
        sa.Column("monthly_consumption_value", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "product_usage_locations",
        sa.Column("monthly_consumption_unit", sa.String(), nullable=True),
    )
    op.create_check_constraint(
        "ck_product_usage_locations_peak_quantity_nonnegative",
        "product_usage_locations",
        "peak_quantity_value >= 0",
    )
    op.create_check_constraint(
        "ck_product_usage_locations_monthly_consumption_nonnegative",
        "product_usage_locations",
        "monthly_consumption_value IS NULL OR monthly_consumption_value >= 0",
    )
    op.create_check_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations",
        "(monthly_consumption_value IS NULL "
        "AND monthly_consumption_unit IS NULL) "
        "OR (monthly_consumption_value IS NOT NULL "
        "AND monthly_consumption_unit IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_product_usage_locations_monthly_consumption_pair",
        "product_usage_locations",
        type_="check",
    )
    op.drop_constraint(
        "ck_product_usage_locations_monthly_consumption_nonnegative",
        "product_usage_locations",
        type_="check",
    )
    op.drop_constraint(
        "ck_product_usage_locations_peak_quantity_nonnegative",
        "product_usage_locations",
        type_="check",
    )
    op.drop_column("product_usage_locations", "monthly_consumption_unit")
    op.drop_column("product_usage_locations", "monthly_consumption_value")
    op.alter_column(
        "product_usage_locations",
        "peak_quantity_unit",
        new_column_name="quantity_unit",
    )
    op.alter_column(
        "product_usage_locations",
        "peak_quantity_value",
        new_column_name="quantity_value",
    )

    op.drop_column("products", "waste_code")
    op.drop_column("products", "waste_type")
