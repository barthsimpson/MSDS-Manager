from datetime import date, datetime, timezone
from decimal import Decimal

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SafetyInformationStatus,
    SdsDocumentStatus,
    UsageLocationStatus,
)
from app.domain.models import (
    BhpDecision,
    DecisionEvidence,
    Manufacturer,
    Product,
    ProductUsageLocation,
    SafetyProfile,
    SdsComponent,
    SdsDocument,
    UsageLocation,
)


NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


def make_safety_profile(**overrides) -> SafetyProfile:
    values = {
        "sds_id": "sds-1",
        "product_definition": "Cleaning mixture",
        "hazardous_classification_status": SafetyInformationStatus.YES,
        "clp_classification_text": "Eye Irrit. 2",
        "signal_word": "Warning",
        "hazard_statements": ("H319",),
        "supplemental_hazard_statements": (),
        "pbt_status": SafetyInformationStatus.NO,
        "vpvb_status": SafetyInformationStatus.NO_DATA,
        "carcinogenicity_status": SafetyInformationStatus.NO,
        "germ_cell_mutagenicity_status": SafetyInformationStatus.NO,
        "reproductive_toxicity_status": SafetyInformationStatus.NO,
        "endocrine_section_2_status": SafetyInformationStatus.YES,
        "endocrine_section_11_status": SafetyInformationStatus.NO_DATA,
        "skin_sensitization_status": SafetyInformationStatus.NO,
        "respiratory_sensitization_status": SafetyInformationStatus.NO,
        "approved_at": NOW,
    }
    values.update(overrides)
    return SafetyProfile(**values)


def test_catalog_and_usage_models_can_be_created() -> None:
    manufacturer = Manufacturer("manufacturer-1", "Example Chemicals")
    product = Product(
        product_id="product-1",
        product_name="Cleaner",
        manufacturer_product_code="C-100",
        manufacturer_id=manufacturer.manufacturer_id,
        use_description="Surface cleaning",
        use_restriction="Professional use",
        usage_status=ProductUsageStatus.PENDING_APPROVAL,
        waste_type=None,
        waste_code=None,
    )
    location = UsageLocation("location-1", "Factory hall")
    usage = ProductUsageLocation(
        product_id=product.product_id,
        location_id=location.location_id,
        peak_quantity_value=Decimal("2.50"),
        peak_quantity_unit="kg",
    )

    assert product.manufacturer_id == manufacturer.manufacturer_id
    assert product.waste_type is None
    assert product.waste_code is None
    assert usage.peak_quantity_value == Decimal("2.50")
    assert location.status is UsageLocationStatus.ACTIVE


def test_usage_location_can_be_deactivated_and_reactivated() -> None:
    active_location = UsageLocation("location-1", "Factory hall")

    inactive_location = active_location.deactivate()
    reactivated_location = inactive_location.reactivate()

    assert active_location.status is UsageLocationStatus.ACTIVE
    assert inactive_location.status is UsageLocationStatus.INACTIVE
    assert reactivated_location.status is UsageLocationStatus.ACTIVE


def test_product_accepts_informational_waste_fields() -> None:
    product = Product(
        product_id="product-1",
        product_name="Cleaner",
        manufacturer_product_code="C-100",
        manufacturer_id="manufacturer-1",
        use_description="Surface cleaning",
        use_restriction="Professional use",
        usage_status=ProductUsageStatus.ACTIVE,
        waste_type="Waste solvent",
        waste_code="14 06 03*",
    )

    assert product.waste_type == "Waste solvent"
    assert product.waste_code == "14 06 03*"


def test_sds_issue_date_and_revision_are_optional() -> None:
    document = SdsDocument(
        sds_id="sds-1",
        product_id="product-1",
        original_filename="sds.pdf",
        relative_path="missing/sds.pdf",
        document_status=SdsDocumentStatus.CURRENT,
        registered_at=NOW,
        file_status=FileAvailabilityStatus.MISSING,
    )

    assert document.issue_date is None
    assert document.revision is None


def test_sds_accepts_issue_date_and_revision() -> None:
    document = SdsDocument(
        sds_id="sds-1",
        product_id="product-1",
        original_filename="sds.pdf",
        relative_path="sds.pdf",
        issue_date=date(2026, 1, 5),
        revision="2.0",
        document_status=SdsDocumentStatus.ARCHIVED,
        registered_at=NOW,
        file_status=FileAvailabilityStatus.AVAILABLE,
    )

    assert document.issue_date == date(2026, 1, 5)
    assert document.revision == "2.0"


def test_decision_and_evidence_models_can_be_created() -> None:
    evidence = DecisionEvidence(
        evidence_id="evidence-1",
        relative_path="decisions/approval.msg",
        evidence_type=EvidenceType.EMAIL,
        file_format=EvidenceFileFormat.MSG,
        file_status=FileAvailabilityStatus.AVAILABLE,
    )
    decision = BhpDecision(
        decision_id="decision-1",
        product_id="product-1",
        sds_id="sds-1",
        decision_status=BhpDecisionStatus.APPROVED,
        notes=None,
        registered_at=NOW,
        record_status=DecisionRecordStatus.CURRENT,
        evidence_id=evidence.evidence_id,
    )

    assert decision.evidence_id == evidence.evidence_id
    assert decision.notes is None


def test_endocrine_statuses_are_independent() -> None:
    profile = make_safety_profile(
        endocrine_section_2_status=SafetyInformationStatus.YES,
        endocrine_section_11_status=SafetyInformationStatus.NO,
    )

    assert profile.endocrine_section_2_status is SafetyInformationStatus.YES
    assert profile.endocrine_section_11_status is SafetyInformationStatus.NO


def test_safety_profile_last_manual_edit_defaults_to_none() -> None:
    assert make_safety_profile().last_manual_edit_at is None


def test_sds_component_represents_missing_data() -> None:
    component = SdsComponent(
        component_id="component-1",
        sds_id="sds-1",
        component_name="Unknown substance",
    )

    assert component.cas_number is None
    assert component.ec_number is None
    assert component.reach_registration_number is None
    assert component.concentration_text is None
    assert component.classification_text is None
    assert component.hazard_statements == ()
