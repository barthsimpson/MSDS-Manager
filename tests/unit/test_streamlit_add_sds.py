from datetime import date

from streamlit.testing.v1 import AppTest

from app.application.dto import SdsDraft


class FakeComposition:
    def __init__(self) -> None:
        self.accepted = []
        self.prepared = []

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
    assert app.text_input(key="sds-product-name").value == "Parsed product"

    app.text_input(key="sds-product-name").set_value("Corrected product")
    app.button(key="accept-sds").click().run()

    assert len(composition.accepted) == 1
    assert composition.accepted[0].product_name == "Corrected product"
    assert any("SDS został zapisany" in item.value for item in app.success)
    assert "add_sds_draft" not in app.session_state


def test_add_sds_cancel_clears_draft_without_accept() -> None:
    composition = FakeComposition()
    app = _app(composition).run()

    app.button(key="read-sds").click().run()
    app.button(key="cancel-sds").click().run()

    assert composition.accepted == []
    assert "add_sds_draft" not in app.session_state