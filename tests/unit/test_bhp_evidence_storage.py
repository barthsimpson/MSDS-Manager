from pathlib import Path
from uuid import UUID

import pytest

from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage


@pytest.mark.parametrize("filename", ["source.MSG", "source.PDF", "source.JPG", "source.JPEG", "source.PNG"])
def test_store_read_and_remove_in_imported_directory(tmp_path: Path, filename: str) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    relative = storage.store_new_evidence(filename, b"source bytes")
    assert relative.startswith("imported/")
    assert relative.endswith(Path(filename).suffix.lower())
    assert UUID(Path(relative).stem)
    assert storage.confirm_exists(relative) is None
    assert storage.check_availability(relative)
    assert storage.read_existing_evidence(relative) == b"source bytes"
    assert (relative, Path(relative).name) in storage.list_existing_evidence()
    storage.remove_unregistered_evidence(relative)
    assert not storage.check_availability(relative)


@pytest.mark.parametrize("filename,content", [
    ("empty.pdf", b""), ("notes.txt", b"content"),
    ("../escape.pdf", b"content"), ("..\\escape.pdf", b"content"),
    ("C:\\escape.pdf", b"content"), ("\\\\server\\share\\escape.pdf", b"content"),
])
def test_invalid_new_files_do_not_create_import(tmp_path: Path, filename: str, content: bytes) -> None:
    with pytest.raises(ValueError):
        BhpEvidenceStorage(tmp_path).store_new_evidence(filename, content)
    assert not (tmp_path / "imported").exists()


def test_collision_generates_new_name_without_overwrite(tmp_path: Path) -> None:
    first_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    second_id = UUID("550e8400-e29b-41d4-a716-446655440001")
    ids = iter((first_id, first_id, second_id))
    storage = BhpEvidenceStorage(tmp_path, uuid_factory=lambda: next(ids))
    first = storage.store_new_evidence("first.pdf", b"first")
    second = storage.store_new_evidence("second.pdf", b"second")
    assert first != second
    assert storage.read_existing_evidence(first) == b"first"
    assert storage.read_existing_evidence(second) == b"second"


@pytest.mark.parametrize("path", [
    "../outside.pdf", "..\\outside.pdf", "/outside.pdf",
    "C:\\outside.pdf", "\\\\server\\share\\outside.pdf",
    "folder/../inside.pdf", "folder//inside.pdf",
])
def test_existing_path_cannot_escape_root(tmp_path: Path, path: str) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.resolve_existing_evidence_path(path)
    assert not storage.check_availability(path)


def test_missing_and_non_imported_files_cannot_be_removed_as_compensation(tmp_path: Path) -> None:
    (tmp_path / "existing.pdf").write_bytes(b"protected")
    storage = BhpEvidenceStorage(tmp_path)
    assert not storage.check_availability("missing.pdf")
    with pytest.raises(FileNotFoundError):
        storage.read_existing_evidence("missing.pdf")
    with pytest.raises(ValueError):
        storage.remove_unregistered_evidence("existing.pdf")
    assert (tmp_path / "existing.pdf").read_bytes() == b"protected"


def test_empty_existing_file_is_not_selectable(tmp_path: Path) -> None:
    (tmp_path / "empty.pdf").write_bytes(b"")
    storage = BhpEvidenceStorage(tmp_path)
    assert not storage.check_availability("empty.pdf")
    assert storage.list_existing_evidence() == ()
    with pytest.raises(ValueError, match="pusty"):
        storage.read_existing_evidence("empty.pdf")
