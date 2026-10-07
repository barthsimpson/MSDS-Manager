"""AppTest coverage for the physical review navigation and lifecycle controls."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from streamlit.testing.v1 import AppTest

from app.application.dto.physical_review import (
    PhysicalReviewDetails, PhysicalReviewItemRow, PhysicalReviewSummary,
)
from app.domain.enums import ReviewStatus
from app.presentation.streamlit.analytics import _parse_observed


REVIEW_ID = "f9d099c3-3872-4504-a174-e19cc7261f2c"
ITEM_ID = "2dba60c8-89bd-4bba-b725-fd91ec4d912e"


class FakeComposition:
    def __init__(self):
        self.review = None
        self.created_dates = []

    def get_active_physical_review_draft(self):
        if self.review and self.review.summary.status is ReviewStatus.DRAFT:
            return self.review.summary
        return None

    def list_physical_reviews(self):
        return [self.review.summary] if self.review else []

    def get_physical_review(self, review_id):
        assert review_id == REVIEW_ID
        return self.review

    def create_physical_review(self, review_date):
        self.created_dates.append(review_date)
        self.review = PhysicalReviewDetails(
            summary=PhysicalReviewSummary(
                REVIEW_ID, review_date, ReviewStatus.DRAFT,
                datetime(2026, 10, 7, tzinfo=timezone.utc), None,
            ),
            items=(PhysicalReviewItemRow(
                ITEM_ID, "hidden-product-id", "Lakier", "hidden-location-id",
                "HALA-1", "Hala pierwsza", Decimal("10"), "kg", None,
            ),),
        )
        return REVIEW_ID

    def finalize_physical_review(self, review_id):
        assert review_id == REVIEW_ID
        self.review = replace(self.review, summary=replace(
            self.review.summary, status=ReviewStatus.FINAL,
            finalized_at=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        ))

    def discard_physical_review_draft(self, review_id):
        assert review_id == REVIEW_ID
        self.review = None

    def update_review_observed_quantity(self, review_item_id, value):
        assert review_item_id == ITEM_ID
        self.review = replace(self.review, items=(replace(
            self.review.items[0], observed_quantity=value,
        ),))


def _app(composition):
    def render(composition):
        from app.presentation.streamlit.analytics import render_analytics
        render_analytics(composition)

    app = AppTest.from_function(render, args=(composition,), default_timeout=10)
    app.session_state["analytics-view"] = "Raport przeglądu"
    app.run()
    assert not app.exception
    return app


def test_review_create_incomplete_confirmation_final_read_only_and_no_uuid():
    composition = FakeComposition()
    app = _app(composition)
    assert not app.exception
    assert app.date_input(key="review-date").label == "Data przeglądu"
    chosen = date(2026, 10, 3)
    app.date_input(key="review-date").set_value(chosen).run()
    app.button(key="review-create").click().run()
    assert not app.exception
    assert composition.created_dates == [chosen]
    assert app.button(key="review-save").label == "Zapisz stany"
    app.button(key="review-save").click().run()
    assert not app.exception
    assert app.button(key="review-finalize").disabled
    assert any("Niesprawdzone pozycje: 1" in item.value for item in app.warning)
    app.checkbox(key="review-confirm-incomplete").check().run()
    assert not app.button(key="review-finalize").disabled
    app.button(key="review-finalize").click().run()
    assert not app.exception
    assert composition.review.summary.status is ReviewStatus.FINAL
    assert not app.get("data_editor")
    assert len(app.dataframe) == 1
    assert "" in app.dataframe[0].value["Stan na dzień"].tolist()
    assert not any(button.label == "Odrzuć draft" for button in app.button)
    displayed = " ".join(
        str(item.value) for item in (*app.markdown, *app.caption, *app.dataframe)
    )
    assert REVIEW_ID not in displayed
    assert ITEM_ID not in displayed
    assert "hidden-product-id" not in displayed


def test_review_discard_and_numeric_input():
    composition = FakeComposition()
    app = _app(composition)
    app.button(key="review-create").click().run()
    assert not app.exception
    app.button(key="review-discard").click().run()
    assert not app.exception
    assert composition.review is None
    assert app.button(key="review-create").label == "Utwórz przegląd"
    assert _parse_observed("") is None
    assert _parse_observed("0") == Decimal("0")
    assert _parse_observed("1.25") == Decimal("1.25")


def test_review_editor_saves_zero_without_turning_it_into_null(monkeypatch):
    composition = FakeComposition()
    composition.create_physical_review(date(2026, 10, 7))

    def edited_rows(rows, **kwargs):
        return [{**row, "Stan na dzień": "0"} for row in rows]

    monkeypatch.setattr("app.presentation.streamlit.analytics.st.data_editor", edited_rows)
    app = _app(composition)
    app.button(key="review-save").click().run()
    assert not app.exception
    assert composition.review.items[0].observed_quantity == Decimal("0")
    assert composition.review.items[0].difference == Decimal("-10")
    assert not app.button(key="review-finalize").disabled
