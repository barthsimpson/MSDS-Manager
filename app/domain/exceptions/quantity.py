"""Exceptions raised by domain quantity rules."""


class MixedQuantityUnitsError(ValueError):
    """Raised when quantities with different units cannot be summed."""
