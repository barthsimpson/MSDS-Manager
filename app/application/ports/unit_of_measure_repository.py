"""Application-facing reads of controlled units of measure."""

from typing import Protocol

from app.domain.models import UnitOfMeasure


class UnitOfMeasureRepositoryPort(Protocol):
    def get_by_id(self, unit_id: str) -> UnitOfMeasure | None: ...

    def list_active(self) -> list[UnitOfMeasure]: ...
