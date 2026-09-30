"""Read-only SQLAlchemy adapter for controlled units of measure."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports import UnitOfMeasureRepositoryPort
from app.domain.enums import UnitCategory, UnitStatus
from app.domain.models import UnitOfMeasure
from app.infrastructure.db.models import UnitOfMeasureModel


def _to_domain(row: UnitOfMeasureModel) -> UnitOfMeasure:
    return UnitOfMeasure(
        unit_id=row.unit_id,
        code=row.code,
        name=row.name,
        category=UnitCategory(row.category),
        status=UnitStatus(row.status),
    )


class SqlAlchemyUnitOfMeasureRepository(UnitOfMeasureRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, unit_id: str) -> UnitOfMeasure | None:
        row = self._session.get(UnitOfMeasureModel, unit_id)
        return None if row is None else _to_domain(row)

    def list_active(self) -> list[UnitOfMeasure]:
        rows = self._session.scalars(
            select(UnitOfMeasureModel)
            .where(UnitOfMeasureModel.status == UnitStatus.ACTIVE)
            .order_by(UnitOfMeasureModel.code)
        ).all()
        return [_to_domain(row) for row in rows]
