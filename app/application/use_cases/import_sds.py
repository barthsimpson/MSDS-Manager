"""Orchestrate one controlled PDF import and existing SDS registration."""

from collections.abc import Callable
from dataclasses import replace
from typing import TypeVar

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput
from app.application.ports import SdsPdfStoragePort
from app.application.use_cases.accept_sds import AcceptSds
from app.application.use_cases.add_sds_revision import AddSdsRevision


Registration = AcceptSdsInput | AddSdsRevisionInput
Result = TypeVar("Result")


class SdsImportCleanupError(RuntimeError):
    """Registration failed and its unregistered PDF could not be removed."""

    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        super().__init__(f"Import SDS nieudany; osierocony plik: {relative_path}")


class ImportSds:
    def __init__(self, storage: SdsPdfStoragePort) -> None:
        self._storage = storage

    def execute(
        self,
        data: Registration,
        original_filename: str,
        pdf_bytes: bytes,
        register: Callable[[Registration], Result],
        verify_product: Callable[[str], None] | None = None,
    ) -> Result:
        # Existing registration rules are checked before the filesystem is touched.
        pending = replace(data, source_relative_path="pending.pdf")
        if isinstance(data, AcceptSdsInput):
            AcceptSds._validate(pending)
        else:
            AddSdsRevision._validate(pending)
            if verify_product is None:
                raise ValueError("Product verification is required for an SDS revision.")
            verify_product(data.product_id)

        if not isinstance(original_filename, str) or not original_filename or (
            "/" in original_filename or "\\" in original_filename or ":" in original_filename
            or original_filename in {".", ".."}
        ):
            raise ValueError("Podaj nazwę pliku PDF bez ścieżki.")
        if not original_filename.lower().endswith(".pdf"):
            raise ValueError("Plik SDS musi mieć rozszerzenie .pdf.")
        if not isinstance(pdf_bytes, bytes) or not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("Plik SDS jest pusty lub nie ma sygnatury PDF.")

        relative_path = self._storage.store_new_pdf(pdf_bytes)
        try:
            self._storage.confirm_exists(relative_path)
            return register(replace(
                data, source_relative_path=relative_path,
                original_filename=original_filename,
            ))
        except Exception:
            try:
                self._storage.remove_unregistered_file(relative_path)
            except Exception as cleanup_error:
                raise SdsImportCleanupError(relative_path) from cleanup_error
            raise
