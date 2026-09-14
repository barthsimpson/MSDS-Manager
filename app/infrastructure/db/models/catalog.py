"""Persistence mappings for manufacturers, products, and usage locations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ProductUsageStatus, UsageLocationStatus

from .base import Base
from .column_types import enum_column_type


class ManufacturerModel(Base):
    __tablename__ = "manufacturers"

    manufacturer_id: Mapped[str] = mapped_column(String, primary_key=True)
    manufacturer_name: Mapped[str] = mapped_column(String, nullable=False)

    products: Mapped[list[ProductModel]] = relationship(back_populates="manufacturer")


class ProductModel(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    manufacturer_product_code: Mapped[str] = mapped_column(String, nullable=False)
    manufacturer_id: Mapped[str] = mapped_column(
        ForeignKey("manufacturers.manufacturer_id"), nullable=False
    )
    use_description: Mapped[str] = mapped_column(String, nullable=False)
    use_restriction: Mapped[str] = mapped_column(String, nullable=False)
    usage_status: Mapped[ProductUsageStatus] = mapped_column(
        enum_column_type(ProductUsageStatus, "product_usage_status_values"),
        nullable=False,
    )
    waste_type: Mapped[str | None] = mapped_column(String, nullable=True)
    waste_code: Mapped[str | None] = mapped_column(String, nullable=True)

    manufacturer: Mapped[ManufacturerModel] = relationship(back_populates="products")
    product_usage_locations: Mapped[list[ProductUsageLocationModel]] = relationship(
        back_populates="product"
    )
    sds_documents: Mapped[list[SdsDocumentModel]] = relationship(
        back_populates="product"
    )
    bhp_decisions: Mapped[list[BhpDecisionModel]] = relationship(
        back_populates="product", overlaps="sds_document"
    )


class UsageLocationModel(Base):
    __tablename__ = "usage_locations"

    location_id: Mapped[str] = mapped_column(String, primary_key=True)
    location_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[UsageLocationStatus] = mapped_column(
        enum_column_type(UsageLocationStatus, "usage_location_status_values"),
        nullable=False,
    )

    product_usage_locations: Mapped[list[ProductUsageLocationModel]] = relationship(
        back_populates="location"
    )


class ProductUsageLocationModel(Base):
    __tablename__ = "product_usage_locations"
    __table_args__ = (
        CheckConstraint(
            "peak_quantity_value >= 0",
            name="ck_product_usage_locations_peak_quantity_nonnegative",
        ),
        CheckConstraint(
            "monthly_consumption_value IS NULL "
            "OR monthly_consumption_value >= 0",
            name="ck_product_usage_locations_monthly_consumption_nonnegative",
        ),
        CheckConstraint(
            "(monthly_consumption_value IS NULL "
            "AND monthly_consumption_unit IS NULL) "
            "OR (monthly_consumption_value IS NOT NULL "
            "AND monthly_consumption_unit IS NOT NULL)",
            name="ck_product_usage_locations_monthly_consumption_pair",
        ),
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )
    location_id: Mapped[str] = mapped_column(
        ForeignKey("usage_locations.location_id"), primary_key=True
    )
    peak_quantity_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    peak_quantity_unit: Mapped[str] = mapped_column(String, nullable=False)
    monthly_consumption_value: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    monthly_consumption_unit: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    product: Mapped[ProductModel] = relationship(
        back_populates="product_usage_locations"
    )
    location: Mapped[UsageLocationModel] = relationship(
        back_populates="product_usage_locations"
    )


class ProductHistoryModel(Base):
    __tablename__ = "product_history"
    __table_args__ = (
        Index("ix_product_history_product_id_changed_at", "product_id", "changed_at"),
    )

    history_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    usage_status: Mapped[ProductUsageStatus] = mapped_column(
        enum_column_type(ProductUsageStatus, "product_usage_status_values"),
        nullable=False,
    )
    use_description: Mapped[str] = mapped_column(String, nullable=False)
    use_restriction: Mapped[str] = mapped_column(String, nullable=False)
    waste_type: Mapped[str | None] = mapped_column(String, nullable=True)
    waste_code: Mapped[str | None] = mapped_column(String, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UsageLocationHistoryModel(Base):
    __tablename__ = "usage_location_history"
    __table_args__ = (
        Index("ix_usage_location_history_location_id_changed_at", "location_id", "changed_at"),
    )

    history_id: Mapped[str] = mapped_column(String, primary_key=True)
    location_id: Mapped[str] = mapped_column(ForeignKey("usage_locations.location_id"), nullable=False)
    status: Mapped[UsageLocationStatus] = mapped_column(
        enum_column_type(UsageLocationStatus, "usage_location_status_values"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ProductUsageLocationHistoryModel(Base):
    __tablename__ = "product_usage_location_history"
    __table_args__ = (
        Index(
            "ix_product_usage_location_history_product_location_changed_at",
            "product_id",
            "location_id",
            "changed_at",
        ),
    )

    history_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("usage_locations.location_id"), nullable=False)
    peak_quantity_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    peak_quantity_unit: Mapped[str] = mapped_column(String, nullable=False)
    monthly_consumption_value: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    monthly_consumption_unit: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


from .documents import BhpDecisionModel, SdsDocumentModel  # noqa: E402
