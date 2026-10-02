"""Lazy read of the PRODUCT × active USAGE_LOCATION report."""

from app.application.dto.analytics import AnalyticsFilters, ProductLocationAnalyticsRow
from app.application.ports.analytics_read import AnalyticsReadPort
from app.application.use_cases.get_analytics_dashboard import validate_analytics_filters


class ListAnalyticsProductLocations:
    def __init__(self, query: AnalyticsReadPort) -> None:
        self._query = query

    def execute(self, filters: AnalyticsFilters) -> list[ProductLocationAnalyticsRow]:
        validate_analytics_filters(filters)
        return self._query.list_product_location_rows(filters)
