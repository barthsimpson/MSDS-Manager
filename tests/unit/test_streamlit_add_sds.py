from datetime import date
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from app.application.dto import SdsDraft


class FakeComposition:
    def __init__(self) -> None:
        self.accepted = []
        self.prepared = []
        self.imported = []

    def list_sds_files(self) -> tuple[str, ...]:
        return ("fixture.pdf",)

    def prepare_sds_draft(self, relative_path: str) -> SdsDraft:
        self.prepared.append(relative_path)
        return SdsDraft(
            source_relative_path=relative_path,
            product_name="Parsed product",
            manufacturer_product_code="P-1",
            manufacturer_name=None,
            use_description="Parsed use",
            use_restriction="Parsed restriction",
            issue_date=date(2025, 10, 3),
            revision="10.02",
            detected_language="PL",
            language_valid=True,
        )

    def accept_sds(self, data) -> str:
        self.accepted.append(data)
        return "accepted-sds"

    def import_sds(self, data, original_filename: str, pdf_bytes: bytes) -> str:
        self.imported.append((data, original_filename, pdf_bytes))
        return "imported-sds"


def _app(composition: FakeComposition):
    def render(current_composition) -> None:
        from app.presentation.streamlit.add_sds import render_add_sds

        render_add_sds(current_composition)

    return AppTest.from_function(render, args=(composition,))


def test_add_sds_reads_and_accepts_manual_correction() -> None:
    composition = FakeComposition()
    app = _app(composition).run()

    app.button(key="read-sds").click().run()
    assert composition.prepared == ["fixture.pdf"]
    assert app.date_input(key="sds-issue-date").label == "Data wydania / rewizji SDS"
    assert app.text_input(key="sds-revision").label == "Rewizja SDS"
    assert app.text_input(key="sds-product-name").value == "Parsed product"
    assert [item.value for item in app.subheader] == ["Dokument SDS", "Produkt"]
    assert {item.label for item in app.expander} == {
        "Dane bezpieczeństwa — opcjonalne", "Składniki — opcjonalne"
    }
    assert {item.label for item in app.text_input if item.label.endswith("*")} == {
        "Nazwa produktu *", "Kod producenta *", "Producent *",
        "Opis zastosowania *", "Ograniczenia zastosowania *",
    }
    assert any(item.value == "* pole wymagane" for item in app.caption)

    app.text_input(key="sds-product-name").set_value("Corrected product")
    app.button(key="accept-sds").click().run()

    assert len(composition.accepted) == 1
    assert composition.accepted[0].product_name == "Corrected product"
    assert [item.value for item in app.success] == [
        "SDS został zapisany. Produkt oczekuje na decyzję BHP."
    ]
    assert "add_sds_draft" not in app.session_state


def test_add_sds_cancel_clears_draft_without_accept() -> None:
    composition = FakeComposition()
    app = _app(composition).run()

    app.button(key="read-sds").click().run()
    app.button(key="cancel-sds").click().run()

    assert composition.accepted == []
    assert "add_sds_draft" not in app.session_state


def test_add_sds_manual_fallback_keeps_unknown_date_empty() -> None:
    composition = FakeComposition()
    app = _app(composition).run()

    app.button(key="manual-sds").click().run()
    assert composition.prepared == []
    assert app.date_input(key="sds-issue-date").value is None

    app.text_input(key="sds-product-name").set_value("Manual product")
    app.text_input(key="sds-product-code").set_value("M-1")
    app.text_input(key="sds-manufacturer").set_value("Manual manufacturer")
    app.text_input(key="sds-use-description").set_value("Cleaning")
    app.text_input(key="sds-use-restriction").set_value("Ventilation")
    app.button(key="accept-sds").click().run()

    assert app.exception == []
    assert len(composition.accepted) == 1
    assert composition.accepted[0].issue_date is None
    assert composition.accepted[0].source_relative_path == "fixture.pdf"


def test_add_sds_accepts_date_without_revision() -> None:
    composition = FakeComposition()
    app = _app(composition).run()
    app.button(key="manual-sds").click().run()
    app.date_input(key="sds-issue-date").set_value(date(2026, 9, 30))
    app.text_input(key="sds-product-name").set_value("Manual product")
    app.text_input(key="sds-product-code").set_value("M-1")
    app.text_input(key="sds-manufacturer").set_value("Manual manufacturer")
    app.text_input(key="sds-use-description").set_value("Cleaning")
    app.text_input(key="sds-use-restriction").set_value("Ventilation")
    app.button(key="accept-sds").click().run()

    assert app.exception == []
    assert composition.accepted[0].issue_date == date(2026, 9, 30)
    assert composition.accepted[0].revision is None


def test_uploaded_sds_is_imported_only_on_accept() -> None:
    composition = FakeComposition()
    app = _app(composition).run()
    assert app.file_uploader[0].label == "Wybierz plik PDF z komputera"
    assert composition.imported == []

    from app.presentation.streamlit.add_sds import DRAFT_KEY, UPLOAD_KEY
    app.session_state[DRAFT_KEY] = SdsDraft(source_relative_path="")
    app.session_state[UPLOAD_KEY] = ("local.pdf", b"%PDF-1.4\n")
    app.run()
    assert composition.imported == []
    app.text_input(key="sds-product-name").set_value("Product")
    app.text_input(key="sds-product-code").set_value("P-1")
    app.text_input(key="sds-manufacturer").set_value("Maker")
    app.text_input(key="sds-use-description").set_value("Use")
    app.text_input(key="sds-use-restriction").set_value("Restriction")
    app.button(key="accept-sds").click().run()

    assert app.exception == []
    assert len(composition.imported) == 1
    assert composition.imported[0][1:] == ("local.pdf", b"%PDF-1.4\n")
    assert composition.accepted == []
    assert UPLOAD_KEY not in app.session_state


def test_upload_selection_stays_in_memory_until_accept(monkeypatch) -> None:
    from app.presentation.streamlit import add_sds

    monkeypatch.setattr(
        add_sds.st, "file_uploader",
        lambda *_args, **_kwargs: SimpleNamespace(name="source.pdf", getvalue=lambda: b"%PDF-1.4\n"),
    )
    composition = FakeComposition()
    app = _app(composition).run()
    assert composition.imported == []
    app.button(key="manual-upload-sds").click().run()
    assert composition.imported == []
    assert app.session_state[add_sds.UPLOAD_KEY] == ("source.pdf", b"%PDF-1.4\n")
    app.button(key="cancel-sds").click().run()
    assert composition.imported == []
    assert add_sds.UPLOAD_KEY not in app.session_state
