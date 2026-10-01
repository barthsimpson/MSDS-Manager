"""Add source filename metadata to decision evidence.

Revision ID: b379f54c12a0
Revises: a97e2cb7f31d
"""

from alembic import op
import sqlalchemy as sa


revision = "b379f54c12a0"
down_revision = "a97e2cb7f31d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Historical evidence has no reliably recoverable source filename.
    # New registrations require it at the Application boundary.
    op.add_column(
        "decision_evidence",
        sa.Column("original_filename", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("decision_evidence", "original_filename")
