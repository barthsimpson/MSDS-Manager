"""Streamlit view for preparing and accepting an SDS draft."""

from datetime import date

import streamlit as st

from app.application.dto import AcceptSdsInput, SdsComponentDraft, SdsSafetyProfileDraft
from app.domain.enums import SafetyInformationStatus
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError


DRAFT_KEY = "add_sds_draft"
STATUS_OPTIONS = ["", *(status.value for status in SafetyInformationStatus)]


def _status_input(label: str, value: SafetyInformationStatus | None, key: str):
    selected = st.selectbox(
        label,
        STATUS_OPTIONS,
        index=0 if value is None else STATUS_OPTIONS.index(value.value),
        key=key,
    )
    return SafetyInformationStatus(selected) if selected else None


def _lines_input(label: str, values: list[str], key: str) -> list[str]:
    text = st.text_area(label, "\n".join(values), key=key)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _render_profile(profile: SdsSafetyProfileDraft) -> SdsSafetyProfileDraft:
    st.subheader("SAFETY_PROFILE")
    profile.product_definition = st.text_input(
        "Definicja produktu", profile.product_definition or "", key="sds-product-definition"
    ) or None
    profile.clp_classification_text = st.text_input(
        "Klasyfikacja CLP", profile.clp_classification_text or "", key="sds-clp"
    ) or None
    profile.signal_word = st.text_input(
        "Hasło ostrzegawcze", profile.signal_word or "", key="sds-signal-word"
    ) or None
    profile.hazardous_classification_status = _status_input(
        "Status klasyfikacji", profile.hazardous_classification_status, "sds-hazardous-status"
    )
    profile.hazard_statements = _lines_input(
        "Zwroty H", profile.hazard_statements, "sds-hazard-statements"
    )
    profile.supplemental_hazard_statements = _lines_input(
        "Uzupełniające zwroty zagrożenia",
        profile.supplemental_hazard_statements,
        "sds-supplemental-hazard-statements",
    )
    status_fields = (
        ("PBT", "pbt_status"),
        ("vPvB", "vpvb_status"),
        ("Rakotwórczość", "carcinogenicity_status"),
        ("Mutagenność komórek rozrodczych", "germ_cell_mutagenicity_status"),
        ("Działanie szkodliwe na rozrodczość", "reproductive_toxicity_status"),
        ("Endokrynne sekcja 2", "endocrine_section_2_status"),
        ("Endokrynne sekcja 11", "endocrine_section_11_status"),
        ("Uczulenie skóry", "skin_sensitization_status"),
        ("Uczulenie dróg oddechowych", "respiratory_sensitization_status"),
    )
    for label, field_name in status_fields:
        setattr(
            profile,
            field_name,
            _status_input(label, getattr(profile, field_name), f"sds-{field_name}"),
        )
    return profile


def _render_components(components: list[SdsComponentDraft]) -> list[SdsComponentDraft]:
    st.subheader("SDS_COMPONENTS")
    updated: list[SdsComponentDraft] = []
    for index, component in enumerate(components):
        with st.container(border=True):
            st.markdown(f"Składnik {index + 1}")
            component.component_name = st.text_input(
                "Nazwa składnika", component.component_name or "", key=f"component-name-{index}"
            ) or None
            component.cas_number = st.text_input(
                "CAS", component.cas_number or "", key=f"component-cas-{index}"
            ) or None
            component.ec_number = st.text_input(
                "WE", component.ec_number or "", key=f"component-ec-{index}"
            ) or None
            component.reach_registration_number = st.text_input(
                "Numer REACH",
                component.reach_registration_number or "",
                key=f"component-reach-{index}",
            ) or None
            component.concentration_text = st.text_input(
                "Stężenie", component.concentration_text or "", key=f"component-concentration-{index}"
            ) or None
            component.classification_text = st.text_input(
                "Klasyfikacja składnika",
                component.classification_text or "",
                key=f"component-classification-{index}",
            ) or None
            component.hazard_statements = _lines_input(
                "Zwroty H składnika", component.hazard_statements, f"component-h-{index}"
            )
            if not st.button("Usuń składnik", key=f"remove-component-{index}"):
                updated.append(component)
    if st.button("Dodaj składnik", key="add-component"):
        updated.append(SdsComponentDraft())
    return updated


def _render_draft(composition: ShellComposition) -> None:
    draft = st.session_state[DRAFT_KEY]
    st.caption(f"Plik: {draft.source_relative_path}")
    draft.product_name = st.text_input("Nazwa produktu", draft.product_name or "", key="sds-product-name") or None
    draft.manufacturer_product_code = st.text_input(
        "Kod produktu producenta", draft.manufacturer_product_code or "", key="sds-product-code"
    ) or None
    draft.manufacturer_name = st.text_input(
        "Producent", draft.manufacturer_name or "", key="sds-manufacturer"
    ) or None
    draft.use_description = st.text_input(
        "Opis zastosowania", draft.use_description or "", key="sds-use-description"
    ) or None
    draft.use_restriction = st.text_input(
        "Ograniczenie zastosowania", draft.use_restriction or "", key="sds-use-restriction"
    ) or None
    draft.revision = st.text_input("Rewizja", draft.revision or "", key="sds-revision") or None
    has_issue_date = st.checkbox("Podaj datę wydania", value=draft.issue_date is not None, key="sds-has-issue-date")
    if has_issue_date:
        draft.issue_date = st.date_input("Data wydania", draft.issue_date or date.today(), key="sds-issue-date")
    else:
        draft.issue_date = None
    draft.safety_profile = _render_profile(draft.safety_profile)
    draft.components = _render_components(draft.components)
    save, cancel = st.columns(2)
    if save.button("Zapisz / Akceptuj", key="accept-sds"):
        try:
            sds_id = composition.accept_sds(AcceptSdsInput(**vars(draft)))
            del st.session_state[DRAFT_KEY]
            st.success(f"SDS został zapisany. Produkt oczekuje na decyzję BHP. ({sds_id})")
        except (ShellInitializationError, ValueError, OSError) as error:
            st.error(str(error))
    if cancel.button("Anuluj", key="cancel-sds"):
        del st.session_state[DRAFT_KEY]
        st.rerun()


def render_add_sds(composition: ShellComposition) -> None:
    st.header("Dodaj SDS")
    files = composition.list_sds_files()
    if not files:
        st.info("Brak plików PDF w SDS_ROOT_PATH.")
        return
    selected = st.selectbox("Plik SDS", files, key="sds-selected-file")
    if DRAFT_KEY not in st.session_state and st.button("Odczytaj dane", key="read-sds"):
        try:
            st.session_state[DRAFT_KEY] = composition.prepare_sds_draft(selected)
            st.rerun()
        except (ShellInitializationError, ValueError, OSError) as error:
            st.error(str(error))
    if DRAFT_KEY in st.session_state:
        _render_draft(composition)