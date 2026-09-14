"""Application workflow for accepting one verified SDS draft."""

from app.application.dto import AcceptSdsInput
from app.application.exceptions import SdsAcceptanceValidationError
from app.application.ports import (
    SdsAcceptanceRepositoryPort,
    SdsFileValidatorPort,
)
from app.domain.enums import SafetyInformationStatus


class AcceptSds:
    def __init__(
        self,
        repository: SdsAcceptanceRepositoryPort,
        file_validator: SdsFileValidatorPort,
    ) -> None:
        self._repository = repository
        self._file_validator = file_validator

    def execute(self, data: AcceptSdsInput) -> str:
        self._validate(data)
        self._file_validator.validate_relative(data.source_relative_path)
        return self._repository.accept(data)

    @staticmethod
    def _validate(data: AcceptSdsInput) -> None:
        required = {
            "source_relative_path": data.source_relative_path,
            "product_name": data.product_name,
            "manufacturer_product_code": data.manufacturer_product_code,
            "manufacturer_name": data.manufacturer_name,
            "use_description": data.use_description,
            "use_restriction": data.use_restriction,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SdsAcceptanceValidationError(
                "Missing required SDS acceptance fields: " + ", ".join(missing)
            )
        if data.detected_language != "PL" or data.language_valid is not True:
            raise SdsAcceptanceValidationError("Accepted SDS must be a valid PL document.")

        profile = data.safety_profile
        status_fields = (
            "hazardous_classification_status",
            "pbt_status",
            "vpvb_status",
            "carcinogenicity_status",
            "germ_cell_mutagenicity_status",
            "reproductive_toxicity_status",
            "endocrine_section_2_status",
            "endocrine_section_11_status",
            "skin_sensitization_status",
            "respiratory_sensitization_status",
        )
        for field_name in status_fields:
            value = getattr(profile, field_name)
            if value is not None and not isinstance(value, SafetyInformationStatus):
                raise SdsAcceptanceValidationError(
                    f"Invalid safety status: {field_name}"
                )
        missing_component_names = [
            index
            for index, component in enumerate(data.components)
            if not component.component_name
        ]
        if missing_component_names:
            raise SdsAcceptanceValidationError(
                "Each accepted SDS component requires component_name."
            )