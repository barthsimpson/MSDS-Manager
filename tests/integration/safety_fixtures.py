"""Shared fixture data for tests that need an enriched CURRENT SDS."""

from datetime import datetime, timezone

from app.domain.enums import SafetyInformationStatus
from app.infrastructure.db.models import SafetyProfileModel


_STATUS_FIELDS = (
    "hazardous_classification_status", "pbt_status", "vpvb_status",
    "carcinogenicity_status", "germ_cell_mutagenicity_status",
    "reproductive_toxicity_status", "endocrine_section_2_status",
    "endocrine_section_11_status", "skin_sensitization_status",
    "respiratory_sensitization_status",
)


def safety_profile(sds_id: str) -> SafetyProfileModel:
    """Minimal SAFETY_PROFILE; BHP decisions require one for the CURRENT SDS."""
    return SafetyProfileModel(
        sds_id=sds_id,
        hazard_statements=[],
        supplemental_hazard_statements=[],
        approved_at=datetime.now(timezone.utc),
        **{field: SafetyInformationStatus.NO_DATA for field in _STATUS_FIELDS},
    )
