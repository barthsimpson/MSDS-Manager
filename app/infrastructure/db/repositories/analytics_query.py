"""Bounded PostgreSQL reads for the dynamic analytics model."""

from sqlalchemy import Date, String, and_, case, cast, distinct, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.application.dto.analytics import (
    AnalyticsBhpStatus, AnalyticsFilters, AnalyticsSdsStatus,
    ProductAnalyticsFact, ProductLocationAnalyticsRow, SdsTrendPoint,
)
from app.application.ports.analytics_read import AnalyticsReadPort
from app.domain.enums import DecisionRecordStatus, SdsDocumentStatus, UsageLocationStatus
from app.infrastructure.db.models import (
    BhpDecisionModel, DecisionEvidenceModel, ManufacturerModel, ProductModel,
    ProductUsageLocationModel, SdsDocumentModel, UnitOfMeasureModel,
    UsageLocationModel,
)
from app.infrastructure.db.repositories.physical_review import latest_final_review_items_subquery


class SqlAlchemyAnalyticsQuery(AnalyticsReadPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _base():
        active_locations = (
            select(
                ProductUsageLocationModel.product_id.label("product_id"),
                func.count(distinct(UsageLocationModel.location_id)).label("active_location_count"),
            )
            .join(UsageLocationModel, and_(
                UsageLocationModel.location_id == ProductUsageLocationModel.location_id,
                UsageLocationModel.status == UsageLocationStatus.ACTIVE,
            ))
            .group_by(ProductUsageLocationModel.product_id)
            .subquery()
        )
        latest_sds = (
            select(
                SdsDocumentModel.product_id.label("product_id"),
                func.max(SdsDocumentModel.registered_at).label("latest_sds_registered_at"),
            )
            .group_by(SdsDocumentModel.product_id)
            .subquery()
        )
        category = case(
            (SdsDocumentModel.sds_id.is_(None), AnalyticsBhpStatus.NOT_APPLICABLE_NO_CURRENT_SDS.value),
            (BhpDecisionModel.decision_id.is_(None), AnalyticsBhpStatus.NO_DECISION.value),
            else_=cast(BhpDecisionModel.decision_status, String),
        )
        return (
            select(
                ProductModel.product_id,
                ProductModel.product_name,
                ProductModel.usage_status,
                ProductModel.manufacturer_id,
                ManufacturerModel.manufacturer_name,
                SdsDocumentModel.sds_id.label("current_sds_id"),
                SdsDocumentModel.original_filename.label("current_sds_original_filename"),
                SdsDocumentModel.relative_path.label("current_sds_relative_path"),
                SdsDocumentModel.registered_at.label("current_sds_registered_at"),
                SdsDocumentModel.revision.label("current_sds_revision"),
                SdsDocumentModel.issue_date.label("current_sds_issue_date"),
                category.label("bhp_category"),
                BhpDecisionModel.decision_id.label("current_bhp_decision_id"),
                DecisionEvidenceModel.evidence_id.label("current_evidence_id"),
                DecisionEvidenceModel.original_filename.label("current_evidence_original_filename"),
                DecisionEvidenceModel.relative_path.label("current_evidence_relative_path"),
                func.coalesce(active_locations.c.active_location_count, 0).label("active_location_count"),
                latest_sds.c.latest_sds_registered_at,
            )
            .select_from(ProductModel)
            .join(ManufacturerModel, ManufacturerModel.manufacturer_id == ProductModel.manufacturer_id)
            .outerjoin(SdsDocumentModel, and_(
                SdsDocumentModel.product_id == ProductModel.product_id,
                SdsDocumentModel.document_status == SdsDocumentStatus.CURRENT,
            ))
            .outerjoin(BhpDecisionModel, and_(
                BhpDecisionModel.sds_id == SdsDocumentModel.sds_id,
                BhpDecisionModel.record_status == DecisionRecordStatus.CURRENT,
            ))
            .outerjoin(DecisionEvidenceModel,
                       DecisionEvidenceModel.evidence_id == BhpDecisionModel.evidence_id)
            .outerjoin(active_locations, active_locations.c.product_id == ProductModel.product_id)
            .outerjoin(latest_sds, latest_sds.c.product_id == ProductModel.product_id)
            .subquery()
        )

    @staticmethod
    def _scope(base, filters: AnalyticsFilters):
        conditions = []
        if filters.manufacturer_id is not None:
            conditions.append(base.c.manufacturer_id == str(filters.manufacturer_id))
        if filters.sds_status == AnalyticsSdsStatus.CURRENT_PRESENT:
            conditions.append(base.c.current_sds_id.is_not(None))
        elif filters.sds_status == AnalyticsSdsStatus.CURRENT_MISSING:
            conditions.append(base.c.current_sds_id.is_(None))
        if filters.bhp_status is not None:
            conditions.append(base.c.bhp_category == filters.bhp_status.value)
        if filters.usage_location_id is not None:
            matching_location = (
                select(ProductUsageLocationModel.product_id)
                .join(UsageLocationModel, and_(
                    UsageLocationModel.location_id == ProductUsageLocationModel.location_id,
                    UsageLocationModel.status == UsageLocationStatus.ACTIVE,
                ))
                .where(
                    ProductUsageLocationModel.product_id == base.c.product_id,
                    UsageLocationModel.location_id == str(filters.usage_location_id),
                )
                .exists()
            )
            conditions.append(or_(matching_location, base.c.active_location_count == 0)
                              if filters.include_no_active_location else matching_location)
        elif filters.include_no_active_location:
            conditions.append(base.c.active_location_count == 0)
        return conditions

    def list_product_facts(self, filters: AnalyticsFilters) -> list[ProductAnalyticsFact]:
        base = self._base()
        statement = select(base).where(*self._scope(base, filters)).order_by(
            base.c.product_name, base.c.product_id
        )
        with self._session.no_autoflush:
            rows = self._session.execute(statement).mappings().all()
        facts = []
        for row in rows:
            count = row["active_location_count"]
            facts.append(ProductAnalyticsFact(
                product_id=row["product_id"], product_name=row["product_name"],
                usage_status=row["usage_status"], manufacturer_id=row["manufacturer_id"],
                manufacturer_name=row["manufacturer_name"],
                has_current_sds=row["current_sds_id"] is not None,
                current_sds_id=row["current_sds_id"],
                current_sds_original_filename=row["current_sds_original_filename"],
                current_sds_relative_path=row["current_sds_relative_path"],
                current_sds_registered_at=row["current_sds_registered_at"],
                bhp_category=AnalyticsBhpStatus(row["bhp_category"]),
                current_bhp_decision_id=row["current_bhp_decision_id"],
                current_evidence_id=row["current_evidence_id"],
                current_evidence_original_filename=row["current_evidence_original_filename"],
                current_evidence_relative_path=row["current_evidence_relative_path"],
                active_location_count=count, has_active_location=count > 0,
                latest_sds_registered_at=row["latest_sds_registered_at"],
            ))
        return facts

    def get_active_location_count(self, filters: AnalyticsFilters, product_ids: tuple[str, ...]) -> int:
        product_filter = (filters.manufacturer_id is not None or filters.sds_status is not None
                          or filters.bhp_status is not None or filters.usage_location_id is not None
                          or filters.include_no_active_location)
        statement = select(func.count(distinct(UsageLocationModel.location_id))).where(
            UsageLocationModel.status == UsageLocationStatus.ACTIVE
        )
        if product_filter:
            statement = statement.join(
                ProductUsageLocationModel,
                ProductUsageLocationModel.location_id == UsageLocationModel.location_id,
            ).where(ProductUsageLocationModel.product_id.in_(product_ids))
        if filters.usage_location_id is not None:
            statement = statement.where(UsageLocationModel.location_id == str(filters.usage_location_id))
        with self._session.no_autoflush:
            return int(self._session.scalar(statement) or 0)

    def get_sds_trend(self, product_ids: tuple[str, ...], filters: AnalyticsFilters) -> list[SdsTrendPoint]:
        numbered = select(
            SdsDocumentModel.product_id.label("product_id"),
            SdsDocumentModel.registered_at.label("registered_at"),
            func.row_number().over(
                partition_by=SdsDocumentModel.product_id,
                order_by=(SdsDocumentModel.registered_at, SdsDocumentModel.sds_id),
            ).label("sequence"),
        ).subquery()
        period = func.date_trunc("month", numbered.c.registered_at)
        statement = (
            select(
                period.label("period_start"),
                func.count().filter(numbered.c.sequence == 1).label("new_sds_count"),
                func.count().filter(numbered.c.sequence > 1).label("updated_sds_count"),
            )
            .where(
                numbered.c.product_id.in_(product_ids),
                cast(numbered.c.registered_at, Date) >= filters.trend_date_from,
                cast(numbered.c.registered_at, Date) <= filters.trend_date_to,
            )
            .group_by(period).order_by(period)
        )
        with self._session.no_autoflush:
            rows = self._session.execute(statement).all()
        return [SdsTrendPoint(row.period_start.date(), row.new_sds_count, row.updated_sds_count)
                for row in rows]

    def list_product_location_rows(self, filters: AnalyticsFilters) -> list[ProductLocationAnalyticsRow]:
        base = self._base()
        scoped = select(base).where(*self._scope(base, filters)).subquery()
        active_relation = (
            select(
                ProductUsageLocationModel.product_id,
                UsageLocationModel.location_id,
                UsageLocationModel.location_name,
                ProductUsageLocationModel.peak_quantity_value,
                ProductUsageLocationModel.peak_quantity_unit_id,
                ProductUsageLocationModel.monthly_consumption_value,
                ProductUsageLocationModel.monthly_consumption_unit_id,
            )
            .join(UsageLocationModel, and_(
                UsageLocationModel.location_id == ProductUsageLocationModel.location_id,
                UsageLocationModel.status == UsageLocationStatus.ACTIVE,
            ))
            .subquery()
        )
        peak_unit = aliased(UnitOfMeasureModel)
        monthly_unit = aliased(UnitOfMeasureModel)
        review_unit = aliased(UnitOfMeasureModel)
        latest_review = latest_final_review_items_subquery()
        statement = (
            select(
                scoped.c.product_id, scoped.c.product_name, scoped.c.manufacturer_name,
                active_relation.c.location_id, active_relation.c.location_name,
                active_relation.c.peak_quantity_value,
                peak_unit.code.label("peak_quantity_unit_code"),
                active_relation.c.monthly_consumption_value,
                monthly_unit.code.label("monthly_consumption_unit_code"),
                scoped.c.usage_status, scoped.c.current_sds_revision,
                scoped.c.current_sds_issue_date, scoped.c.bhp_category,
                latest_review.c.observed_quantity.label("review_observed_quantity"),
                (latest_review.c.observed_quantity -
                 latest_review.c.baseline_max_quantity).label("review_difference"),
                review_unit.code.label("review_unit_code"),
            )
            .select_from(scoped)
            .outerjoin(active_relation, active_relation.c.product_id == scoped.c.product_id)
            .outerjoin(peak_unit, peak_unit.unit_id == active_relation.c.peak_quantity_unit_id)
            .outerjoin(monthly_unit,
                       monthly_unit.unit_id == active_relation.c.monthly_consumption_unit_id)
            .outerjoin(latest_review, and_(
                latest_review.c.product_id == scoped.c.product_id,
                latest_review.c.location_id == active_relation.c.location_id,
            ))
            .outerjoin(review_unit, review_unit.unit_id == latest_review.c.baseline_unit_id)
        )
        if filters.usage_location_id is not None:
            statement = statement.where(or_(
                active_relation.c.location_id == str(filters.usage_location_id),
                and_(filters.include_no_active_location, scoped.c.active_location_count == 0,
                     active_relation.c.product_id.is_(None)),
            ))
        statement = statement.order_by(scoped.c.product_name, scoped.c.product_id,
                                       active_relation.c.location_name, active_relation.c.location_id)
        with self._session.no_autoflush:
            rows = self._session.execute(statement).mappings().all()
        return [ProductLocationAnalyticsRow(
            product_id=row["product_id"], product_name=row["product_name"],
            manufacturer_name=row["manufacturer_name"], location_id=row["location_id"],
            location_name=row["location_name"],
            peak_quantity_value=row["peak_quantity_value"],
            peak_quantity_unit_code=row["peak_quantity_unit_code"],
            monthly_consumption_value=row["monthly_consumption_value"],
            monthly_consumption_unit_code=row["monthly_consumption_unit_code"],
            product_usage_status=row["usage_status"],
            current_sds_revision=row["current_sds_revision"],
            current_sds_issue_date=row["current_sds_issue_date"],
            bhp_category=AnalyticsBhpStatus(row["bhp_category"]),
            review_observed_quantity=row["review_observed_quantity"],
            review_difference=row["review_difference"],
            review_unit_code=row["review_unit_code"],
        ) for row in rows]
