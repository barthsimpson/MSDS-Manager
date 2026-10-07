"""Read contracts for physical review snapshots."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.domain.enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class ReviewPopulationItem:
    product_id: str
    location_id: str
    baseline_max_quantity: Decimal
    baseline_unit_id: str


@dataclass(frozen=True, slots=True)
class PhysicalReviewSummary:
    review_id: str
    review_date: date
    status: ReviewStatus
    created_at: datetime
    finalized_at: datetime | None


@dataclass(frozen=True, slots=True)
class PhysicalReviewItemRow:
    review_item_id: str
    product_id: str
    product_name: str
    location_id: str
    location_code: str
    location_name: str
    baseline_max_quantity: Decimal
    unit_code: str
    observed_quantity: Decimal | None

    @property
    def difference(self) -> Decimal | None:
        return (None if self.observed_quantity is None
                else self.observed_quantity - self.baseline_max_quantity)


@dataclass(frozen=True, slots=True)
class PhysicalReviewDetails:
    summary: PhysicalReviewSummary
    items: tuple[PhysicalReviewItemRow, ...]

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def observed_items(self) -> int:
        return sum(item.observed_quantity is not None for item in self.items)

    @property
    def unobserved_items(self) -> int:
        return self.total_items - self.observed_items


@dataclass(frozen=True, slots=True)
class LatestFinalReviewItem:
    product_id: str
    location_id: str
    review_date: date
    observed_quantity: Decimal | None
    difference: Decimal | None
