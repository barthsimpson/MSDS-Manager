"""Physical review lifecycle and read use cases."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.application.dto.physical_review import (
    LatestFinalReviewItem, PhysicalReviewDetails, PhysicalReviewSummary,
)
from app.application.ports.physical_review import PhysicalReviewPort
from app.domain.enums import ReviewStatus
from app.domain.models import PhysicalReview, PhysicalReviewItem


class ReviewDraftAlreadyExistsError(ValueError):
    pass


class EmptyReviewPopulationError(ValueError):
    pass


class ReviewNotFoundError(ValueError):
    pass


class ReviewAlreadyFinalError(ValueError):
    pass


class FinalReviewImmutableError(ValueError):
    pass


class InvalidObservedQuantityError(ValueError):
    pass


class CreatePhysicalReview:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self, review_date: date) -> str:
        if not isinstance(review_date, date) or isinstance(review_date, datetime):
            raise TypeError("review_date must be a date")
        if self._repository.get_active_draft() is not None:
            raise ReviewDraftAlreadyExistsError("A DRAFT already exists")
        review_id = str(uuid4())
        self._repository.add_draft_header(PhysicalReview(
            review_id=review_id, review_date=review_date, status=ReviewStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
        ))
        population = self._repository.list_population()
        if not population:
            raise EmptyReviewPopulationError("No active-location assignments to review")
        self._repository.add_items([
            PhysicalReviewItem(
                review_item_id=str(uuid4()), review_id=review_id,
                product_id=row.product_id, location_id=row.location_id,
                baseline_max_quantity=row.baseline_max_quantity,
                baseline_unit_id=row.baseline_unit_id,
            )
            for row in population
        ])
        return review_id


class UpdateReviewObservedQuantity:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self, review_item_id: str, observed_quantity: Decimal | None) -> None:
        if (observed_quantity is not None and
                (not isinstance(observed_quantity, Decimal)
                 or not observed_quantity.is_finite() or observed_quantity < 0)):
            raise InvalidObservedQuantityError("Observed quantity must be a nonnegative Decimal or None")
        self._repository.update_observed_quantity(review_item_id, observed_quantity)


class DiscardPhysicalReviewDraft:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self, review_id: str) -> None:
        self._repository.discard_draft(review_id)


class FinalizePhysicalReview:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self, review_id: str) -> None:
        self._repository.finalize_draft(review_id)


class GetActivePhysicalReviewDraft:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self) -> PhysicalReviewSummary | None:
        return self._repository.get_active_draft()


class GetPhysicalReview:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self, review_id: str) -> PhysicalReviewDetails:
        result = self._repository.get_review(review_id)
        if result is None:
            raise ReviewNotFoundError("Review not found")
        return result


class ListPhysicalReviews:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self) -> list[PhysicalReviewSummary]:
        return self._repository.list_reviews()


class GetLatestFinalReviewItemsForAnalytics:
    def __init__(self, repository: PhysicalReviewPort) -> None:
        self._repository = repository

    def execute(self) -> list[LatestFinalReviewItem]:
        return self._repository.get_latest_final_items_for_analytics()
