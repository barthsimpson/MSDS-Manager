from pathlib import Path

import pytest

from app.application.exceptions import (
    InvalidEvidenceFileTypeError,
    SdsFileNotFoundError,
    SdsOutsideRootPathError,
)
from app.infrastructure.filesystem.bhp_evidence_validator import BhpEvidenceValidator


def test_bhp_evidence_validator_accepts_allowed_relative_file(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    evidence = root / "decisions" / "approval.pdf"
    evidence.parent.mkdir()
    evidence.write_bytes(b"test evidence")

    assert BhpEvidenceValidator(root).validate("decisions/approval.pdf") == (
        "decisions/approval.pdf"
    )


def test_bhp_evidence_validator_rejects_missing_outside_and_unsupported_files(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "notes.txt").write_text("test", encoding="utf-8")

    validator = BhpEvidenceValidator(root)
    with pytest.raises(SdsFileNotFoundError):
        validator.validate("missing.pdf")
    with pytest.raises(SdsOutsideRootPathError):
        validator.validate("../outside.pdf")
    with pytest.raises(InvalidEvidenceFileTypeError):
        validator.validate("notes.txt")