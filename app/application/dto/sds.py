"""Application DTOs for the minimal SDS preparation workflow."""

from dataclasses import dataclass, field
from datetime import date

from app.domain.enums import SafetyInformationStatus


@dataclass
class SdsSafetyProfileDraft:
    product_definition: str | None = None
    hazardous_classification_status: SafetyInformationStatus | None = None
    clp_classification_text: str | None = None
    signal_word: str | None = None
    hazard_statements: list[str] = field(default_factory=list)
    supplemental_hazard_statements: list[str] = field(default_factory=list)
    pbt_status: SafetyInformationStatus | None = None
    vpvb_status: SafetyInformationStatus | None = None
    carcinogenicity_status: SafetyInformationStatus | None = None
    germ_cell_mutagenicity_status: SafetyInformationStatus | None = None
    reproductive_toxicity_status: SafetyInformationStatus | None = None
    endocrine_section_2_status: SafetyInformationStatus | None = None
    endocrine_section_11_status: SafetyInformationStatus | None = None
    skin_sensitization_status: SafetyInformationStatus | None = None
    respiratory_sensitization_status: SafetyInformationStatus | None = None


@dataclass
class SdsComponentDraft:
    component_name: str | None = None
    cas_number: str | None = None
    ec_number: str | None = None
    reach_registration_number: str | None = None
    concentration_text: str | None = None
    classification_text: str | None = None
    hazard_statements: list[str] = field(default_factory=list)


@dataclass
class ExtractedSdsData:
    product_name: str | None = None
    manufacturer_product_code: str | None = None
    manufacturer_name: str | None = None
    use_description: str | None = None
    use_restriction: str | None = None
    issue_date: date | None = None
    revision: str | None = None
    detected_language: str | None = None
    language_valid: bool | None = None
    safety_profile: SdsSafetyProfileDraft = field(
        default_factory=SdsSafetyProfileDraft
    )
    components: list[SdsComponentDraft] = field(default_factory=list)


@dataclass
class SdsDraft:
    source_relative_path: str
    product_name: str | None = None
    manufacturer_product_code: str | None = None
    manufacturer_name: str | None = None
    use_description: str | None = None
    use_restriction: str | None = None
    issue_date: date | None = None
    revision: str | None = None
    detected_language: str | None = None
    language_valid: bool | None = None
    safety_profile: SdsSafetyProfileDraft = field(
        default_factory=SdsSafetyProfileDraft
    )
    components: list[SdsComponentDraft] = field(default_factory=list)


@dataclass
class AcceptSdsInput(SdsDraft):
    """User-approved draft contract for the future Core write workflow."""


@dataclass
class AddSdsRevisionInput:
    """User-approved SDS revision for an explicitly selected product."""

    product_id: str
    source_relative_path: str
    issue_date: date | None = None
    revision: str | None = None
    safety_profile: SdsSafetyProfileDraft = field(
        default_factory=SdsSafetyProfileDraft
    )
    components: list[SdsComponentDraft] = field(default_factory=list)


# A validator may use this value to identify the configured deployment language.
DEFAULT_SDS_LANGUAGE = "PL"
