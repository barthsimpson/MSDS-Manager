"""Application use case for the supervisory read model."""

from dataclasses import replace

from app.application.dto import SupervisoryProductRow
from app.application.ports import SupervisoryQueryPort
from app.domain.enums import ProductUsageStatus


class ListSupervisoryProducts:
    def __init__(self, query: SupervisoryQueryPort) -> None:
        self._query = query

    def execute(self) -> list[SupervisoryProductRow]:
        result: list[SupervisoryProductRow] = []
        for row in self._query.list_products():
            reasons: list[str] = []
            if row.usage_status == ProductUsageStatus.PENDING_APPROVAL:
                reasons.append("BRAK DECYZJI BHP")
            if row.usage_status == ProductUsageStatus.REJECTED:
                reasons.append("PRODUKT ODRZUCONY")
            if row.current_sds_id is None:
                reasons.append("BRAK CURRENT SDS")
            elif not row.current_sds_file_available:
                reasons.append("BRAK PLIKU SDS")
            if not row.usage_locations:
                reasons.append("BRAK MIEJSCA STOSOWANIA")
            if (
                row.current_bhp_decision_id is not None
                and not row.current_bhp_evidence_available
            ):
                reasons.append("BRAK PLIKU DOWODU BHP")
            result.append(replace(
                row, requires_action=bool(reasons), action_reasons=tuple(reasons)
            ))
        return sorted(result, key=lambda row: (
            row.product_name, row.manufacturer_product_code, row.product_id
        ))
