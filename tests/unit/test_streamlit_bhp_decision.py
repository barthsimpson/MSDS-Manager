from dataclasses import replace
from datetime import date, datetime, timezone

from streamlit.testing.v1 import AppTest

from app.application.dto import (
    BhpDecisionProduct,
    CurrentBhpDecision,
    RegisterBhpDecisionResult,
)
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus


class FakeComposition:
    def __init__(self, products=None, evidence=("decision.pdf",)) -> None:
        self.products = products or [
            BhpDecisionProduct(
                product_id="product-1",
                product_name="Product",
                manufacturer_product_code="P-1",
                manufacturer_name="Manufacturer",
                usage_status=ProductUsageStatus.PENDING_APPROVAL,
                sds_id="sds-1",
                sds_filename="sds.pdf",
                sds_issue_date=date(2026, 1, 1),
                sds_revision="1",
            )
        ]
        self.evidence = evidence
        self.registered = []
        self.current_decision = None
        self.read_count = 0

    def list_bhp_products(self):
        self.read_count += 1
        return tuple(self.products)

    def list_bhp_evidence_files(self):
        return self.evidence

    def get_current_bhp_decision(self, sds_id):
        return self.current_decision

    def register_bhp_decision(self, data):
        self.registered.append(data)
        result = RegisterBhpDecisionResult(
            decision_id="decision-1",
            product_id=data.product_id,
            sds_id=data.sds_id,
            decision_status=data.decision_status,
            product_usage_status=(
                ProductUsageStatus.ACTIVE
                if data.decision_status is BhpDecisionStatus.APPROVED
                else ProductUsageStatus.REJECTED
            ),
            registered_at=datetime.now(timezone.utc),
            evidence_relative_path=data.evidence_relative_path,
        )
        self.products = [
            replace(product, usage_status=result.product_usage_status)
            if product.product_id == data.product_id else product
            for product in self.products
        ]
        self.current_decision = CurrentBhpDecision(
            decision_status=data.decision_status,
            registered_at=result.registered_at,
            notes=data.notes,
            evidence_relative_path=data.evidence_relative_path,
        )
        return result


def _app(composition):
    def render(current_composition) -> None:
        from app.presentation.streamlit.bhp_decision import render_bhp_decision

        render_bhp_decision(current_composition)

    return AppTest.from_function(render, args=(composition,))


def test_bhp_decision_approved_passes_notes_and_shows_active() -> None:
    composition = FakeComposition()
    app = _app(composition).run()

    app.text_area(key="bhp-notes").set_value("Approved after review")
    app.button(key="save-bhp-decision").click().run()

    assert len(composition.registered) == 1
    assert composition.registered[0].decision_status is BhpDecisionStatus.APPROVED
    assert composition.registered[0].notes == "Approved after review"
    assert composition.read_count >= 2
    assert any("Status produktu: Aktywny" == item.value for item in app.text)
    assert any("Decyzja: Dopuszczony" == item.value for item in app.text)
    assert [item.value for item in app.success] == ["Decyzja BHP została zapisana."]


def test_bhp_decision_rejected_shows_rejected() -> None:
    composition = FakeComposition()
    app = _app(composition).run()
    app.radio(key="bhp-decision-status").set_value("REJECTED")
    app.button(key="save-bhp-decision").click().run()

    assert composition.registered[0].decision_status is BhpDecisionStatus.REJECTED
    assert composition.read_count >= 2
    assert any("Status produktu: Odrzucony" == item.value for item in app.text)
    assert any("Decyzja: Niedopuszczony" == item.value for item in app.text)
    assert [item.value for item in app.success] == ["Decyzja BHP została zapisana."]


def test_bhp_decision_without_evidence_does_not_register() -> None:
    composition = FakeComposition(evidence=())
    app = _app(composition).run()
    app.button(key="save-bhp-decision").click().run()

    assert composition.registered == []
    assert app.error[0].value == "Wybierz dowód decyzji."
    assert app.success == []


def test_evidence_shows_filename_and_keeps_relative_path_for_write() -> None:
    composition = FakeComposition(evidence=("archiwum/decision.pdf",))
    app = _app(composition).run()

    assert app.selectbox(key="bhp-evidence").options == ["decision.pdf"]
    assert any(item.value == "Plik dostępny" for item in app.caption)
    app.button(key="save-bhp-decision").click().run()

    assert composition.registered[0].evidence_relative_path == "archiwum/decision.pdf"


def test_bhp_decision_shows_existing_current_decision() -> None:
    composition = FakeComposition()
    composition.current_decision = CurrentBhpDecision(
        decision_status=BhpDecisionStatus.APPROVED,
        registered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        notes="Existing notes",
        evidence_relative_path="archiwum/old.pdf",
    )
    app = _app(composition).run()

    assert any(item.value == "Decyzja: Dopuszczony" for item in app.text)
    assert any(item.value == "Dowód: old.pdf" for item in app.text)
    assert any(item.value == "Uwagi: Existing notes" for item in app.text)
    assert any(item.value == "Brak pliku dowodu" for item in app.caption)
