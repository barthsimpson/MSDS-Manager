"""R9 LOCTITE current dates and literal SDS card revisions."""

from copy import deepcopy
from pathlib import Path

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import (
    evaluate_binding, load_catalog, match_card_header_revision,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _document, _ranges, _read_pdf, extract_evidence, validate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data/sds/Paczki/paczka 5 loctite"


@pytest.mark.parametrize("filename,pages,sha,name,date,revision,card_number", [
    ("Loctite 242 31.05.2022.pdf", 16,
     "6c1da6c8164c8bb52aa1631508cc6e28a862ee783c2af6ef09db11f4f6a9b6af",
     "LOCTITE 242", "2022-07-11", "V005.1", "173036"),
    ("Loctite 243  rew 014.0 (27.03.2024).pdf", 24,
     "803058b5358f90c90bd3d8007b7761ccddc1d4513588f6080702f8d988b3c39d",
     "LOCTITE 243", "2024-05-14", "V014.0", "316211"),
    ("Loctite 638 24.10.2022.PDF", 32,
     "2b8264bb9021c5c0f952539a9f91da7f80909137d666fc157e2dddac8b7ff1b6",
     "Loctite 638", "2022-10-24", "V013.0", "450822"),
])
def test_original_loctite_drafts(filename, pages, sha, name, date, revision, card_number):
    pdf = PACKAGE / filename
    draft, gates = extract_evidence(pdf)
    assert draft["source"]["file_sha256"] == sha
    assert draft["source"]["page_count"] == pages
    assert draft["source"]["readability_status"] == "READABLE"
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert {key: gate["status"] for key, gate in gates.items()} == {
        "G1": "PASS", "G2": "PASS", "G3": "PASS"}
    doc, = draft["documents"]
    assert doc["document_key"] == "DOC-001"
    assert doc["page_range"] == {"from": 1, "to": pages}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    assert doc["product"]["product_name"]["value"] == name
    assert doc["product"]["manufacturer_product_code"] == {
        "value": None, "state": "NOT_FOUND", "evidence": []}
    issue_date = doc["document_metadata"]["issue_date"]
    assert issue_date["state"] == "FOUND" and issue_date["value"] == date
    date_proof, = issue_date["evidence"]
    assert date_proof["page"] == 1 and date_proof["section"] == "HEADER"
    assert date_proof["label"] == "Aktualizacja"
    assert "Aktualizacja:" in date_proof["source_text"]
    assert "Data druku:" not in date_proof["source_text"]
    revision_field = doc["document_metadata"]["revision"]
    assert revision_field["state"] == "FOUND" and revision_field["value"] == revision
    revision_proof, = revision_field["evidence"]
    assert revision_proof == {
        "page": 1, "section": "HEADER", "subsection": None, "label": "V",
        "source_text": f"KC Numer :  {card_number}\n{revision}",
    }
    assert [(p["role"], p["name"]["state"], p["name"]["value"])
            for p in doc["parties"]] == [
                ("SUPPLIER", "FOUND", "Henkel Polska Sp. z o.o.")]
    assert doc["parties"][0]["name"]["evidence"][0]["subsection"] == "1.3"
    pages_text, _, _ = _read_pdf(pdf)
    assert _ranges(pages_text) == [(1, pages)]
    assert {match_card_header_revision(text, page=number).value
            for number, text in enumerate(pages_text, 1)} == {revision}


def test_dotted_date_uses_current_label_and_valid_calendar():
    rule = load_catalog()["A-008"]
    current = evaluate_binding(
        rule, "Produkt X     Aktualizacja: 11.07.2022\n"
              "Data druku: 30.11.2022\nZastępuje wersje z: 31.05.2022",
        page=1, section="HEADER", location="HEADER",
    )
    assert current.state == "FOUND" and current.value == "2022-07-11"
    assert current.evidence[0]["source_text"] == "Produkt X     Aktualizacja: 11.07.2022"
    for negative in ("Data druku: 30.11.2022", "Zastępuje wersje z: 31.05.2022",
                     "Data aktualizacji: 11.07.2022"):
        assert evaluate_binding(rule, negative, page=1, section="HEADER",
                                location="HEADER").state == "NOT_FOUND"
    assert evaluate_binding(rule, "Aktualizacja: 31.02.2022", page=1,
                            section="HEADER", location="HEADER").state == "AMBIGUOUS"
    assert evaluate_binding(rule, "Aktualizacja: 2024/05/14", page=1,
                            section="HEADER", location="HEADER").value == "2024-05-14"


def _header(token: str, card_number: str = "173036", *, page: int = 1, total: int = 2) -> str:
    return (f"Karta charakterystyki\nStrona {page} z {total}\n"
            f"KC Numer :  {card_number}\n{token}\n")


def test_card_revision_requires_header_context_and_literal_token():
    valid = match_card_header_revision(_header("V005.1"), page=1)
    assert valid.state == "FOUND" and valid.value == "V005.1"
    for text in (
        "KC Numer : 173036\nV005.1",
        "Karta charakterystyki\nStrona 1 z 2\nV005.1",
        "Karta charakterystyki\nStrona 1 z 2\nKC Numer : 173036\nH005.1",
        "Karta charakterystyki\nStrona 1 z 2\nKC Numer : 173036\nWersja transportu V005.1",
        "SEKCJA 16: Inne informacje\nKC Numer : 173036\nV005.1",
        "Karta charakterystyki\nStrona 1 z 2\nKC Numer : 173036\n"
        + "\n" * 15 + "V005.1",
    ):
        assert match_card_header_revision(text, page=1).state == "NOT_FOUND"


def test_repeated_card_revision_and_conflict_stay_within_logical_sds():
    first = _header("V005.1") + "SEKCJA 1: Identyfikacja\n1.1. Identyfikator produktu\nProdukt X\n"
    second = _header("V005.1", page=2)
    catalog = load_catalog()
    same = _document([first, second], 1, 2, 1, catalog)
    assert same["document_metadata"]["revision"]["value"] == "V005.1"
    assert same["document_metadata"]["revision"]["state"] == "FOUND"
    conflicting = _header("V014.0", page=2)
    conflict = _document([first, conflicting], 1, 2, 1, catalog)
    assert conflict["document_metadata"]["revision"] == {
        "value": None, "state": "AMBIGUOUS", "evidence": []}
    third = (_header("V014.0", "316211", page=3, total=3) +
             "SEKCJA 1: Identyfikacja\n1.1. Identyfikator produktu\nProdukt Y\n")
    pages = [first, second, third]
    assert _ranges(pages) == [(1, 2), (3, 3)]
    assert _document(pages, 1, 2, 1, catalog)["document_metadata"]["revision"]["value"] == "V005.1"
    assert _document(pages, 3, 3, 2, catalog)["document_metadata"]["revision"]["value"] == "V014.0"


def test_gates_reject_rewritten_revision_and_card_number_as_product_code():
    pdf = PACKAGE / "Loctite 242 31.05.2022.pdf"
    draft, _ = extract_evidence(pdf)
    pages, _, _ = _read_pdf(pdf)
    wrong_revision = deepcopy(draft)
    wrong_revision["documents"][0]["document_metadata"]["revision"]["value"] = "V005.2"
    assert validate_evidence(wrong_revision, pages)["G2"]["status"] == "FAIL"
    wrong_proof = deepcopy(draft)
    wrong_proof["documents"][0]["document_metadata"]["revision"]["evidence"][0]["page"] = 2
    assert validate_evidence(wrong_proof, pages)["G2"]["status"] == "FAIL"
    false_code = deepcopy(draft)
    false_code["documents"][0]["product"]["manufacturer_product_code"] = {
        "value": "173036", "state": "FOUND", "evidence": [
            wrong_revision["documents"][0]["document_metadata"]["revision"]["evidence"][0]]}
    assert validate_evidence(false_code, pages)["G2"]["status"] == "FAIL"
