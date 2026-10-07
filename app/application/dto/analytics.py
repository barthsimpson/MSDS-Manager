"""Read-only analytics contracts. These categories are not Domain statuses."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.enums import ProductUsageStatus


class AnalyticsSdsStatus(StrEnum):
    CURRENT_PRESENT = "CURRENT_PRESENT"
    CURRENT_MISSING = "CURRENT_MISSING"


class AnalyticsBhpStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NO_DECISION = "NO_DECISION"
    NOT_APPLICABLE_NO_CURRENT_SDS = "NOT_APPLICABLE_NO_CURRENT_SDS"


class AnalyticsFileAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    CHECK_FAILED = "CHECK_FAILED"


@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    trend_date_from: date
    trend_date_to: date
    manufacturer_id: UUID | None = None
    sds_status: AnalyticsSdsStatus | None = None
    bhp_status: AnalyticsBhpStatus | None = None
    usage_location_id: UUID | None = None
    include_no_active_location: bool = False


@dataclass(frozen=True, slots=True)
class ProductAnalyticsFact:
    product_id: str
    product_name: str
    usage_status: ProductUsageStatus
    manufacturer_id: str
    manufacturer_name: str
    has_current_sds: bool
    current_sds_id: str | None
    current_sds_original_filename: str | None
    current_sds_relative_path: str | None
    current_sds_registered_at: datetime | None
    bhp_category: AnalyticsBhpStatus
    current_bhp_decision_id: str | None
    current_evidence_id: str | None
    current_evidence_original_filename: str | None
    current_evidence_relative_path: str | None
    active_location_count: int
    has_active_location: bool
    latest_sds_registered_at: datetime | None
    current_sds_availability: AnalyticsFileAvailability | None = None
    current_evidence_availability: AnalyticsFileAvailability | None = None


@dataclass(frozen=True, slots=True)
class AnalyticsKpiDto:
    products_total: int
    current_sds_count: int
    bhp_approved_count: int
    attention_products_count: int
    active_locations_count: int


@dataclass(frozen=True, slots=True)
class BhpStatusDistributionDto:
    approved: int
    rejected: int
    no_decision: int


@dataclass(frozen=True, slots=True)
class SdsTrendPoint:
    period_start: date
    new_sds_count: int
    updated_sds_count: int


@dataclass(frozen=True, slots=True)
class ManufacturerSummaryRow:
    manufacturer_id: str
    manufacturer_name: str
    products_count: int
    current_sds_count: int
    bhp_approved_count: int
    attention_products_count: int
    latest_sds_registered_at: datetime | None


@dataclass(frozen=True, slots=True)
class ProductLocationAnalyticsRow:
    product_id: str
    product_name: str
    manufacturer_name: str
    location_id: str | None
    location_name: str | None
    peak_quantity_value: Decimal | None
    peak_quantity_unit_code: str | None
    monthly_consumption_value: Decimal | None
    monthly_consumption_unit_code: str | None
    product_usage_status: ProductUsageStatus
    current_sds_revision: str | None
    current_sds_issue_date: date | None
    bhp_category: AnalyticsBhpStatus
    review_observed_quantity: Decimal | None = None
    review_difference: Decimal | None = None
    review_unit_code: str | None = None


@dataclass(frozen=True, slots=True)
class AttentionSummaryDto:
    no_current_sds_count: int
    no_bhp_decision_count: int
    no_active_location_count: int
    missing_source_file_count: int
    affected_product_ids_by_reason: dict[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class AnalyticsDashboardDto:
    product_facts: tuple[ProductAnalyticsFact, ...]
    kpi: AnalyticsKpiDto
    bhp_status: BhpStatusDistributionDto
    sds_trend: tuple[SdsTrendPoint, ...]
    manufacturer_summary: tuple[ManufacturerSummaryRow, ...]
    attention: AttentionSummaryDto
