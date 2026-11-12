"""R7 approved WEICON context rules and paczka 3 evidence regression."""

from copy import deepcopy
from pathlib import Path

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import evaluate_binding, load_catalog
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _read_pdf, extract_evidence, validate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data/sds/Paczki/paczka3 silicon"


@pytest.mark.parametrize("filename,pages,name,code,date,revision,supplier", [
    ("Repair Stick Steel 10.19.2022 rew.3.01.pdf", 14, "Repair Stick Steel",
     "105330", "2022-10-20", "3.01", "WEICON GmbH & Co. KG"),
    ("Silicon F Weicon 10.19.2022 rew. 3.01.pdf", 12, "Silicone F",
     "132000", "2022-10-20", "3.01", "WEICON GmbH & Co. KG"),
    ("silikon A DOWSIL  CN-8760-PL rew.05 20230106.pdf", 17,
     "DOWSIL CN-8760 Encapsulant Part A", None, "2023-01-06", "5.0",
     "DOW POLSKA SP.Z O.O."),
    ("silikon B DOWSIL  CN-8760 PL rew.05 20240725.pdf", 29,
     "DOWSIL CN-8760 Encapsulant Part B", None, "2024-07-25", "5.0",
     "DOW POLSKA SP.Z O.O."),
])
def test_original_paczka3_identity_and_gates(filename, pages, name, code, date, revision, supplier):
    draft, gates = extract_evidence(PACKAGE / filename)
    assert draft["source"]["page_count"] == pages
    assert draft["source"]["readability_status"] == "READABLE"
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert {key: value["status"] for key, value in gates.items()} == {
        "G1": "PASS", "G2": "PASS", "G3": "PASS"}
    doc, = draft["documents"]
    assert doc["document_key"] == "DOC-001"
    assert doc["page_range"] == {"from": 1, "to": pages}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    assert doc["product"]["product_name"]["value"] == name
    product_code = doc["product"]["manufacturer_product_code"]
    assert (product_code["state"], product_code["value"]) == (
        ("FOUND", code) if code else ("NOT_FOUND", None))
    assert doc["document_metadata"]["issue_date"]["value"] == date
    assert doc["document_metadata"]["revision"]["value"] == revision
    assert [(party["role"], party["name"]["state"], party["name"]["value"])
            for party in doc["parties"]] == [("SUPPLIER", "FOUND", supplier)]
    for field in (doc["product"]["product_name"], *doc["document_metadata"].values(),
                  doc["parties"][0]["name"]):
        assert field["state"] == "FOUND" and field["evidence"]
        assert all(1 <= proof["page"] <= pages and proof["source_text"]
                   for proof in field["evidence"])
        assert any(proof["page"] == 1 for proof in field["evidence"])
    if code:
        assert product_code["evidence"][0]["page"] == 1
        assert doc["document_metadata"]["issue_date"]["evidence"][0]["section"] == "FOOTER"
        assert "10/20/2022" in doc["document_metadata"]["issue_date"]["evidence"][0]["source_text"]
        supplier_proof = doc["parties"][0]["name"]["evidence"][0]
        assert supplier_proof["section"] == "1" and supplier_proof["subsection"] == "1.3"
        assert "WEICON GmbH & Co. KG" in supplier_proof["source_text"]
        assert "Königsberger Str." not in supplier_proof["source_text"]
        assert not any(party["role"] == "MANUFACTURER" for party in doc["parties"])
    else:
        assert product_code["evidence"] == []


@pytest.mark.parametrize("source,expected", [
    ("02/03/2022", "2022-03-02"),
    ("10/20/2022   Data poprzedniego wydania :10/19/2022", "2022-10-20"),
    ("02/03/2022   Data poprzedniego wydania :10/19/2022", "2022-02-03"),
    ("02/03/2022   Data poprzedniego wydania :02/99/2022", "2022-03-02"),
    ("25, Listopad, 2022   Data poprzedniego wydania :18, Cze, 2022", "2022-11-25"),
])
def test_current_date_format_priority_and_literal_evidence(source, expected):
    rule = load_catalog()["A-005"]
    result = evaluate_binding(rule, "Data wydania/Data aktualizacji :" + source,
                              page=1, section="FOOTER", location="FOOTER")
    assert result.state == "FOUND" and result.value == expected
    proof, = result.evidence
    assert proof["page"] == 1 and proof["section"] == "FOOTER"
    assert proof["label"] == "Data wydania/Data aktualizacji"
    assert source in proof["source_text"]


def test_current_date_rejects_impossible_and_wrong_labels():
    rule = load_catalog()["A-005"]
    invalid = evaluate_binding(rule, "Data wydania/Data aktualizacji :31/02/2022",
                               page=1, section="FOOTER", location="FOOTER")
    assert invalid.state == "AMBIGUOUS" and invalid.value is None
    assert evaluate_binding(rule, "Data poprzedniego wydania :10/19/2022\n"
                            "Data wydruku :10/21/2022", page=1, section="FOOTER",
                            location="FOOTER").state == "NOT_FOUND"


def test_supplier_next_line_and_negative_contexts():
    rule = load_catalog()["A-013"]
    text = ("1.3 Dane dotyczące dostawcy karty charakterystyki\n"
            "WEICON GmbH & Co. KG\nKönigsberger Str. 255\n"
            "Phone: +49 251 93220\nAdres e-mail osoby: msds@weicon.de")
    result = evaluate_binding(rule, text, page=1, section="1.3", location="SECTION")
    assert result.state == "FOUND" and result.value == "WEICON GmbH & Co. KG"
    assert result.evidence[0]["source_text"] == (
        "1.3 Dane dotyczące dostawcy karty charakterystyki\nWEICON GmbH & Co. KG")
    for next_line in ("Königsberger Str. 255", "Königsberger Str.", "Phone: +49 251 93220",
                      "Adres e-mail osoby: msds@weicon.de", "Copyright Company"):
        negative = evaluate_binding(rule,
                                    "1.3 Dane dotyczące dostawcy karty charakterystyki\n" + next_line,
                                    page=1, section="1.3", location="SECTION")
        assert negative.state != "FOUND"
    assert evaluate_binding(rule, text, page=1, section="1.4", location="SECTION").state == "NOT_FOUND"
    assert evaluate_binding(rule, "1.3 Dane dotyczące dostawcy karty charakterystyki\n"
                            "IDENTYFIKACJA FIRMY\nDOW POLSKA SP.Z O.O.",
                            page=1, section="1.3", location="SECTION").state == "NOT_FOUND"


def test_identical_revisions_merge_but_conflicts_remain_ambiguous():
    rule = load_catalog()["A-006"]
    same = evaluate_binding(rule, "Wersja : 3.01\nWersja :3.01 12/12",
                            page=12, section="FOOTER", location="FOOTER")
    assert same.state == "FOUND" and same.value == "3.01"
    assert same.evidence[0]["page"] == 12
    conflict = evaluate_binding(rule, "Wersja : 3.01\nWersja : 4.00",
                                page=12, section="FOOTER", location="FOOTER")
    assert conflict.state == "AMBIGUOUS" and conflict.value is None
    assert evaluate_binding(rule, "Wersja transportu: 5\n12/12",
                            page=12, section="FOOTER", location="FOOTER").state == "NOT_FOUND"


def test_previous_date_cannot_be_substituted_for_current_date():
    pdf = PACKAGE / "Silicon F Weicon 10.19.2022 rew. 3.01.pdf"
    draft, _ = extract_evidence(pdf)
    pages, _, _ = _read_pdf(pdf)
    wrong = deepcopy(draft)
    wrong["documents"][0]["document_metadata"]["issue_date"]["value"] = "2022-10-19"
    assert validate_evidence(wrong, pages)["G2"]["status"] == "FAIL"
