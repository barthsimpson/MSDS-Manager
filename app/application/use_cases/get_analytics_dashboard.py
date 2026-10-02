"""Compose current-state analytics from bounded reads and runtime file checks."""

from collections import defaultdict
from dataclasses import replace

from app.application.dto.analytics import (
    AnalyticsBhpStatus, AnalyticsDashboardDto, AnalyticsFileAvailability,
    AnalyticsFilters, AnalyticsKpiDto, AttentionSummaryDto,
    BhpStatusDistributionDto, ManufacturerSummaryRow, ProductAnalyticsFact,
)
from app.application.ports.analytics_read import AnalyticsFileAvailabilityPort, AnalyticsReadPort
from app.domain.enums import ProductUsageStatus


def validate_analytics_filters(filters: AnalyticsFilters) -> None:
    if filters.trend_date_from > filters.trend_date_to:
        raise ValueError("trend_date_from must be on or before trend_date_to")
    if filters.bhp_status == AnalyticsBhpStatus.NOT_APPLICABLE_NO_CURRENT_SDS:
        raise ValueError("NOT_APPLICABLE_NO_CURRENT_SDS is not a selectable BHP filter")


def _attention_reasons(fact: ProductAnalyticsFact) -> tuple[str, ...]:
    reasons = []
    if not fact.has_current_sds:
        reasons.append("NO_CURRENT_SDS")
    if fact.bhp_category == AnalyticsBhpStatus.NO_DECISION:
        reasons.append("NO_BHP_DECISION")
    if (fact.usage_status in (ProductUsageStatus.ACTIVE, ProductUsageStatus.PENDING_APPROVAL)
            and not fact.has_active_location):
        reasons.append("NO_ACTIVE_LOCATION")
    if (fact.current_sds_availability == AnalyticsFileAvailability.MISSING
            or fact.current_evidence_availability == AnalyticsFileAvailability.MISSING):
        reasons.append("MISSING_SOURCE_FILE")
    return tuple(reasons)


class GetAnalyticsDashboard:
    def __init__(self, query: AnalyticsReadPort, files: AnalyticsFileAvailabilityPort) -> None:
        self._query = query
        self._files = files

    def execute(self, filters: AnalyticsFilters) -> AnalyticsDashboardDto:
        validate_analytics_filters(filters)
        facts = []
        for fact in self._query.list_product_facts(filters):
            facts.append(replace(
                fact,
                current_sds_availability=(
                    self._files.sds_availability(fact.current_sds_relative_path)
                    if fact.current_sds_id and fact.current_sds_relative_path
                    else AnalyticsFileAvailability.CHECK_FAILED if fact.current_sds_id else None
                ),
                current_evidence_availability=(
                    self._files.evidence_availability(fact.current_evidence_relative_path)
                    if fact.current_bhp_decision_id and fact.current_evidence_relative_path
                    else AnalyticsFileAvailability.CHECK_FAILED if fact.current_bhp_decision_id else None
                ),
            ))
        ids = tuple(fact.product_id for fact in facts)
        if len(ids) != len(set(ids)):
            raise ValueError("Analytics read returned duplicate PRODUCT facts")

        by_reason: dict[str, list[str]] = defaultdict(list)
        manufacturers: dict[str, list[ProductAnalyticsFact]] = defaultdict(list)
        for fact in facts:
            manufacturers[fact.manufacturer_id].append(fact)
            for reason in _attention_reasons(fact):
                by_reason[reason].append(fact.product_id)
        attention_ids = {product_id for values in by_reason.values() for product_id in values}
        attention = AttentionSummaryDto(
            no_current_sds_count=len(by_reason["NO_CURRENT_SDS"]),
            no_bhp_decision_count=len(by_reason["NO_BHP_DECISION"]),
            no_active_location_count=len(by_reason["NO_ACTIVE_LOCATION"]),
            missing_source_file_count=len(by_reason["MISSING_SOURCE_FILE"]),
            affected_product_ids_by_reason={key: tuple(values) for key, values in by_reason.items()},
        )
        kpi = AnalyticsKpiDto(
            products_total=len(facts),
            current_sds_count=sum(f.has_current_sds for f in facts),
            bhp_approved_count=sum(f.bhp_category == AnalyticsBhpStatus.APPROVED for f in facts),
            attention_products_count=len(attention_ids),
            active_locations_count=self._query.get_active_location_count(filters, ids),
        )
        bhp = BhpStatusDistributionDto(
            approved=sum(f.bhp_category == AnalyticsBhpStatus.APPROVED for f in facts),
            rejected=sum(f.bhp_category == AnalyticsBhpStatus.REJECTED for f in facts),
            no_decision=sum(f.bhp_category == AnalyticsBhpStatus.NO_DECISION for f in facts),
        )
        summaries = []
        for manufacturer_id, members in manufacturers.items():
            registered = [f.latest_sds_registered_at for f in members
                          if f.latest_sds_registered_at is not None]
            summaries.append(ManufacturerSummaryRow(
                manufacturer_id=manufacturer_id,
                manufacturer_name=members[0].manufacturer_name,
                products_count=len(members),
                current_sds_count=sum(f.has_current_sds for f in members),
                bhp_approved_count=sum(f.bhp_category == AnalyticsBhpStatus.APPROVED for f in members),
                attention_products_count=sum(f.product_id in attention_ids for f in members),
                latest_sds_registered_at=max(registered) if registered else None,
            ))
        summaries.sort(key=lambda row: (row.manufacturer_name, row.manufacturer_id))
        return AnalyticsDashboardDto(
            product_facts=tuple(facts), kpi=kpi, bhp_status=bhp,
            sds_trend=tuple(self._query.get_sds_trend(ids, filters)),
            manufacturer_summary=tuple(summaries), attention=attention,
        )
