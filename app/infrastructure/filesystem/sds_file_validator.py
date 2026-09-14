"""Validation of SDS paths owned by the configured filesystem root."""

from pathlib import Path

from app.application.exceptions import (
    InvalidSdsFileTypeError,
    SdsFileNotFoundError,
    SdsOutsideRootPathError,
)
from app.application.ports import SdsFileValidatorPort


class SdsFileValidator(SdsFileValidatorPort):
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path.resolve()

    def validate(self, pdf_path: Path) -> str:
        return self._validate_path(pdf_path).relative_to(self._root_path).as_posix()

    def validate_relative(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise SdsOutsideRootPathError("SDS path must be relative.")
        return self._validate_path(self._root_path / candidate)

    def _validate_path(self, pdf_path: Path) -> Path:
        resolved = pdf_path.resolve()
        try:
            resolved.relative_to(self._root_path)
        except ValueError as error:
            raise SdsOutsideRootPathError(
                f"SDS path is outside configured root: {pdf_path}"
            ) from error
        if not resolved.is_file():
            raise SdsFileNotFoundError(f"SDS file does not exist: {pdf_path}")
        if resolved.suffix.lower() != ".pdf":
            raise InvalidSdsFileTypeError(f"SDS file is not a PDF: {pdf_path}")
        return resolved