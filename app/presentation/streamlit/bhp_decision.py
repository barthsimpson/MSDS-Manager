"""Streamlit view for registering a BHP decision."""

import streamlit as st

from app.application.dto import RegisterBhpDecisionInput
from app.domain.enums import BhpDecisionStatus
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError


SUCCESS_KEY = "bhp_decision_success"


def _product_label(product) -> str:
    return (
        f"{product.product_name} - {product.manufacturer_product_code} "
        f"({product.manufacturer_name}) [{product.usage_status.value}]"
    )


def _render_current_decision(composition: ShellComposition, sds_id: str) -> None:
    decision = composition.get_current_bhp_decision(sds_id)
    if decision is None:
        return
    st.info(
        "Istniejąca decyzja CURRENT: "
        f"{decision.decision_status.value}, {decision.registered_at.isoformat()}, "
        f"dowód: {decision.evidence_relative_path}"
    )
    if decision.notes:
        st.caption(f"Notes: {decision.notes}")
    st.warning("Zapis nowej decyzji zastąpi bieżącą decyzję.")


def render_bhp_decision(composition: ShellComposition) -> None:
    st.header("Decyzja BHP")
    success_message = st.session_state.pop(SUCCESS_KEY, None)
    if success_message:
        st.success(success_message)
    products = composition.list_bhp_products()
    if not products:
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
    st.subheader("CURRENT SDS")
    st.write(f"Plik: {product.sds_filename}")
    st.write(f"Data wydania: {product.sds_issue_date or 'Brak danych'}")
    st.write(f"Rewizja: {product.sds_revision or 'Brak danych'}")
    st.write("Status dokumentu: CURRENT")
    _render_current_decision(composition, product.sds_id)

    evidence_files = composition.list_bhp_evidence_files()
    if not evidence_files:
        st.info("Brak dostępnych dowodów decyzji w BHP_EVIDENCE_ROOT_PATH.")
    evidence_path = st.selectbox("Dowód decyzji", evidence_files, key="bhp-evidence") if evidence_files else ""
    decision_status = st.radio(
        "Decyzja",
        [BhpDecisionStatus.APPROVED.value, BhpDecisionStatus.REJECTED.value],
        format_func=lambda value: "Dopuszczony" if value == "APPROVED" else "Odrzucony",
        key="bhp-decision-status",
    )
    notes = st.text_area("Notes", key="bhp-notes")
    if st.button("Zapisz decyzję", key="save-bhp-decision"):
        if not evidence_path:
            st.error("Wybierz dowód decyzji.")
            return
        try:
            result = composition.register_bhp_decision(
                RegisterBhpDecisionInput(
                    product_id=product.product_id,
                    sds_id=product.sds_id,
                    decision_status=BhpDecisionStatus(decision_status),
                    evidence_relative_path=evidence_path,
                    notes=notes or None,
                )
            )
            if result.product_usage_status.value == "ACTIVE":
                success_message = (
                    "Decyzja BHP została zapisana. Produkt został dopuszczony "
                    "do stosowania. Status produktu: ACTIVE."
                )
            else:
                success_message = (
                    "Decyzja BHP została zapisana. Produkt nie został dopuszczony "
                    "do stosowania. Status produktu: REJECTED."
                )
            st.session_state[SUCCESS_KEY] = success_message
            st.rerun()
        except (ShellInitializationError, ValueError, OSError) as error:
            st.error(str(error))