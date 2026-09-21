"""SQLAlchemy adapter for existing-product application contracts."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from uuid import uuid4

from app.application.dto import (
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    UpdateProductAdministrativeDataInput,
    UpdateProductIdentityInput,
)
from app.application.ports import ProductRepositoryPort
from app.infrastructure.db.models import (
    ManufacturerModel,
    ProductModel,
    ProductUsageLocationModel,
    UsageLocationModel,
)


def _product_list_item(
    product: ProductModel, manufacturer: ManufacturerModel
) -> ProductListItem:
    return ProductListItem(
        product_id=product.product_id,
        product_name=product.product_name,
        manufacturer_product_code=product.manufacturer_product_code,
        manufacturer_id=product.manufacturer_id,
        manufacturer_name=manufacturer.manufacturer_name,
        usage_status=product.usage_status,
        use_description=product.use_description,
        use_restriction=product.use_restriction,
        waste_type=product.waste_type,
        waste_code=product.waste_code,
    )


class SqlAlchemyProductRepository(ProductRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[ProductListItem]:
        rows = self._session.execute(
            select(ProductModel, ManufacturerModel)
            .join(
                ManufacturerModel,
                ProductModel.manufacturer_id == ManufacturerModel.manufacturer_id,
            )
            .order_by(ProductModel.product_id)
        ).all()
        return [_product_list_item(product, manufacturer) for product, manufacturer in rows]

    def get_details(self, product_id: str) -> ProductDetails | None:
        row = self._session.execute(
            select(ProductModel, ManufacturerModel)
            .join(
                ManufacturerModel,
                ProductModel.manufacturer_id == ManufacturerModel.manufacturer_id,
            )
            .where(ProductModel.product_id == product_id)
        ).one_or_none()
        if row is None:
            return None

        product, manufacturer = row
        location_rows = self._session.execute(
            select(ProductUsageLocationModel, UsageLocationModel)
            .join(
                UsageLocationModel,
                ProductUsageLocationModel.location_id
                == UsageLocationModel.location_id,
            )
            .where(ProductUsageLocationModel.product_id == product_id)
            .order_by(ProductUsageLocationModel.location_id)
        ).all()
        locations = tuple(
            ProductUsageLocationDetails(
                location_id=location.location_id,
                location_name=location.location_name,
                location_status=location.status,
                peak_quantity_value=assignment.peak_quantity_value,
                peak_quantity_unit=assignment.peak_quantity_unit,
                monthly_consumption_value=assignment.monthly_consumption_value,
                monthly_consumption_unit=assignment.monthly_consumption_unit,
            )
            for assignment, location in location_rows
        )
        item = _product_list_item(product, manufacturer)
        return ProductDetails(
            product_id=item.product_id,
            product_name=item.product_name,
            manufacturer_product_code=item.manufacturer_product_code,
            manufacturer_id=item.manufacturer_id,
            manufacturer_name=item.manufacturer_name,
            usage_status=item.usage_status,
            use_description=item.use_description,
            use_restriction=item.use_restriction,
            waste_type=item.waste_type,
            waste_code=item.waste_code,
            usage_locations=locations,
        )

    def update_administrative_data(
        self, data: UpdateProductAdministrativeDataInput
    ) -> bool:
        updated_id = self._session.scalar(
            update(ProductModel)
            .where(ProductModel.product_id == data.product_id)
            .values(
                use_description=data.use_description,
                use_restriction=data.use_restriction,
                waste_type=data.waste_type,
                waste_code=data.waste_code,
            )
            .returning(ProductModel.product_id)
        )
        return updated_id is not None

    def update_identity(self, data: UpdateProductIdentityInput) -> bool:
        product = self._session.get(ProductModel, data.product_id)
        if product is None:
            return False

        manufacturers = self._session.scalars(
            select(ManufacturerModel).where(
                ManufacturerModel.manufacturer_name == data.manufacturer_name
            )
        ).all()
        if len(manufacturers) > 1:
            raise ValueError("Manufacturer identity is ambiguous.")
        manufacturer = manufacturers[0] if manufacturers else ManufacturerModel(
            manufacturer_id=uuid4().hex,
            manufacturer_name=data.manufacturer_name,
        )
        if not manufacturers:
            self._session.add(manufacturer)
            self._session.flush()

        product.product_name = data.product_name
        product.manufacturer_product_code = data.manufacturer_product_code
        product.manufacturer_id = manufacturer.manufacturer_id
        self._session.flush()
        return True
