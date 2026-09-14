from datetime import date
from pathlib import Path

from app.application.dto import (
    AcceptSdsInput,
    ExtractedSdsData,
    SdsComponentDraft,
    SdsSafetyProfileDraft,
)
from app.application.use_cases import PrepareSdsDraft
from app.domain.enums import SafetyInformationStatus


class FakeSdsExtractor:
    def __init__(self, result: ExtractedSdsData) -> None:
        self.result = result
        self.paths: list[Path] = []

    def extract(self, pdf_path: Path) -> ExtractedSdsData:
        self.paths.append(pdf_path)
        return self.result


class FakeSdsFileValidator:
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.paths: list[Path] = []

    def validate(self, pdf_path: Path) -> str:
        self.paths.append(pdf_path)
        return self.relative_path


def test_prepare_sds_draft_maps_extractor_data_without_persistence() -> None:
    extracted = ExtractedSdsData(
        product_name="Cleaner",
        manufacturer_product_code="CL-100",
        manufacturer_name="Example Chemicals",
        use_description="Industrial cleaning",
        use_restriction="Professional use",
        issue_date=date(2026, 9, 1),
        revision="3",
        detected_language="PL",
        language_valid=True,
        safety_profile=SdsSafetyProfileDraft(
            product_definition="mixture",
            hazardous_classification_status=SafetyInformationStatus.YES,
            clp_classification_text="Eye Irrit. 2",
            signal_word="Warning",
            hazard_statements=["H319"],
        ),
        components=[
            SdsComponentDraft(
                component_name="Example solvent",
                cas_number="111-11-1",
                concentration_text="10-20%",
                hazard_statements=["H315"],
            )
        ],
    )
    extractor = FakeSdsExtractor(extracted)
    validator = FakeSdsFileValidator("incoming/cleaner.pdf")
    pdf_path = Path("C:/sds/cleaner.pdf")

    result = PrepareSdsDraft(extractor, validator).execute(pdf_path)

    assert result.source_relative_path == "incoming/cleaner.pdf"
    assert result.product_name == "Cleaner"
    assert result.manufacturer_name == "Example Chemicals"
    assert result.issue_date == date(2026, 9, 1)
    assert result.safety_profile.hazard_statements == ["H319"]
    assert result.components[0].cas_number == "111-11-1"
    assert extractor.paths == [pdf_path]
    assert validator.paths == [pdf_path]


def test_prepare_sds_draft_accepts_missing_fields_and_empty_components() -> None:
    extractor = FakeSdsExtractor(ExtractedSdsData())
    validator = FakeSdsFileValidator("empty.pdf")

    result = PrepareSdsDraft(extractor, validator).execute(Path("empty.pdf"))

    assert result.product_name is None
    assert result.issue_date is None
    assert result.detected_language is None
    assert result.safety_profile.product_definition is None
    assert result.components == []


def test_draft_and_accept_input_are_mutable_for_manual_fallback() -> None:
    accepted = AcceptSdsInput(source_relative_path="manual.pdf")

    accepted.product_name = "Entered manually"
    accepted.components.append(SdsComponentDraft(component_name="Manual component"))
    accepted.safety_profile.signal_word = "Danger"

    assert accepted.product_name == "Entered manually"
    assert accepted.components[0].component_name == "Manual component"
    assert accepted.safety_profile.signal_word == "Danger"


def test_sds_contract_does_not_expose_confidence_score() -> None:
    extracted_fields = set(ExtractedSdsData.__dataclass_fields__)
    safety_fields = set(SdsSafetyProfileDraft.__dataclass_fields__)
    component_fields = set(SdsComponentDraft.__dataclass_fields__)

    assert "confidence_score" not in extracted_fields
    assert "confidence_score" not in safety_fields
    assert "confidence_score" not in component_fields
