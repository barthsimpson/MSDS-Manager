"""Allow unknown manufacturer code and audit explicit identity changes.

Revision ID: c6a8f1d2940e
Revises: 9f62c4e8b7a1
"""

from alembic import op
import sqlalchemy as sa


revision = "c6a8f1d2940e"
down_revision = "9f62c4e8b7a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "products", "manufacturer_product_code",
        existing_type=sa.String(), existing_nullable=False, nullable=True,
    )
    op.create_table(
        "product_identity_changes",
        sa.Column("change_id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("change_kind", sa.String(), nullable=False),
        sa.Column("old_product_name", sa.String(), nullable=False),
        sa.Column("new_product_name", sa.String(), nullable=False),
        sa.Column("old_manufacturer_product_code", sa.String(), nullable=True),
        sa.Column("new_manufacturer_product_code", sa.String(), nullable=True),
        sa.Column("old_manufacturer_id", sa.String(), nullable=False),
        sa.Column("new_manufacturer_id", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "change_kind IN ('CODE_COMPLETION', 'CORRECTION')",
            name="ck_product_identity_changes_change_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("product_identity_changes")
    op.alter_column(
        "products", "manufacturer_product_code",
        existing_type=sa.String(), existing_nullable=True, nullable=False,
    )
