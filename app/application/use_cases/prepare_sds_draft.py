"""Prepare editable SDS data without writing to Core."""

from pathlib import Path

from app.application.dto import ExtractedSdsData, SdsDraft
from app.application.ports.sds_extractor import (
    SdsExtractorPort,
    SdsFileValidatorPort,
)


class PrepareSdsDraft:
    def __init__(
        self,
        extractor: SdsExtractorPort,
        file_validator: SdsFileValidatorPort,
    ) -> None:
        self._extractor = extractor
        self._file_validator = file_validator

    def execute(self, pdf_path: Path) -> SdsDraft:
        source_relative_path = self._file_validator.validate(pdf_path)
        extracted: ExtractedSdsData = self._extractor.extract(pdf_path)
        return SdsDraft(
            source_relative_path=source_relative_path,
            product_name=extracted.product_name,
            manufacturer_product_code=extracted.manufacturer_product_code,
            manufacturer_name=extracted.manufacturer_name,
            use_description=extracted.use_description,
            use_restriction=extracted.use_restriction,
            issue_date=extracted.issue_date,
            revision=extracted.revision,
            detected_language=extracted.detected_language,
            language_valid=extracted.language_valid,
            safety_profile=extracted.safety_profile,
            components=extracted.components,
        )
