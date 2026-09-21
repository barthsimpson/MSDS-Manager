from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

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
    is_encrypted = False

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

    def decrypt(self, _password: str) -> int:
        raise AssertionError("Plain PDFs must not be decrypted")


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


def test_extractor_reads_encrypted_pdf_after_empty_password_decrypt(
    monkeypatch, tmp_path: Path
) -> None:
    class EncryptedReader(FakeReader):
        is_encrypted = True

        def __init__(self, path: Path) -> None:
            self.decrypted = False
            super().__init__(path)

        def decrypt(self, password: str) -> int:
            assert password == ""
            self.decrypted = True
            return 1

        @property
        def pages(self):
            assert self.decrypted
            return self._pages

        @pages.setter
        def pages(self, value) -> None:
            self._pages = value

    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", EncryptedReader)
    pdf_path = tmp_path / "copy-protected.pdf"
    pdf_path.touch()

    result = PdfSdsExtractor().extract(pdf_path)

    assert result.product_name == "PRODUCT"


def test_extractor_reads_real_aes_encrypted_pdf(
    tmp_path: Path,
) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 20 280 Td (AES SDS text) Tj ET")
    page[NameObject("/Contents")] = content
    writer.encrypt("", owner_password="owner", algorithm="AES-256")

    pdf_path = tmp_path / "aes-encrypted.pdf"
    with pdf_path.open("wb") as pdf_file:
        writer.write(pdf_file)

    result = PdfSdsExtractor().extract(pdf_path)

    assert result.product_name == "AES SDS text"


def test_extractor_reports_controlled_error_when_password_is_required(
    monkeypatch, tmp_path: Path
) -> None:
    class PasswordProtectedReader:
        is_encrypted = True

        def __init__(self, _path: Path) -> None:
            pass

        def decrypt(self, password: str) -> int:
            assert password == ""
            return 0

        @property
        def pages(self):
            raise AssertionError("Pages must not be read after failed decryption")

    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", PasswordProtectedReader)
    pdf_path = tmp_path / "password-protected.pdf"
    pdf_path.touch()

    with pytest.raises(SdsPdfExtractionError, match="Could not read SDS PDF"):
        PdfSdsExtractor().extract(pdf_path)


def test_extractor_rejects_pdf_without_text(monkeypatch, tmp_path: Path) -> None:
    class EmptyReader:
        is_encrypted = False

        def __init__(self, _path: Path) -> None:
            self.pages = [FakePage("")]

    monkeypatch.setattr(pdf_sds_extractor, "PdfReader", EmptyReader)
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.touch()

    with pytest.raises(SdsPdfExtractionError):
        PdfSdsExtractor().extract(pdf_path)
