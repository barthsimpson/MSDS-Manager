"""Bind one Evidence JSON to a PDF from a controlled batch manifest."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath


@dataclass(frozen=True, slots=True)
class SourcePdfBinding:
    status: str
    filename: str | None = None
    content: bytes | None = None
    expected_sha256: str | None = None

    @property
    def signature(self) -> tuple[str, str | None, str | None]:
        return self.status, self.filename, sha256(self.content).hexdigest() if self.content else None


def _plain_filename(value: object) -> bool:
    return (
        isinstance(value, str) and bool(value) and value not in {".", ".."}
        and Path(value).name == value and PureWindowsPath(value).name == value
        and not any(char in value for char in ("/", "\\", ":", "\x00"))
    )


def _sha256(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdefABCDEF" for char in value))


def _verified_pdf(filename: str, content: bytes, expected_sha256: str, status: str) -> SourcePdfBinding:
    if (not filename.lower().endswith(".pdf") or not content.startswith(b"%PDF-")
            or sha256(content).hexdigest().casefold() != expected_sha256.casefold()):
        return SourcePdfBinding("PDF_MISMATCH", expected_sha256=expected_sha256)
    return SourcePdfBinding(status, filename, content, expected_sha256)


def resolve_source_pdf(
    manifest_path: Path, json_filename: str, payload: dict,
    fallback: tuple[str, bytes] | None = None,
    source_root: Path | None = None,
) -> SourcePdfBinding:
    """Use exact manifest identity/hash; optionally override only its input directory."""
    source = payload.get("source") if isinstance(payload, dict) else None
    if not isinstance(source, dict):
        return SourcePdfBinding("INVALID_SOURCE")
    filename, expected_sha256 = source.get("original_filename"), source.get("file_sha256")
    if (not _plain_filename(json_filename) or not _plain_filename(filename)
            or not filename.lower().endswith(".pdf") or not _sha256(expected_sha256)):
        return SourcePdfBinding("INVALID_SOURCE")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        manifest = None
    if isinstance(manifest, dict) and manifest.get("batch") == "BATCH-001_CX":
        entries = manifest.get("files")
        matches = [item for item in entries if isinstance(item, dict) and item.get("json") == json_filename] \
            if isinstance(entries, list) else []
        if len(matches) > 1:
            return SourcePdfBinding("PDF_MISMATCH", expected_sha256=expected_sha256)
        if matches:
            entry = matches[0]
            if (entry.get("source_file") != filename
                    or not _sha256(entry.get("sha256"))
                    or entry["sha256"].casefold() != expected_sha256.casefold()):
                return SourcePdfBinding("PDF_MISMATCH", expected_sha256=expected_sha256)
            directory = manifest.get("input_directory")
            if source_root is not None or isinstance(directory, str) and directory:
                root = Path(source_root) if source_root is not None else Path(directory)
                if root.is_absolute() and root.is_dir():
                    resolved_root = root.resolve()
                    candidate = (root / filename).resolve()
                    if not candidate.is_relative_to(resolved_root):
                        return SourcePdfBinding("PDF_MISMATCH", expected_sha256=expected_sha256)
                    try:
                        if candidate.is_file():
                            return _verified_pdf(filename, candidate.read_bytes(),
                                                 expected_sha256, "AUTO_BOUND")
                    except OSError:
                        pass

    if fallback is None:
        return SourcePdfBinding("FALLBACK_REQUIRED", expected_sha256=expected_sha256)
    fallback_name, fallback_content = fallback
    if not _plain_filename(fallback_name) or not isinstance(fallback_content, bytes):
        return SourcePdfBinding("PDF_MISMATCH", expected_sha256=expected_sha256)
    return _verified_pdf(fallback_name, fallback_content, expected_sha256, "MANUAL_BOUND")
