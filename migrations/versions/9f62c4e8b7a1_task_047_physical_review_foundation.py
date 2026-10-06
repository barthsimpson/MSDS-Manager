"""Add physical review snapshot foundation.

Revision ID: 9f62c4e8b7a1
Revises: d8f3a21c6046
"""

from alembic import op
import sqlalchemy as sa


revision = "9f62c4e8b7a1"
down_revision = "d8f3a21c6046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "physical_reviews",
        sa.Column("review_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'FINAL')", name="ck_physical_reviews_status"),
        sa.CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL) "
            "OR (status = 'FINAL' AND finalized_at IS NOT NULL)",
            name="ck_physical_reviews_finalized_at",
        ),
    )
    op.create_index("ix_physical_reviews_status", "physical_reviews", ["status"])
    op.create_index(
        "ix_physical_reviews_date_finalized", "physical_reviews",
        ["review_date", "finalized_at"],
    )
    op.create_index(
        "uq_physical_reviews_single_draft", "physical_reviews", ["status"],
        unique=True, postgresql_where=sa.text("status = 'DRAFT'"),
    )

    op.create_table(
        "physical_review_items",
        sa.Column("review_item_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("review_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("baseline_max_quantity", sa.Numeric(), nullable=False),
        sa.Column("baseline_unit_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("observed_quantity", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["review_id"], ["physical_reviews.review_id"],
            name="fk_physical_review_items_review_id", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.product_id"],
            name="fk_physical_review_items_product_id", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["usage_locations.location_id"],
            name="fk_physical_review_items_location_id", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["baseline_unit_id"], ["unit_of_measure.unit_id"],
            name="fk_physical_review_items_baseline_unit_id", ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "baseline_max_quantity >= 0",
            name="ck_physical_review_items_baseline_nonnegative",
        ),
        sa.CheckConstraint(
            "observed_quantity IS NULL OR observed_quantity >= 0",
            name="ck_physical_review_items_observed_nonnegative",
        ),
        sa.UniqueConstraint(
            "review_id", "product_id", "location_id",
            name="uq_physical_review_items_review_product_location",
        ),
    )
    op.create_index("ix_physical_review_items_review_id", "physical_review_items", ["review_id"])
    op.create_index(
        "ix_physical_review_items_product_location_review", "physical_review_items",
        ["product_id", "location_id", "review_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_physical_review_items_product_location_review", table_name="physical_review_items")
    op.drop_index("ix_physical_review_items_review_id", table_name="physical_review_items")
    op.drop_table("physical_review_items")
    op.drop_index("uq_physical_reviews_single_draft", table_name="physical_reviews")
    op.drop_index("ix_physical_reviews_date_finalized", table_name="physical_reviews")
    op.drop_index("ix_physical_reviews_status", table_name="physical_reviews")
    op.drop_table("physical_reviews")
