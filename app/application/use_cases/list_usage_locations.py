"""Use case for listing active and inactive usage locations."""

from app.application.ports import UsageLocationRepositoryPort
from app.domain.models import UsageLocation


class ListUsageLocations:
    def __init__(self, repository: UsageLocationRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[UsageLocation]:
        return self._repository.list_all()
