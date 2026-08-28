"""SQLAlchemy adapter for manufacturer reads."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports import ManufacturerRepositoryPort
from app.domain.models import Manufacturer
from app.infrastructure.db.models import ManufacturerModel


class SqlAlchemyManufacturerRepository(ManufacturerRepositoryPort):
    """Read manufacturers using an externally owned SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Manufacturer]:
        models = self._session.scalars(select(ManufacturerModel)).all()
        return [
            Manufacturer(
                manufacturer_id=model.manufacturer_id,
                manufacturer_name=model.manufacturer_name,
            )
            for model in models
        ]
