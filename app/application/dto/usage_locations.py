"""Application input DTOs for usage locations."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateUsageLocationInput:
    location_name: str
