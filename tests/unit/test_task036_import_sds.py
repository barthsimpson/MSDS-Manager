"""Controlled SDS import failures and filesystem boundaries."""

from uuid import UUID

import pytest

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput
from app.application.use_cases.import_sds import ImportSds, SdsImportCleanupError
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


PDF = b"%PDF-1.4\nfixture\n"


def first_sds() -> AcceptSdsInput:
    return AcceptSdsInput(
        source_relative_path="", product_name="Fixture", manufacturer_product_code="F-1",
        manufacturer_name="Maker", use_description="Use", use_restriction="Restriction",
    )


def test_exclusive_storage_retries_collision_without_overwriting(tmp_path) -> None:
    first = UUID("11111111-1111-4111-8111-111111111111")
    second = UUID("22222222-2222-4222-8222-222222222222")
    imported = tmp_path / "imported"
    imported.mkdir()
    existing = imported / f"{first}.pdf"
    existing.write_bytes(b"original")
    ids = iter((first, second))
    storage = SdsPdfStorage(tmp_path, uuid_factory=lambda: next(ids))

    relative = storage.store_new_pdf(PDF)

    assert relative == f"imported/{second}.pdf"
    assert existing.read_bytes() == b"original"
    assert (tmp_path / relative).read_bytes() == PDF


@pytest.mark.parametrize("filename,contents", [
    ("input.txt", PDF), ("input.pdf", b""), ("input.pdf", b"not a PDF"),
    ("../escape.pdf", PDF), (r"..\escape.pdf", PDF),
    (r"C:\escape.pdf", PDF), (r"\\server\share.pdf", PDF),
])
def test_invalid_input_never_writes_or_registers(tmp_path, filename, contents) -> None:
    registered = []
    importer = ImportSds(SdsPdfStorage(tmp_path))

    with pytest.raises(ValueError):
        importer.execute(first_sds(), filename, contents, registered.append)

    assert registered == []
    assert not (tmp_path / "imported").exists()


def test_missing_root_and_bad_product_fail_before_write(tmp_path) -> None:
    with pytest.raises(OSError):
        ImportSds(SdsPdfStorage(tmp_path / "missing")).execute(
            first_sds(), "document.pdf", PDF, lambda _: None
        )
    importer = ImportSds(SdsPdfStorage(tmp_path))
    with pytest.raises(ValueError, match="does not exist"):
        importer.execute(
            AddSdsRevisionInput("missing", ""), "revision.pdf", PDF, lambda _: None,
            lambda _: (_ for _ in ()).throw(ValueError("Selected product does not exist.")),
        )
    assert not (tmp_path / "imported").exists()


def test_invalid_product_fields_fail_before_write(tmp_path) -> None:
    with pytest.raises(ValueError, match="product_name"):
        ImportSds(SdsPdfStorage(tmp_path)).execute(
            AcceptSdsInput(source_relative_path=""),
            "document.pdf", PDF, lambda _: None,
        )
    assert not (tmp_path / "imported").exists()


def test_registration_failure_removes_only_new_file(tmp_path) -> None:
    existing = tmp_path / "imported" / "protected.pdf"
    existing.parent.mkdir()
    existing.write_bytes(b"protected")

    with pytest.raises(RuntimeError, match="DB failed"):
        ImportSds(SdsPdfStorage(tmp_path)).execute(
            first_sds(), "document.PDF", PDF,
            lambda _: (_ for _ in ()).throw(RuntimeError("DB failed")),
        )

    assert existing.read_bytes() == b"protected"
    assert list(existing.parent.iterdir()) == [existing]


def test_cleanup_failure_reports_orphan_path(tmp_path, monkeypatch) -> None:
    storage = SdsPdfStorage(tmp_path)
    monkeypatch.setattr(storage, "remove_unregistered_file", lambda _: (_ for _ in ()).throw(OSError("denied")))
    with pytest.raises(SdsImportCleanupError) as error:
        ImportSds(storage).execute(
            first_sds(), "document.pdf", PDF,
            lambda _: (_ for _ in ()).throw(RuntimeError("DB failed")),
        )
    assert error.value.relative_path.startswith("imported/")
    assert (tmp_path / error.value.relative_path).read_bytes() == PDF


def test_success_keeps_file_and_passes_original_filename(tmp_path) -> None:
    received = []
    importer = ImportSds(SdsPdfStorage(tmp_path))
    result = importer.execute(first_sds(), "Original.PDF", PDF, lambda data: received.append(data) or "sds-id")
    assert result == "sds-id"
    assert received[0].original_filename == "Original.PDF"
    assert received[0].source_relative_path.startswith("imported/")
    assert (tmp_path / received[0].source_relative_path).read_bytes() == PDF


def test_storage_rejects_symlink_outside_root(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "imported").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unavailable")
    with pytest.raises(OSError, match="poza"):
        SdsPdfStorage(root).store_new_pdf(PDF)


def test_exhausted_uuid_collisions_leave_existing_file(tmp_path) -> None:
    fixed = UUID("33333333-3333-4333-8333-333333333333")
    imported = tmp_path / "imported"
    imported.mkdir()
    existing = imported / f"{fixed}.pdf"
    existing.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        SdsPdfStorage(tmp_path, uuid_factory=lambda: fixed, max_attempts=2).store_new_pdf(PDF)
    assert existing.read_bytes() == b"original"
