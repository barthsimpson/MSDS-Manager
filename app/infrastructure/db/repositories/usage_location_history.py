"""SQLAlchemy adapter for usage-location history snapshots."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports import UsageLocationHistoryRepositoryPort
from app.domain.models import UsageLocationHistory
from app.infrastructure.db.models import UsageLocationHistoryModel


class SqlAlchemyUsageLocationHistoryRepository(UsageLocationHistoryRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: UsageLocationHistory) -> None:
        self._session.add(
            UsageLocationHistoryModel(
                history_id=snapshot.history_id,
                location_id=snapshot.location_id,
                status=snapshot.status,
                changed_at=snapshot.changed_at,
            )
        )

    def get_by_location_id(self, location_id: str) -> list[UsageLocationHistory]:
        rows = self._session.execute(
            select(UsageLocationHistoryModel)
            .where(UsageLocationHistoryModel.location_id == location_id)
            .order_by(UsageLocationHistoryModel.changed_at.asc(), UsageLocationHistoryModel.history_id.asc())
        ).scalars().all()
        return [
            UsageLocationHistory(
                location_id=row.location_id,
                status=row.status,
                history_id=row.history_id,
                changed_at=row.changed_at,
            )
            for row in rows
        ]
