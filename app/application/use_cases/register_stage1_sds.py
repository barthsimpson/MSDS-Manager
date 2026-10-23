"""Register one reviewed SDS identity while safety enrichment is pending."""

from app.application.dto.sds import Stage1SdsInput
from app.application.ports import SdsFileValidatorPort


class RegisterStage1Sds:
    def __init__(self, repository, file_validator: SdsFileValidatorPort) -> None:
        self._repository = repository
        self._file_validator = file_validator

    def execute(self, data: Stage1SdsInput) -> str:
        self._validate(data)
        self._file_validator.validate_relative(data.source_relative_path)
        return self._repository.register_stage1(data)

    @staticmethod
    def _validate(data: Stage1SdsInput) -> None:
        for name in ("source_relative_path", "original_filename", "product_name",
                     "manufacturer_name"):
            value = getattr(data, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"PLAN_NOT_READY: {name}")
        for name in ("use_description", "use_restriction"):
            value = getattr(data, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"PLAN_NOT_READY: {name}")
        if data.controlled_product_decision.action == "LINK" and not data.product_id:
            raise ValueError("PLAN_NOT_READY: product_id")
        if data.controlled_product_decision.action == "CREATE" and data.product_id:
            raise ValueError("Invalid controlled product decision.")
