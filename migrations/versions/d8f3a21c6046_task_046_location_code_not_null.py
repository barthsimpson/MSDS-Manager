"""Require a business code for every usage location.

Revision ID: d8f3a21c6046
Revises: c7e5a82d9043
"""

from alembic import op
import sqlalchemy as sa


revision = "d8f3a21c6046"
down_revision = "c7e5a82d9043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "usage_locations", "location_code",
        existing_type=sa.String(32), nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "usage_locations", "location_code",
        existing_type=sa.String(32), nullable=True,
    )
