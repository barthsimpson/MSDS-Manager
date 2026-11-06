"""Apply an approved identity correction and SDS revision in one transaction."""

from app.application.dto import CorrectProductIdentityInput
from app.application.dto.sds import Stage1SdsInput
from app.application.ports import ProductRepositoryPort, SdsFileValidatorPort
from app.application.use_cases.correct_product_identity import CorrectProductIdentity
from app.application.use_cases.register_stage1_sds import RegisterStage1Sds


class CorrectAndRegisterStage1Sds:
    """The caller must supply repositories sharing one owned transaction."""

    def __init__(self, product_repository: ProductRepositoryPort,
                 sds_repository, file_validator: SdsFileValidatorPort) -> None:
        self._product_repository = product_repository
        self._sds_repository = sds_repository
        self._file_validator = file_validator

    def execute(self, correction: CorrectProductIdentityInput,
                revision: Stage1SdsInput) -> str:
        if (revision.controlled_product_decision.action != "LINK"
                or revision.product_id != correction.product_id
                or revision.product_name != correction.product_name
                or revision.manufacturer_product_code != correction.manufacturer_product_code):
            raise ValueError("CORRECTION_REVISION_IDENTITY_MISMATCH")
        CorrectProductIdentity(self._product_repository).execute(correction)
        return RegisterStage1Sds(self._sds_repository, self._file_validator).execute(revision)
