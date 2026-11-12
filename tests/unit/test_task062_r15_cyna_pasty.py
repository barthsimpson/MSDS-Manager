"""R15 source checks and negative guards for the nine solder and paste SDS."""

from copy import deepcopy
import logging
from pathlib import Path

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import (
    load_catalog, match_first_issue_header, match_labeled_supplier,
    match_paste_header, match_update_timeline,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _document, _ranges, _read_pdf, _subsection, _verified_compact_name,
    extract_evidence, validate_evidence,
)


logging.disable(logging.CRITICAL)
PACKAGE = Path(__file__).resolve().parents[2] / "data/sds/Paczki/paczka 6 cyna, pasty"

CASES = [
    ("2020_12*", "6e11c52e3f9a44cfdf52f07420673208abdfa6bea06cf19ff195dc4ce4bf1c9e",
     8, "Pasta lutownicza seria RMA-218", None, "2020-12-14", "2",
     "SUPPLIER", "Reball.pl Roman Jędrzejewski"),
    ("Anti-Seize*", "52550499e07b697e644ba57f4ec7891a3be6c99676fe49a60de0253a00d33b7e",
     18, "Anti-Seize Pasty montażowe Presspack", "260001", "2022-12-16", "4.03",
     "SUPPLIER", "WEICON GmbH & Co. KG"),
    ("cyna_SDS-SLZ*", "55ecd64dd7fddd55c2adbf6bb86f58826d81ad8d536daeb94b697a8616ea4e43",
     19, "Spoiwo lutownicze bezołowiowe z topnikiem EVO / EVO11 / PRO / SW26 / 1.1.2 / EVO-H",
     None, "2025-07-08", "5.0/PL", "SUPPLIER", "Cynel-Unipress Sp. z o.o."),
    ("cyna_SDS-Spoiwo*", "94cbbc8c8ccf816ce9e8f2e40fa27557ddf4c043687ef764ae8d571fceefe1ed",
     19, "Spoiwo lutownicze bezołowiowe z topnikiem 1.1.3 /CF48",
     None, "2025-07-08", "5.0/PL", "SUPPLIER", "Cynel-Unipress Sp. z o.o."),
    ("INSTALFLUX*", "2ef0c919e9533e0a97cb47da8a40e55eb5f41ca47e7d832d457ad75d7b63ad37",
     12, "INSTALFLUX TLA-4N", None, "2022-03-07", None,
     "SUPPLIER", "LUT – SPAW Sp. z o.o."),
    ("Pasta AMTECH*", "715e4278b985e462b7c01e74090ed3d64232049e1d235ccc72d6cf21a3929558",
     9, "Pasta lutownicza seria 218, 223, 559, 4300, 321", None, "2020-12-14", "3",
     "SUPPLIER", "Reball.pl Roman Jędrzejewski"),
    ("Pasta termoprzew*", "00fd5a6f459721f231666cf43e1c50cfc260c8786be98c8bd1c202646bb99d1c",
     9, "Pasta termoprzewodząca H", None, "2023-01-26", "11.0",
     "MANUFACTURER", "AG TermoPasty Grzegorz Gąsowski"),
    ("Topnik lutowniczy*", "bad2a1cbe4749dbadefc9280162a749c51762237bcef3b19f56d7c251e74f7e0",
     9, "Topnik lutowniczy 559, 223, 218, 4300, 321", None, "2024-11-08", "1.0",
     "SUPPLIER", "REBALL TECHNOLOGY Sp. z o.o."),
    ("Topnik-TK*", "5591d3d0c3af17ba4386a2f61108ba55def4c805d74221105cabc58edbeeb8c1",
     17, "Topnik TK 83", None, "2024-01-26", "7.0",
     "MANUFACTURER", "AG TermoPasty Grzegorz Gąsowski"),
]


@pytest.mark.parametrize("pattern,sha,pages,name,code,issue,revision,role,party", CASES)
def test_original_pdf(pattern, sha, pages, name, code, issue, revision, role, party):
    pdf, = PACKAGE.glob(pattern)
    draft, gates = extract_evidence(pdf)
    assert draft["source"]["file_sha256"] == sha
    assert draft["source"]["page_count"] == pages
    assert draft["source"]["language"] == "pl"
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert {key: gate["status"] for key, gate in gates.items()} == dict.fromkeys(("G1", "G2", "G3"), "PASS")
    doc, = draft["documents"]
    assert doc["page_range"] == {"from": 1, "to": pages}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    assert doc["product"]["product_name"]["value"] == name
    assert doc["product"]["product_name"]["state"] == "FOUND"
    code_field = doc["product"]["manufacturer_product_code"]
    assert (code_field["state"], code_field["value"]) == (
        "FOUND" if code else "NOT_FOUND", code)
    assert doc["document_metadata"]["issue_date"]["value"] == issue
    revision_field = doc["document_metadata"]["revision"]
    assert (revision_field["state"], revision_field["value"]) == (
        "FOUND" if revision else "NOT_FOUND", revision)
    assert [(p["role"], p["name"]["state"], p["name"]["value"])
            for p in doc["parties"]] == [(role, "FOUND", party)]
    for field in (doc["product"]["product_name"], doc["document_metadata"]["issue_date"],
                  doc["parties"][0]["name"]):
        assert field["evidence"]
        assert all(1 <= proof["page"] <= pages for proof in field["evidence"])
    if pattern.startswith("cyna_SDS-SLZ"):
        assert doc["parties"][0]["name"]["evidence"][0]["page"] == 2
        assert doc["product"]["product_name"]["evidence"][0]["source_text"].splitlines()[1] == "NAZWA HANDLOWA:"
        assert name.endswith("/ EVO-H")  # The conflicting footer remains unresolved.
        assert "DOC-001:SOURCE_PRODUCT_NAME_DISCREPANCY_REQUIRES_HUMAN_REVIEW" in draft[
            "extraction_report"]["warnings"]
    if pattern.startswith("cyna_SDS-Spoiwo"):
        assert " /CF48" in name
        assert "DOC-001:SOURCE_PRODUCT_NAME_DISCREPANCY_REQUIRES_HUMAN_REVIEW" not in draft[
            "extraction_report"]["warnings"]
    if pattern.startswith("INSTALFLUX"):
        assert "TLA                   -4N" in doc["product"]["product_name"]["evidence"][0]["source_text"]


def test_g2_rejects_label_as_product_name_with_real_page_and_quote():
    pdf, = PACKAGE.glob("cyna_SDS-SLZ*")
    pages, _, _ = _read_pdf(pdf)
    draft, _ = extract_evidence(pdf)
    forged = deepcopy(draft)
    field = forged["documents"][0]["product"]["product_name"]
    field["value"] = "NAZWA HANDLOWA:"
    field["evidence"][0]["source_text"] = "1.1. Identyfikator produktu\nNAZWA HANDLOWA:"
    gates = validate_evidence(forged, pages)
    assert gates["G2"]["status"] == "FAIL"
    assert any("PRODUCT_LABEL_AS_NAME" in issue for issue in gates["G2"]["issues"])


def test_typo_subsection_is_limited_to_section_one_and_merged_sds():
    section1 = ("Karta Charakterystyki\nSEKCJA 1. Identyfikacja\n"
                "11.1 Identyfikator produktu\nNazwa produktu: Alpha\n"
                "1.2 Zastosowanie\n1.3 Dane dotyczące dostawcy karty charakterystyki\nAlpha GmbH")
    section11 = "SEKCJA 11. Informacje\n11.1 Identyfikator produktu\nNazwa produktu: Wrong"
    second = "Karta Charakterystyki\nSEKCJA 1. Identyfikacja\n11.1 Identyfikator produktu\nNazwa produktu: Beta"
    assert "Alpha" in _subsection(section1, "1.1")
    assert _subsection(section11, "1.1") == ""
    pages = [section1, section11, second]
    assert _ranges(pages) == [(1, 2), (3, 3)]
    first = _document(pages, 1, 2, 1, load_catalog())
    later = _document(pages, 3, 3, 2, load_catalog())
    assert first["product"]["product_name"]["value"] == "Alpha"
    assert later["product"]["product_name"]["value"] == "Beta"


def test_section_13_continues_on_next_page_but_not_from_other_sds():
    first = "Karta Charakterystyki\nSEKCJA 1: Identyfikacja\n1.1 Nazwa produktu: First"
    continuation = ("Karta Charakterystyki\n1.2. Zastosowania\n"
                    "1.3 Dane dotyczące dostawcy karty charakterystyki\n"
                    "Cynel-Unipress Sp. z o.o.\n1.4 Numer alarmowy\nSEKCJA 2: Zagrożenia")
    next_sds = ("Karta Charakterystyki\nSEKCJA 1: Identyfikacja\n"
                "1.1 Nazwa produktu: Second\n1.3 Dane dotyczące dostawcy karty charakterystyki\nSecond GmbH")
    pages = [first, continuation, next_sds]
    assert _ranges(pages) == [(1, 2), (3, 3)]
    assert "Cynel-Unipress" in _subsection(continuation, "1.3")
    assert "Second GmbH" not in _subsection(continuation, "1.3")
    doc = _document(pages, 1, 2, 1, load_catalog())
    assert any(p["name"]["value"] == "Cynel-Unipress Sp. z o.o." for p in doc["parties"])


def test_iso_dates_and_editions_reject_invalid_and_conflicting_values():
    first = "Data aktualizacji: 2020-12-14       Wydanie 2\nKarta Charakterystyki\nSEKCJA 1: Identyfikacja"
    repeat = "Data aktualizacji: 2020-12-14       Wydanie\nKarta Charakterystyki\nSEKCJA 2: Zagrożenia"
    conflicting = "Data aktualizacji: 2020-12-15       Wydanie 3\nKarta Charakterystyki\nSEKCJA 2: Zagrożenia"
    assert (match_paste_header(first, page=1)[0].value,
            match_paste_header(first, page=1)[1].value) == ("2020-12-14", "2")
    assert match_paste_header(repeat, page=2)[1].state == "NOT_FOUND"
    assert match_paste_header("Data aktualizacji: 2020-02-30\nKarta Charakterystyki", page=1)[0].state != "FOUND"
    doc = _document([first, repeat, conflicting], 1, 3, 1, load_catalog())
    assert doc["document_metadata"]["issue_date"]["state"] == "AMBIGUOUS"
    assert doc["document_metadata"]["revision"]["state"] == "AMBIGUOUS"
    full = "KARTA CHARAKTERYSTYKI\nData wydania: 2015-12-12  Data aktualizacji: 2025-07-08  wersja: 5.0/PL"
    assert match_paste_header(full, page=1)[1].value == "5.0/PL"


def test_timeline_last_date_without_revision_and_first_issue_fallback():
    chronology = ("KARTA CHARAKTERYSTYKI\nData sporządzenia/aktualizacji: "
                  "25.01.2016/26.03.2017 r. (1) / 07.03.2022 r. (2)")
    assert match_update_timeline(chronology, page=1).value == "2022-03-07"
    assert match_update_timeline(chronology.replace("07.03.2022", "31.02.2022"), page=1).state != "FOUND"
    first = ("KARTA CHARAKTERYSTYKI     Data opracowania:\n08.11.2024\n"
             "Data aktualizacji:-\nWersja 1.0")
    assert (match_first_issue_header(first, page=1)[0].value,
            match_first_issue_header(first, page=1)[1].value) == ("2024-11-08", "1.0")
    assert match_first_issue_header(first.replace("Data aktualizacji:-", "Data aktualizacji: 09.11.2024"), page=1)[0].state == "NOT_FOUND"
    assert match_first_issue_header(first.replace("Wersja 1.0", "Wersja 2.0"), page=1)[0].state == "NOT_FOUND"


def test_supplier_requires_company_and_name_compaction_requires_same_sds():
    section = ("1.3 Dane dotyczące dostawcy karty charakterystyki\n"
               "Dostawca:\nLUT – SPAW Sp. z o.o.\nul. Testowa 1")
    assert match_labeled_supplier(section, page=1).value == "LUT – SPAW Sp. z o.o."
    assert match_labeled_supplier(section.replace("LUT – SPAW Sp. z o.o.", "Tel.: 123"), page=1).state == "NOT_FOUND"
    inline = ("1.3 Dane dotyczące dostawcy karty charakterystyki:\n"
              "Nazwa i adres:            REBALL TECHNOLOGY Sp. z o.o.\n"
              "Adres email osoby odpowiedzialnej: bok@example.com")
    assert match_labeled_supplier(inline, page=1).value == "REBALL TECHNOLOGY Sp. z o.o."
    assert match_labeled_supplier(inline.replace("REBALL TECHNOLOGY Sp. z o.o.", "ul. Testowa 1"), page=1).state == "NOT_FOUND"
    raw = {"state": "FOUND", "value": "INSTALFLUX TLA                   -4N", "evidence": []}
    assert _verified_compact_name(raw, ["Other product"], 1, 1)["value"] == raw["value"]
    assert _verified_compact_name(raw, ["INSTALFLUX TLA-4N"], 1, 1)["value"] == "INSTALFLUX TLA-4N"
