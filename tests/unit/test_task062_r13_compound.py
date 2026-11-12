"""R13 COMPOUND source evidence and narrow regression guards."""

from copy import deepcopy
from pathlib import Path
import logging

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import (
    evaluate_binding, load_catalog, match_combined_supplier, match_compound_identity,
    match_distributor_blocks, match_english_revision_header,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _document, _ranges, _source_language, _subsection, extract_evidence,
    validate_evidence,
)


logging.disable(logging.CRITICAL)  # pypdf's optional fontTools warnings are very large.
PACKAGE = Path(__file__).resolve().parents[2] / "data/sds/Paczki/paczka 10 compound"
ROESLER = "Rösler Oberflächentechnik GmbH"
DIST = "ZYGMUNT J. GLUCHOWSKI S.C."


@pytest.mark.parametrize("pattern,sha,pages,name,code,issue,revision,language", [
    ("*R 20*", "683117193777c9baf15571ef4c046c7a8628436f99e55074db05533e25fac7e9",
     11, "Compound R 20", "04502000200", "2021-11-29", "16", "en"),
    ("*R 35 E*", "89e54bed1c751bfa0e299d05fd57b73a05b3a187148256ad631d0852f36daa55",
     11, "Compound R 35 E", "04502000355", "2023-07-07", "15", "pl"),
    ("*R 48*", "65449c00dfadc643bda3d60ef4516fd949d0f1b5d5aa8fabc09a470c4ba280c3",
     10, "Compound R 48", "04502000480", "2023-07-07", "15", "pl"),
])
def test_originals(pattern, sha, pages, name, code, issue, revision, language):
    pdf, = PACKAGE.glob(pattern)
    draft, gates = extract_evidence(pdf)
    assert draft["source"]["file_sha256"] == sha
    assert draft["source"]["page_count"] == pages
    assert draft["source"]["language"] == language
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert {key: gate["status"] for key, gate in gates.items()} == dict.fromkeys(("G1", "G2", "G3"), "PASS")
    doc, = draft["documents"]
    assert doc["page_range"] == {"from": 1, "to": pages}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    for field, value in ((doc["product"]["product_name"], name),
                         (doc["product"]["manufacturer_product_code"], code),
                         (doc["document_metadata"]["issue_date"], issue),
                         (doc["document_metadata"]["revision"], revision)):
        assert (field["state"], field["value"]) == ("FOUND", value)
        assert field["evidence"][0]["page"] == 1
    supplier = [p for p in doc["parties"] if p["role"] == "SUPPLIER"]
    assert len(supplier) == 1
    assert supplier[0]["name"]["value"] == ROESLER
    proof = supplier[0]["name"]["evidence"][0]
    assert proof["page"] == 1 and proof["subsection"] == "1.3"
    assert proof["label"] == ("Manufacturer/Supplier" if language == "en" else "Producent/Dostawcy")
    assert "MANUFACTURER" not in [p["role"] for p in doc["parties"]]
    distributors = [p["name"] for p in doc["parties"] if p["role"] == "DISTRIBUTOR"]
    if language == "en":
        assert distributors == []
    else:
        assert [(p["state"], p["value"]) for p in distributors] == [
            ("FOUND", DIST), ("AMBIGUOUS", None)]
        assert all(p["evidence"] for p in distributors)
        assert [p["source_text"] for p in distributors[1]["evidence"]] == [
            "Filip Kapela", "Lucjan Zalewski\nTechnika Obróbki"]
        assert "DOC-001:DISTRIBUTOR_IDENTITY_AMBIGUOUS" in gates["G3"]["issues"]


def test_hyphenated_english_and_polish_sections_split_at_sds_boundary():
    en = "Safety data sheet\n* SECTION 1: Identification\n- 1.1 Product identifier\n- Trade name: Alpha\n- Article number: 001\n- 1.3 Supplier\n- Manufacturer/Supplier:\nAlpha GmbH\nSECTION 10: Stability"
    pl = "KARTA CHARAKTERYSTYKI\nSEKCJA 1: Identyfikacja\n- 1.1 Identyfikator produktu\n- Nazwa handlowa: Beta\n- Numer artykułu: 002\n- 1.3 Dane dotyczące dostawcy\n- Producent/Dostawcy:\nBeta GmbH\nSEKCJA 16: Inne"
    pages = [en, "SECTION 16: continued", pl]
    assert _ranges(pages) == [(1, 2), (3, 3)]
    assert "Article number: 001" in _subsection(en, "1.1")
    assert "SECTION 10" not in _subsection(en, "1.3")
    assert "Numer artykułu: 002" in _subsection(pl, "1.1")
    catalog = load_catalog()
    first = _document(pages, 1, 2, 1, catalog)
    second = _document(pages, 3, 3, 2, catalog)
    assert first["product"]["manufacturer_product_code"]["value"] == "001"
    assert second["product"]["manufacturer_product_code"]["value"] == "002"
    assert _source_language(["Safety data sheet without numbered sections"]) == "und"
    assert _source_language(["Safety data sheet\nSECTION 1\nKarta charakterystyki"]) == "und"
    assert _ranges([en, "* SECTION 1: repeated header\ncontinued", pl]) == [(1, 2), (3, 3)]


def test_conflicting_current_values_within_one_sds_are_ambiguous():
    first = ("Safety data sheet\nRevision: 29.11.2021Version 16 (replaces version 14)\n"
             "* SECTION 1: Identification\n- 1.1 Product identifier\n- Trade name: Alpha\n"
             "- Article number: 0001\n- 1.3 Supplier\n- Manufacturer/Supplier:\nAlpha GmbH")
    second = ("Safety data sheet\nRevision: 30.11.2021Version 17 (replaces version 16)\n"
              "SECTION 2: Hazards\n- Article number: 9999")
    doc = _document([first, second], 1, 2, 1, load_catalog())
    assert doc["document_metadata"]["issue_date"] == {
        "value": None, "state": "AMBIGUOUS", "evidence": []}
    assert doc["document_metadata"]["revision"]["state"] == "AMBIGUOUS"
    assert doc["product"]["manufacturer_product_code"]["value"] == "0001"
    conflicting_article = first.replace("- 1.3 Supplier", "- Article number: 0002\n- 1.3 Supplier")
    assert _document([conflicting_article], 1, 1, 1, load_catalog())["product"][
        "manufacturer_product_code"]["state"] == "AMBIGUOUS"


def test_article_labels_require_own_section_and_ignore_ufi_cas():
    assert len(load_catalog()) == 13
    for label in ("Article number", "Numer artykułu"):
        assert match_compound_identity(f"- {label}: 000123", page=1)[1].value == "000123"
    assert match_compound_identity("- UFI: 000123\n- CAS: 001", page=1)[1].state == "NOT_FOUND"


def test_header_dates_and_versions_require_current_labels():
    catalog = load_catalog()
    for header, expected in (("Aktualizacja: 07.07.2023Wersja 15", "2023-07-07"),
                             ("Data druku: 01.01.2000 Aktualizacja: 07.07.2023Wersja 15", "2023-07-07")):
        date = evaluate_binding(catalog["A-008"], header, page=1,
                                section="HEADER", location="HEADER")
        version = evaluate_binding(catalog["A-006"], header, page=1,
                                   section="HEADER", location="HEADER")
        assert date.value == expected and version.value == "15"
    for header in ("Data druku: 07.07.2023", "Aktualizacja: 31.02.2023Wersja 15"):
        assert evaluate_binding(catalog["A-008"], header, page=1,
                                section="HEADER", location="HEADER").state != "FOUND"
    en = "Safety data sheet\nPrinting date 01.01.2000  Revision: 29.11.2021Version 16 (replaces version 14)"
    issue, version = match_english_revision_header(en, page=1)
    assert (issue.value, version.value) == ("2021-11-29", "16")
    assert match_english_revision_header("Revision: 29.11.2021Version 16", page=1)[0].state == "NOT_FOUND"
    assert match_english_revision_header("Safety data sheet\nRevision: 16", page=1)[1].state == "NOT_FOUND"
    assert match_english_revision_header("Safety data sheet\nRevision: 31.02.2021Version 16", page=1)[0].state != "FOUND"


def test_supplier_and_distributor_blocks_do_not_promote_contacts():
    section = ("- 1.3 Dane dotyczące dostawcy\n- Producent/Dostawcy:\n"
               "Rösler Oberflächentechnik GmbH       Tel.: 123\n"
               "- Identyfikacja dystrybutora:\nZYGMUNT J. GLUCHOWSKI S.C.\n"
               "Z. Gluchowski i H. Gluchowska\nul. Testowa 1\n\n"
               "Filip Kapela\nul. Testowa 2\n\nLucjan Zalewski\nTechnika Obróbki\n"
               "mail@example.com")
    supplier = match_combined_supplier(section, page=1)
    assert (supplier.role, supplier.value) == ("SUPPLIER", ROESLER)
    blocks = match_distributor_blocks(section, page=1)
    assert [(r.state, r.value) for r in blocks] == [("FOUND", DIST), ("AMBIGUOUS", None)]
    assert not any(r.state == "FOUND" and r.value in {"Filip Kapela", "Lucjan Zalewski"} for r in blocks)
    assert match_combined_supplier("- 1.3 Supplier\n- Manufacturer/Supplier:\nTel.: 123", page=1).state == "NOT_FOUND"


def test_gates_accept_distinct_distributors_and_reject_duplicate_or_wrong_role():
    pdf, = PACKAGE.glob("*R 35 E*")
    from app.infrastructure.filesystem.sds_evidence_pipeline import _read_pdf
    pages, _, _ = _read_pdf(pdf)
    draft, _ = extract_evidence(pdf)
    doc = draft["documents"][0]
    second = deepcopy(doc["parties"][1])
    second["name"]["value"] = "ANOTHER S.C."
    second["name"]["evidence"][0]["source_text"] = "- Identyfikacja dystrybutora:\nANOTHER S.C."
    altered_pages = pages.copy()
    altered_pages[0] += "\n- Identyfikacja dystrybutora:\nANOTHER S.C.\n"
    # Same role with a distinct quoted company is structurally allowed.
    draft2 = deepcopy(draft)
    draft2["documents"][0]["parties"].append(second)
    assert not any("INVALID_OR_DUPLICATE_ROLE" in issue for issue in validate_evidence(draft2, altered_pages)["G3"]["issues"])
    duplicate = deepcopy(draft)
    duplicate["documents"][0]["parties"].append(deepcopy(doc["parties"][1]))
    assert validate_evidence(duplicate, pages)["G3"]["status"] == "FAIL"
    wrong_role = deepcopy(draft)
    wrong_role["documents"][0]["parties"][0]["role"] = "MANUFACTURER"
    assert "DOC-001:ROLE_EVIDENCE_MISMATCH" in validate_evidence(wrong_role, pages)["G3"]["issues"]
    false_person = deepcopy(draft)
    false_person["documents"][0]["parties"][1]["name"]["value"] = "Filip Kapela"
    assert validate_evidence(false_person, pages)["G2"]["status"] == "FAIL"
