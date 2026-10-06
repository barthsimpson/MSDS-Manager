"""Add nullable usage location business code without changing legacy rows.

Revision ID: c7e5a82d9043
Revises: b379f54c12a0
"""

from alembic import op
import sqlalchemy as sa


revision = "c7e5a82d9043"
down_revision = "b379f54c12a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usage_locations", sa.Column("location_code", sa.String(32), nullable=True)
    )
    op.create_check_constraint(
        "ck_usage_locations_location_code_format",
        "usage_locations",
        "location_code IS NULL OR location_code ~ '^[A-Z0-9][A-Z0-9_-]{0,31}$'",
    )
    op.create_unique_constraint(
        "uq_usage_locations_location_code", "usage_locations", ["location_code"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_usage_locations_location_code", "usage_locations", type_="unique"
    )
    op.drop_constraint(
        "ck_usage_locations_location_code_format", "usage_locations", type_="check"
    )
    op.drop_column("usage_locations", "location_code")
