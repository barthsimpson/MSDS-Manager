"""Focused read-only CURRENT SDS download coverage."""

from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from streamlit.testing.v1 import AppTest

from app.application.dto import ProductDetails
from app.application.exceptions import EntityNotFoundError
from app.application.use_cases.get_current_sds_file import (
    CurrentSdsFile,
    CurrentSdsReference,
    GetCurrentSdsFile,
)
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage
from app.infrastructure.db.repositories.current_sds_query import SqlAlchemyCurrentSdsQuery
from tests.unit.test_product_registry_view import make_product


class FakeQuery:
    def __init__(self, reference: CurrentSdsReference | None, exists: bool = True) -> None:
        self.reference = reference
        self.exists = exists

    def product_exists(self, product_id: str) -> bool:
        assert product_id == "product-1"
        return self.exists

    def get_current(self, product_id: str) -> CurrentSdsReference | None:
        assert product_id == "product-1"
        return self.reference


def test_current_sds_read_returns_original_name_and_preserves_file(tmp_path: Path) -> None:
    root = tmp_path / "sds"
    root.mkdir()
    stored = root / "imported" / "550e8400-e29b-41d4-a716-446655440000.pdf"
    stored.parent.mkdir()
    stored.write_bytes(b"%PDF-1.4\ncurrent")
    before = stored.stat().st_mtime_ns
    reference = CurrentSdsReference("Operator-original.pdf", "imported/" + stored.name)

    result = GetCurrentSdsFile(FakeQuery(reference), SdsPdfStorage(root)).execute("product-1")

    assert result == CurrentSdsFile("Operator-original.pdf", b"%PDF-1.4\ncurrent")
    assert stored.read_bytes() == result.content
    assert stored.stat().st_mtime_ns == before
    assert result.original_filename != stored.name


def test_no_current_sds_and_unknown_product(tmp_path: Path) -> None:
    storage = SdsPdfStorage(tmp_path)
    assert GetCurrentSdsFile(FakeQuery(None), storage).execute("product-1") is None
    with pytest.raises(EntityNotFoundError):
        GetCurrentSdsFile(FakeQuery(None, exists=False), storage).execute("product-1")


def test_db_query_selects_only_current_and_does_not_change_lifecycle() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE products (product_id TEXT PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE sds_documents (product_id TEXT, original_filename TEXT, relative_path TEXT, document_status TEXT)"))
        connection.execute(text("INSERT INTO products VALUES ('product-1')"))
        connection.execute(text("INSERT INTO sds_documents VALUES ('product-1', 'Old.pdf', 'old.pdf', 'ARCHIVED')"))
        connection.execute(text("INSERT INTO sds_documents VALUES ('product-1', 'Current.pdf', 'current.pdf', 'CURRENT')"))
    with Session(engine) as session:
        query = SqlAlchemyCurrentSdsQuery(session)
        assert query.product_exists("product-1")
        assert not query.product_exists("missing")
        assert query.get_current("product-1") == CurrentSdsReference("Current.pdf", "current.pdf")
        assert query.get_current("missing") is None
        assert session.execute(text("SELECT document_status FROM sds_documents ORDER BY original_filename")).scalars().all() == ["CURRENT", "ARCHIVED"]
    engine.dispose()


def test_missing_current_sds_is_not_substituted(tmp_path: Path) -> None:
    root = tmp_path / "sds"
    root.mkdir()
    (root / "other.pdf").write_bytes(b"other")
    reference = CurrentSdsReference("Current.pdf", "missing.pdf")
    with pytest.raises(FileNotFoundError):
        GetCurrentSdsFile(FakeQuery(reference), SdsPdfStorage(root)).execute("product-1")
    assert (root / "other.pdf").read_bytes() == b"other"


@pytest.mark.parametrize("relative_path", [
    "/outside.pdf", "C:\\outside.pdf", "\\\\server\\share\\file.pdf",
    "../outside.pdf", "..\\outside.pdf", "folder/../../outside.pdf",
])
def test_unsafe_paths_are_blocked(tmp_path: Path, relative_path: str) -> None:
    storage = SdsPdfStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.read_sds(relative_path)


def test_symlink_outside_root_is_blocked(tmp_path: Path) -> None:
    root = tmp_path / "sds"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    link = root / "link.pdf"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable")
    with pytest.raises(ValueError):
        SdsPdfStorage(root).read_sds("link.pdf")


def test_resolved_path_outside_root_is_blocked_without_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "sds"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    original_resolve = Path.resolve

    def resolve(path: Path, *args, **kwargs) -> Path:
        if path == root / "link.pdf":
            return outside
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError):
        SdsPdfStorage(root).read_sds("link.pdf")
    assert outside.read_bytes() == b"outside"


def _details() -> ProductDetails:
    return ProductDetails(**asdict(make_product("product-1", "Manufacturer")), usage_locations=())


def _row():
    return SimpleNamespace(
        current_sds_id="sds-1", current_sds_filename="Operator-original.pdf",
        current_sds_issue_date=None, current_sds_revision=None,
        current_sds_file_available=True, current_bhp_decision_status=None,
    )


def _render_sds(composition, row):
    def render(current_composition, current_row, details):
        from app.presentation.streamlit.product_registry import _render_details
        _render_details(current_composition, details, current_row)

    return AppTest.from_function(render, args=(composition, row, _details())).run()


def test_app_download_button_only_for_available_current_sds() -> None:
    class Composition:
        calls = []

        def get_current_sds_file(self, product_id):
            self.calls.append(product_id)
            return CurrentSdsFile("Operator-original.pdf", b"%PDF-1.4\n")

    composition = Composition()
    app = _render_sds(composition, _row())
    assert not app.exception
    assert app.download_button(key="current-sds-download-product-1").label == "Pobierz SDS"
    assert composition.calls == ["product-1"]

    app = _render_sds(composition, None)
    assert not app.exception
    assert not app.get("download_button")
    assert composition.calls == ["product-1"]


def test_ui_uses_original_filename_for_download(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.presentation.streamlit import product_registry

    captured = []
    monkeypatch.setattr(
        product_registry.st, "download_button",
        lambda _label, data, **kwargs: captured.append((data, kwargs["file_name"])),
    )

    class Composition:
        def get_current_sds_file(self, _product_id):
            return CurrentSdsFile("Operator-original.pdf", b"%PDF-1.4\n")

    app = _render_sds(Composition(), _row())
    assert not app.exception
    assert captured == [(b"%PDF-1.4\n", "Operator-original.pdf")]


def test_app_missing_current_file_has_no_download() -> None:
    class Composition:
        def get_current_sds_file(self, product_id):
            raise FileNotFoundError(product_id)

    app = _render_sds(Composition(), _row())
    assert not app.exception
    assert not app.get("download_button")
    assert any("MISSING" in item.value for item in app.info)
