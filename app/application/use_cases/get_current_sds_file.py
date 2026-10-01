"""Read the registered CURRENT SDS for one product."""

from dataclasses import dataclass
from typing import Protocol

from app.application.exceptions import EntityNotFoundError


@dataclass(frozen=True, slots=True)
class CurrentSdsReference:
    original_filename: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class CurrentSdsFile:
    original_filename: str
    content: bytes


class CurrentSdsQueryPort(Protocol):
    def product_exists(self, product_id: str) -> bool: ...

    def get_current(self, product_id: str) -> CurrentSdsReference | None: ...


class SdsReadPort(Protocol):
    def read_sds(self, relative_path: str) -> bytes: ...


class GetCurrentSdsFile:
    def __init__(self, query: CurrentSdsQueryPort, storage: SdsReadPort) -> None:
        self._query = query
        self._storage = storage

    def execute(self, product_id: str) -> CurrentSdsFile | None:
        if not self._query.product_exists(product_id):
            raise EntityNotFoundError("PRODUCT", product_id)
        reference = self._query.get_current(product_id)
        if reference is None:
            return None
        if not reference.original_filename or not reference.relative_path:
            raise ValueError("Incomplete CURRENT SDS file metadata.")
        return CurrentSdsFile(
            original_filename=reference.original_filename,
            content=self._storage.read_sds(reference.relative_path),
        )
