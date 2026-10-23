"""One logical Evidence JSON SDS: review, approve, then controlled commit."""

from __future__ import annotations

from hashlib import sha256
import json

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.dto.sds import SdsSafetyProfileDraft
from app.application.use_cases.controlled_evidence_import import ImportPlanError, SAFETY_STATUS_FIELDS
from app.application.use_cases.import_sds import SdsImportCleanupError
from app.domain.enums import SafetyInformationStatus
from app.infrastructure.db.transactions import PersistenceError
from app.presentation.streamlit.composition import ShellComposition, ShellInitializationError
from app.presentation.streamlit.product_registry import PRODUCT_CARD_KEY


WORK_KEY = "evidence-import-work"
RESULT_KEY = "evidence-import-result"
BOUND_STATUSES = frozenset({"AUTO_BOUND", "MANUAL_BOUND"})
STALE_MESSAGE = "Plan nie jest już aktualny. Uruchom ponownie DRY RUN i zatwierdź nowy plan."
STATUS_LABELS = {
    "CREATE_CANDIDATE": "Nowy rekord — wymaga potwierdzenia",
    "LINK_CANDIDATE": "Powiązanie z istniejącym rekordem — wymaga potwierdzenia",
    "HUMAN_REVIEW": "Wymaga decyzji użytkownika",
    "PENDING_MANUFACTURER": "Najpierw rozstrzygnij producenta",
    "INVALID": "Niepoprawne dane źródłowe",
    "NOT_READY": "Niegotowy do zapisu",
    "VALID": "Poprawny",
}
SAFETY_LABELS = {
    "hazardous_classification_status": "Klasyfikacja jako niebezpieczny",
    "pbt_status": "PBT", "vpvb_status": "vPvB",
    "carcinogenicity_status": "Rakotwórczość",
    "germ_cell_mutagenicity_status": "Mutagenność komórek rozrodczych",
    "reproductive_toxicity_status": "Szkodliwość dla rozrodczości",
    "endocrine_section_2_status": "Zaburzenia endokrynne — sekcja 2",
    "endocrine_section_11_status": "Zaburzenia endokrynne — sekcja 11",
    "skin_sensitization_status": "Uczulenie skóry",
    "respiratory_sensitization_status": "Uczulenie dróg oddechowych",
}
VALUE_LABELS = {
    "": "Brak decyzji", "YES": "Tak", "NO": "Nie",
    "NO_DATA": "Brak danych w źródłowym SDS",
    "NOT_APPLICABLE": "Nie dotyczy według źródłowego SDS",
}
BLOCKER_LABELS = {
    "DOCUMENT_HUMAN_APPROVAL_REQUIRED": "Dokument wymaga zatwierdzenia przez użytkownika.",
    "INCOMPLETE_SAFETY_DATA": "Uzupełnij i zatwierdź dane bezpieczeństwa na podstawie SDS.",
    "PRODUCT_PENDING_MANUFACTURER": "Najpierw rozstrzygnij tożsamość producenta.",
    "UNAPPROVED_MANUFACTURER_RAW_VALUE": "Zatwierdź nazwę producenta z nieznanego wariantu źródłowego.",
    "EXTRACTION_REQUIRES_HUMAN_REVIEW": "Ekstrakcja wymaga przeglądu użytkownika.",
    "EXTRACTION_VALIDATION_BLOCKED": "Walidacja ekstrakcji zablokowała import.",
}


def _label(value: object) -> str:
    return "Brak danych" if value is None or value == "" else str(value)


def _evidence_rows(document: dict) -> list[dict[str, str]]:
    rows = []
    fields = []
    for section in ("product", "document_metadata", "safety_profile"):
        fields.extend((f"{section}.{key}", value)
                      for key, value in document.get(section, {}).items())
    fields.extend((f"parties[{index}].{party.get('role', 'OTHER')}", party.get("name"))
                  for index, party in enumerate(document.get("parties", [])))
    for field_name, field in fields:
        if not isinstance(field, dict):
            continue
        evidence = field.get("evidence") or [None]
        for proof in evidence:
            proof = proof or {}
            context = " / ".join(str(proof[key]) for key in ("section", "subsection", "label")
                                 if proof.get(key))
            value = field.get("domain_value") if "domain_value" in field else field.get("value")
            rows.append({
                "Pole": field_name, "Wartość": _label(value),
                "Stan": _label(field.get("state")), "Strona": _label(proof.get("page")),
                "Sekcja / kontekst": _label(context),
                "Tekst źródłowy": _label(proof.get("source_text")),
            })
    return rows


def _reset() -> None:
    st.session_state.pop(WORK_KEY, None)
    st.session_state.pop(RESULT_KEY, None)


def _source_signature(upload) -> tuple[str, str] | None:
    return (upload.name, sha256(upload.getvalue()).hexdigest()) if upload else None


def _render_result() -> None:
    result = st.session_state[RESULT_KEY]
    st.success("Import zakończony")
    action = "utworzony" if result["product_action"] == "CREATE" else "powiązany"
    status = {"CURRENT": "bieżący (CURRENT)", "ARCHIVED": "archiwalny (ARCHIVED)"}.get(
        result["status"], result["status"])
    st.write(f"Produkt: {result['product']} — {action}")
    st.write(f"SDS zarejestrowany: {result['sds_id']} · Status: {status}")
    st.write(f"Plik źródłowy: {result['filename']}")
    card, again = st.columns([1, 1])
    if card.button("Otwórz kartę produktu", key="evidence-open-product", icon=":material/open_in_new:"):
        st.session_state[PRODUCT_CARD_KEY] = result["product_id"]
        st.session_state["shell-navigation-target"] = "Produkty"
        st.rerun()
    if again.button("Rozpocznij nowy import", key="evidence-new"):
        _reset()
        st.rerun()


def _render_safety(document: dict) -> tuple[SdsSafetyProfileDraft, bool]:
    st.markdown("#### SDS / bezpieczeństwo")
    st.caption("Każdy status wybierz świadomie na podstawie wskazanego PDF. „Brak danych” oznacza treść SDS, a nie brak wyniku ekstrakcji.")
    source = document.get("safety_profile", {})
    profile = SdsSafetyProfileDraft()
    choices = ["", *(status.value for status in SafetyInformationStatus)]
    columns = st.columns(2)
    for index, field in enumerate(SAFETY_STATUS_FIELDS):
        proposal = source.get(field, {})
        proposed = (
            proposal.get("domain_value") if "domain_value" in proposal else proposal.get("value")
        ) if isinstance(proposal, dict) and proposal.get("state") == "FOUND" else None
        with columns[index % 2]:
            selected = st.selectbox(
                SAFETY_LABELS[field] + " *", choices, key=f"evidence-safety-{field}",
                format_func=lambda value: VALUE_LABELS[value],
                help=f"Propozycja Evidence JSON: {_label(proposed)}" if proposed else "Brak propozycji z Evidence JSON",
            )
            if selected:
                st.caption("Z Evidence JSON · zatwierdzone ręcznie" if selected == proposed
                           else "Uzupełnione ręcznie")
            else:
                st.caption("Brak decyzji" + (f" · propozycja: {VALUE_LABELS.get(proposed, proposed)}" if proposed else ""))
            setattr(profile, field, SafetyInformationStatus(selected) if selected else None)
    with st.expander("Dodatkowe dane SDS i dowody źródłowe", expanded=True):
        profile.product_definition = st.text_input("Definicja produktu", key="evidence-product-definition") or None
        profile.clp_classification_text = st.text_input("Klasyfikacja CLP", key="evidence-clp") or None
        profile.signal_word = st.text_input("Hasło ostrzegawcze", key="evidence-signal") or None
        profile.hazard_statements = [line.strip() for line in st.text_area(
            "Zwroty H — po jednym wierszu", key="evidence-hazard-statements").splitlines() if line.strip()]
        profile.supplemental_hazard_statements = [line.strip() for line in st.text_area(
            "Uzupełniające zwroty — po jednym wierszu", key="evidence-supplemental").splitlines() if line.strip()]
        st.dataframe(_evidence_rows(document), hide_index=True, use_container_width=True)
    confirmed = st.checkbox("Potwierdzam weryfikację danych bezpieczeństwa ze źródłowym SDS.",
                            key="evidence-safety-confirmed")
    return profile, confirmed


def _render_approved(composition: ShellComposition, work: dict) -> None:
    approved = work["approved"]
    st.success("Plan importu zatwierdzony · fingerprint JSON i PDF związane z planem")
    summary, data = st.columns(2)
    with summary:
        st.write(f"Produkt: {approved.product_decision.name} · {approved.product_decision.action}")
        st.write(f"Producent z SDS: {approved.manufacturer_decision.name}")
        if approved.manufacturer_decision.action == "LINK":
            st.write(f"Powiąż z istniejącym: {approved.manufacturer_selected_name} "
                     f"({approved.manufacturer_decision.selected_id})")
        else:
            st.write("Producent: CREATE")
        st.write(f"Kod producenta: {_label(approved.product_decision.manufacturer_product_code)}")
        st.write(f"SDS: {_label(approved.issue_date)} · rewizja: {_label(approved.revision)}")
    with data:
        st.write(f"PDF: {approved.original_filename}")
        st.write(f"Opis zastosowania: {approved.use_description}")
        st.write(f"Ograniczenia: {approved.use_restriction}")
        st.write("Safety / składniki: do uzupełnienia w kolejnym etapie")
        st.write("Zatwierdzone przez: " + approved.human_approval.approved_by)
        st.write("Powiązanie ze źródłem: SHA-256 JSON i PDF")
    chosen = next(item for item in work["plans"] if item.document_key == work["document_key"])
    if chosen.warnings:
        st.warning("Ostrzeżenia DRY RUN: " + "; ".join(chosen.warnings))
    confirmed = st.checkbox("Potwierdzam zapis produktu i SDS do MSDS Managera.",
                            key="evidence-final-confirmed")
    commit, cancel = st.columns(2)
    if commit.button("Wykonaj import", type="primary", icon=":material/save:",
                     disabled=not confirmed or work.get("consumed", False), key="evidence-commit"):
        # Consume before I/O. A failed or uncertain commit needs a new DRY RUN.
        work["consumed"] = True
        try:
            sds_id = composition.commit_evidence_import(approved, work["raw"], work["pdf_bytes"])
            product_id, status, filename = composition.evidence_import_result(sds_id)
            st.session_state[RESULT_KEY] = {
                "sds_id": sds_id, "product_id": product_id, "status": status,
                "filename": filename, "product": approved.product_decision.name,
                "product_action": approved.product_decision.action,
            }
            st.session_state.pop(WORK_KEY, None)
            st.rerun()
        except (ImportPlanError, SdsImportCleanupError, PersistenceError,
                ShellInitializationError, SQLAlchemyError, ValueError, OSError, RuntimeError) as error:
            st.session_state.pop(WORK_KEY, None)
            st.error(STALE_MESSAGE if str(error) in {
                "SOURCE_CHANGED", "PDF_CHANGED", "STALE_RESOLUTION", "LINK_TARGET_NOT_APPROVED"
            } else f"Import zatrzymany: {error}. Uruchom ponownie DRY RUN przed kolejną próbą.")
    if cancel.button("Anuluj", key="evidence-cancel-approved"):
        _reset()
        st.rerun()


def _render_review(composition: ShellComposition, work: dict, pdf) -> None:
    st.markdown("### Etap 1 — Rejestracja SDS i danych nagłówkowych")
    st.info("Safety / składniki: do uzupełnienia w kolejnym etapie")
    plans = work["plans"]
    options = [item.document_key for item in plans]
    document_key = st.selectbox("Logical SDS *", options, index=None,
                                placeholder="Wybierz jeden dokument", key="evidence-document")
    if document_key is None:
        st.info("Wybierz jeden logical SDS do przeglądu.")
        return
    if work.get("approved"):
        if document_key != work["document_key"]:
            st.session_state.pop(WORK_KEY, None)
            st.error(STALE_MESSAGE)
            return
        _render_approved(composition, work)
        return
    plan = next(item for item in plans if item.document_key == document_key)
    document = next(item for item in work["payload"]["documents"]
                    if item.get("document_key") == document_key)
    source = work["payload"]["source"]
    validation_chip, readiness_chip, safety_chip = st.columns(3)
    validation_chip.badge(
        "Walidacja: " + STATUS_LABELS.get(plan.validation_status, plan.validation_status),
        color="green" if plan.validation_status == "VALID" else "red",
    )
    readiness_chip.badge(
        "DRY RUN: " + STATUS_LABELS.get(plan.commit_readiness, plan.commit_readiness),
        color="orange",
    )
    safety_chip.badge("SAFETY ENRICHMENT PENDING", color="orange")
    if plan.validation_status != "VALID":
        for error in plan.errors:
            st.error(error)
        return
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(border=True):
            st.markdown("#### Tożsamość produktu")
            st.write(f"Produkt: **{_label(plan.mapped_product_name)}**")
            st.write(f"Kod producenta: **{_label(plan.mapped_manufacturer_product_code)}**")
            st.write(f"Rozstrzygnięcie produktu: {STATUS_LABELS.get(plan.product_resolution.status, plan.product_resolution.status)}")
            st.write(f"Wymagane ręcznie: {', '.join(plan.required_manual_inputs)}")
        with st.container(border=True):
            st.markdown("#### Producent — decyzja człowieka")
            canonical = plan.manufacturer_resolution.canonical_name
            if plan.manufacturer_resolution.status == "HUMAN_REVIEW" and canonical:
                canonical = st.text_input("Zatwierdzona nazwa kanoniczna *", value=canonical,
                                          key="evidence-canonical")
            st.write(f"Producent z SDS (kanoniczny): **{_label(plan.manufacturer_resolution.canonical_name)}**")
            st.write(f"Wynik resolvera: {STATUS_LABELS.get(plan.manufacturer_resolution.status, plan.manufacturer_resolution.status)}")
            exact, similar, _ = composition.evidence_candidates(
                canonical or "", plan.mapped_product_name or "", None,
                plan.mapped_manufacturer_product_code)
            st.write("Dokładne rekordy: " + (", ".join(
                f"{row.name} ({row.record_id})" for row in exact) or "Brak"))
            st.write("Podobne rekordy: " + (", ".join(f"{row.name} ({row.record_id})" for row in similar) or "Brak"))
            st.caption("Podobieństwo jest tylko wskazówką. LINK wymaga wyboru istniejącego rekordu i potwierdzenia.")
            manufacturer_action = st.radio("Decyzja producenta *", ("Brak decyzji", "CREATE", "LINK"),
                                           horizontal=True, key="evidence-manufacturer-action")
            manufacturer_id = None
            manufacturer_link_confirmed = True
            if manufacturer_action == "LINK":
                candidates = (*exact, *similar)
                manufacturer_id = st.selectbox("Istniejący producent do LINK *", [row.record_id for row in candidates],
                                               index=None, key="evidence-manufacturer-id",
                                               format_func=lambda value: next(row.name for row in candidates if row.record_id == value))
                selected_manufacturer = next((row for row in candidates
                                              if row.record_id == manufacturer_id), None)
                if selected_manufacturer:
                    st.write(f"Producent z SDS: **{canonical}**")
                    st.write(f"Powiąż z istniejącym: **{selected_manufacturer.name}**")
                    manufacturer_link_confirmed = st.checkbox(
                        "Potwierdzam powiązanie z tym istniejącym producentem.",
                        key="evidence-manufacturer-link-confirmed",
                    )
            similar_confirmed = not similar or manufacturer_action != "CREATE" or st.checkbox(
                "Potwierdzam CREATE nowego producenta po przeglądzie podobnych rekordów.",
                key="evidence-similar-manufacturer-confirmed",
            )
    with right:
        with st.container(border=True):
            st.markdown("#### Dokument SDS")
            st.write(f"Data wydania: {_label(plan.mapped_issue_date)} · Rewizja: {_label(plan.mapped_revision)}")
            st.write(f"Nazwa źródłowego PDF z JSON: {_label(source.get('original_filename'))}")
            st.write(f"Powiązany PDF: {_label(pdf.filename if pdf else None)}")
            if pdf and pdf.content:
                st.download_button("Otwórz / pobierz powiązany PDF", pdf.content, file_name=pdf.filename,
                                   mime="application/pdf", key="evidence-download-pdf")
        with st.container(border=True):
            st.markdown("#### Produkt — decyzja człowieka")
            _, _, product_candidates = composition.evidence_candidates(
                canonical or "", plan.mapped_product_name or "", manufacturer_id,
                plan.mapped_manufacturer_product_code)
            st.write("Kandydaci: " + (", ".join(
                f"{row.name} · kod: {_label(row.manufacturer_product_code)} ({row.record_id})"
                for row in product_candidates) or "Brak dokładnych kandydatów"))
            product_action = st.radio("Decyzja produktu *", ("Brak decyzji", "CREATE", "LINK"),
                                      horizontal=True, key="evidence-product-action")
            product_id = None
            if product_action == "LINK":
                product_id = st.selectbox("Rekord produktu *", [row.record_id for row in product_candidates],
                                          index=None, key="evidence-product-id")
            null_confirmed = True
            if product_action == "LINK" and plan.mapped_manufacturer_product_code is None:
                null_confirmed = st.checkbox("Potwierdzam LINK produktu mimo braku kodu producenta w JSON.",
                                             key="evidence-null-code-confirmed")
    with st.container(border=True):
        st.markdown("#### Dane ręczne / przegląd")
        description = st.text_area("Opis zastosowania *", key="evidence-use-description")
        restriction = st.text_area("Ograniczenia zastosowania *", key="evidence-use-restriction")
        reviewer = st.text_input("Osoba zatwierdzająca *", key="evidence-reviewer")
        manual_confirmed = st.checkbox("Potwierdzam dane ręczne na podstawie SDS.",
                                       key="evidence-manual-confirmed")
        pdf_confirmed = st.checkbox("Potwierdzam, że wybrany PDF odpowiada temu Evidence JSON.",
                                    key="evidence-pdf-confirmed")
        document_confirmed = st.checkbox("Zatwierdzam ten logical SDS po przeglądzie dowodów źródłowych.",
                                         key="evidence-document-confirmed")
    with st.expander("Dowody źródłowe danych identyfikacyjnych", expanded=True):
        st.dataframe(_evidence_rows(document), hide_index=True, use_container_width=True)
    st.markdown("#### Podsumowanie i blokady")
    if plan.warnings:
        st.warning("Ostrzeżenia DRY RUN: " + "; ".join(plan.warnings))
    if plan.blockers:
        st.info("Blokady DRY RUN do rozstrzygnięcia: " + "; ".join(
            BLOCKER_LABELS.get(item, item) for item in plan.blockers))
    pdf_valid = pdf is not None and pdf.status in BOUND_STATUSES
    blockers = []
    if manufacturer_action == "Brak decyzji" or manufacturer_action == "LINK" and not manufacturer_id:
        blockers.append("Zatwierdź CREATE lub wybierz dokładny rekord producenta do LINK.")
    if manufacturer_action == "CREATE" and exact:
        blockers.append("Istnieje rekord producenta dopuszczony do LINK. Rozstrzygnij powiązanie po ponownym DRY RUN.")
    if not manufacturer_link_confirmed:
        blockers.append("Potwierdź powiązanie z wybranym istniejącym producentem.")
    if not similar_confirmed:
        blockers.append("Potwierdź decyzję CREATE po przeglądzie podobnych producentów.")
    if product_action == "Brak decyzji" or product_action == "LINK" and not product_id:
        blockers.append("Zatwierdź CREATE lub wybierz rekord produktu do LINK.")
    if product_action == "LINK" and manufacturer_action != "LINK":
        blockers.append("LINK produktu wymaga LINK producenta.")
    if product_action == "CREATE" and product_candidates:
        blockers.append("Istnieje dokładny kandydat produktu. Rozstrzygnij LINK po ponownym DRY RUN.")
    if not null_confirmed:
        blockers.append("Potwierdź LINK produktu z brakującym kodem w JSON.")
    if not description.strip() or not restriction.strip() or not manual_confirmed:
        blockers.append("Uzupełnij i potwierdź oba pola zastosowania.")
    if not pdf_valid:
        blockers.append("Wybierz poprawny PDF zgodny z SHA-256 zapisanym w Evidence JSON.")
    if not pdf_confirmed or not reviewer.strip():
        blockers.append("Potwierdź PDF i podaj osobę zatwierdzającą.")
    if not document_confirmed:
        blockers.append("Zatwierdź logical SDS po przeglądzie dowodów źródłowych.")
    if any(item in plan.blockers for item in (
        "EXTRACTION_VALIDATION_BLOCKED", "MANUFACTURER_PRODUCT_CODE_REQUIRES_HUMAN_REVIEW",
        "PRODUCT_NAME_REQUIRES_HUMAN_REVIEW", "INVALID_ISSUE_DATE",
    )):
        blockers.append("DRY RUN zawiera nierozstrzygnięte blokady ekstrakcji.")
    for item in blockers:
        st.warning(item)
    approve, cancel = st.columns([1, 1])
    if approve.button("Zatwierdź plan importu", type="primary", icon=":material/fact_check:",
                      disabled=bool(blockers), key="evidence-approve"):
        manufacturer = IdentityDecision(
            manufacturer_action, canonical or "", selected_id=manufacturer_id,
            manufacturer_link_confirmed=(manufacturer_link_confirmed
                                         if manufacturer_action == "LINK" else False),
        )
        product = IdentityDecision(
            product_action, plan.mapped_product_name or "", selected_id=product_id,
            manufacturer_product_code=plan.mapped_manufacturer_product_code,
            null_code_link_confirmed=null_confirmed,
        )
        try:
            work["approved"] = composition.approve_evidence_import(
                work["raw"], document_key, manufacturer, product,
                description, restriction, None, source["original_filename"], pdf.content,
                HumanApproval(reviewer.strip(), True, True, manual_confirmed,
                              False, pdf_confirmed),
            )
            work["pdf_bytes"] = pdf.content
            work["document_key"] = document_key
            st.rerun()
        except (ImportPlanError, ShellInitializationError, ValueError) as error:
            st.error(f"Nie można zatwierdzić planu: {error}")
    if cancel.button("Anuluj", key="evidence-cancel"):
        _reset()
        st.rerun()


def render_evidence_import(composition: ShellComposition) -> None:
    if RESULT_KEY in st.session_state:
        _render_result()
        return
    st.caption("Jeden Evidence JSON · jeden logical SDS · jedno zatwierdzenie · jeden kontrolowany zapis")
    payload = None
    binding = None
    with st.container(border=True):
        json_col, pdf_col = st.columns(2, gap="medium")
        with json_col:
            st.markdown("#### Evidence JSON")
            raw_upload = st.file_uploader("Wybierz Evidence JSON *", type=["json"],
                                          key="evidence-json-upload")
            if raw_upload:
                st.caption(raw_upload.name)
        with pdf_col:
            st.markdown("#### Źródłowy PDF")
            if raw_upload:
                try:
                    payload = json.loads(raw_upload.getvalue())
                    binding = composition.resolve_evidence_pdf(raw_upload.name, payload)
                    if binding.status == "FALLBACK_REQUIRED":
                        st.info("Nie odnaleziono źródłowego PDF. Wskaż plik ręcznie.")
                        fallback_upload = st.file_uploader("Wskaż źródłowy PDF", type=["pdf"],
                                                           key="evidence-pdf-upload")
                        if fallback_upload:
                            binding = composition.resolve_evidence_pdf(
                                raw_upload.name, payload,
                                (fallback_upload.name, fallback_upload.getvalue()),
                            )
                    if binding.status in BOUND_STATUSES:
                        st.badge("PDF powiązany / zweryfikowany", color="green")
                        st.write(binding.filename)
                        st.caption("SHA-256 zgodny z Evidence JSON" +
                                   (" i manifestem" if binding.status == "AUTO_BOUND" else ""))
                    elif binding.status == "PDF_MISMATCH":
                        st.error("PDF_MISMATCH — SHA-256 lub sygnatura PDF jest niezgodna. DRY RUN zablokowany.")
                    elif binding.status == "INVALID_SOURCE":
                        st.error("Niepoprawne metadane źródłowe w Evidence JSON.")
                except (ValueError, TypeError, ShellInitializationError) as error:
                    st.error(f"Nie można odczytać Evidence JSON: {error}")
            else:
                st.caption("Wybierz Evidence JSON, aby ustalić źródłowy PDF.")
    work = st.session_state.get(WORK_KEY)
    if work and (work["json_signature"] != _source_signature(raw_upload)
                 or binding is None or binding.status not in BOUND_STATUSES
                 or work.get("binding_signature") != binding.signature):
        st.session_state.pop(WORK_KEY, None)
        work = None
        st.error(STALE_MESSAGE)
    if st.button("Uruchom DRY RUN", disabled=binding is None or binding.status not in BOUND_STATUSES,
                 icon=":material/preview:", key="evidence-dry-run"):
        try:
            raw = raw_upload.getvalue()
            plans = composition.dry_run_evidence_json(payload)
            st.session_state[WORK_KEY] = {
                "raw": raw, "payload": payload, "plans": plans,
                "json_signature": _source_signature(raw_upload),
                "binding_signature": binding.signature,
            }
            st.rerun()
        except (ValueError, TypeError, ShellInitializationError) as error:
            st.error(f"Nie można wykonać DRY RUN: {error}")
    if work:
        _render_review(composition, work, binding)
