"""Application port for the supervisory read model."""

from typing import Protocol

from app.application.dto import SupervisoryProductRow


class SupervisoryQueryPort(Protocol):
    def list_products(self) -> list[SupervisoryProductRow]:
        """Read current facts, without assessing action reasons or writing Core.

        Raise SupervisoryReadError if CURRENT cannot be selected unambiguously.
        Only ListSupervisoryProducts returns assessed rows for consumers.
        """
        ...
