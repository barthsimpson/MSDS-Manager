"""Use case for creating an active usage location."""

from collections.abc import Callable
import re
from uuid import uuid4

from app.application.dto import CreateUsageLocationInput
from app.application.exceptions import DuplicateLocationCodeError
from app.application.ports import UsageLocationRepositoryPort
from app.domain.models import UsageLocation


def new_location_id() -> str:
    return str(uuid4())


def normalize_location_code(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("location_code is required.")
    location_code = value.strip().upper()
    if re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{0,31}", location_code) is None:
        raise ValueError("location_code must match ^[A-Z0-9][A-Z0-9_-]{0,31}$.")
    return location_code


class CreateUsageLocation:
    def __init__(
        self,
        repository: UsageLocationRepositoryPort,
        id_factory: Callable[[], str] = new_location_id,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory

    def execute(self, data: CreateUsageLocationInput) -> UsageLocation:
        location_code = normalize_location_code(data.location_code)
        if self._repository.get_by_code(location_code) is not None:
            raise DuplicateLocationCodeError(location_code)
        location = UsageLocation(
            location_id=self._id_factory(),
            location_name=data.location_name,
            location_code=location_code,
        )
        self._repository.add(location)
        return location
