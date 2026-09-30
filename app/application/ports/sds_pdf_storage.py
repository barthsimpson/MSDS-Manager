"""Storage contract for controlled SDS imports."""

from typing import Protocol


class SdsPdfStoragePort(Protocol):
    def store_new_pdf(self, pdf_bytes: bytes) -> str: ...

    def confirm_exists(self, relative_path: str) -> None: ...

    def remove_unregistered_file(self, relative_path: str) -> None: ...
