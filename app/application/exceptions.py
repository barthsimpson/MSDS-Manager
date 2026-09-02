"""Small, technology-independent errors exposed by application contracts."""


class EntityNotFoundError(LookupError):
    def __init__(self, entity_name: str, entity_id: str) -> None:
        super().__init__(f"{entity_name} not found: {entity_id}")


class InactiveUsageLocationError(ValueError):
    def __init__(self, location_id: str) -> None:
        super().__init__(f"Usage location is inactive: {location_id}")
