"""Session-scoped persistence foundation for review snapshots.

The caller owns the existing transaction boundary. Lifecycle writes are reserved
for the later application task.
"""

from sqlalchemy.orm import Session

from app.domain.models import PhysicalReview, PhysicalReviewItem
from app.infrastructure.db.models import PhysicalReviewItemModel, PhysicalReviewModel


class SqlAlchemyPhysicalReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_snapshot(
        self, review: PhysicalReview, items: list[PhysicalReviewItem]
    ) -> None:
        """Stage a header and its full supplied population in one session."""
        if any(item.review_id != review.review_id for item in items):
            raise ValueError("All items must belong to the review.")
        self._session.add(PhysicalReviewModel(
            review_id=review.review_id,
            review_date=review.review_date,
            status=review.status.value,
            created_at=review.created_at,
            finalized_at=review.finalized_at,
        ))
        self._session.add_all([
            PhysicalReviewItemModel(
                review_item_id=item.review_item_id,
                review_id=item.review_id,
                product_id=item.product_id,
                location_id=item.location_id,
                baseline_max_quantity=item.baseline_max_quantity,
                baseline_unit_id=item.baseline_unit_id,
                observed_quantity=item.observed_quantity,
            )
            for item in items
        ])
