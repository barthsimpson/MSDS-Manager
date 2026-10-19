"""SQLAlchemy SELECT-only identity queries for Evidence JSON planning."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.evidence_json import IdentityRecord
from app.infrastructure.db.models import ManufacturerModel, ProductModel


class SqlAlchemyEvidenceIdentityRead:
    def __init__(self, session: Session) -> None:
        self._session = session

    def manufacturers_named(self, name: str) -> tuple[IdentityRecord, ...]:
        rows = self._session.scalars(
            select(ManufacturerModel)
            .where(ManufacturerModel.manufacturer_name == name)
            .order_by(ManufacturerModel.manufacturer_id)
        ).all()
        return tuple(IdentityRecord(row.manufacturer_id, row.manufacturer_name) for row in rows)

    def similar_manufacturers(self, name: str) -> tuple[IdentityRecord, ...]:
        # Diagnostics only. Similarity never establishes identity.
        token = name.split(" ", 1)[0]
        rows = self._session.scalars(
            select(ManufacturerModel)
            .where(ManufacturerModel.manufacturer_name != name)
            .where(ManufacturerModel.manufacturer_name.icontains(token, autoescape=True))
            .order_by(ManufacturerModel.manufacturer_id)
        ).all()
        return tuple(IdentityRecord(row.manufacturer_id, row.manufacturer_name) for row in rows)

    def products_named(self, name: str) -> tuple[IdentityRecord, ...]:
        rows = self._session.scalars(
            select(ProductModel)
            .where(ProductModel.product_name == name)
            .order_by(ProductModel.product_id)
        ).all()
        return tuple(
            IdentityRecord(row.product_id, row.product_name, row.manufacturer_product_code)
            for row in rows
        )

    def products_for_manufacturer(
        self, name: str, manufacturer_id: str, code: str | None
    ) -> tuple[IdentityRecord, ...]:
        query = select(ProductModel).where(
            ProductModel.product_name == name,
            ProductModel.manufacturer_id == manufacturer_id,
        )
        if code is not None:
            query = query.where(ProductModel.manufacturer_product_code == code)
        rows = self._session.scalars(query.order_by(ProductModel.product_id)).all()
        return tuple(
            IdentityRecord(row.product_id, row.product_name, row.manufacturer_product_code)
            for row in rows
        )
