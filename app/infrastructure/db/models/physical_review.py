"""Persistence mapping for physical review snapshots."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Uuid, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PhysicalReviewModel(Base):
    __tablename__ = "physical_reviews"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'FINAL')", name="ck_physical_reviews_status"),
        CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL) "
            "OR (status = 'FINAL' AND finalized_at IS NOT NULL)",
            name="ck_physical_reviews_finalized_at",
        ),
        Index("ix_physical_reviews_status", "status"),
        Index("ix_physical_reviews_date_finalized", "review_date", "finalized_at"),
        Index(
            "uq_physical_reviews_single_draft", "status", unique=True,
            postgresql_where=text("status = 'DRAFT'"),
        ),
    )

    review_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["PhysicalReviewItemModel"]] = relationship(back_populates="review")


class PhysicalReviewItemModel(Base):
    __tablename__ = "physical_review_items"
    __table_args__ = (
        CheckConstraint(
            "baseline_max_quantity >= 0",
            name="ck_physical_review_items_baseline_nonnegative",
        ),
        CheckConstraint(
            "observed_quantity IS NULL OR observed_quantity >= 0",
            name="ck_physical_review_items_observed_nonnegative",
        ),
        UniqueConstraint(
            "review_id", "product_id", "location_id",
            name="uq_physical_review_items_review_product_location",
        ),
        Index("ix_physical_review_items_review_id", "review_id"),
        Index(
            "ix_physical_review_items_product_location_review",
            "product_id", "location_id", "review_id",
        ),
    )

    review_item_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey(
            "physical_reviews.review_id", name="fk_physical_review_items_review_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey(
            "products.product_id", name="fk_physical_review_items_product_id",
            ondelete="RESTRICT",
        ), nullable=False,
    )
    location_id: Mapped[str] = mapped_column(
        String, ForeignKey(
            "usage_locations.location_id", name="fk_physical_review_items_location_id",
            ondelete="RESTRICT",
        ), nullable=False,
    )
    baseline_max_quantity: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    baseline_unit_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey(
            "unit_of_measure.unit_id", name="fk_physical_review_items_baseline_unit_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    observed_quantity: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)

    review: Mapped[PhysicalReviewModel] = relationship(back_populates="items")
