"""Application boundary for bounded analytics queries and safe availability."""

from typing import Protocol

from app.application.dto.analytics import (
    AnalyticsFileAvailability, AnalyticsFilters, ProductAnalyticsFact,
    ProductLocationAnalyticsRow, SdsTrendPoint,
)


class AnalyticsReadPort(Protocol):
    def list_product_facts(self, filters: AnalyticsFilters) -> list[ProductAnalyticsFact]: ...
    def get_active_location_count(self, filters: AnalyticsFilters, product_ids: tuple[str, ...]) -> int: ...
    def get_sds_trend(self, product_ids: tuple[str, ...], filters: AnalyticsFilters) -> list[SdsTrendPoint]: ...
    def list_product_location_rows(self, filters: AnalyticsFilters) -> list[ProductLocationAnalyticsRow]: ...


class AnalyticsFileAvailabilityPort(Protocol):
    def sds_availability(self, relative_path: str) -> AnalyticsFileAvailability: ...
    def evidence_availability(self, relative_path: str) -> AnalyticsFileAvailability: ...
