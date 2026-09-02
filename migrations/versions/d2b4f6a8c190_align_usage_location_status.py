"""align usage location status

Revision ID: d2b4f6a8c190
Revises: c41d8e2f7a90
Create Date: 2026-09-02
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d2b4f6a8c190"
down_revision: Union[str, None] = "c41d8e2f7a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "usage_location_status_values",
        "usage_locations",
        "status IN ('ACTIVE', 'INACTIVE')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "usage_location_status_values",
        "usage_locations",
        type_="check",
    )
