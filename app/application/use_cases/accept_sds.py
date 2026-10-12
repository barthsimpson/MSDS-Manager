"""Application workflow for accepting one verified SDS draft."""

from dataclasses import replace

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
        accepted_data = replace(
            data,
            manufacturer_product_code=(
                data.manufacturer_product_code.strip() or None
                if isinstance(data.manufacturer_product_code, str) else None
            ),
            components=[
                component
                for component in data.components
                if component.component_name and component.component_name.strip()
            ],
        )
        self._file_validator.validate_relative(accepted_data.source_relative_path)
        return self._repository.accept(accepted_data)

    @staticmethod
    def _validate(data: AcceptSdsInput) -> None:
        if data.manufacturer_product_code is not None and not isinstance(data.manufacturer_product_code, str):
            raise SdsAcceptanceValidationError("Invalid manufacturer_product_code.")
        required = {
            "source_relative_path": data.source_relative_path,
            "product_name": data.product_name,
            "manufacturer_name": data.manufacturer_name,
            "use_description": data.use_description,
            "use_restriction": data.use_restriction,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SdsAcceptanceValidationError(
                "Missing required SDS acceptance fields: " + ", ".join(missing)
            )
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
