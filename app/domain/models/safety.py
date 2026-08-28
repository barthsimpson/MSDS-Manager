"""Approved SDS safety information domain models."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import SafetyInformationStatus


@dataclass(frozen=True, slots=True)
class SafetyProfile:
    sds_id: str
    product_definition: str | None
    hazardous_classification_status: SafetyInformationStatus
    clp_classification_text: str | None
    signal_word: str | None
    hazard_statements: tuple[str, ...]
    supplemental_hazard_statements: tuple[str, ...]
    pbt_status: SafetyInformationStatus
    vpvb_status: SafetyInformationStatus
    carcinogenicity_status: SafetyInformationStatus
    germ_cell_mutagenicity_status: SafetyInformationStatus
    reproductive_toxicity_status: SafetyInformationStatus
    endocrine_section_2_status: SafetyInformationStatus
    endocrine_section_11_status: SafetyInformationStatus
    skin_sensitization_status: SafetyInformationStatus
    respiratory_sensitization_status: SafetyInformationStatus
    approved_at: datetime
    last_manual_edit_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SdsComponent:
    component_id: str
    sds_id: str
    component_name: str
    cas_number: str | None = None
    ec_number: str | None = None
    reach_registration_number: str | None = None
    concentration_text: str | None = None
    classification_text: str | None = None
    hazard_statements: tuple[str, ...] = ()
