"""Focused Application and filesystem checks for TASK-041."""

from datetime import date, datetime
from pathlib import Path

import pytest

from app.application.dto.analytics import (
    AnalyticsBhpStatus as Bhp, AnalyticsFileAvailability as Availability,
    AnalyticsFilters, ProductAnalyticsFact,
)
from app.application.use_cases.get_analytics_dashboard import GetAnalyticsDashboard
from app.domain.enums import ProductUsageStatus
from app.infrastructure.filesystem.analytics_availability import AnalyticsFileAvailabilityAdapter
from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


def filters(start=date(2026, 1, 1), end=date(2026, 12, 31)):
    return AnalyticsFilters(trend_date_from=start, trend_date_to=end)


def fact(product_id, *, sds=False, bhp=None, status=ProductUsageStatus.ACTIVE,
         locations=0, manufacturer="m1"):
    return ProductAnalyticsFact(
        product_id=product_id, product_name=product_id, usage_status=status,
        manufacturer_id=manufacturer, manufacturer_name=manufacturer,
        has_current_sds=sds, current_sds_id=product_id if sds else None,
        current_sds_original_filename="source.pdf" if sds else None,
        current_sds_relative_path=f"{product_id}.pdf" if sds else None,
        current_sds_registered_at=datetime(2026, 2, 1) if sds else None,
        bhp_category=bhp or (Bhp.NO_DECISION if sds else Bhp.NOT_APPLICABLE_NO_CURRENT_SDS),
        current_bhp_decision_id=product_id if bhp in (Bhp.APPROVED, Bhp.REJECTED) else None,
        current_evidence_id=product_id if bhp in (Bhp.APPROVED, Bhp.REJECTED) else None,
        current_evidence_original_filename="decision.pdf" if bhp in (Bhp.APPROVED, Bhp.REJECTED) else None,
        current_evidence_relative_path=f"{product_id}.pdf" if bhp in (Bhp.APPROVED, Bhp.REJECTED) else None,
        active_location_count=locations, has_active_location=locations > 0,
        latest_sds_registered_at=datetime(2026, 2, 1) if sds else None,
    )


class Query:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def list_product_facts(self, filters):
        self.calls.append("facts")
        return self.rows

    def get_active_location_count(self, filters, product_ids):
        self.calls.append("locations")
        return 2

    def get_sds_trend(self, product_ids, filters):
        self.calls.append(("trend", filters.trend_date_from, filters.trend_date_to))
        return []


class Files:
    def sds_availability(self, path):
        return Availability.MISSING if path == "p1.pdf" else Availability.AVAILABLE

    def evidence_availability(self, path):
        return Availability.CHECK_FAILED


def test_kpi_attention_and_status_categories_are_product_based():
    rows = [
        fact("p1"),
        fact("p2", sds=True),
        fact("p3", sds=True, bhp=Bhp.APPROVED, locations=1),
        fact("p4", sds=True, bhp=Bhp.REJECTED, status=ProductUsageStatus.REJECTED),
        fact("p5", status=ProductUsageStatus.INACTIVE),
    ]
    query = Query(rows)
    result = GetAnalyticsDashboard(query, Files()).execute(filters())
    assert result.kpi.products_total == 5
    assert result.kpi.current_sds_count == 3
    assert result.kpi.bhp_approved_count == 1
    assert result.kpi.attention_products_count == 3
    assert result.kpi.active_locations_count == 2
    assert result.bhp_status.approved == 1
    assert result.bhp_status.rejected == 1
    assert result.bhp_status.no_decision == 1
    assert result.attention.no_current_sds_count == 2
    assert result.attention.no_bhp_decision_count == 1
    assert result.attention.no_active_location_count == 2
    assert result.attention.missing_source_file_count == 0
    assert result.product_facts[2].current_evidence_availability == Availability.CHECK_FAILED
    assert result.manufacturer_summary[0].latest_sds_registered_at == datetime(2026, 2, 1)
    assert query.calls == ["facts", "locations", ("trend", date(2026, 1, 1), date(2026, 12, 31))]


def test_missing_files_are_counted_once_per_product_and_date_only_changes_trend():
    rows = [fact("p1", sds=True, bhp=Bhp.APPROVED, locations=1)]
    class MissingFiles(Files):
        def sds_availability(self, path):
            return Availability.MISSING
        def evidence_availability(self, path):
            return Availability.MISSING
    query = Query(rows)
    first = GetAnalyticsDashboard(query, MissingFiles()).execute(filters())
    second = GetAnalyticsDashboard(query, MissingFiles()).execute(
        filters(date(2025, 1, 1), date(2025, 1, 31))
    )
    assert first.kpi == second.kpi
    assert first.kpi.attention_products_count == 1
    assert first.attention.missing_source_file_count == 1


def test_filter_validation_and_duplicate_fact_guard():
    with pytest.raises(ValueError, match="trend_date_from"):
        GetAnalyticsDashboard(Query([]), Files()).execute(filters(date(2026, 2, 1), date(2026, 1, 1)))
    with pytest.raises(ValueError, match="duplicate PRODUCT"):
        GetAnalyticsDashboard(Query([fact("same"), fact("same")]), Files()).execute(filters())


def test_safe_filesystem_overlay_without_mutation(tmp_path: Path):
    sds_root, evidence_root = tmp_path / "sds", tmp_path / "evidence"
    sds_root.mkdir()
    evidence_root.mkdir()
    (sds_root / "current.pdf").write_bytes(b"pdf")
    (evidence_root / "decision.pdf").write_bytes(b"evidence")
    adapter = AnalyticsFileAvailabilityAdapter(SdsPdfStorage(sds_root), BhpEvidenceStorage(evidence_root))
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") )
    assert adapter.sds_availability("current.pdf") == Availability.AVAILABLE
    assert adapter.sds_availability("missing.pdf") == Availability.MISSING
    assert adapter.evidence_availability("decision.pdf") == Availability.AVAILABLE
    assert adapter.evidence_availability("missing.pdf") == Availability.MISSING
    assert adapter.sds_availability("../outside.pdf") == Availability.CHECK_FAILED
    assert adapter.evidence_availability("../outside.pdf") == Availability.CHECK_FAILED
    assert adapter.sds_availability(str(tmp_path / "outside.pdf")) == Availability.CHECK_FAILED
    assert adapter.evidence_availability(str(tmp_path / "outside.pdf")) == Availability.CHECK_FAILED
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before


def test_check_failure_is_not_missing(tmp_path: Path):
    adapter = AnalyticsFileAvailabilityAdapter(
        SdsPdfStorage(tmp_path / "absent-sds"),
        BhpEvidenceStorage(tmp_path / "absent-evidence"),
    )
    assert adapter.sds_availability("source.pdf") == Availability.CHECK_FAILED
    assert adapter.evidence_availability("decision.pdf") == Availability.CHECK_FAILED
