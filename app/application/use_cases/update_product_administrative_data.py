"""Use case for the approved administrative fields of an existing product."""

from datetime import datetime, timezone

from app.application.dto import UpdateProductAdministrativeDataInput
from app.application.exceptions import EntityNotFoundError
from app.application.ports import ProductHistoryRepositoryPort, ProductRepositoryPort
from app.domain.models import ProductHistory


class UpdateProductAdministrativeData:
    def __init__(
        self,
        repository: ProductRepositoryPort,
        history_repository: ProductHistoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._history_repository = history_repository

    def execute(self, data: UpdateProductAdministrativeDataInput) -> None:
        if not self._repository.update_administrative_data(data):
            raise EntityNotFoundError("Product", data.product_id)

        if self._history_repository is not None:
            current = self._repository.get_details(data.product_id)
            if current is not None:
                snapshot = ProductHistory(
                    product_id=data.product_id,
                    usage_status=current.usage_status,
                    use_description=data.use_description,
                    use_restriction=data.use_restriction,
                    waste_type=data.waste_type,
                    waste_code=data.waste_code,
                    changed_at=datetime.now(timezone.utc),
                )
                self._history_repository.add(snapshot)
