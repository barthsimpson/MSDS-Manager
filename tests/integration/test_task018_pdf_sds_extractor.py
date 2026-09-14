from pathlib import Path

from app.infrastructure.filesystem.pdf_sds_extractor import PdfSdsExtractor


FIXTURE = Path(__file__).parents[2] / "docs" / "tasks" / (
    "30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf"
)


def test_extracts_30470_fixture_without_sds_root_copy() -> None:
    result = PdfSdsExtractor().extract(FIXTURE)

    assert result.product_name == "IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO"
    assert result.manufacturer_product_code == "30470"
    assert result.use_description == "Farba lub inna podobna substancja."
    assert result.use_restriction == "Jedynie do stosowania przemysłowego."
    assert result.issue_date is not None
    assert result.issue_date.isoformat() == "2025-10-03"
    assert result.revision == "10.02"
    assert result.safety_profile.product_definition == "Mieszanina"
    assert result.safety_profile.hazardous_classification_status.value == "NO"
    assert result.components
    assert any(component.cas_number == "111-76-2" for component in result.components)