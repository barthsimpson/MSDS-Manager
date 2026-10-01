"""Streamlit rendering for the Product Registry."""

from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st

from app.application.dto import (
    AddSdsRevisionInput,
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    SupervisoryProductRow,
    UpdateProductAdministrativeDataInput,
    UpdateProductIdentityInput,
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
STATUS_LABELS = {
    "ACTIVE": "Aktywny",
    "PENDING_APPROVAL": "Oczekuje na BHP",
    "REJECTED": "Odrzucony",
    "INACTIVE": "Nieaktywny",
}


def _optional_text(value: str | Decimal | None) -> str:
    return MISSING_VALUE if value is None else str(value)


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
        "Kod producenta": product.manufacturer_product_code,
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


def _render_identity_edit(composition, details: ProductDetails) -> None:
    active_key = f"identity-edit-active-{details.product_id}"
    if st.button("Edytuj dane produktu", key=f"edit-product-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.subheader("Edycja danych produktu")
    product_name = st.text_input(
        "Nazwa produktu",
        details.product_name,
        key=f"edit-product-name-{details.product_id}",
    )
    manufacturer_product_code = st.text_input(
        "Kod produktu producenta",
        details.manufacturer_product_code,
        key=f"edit-product-code-{details.product_id}",
    )
    manufacturer_name = st.text_input(
        "Producent",
        details.manufacturer_name,
        key=f"edit-manufacturer-{details.product_id}",
    )
    save, cancel = st.columns(2)
    if save.button("Zapisz zmiany", key=f"save-product-{details.product_id}"):
        try:
            composition.update_product_identity(
                UpdateProductIdentityInput(
                    product_id=details.product_id,
                    product_name=product_name,
                    manufacturer_product_code=manufacturer_product_code,
                    manufacturer_name=manufacturer_name,
                )
            )
            st.session_state.pop(active_key, None)
            st.success("Dane produktu zapisane.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))
    if cancel.button("Anuluj edycję", key=f"cancel-product-{details.product_id}"):
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


def _render_details(
    composition, details: ProductDetails, row: SupervisoryProductRow | None
) -> None:
    st.subheader("Szczegóły produktu")
    st.markdown("#### Tożsamość")
    st.text(f"Nazwa produktu: {details.product_name}")
    st.text(f"Kod producenta: {details.manufacturer_product_code}")
    st.text(f"Producent: {details.manufacturer_name}")
    st.text(f"Status użytkowania: {_status_label(details.usage_status)}")

    st.markdown("#### SDS")
    st.text(f"Stan: {_sds_label(row)}")
    if row is not None and row.current_sds_id is not None:
        st.text(f"Plik: {row.current_sds_filename or MISSING_VALUE}")
        st.text(f"Data wydania / rewizji SDS: {row.current_sds_issue_date or MISSING_VALUE}")
        st.text(f"Rewizja SDS: {row.current_sds_revision or MISSING_VALUE}")
        try:
            current_file = composition.get_current_sds_file(details.product_id)
        except FileNotFoundError:
            st.info("MISSING — Plik SDS jest obecnie niedostępny.")
        except (ShellInitializationError, OSError, ValueError):
            st.error("Nie udało się bezpiecznie odczytać pliku CURRENT SDS.")
        else:
            if current_file is None:
                st.info("Brak CURRENT SDS do pobrania.")
            else:
                st.download_button(
                    "Pobierz SDS", current_file.content,
                    file_name=current_file.original_filename,
                    mime="application/pdf", key=f"current-sds-download-{details.product_id}",
                )

    st.markdown("#### BHP")
    st.text(f"Stan: {_bhp_label(row)}")

    st.markdown("#### Miejsca stosowania")
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
    _render_product_operations(composition, details, selection if details.usage_locations else None)

    st.subheader("Dane administracyjne")
    st.text(f"Opis użycia: {details.use_description}")
    st.text(f"Ograniczenia użycia: {details.use_restriction}")
    st.text(f"Typ odpadu: {_optional_text(details.waste_type)}")
    st.text(f"Kod odpadu: {_optional_text(details.waste_code)}")
    with st.expander("Edytuj dane administracyjne"):
        use_description = st.text_input("Opis użycia", details.use_description)
        use_restriction = st.text_input("Ograniczenia użycia", details.use_restriction)
        waste_type = st.text_input("Typ odpadu", details.waste_type or "")
        waste_code = st.text_input("Kod odpadu", details.waste_code or "")
        if st.button("Zapisz dane administracyjne", key=f"product-admin-{details.product_id}"):
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
                st.success("Dane administracyjne zapisane.")
            except ShellInitializationError as error:
                st.error(str(error))


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


def _render_product_operations(composition, details: ProductDetails, selection) -> None:
    mode_key = f"location-mode-{details.product_id}"
    if st.button("+ Dodaj miejsce stosowania", key=f"add-location-{details.product_id}"):
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
        if st.button("Przypisz lokalizację", key=f"assign-{details.product_id}"):
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
    if st.button("Anuluj", key=f"cancel-location-{details.product_id}"):
        st.session_state.pop(mode_key, None)
        st.rerun()


def _render_revision(
    composition, details: ProductDetails, current_sds: SupervisoryProductRow | None = None
) -> None:
    active_key = f"revision-active-{details.product_id}"
    if st.button("Dodaj nową rewizję SDS", key=f"add-revision-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.subheader("Nowa rewizja SDS")
    st.text(f"Produkt: {details.product_name}")
    st.text(f"Producent: {details.manufacturer_name}")
    st.text(f"Kod producenta: {details.manufacturer_product_code}")
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


def render_product_registry(composition: ShellComposition) -> None:
    st.header("Produkty")
    products = composition.products
    if not products:
        st.info("Brak produktów w rejestrze.")
        return

    try:
        supervisory_rows = {
            row.product_id: row for row in composition.list_supervisory_products()
        }
    except (ShellInitializationError, SupervisoryReadError):
        supervisory_rows = {}
        st.warning("Nie udało się odczytać bieżącego stanu SDS i BHP.")

    selection = st.dataframe(
        [_registry_row(product, supervisory_rows.get(product.product_id)) for product in products],
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="product-registry",
    )
    selected_rows = selection.selection.rows
    if not selected_rows or selected_rows[0] >= len(products):
        st.info("Wybierz produkt w tabeli, aby zobaczyć szczegóły i akcje.")
        return
    selected_product_id = products[selected_rows[0]].product_id
    try:
        details = composition.get_product_details(selected_product_id)
    except ShellInitializationError as error:
        st.error(str(error))
        return
    _render_details(composition, details, supervisory_rows.get(selected_product_id))
    st.subheader("Akcje produktu")
    _render_identity_edit(composition, details)
    _render_revision(composition, details, supervisory_rows.get(selected_product_id))
    st.divider()
    _render_delete_product(composition, details)


def render_usage_locations(composition: ShellComposition) -> None:
    st.header("Stanowiska")
    locations = composition.list_usage_locations()
    if locations:
        st.dataframe(
            [
                {
                    "ID lokalizacji": location.location_id,
                    "Lokalizacja": location.location_name,
                    "Status": location.status.value,
                }
                for location in locations
            ],
            hide_index=True,
            use_container_width=True,
        )

    location_name = st.text_input("Nazwa lokalizacji")
    if st.button("Dodaj lokalizację"):
        try:
            if not location_name.strip():
                raise ValueError("Nazwa lokalizacji jest wymagana.")
            composition.create_usage_location(
                CreateUsageLocationInput(location_name=location_name.strip())
            )
            st.success("Lokalizacja utworzona.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))

    for location in locations:
        action = "Dezaktywuj" if location.status is UsageLocationStatus.ACTIVE else "Reaktywuj"
        if st.button(action, key=f"location-status-{location.location_id}"):
            try:
                composition.change_usage_location_status(
                    location.location_id,
                    active=location.status is UsageLocationStatus.INACTIVE,
                )
                st.success("Status lokalizacji zapisany.")
            except ShellInitializationError as error:
                st.error(str(error))
