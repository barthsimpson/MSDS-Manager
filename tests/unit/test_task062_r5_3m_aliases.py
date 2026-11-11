"""Approved 3M identity rules on original SDS; no database or UI."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from app.application.use_cases.plan_evidence_json_import import _validate_document
from app.infrastructure.filesystem.sds_alias_matcher import (
    InactiveAliasError, evaluate_binding, load_catalog, match_active_alias,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _context, _plural_product_codes, _read_pdf, _subsection,
    extract_evidence, validate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
THREE_M = ROOT / "docs/sds_Work/3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf"
SHA = "deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48"


@pytest.mark.parametrize("page,name,date,revision,code_state", [
    (1, "3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Kit", "2023-07-06", "13.00", "AMBIGUOUS"),
    (4, "3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part B", "2023-07-06", "14.00", "AMBIGUOUS"),
    (27, "3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part A", "2023-04-26", "14.00", "NOT_FOUND"),
])
def test_approved_candidate_bindings_on_original_pages(page, name, date, revision, code_state):
    pages, sha, status = _read_pdf(THREE_M)
    assert len(pages) == 49 and sha == SHA and status == "READABLE"
    catalog = load_catalog()
    expected = {"A-010": name, "A-011": date, "A-012": revision, "A-013": "3M Poland Sp. z o.o."}
    for alias_id, value in expected.items():
        content, section, location = _context(pages[page - 1], alias_id)[0]
        result = evaluate_binding(catalog[alias_id], content, page=page, section=section, location=location)
        assert result.state == "FOUND" and result.value == value
        proof, = result.evidence
        assert proof["page"] == page and proof["source_text"]
        assert proof["subsection"] == ("1.1" if alias_id == "A-010" else "1.3" if alias_id == "A-013" else None)
    plural = _plural_product_codes(_subsection(pages[page - 1], "1.1"), page)
    assert plural["state"] == code_state and plural["value"] is None
    if code_state == "AMBIGUOUS":
        assert plural["evidence"][0]["page"] == page
        assert "identyfikacyjne produktu" in plural["evidence"][0]["source_text"]
    else:
        assert plural["evidence"] == []


def test_contextual_negatives_and_inactive_gate():
    catalog = load_catalog()
    name = catalog["A-010"]
    assert evaluate_binding(name, "1.1. Identyfikator produktu\nNazwa produktu: Inna nazwa",
                            page=1, section="1.1", location="SECTION").state == "NOT_FOUND"
    assert evaluate_binding(name, "1.1. Identyfikator produktu\nPart B",
                            page=1, section="1.3", location="SECTION").state == "NOT_FOUND"
    current = evaluate_binding(catalog["A-011"],
                               "Data aktualizacji: 06/07/2023   Zastępuje wersję 17/11/2022",
                               page=1, section="HEADER", location="HEADER")
    assert current.value == "2023-07-06"
    assert evaluate_binding(catalog["A-011"], "Zastępuje wersję 17/11/2022",
                            page=1, section="HEADER", location="HEADER").state == "NOT_FOUND"
    assert evaluate_binding(catalog["A-011"], "Data aktualizacji: 31/02/2023",
                            page=1, section="HEADER", location="HEADER").state == "AMBIGUOUS"
    assert evaluate_binding(catalog["A-012"], "Numer wersji transportu: 5\nNumer ID dokumentu: 19-2630-2",
                            page=1, section="HEADER", location="HEADER").state == "NOT_FOUND"
    supplier = catalog["A-013"]
    assert evaluate_binding(supplier, "Prawa autorskie 3M Company\nAdres: 3M Poland Sp. z o.o. al. Testowa 1",
                            page=1, section="1.3", location="SECTION").state == "NOT_FOUND"
    assert evaluate_binding(supplier, "1.3 Dane dotyczące dostawcy karty charakterystyki\nAdres: Nazwa bez ulicy",
                            page=1, section="1.3", location="SECTION").state == "AMBIGUOUS"
    assert _plural_product_codes("Numer ID dokumentu: 19-2630-2", 1)["state"] == "NOT_FOUND"
    assert _plural_product_codes("UFI: ABCD-1234-EFGH-5678", 1)["state"] == "NOT_FOUND"
    for alias_id in ("A-010", "A-011", "A-012", "A-013"):
        inactive = replace(catalog[alias_id], status="APPROVED")
        with pytest.raises(InactiveAliasError):
            match_active_alias(alias_id, "test", page=1, section="HEADER", location="HEADER",
                               catalog={alias_id: inactive})


def test_three_drafts_and_evidence_gates_after_activation():
    catalog = load_catalog()
    if any(catalog[key].status != "ACTIVE" for key in ("A-010", "A-011", "A-012", "A-013")):
        pytest.skip("Full runtime check follows alias activation")
    draft, gates = extract_evidence(THREE_M)
    pages, _, _ = _read_pdf(THREE_M)
    assert draft["source"]["file_sha256"] == SHA
    assert draft["extraction_report"]["logical_sds_count"] == 3
    assert [doc["document_key"] for doc in draft["documents"]] == ["DOC-001", "DOC-002", "DOC-003"]
    assert [doc["page_range"] for doc in draft["documents"]] == [
        {"from": 1, "to": 3}, {"from": 4, "to": 26}, {"from": 27, "to": 49}]
    assert all(gate["status"] == "PASS" for gate in gates.values())
    expected = [
        ("3M Scotch-Weld DP-490 Black Structural Adhesive Kit", "2023-07-06", "13.00", "AMBIGUOUS", 1),
        ("3M Scotch-Weld DP-490 Black Structural Adhesive Part B", "2023-07-06", "14.00", "AMBIGUOUS", 4),
        ("3M Scotch-Weld DP-490 Black Structural Adhesive Part A", "2023-04-26", "14.00", "NOT_FOUND", 27),
    ]
    for index, (doc, (name, date, revision, code_state, page)) in enumerate(zip(draft["documents"], expected)):
        assert _validate_document(doc, draft["source"], index) == ()
        assert doc["review_status"] == "PENDING_REVIEW"
        assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
        assert doc["product"]["product_name"]["value"] == name
        assert doc["document_metadata"]["issue_date"]["value"] == date
        assert doc["document_metadata"]["revision"]["value"] == revision
        assert doc["product"]["manufacturer_product_code"]["state"] == code_state
        assert doc["product"]["manufacturer_product_code"]["value"] is None
        assert [(party["role"], party["name"]["value"]) for party in doc["parties"]] == [
            ("SUPPLIER", "3M Poland Sp. z o.o.")]
        assert "™" in doc["product"]["product_name"]["evidence"][0]["source_text"]
        for field in (doc["product"]["product_name"], *doc["document_metadata"].values(),
                      doc["parties"][0]["name"]):
            assert field["state"] == "FOUND" and field["evidence"][0]["page"] == page
        if code_state == "AMBIGUOUS":
            assert doc["product"]["manufacturer_product_code"]["evidence"][0]["page"] == page
        else:
            assert doc["product"]["manufacturer_product_code"]["evidence"] == []
        assert doc["safety_profile"] == {} and doc["components"] == []
    swapped = deepcopy(draft)
    swapped["documents"][1]["product"]["product_name"]["evidence"][0]["page"] = 27
    assert validate_evidence(swapped, pages)["G2"]["status"] == "FAIL"
    false_name = deepcopy(draft)
    false_name["documents"][2]["product"]["product_name"]["value"] = expected[1][0]
    assert validate_evidence(false_name, pages)["G2"]["status"] == "FAIL"
    false_code = deepcopy(draft)
    false_code["documents"][0]["product"]["manufacturer_product_code"]["value"] = "19-3248-2"
    assert validate_evidence(false_code, pages)["G1"]["status"] == "FAIL"
