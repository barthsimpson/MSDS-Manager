from pathlib import Path

import pytest

from app.application.dto import NewBhpDecisionInput
from app.application.use_cases.bhp_evidence import (
    BhpEvidenceCleanupError, ImportBhpEvidence, ListBhpEvidence, ReadBhpEvidence,
)
from app.domain.enums import BhpDecisionStatus
from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage


def data(filename: str = "Source Approval.PDF", content: bytes = b"evidence") -> NewBhpDecisionInput:
    return NewBhpDecisionInput(
        product_id="product-1", sds_id="sds-1",
        decision_status=BhpDecisionStatus.APPROVED,
        original_filename=filename, content=content,
    )


def test_success_stores_once_and_keeps_file_after_registration(tmp_path: Path) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    order = []
    def verify(product_id, sds_id):
        order.append("verify")
    def register(command):
        order.append("register")
        assert command.original_filename == "Source Approval.PDF"
        assert command.evidence_relative_path.startswith("imported/")
        assert storage.check_availability(command.evidence_relative_path)
        return command

    result = ImportBhpEvidence(storage).execute(data(), verify, register)
    assert order == ["verify", "register"]
    assert storage.read_existing_evidence(result.evidence_relative_path) == b"evidence"


def test_database_failure_removes_only_new_file(tmp_path: Path) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    (tmp_path / "protected.pdf").write_bytes(b"protected")
    def fail(command):
        raise RuntimeError("database failure")
    with pytest.raises(RuntimeError, match="database failure"):
        ImportBhpEvidence(storage).execute(data(), lambda *_: None, fail)
    assert (tmp_path / "protected.pdf").read_bytes() == b"protected"
    assert list((tmp_path / "imported").iterdir()) == []


def test_cleanup_failure_exposes_orphan_path(tmp_path: Path) -> None:
    class FailingCleanupStorage(BhpEvidenceStorage):
        def remove_unregistered_evidence(self, relative_path):
            raise OSError("cleanup failure")
    storage = FailingCleanupStorage(tmp_path)
    def fail(command):
        raise RuntimeError("database failure")
    with pytest.raises(BhpEvidenceCleanupError) as error:
        ImportBhpEvidence(storage).execute(data(), lambda *_: None, fail)
    assert error.value.relative_path.startswith("imported/")
    assert storage.check_availability(error.value.relative_path)


@pytest.mark.parametrize("filename,content", [("bad.txt", b"x"), ("empty.pdf", b"")])
def test_invalid_upload_never_reaches_registration(tmp_path: Path, filename: str, content: bytes) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    with pytest.raises(ValueError):
        ImportBhpEvidence(storage).execute(
            data(filename, content), lambda *_: None,
            lambda command: pytest.fail("registration must not run"),
        )
    assert not (tmp_path / "imported").exists()


def test_list_uses_registered_source_name_and_read_reports_missing(tmp_path: Path) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    relative = storage.store_new_evidence("Original Approval.pdf", b"bytes")
    listed = ListBhpEvidence(storage).execute({relative: "Original Approval.pdf"})
    assert listed[0].original_filename == "Original Approval.pdf"
    access = ReadBhpEvidence(storage)
    assert access.available(relative)
    assert access.execute(relative) == b"bytes"
    storage.remove_unregistered_evidence(relative)
    assert not access.available(relative)


def test_unregistered_import_is_not_offered_as_existing_evidence(tmp_path: Path) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    storage.store_new_evidence("Source.pdf", b"bytes")
    assert ListBhpEvidence(storage).execute({}) == ()


def test_scope_failure_prevents_filesystem_write(tmp_path: Path) -> None:
    storage = BhpEvidenceStorage(tmp_path)
    def fail_scope(*_):
        raise ValueError("SDS is not CURRENT")
    with pytest.raises(ValueError, match="not CURRENT"):
        ImportBhpEvidence(storage).execute(
            data(), fail_scope, lambda *_: pytest.fail("register must not run"),
        )
    assert not (tmp_path / "imported").exists()
