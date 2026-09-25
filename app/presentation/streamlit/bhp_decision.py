"""Streamlit view for registering a BHP decision."""

from pathlib import Path

import streamlit as st

from app.application.dto import RegisterBhpDecisionInput
from app.domain.enums import BhpDecisionStatus
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError


SUCCESS_KEY = "bhp_decision_success"
PRODUCT_STATUS_LABELS = {
    "PENDING_APPROVAL": "Oczekuje na BHP",
    "ACTIVE": "Aktywny",
    "REJECTED": "Odrzucony",
    "INACTIVE": "Nieaktywny",
}


def _product_status_label(status) -> str:
    return PRODUCT_STATUS_LABELS.get(status.value, status.value)


def _decision_label(status: BhpDecisionStatus) -> str:
    return "Dopuszczony" if status is BhpDecisionStatus.APPROVED else "Niedopuszczony"


def _product_label(product) -> str:
    return (
        f"{product.product_name} - {product.manufacturer_product_code} "
        f"({product.manufacturer_name}) [{_product_status_label(product.usage_status)}]"
    )


def _render_current_decision(
    composition: ShellComposition, sds_id: str, evidence_files: tuple[str, ...]
) -> None:
    decision = composition.get_current_bhp_decision(sds_id)
    if decision is None:
        return
    st.subheader("Bieżąca decyzja")
    st.text(f"Decyzja: {_decision_label(decision.decision_status)}")
    st.text(f"Zarejestrowano: {decision.registered_at.isoformat()}")
    st.text(f"Dowód: {Path(decision.evidence_relative_path).name}")
    st.caption(
        "Plik dostępny" if decision.evidence_relative_path in evidence_files
        else "Brak pliku dowodu"
    )
    if decision.notes:
        st.text(f"Uwagi: {decision.notes}")
    st.warning("Zapis nowej decyzji zastąpi bieżącą decyzję.")


def render_bhp_decision(composition: ShellComposition) -> None:
    st.header("Decyzja BHP")
    saved = st.session_state.pop(SUCCESS_KEY, False)
    products = composition.list_bhp_products()
    if not products:
        if saved:
            st.success("Decyzja BHP została zapisana.")
        st.info("Brak produktów z CURRENT SDS.")
        return

    selected_id = st.selectbox(
        "Produkt",
        [product.product_id for product in products],
        format_func=lambda product_id: _product_label(
            next(product for product in products if product.product_id == product_id)
        ),
        key="bhp-product",
    )
    product = next(product for product in products if product.product_id == selected_id)
    if saved:
        st.success("Decyzja BHP została zapisana.")
    st.subheader("Produkt")
    identity, status = st.columns(2)
    with identity:
        st.text(f"Nazwa: {product.product_name}")
        st.text(f"Producent: {product.manufacturer_name}")
        st.text(f"Kod producenta: {product.manufacturer_product_code}")
    with status:
        st.text(f"Status produktu: {_product_status_label(product.usage_status)}")
    st.subheader("CURRENT SDS")
    sds_file, sds_metadata = st.columns(2)
    with sds_file:
        st.text(f"Plik: {Path(product.sds_filename).name}")
        st.text("Status dokumentu: CURRENT")
    with sds_metadata:
        st.text(f"Rewizja: {product.sds_revision or 'Brak danych'}")
        st.text(f"Data SDS: {product.sds_issue_date or 'Brak danych'}")
    evidence_files = composition.list_bhp_evidence_files()
    _render_current_decision(composition, product.sds_id, evidence_files)

    st.subheader("Nowa decyzja")
    if not evidence_files:
        st.info("Brak dostępnych plików dowodu decyzji.")
    evidence_path = (
        st.selectbox(
            "Dowód decyzji *", evidence_files,
            format_func=lambda path: Path(path).name,
            key="bhp-evidence",
        ) if evidence_files else ""
    )
    if evidence_path:
        st.caption("Plik dostępny")
    decision_status = st.radio(
        "Decyzja",
        [BhpDecisionStatus.APPROVED.value, BhpDecisionStatus.REJECTED.value],
        format_func=lambda value: _decision_label(BhpDecisionStatus(value)),
        key="bhp-decision-status",
    )
    notes = st.text_area("Uwagi", key="bhp-notes")
    if st.button("Zapisz decyzję", key="save-bhp-decision"):
        if not evidence_path:
            st.error("Wybierz dowód decyzji.")
            return
        try:
            composition.register_bhp_decision(
                RegisterBhpDecisionInput(
                    product_id=product.product_id,
                    sds_id=product.sds_id,
                    decision_status=BhpDecisionStatus(decision_status),
                    evidence_relative_path=evidence_path,
                    notes=notes or None,
                )
            )
            st.session_state[SUCCESS_KEY] = True
            st.rerun()
        except (ShellInitializationError, ValueError, OSError) as error:
            st.error(str(error))
