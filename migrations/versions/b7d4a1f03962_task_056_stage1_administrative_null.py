"""Allow true Stage 1 administrative NULL snapshots.

Revision ID: b7d4a1f03962
Revises: c6a8f1d2940e
"""

from alembic import op
import sqlalchemy as sa


revision = "b7d4a1f03962"
down_revision = "c6a8f1d2940e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("products", "product_history"):
        for column in ("use_description", "use_restriction"):
            op.alter_column(
                table, column, existing_type=sa.String(),
                existing_nullable=False, nullable=True,
            )


def downgrade() -> None:
    for table in ("product_history", "products"):
        for column in ("use_restriction", "use_description"):
            op.alter_column(
                table, column, existing_type=sa.String(),
                existing_nullable=True, nullable=False,
            )
