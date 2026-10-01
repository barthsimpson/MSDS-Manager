"""Streamlit view for registering a BHP decision."""

from pathlib import Path

import streamlit as st

from app.application.dto import NewBhpDecisionInput, RegisterBhpDecisionInput
from app.application.use_cases.bhp_evidence import BhpEvidenceCleanupError
from app.domain.enums import BhpDecisionStatus
from app.infrastructure.db.transactions import PersistenceError
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


def _render_evidence_access(composition: ShellComposition, relative_path: str, original_filename: str | None, key: str) -> None:
    filename = original_filename or Path(relative_path).name
    st.text(f"Dowód: {filename}")
    if not composition.bhp_evidence_available(relative_path):
        st.caption("MISSING — plik dowodu jest niedostępny.")
        return
    try:
        content = composition.read_bhp_evidence(relative_path)
    except (OSError, ValueError):
        st.caption("MISSING — plik dowodu jest niedostępny.")
        return
    mime = {
        ".pdf": "application/pdf",
        ".msg": "application/vnd.ms-outlook",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(Path(relative_path).suffix.lower(), "application/octet-stream")
    st.download_button("Pobierz dowód", content, file_name=filename, mime=mime, key=key)


def _render_current_decision(composition: ShellComposition, sds_id: str) -> None:
    decision = composition.get_current_bhp_decision(sds_id)
    if decision is None:
        return
    st.subheader("Bieżąca decyzja")
    st.text(f"Decyzja: {_decision_label(decision.decision_status)}")
    st.text(f"Zarejestrowano: {decision.registered_at.isoformat()}")
    _render_evidence_access(
        composition, decision.evidence_relative_path,
        decision.evidence_original_filename, "bhp-current-download",
    )
    if decision.notes:
        st.text(f"Uwagi: {decision.notes}")
    st.warning("Zapis nowej decyzji zastąpi bieżącą decyzję.")


def _render_history(composition: ShellComposition, sds_id: str) -> None:
    historical = tuple(
        decision for decision in composition.list_bhp_decisions(sds_id)
        if decision.record_status.value == "SUPERSEDED"
    )
    if not historical:
        return
    st.subheader("Historia decyzji")
    for decision in historical:
        with st.expander(f"{decision.registered_at.isoformat()} — {_decision_label(decision.decision_status)}"):
            st.text("Status rekordu: SUPERSEDED")
            _render_evidence_access(
                composition, decision.evidence_relative_path,
                decision.evidence_original_filename, f"bhp-history-download-{decision.decision_id}",
            )
            if decision.notes:
                st.text(f"Uwagi: {decision.notes}")


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
        st.text(f"Rewizja SDS: {product.sds_revision or 'Brak danych'}")
        st.text(f"Data wydania / rewizji SDS: {product.sds_issue_date or 'Brak danych'}")
    evidence_files = composition.list_bhp_evidence()
    _render_current_decision(composition, product.sds_id)
    _render_history(composition, product.sds_id)

    st.subheader("Nowa decyzja")
    mode = st.radio(
        "Sposób wskazania dowodu",
        ("Wybierz istniejący dowód", "Dodaj nowy dowód z komputera"),
        key="bhp-evidence-mode",
    )
    selected_evidence = None
    uploaded = None
    if mode == "Wybierz istniejący dowód":
        if not evidence_files:
            st.info("Brak dostępnych plików dowodu decyzji.")
        selected_evidence = st.selectbox(
            "Dowód decyzji *", (None, *evidence_files),
            format_func=lambda item: "BRAK WYBORU" if item is None else (
                f"{item.original_filename} ({item.relative_path})"
            ),
            key=f"bhp-evidence-{st.session_state.get('bhp-form-version', 0)}",
        )
        if selected_evidence is not None:
            st.caption("Plik dostępny")
    else:
        uploaded = st.file_uploader(
            "Nowy dowód decyzji *", type=["msg", "pdf", "jpg", "jpeg", "png"],
            key=f"bhp-upload-{st.session_state.get('bhp-form-version', 0)}",
        )
    decision_status = st.radio(
        "Decyzja",
        [BhpDecisionStatus.APPROVED.value, BhpDecisionStatus.REJECTED.value],
        format_func=lambda value: _decision_label(BhpDecisionStatus(value)),
        key="bhp-decision-status",
    )
    notes = st.text_area("Uwagi", key="bhp-notes")
    if st.button("Zapisz decyzję", key="save-bhp-decision"):
        if mode == "Wybierz istniejący dowód" and selected_evidence is None:
            st.error("Wybierz dowód decyzji.")
            return
        if mode == "Dodaj nowy dowód z komputera" and uploaded is None:
            st.error("Dodaj plik dowodu decyzji.")
            return
        try:
            if selected_evidence is not None:
                composition.register_bhp_decision(RegisterBhpDecisionInput(
                    product_id=product.product_id,
                    sds_id=product.sds_id,
                    decision_status=BhpDecisionStatus(decision_status),
                    evidence_relative_path=selected_evidence.relative_path,
                    original_filename=selected_evidence.original_filename,
                    notes=notes or None,
                ))
            else:
                composition.register_new_bhp_decision(NewBhpDecisionInput(
                    product_id=product.product_id,
                    sds_id=product.sds_id,
                    decision_status=BhpDecisionStatus(decision_status),
                    original_filename=uploaded.name,
                    content=uploaded.getvalue(),
                    notes=notes or None,
                ))
            st.session_state[SUCCESS_KEY] = True
            st.session_state["bhp-form-version"] = st.session_state.get("bhp-form-version", 0) + 1
            st.rerun()
        except (ShellInitializationError, BhpEvidenceCleanupError, PersistenceError, ValueError, OSError) as error:
            st.error(str(error))
