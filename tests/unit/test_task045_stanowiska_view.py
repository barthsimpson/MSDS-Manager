"""Stanowiska row controls with application use cases and no database writes."""

from streamlit.testing.v1 import AppTest

from app.application.dto import CreateUsageLocationInput
from app.application.use_cases import (
    CreateUsageLocation,
    DeactivateUsageLocation,
    ReactivateUsageLocation,
)
from app.domain.enums import UsageLocationStatus
from app.domain.models import UsageLocation


class MemoryLocations:
    def __init__(self, *rows: UsageLocation) -> None:
        self.rows = {row.location_id: row for row in rows}
        self.status_updates: list[tuple[str, UsageLocationStatus]] = []

    def list_all(self) -> list[UsageLocation]:
        return list(self.rows.values())

    def get_by_id(self, location_id: str) -> UsageLocation | None:
        return self.rows.get(location_id)

    def get_by_code(self, location_code: str) -> UsageLocation | None:
        return next((row for row in self.rows.values()
                     if row.location_code == location_code), None)

    def add(self, location: UsageLocation) -> None:
        self.rows[location.location_id] = location

    def update_status(self, location: UsageLocation) -> None:
        self.rows[location.location_id] = location
        self.status_updates.append((location.location_id, location.status))


class Composition:
    def __init__(self, *rows: UsageLocation) -> None:
        self.repository = MemoryLocations(*rows)

    def list_usage_locations(self) -> list[UsageLocation]:
        return self.repository.list_all()

    def change_usage_location_status(self, location_id: str, active: bool) -> None:
        use_case = ReactivateUsageLocation if active else DeactivateUsageLocation
        use_case(self.repository).execute(location_id)

    def create_usage_location(self, data: CreateUsageLocationInput) -> None:
        CreateUsageLocation(
            self.repository, id_factory=lambda: f"new-{len(self.repository.rows)}"
        ).execute(data)


def _app(composition: Composition) -> AppTest:
    def render(current_composition):
        from app.presentation.streamlit.product_registry import render_usage_locations

        render_usage_locations(current_composition)

    return AppTest.from_function(
        render, args=(composition,), default_timeout=10
    ).run()


def test_rows_show_codes_and_lifecycle_buttons_target_correct_rows() -> None:
    composition = Composition(
        UsageLocation("uuid-active", "Magazyn", UsageLocationStatus.ACTIVE, "MZT"),
        UsageLocation("uuid-inactive", "Warsztat", UsageLocationStatus.INACTIVE, "UTR"),
    )
    app = _app(composition)

    assert app.exception == []
    assert len(app.dataframe) == 0
    visible = " ".join(str(item.value) for item in (*app.markdown, *app.caption))
    assert all(label in visible for label in ("Symbol", "Lokalizacja", "Status", "Akcja", "MZT", "UTR"))
    assert "uuid-active" not in visible and "uuid-inactive" not in visible
    assert app.button(key="location-status-uuid-active").label == "Dezaktywuj"
    assert app.button(key="location-status-uuid-inactive").label == "Reaktywuj"

    app.button(key="location-status-uuid-inactive").click().run()
    assert composition.repository.status_updates == [("uuid-inactive", UsageLocationStatus.ACTIVE)]
    assert composition.repository.rows["uuid-active"].status is UsageLocationStatus.ACTIVE
    app.button(key="location-status-uuid-active").click().run()
    assert composition.repository.status_updates[-1] == ("uuid-active", UsageLocationStatus.INACTIVE)


def test_new_location_requires_valid_unique_code() -> None:
    composition = Composition(
        UsageLocation("uuid-coded", "Warsztat", location_code="UTR"),
    )
    app = _app(composition)

    next(item for item in app.text_input if item.label == "Nazwa lokalizacji").set_value("Nowa").run()
    next(item for item in app.button if item.label == "Dodaj lokalizację").click().run()
    assert app.error and "location_code" in app.error[0].value
    assert len(composition.repository.rows) == 1

    next(item for item in app.text_input if item.label == "Symbol lokalizacji").set_value("bad code").run()
    next(item for item in app.button if item.label == "Dodaj lokalizację").click().run()
    assert app.error and "location_code" in app.error[0].value
    assert len(composition.repository.rows) == 1

    next(item for item in app.text_input if item.label == "Symbol lokalizacji").set_value("utr").run()
    next(item for item in app.button if item.label == "Dodaj lokalizację").click().run()
    assert app.error and "already exists" in app.error[0].value
    assert len(composition.repository.rows) == 1

    next(item for item in app.text_input if item.label == "Symbol lokalizacji").set_value("reg").run()
    next(item for item in app.button if item.label == "Dodaj lokalizację").click().run()
    assert any(row.location_name == "Nowa" and row.location_code == "REG"
               for row in composition.repository.rows.values())
