"""Streamlit rendering for the Product Registry."""

from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st

from app.application.dto import (
    AddSdsRevisionInput,
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    ProductUsageLocationDetails,
    UpdateProductAdministrativeDataInput,
    UpdateProductIdentityInput,
    UpdateProductUsageLocationInput,
)
from app.domain.enums import UsageLocationStatus
from app.presentation.streamlit.composition import (
    ShellComposition,
    ShellInitializationError,
)


MISSING_VALUE = "Brak danych"


def _optional_text(value: str | Decimal | None) -> str:
    return MISSING_VALUE if value is None else str(value)


def _registry_row(product: ProductListItem) -> dict[str, str]:
    return {
        "ID produktu": product.product_id,
        "Produkt": product.product_name,
        "Kod producenta": product.manufacturer_product_code,
        "Producent": product.manufacturer_name,
        "Status": product.usage_status.value,
        "Opis użycia": product.use_description,
        "Ograniczenia": product.use_restriction,
        "Typ odpadu": _optional_text(product.waste_type),
        "Kod odpadu": _optional_text(product.waste_code),
    }


def _location_row(location: ProductUsageLocationDetails) -> dict[str, str]:
    return {
        "Lokalizacja": location.location_name,
        "Status lokalizacji": location.location_status.value,
        "Peak wartość": str(location.peak_quantity_value),
        "Peak jednostka": location.peak_quantity_unit,
        "Monthly wartość": _optional_text(location.monthly_consumption_value),
        "Monthly jednostka": _optional_text(location.monthly_consumption_unit),
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


def _render_details(composition, details: ProductDetails) -> None:
    st.subheader("Szczegóły produktu")
    st.text(f"Nazwa produktu: {details.product_name}")
    st.text(f"Kod producenta: {details.manufacturer_product_code}")
    st.text(f"Producent: {details.manufacturer_name}")
    st.text(f"Status użytkowania: {details.usage_status.value}")
    _render_identity_edit(composition, details)
    _render_delete_product(composition, details)

    st.subheader("Dane administracyjne")
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

    st.text(f"Opis użycia: {details.use_description}")
    st.text(f"Ograniczenia użycia: {details.use_restriction}")
    st.text(f"Typ odpadu: {_optional_text(details.waste_type)}")
    st.text(f"Kod odpadu: {_optional_text(details.waste_code)}")

    _render_revision(composition, details)

    st.subheader("Miejsca stosowania")
    if not details.usage_locations:
        st.info("Brak przypisanych miejsc stosowania.")
        return
    st.dataframe(
        [_location_row(location) for location in details.usage_locations],
        hide_index=True,
        use_container_width=True,
    )


def _decimal(value: str, label: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: podaj poprawną liczbę.") from None


def _quantity_form(composition, details: ProductDetails, location) -> None:
    peak_value = st.text_input("Peak quantity", str(location.peak_quantity_value), key=f"peak-{location.location_id}")
    peak_unit = st.text_input("Jednostka peak", location.peak_quantity_unit, key=f"peak-unit-{location.location_id}")
    monthly_enabled = st.checkbox("Podaj miesięczne zużycie", value=location.monthly_consumption_value is not None, key=f"monthly-enabled-{location.location_id}")
    monthly_value = st.text_input("Monthly consumption", _optional_text(location.monthly_consumption_value) if monthly_enabled else "", key=f"monthly-{location.location_id}")
    monthly_unit = st.text_input("Jednostka monthly", _optional_text(location.monthly_consumption_unit) if monthly_enabled else "", key=f"monthly-unit-{location.location_id}")
    if st.button("Zapisz ilości", key=f"quantity-{details.product_id}-{location.location_id}"):
        try:
            monthly_data = ((_decimal(monthly_value, "Monthly consumption"), monthly_unit) if monthly_enabled else (None, None))
            if monthly_data[0] is not None and not monthly_data[1].strip():
                raise ValueError("Jednostka monthly jest wymagana.")
            composition.update_product_usage_location(
                UpdateProductUsageLocationInput(
                    product_id=details.product_id,
                    location_id=location.location_id,
                    peak_quantity_value=_decimal(peak_value, "Peak quantity"),
                    peak_quantity_unit=peak_unit,
                    monthly_consumption_value=monthly_data[0],
                    monthly_consumption_unit=monthly_data[1] if monthly_data[1] else None,
                )
            )
            st.success("Ilości zapisane.")
        except (ShellInitializationError, ValueError) as error:
            st.error(str(error))


def _render_product_operations(composition, details: ProductDetails) -> None:
    for location in details.usage_locations:
        _quantity_form(composition, details, location)

    locations = composition.list_usage_locations()
    available = [
        location
        for location in locations
        if location.status is UsageLocationStatus.ACTIVE
        and location.location_id not in {item.location_id for item in details.usage_locations}
    ]
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
        peak_value = st.text_input("Peak quantity nowego przypisania", "0")
        peak_unit = st.text_input("Jednostka peak nowego przypisania", "")
        if st.button("Przypisz lokalizację", key=f"assign-{details.product_id}"):
            try:
                composition.assign_product_usage_location(
                    AssignProductUsageLocationInput(
                        product_id=details.product_id,
                        location_id=location_id,
                        peak_quantity_value=_decimal(peak_value, "Peak quantity"),
                        peak_quantity_unit=peak_unit,
                    )
                )
                st.success("Lokalizacja przypisana.")
            except (ShellInitializationError, ValueError) as error:
                st.error(str(error))


def _render_revision(composition, details: ProductDetails) -> None:
    active_key = f"revision-active-{details.product_id}"
    if st.button("Dodaj nową rewizję SDS", key=f"add-revision-{details.product_id}"):
        st.session_state[active_key] = True
    if not st.session_state.get(active_key):
        return

    st.subheader("Nowa rewizja SDS")
    files = composition.list_sds_files()
    if not files:
        st.info("Brak plików PDF w SDS_ROOT_PATH.")
        return
    selected = st.selectbox(
        "Plik nowej rewizji SDS",
        files,
        key=f"revision-file-{details.product_id}",
    )
    revision = st.text_input(
        "Rewizja nowego SDS", key=f"revision-value-{details.product_id}"
    )
    has_issue_date = st.checkbox(
        "Podaj datę wydania nowej rewizji",
        key=f"revision-has-date-{details.product_id}",
    )
    issue_date = (
        st.date_input(
            "Data wydania nowej rewizji",
            date.today(),
            key=f"revision-date-{details.product_id}",
        )
        if has_issue_date
        else None
    )
    save, cancel = st.columns(2)
    if save.button("Zapisz nową rewizję", key=f"save-revision-{details.product_id}"):
        try:
            sds_id = composition.accept_sds_revision(
                AddSdsRevisionInput(
                    product_id=details.product_id,
                    source_relative_path=selected,
                    revision=revision or None,
                    issue_date=issue_date,
                )
            )
            st.session_state.pop(active_key, None)
            st.success(
                f"Nowa rewizja została zapisana. Produkt oczekuje na decyzję BHP. ({sds_id})"
            )
        except (ShellInitializationError, ValueError, OSError) as error:
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

    st.dataframe(
        [_registry_row(product) for product in products],
        hide_index=True,
        use_container_width=True,
    )
    labels = {
        product.product_id: (
            f"{product.product_name} — {product.manufacturer_product_code} "
            f"({product.manufacturer_name})"
        )
        for product in products
    }
    selected_product_id = st.selectbox(
        "Wybierz produkt",
        [product.product_id for product in products],
        format_func=labels.__getitem__,
    )
    try:
        details = composition.get_product_details(selected_product_id)
    except ShellInitializationError as error:
        st.error(str(error))
        return
    _render_details(composition, details)
    _render_product_operations(composition, details)


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
