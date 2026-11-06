"""Focused AppTest for the existing Product Card SDS history action."""

from datetime import datetime, timezone
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from app.application.dto import SdsHistoryItem
from app.domain.enums import SdsDocumentStatus


class Composition:
    def __init__(self):
        self.saved = []
        self.read = []

    def invalidate_sds(self, data):
        self.saved.append(data)

    def read_sds_history_file(self, path):
        self.read.append(path)
        return b"%PDF-1.4\nfixture"


def test_current_invalidation_requires_reason_confirmation_and_explicit_restore_choice():
    now = datetime.now(timezone.utc)
    details = SimpleNamespace(product_id="product", product_name="Solvent", manufacturer_name="Maker")
    history = tuple(SdsHistoryItem(
        sds_id=sds_id, product_id="product", original_filename=f"{sds_id}.pdf",
        relative_path=f"{sds_id}.pdf", issue_date=None, revision=None,
        document_status=status, registered_at=now, invalidated_at=None,
        invalidation_reason=None, invalidated_from_status=None, restored_sds_id=None,
    ) for sds_id, status in (("a", SdsDocumentStatus.ARCHIVED), ("b", SdsDocumentStatus.CURRENT)))
    composition = Composition()

    def render(current_composition, current_details, current_history):
        from app.presentation.streamlit.product_registry import _render_sds_history
        _render_sds_history(current_composition, current_details, current_history, "b")

    app = AppTest.from_function(render, args=(composition, details, history)).run()
    app.button(key="invalidate-sds-b").click().run()
    assert app.selectbox(key="invalidation-mode-b").value is None
    assert app.button(key="invalidation-save-b").disabled
    app.text_area(key="invalidation-reason-b").set_value("Incorrect SDS").run()
    app.checkbox(key="invalidation-confirm-b").check().run()
    assert app.button(key="invalidation-save-b").disabled
    app.selectbox(key="invalidation-mode-b").set_value("RESTORE_ARCHIVED").run()
    assert app.selectbox(key="invalidation-replacement-b").value is None
    assert app.button(key="invalidation-save-b").disabled
    app.selectbox(key="invalidation-replacement-b").set_value("a").run()
    assert not app.button(key="invalidation-save-b").disabled
    app.button(key="invalidation-save-b").click().run()
    assert len(composition.saved) == 1
    assert composition.saved[0].restored_sds_id == "a"
    assert composition.saved[0].reason == "Incorrect SDS"


def test_invalidated_history_shows_reason_and_pdf_without_action():
    now = datetime.now(timezone.utc)
    details = SimpleNamespace(product_id="product", product_name="Solvent", manufacturer_name="Maker")
    item = SdsHistoryItem(
        sds_id="old", product_id="product", original_filename="old.pdf",
        relative_path="old.pdf", issue_date=None, revision=None,
        document_status=SdsDocumentStatus.INVALIDATED, registered_at=now,
        invalidated_at=now, invalidation_reason="Wrong source",
        invalidated_from_status="ARCHIVED", restored_sds_id=None,
    )
    composition = Composition()

    def render(current_composition, current_details, current_history):
        from app.presentation.streamlit.product_registry import _render_sds_history
        _render_sds_history(current_composition, current_details, current_history, None)

    app = AppTest.from_function(render, args=(composition, details, (item,))).run()
    assert any("Wycofany / błędna rejestracja" in element.value for element in app.markdown)
    assert any("Wrong source" in element.value for element in app.caption)
    assert any("Poprzedni status: ARCHIVED" in element.value for element in app.caption)
    assert not any(button.key == "invalidate-sds-old" for button in app.button)
    app.button(key="open-history-pdf-old").click().run()
    assert composition.read == ["old.pdf"]
