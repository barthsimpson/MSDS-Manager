"""Persistence mappings for manufacturers, products, and usage locations."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ProductUsageStatus

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
    status: Mapped[str] = mapped_column(String, nullable=False)

    product_usage_locations: Mapped[list[ProductUsageLocationModel]] = relationship(
        back_populates="location"
    )


class ProductUsageLocationModel(Base):
    __tablename__ = "product_usage_locations"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )
    location_id: Mapped[str] = mapped_column(
        ForeignKey("usage_locations.location_id"), primary_key=True
    )
    quantity_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String, nullable=False)

    product: Mapped[ProductModel] = relationship(
        back_populates="product_usage_locations"
    )
    location: Mapped[UsageLocationModel] = relationship(
        back_populates="product_usage_locations"
    )


from .documents import BhpDecisionModel, SdsDocumentModel  # noqa: E402
