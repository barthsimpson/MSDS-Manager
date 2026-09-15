from contextlib import nullcontext
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.application.dto import SupervisoryProductRow
from app.application.exceptions import SupervisoryReadError
from app.application.use_cases import ListSupervisoryProducts
from app.domain.enums import BhpDecisionStatus, ProductUsageStatus
from app.infrastructure.config import Settings
from app.infrastructure.db.repositories import SqlAlchemySupervisoryQuery
from app.infrastructure.filesystem.file_availability import source_file_available


@pytest.fixture
def complete_row() -> SupervisoryProductRow:
    return SupervisoryProductRow(
        product_id="product-1", product_name="Paint", manufacturer_name="Maker",
        manufacturer_product_code="001", usage_status=ProductUsageStatus.ACTIVE,
        use_description="Painting", use_restriction="Professional use",
        usage_locations=("Workshop",), current_sds_id="sds-1",
        current_sds_filename="paint.pdf", current_sds_issue_date=date(2025, 1, 1),
        current_sds_revision="1", current_sds_file_available=True,
        current_bhp_decision_id="bhp-1",
        current_bhp_decision_status=BhpDecisionStatus.APPROVED,
        current_bhp_registered_at=datetime(2025, 1, 2), current_bhp_notes=None,
        current_bhp_evidence_relative_path="approval.pdf",
        current_bhp_evidence_available=True,
    )


@pytest.mark.parametrize(("changes", "expected"), [
    ({}, ()),
    ({"usage_status": ProductUsageStatus.INACTIVE}, ()),
    ({"usage_status": ProductUsageStatus.PENDING_APPROVAL,
      "current_bhp_decision_id": None, "current_bhp_decision_status": None,
      "current_bhp_registered_at": None, "current_bhp_evidence_relative_path": None,
      "current_bhp_evidence_available": False}, ("BRAK DECYZJI BHP",)),
    ({"usage_status": ProductUsageStatus.REJECTED}, ("PRODUKT ODRZUCONY",)),
    ({"current_sds_id": None, "current_sds_file_available": False,
      "current_bhp_decision_id": None, "current_bhp_evidence_available": False},
     ("BRAK CURRENT SDS",)),
    ({"current_sds_file_available": False}, ("BRAK PLIKU SDS",)),
    ({"usage_locations": ()}, ("BRAK MIEJSCA STOSOWANIA",)),
    ({"current_bhp_evidence_available": False}, ("BRAK PLIKU DOWODU BHP",)),
    ({"usage_status": ProductUsageStatus.REJECTED, "usage_locations": (),
      "current_sds_file_available": False, "current_bhp_evidence_available": False},
     ("PRODUKT ODRZUCONY", "BRAK PLIKU SDS", "BRAK MIEJSCA STOSOWANIA",
      "BRAK PLIKU DOWODU BHP")),
    ({"usage_status": ProductUsageStatus.PENDING_APPROVAL, "usage_locations": (),
      "current_sds_id": None, "current_sds_file_available": False,
      "current_bhp_decision_id": None, "current_bhp_evidence_available": False},
     ("BRAK DECYZJI BHP", "BRAK CURRENT SDS", "BRAK MIEJSCA STOSOWANIA")),
])
def test_application_assesses_facts_without_mutating_input(
    complete_row, changes, expected
) -> None:
    row = replace(complete_row, **changes)
    query = Mock()
    query.list_products.return_value = [row]
    [result] = ListSupervisoryProducts(query).execute()
    assert result.action_reasons == expected
    assert result.requires_action is bool(expected)
    assert row.action_reasons == ()
    assert row.requires_action is False
    assert replace(result, requires_action=False, action_reasons=()) == row
    query.list_products.assert_called_once_with()


def test_empty_list_and_stable_order(complete_row) -> None:
    query = Mock()
    query.list_products.return_value = []
    assert ListSupervisoryProducts(query).execute() == []
    rows = [
        replace(complete_row, product_id="3", manufacturer_product_code="002"),
        replace(complete_row, product_id="2"),
        replace(complete_row, product_id="0", product_name="Zinc"),
        complete_row,
    ]
    query.list_products.return_value = rows
    assert [row.product_id for row in ListSupervisoryProducts(query).execute()] == [
        "2", "product-1", "3", "0"
    ]


@pytest.mark.parametrize("conflicting_field", [
    "current_sds_id", "current_bhp_decision_id"
])
def test_ambiguous_current_stops_the_read_without_selecting_a_winner(
    conflicting_field, tmp_path
) -> None:
    # Production constraints prohibit these rows. Inject a corrupt read result
    # without disabling PostgreSQL constraints or changing the schema.
    first = {"product_id": "p1", "current_sds_id": "s1",
             "current_bhp_decision_id": "d1"}
    second = {**first, conflicting_field: "other"}
    session = Mock()
    session.no_autoflush = nullcontext()
    session.execute.return_value.mappings.return_value.all.return_value = [first, second]
    query = SqlAlchemySupervisoryQuery(
        session, settings=Settings("unused", tmp_path, tmp_path)
    )
    with pytest.raises(SupervisoryReadError, match="Ambiguous CURRENT.*p1"):
        ListSupervisoryProducts(query).execute()
    session.execute.assert_called_once()


def test_file_availability_uses_root_and_requires_a_regular_file(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "present.pdf").write_bytes(b"source")
    (tmp_path / "outside.pdf").write_bytes(b"outside")
    assert source_file_available(root, "present.pdf") is True
    for reference in (None, "", "missing.pdf", ".", "../outside.pdf",
                      str(tmp_path / "outside.pdf")):
        assert source_file_available(root, reference) is False


def test_file_access_error_means_unavailable(tmp_path, monkeypatch) -> None:
    def inaccessible(_self):
        raise PermissionError("access denied")
    monkeypatch.setattr(Path, "is_file", inaccessible)
    assert source_file_available(tmp_path, "source.pdf") is False
