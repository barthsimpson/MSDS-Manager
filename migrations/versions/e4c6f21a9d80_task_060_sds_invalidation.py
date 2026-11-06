"""Add controlled SDS invalidation and its immutable audit record.

Revision ID: e4c6f21a9d80
Revises: b7d4a1f03962
"""

from alembic import op
import sqlalchemy as sa


revision = "e4c6f21a9d80"
down_revision = "b7d4a1f03962"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("sds_document_status_values", "sds_documents", type_="check")
    op.alter_column(
        "sds_documents", "document_status",
        existing_type=sa.String(length=8), type_=sa.String(length=11),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "sds_document_status_values", "sds_documents",
        "document_status IN ('CURRENT', 'ARCHIVED', 'INVALIDATED')",
    )
    op.create_table(
        "sds_invalidation",
        sa.Column("invalidation_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("invalidated_sds_id", sa.String(), sa.ForeignKey("sds_documents.sds_id"), nullable=False),
        sa.Column("invalidated_from_status", sa.String(), nullable=False),
        sa.Column("restored_sds_id", sa.String(), sa.ForeignKey("sds_documents.sds_id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("invalidated_sds_id", name="uq_sds_invalidation_sds"),
        sa.CheckConstraint(
            "invalidated_from_status IN ('CURRENT', 'ARCHIVED')",
            name="ck_sds_invalidation_from_status",
        ),
        sa.CheckConstraint("length(btrim(reason)) > 0", name="ck_sds_invalidation_reason"),
        sa.CheckConstraint(
            "restored_sds_id IS NULL OR restored_sds_id <> invalidated_sds_id",
            name="ck_sds_invalidation_distinct_sds",
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    audit_count = bind.execute(sa.text("SELECT count(*) FROM sds_invalidation")).scalar_one()
    invalidated_count = bind.execute(sa.text(
        "SELECT count(*) FROM sds_documents WHERE document_status = 'INVALIDATED'"
    )).scalar_one()
    if audit_count or invalidated_count:
        raise RuntimeError("Cannot downgrade SDS invalidation with INVALIDATED SDS or audit data.")
    op.drop_table("sds_invalidation")
    op.drop_constraint("sds_document_status_values", "sds_documents", type_="check")
    op.alter_column(
        "sds_documents", "document_status",
        existing_type=sa.String(length=11), type_=sa.String(length=8),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "sds_document_status_values", "sds_documents",
        "document_status IN ('CURRENT', 'ARCHIVED')",
    )
