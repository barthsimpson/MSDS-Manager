"""task 015 history tables

Revision ID: e0dd7d6468bf
Revises: d2b4f6a8c190
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0dd7d6468bf"
down_revision: Union[str, None] = "d2b4f6a8c190"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_history",
        sa.Column("history_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column(
            "usage_status",
            sa.Enum(
                "PENDING_APPROVAL",
                "ACTIVE",
                "REJECTED",
                "INACTIVE",
                name="product_usage_status_values",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("use_description", sa.String(), nullable=False),
        sa.Column("use_restriction", sa.String(), nullable=False),
        sa.Column("waste_type", sa.String(), nullable=True),
        sa.Column("waste_code", sa.String(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_table(
        "usage_location_history",
        sa.Column("history_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "INACTIVE",
                name="usage_location_status_values",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["usage_locations.location_id"]),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_table(
        "product_usage_location_history",
        sa.Column("history_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("peak_quantity_value", sa.Numeric(), nullable=False),
        sa.Column("peak_quantity_unit", sa.String(), nullable=False),
        sa.Column("monthly_consumption_value", sa.Numeric(), nullable=True),
        sa.Column("monthly_consumption_unit", sa.String(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.ForeignKeyConstraint(["location_id"], ["usage_locations.location_id"]),
        sa.PrimaryKeyConstraint("history_id"),
    )

    op.create_index(
        "ix_product_history_product_id_changed_at",
        "product_history",
        ["product_id", "changed_at"],
    )
    op.create_index(
        "ix_usage_location_history_location_id_changed_at",
        "usage_location_history",
        ["location_id", "changed_at"],
    )
    op.create_index(
        "ix_product_usage_location_history_product_location_changed_at",
        "product_usage_location_history",
        ["product_id", "location_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_usage_location_history_product_location_changed_at",
        table_name="product_usage_location_history",
    )
    op.drop_index(
        "ix_usage_location_history_location_id_changed_at",
        table_name="usage_location_history",
    )
    op.drop_index(
        "ix_product_history_product_id_changed_at",
        table_name="product_history",
    )
    op.drop_table("product_usage_location_history")
    op.drop_table("usage_location_history")
    op.drop_table("product_history")
