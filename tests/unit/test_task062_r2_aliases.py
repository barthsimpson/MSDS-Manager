"""Focused alias regression on real local SDS files; no database or OCR."""

from dataclasses import replace
from pathlib import Path
import re

import pytest
from pypdf import PdfReader

from app.infrastructure.filesystem.sds_alias_matcher import (
    InactiveAliasError,
    evaluate_binding,
    load_catalog,
    match_active_alias,
)


ROOT = Path(__file__).resolve().parents[2]
OPEX = ROOT / "data/sds/Paczki/paczka 14 farba/T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
SYLGARD = ROOT / "data/sds/Paczki/paczka2 sylgard"
ALIAS_DOC = ROOT / "docs/tasks/SDS-ALIAS-001_Biblioteka_aliasow_i_reguly_rozszerzania_v1.0-approved.md"


def _page(path: Path, number: int = 1) -> str:
    if not path.is_file():
        pytest.skip(f"Reference PDF unavailable: {path.name}")
    return PdfReader(path).pages[number - 1].extract_text(extraction_mode="layout") or ""


def _between(text: str, start: str, end: str) -> str:
    return start + text.split(start, 1)[1].split(end, 1)[0]


def _probe(alias_id: str, text: str, *, page: int, section: str, location: str):
    return evaluate_binding(load_catalog()[alias_id], text, page=page, section=section, location=location)


def _assert_found(result, expected: str, *, page: int, section: str):
    assert result.state == "FOUND"
    assert result.value == expected
    assert result.evidence
    proof, = result.evidence
    assert proof["page"] == page
    assert proof["section"] == section
    assert proof["source_text"]


def test_catalog_and_approved_document_agree():
    catalog = load_catalog()
    original = {f"A-{number:03d}" for number in range(1, 10)}
    assert set(catalog) == {f"A-{number:03d}" for number in range(1, 14)}
    assert {key for key, rule in catalog.items() if rule.status == "ACTIVE"} == set(catalog)
    statuses = dict(re.findall(r"alias_id: (A-\d{3})[\s\S]*?status: (\w+)", ALIAS_DOC.read_text(encoding="utf-8")))
    assert statuses == {key: catalog[key].status for key in original}


def test_opex_same_line_next_line_roles_and_footer_dates():
    first = _page(OPEX)
    product = _between(first, "1.1 Identyfikator produktu", "1.2 ")
    parties = _between(first, "1.3 Dane", "1.4 ")
    name = _probe("A-001", product, page=1, section="1.1", location="SECTION")
    _assert_found(name, "OPEX\u00ae Acrylic Clear Metal Lacquer", page=1, section="1")
    assert "\ufffd" not in name.value
    _assert_found(_probe("A-002", product, page=1, section="1.1", location="SECTION"),
                  "T82C13", page=1, section="1")
    manufacturer = _probe("A-003", parties, page=1, section="1.3", location="SECTION")
    _assert_found(manufacturer, "The Sherwin-Williams Company", page=1, section="1")
    assert manufacturer.role == "MANUFACTURER_EXPORTER"
    representative = _probe("A-004", parties, page=1, section="1.3", location="SECTION")
    _assert_found(representative, "Valspar B.V.", page=1, section="1")
    assert representative.role == "EU_REPRESENTATIVE"
    assert manufacturer.evidence[0]["source_text"] != representative.evidence[0]["source_text"]

    for number in (1, 25):
        text = _page(OPEX, number)
        footer = "\n".join(line for line in text.splitlines()
                           if "Data wydania/Data aktualizacji" in line)
        _assert_found(_probe("A-005", footer, page=number, section="FOOTER", location="FOOTER"),
                      "2022-11-25", page=number, section="FOOTER")
        _assert_found(_probe("A-006", footer, page=number, section="FOOTER", location="FOOTER"),
                      "8", page=number, section="FOOTER")
        assert "18, Cze, 2022" in footer


@pytest.mark.parametrize("filename, expected_date, expected_revision, expected_name", [
    ("Sylgard 160 A rew. 5.0 (2021.10.28).pdf", "2021-10-28", "5.0", "SYLGARD\u2122 160 Silicone Elastomer-Part A"),
    ("Sylgard 160 part B rew. 5.0 (2022.22.01).pdf", "2022-11-01", "5.0", "SYLGARD\u2122 160 Silicone Elastomer-Part B"),
    ("sylgard-170-silicone-rew. 4.1_part-A_2021.10.26.pdf", "2021-10-26", "4.1", "SYLGARD\u2122 170 Silicone Elastomer Part A"),
    ("sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf", "2022-11-07", "7.0", "SYLGARD\u2122 170 Silicone Elastomer Part B"),
])
def test_sylgard_content_outweighs_filename_and_supplier_is_not_manufacturer(
    filename, expected_date, expected_revision, expected_name,
):
    first = _page(SYLGARD / filename)
    product = _between(first, "1.1 Identyfikator produktu", "1.2 ")
    parties = _between(first, "1.3 Dane", "1.4 ")
    header = first.split("SEKCJA 1:", 1)[0]
    name = _probe("A-007", product, page=1, section="1.1", location="SECTION")
    _assert_found(name, expected_name, page=1, section="1")
    assert "\ufffd" not in name.value
    assert name.evidence[0]["page"] == 1
    assert name.evidence[0]["section"] == "1"
    _assert_found(_probe("A-008", header, page=1, section="HEADER", location="HEADER"),
                  expected_date, page=1, section="HEADER")
    _assert_found(_probe("A-006", header, page=1, section="HEADER", location="HEADER"),
                  expected_revision, page=1, section="HEADER")
    supplier = _probe("A-009", parties, page=1, section="1.3", location="SECTION")
    _assert_found(supplier, "DOW POLSKA SP.Z O.O.", page=1, section="1")
    assert supplier.role == "SUPPLIER"
    assert _probe("A-002", product, page=1, section="1.1", location="SECTION").state == "NOT_FOUND"
    assert "Data ostatniego wydania:" in header


def test_boundaries_uncertainty_and_inactive_alias():
    first = _page(OPEX)
    section_14 = first.split("1.4 Numer telefonu alarmowego", 1)[1].split("SEKCJA 2:", 1)[0]
    assert _probe("A-009", section_14, page=1, section="1.4", location="SECTION").state == "NOT_FOUND"
    assert _probe("A-003", section_14, page=1, section="1.4", location="SECTION").state == "NOT_FOUND"
    assert _probe("A-006", "1/25", page=1, section="FOOTER", location="FOOTER").state == "NOT_FOUND"
    assert _probe("A-005", "Data wydania/Data aktualizacji: 18, Cze, 2022 Data poprzedniego: 25, Listopad, 2022",
                  page=1, section="HEADER", location="HEADER").state == "NOT_FOUND"
    assert _probe("A-008", "Data wydania/Data aktualizacji: 25, Listopad, 2022",
                  page=1, section="HEADER", location="HEADER").state == "NOT_FOUND"
    ambiguous = _probe("A-008", "Aktualizacja: 2022/11/01\nAktualizacja: 2022/11/07",
                       page=1, section="HEADER", location="HEADER")
    assert ambiguous.state == "AMBIGUOUS" and ambiguous.value is None
    damaged = _probe("A-007", "Nazwa wyrobu: SYLGARD\ufffd 160 Part A",
                     page=1, section="1.1", location="SECTION")
    assert damaged.state == "UNREADABLE" and damaged.value is None
    rule = replace(load_catalog()["A-008"], status="APPROVED")
    with pytest.raises(InactiveAliasError):
        match_active_alias("A-008", "Aktualizacja: 2022/11/07", page=1,
                           section="HEADER", location="HEADER", catalog={"A-008": rule})


def test_active_runtime_gate_on_real_sylgard_header():
    source = _page(SYLGARD / "sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf")
    header = source.split("SEKCJA 1:", 1)[0]
    result = match_active_alias("A-008", header, page=1,
                                section="HEADER", location="HEADER")
    _assert_found(result, "2022-11-07", page=1, section="HEADER")
