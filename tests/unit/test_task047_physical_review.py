"""Focused domain and mapping checks for TASK-047."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import Numeric, String, Uuid

from app.domain.enums import ReviewStatus
from app.domain.models import PhysicalReview, PhysicalReviewItem
from app.infrastructure.db.models import Base


def _id() -> str:
    return str(uuid4())


def test_domain_review_status_and_timestamp_pair() -> None:
    values = dict(
        review_id=_id(), review_date=date(2026, 10, 6),
        created_at=datetime.now(timezone.utc),
    )
    assert PhysicalReview(**values, status=ReviewStatus.DRAFT).finalized_at is None
    assert PhysicalReview(
        **values, status=ReviewStatus.FINAL,
        finalized_at=datetime.now(timezone.utc),
    ).status is ReviewStatus.FINAL
    with pytest.raises(ValueError):
        PhysicalReview(**values, status=ReviewStatus.FINAL)
    with pytest.raises(ValueError):
        PhysicalReview(
            **values, status=ReviewStatus.DRAFT,
            finalized_at=datetime.now(timezone.utc),
        )


def test_domain_item_preserves_null_and_zero_and_rejects_negative() -> None:
    values = dict(
        review_item_id=_id(), review_id=_id(), product_id="product-1",
        location_id="location-1", baseline_max_quantity=Decimal("0"),
        baseline_unit_id=_id(),
    )
    assert PhysicalReviewItem(**values).observed_quantity is None
    assert PhysicalReviewItem(**values, observed_quantity=Decimal("0")).observed_quantity == 0
    with pytest.raises(ValueError):
        PhysicalReviewItem(**values, observed_quantity=Decimal("-1"))
    with pytest.raises(ValueError):
        PhysicalReviewItem(**{**values, "baseline_max_quantity": Decimal("-1")})


def test_mapping_uses_existing_fk_and_quantity_types() -> None:
    reviews = Base.metadata.tables["physical_reviews"]
    items = Base.metadata.tables["physical_review_items"]
    usage = Base.metadata.tables["product_usage_locations"]
    assert {"review_id", "review_date", "status", "created_at", "finalized_at"} == set(reviews.c.keys())
    assert set(items.c.keys()) == {
        "review_item_id", "review_id", "product_id", "location_id",
        "baseline_max_quantity", "baseline_unit_id", "observed_quantity",
    }
    assert isinstance(items.c.product_id.type, String)
    assert isinstance(items.c.location_id.type, String)
    assert isinstance(items.c.baseline_unit_id.type, Uuid)
    assert isinstance(items.c.baseline_max_quantity.type, Numeric)
    assert items.c.baseline_max_quantity.type.precision == usage.c.peak_quantity_value.type.precision
    assert items.c.baseline_max_quantity.type.scale == usage.c.peak_quantity_value.type.scale
    assert items.c.observed_quantity.type.precision == usage.c.peak_quantity_value.type.precision
    assert items.c.observed_quantity.type.scale == usage.c.peak_quantity_value.type.scale
    assert "uq_physical_reviews_single_draft" in {index.name for index in reviews.indexes}
