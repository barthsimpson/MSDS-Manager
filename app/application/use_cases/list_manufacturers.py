"""Use case for listing manufacturers."""

from app.application.ports import ManufacturerRepositoryPort
from app.domain.models import Manufacturer


class ListManufacturers:
    """Return manufacturers through an application-owned port."""

    def __init__(self, repository: ManufacturerRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[Manufacturer]:
        return self._repository.list_all()
