from pathlib import Path

import pytest

from app.infrastructure.filesystem import pdf_sds_extractor
from app.infrastructure.filesystem.pdf_sds_extractor import (
    PdfSdsExtractor,
    SdsPdfExtractionError,
)


class FakePage:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakeReader:
    def __init__(self, _path: Path) -> None:
        self.pages = [
            FakePage(
                """PRODUCT\nKARTA CHARAKTERYSTYKI\nSEKCJA 1: Identyfikacja
Kod produktu :\nABC-1\nSEKCJA 2: Identyfikacja zagrożeń
Definicja produktu : Mieszanina\nProdukt nie został sklasyfikowany.
SEKCJA 3: Skład/informacja o składnikach\nIron\nCAS: 111-11-1
SEKCJA 11: Informacje toksykologiczne\nNiedostępne."""
            )
        ]


def test_extractor_reads_text_and_returns_minimal_draft(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", FakeReader)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.touch()

    result = PdfSdsExtractor().extract(pdf_path)

    assert result.product_name == "PRODUCT"
    assert result.manufacturer_product_code == "ABC-1"
    assert result.safety_profile.hazardous_classification_status.value == "NO"
    assert result.safety_profile.carcinogenicity_status.value == "NO_DATA"
    assert result.components[0].cas_number == "111-11-1"


def test_extractor_returns_none_for_unread_fields(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", FakeReader)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.touch()

    result = PdfSdsExtractor().extract(pdf_path)

    assert result.manufacturer_name is None
    assert result.issue_date is None
    assert result.use_restriction is None


def test_extractor_rejects_pdf_without_text(monkeypatch, tmp_path: Path) -> None:
    class EmptyReader:
        pages = [FakePage("")]

    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", EmptyReader)

    with pytest.raises(SdsPdfExtractionError):
        PdfSdsExtractor().extract(tmp_path / "scan.pdf")