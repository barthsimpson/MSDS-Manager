"""TDR-012 identity PoC: original PDFs, bounded negative cases, no database."""

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

import pytest
from pypdf import PdfReader, PdfWriter

from app.application.use_cases.plan_evidence_json_import import _validate_document
from app.infrastructure.filesystem.sds_alias_matcher import load_catalog
from app.infrastructure.filesystem.sds_evidence_pipeline import (
    EvidencePdfError, _document, _ranges, _read_pdf, extract_evidence,
    validate_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
OPEX = ROOT / "data/sds/Paczki/paczka 14 farba/T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
SYLGARD = ROOT / "data/sds/Paczki/paczka2 sylgard"
THREE_M = ROOT / "data/sds/Paczki/paczka 17 inne/3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf"


def _required(path: Path) -> Path:
    if not path.is_file():
        pytest.fail(f"Required original SDS missing: {path}")
    return path


@pytest.mark.parametrize("path,name,code,date,revision,roles,sha", [
    (OPEX, "OPEX Acrylic Clear Metal Lacquer", "T82C13", "2022-11-25", "8",
     [("MANUFACTURER_EXPORTER", "The Sherwin-Williams Company"), ("EU_REPRESENTATIVE", "Valspar B.V.")],
     "2de8f263567f82860fc229adc11a6fad20c4c65ab3972af5288e72c968905d3b"),
    (SYLGARD / "Sylgard 160 A rew. 5.0 (2021.10.28).pdf", "SYLGARD 160 Silicone Elastomer-Part A",
     None, "2021-10-28", "5.0", [("SUPPLIER", "DOW POLSKA SP.Z O.O.")],
     "f078434cfe90d09238b81cf83f2df846f46ac93107a586a29e8a6db18a2aea72"),
    (SYLGARD / "Sylgard 160 part B rew. 5.0 (2022.22.01).pdf", "SYLGARD 160 Silicone Elastomer-Part B",
     None, "2022-11-01", "5.0", [("SUPPLIER", "DOW POLSKA SP.Z O.O.")],
     "de3640fd8e66dfa9bc8c313cfa90844f0c7e61a09a20f918ae0de296f69d4d3d"),
    (SYLGARD / "sylgard-170-silicone-rew. 4.1_part-A_2021.10.26.pdf", "SYLGARD 170 Silicone Elastomer Part A",
     None, "2021-10-26", "4.1", [("SUPPLIER", "DOW POLSKA SP.Z O.O.")],
     "cbb38ba8ff6cb9bbfb8ab2e9b91b9476dfcb21a467f05c292ba2022c31c4bc45"),
    (SYLGARD / "sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf", "SYLGARD 170 Silicone Elastomer Part B",
     None, "2022-11-07", "7.0", [("SUPPLIER", "DOW POLSKA SP.Z O.O.")],
     "add472a1e9d5b3cd09a4df7da4670398883ddf92df603684a671fe5df6feb5a9"),
])
def test_original_identity_draft_and_all_gates(path, name, code, date, revision, roles, sha):
    draft, gates = extract_evidence(_required(path))
    assert draft["schema"] == "SDS-JSON-001" and draft["schema_version"] == "0.1"
    assert draft["source"]["file_sha256"] == sha
    assert draft["source"]["readability_status"] == "READABLE"
    assert draft["extraction_report"]["logical_sds_count"] == 1
    assert {key: gate["status"] for key, gate in gates.items()} == {"G1": "PASS", "G2": "PASS", "G3": "PASS"}
    doc, = draft["documents"]
    assert _validate_document(doc, draft["source"], 0) == ()
    assert doc["page_range"] == {"from": 1, "to": draft["source"]["page_count"]}
    assert doc["review_status"] == "PENDING_REVIEW"
    assert doc["validation"]["status"] == "REQUIRES_HUMAN_REVIEW"
    assert doc["product"]["product_name"]["value"] == name
    assert any(symbol in doc["product"]["product_name"]["evidence"][0]["source_text"]
               for symbol in ("®", "™"))
    assert doc["product"]["manufacturer_product_code"]["value"] == code
    assert doc["document_metadata"]["issue_date"]["value"] == date
    assert doc["document_metadata"]["revision"]["value"] == revision
    assert [(party["role"], party["name"]["value"]) for party in doc["parties"]] == roles
    assert doc["safety_profile"] == {} and doc["components"] == []
    for field in (*doc["product"].values(), *doc["document_metadata"].values(),
                  *(party["name"] for party in doc["parties"])):
        if field["state"] == "FOUND":
            assert field["evidence"]
            for proof in field["evidence"]:
                assert proof["page"] >= 1 and proof["source_text"] and proof["section"]
        else:
            assert field == {"value": None, "state": "NOT_FOUND", "evidence": []}


def test_real_multi_sds_with_approved_3m_aliases():
    draft, gates = extract_evidence(_required(THREE_M))
    assert draft["source"]["file_sha256"] == "deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48"
    assert draft["extraction_report"]["logical_sds_count"] == 3
    assert [doc["page_range"] for doc in draft["documents"]] == [
        {"from": 1, "to": 3}, {"from": 4, "to": 26}, {"from": 27, "to": 49}]
    assert [doc["document_key"] for doc in draft["documents"]] == ["DOC-001", "DOC-002", "DOC-003"]
    assert all(_validate_document(doc, draft["source"], index) == ()
               for index, doc in enumerate(draft["documents"]))
    assert [doc["product"]["product_name"]["value"] for doc in draft["documents"]] == [
        "3M Scotch-Weld DP-490 Black Structural Adhesive Kit",
        "3M Scotch-Weld DP-490 Black Structural Adhesive Part B",
        "3M Scotch-Weld DP-490 Black Structural Adhesive Part A",
    ]
    assert [doc["product"]["manufacturer_product_code"]["state"] for doc in draft["documents"]] == [
        "AMBIGUOUS", "AMBIGUOUS", "NOT_FOUND"]
    assert all(gate["status"] == "PASS" for gate in gates.values())


def test_section_reference_is_not_a_new_document():
    assert _ranges(["Karta charakterystyki", "Sekcja 1: Numer identyfikacyjny",
                    "SEKCJA 1: Identyfikacja", "SEKCJA 2: Zagrożenia"]) == [(1, 2), (3, 4)]


def test_uncertainty_without_file_name_or_glyph_repair():
    page = ("KARTA CHARAKTERYSTYKI\nAktualizacja: 2022/11/07\nWersja: 7.0\n"
            "SEKCJA 1: Identyfikacja\n1.1 Identyfikator produktu\n"
            "Nazwa wyrobu: SYLGARD\ufffd 170 Part B\n1.2 Zastosowanie\n"
            "1.3 Dane dotyczące dostawcy karty charakterystyki\n"
            "IDENTYFIKACJA FIRMY\nDOW POLSKA SP.Z O.O.\n1.4 Telefon\n")
    doc = _document([page], 1, 1, 1, load_catalog())
    assert doc["product"]["product_name"]["state"] == "UNREADABLE"
    assert doc["product"]["product_name"]["value"] is None
    assert doc["product"]["manufacturer_product_code"]["state"] == "NOT_FOUND"
    assert doc["document_metadata"]["issue_date"]["value"] == "2022-11-07"
    assert doc["parties"][0]["role"] == "SUPPLIER"


def test_gate_rejects_missing_evidence_false_quote_wrong_date_and_role():
    draft, _ = extract_evidence(_required(OPEX))
    pages, _, _ = _read_pdf(OPEX)
    no_proof = deepcopy(draft)
    no_proof["documents"][0]["product"]["product_name"]["evidence"] = []
    assert validate_evidence(no_proof, pages)["G1"]["status"] == "FAIL"
    false_quote = deepcopy(draft)
    false_quote["documents"][0]["product"]["product_name"]["evidence"][0]["source_text"] = "from filename"
    assert validate_evidence(false_quote, pages)["G2"]["status"] == "FAIL"
    wrong_date = deepcopy(draft)
    wrong_date["documents"][0]["document_metadata"]["issue_date"]["value"] = "2022-06-18"
    assert validate_evidence(wrong_date, pages)["G2"]["status"] == "FAIL"
    wrong_role = deepcopy(draft)
    wrong_role["documents"][0]["parties"][1]["role"] = "MANUFACTURER"
    assert validate_evidence(wrong_role, pages)["G3"]["status"] == "FAIL"
    malformed = deepcopy(draft)
    malformed["source"] = "invalid"
    malformed["documents"][0]["parties"] = [{"role": "SUPPLIER", "name": None}]
    assert validate_evidence(malformed, pages)["G1"]["status"] == "FAIL"


def test_input_readability_and_invalid_pdf(tmp_path):
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not-a-pdf")
    with pytest.raises(EvidencePdfError):
        extract_evidence(invalid)
    writer = PdfWriter()
    writer.add_page(PdfReader(_required(OPEX)).pages[0])
    writer.add_blank_page(width=100, height=100)
    partial = tmp_path / "partial.pdf"
    with partial.open("wb") as stream:
        writer.write(stream)
    pages, _, status = _read_pdf(partial)
    assert len(pages) == 2 and status == "PARTIALLY_READABLE"
    draft, gates = extract_evidence(partial)
    assert draft["source"]["readability_status"] == "PARTIALLY_READABLE"
    assert all(gate["status"] == "PASS" for gate in gates.values())
    blank_writer = PdfWriter()
    blank_writer.add_blank_page(width=100, height=100)
    blank = tmp_path / "blank.pdf"
    with blank.open("wb") as stream:
        blank_writer.write(stream)
    blocked, blocked_gates = extract_evidence(blank)
    assert blocked["source"]["readability_status"] == "UNREADABLE"
    assert blocked_gates["G2"]["status"] == "FAIL"
    assert blocked["documents"][0]["validation"]["status"] == "BLOCKED"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.extract_sds_evidence", str(blank),
         "--output-dir", str(tmp_path), "--source-id", "blank"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert (tmp_path / "blank.validation.json").is_file()
    assert not (tmp_path / "blank.evidence.json").exists()
