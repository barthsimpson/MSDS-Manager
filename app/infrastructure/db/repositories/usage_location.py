"""SQLAlchemy adapter for usage-location application contracts."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.ports import UsageLocationRepositoryPort
from app.domain.models import UsageLocation
from app.infrastructure.db.models import UsageLocationModel


def _to_domain(model: UsageLocationModel) -> UsageLocation:
    return UsageLocation(
        location_id=model.location_id,
        location_name=model.location_name,
        status=model.status,
    )


class SqlAlchemyUsageLocationRepository(UsageLocationRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[UsageLocation]:
        models = self._session.scalars(
            select(UsageLocationModel).order_by(UsageLocationModel.location_id)
        ).all()
        return [_to_domain(model) for model in models]

    def get_by_id(self, location_id: str) -> UsageLocation | None:
        model = self._session.get(UsageLocationModel, location_id)
        return None if model is None else _to_domain(model)

    def add(self, location: UsageLocation) -> None:
        self._session.add(
            UsageLocationModel(
                location_id=location.location_id,
                location_name=location.location_name,
                status=location.status,
            )
        )

    def update_status(self, location: UsageLocation) -> None:
        self._session.execute(
            update(UsageLocationModel)
            .where(UsageLocationModel.location_id == location.location_id)
            .values(status=location.status)
        )
