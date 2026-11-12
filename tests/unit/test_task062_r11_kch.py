"""R11 KCH identity, header metadata, source roles, and dotted SDS boundaries."""

from copy import deepcopy
from pathlib import Path
import re

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import (
    evaluate_binding, load_catalog, match_edition_revision, match_named_party_roles,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _document, _ranges, _read_pdf, extract_evidence, validate_evidence,
)


PACKAGE = Path(__file__).resolve().parents[2] / "data/sds/Paczki/paczka 4 KCH"
CX80 = "CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA"
AG = "AG TermoPasty Grzegorz Gąsowski"


@pytest.mark.parametrize("pattern,sha,pages,name,current,revision,role,party", [
    ("KCH EGR CLEANER rew*.pdf", "30187c7f8a32c58e9148c02e0b7892cb90d5dffb5919d3d34c08c939307e02de",
     8, "EGR CLEANER", "2023-01-23", "2.0", "MANUFACTURER", CX80),
    ("KCH RC72-1*.pdf", "23700d4454879b5c257a6d16cb05bfd2a08b4162c0b28d7ba923d19809d7ee5f",
     11, "RC72", "2023-01-23", "2.0", "MANUFACTURER", CX80),
    ("KCH Topnik RF*.pdf", "191c310803b028c074b4addaf75ce7a928ada10cb45bf0956197cf45f9c2d2b8",
     13, "Topnik RF 800", "2024-01-25", "13.0", "DISTRIBUTOR", AG),
    ("KCH-Lakier-PVB-16*.pdf", "3fab38a836340ed9a7b6a56ea0057c5fbfa2131a5f07ebec247478d6a8684d8b",
     13, "Lakier PVB 16", "2024-02-27", "6.0", "MANUFACTURER", AG),
    ("KCH-Lakier-PVB-60*.pdf", "2409eab94e207c629f44db53526b5a38ba085c4399d655b1b036dfa805ba980d",
     14, "Lakier PVB 60", "2024-01-26", "12.0", "MANUFACTURER", AG),
    ("KCH2 Farba*.pdf", "d48c77f564ae1afeb18a98caf95f9d8bd198721ce055e1b6605c1d6343277a7e",
     17, "Farba KONTUR ŻOŁTY.", "2025-07-17", "04", "SUPPLIER",
     "KON-TUR sp. z o. o. sp. k."),
])
def test_original_kch_pdf(pattern, sha, pages, name, current, revision, role, party):
    pdf, = PACKAGE.glob(pattern)
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
    assert doc["product"]["product_name"]["state"] == "FOUND"
    assert doc["product"]["product_name"]["value"] == name
    assert doc["product"]["manufacturer_product_code"] == {
        "value": None, "state": "NOT_FOUND", "evidence": []}
    assert doc["document_metadata"]["issue_date"]["value"] == current
    assert doc["document_metadata"]["revision"]["value"] == revision
    for field in (doc["product"]["product_name"], *doc["document_metadata"].values()):
        assert field["state"] == "FOUND"
        assert field["evidence"][0]["page"] == 1
    assert [(item["role"], item["name"]["state"], item["name"]["value"])
            for item in doc["parties"]] == [(role, "FOUND", party)]
    proof, = doc["parties"][0]["name"]["evidence"]
    assert proof["page"] == 1 and proof["subsection"] == "1.3"
    assert party.split()[0] in proof["source_text"]
    if party == CX80:
        assert "DARIUSZ NADERA SPÓŁKA" in proof["source_text"]
        assert "KOMANDYTOWA" in proof["source_text"]
        assert "Adres e-mail kompetentnej osoby" not in proof["source_text"]
    if role == "DISTRIBUTOR":
        assert gates["G3"]["issues"] == ["DOC-001:MANUFACTURER_REQUIRES_HUMAN_REVIEW"]


def test_duplicate_is_bitwise_identical():
    first = PACKAGE / "KCH EGR CLEANER rew. 2.0 23.01.2023.pdf"
    duplicate = PACKAGE / "KCH EGR CLEANER.pdf"
    assert first.read_bytes() == duplicate.read_bytes()


def test_current_date_and_version_bind_only_their_header_columns():
    catalog = load_catalog()
    header = ("KARTA CHARAKTERYSTYKI\nData utworzenia  02.04.2021\n"
              "Data aktualizacji  25.01.2024    Numer wersji  13.0\nSEKCJA 1: produkt")
    current = evaluate_binding(catalog["A-011"], header, page=1,
                               section="HEADER", location="HEADER")
    version = evaluate_binding(catalog["A-012"], header, page=1,
                               section="HEADER", location="HEADER")
    assert current.state == "FOUND" and current.value == "2024-01-25"
    assert version.state == "FOUND" and version.value == "13.0"
    assert "Data aktualizacji" in current.evidence[0]["source_text"]
    for wrong in ("Data utworzenia  02.04.2021", "Data wydania  25.01.2024",
                  "Data aktualizacji  31.02.2024    Numer wersji  13.0"):
        result = evaluate_binding(catalog["A-011"], wrong, page=1,
                                  section="HEADER", location="HEADER")
        assert result.state != "FOUND"
    for wrong in ("Numer wersji  24.2.26 SBLCore", "Wersja transportowa  13.0",
                  "Data aktualizacji  25.01.2024"):
        result = evaluate_binding(catalog["A-012"], wrong, page=1,
                                  section="HEADER", location="HEADER")
        assert result.state != "FOUND"


def test_inline_name_rejects_unresolved_neighbor_column():
    result = evaluate_binding(
        load_catalog()["A-010"],
        "1.1. Identyfikator produktu  EGR CLEANER    Substancja / mieszanina  mieszanina",
        page=1, section="1.1", location="SECTION",
    )
    assert result.state == "AMBIGUOUS" and result.value is None


def test_edition_header_requires_aligned_complete_columns():
    catalog = load_catalog()
    valid = "Edycja  Data wydania  Data aktualizacji  1 z 17\n04  08.01.2021  17.07.2025"
    date = evaluate_binding(catalog["A-011"], valid, page=1,
                            section="HEADER", location="HEADER")
    edition = match_edition_revision(valid, page=1)
    assert date.state == "FOUND" and date.value == "2025-07-17"
    assert edition.state == "FOUND" and edition.value == "04"
    for wrong in (
        "Edycja  Data aktualizacji  Data wydania\n04  17.07.2025  08.01.2021",
        "Edycja  Data wydania  Data aktualizacji\n04  08.01.2021",
        "Edycja  Data wydania  Data aktualizacji\n04  08.01.2021  31.02.2025",
        "SEKCJA 16. INNE INFORMACJE\n" + valid,
    ):
        found_date = evaluate_binding(catalog["A-011"], wrong, page=1,
                                      section="HEADER", location="HEADER")
        assert found_date.state != "FOUND"
    assert match_edition_revision("Edycja  Data wydania  Data aktualizacji\n"
                                  "04  08.01.2021", page=1).state == "NOT_FOUND"
    assert match_edition_revision("SEKCJA 16. INNE INFORMACJE\n" + valid,
                                  page=1).state == "NOT_FOUND"


def test_conflicting_revisions_and_dates_are_ambiguous_within_one_sds():
    pdf, = PACKAGE.glob("KCH2 Farba*.pdf")
    pages, _, _ = _read_pdf(pdf)
    conflicting = pages[1].replace("04                     08.01.2021", "05                     08.01.2021")
    doc = _document([pages[0], conflicting], 1, 2, 1, load_catalog())
    assert doc["document_metadata"]["revision"] == {
        "value": None, "state": "AMBIGUOUS", "evidence": []}
    conflicting_date = pages[1].replace("17.07.2025", "18.07.2025", 1)
    doc = _document([pages[0], conflicting_date], 1, 2, 1, load_catalog())
    assert doc["document_metadata"]["issue_date"]["state"] == "AMBIGUOUS"
    sbl_pdf = PACKAGE / "KCH EGR CLEANER rew. 2.0 23.01.2023.pdf"
    sbl_pages, _, _ = _read_pdf(sbl_pdf)
    conflicting_version = re.sub(r"(Numer wersji\s+)2\.0", r"\g<1>3.0", sbl_pages[1])
    assert conflicting_version != sbl_pages[1]
    sbl_doc = _document([sbl_pages[0], conflicting_version], 1, 2, 1, load_catalog())
    assert sbl_doc["document_metadata"]["revision"]["state"] == "AMBIGUOUS"


def test_party_role_words_are_never_company_names_and_gates_detect_tampering():
    pdf = PACKAGE / "KCH EGR CLEANER rew. 2.0 23.01.2023.pdf"
    draft, _ = extract_evidence(pdf)
    pages, _, _ = _read_pdf(pdf)
    section = pages[0].split("1.3.", 1)[1].split("1.4.", 1)[0]
    assert match_named_party_roles("1.3." + section, page=1)[0].value == CX80
    supplier = evaluate_binding(load_catalog()["A-013"], "1.3." + section,
                                page=1, section="1.3", location="SECTION")
    assert supplier.state == "NOT_FOUND"
    word_as_name = deepcopy(draft)
    word_as_name["documents"][0]["parties"][0]["name"]["value"] = "Producent"
    assert "DOC-001:PARTY_ROLE_WORD_AS_NAME" in validate_evidence(word_as_name, pages)["G2"]["issues"]
    wrong_role = deepcopy(draft)
    wrong_role["documents"][0]["parties"][0]["role"] = "SUPPLIER"
    assert validate_evidence(wrong_role, pages)["G3"]["status"] == "FAIL"
    wrong_name = deepcopy(draft)
    wrong_name["documents"][0]["parties"][0]["name"]["value"] = AG
    assert validate_evidence(wrong_name, pages)["G2"]["status"] == "FAIL"
    weak_proof = deepcopy(draft)
    weak_proof["documents"][0]["parties"][0]["name"]["evidence"][0]["source_text"] = "Producent"
    assert validate_evidence(weak_proof, pages)["G2"]["status"] == "FAIL"
    distributor_pdf, = PACKAGE.glob("KCH Topnik RF*.pdf")
    distributor_draft, _ = extract_evidence(distributor_pdf)
    distributor_pages, _, _ = _read_pdf(distributor_pdf)
    distributor_draft["documents"][0]["parties"][0]["name"]["value"] = "Dystrybutor"
    assert validate_evidence(distributor_draft, distributor_pages)["G2"]["status"] == "FAIL"


def test_dotted_section_one_splits_joined_documents_without_false_starts():
    pdf, = PACKAGE.glob("KCH2 Farba*.pdf")
    pages, _, _ = _read_pdf(pdf)
    assert _ranges(pages) == [(1, 17)]
    joined = [pages[0], pages[1], pages[0], pages[1]]
    assert _ranges(joined) == [(1, 2), (3, 4)]
    for text in ("SEKCJA 10. Stabilność", "SEKCJA 16. Inne informacje",
                 "SEKCJA 1.1. Identyfikator produktu", "1.1. Identyfikator produktu",
                 "KARTA CHARAKTERYSTYKI"):
        assert _ranges([pages[0], text]) == [(1, 2)]
