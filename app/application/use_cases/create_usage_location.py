"""Use case for creating an active usage location."""

from collections.abc import Callable
from uuid import uuid4

from app.application.dto import CreateUsageLocationInput
from app.application.ports import UsageLocationRepositoryPort
from app.domain.models import UsageLocation


def new_location_id() -> str:
    return str(uuid4())


class CreateUsageLocation:
    def __init__(
        self,
        repository: UsageLocationRepositoryPort,
        id_factory: Callable[[], str] = new_location_id,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory

    def execute(self, data: CreateUsageLocationInput) -> UsageLocation:
        location = UsageLocation(
            location_id=self._id_factory(),
            location_name=data.location_name,
        )
        self._repository.add(location)
        return location
