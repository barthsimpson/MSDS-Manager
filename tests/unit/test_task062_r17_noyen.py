"""R17 checks against the five original SDS and source evidence guards."""

from copy import deepcopy
from pathlib import Path

import pytest

from app.infrastructure.filesystem.sds_alias_matcher import (
    load_catalog, match_current_update_footer, match_inline_product_identifier,
    match_parallel_party_columns, match_wrapped_supplier,
)
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    _document, _read_pdf, _subsection, extract_evidence, validate_evidence,
)


PACKAGE = Path(__file__).resolve().parents[2] / "data/sds/Paczki/paczka 7 Noyen"
CASES = [
    ("Nitra Cid*", "27515dc54c32e568bd2fdd0368c242d2b029e08618f6f3204156b85d901e734e",
     17, "Nitra Cid", "193", "2023-02-16", "9.02",
     [("SUPPLIER", "CID LINES N.V."), ("DISTRIBUTOR", "CID LINES Sp. z. o.o.")]),
    ("NOYEN 22*", "0a106f69565726ad0a898b31603cb3678a342f6fa8fb03351ce9495b9e2f1e0c",
     15, "NOYEN 22 - Preparat do usuwania korozji i kamienia wodnego - koncentrat",
     None, "2023-04-26", "4", [("SUPPLIER", "NOYEN sp. z o.o.")]),
    ("NOYEN PM200*", "fa49e0037b248572ae5bccdb4a9e6789f6496fa2e4a7628d3932b2df07b23ea8",
     13, "NOYEN PM200 - Preprat do mycia  i odtłuszczania powierzchni metalowych",
     None, "2023-02-20", "4", [("SUPPLIER", "NOYEN sp. z o.o.")]),
    ("NOYEN TIP2*", "8738ab31c3f4fa9651cdef28ed0f999aebef5d9dbcf799df79b5b0af838476a6",
     15, "NOYEN TIP2 - Preparat do usuwania nagarów", None, "2022-11-17", "3",
     [("SUPPLIER", "NOYEN sp. z o.o.")]),
    ("NT019*", "b4666605f692d03b9c55627b4da1180c46c2dbfc71f0d24f0ceafe53ddb1e3ff",
     17, "THINNER", "NT019", "2022-12-06", "2",
     [("SUPPLIER", "Sherwin-Williams Sweden AB")]),
]


@pytest.mark.parametrize("pattern,sha,pages,name,code,issue,revision,parties", CASES)
def test_original_pdf(pattern, sha, pages, name, code, issue, revision, parties):
    pdf, = PACKAGE.glob(pattern)
    draft, gates = extract_evidence(pdf)
    assert draft["source"] == {
        "original_filename": pdf.name, "file_sha256": sha, "page_count": pages,
        "language": "pl", "readability_status": "READABLE",
    }
    assert {gate: result["status"] for gate, result in gates.items()} == {
        "G1": "PASS", "G2": "PASS", "G3": "PASS"}
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert draft["extraction_report"]["errors"] == []
    doc, = draft["documents"]
    assert doc["document_key"] == "DOC-001"
    assert doc["page_range"] == {"from": 1, "to": pages}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    assert "DOC-001:MANUFACTURER_REQUIRES_HUMAN_REVIEW" in gates["G3"]["issues"]
    for field, value, subsection in (
        (doc["product"]["product_name"], name, "1.1"),
        (doc["product"]["manufacturer_product_code"], code, "1.1"),
        (doc["document_metadata"]["issue_date"], issue, None),
        (doc["document_metadata"]["revision"], revision, None),
    ):
        assert (field["state"], field["value"]) == (
            "FOUND" if value is not None else "NOT_FOUND", value)
        if value is not None:
            assert field["evidence"]
            assert all(proof["page"] in range(1, pages + 1) and
                       proof["subsection"] == subsection for proof in field["evidence"])
        else:
            assert field["evidence"] == []
    assert [(party["role"], party["name"]["value"]) for party in doc["parties"]] == parties
    assert all(party["name"]["state"] == "FOUND" and
               party["name"]["evidence"][0]["subsection"] == "1.3"
               for party in doc["parties"])
    assert not any(party["role"] == "MANUFACTURER" for party in doc["parties"])
    if pattern == "NT019*":
        assert any("Kontakt krajowy / Sherwin-Williams Poland Sp. z.o.o." in warning
                   for warning in draft["extraction_report"]["warnings"])
        assert not any("Sherwin-Williams Poland" in party["name"]["value"]
                       for party in doc["parties"])


def test_explicit_name_beats_product_form_without_breaking_inline_name():
    pdf, = PACKAGE.glob("Nitra Cid*")
    pages, _, _ = _read_pdf(pdf)
    section = _subsection(pages[0], "1.1")
    assert match_inline_product_identifier(section, page=1).state == "NOT_FOUND"
    doc = _document(pages, 1, len(pages), 1, load_catalog())
    assert doc["product"]["product_name"]["value"] == "Nitra Cid"
    inline = ("SEKCJA 1: Identyfikacja\n1.1 Identyfikator produktu: "
              "Alpha - pełna nazwa\nInne sposoby identyfikacji: UFI 123\n"
              "1.2 Zastosowanie\nNazwa produktu: Wrong")
    assert _document([inline], 1, 1, 1, load_catalog())["product"][
        "product_name"]["value"] == "Alpha - pełna nazwa"
    assert match_inline_product_identifier("1.1 Identyfikator produktu: UFI 123", page=1).state == "NOT_FOUND"


def test_columns_are_bound_to_roles_and_labels_are_not_names():
    pdf, = PACKAGE.glob("Nitra Cid*")
    pages, _, _ = _read_pdf(pdf)
    results = match_parallel_party_columns(_subsection(pages[0], "1.3"), page=1)
    assert [(result.role, result.value) for result in results] == [
        ("SUPPLIER", "CID LINES N.V."), ("DISTRIBUTOR", "CID LINES Sp. z. o.o.")]
    draft, _ = extract_evidence(pdf)
    forged = deepcopy(draft)
    forged["documents"][0]["parties"][0]["name"]["value"] = "Dostawca Dystrybutor"
    gates = validate_evidence(forged, pages)
    assert gates["G2"]["status"] == "FAIL"
    assert "DOC-001:PARTY_ROLE_WORD_AS_NAME" in gates["G2"]["issues"]
    assert gates["G3"]["status"] == "FAIL"
    swapped = deepcopy(draft)
    swapped["documents"][0]["parties"][0]["name"]["value"] = "CID LINES Sp. z. o.o."
    assert validate_evidence(swapped, pages)["G2"]["status"] == "FAIL"
    wrong_role = deepcopy(draft)
    wrong_role["documents"][0]["parties"][0]["role"] = "MANUFACTURER"
    assert validate_evidence(wrong_role, pages)["G3"]["status"] == "FAIL"
    duplicate = deepcopy(draft)
    duplicate["documents"][0]["parties"].append(deepcopy(duplicate["documents"][0]["parties"][0]))
    assert validate_evidence(duplicate, pages)["G3"]["status"] == "FAIL"
    no_names = "1.3 Dane dotyczące dostawcy karty charakterystyki\nDostawca       Dystrybutor\n1.4 Alarm"
    assert match_parallel_party_columns(no_names, page=1) == []


def test_current_footer_uses_update_and_current_version_only():
    footer = ("Data sporządzenia: 29.01.2019    Aktualizacja: 26.04.2023    "
              "Wersja: 4 (zastępuje 3) Strona 1/15")
    date, revision = match_current_update_footer(footer + "\n" * 30, page=1)
    assert (date.value, revision.value) == ("2023-04-26", "4")
    assert match_current_update_footer(footer.replace("26.04.2023", "31.02.2023"), page=1)[0].state != "FOUND"
    assert match_current_update_footer(footer.replace("Aktualizacja:", "Data druku:"), page=1)[0].state == "NOT_FOUND"
    assert match_current_update_footer(footer.replace("Wersja: 4", "Wersja: 04"), page=1)[1].value == "04"
    first = "Karta charakterystyki\nSEKCJA 1: Identyfikacja\n1.1 Identyfikator produktu: Alpha\n" + footer
    second = "Karta charakterystyki\nSEKCJA 2: Zagrożenia\n" + footer.replace(
        "26.04.2023", "27.04.2023").replace("Wersja: 4", "Wersja: 5")
    doc = _document([first, second], 1, 2, 1, load_catalog())
    assert doc["document_metadata"]["issue_date"]["state"] == "AMBIGUOUS"
    assert doc["document_metadata"]["revision"]["state"] == "AMBIGUOUS"


def test_wrapped_supplier_and_local_contact_are_distinct():
    pdf, = PACKAGE.glob("NT019*")
    pages, _, _ = _read_pdf(pdf)
    supplier = match_wrapped_supplier(_subsection(pages[0], "1.3"), page=1)
    assert (supplier.state, supplier.value) == ("FOUND", "Sherwin-Williams Sweden AB")
    assert "Kontakt krajowy" not in supplier.evidence[0]["source_text"]
    assert match_wrapped_supplier("1.3 Dane dotyczące dostawcy karty\ncharakterystyki\nKontakt krajowy", page=1).state == "NOT_FOUND"
    assert match_wrapped_supplier(
        "1.3 Dane dotyczące dostawcy karty\ncharakterystyki\n"
        "Mfg. in U.S.A and exported by:", page=1).state == "NOT_FOUND"
    draft, _ = extract_evidence(pdf)
    forged = deepcopy(draft)
    forged["documents"][0]["parties"][0]["name"]["evidence"][0]["source_text"] = "Kontakt krajowy"
    assert validate_evidence(forged, pages)["G2"]["status"] == "FAIL"
    assert _subsection("SEKCJA 1: Identyfikacja\n1.4 Telefon\nDostawca\nTel.: 123", "1.3") == ""


def test_proofs_cannot_cross_logical_sds_boundary():
    first = ("Karta charakterystyki\nSEKCJA 1: Identyfikacja\n"
             "1.1 Identyfikator produktu: Alpha\n1.3 Dane dotyczące dostawcy karty\n"
             "charakterystyki\nAlpha AB")
    second = ("Karta charakterystyki\nSEKCJA 1: Identyfikacja\n"
              "1.1 Identyfikator produktu: Beta\n1.3 Dane dotyczące dostawcy karty\n"
              "charakterystyki\nBeta AB")
    first_doc = _document([first, second], 1, 1, 1, load_catalog())
    assert first_doc["product"]["product_name"]["value"] == "Alpha"
    assert first_doc["parties"][0]["name"]["value"] == "Alpha AB"
