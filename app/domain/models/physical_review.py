"""Physical review snapshot domain values."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.enums import ReviewStatus


def _require_uuid(value: str, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a UUID string.")
    try:
        UUID(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a UUID string.") from error


@dataclass(frozen=True, slots=True)
class PhysicalReview:
    review_id: str
    review_date: date
    status: ReviewStatus
    created_at: datetime
    finalized_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_uuid(self.review_id, "review_id")
        if not isinstance(self.review_date, date) or isinstance(self.review_date, datetime):
            raise TypeError("review_date must be a date.")
        if not isinstance(self.status, ReviewStatus):
            raise ValueError("status is invalid.")
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware.")
        if self.status is ReviewStatus.DRAFT and self.finalized_at is not None:
            raise ValueError("DRAFT cannot have finalized_at.")
        if self.status is ReviewStatus.FINAL and (
            not isinstance(self.finalized_at, datetime) or self.finalized_at.tzinfo is None
        ):
            raise ValueError("FINAL requires timezone-aware finalized_at.")


@dataclass(frozen=True, slots=True)
class PhysicalReviewItem:
    review_item_id: str
    review_id: str
    product_id: str
    location_id: str
    baseline_max_quantity: Decimal
    baseline_unit_id: str
    observed_quantity: Decimal | None = None

    def __post_init__(self) -> None:
        _require_uuid(self.review_item_id, "review_item_id")
        _require_uuid(self.review_id, "review_id")
        _require_uuid(self.baseline_unit_id, "baseline_unit_id")
        for name in ("product_id", "location_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} is required.")
        if not isinstance(self.baseline_max_quantity, Decimal):
            raise TypeError("baseline_max_quantity must be a Decimal.")
        if self.baseline_max_quantity < 0:
            raise ValueError("baseline_max_quantity cannot be negative.")
        if self.observed_quantity is not None:
            if not isinstance(self.observed_quantity, Decimal):
                raise TypeError("observed_quantity must be a Decimal or None.")
            if self.observed_quantity < 0:
                raise ValueError("observed_quantity cannot be negative.")
