"""Session-scoped persistence for physical review snapshots."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.application.dto.physical_review import (
    LatestFinalReviewItem, PhysicalReviewDetails, PhysicalReviewItemRow,
    PhysicalReviewSummary, ReviewPopulationItem,
)
from app.application.use_cases.physical_review import (
    FinalReviewImmutableError, ReviewAlreadyFinalError, ReviewNotFoundError,
)
from app.domain.enums import ReviewStatus, UsageLocationStatus
from app.domain.models import PhysicalReview, PhysicalReviewItem
from app.infrastructure.db.models import (
    PhysicalReviewItemModel, PhysicalReviewModel, ProductModel,
    ProductUsageLocationModel, UnitOfMeasureModel, UsageLocationModel,
)


def latest_final_review_items_subquery():
    """Rank every FINAL item before filtering so a latest NULL stays NULL."""
    ranked = select(
        PhysicalReviewItemModel.product_id.label("product_id"),
        PhysicalReviewItemModel.location_id.label("location_id"),
        PhysicalReviewItemModel.observed_quantity.label("observed_quantity"),
        PhysicalReviewItemModel.baseline_max_quantity.label("baseline_max_quantity"),
        PhysicalReviewItemModel.baseline_unit_id.label("baseline_unit_id"),
        PhysicalReviewModel.review_date.label("review_date"),
        func.row_number().over(
            partition_by=(PhysicalReviewItemModel.product_id,
                          PhysicalReviewItemModel.location_id),
            order_by=(PhysicalReviewModel.review_date.desc(),
                      PhysicalReviewModel.finalized_at.desc(),
                      PhysicalReviewModel.review_id.desc()),
        ).label("rank"),
    ).join(
        PhysicalReviewModel,
        PhysicalReviewModel.review_id == PhysicalReviewItemModel.review_id,
    ).where(PhysicalReviewModel.status == ReviewStatus.FINAL.value).subquery()
    return select(ranked).where(ranked.c.rank == 1).subquery()


def _summary(model: PhysicalReviewModel) -> PhysicalReviewSummary:
    return PhysicalReviewSummary(
        review_id=model.review_id, review_date=model.review_date,
        status=ReviewStatus(model.status), created_at=model.created_at,
        finalized_at=model.finalized_at,
    )


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

    def get_active_draft(self) -> PhysicalReviewSummary | None:
        model = self._session.scalar(select(PhysicalReviewModel).where(
            PhysicalReviewModel.status == ReviewStatus.DRAFT.value
        ))
        return _summary(model) if model is not None else None

    def list_population(self) -> list[ReviewPopulationItem]:
        rows = self._session.execute(select(
            ProductUsageLocationModel.product_id,
            ProductUsageLocationModel.location_id,
            ProductUsageLocationModel.peak_quantity_value,
            ProductUsageLocationModel.peak_quantity_unit_id,
        ).join(
            UsageLocationModel,
            UsageLocationModel.location_id == ProductUsageLocationModel.location_id,
        ).where(
            UsageLocationModel.status == UsageLocationStatus.ACTIVE
        ).order_by(
            ProductUsageLocationModel.product_id,
            ProductUsageLocationModel.location_id,
        )).all()
        return [ReviewPopulationItem(
            product_id=row.product_id, location_id=row.location_id,
            baseline_max_quantity=row.peak_quantity_value,
            baseline_unit_id=row.peak_quantity_unit_id,
        ) for row in rows]

    def add_draft_header(self, review: PhysicalReview) -> None:
        if review.status is not ReviewStatus.DRAFT:
            raise ValueError("Only DRAFT can be created")
        self.add_snapshot(review, [])
        self._session.flush()  # claim the single-DRAFT unique index before population read

    def add_items(self, items: list[PhysicalReviewItem]) -> None:
        self._session.add_all([
            PhysicalReviewItemModel(
                review_item_id=item.review_item_id, review_id=item.review_id,
                product_id=item.product_id, location_id=item.location_id,
                baseline_max_quantity=item.baseline_max_quantity,
                baseline_unit_id=item.baseline_unit_id,
                observed_quantity=item.observed_quantity,
            ) for item in items
        ])

    def list_reviews(self) -> list[PhysicalReviewSummary]:
        models = self._session.scalars(select(PhysicalReviewModel).order_by(
            PhysicalReviewModel.review_date.desc(),
            PhysicalReviewModel.finalized_at.desc().nulls_first(),
            PhysicalReviewModel.created_at.desc(),
        )).all()
        return [_summary(model) for model in models]

    def get_review(self, review_id: str) -> PhysicalReviewDetails | None:
        model = self._session.get(PhysicalReviewModel, review_id)
        if model is None:
            return None
        rows = self._session.execute(select(
            PhysicalReviewItemModel.review_item_id,
            PhysicalReviewItemModel.product_id,
            ProductModel.product_name,
            PhysicalReviewItemModel.location_id,
            UsageLocationModel.location_code,
            UsageLocationModel.location_name,
            PhysicalReviewItemModel.baseline_max_quantity,
            UnitOfMeasureModel.code.label("unit_code"),
            PhysicalReviewItemModel.observed_quantity,
        ).join(ProductModel,
               ProductModel.product_id == PhysicalReviewItemModel.product_id)
         .join(UsageLocationModel,
               UsageLocationModel.location_id == PhysicalReviewItemModel.location_id)
         .join(UnitOfMeasureModel,
               UnitOfMeasureModel.unit_id == PhysicalReviewItemModel.baseline_unit_id)
         .where(PhysicalReviewItemModel.review_id == review_id)
         .order_by(ProductModel.product_name, UsageLocationModel.location_code,
                   PhysicalReviewItemModel.review_item_id)).mappings().all()
        items = tuple(PhysicalReviewItemRow(**row) for row in rows)
        return PhysicalReviewDetails(_summary(model), items)

    def _locked_review(self, review_id: str) -> PhysicalReviewModel:
        model = self._session.scalar(select(PhysicalReviewModel).where(
            PhysicalReviewModel.review_id == review_id
        ).with_for_update())
        if model is None:
            raise ReviewNotFoundError("Review not found")
        return model

    def update_observed_quantity(self, review_item_id: str, value: Decimal | None) -> None:
        review_id = self._session.scalar(select(PhysicalReviewItemModel.review_id).where(
            PhysicalReviewItemModel.review_item_id == review_item_id
        ))
        if review_id is None:
            raise ReviewNotFoundError("Review item not found")
        review = self._locked_review(review_id)
        if review.status != ReviewStatus.DRAFT.value:
            raise FinalReviewImmutableError("FINAL review is immutable")
        result = self._session.execute(update(PhysicalReviewItemModel).where(
            PhysicalReviewItemModel.review_item_id == review_item_id,
            PhysicalReviewItemModel.review_id == review_id,
        ).values(observed_quantity=value))
        if result.rowcount != 1:
            raise ReviewNotFoundError("Review item not found")

    def discard_draft(self, review_id: str) -> None:
        review = self._locked_review(review_id)
        if review.status != ReviewStatus.DRAFT.value:
            raise FinalReviewImmutableError("FINAL review cannot be discarded")
        self._session.execute(delete(PhysicalReviewItemModel).where(
            PhysicalReviewItemModel.review_id == review_id
        ))
        self._session.delete(review)

    def finalize_draft(self, review_id: str) -> None:
        review = self._locked_review(review_id)
        if review.status != ReviewStatus.DRAFT.value:
            raise ReviewAlreadyFinalError("Review already FINAL")
        review.status = ReviewStatus.FINAL.value
        review.finalized_at = datetime.now(timezone.utc)

    def get_latest_final_items_for_analytics(self) -> list[LatestFinalReviewItem]:
        latest = latest_final_review_items_subquery()
        rows = self._session.execute(select(latest)).mappings().all()
        return [LatestFinalReviewItem(
            product_id=row["product_id"], location_id=row["location_id"],
            review_date=row["review_date"],
            observed_quantity=row["observed_quantity"],
            difference=(None if row["observed_quantity"] is None else
                        row["observed_quantity"] - row["baseline_max_quantity"]),
        ) for row in rows]
