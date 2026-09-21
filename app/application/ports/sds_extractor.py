"""Ports for reading SDS data without coupling Application to PDF tooling."""

from pathlib import Path
from typing import Protocol

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput, ExtractedSdsData


class SdsExtractorPort(Protocol):
    def extract(self, pdf_path: Path) -> ExtractedSdsData:
        """Read the approved minimal SDS fields from a PDF reference."""


class SdsFileValidatorPort(Protocol):
    def validate(self, pdf_path: Path) -> str:
        """Validate and return the path relative to the configured SDS root."""

    def validate_relative(self, relative_path: str) -> Path:
        """Validate a stored relative path and return its resolved file path."""


class SdsAcceptanceRepositoryPort(Protocol):
    def accept(self, data: AcceptSdsInput) -> str:
        """Persist one already validated accepted SDS aggregate."""

    def accept_revision(self, data: AddSdsRevisionInput) -> str:
        """Persist a revision for an explicitly selected existing product."""
