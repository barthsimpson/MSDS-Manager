"""Filesystem validation for BHP decision evidence references."""

from pathlib import Path

from app.application.exceptions import (
    InvalidEvidenceFileTypeError,
    SdsFileNotFoundError,
    SdsOutsideRootPathError,
)
from app.application.ports import BhpEvidenceValidatorPort


ALLOWED_EVIDENCE_SUFFIXES = {".msg", ".pdf", ".jpg", ".jpeg", ".png"}


class BhpEvidenceValidator(BhpEvidenceValidatorPort):
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path.resolve()

    def validate(self, evidence_relative_path: str) -> str:
        candidate = Path(evidence_relative_path)
        if candidate.is_absolute():
            raise SdsOutsideRootPathError("Evidence path must be relative.")
        resolved = (self._root_path / candidate).resolve()
        try:
            relative = resolved.relative_to(self._root_path)
        except ValueError as error:
            raise SdsOutsideRootPathError(
                f"Evidence path is outside configured root: {evidence_relative_path}"
            ) from error
        if not resolved.is_file():
            raise SdsFileNotFoundError(
                f"Evidence file does not exist: {evidence_relative_path}"
            )
        if resolved.suffix.lower() not in ALLOWED_EVIDENCE_SUFFIXES:
            raise InvalidEvidenceFileTypeError(
                f"Unsupported evidence file type: {resolved.suffix}"
            )
        return relative.as_posix()