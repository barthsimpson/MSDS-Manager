"""Application workflow for adding a revision to an existing product."""

from app.application.dto import AddSdsRevisionInput
from app.application.exceptions import SdsAcceptanceValidationError
from app.application.ports import SdsAcceptanceRepositoryPort, SdsFileValidatorPort
from app.domain.enums import SafetyInformationStatus


class AddSdsRevision:
    def __init__(
        self,
        repository: SdsAcceptanceRepositoryPort,
        file_validator: SdsFileValidatorPort,
    ) -> None:
        self._repository = repository
        self._file_validator = file_validator

    def execute(self, data: AddSdsRevisionInput) -> str:
        self._validate(data)
        accepted_data = AddSdsRevisionInput(
            product_id=data.product_id,
            source_relative_path=data.source_relative_path,
            issue_date=data.issue_date,
            revision=data.revision,
            safety_profile=data.safety_profile,
            components=[
                component
                for component in data.components
                if component.component_name and component.component_name.strip()
            ],
        )
        self._file_validator.validate_relative(accepted_data.source_relative_path)
        return self._repository.accept_revision(accepted_data)

    @staticmethod
    def _validate(data: AddSdsRevisionInput) -> None:
        if not data.product_id:
            raise SdsAcceptanceValidationError("Product is required.")
        if not data.source_relative_path:
            raise SdsAcceptanceValidationError("SDS source file is required.")

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
            value = getattr(data.safety_profile, field_name)
            if value is not None and not isinstance(value, SafetyInformationStatus):
                raise SdsAcceptanceValidationError(
                    f"Invalid safety status: {field_name}"
                )
