"""Application-facing persistence needs for manufacturers."""

from typing import Protocol

from app.domain.models import Manufacturer


class ManufacturerRepositoryPort(Protocol):
    """Minimal manufacturer read capability required by the application."""

    def list_all(self) -> list[Manufacturer]:
        """Return all manufacturers as domain models."""

        ...
