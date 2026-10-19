"""Streamlit rendering for the Product Registry."""

from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path

import streamlit as st

from app.application.dto import (
    AddSdsRevisionInput,
    AssignProductUsageLocationInput,
    AssignLegacyUsageLocationCodeInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    SupervisoryProductRow,
    UpdateProductAdministrativeDataInput,
    CompleteManufacturerProductCodeInput,
    CorrectProductIdentityInput,
    UpdateProductUsageLocationInput,
)
from app.application.exceptions import SupervisoryReadError
from app.application.use_cases.import_sds import SdsImportCleanupError
from app.domain.enums import UsageLocationStatus
from app.domain.models import UnitOfMeasure
from app.infrastructure.db.transactions import PersistenceError
from app.presentation.streamlit.composition import (
    ShellComposition,
    ShellInitializationError,
)


MISSING_VALUE = "Brak danych"
PRODUCT_CARD_KEY = "product-card-id"
PRODUCT_CARD_STYLE = """
<style>
.product-card-title {
    font-size: 31px;
    font-weight: 700;
    line-height: 1.16;
    margin: 0 0 5px;
    overflow-wrap: anywhere;
}
.product-card-meta {
    font-size: 15.5px;
    line-height: 1.35;
    margin: 1px 0;
}
.product-card-section {
    font-size: 21px;
    font-weight: 650;
    line-height: 1.2;
    margin: 0 0 7px;
}
.product-card-field {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0 8px;
    line-height: 1.3;
    margin: 2px 0;
}
.product-card-label {
    font-size: 14.5px;
    opacity: .76;
}
.product-card-value {
    font-size: 16px;
    font-weight: 500;
    overflow-wrap: anywhere;
}
.st-key-product-card-actions button {
    min-height: 42px;
    padding: 6px 10px;
    font-size: 15px;
    line-height: 1.2;
}
.st-key-product-card-actions button,
[class*="st-key-add-location-"] button,
[class*="st-key-edit-admin-"] button,
[class*="st-key-assign-"] button,
[class*="st-key-product-admin-"] button,
[class*="st-key-cancel-admin-"] button,
[class*="st-key-cancel-location-"] button {
    border-radius: 8px;
    transition: background-color .15s ease, border-color .15s ease;
}
.st-key-product-card-actions [class*="st-key-complete-code-"] button,
[class*="st-key-add-location-"] button,
[class*="st-key-edit-admin-"] button {
    background-color: #dceaf7 !important;
    border-color: #b8cee3 !important;
    color: #183f63 !important;
    min-height: 38px;
    padding: 6px 12px;
    font-size: 15px;
}
.st-key-product-card-actions [class*="st-key-correct-product-"] button,
.st-key-product-card-actions [class*="st-key-add-revision-"] button,
.st-key-product-card-actions [class*="st-key-current-sds-download-"] button {
    background-color: #f0f4f8 !important;
    border-color: #d2dce6 !important;
    color: #31475e !important;
}
.st-key-product-card-actions [class*="st-key-product-more-actions-"] button,
[class*="st-key-cancel-admin-"] button,
[class*="st-key-cancel-location-"] button {
    background-color: #f3f4f6 !important;
    border-color: #d6d9de !important;
    color: #394554 !important;
}
[class*="st-key-assign-"] button,
[class*="st-key-product-admin-"] button {
    background-color: #246ba5 !important;
    border-color: #246ba5 !important;
    color: #fff !important;
}
[class*="st-key-delete-product-"] button,
[class*="st-key-confirm-delete-product-action-"] button {
    background-color: #a63232 !important;
    border-color: #a63232 !important;
    color: #fff !important;
}
.st-key-product-card-actions button:hover,
[class*="st-key-add-location-"] button:hover,
[class*="st-key-edit-admin-"] button:hover,
[class*="st-key-assign-"] button:hover,
[class*="st-key-product-admin-"] button:hover,
[class*="st-key-cancel-admin-"] button:hover,
[class*="st-key-cancel-location-"] button:hover {
    filter: brightness(.96);
}
</style>
"""
STATUS_LABELS = {
    "ACTIVE": "Aktywny",
    "PENDING_APPROVAL": "Oczekuje na BHP",
    "REJECTED": "Odrzucony",
    "INACTIVE": "Nieaktywny",
}


def _optional_text(value: str | Decimal | None) -> str:
    return MISSING_VALUE if value is None else str(value)


def _card_section(title: str) -> None:
    st.markdown(
        f'<div class="product-card-section" role="heading" aria-level="3">{escape(title)}</div>',
        unsafe_allow_html=True,
    )


def _card_fields(fields: tuple[tuple[str, object], ...], title: str | None = None) -> None:
    heading = (
        f'<div class="product-card-section" role="heading" aria-level="3">{escape(title)}</div>'
        if title else ""
    )
    rows = "".join(
        '<div class="product-card-field">'
        f'<span class="product-card-label">{escape(label)}:</span>'
        f'<span class="product-card-value">{escape(str(value))}</span>'
        '</div>'
        for label, value in fields
    )
    st.markdown(heading + rows, unsafe_allow_html=True)


def _status_label(status) -> str:
    return STATUS_LABELS.get(status.value, status.value)


def _sds_label(row: SupervisoryProductRow | None) -> str:
    if row is None:
        return "—"
    if row.current_sds_id is None:
        return "Brak CURRENT SDS"
    return "CURRENT" if row.current_sds_file_available else "Brak pliku SDS"


def _bhp_label(row: SupervisoryProductRow | None) -> str:
    if row is None:
        return "—"
    if row.current_bhp_decision_status is None:
        return "Brak decyzji"
    return {
        "APPROVED": "Zatwierdzona",
        "REJECTED": "Odrzucona",
    }.get(row.current_bhp_decision_status.value, row.current_bhp_decision_status.value)


def _registry_row(product: ProductListItem, row: SupervisoryProductRow | None) -> dict[str, str]:
    return {
        "Produkt": product.product_name,
        "Kod producenta": _optional_text(product.manufacturer_product_code),
        "Producent": product.manufacturer_name,
        "Status": _status_label(product.usage_status),
        "SDS": _sds_label(row),
        "Rewizja SDS": (
            row.current_sds_revision or "—"
            if row is not None and row.current_sds_id is not None else "—"
        ),
        "BHP": _bhp_label(row),
    }


def _location_row(location: ProductUsageLocationDetails) -> dict[str, str]:
    return {
        "Lokalizacja": location.location_name,
        "Maksymalna ilość": str(location.peak_quantity_value),
        "Jednostka": location.peak_quantity_unit,
        "Zużycie miesięczne": "—" if location.monthly_consumption_value is None else str(location.monthly_consumption_value),
        "Jednostka zużycia": (
            location.monthly_consumption_unit or "—"
            if location.monthly_consumption_value is not None else "—"
        ),
    }


def _render_identity_correction(
    composition, details: ProductDetails, *, show_button: bool = True
) -> None:
    active_key = f"identity-correction-active-{details.product_id}"
    if show_button and st.button("Korekta danych identyfikacyjnych", key=f"correct-product-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.subheader("Korekta danych identyfikacyjnych")
    product_name = st.text_input(
        "Nazwa produktu",
        details.product_name,
        key=f"edit-product-name-{details.product_id}",
    )
    manufacturer_product_code = st.text_input(
        "Kod produktu producenta",
        details.manufacturer_product_code or "",
        key=f"correct-product-code-{details.product_id}",
    )
    manufacturer_name = st.text_input(
        "Producent",
        details.manufacturer_name,
        key=f"correct-manufacturer-{details.product_id}",
    )
    confirmed = st.checkbox(
        "Potwierdzam, że poprawiam błędnie zarejestrowane dane, a nie rejestruję innego produktu.",
        key=f"confirm-correction-{details.product_id}",
    )
    save, cancel = st.columns(2)
    if save.button("Zapisz korektę", key=f"save-correction-{details.product_id}"):
        if not confirmed:
            st.error("Potwierdź znaczenie korekty przed zapisem.")
            return
        try:
            composition.correct_product_identity(
                CorrectProductIdentityInput(
                    product_id=details.product_id,
                    product_name=product_name,
                    manufacturer_product_code=manufacturer_product_code,
                    manufacturer_name=manufacturer_name,
                )
            )
            st.session_state.pop(active_key, None)
            st.success("Korekta danych identyfikacyjnych zapisana.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))
    if cancel.button("Anuluj korektę", key=f"cancel-correction-{details.product_id}"):
        st.session_state.pop(active_key, None)
        st.rerun()


def _render_code_completion(
    composition, details: ProductDetails, *, show_button: bool = True
) -> None:
    if details.manufacturer_product_code is not None:
        return
    active_key = f"code-completion-active-{details.product_id}"
    if show_button and st.button("Uzupełnij kod producenta", key=f"complete-code-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return
    code = st.text_input("Kod produktu producenta", key=f"new-code-{details.product_id}")
    save, cancel = st.columns(2)
    if save.button("Zapisz kod", key=f"save-code-{details.product_id}"):
        try:
            composition.complete_manufacturer_product_code(
                CompleteManufacturerProductCodeInput(details.product_id, code)
            )
            st.session_state.pop(active_key, None)
            st.success("Kod producenta uzupełniony.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))
    if cancel.button("Anuluj", key=f"cancel-code-{details.product_id}"):
        st.session_state.pop(active_key, None)
        st.rerun()


def _render_delete_product(composition, details: ProductDetails) -> None:
    active_key = f"delete-product-active-{details.product_id}"
    if st.button("Usuń produkt", key=f"delete-product-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.warning(
        "Usunięcie produktu jest nieodwracalne w bazie danych. "
        f"Produkt: {details.product_name}; producent: {details.manufacturer_name}; "
        f"kod: {details.manufacturer_product_code}; SDS: {details.sds_count}; "
        f"miejsca stosowania: {len(details.usage_locations)}; "
        f"decyzje BHP: {details.bhp_decision_count}. "
        "Pliki SDS i dowody BHP pozostaną na dysku."
    )
    confirmed = st.checkbox(
        "Potwierdzam usunięcie tego produktu",
        key=f"confirm-delete-product-{details.product_id}",
    )
    if st.button(
        "Usuń produkt trwale", key=f"confirm-delete-product-action-{details.product_id}"
    ):
        if not confirmed:
            st.error("Zaznacz potwierdzenie usunięcia produktu.")
            return
        try:
            composition.delete_product(details.product_id)
            st.session_state.pop(active_key, None)
            st.success("Produkt został usunięty z bazy danych.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))


def _current_sds_download(composition, product_id: str, current_sds):
    if current_sds is None:
        return None, None
    try:
        current_file = composition.get_current_sds_file(product_id)
    except FileNotFoundError:
        return None, ("info", "MISSING — Plik SDS jest obecnie niedostępny.")
    except (ShellInitializationError, OSError, ValueError):
        return None, ("error", "Nie udało się bezpiecznie odczytać pliku CURRENT SDS.")
    if current_file is None:
        return None, ("info", "Brak CURRENT SDS do pobrania.")
    return current_file, None


def _render_details(
    composition, details: ProductDetails, row: SupervisoryProductRow | None
) -> None:
    identity_column, sds_column = st.columns(2)
    with identity_column:
        with st.container(border=True):
            _card_fields((
                ("Nazwa produktu", details.product_name),
                ("Kod producenta", _optional_text(details.manufacturer_product_code)),
                ("Producent", details.manufacturer_name),
                ("Status użytkowania", _status_label(details.usage_status)),
            ), title="Tożsamość produktu")
    with sds_column:
        with st.container(border=True):
            current_sds = row if row is not None and row.current_sds_id is not None else None
            sds_fields = [
                ("Stan SDS", _sds_label(row)),
                ("Rewizja SDS", current_sds.current_sds_revision or MISSING_VALUE if current_sds else MISSING_VALUE),
                ("Data wydania / rewizji SDS", current_sds.current_sds_issue_date or MISSING_VALUE if current_sds else MISSING_VALUE),
            ]
            if current_sds is not None:
                sds_fields.append(("Plik SDS", current_sds.current_sds_filename or MISSING_VALUE))
            sds_fields.append(("Stan BHP", _bhp_label(row)))
            _card_fields(tuple(sds_fields), title="SDS i BHP")

    _card_section("Miejsca stosowania")
    if not details.usage_locations:
        st.info("Brak przypisanych miejsc stosowania.")
    else:
        selection = st.dataframe(
            [_location_row(location) for location in details.usage_locations],
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"product-locations-{details.product_id}",
        )
    if st.button("+ Dodaj miejsce", key=f"add-location-{details.product_id}"):
        st.session_state[f"location-mode-{details.product_id}"] = "add"
    _render_product_operations(
        composition, details, selection if details.usage_locations else None,
        show_add_button=False,
    )

    admin_title, admin_action = st.columns([4, 1])
    with admin_title:
        _card_section("Dane administracyjne")
    admin_key = f"edit-admin-active-{details.product_id}"
    if admin_action.button("Edytuj", key=f"edit-admin-{details.product_id}"):
        st.session_state[admin_key] = True
    admin_left, admin_right = st.columns(2)
    with admin_left:
        _card_fields((
            ("Opis użycia", details.use_description),
            ("Typ odpadu", _optional_text(details.waste_type)),
        ))
    with admin_right:
        _card_fields((
            ("Ograniczenia użycia", details.use_restriction),
            ("Kod odpadu", _optional_text(details.waste_code)),
        ))
    if not st.session_state.get(admin_key):
        return
    with st.container(border=True, key=f"admin-editor-{details.product_id}"):
        use_description = st.text_input("Opis użycia", details.use_description)
        use_restriction = st.text_input("Ograniczenia użycia", details.use_restriction)
        waste_type = st.text_input("Typ odpadu", details.waste_type or "")
        waste_code = st.text_input("Kod odpadu", details.waste_code or "")
        save_admin, cancel_admin = st.columns(2, gap="small")
        if save_admin.button("Zapisz dane administracyjne", key=f"product-admin-{details.product_id}", width="stretch"):
            try:
                composition.update_product_administrative_data(
                    UpdateProductAdministrativeDataInput(
                        product_id=details.product_id,
                        use_description=use_description,
                        use_restriction=use_restriction,
                        waste_type=waste_type or None,
                        waste_code=waste_code or None,
                    )
                )
                composition.get_product_details(details.product_id)
                st.session_state.pop(admin_key, None)
                st.success("Dane administracyjne zapisane.")
            except ShellInitializationError as error:
                st.error(str(error))
        if cancel_admin.button("Anuluj", key=f"cancel-admin-{details.product_id}", width="stretch"):
            st.session_state.pop(admin_key, None)
            st.rerun()


def _decimal(value: str, label: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: podaj poprawną liczbę.") from None


def _quantity_form(
    composition, details: ProductDetails, location, units: tuple[UnitOfMeasure, ...]
) -> None:
    st.subheader("Edytuj przypisanie")
    st.text(f"Lokalizacja: {location.location_name}")
    prefix = f"edit-location-{details.product_id}-{location.location_id}"
    # Parse only on save so an incomplete field does not interrupt rendering.
    peak_value, peak_unit, monthly_value, monthly_unit = _quantity_fields(
        prefix, str(location.peak_quantity_value), location.peak_quantity_unit_id,
        location.monthly_consumption_value, location.monthly_consumption_unit_id, units,
    )
    if st.button("Zapisz przypisanie", key=f"quantity-{details.product_id}-{location.location_id}"):
        try:
            if peak_unit is None:
                raise ValueError("Jednostka maksymalnej ilości jest wymagana.")
            monthly_quantity = _optional_monthly_quantity(monthly_value)
            if monthly_quantity is not None and monthly_unit is None:
                raise ValueError("Jednostka zużycia miesięcznego jest wymagana.")
            composition.update_product_usage_location(
                UpdateProductUsageLocationInput(
                    product_id=details.product_id,
                    location_id=location.location_id,
                    peak_quantity_value=_decimal(peak_value, "Maksymalna ilość na stanowisku"),
                    peak_quantity_unit_id=peak_unit.unit_id,
                    monthly_consumption_value=monthly_quantity,
                    monthly_consumption_unit_id=monthly_unit.unit_id if monthly_quantity is not None else None,
                )
            )
            st.session_state.pop(f"location-mode-{details.product_id}", None)
            st.success("Przypisanie zapisane.")
            st.rerun()
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))


def _optional_monthly_quantity(value: str | None) -> Decimal | None:
    return None if value is None or not value.strip() else _decimal(value, "Zużycie miesięczne")


def _quantity_fields(
    prefix: str, peak: str, peak_unit_id: str | None,
    monthly: Decimal | None, monthly_unit_id: str | None,
    units: tuple[UnitOfMeasure, ...],
):
    first, second = st.columns(2)
    with first:
        peak_value = st.text_input("Maksymalna ilość na stanowisku", peak, key=f"{prefix}-peak")
    with second:
        peak_unit = st.selectbox(
            "Jednostka", units,
            index=next((i for i, unit in enumerate(units) if unit.unit_id == peak_unit_id), None),
            format_func=lambda unit: unit.code,
            placeholder="Wybierz jednostkę",
            key=f"{prefix}-peak-unit",
        )
    monthly_enabled = st.checkbox("Podaj miesięczne zużycie", value=monthly is not None,
                                  key=f"{prefix}-monthly-enabled")
    if not monthly_enabled:
        return peak_value, peak_unit, None, None
    first, second = st.columns(2)
    with first:
        monthly_value = st.text_input("Zużycie miesięczne", "" if monthly is None else str(monthly),
                                      key=f"{prefix}-monthly")
    with second:
        monthly_unit = st.selectbox(
            "Jednostka", units,
            index=next((i for i, unit in enumerate(units) if unit.unit_id == monthly_unit_id), None),
            format_func=lambda unit: unit.code,
            placeholder="Wybierz jednostkę",
            key=f"{prefix}-monthly-unit",
        )
    return peak_value, peak_unit, monthly_value, monthly_unit


def _render_product_operations(
    composition, details: ProductDetails, selection, *, show_add_button: bool = True
) -> None:
    mode_key = f"location-mode-{details.product_id}"
    if show_add_button and st.button("+ Dodaj miejsce stosowania", key=f"add-location-{details.product_id}"):
        st.session_state[mode_key] = "add"
    selected_rows = selection.selection.rows if selection is not None else []
    if selected_rows and selected_rows[0] < len(details.usage_locations):
        if st.button("Edytuj przypisanie", key=f"edit-location-{details.product_id}"):
            st.session_state[mode_key] = details.usage_locations[selected_rows[0]].location_id
    mode = st.session_state.get(mode_key)
    if mode is None:
        return
    try:
        units = composition.list_active_units()
    except ShellInitializationError as error:
        st.error(str(error))
        return
    if mode != "add":
        location = next((item for item in details.usage_locations if item.location_id == mode), None)
        if location is not None:
            _quantity_form(composition, details, location, units)
        if st.button("Anuluj", key=f"cancel-location-{details.product_id}"):
            st.session_state.pop(mode_key, None)
            st.rerun()
        return

    locations = composition.list_usage_locations()
    available = [
        location
        for location in locations
        if location.status is UsageLocationStatus.ACTIVE
        and location.location_id not in {item.location_id for item in details.usage_locations}
    ]
    st.subheader("Dodaj miejsce stosowania")
    if available:
        location_id = st.selectbox(
            "Aktywna lokalizacja",
            [location.location_id for location in available],
            format_func=lambda selected: next(
                location.location_name
                for location in available
                if location.location_id == selected
            ),
        )
        peak_value, peak_unit, monthly_value, monthly_unit = _quantity_fields(
            f"add-location-{details.product_id}", "0", None, None, None, units
        )
        assign_location, cancel_location = st.columns(2, gap="small")
        if assign_location.button("Przypisz lokalizację", key=f"assign-{details.product_id}", width="stretch"):
            try:
                if peak_unit is None:
                    raise ValueError("Jednostka maksymalnej ilości jest wymagana.")
                monthly_quantity = _optional_monthly_quantity(monthly_value)
                if monthly_quantity is not None and monthly_unit is None:
                    raise ValueError("Jednostka zużycia miesięcznego jest wymagana.")
                composition.assign_product_usage_location(
                    AssignProductUsageLocationInput(
                        product_id=details.product_id,
                        location_id=location_id,
                        peak_quantity_value=_decimal(peak_value, "Maksymalna ilość na stanowisku"),
                        peak_quantity_unit_id=peak_unit.unit_id,
                        monthly_consumption_value=monthly_quantity,
                        monthly_consumption_unit_id=monthly_unit.unit_id if monthly_quantity is not None else None,
                    )
                )
                st.session_state.pop(mode_key, None)
                st.success("Lokalizacja przypisana.")
                st.rerun()
            except (ShellInitializationError, ValueError) as error:
                st.error(str(error))
    else:
        st.info("Brak dostępnych aktywnych lokalizacji do przypisania.")
        cancel_location = st
    if cancel_location.button("Anuluj", key=f"cancel-location-{details.product_id}", width="stretch"):
        st.session_state.pop(mode_key, None)
        st.rerun()


def _render_revision(
    composition, details: ProductDetails, current_sds: SupervisoryProductRow | None = None,
    *, show_button: bool = True,
) -> None:
    active_key = f"revision-active-{details.product_id}"
    if show_button and st.button("Dodaj nową rewizję SDS", key=f"add-revision-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.subheader("Nowa rewizja SDS")
    st.text(f"Produkt: {details.product_name}")
    st.text(f"Producent: {details.manufacturer_name}")
    st.text(f"Kod producenta: {_optional_text(details.manufacturer_product_code)}")
    if current_sds is not None and current_sds.current_sds_id is not None:
        st.text(
            f"Aktualny SDS: {current_sds.current_sds_filename or MISSING_VALUE}; "
            f"rewizja SDS: {current_sds.current_sds_revision or MISSING_VALUE}"
        )
    else:
        st.text("Aktualny SDS: Brak danych")
    uploaded = st.file_uploader(
        "Wybierz plik PDF z komputera", type=["pdf"], key=f"revision-upload-{details.product_id}"
    )
    files = composition.list_sds_files()
    selected = None
    if files:
        st.caption("Lub wybierz plik już obecny w katalogu SDS")
        selected = st.selectbox(
            "Plik PDF *", files, format_func=lambda path: Path(path).name,
            key=f"revision-file-{details.product_id}",
        )
    revision_column, date_column = st.columns(2)
    with revision_column:
        revision = st.text_input(
            "Rewizja SDS", key=f"revision-value-{details.product_id}"
        )
    with date_column:
        issue_date = st.date_input(
            "Data wydania / rewizji SDS", value=None, key=f"revision-date-{details.product_id}"
        )
    save, cancel = st.columns(2)
    if save.button("Zapisz nową rewizję", key=f"save-revision-{details.product_id}"):
        try:
            if uploaded is None and selected is None:
                raise ValueError("Wybierz plik PDF SDS.")
            data = AddSdsRevisionInput(
                product_id=details.product_id,
                source_relative_path=selected or "",
                revision=revision or None,
                issue_date=issue_date,
            )
            if uploaded is not None:
                composition.import_sds_revision(data, uploaded.name, uploaded.getvalue())
            else:
                composition.accept_sds_revision(data)
            st.session_state.pop(active_key, None)
            st.success("Nowa rewizja została zapisana. Produkt oczekuje na decyzję BHP.")
        except (ShellInitializationError, SdsImportCleanupError, PersistenceError, ValueError, OSError) as error:
            st.error(str(error))
    if cancel.button(
        "Anuluj nową rewizję", key=f"cancel-revision-{details.product_id}"
    ):
        st.session_state.pop(active_key, None)
        st.rerun()


def _render_product_card(
    composition: ShellComposition, product_id: str,
    supervisory_rows: dict[str, SupervisoryProductRow],
) -> None:
    st.markdown(PRODUCT_CARD_STYLE, unsafe_allow_html=True)
    if st.button("← Produkty", key="back-to-products"):
        st.session_state.pop(PRODUCT_CARD_KEY, None)
        st.rerun()
    try:
        details = composition.get_product_details(product_id)
    except ShellInitializationError as error:
        st.error(str(error))
        return

    row = supervisory_rows.get(product_id)
    current_sds = row if row is not None and row.current_sds_id is not None else None
    revision = current_sds.current_sds_revision or MISSING_VALUE if current_sds else MISSING_VALUE
    st.markdown(
        f'<div class="product-card-title">{escape(details.product_name)}</div>'
        '<div class="product-card-meta">'
        f'{escape(details.manufacturer_name)} · Kod producenta: '
        f'{escape(_optional_text(details.manufacturer_product_code))}'
        '</div><div class="product-card-meta">'
        f'Status użytkowania: {escape(_status_label(details.usage_status))} · '
        f'SDS: {escape(_sds_label(row))} · Rewizja SDS: {escape(str(revision))}'
        '</div>', unsafe_allow_html=True,
    )
    current_file, download_status = _current_sds_download(composition, product_id, current_sds)
    with st.container(key="product-card-actions"):
        action_columns = st.columns(5 if details.manufacturer_product_code is None else 4, gap="small")
        action_index = 0
        if details.manufacturer_product_code is None:
            with action_columns[action_index]:
                if st.button("Uzupełnij kod producenta", key=f"complete-code-{product_id}", width="stretch"):
                    st.session_state[f"code-completion-active-{product_id}"] = True
            action_index += 1
        with action_columns[action_index]:
            if st.button("Korekta danych identyfikacyjnych", key=f"correct-product-{product_id}", width="stretch"):
                st.session_state[f"identity-correction-active-{product_id}"] = True
        with action_columns[action_index + 1]:
            if st.button("Dodaj nową rewizję SDS", key=f"add-revision-{product_id}", width="stretch"):
                st.session_state[f"revision-active-{product_id}"] = True
        with action_columns[action_index + 2]:
            if current_file is None:
                st.button("Pobierz SDS", key=f"current-sds-download-{product_id}", disabled=True, width="stretch")
            else:
                st.download_button(
                    "Pobierz SDS", current_file.content,
                    file_name=current_file.original_filename, mime="application/pdf",
                    key=f"current-sds-download-{product_id}", width="stretch",
                )
        with action_columns[action_index + 3]:
            with st.popover(
                "Więcej akcji", icon=":material/more_horiz:",
                key=f"product-more-actions-{product_id}", width="stretch",
            ):
                _render_delete_product(composition, details)
    if download_status is not None:
        level, message = download_status
        getattr(st, level)(message)

    _render_code_completion(composition, details, show_button=False)
    _render_identity_correction(composition, details, show_button=False)
    _render_revision(composition, details, row, show_button=False)
    _render_details(composition, details, row)


def render_product_registry(composition: ShellComposition) -> None:
    products = composition.products
    card_id = st.session_state.get(PRODUCT_CARD_KEY)
    if card_id is not None and card_id not in {product.product_id for product in products}:
        st.session_state.pop(PRODUCT_CARD_KEY, None)
        card_id = None

    if not products:
        st.header("Produkty")
        st.info("Brak produktów w rejestrze.")
        return

    try:
        supervisory_rows = {
            row.product_id: row for row in composition.list_supervisory_products()
        }
    except (ShellInitializationError, SupervisoryReadError):
        supervisory_rows = {}
        st.warning("Nie udało się odczytać bieżącego stanu SDS i BHP.")

    if card_id is not None:
        _render_product_card(composition, card_id, supervisory_rows)
        return

    st.header("Produkty")
    search_column, sort_column = st.columns([3, 1])
    with search_column:
        search = st.text_input(
            "Szukaj produktu", value=st.session_state.get("product-registry-search-value", ""),
            key="product-registry-search",
        )
        st.session_state["product-registry-search-value"] = search
        query = search.strip().casefold()
    with sort_column:
        sort_options = ("Domyślnie", "Produkt", "Producent", "Kod producenta")
        previous_sort = st.session_state.get("product-registry-sort-value", "Domyślnie")
        sort_by = st.selectbox(
            "Sortuj", sort_options, index=sort_options.index(previous_sort),
            key="product-registry-sort",
        )
        st.session_state["product-registry-sort-value"] = sort_by
    visible_products = [
        product for product in products
        if query in " ".join((
            product.product_name, product.manufacturer_name,
            product.manufacturer_product_code or "",
        )).casefold()
    ]
    if sort_by != "Domyślnie":
        sort_keys = {
            "Produkt": lambda product: product.product_name.casefold(),
            "Producent": lambda product: product.manufacturer_name.casefold(),
            "Kod producenta": lambda product: (product.manufacturer_product_code or "").casefold(),
        }
        visible_products.sort(key=sort_keys[sort_by])
    if not visible_products:
        st.info("Brak produktów pasujących do wyszukiwania.")
        return

    selection = st.dataframe(
        [_registry_row(product, supervisory_rows.get(product.product_id)) for product in visible_products],
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"product-registry-{query}-{sort_by}",
    )
    selected_rows = selection.selection.rows
    if not selected_rows or selected_rows[0] >= len(visible_products):
        st.info("Wybierz produkt w tabeli, aby otworzyć jego kartę.")
        return
    selected_product = visible_products[selected_rows[0]]
    st.caption(f"Wybrany produkt: {selected_product.product_name} · {selected_product.manufacturer_name}")
    if st.button("Otwórz kartę produktu", key="open-product-card"):
        st.session_state[PRODUCT_CARD_KEY] = selected_product.product_id
        st.rerun()


def render_usage_locations(composition: ShellComposition) -> None:
    st.header("Stanowiska")
    locations = composition.list_usage_locations()
    missing_count = sum(location.location_code is None for location in locations)
    st.caption(f"Brak symbolu: {missing_count}")
    if locations:
        symbol_header, name_header, status_header, action_header = st.columns([2, 3, 1, 2])
        symbol_header.markdown("**Symbol**")
        name_header.markdown("**Lokalizacja**")
        status_header.markdown("**Status**")
        action_header.markdown("**Akcja**")
        for location in locations:
            with st.container(border=True):
                symbol_col, name_col, status_col, action_col = st.columns([2, 3, 1, 2])
                with symbol_col:
                    st.write(location.location_code or "BRAK SYMBOLU")
                    if location.location_code is None:
                        code = st.text_input(
                            "Symbol", key=f"legacy-code-{location.location_id}",
                            label_visibility="collapsed", placeholder="Symbol",
                        )
                        if st.button("Uzupełnij", key=f"legacy-assign-{location.location_id}"):
                            try:
                                composition.assign_legacy_usage_location_code(
                                    AssignLegacyUsageLocationCodeInput(location.location_id, code)
                                )
                                st.rerun()
                            except (ShellInitializationError, ValueError) as error:
                                st.error(str(error))
                name_col.write(location.location_name)
                status_col.write(location.status.value)
                action = (
                    "Dezaktywuj" if location.status is UsageLocationStatus.ACTIVE
                    else "Reaktywuj"
                )
                with action_col:
                    if st.button(action, key=f"location-status-{location.location_id}"):
                        try:
                            composition.change_usage_location_status(
                                location.location_id,
                                active=location.status is UsageLocationStatus.INACTIVE,
                            )
                            st.rerun()
                        except ShellInitializationError as error:
                            st.error(str(error))

    location_code = st.text_input("Symbol lokalizacji")
    location_name = st.text_input("Nazwa lokalizacji")
    if st.button("Dodaj lokalizację"):
        try:
            if not location_name.strip():
                raise ValueError("Nazwa lokalizacji jest wymagana.")
            composition.create_usage_location(
                CreateUsageLocationInput(
                    location_name=location_name.strip(), location_code=location_code
                )
            )
            st.rerun()
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))
