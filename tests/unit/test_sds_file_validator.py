from pathlib import Path

import pytest

from app.application.exceptions import InvalidSdsFileTypeError, SdsOutsideRootPathError
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator


def test_validator_returns_relative_path_for_pdf(tmp_path: Path) -> None:
    root = tmp_path / "sds"
    pdf = root / "incoming" / "sample.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF")

    assert SdsFileValidator(root).validate(pdf) == "incoming/sample.pdf"


def test_validator_rejects_outside_root_and_non_pdf(tmp_path: Path) -> None:
    root = tmp_path / "sds"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF")
    text_file = root / "sample.txt"
    text_file.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(SdsOutsideRootPathError):
        SdsFileValidator(root).validate_relative("../outside.pdf")
    with pytest.raises(InvalidSdsFileTypeError):
        SdsFileValidator(root).validate_relative("sample.txt")