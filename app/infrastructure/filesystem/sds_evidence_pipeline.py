"""Local, read-only PDF to SDS-JSON-001 draft for the TDR-012 identity PoC."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from pypdf import PdfReader

from app.infrastructure.filesystem.sds_alias_matcher import (
    MatchResult,
    load_catalog,
    match_active_alias,
    match_card_header_revision,
    match_combined_supplier,
    match_compound_identity,
    match_distributor_blocks,
    match_edition_revision,
    match_english_revision_header,
    match_named_party_roles,
)


SECTION = re.compile(r"(?m)^[ \t]*[*-]?[ \t]*(?:SEKCJA|SECTION)[ \t]+(\d{1,2})[ \t]*[:.](?!\d)")
SUBSECTION = re.compile(r"(?m)^[ \t]*-?[ \t]*(1\.[1-4])\.?[ \t]+", re.IGNORECASE)
FIELD_STATES = frozenset({"FOUND", "NOT_FOUND", "AMBIGUOUS", "UNREADABLE"})
PARTY_ROLES = frozenset({"MANUFACTURER", "MANUFACTURER_EXPORTER", "SUPPLIER",
                         "IMPORTER", "DISTRIBUTOR", "EU_REPRESENTATIVE", "OTHER"})
PLURAL_PRODUCT_IDS = re.compile(r"Numery\s+identyfikacyjne\s+produktu\s*$", re.IGNORECASE)
IDENTIFIER_TOKEN = re.compile(r"(?=.*\d)[A-Za-z0-9.-]+$")
PLURAL_PRODUCT_IDS_LABEL = "Numery identyfikacyjne produktu"


class EvidencePdfError(ValueError):
    """The source cannot be read as a PDF with pages."""


def _read_pdf(path: Path) -> tuple[list[str], str, str]:
    if not path.is_file() or path.suffix.lower() != ".pdf" or path.stat().st_size == 0:
        raise EvidencePdfError("Expected a nonempty PDF file")
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise EvidencePdfError("Invalid PDF signature")
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise EvidencePdfError("Encrypted PDF")
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text(extraction_mode="layout") or "")
            except Exception:
                # A damaged or contentless page remains unreadable; values
                # must never be inferred from adjacent pages or the filename.
                pages.append("")
    except Exception as error:
        raise EvidencePdfError("PDF text extraction failed") from error
    if not pages:
        raise EvidencePdfError("PDF has no pages")
    readable = sum(bool(page.strip()) for page in pages)
    status = "READABLE" if readable == len(pages) else (
        "PARTIALLY_READABLE" if readable else "UNREADABLE")
    return pages, hashlib.sha256(data).hexdigest(), status


def _ranges(pages: list[str]) -> list[tuple[int, int]]:
    # A new Section 1 after page one is a new logical SDS, never a carry-over
    # from the previous document. Page one can itself be a kit SDS without §1.
    starts = [1] + [number for number, text in enumerate(pages, 1)
                    if number > 1 and any(int(m.group(1)) == 1 and
                    ("SECTION" not in m.group(0) or bool(_subsection(text, "1.1")))
                    for m in SECTION.finditer(text))]
    return [(start, (starts[index + 1] - 1 if index + 1 < len(starts) else len(pages)))
            for index, start in enumerate(starts)]


def _subsection(text: str, key: str) -> str:
    headings = list(SUBSECTION.finditer(text))
    for index, heading in enumerate(headings):
        if heading.group(1) == key:
            preceding_sections = list(SECTION.finditer(text, 0, heading.start()))
            if preceding_sections:
                if preceding_sections[-1].group(1) != "1":
                    continue
            elif not re.search(r"IDENTYFIKACJA\s+SUBSTANCJI/MIESZANINY\s+I\s+IDENTYFIKACJA"
                               r"\s+PRZEDSIĘBIORSTWA", text[:heading.start()], re.IGNORECASE):
                continue
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            next_section = SECTION.search(text, heading.end())
            if next_section:
                end = min(end, next_section.start())
            return text[heading.start():end]
    return ""


def _context(text: str, alias_id: str) -> list[tuple[str, str, str]]:
    if alias_id in {"A-001", "A-002", "A-007", "A-010"}:
        return [(_subsection(text, "1.1"), "1.1", "SECTION")]
    if alias_id in {"A-003", "A-004", "A-009", "A-013"}:
        return [(_subsection(text, "1.3"), "1.3", "SECTION")]
    section = SECTION.search(text)
    header = text[:section.start()] if section else "\n".join(text.splitlines()[:30])
    footer = "\n".join(text.splitlines()[-16:])
    if alias_id == "A-005":
        return [(footer, "FOOTER", "FOOTER")]
    if alias_id in {"A-008", "A-011", "A-012"}:
        return [(header, "HEADER", "HEADER")]
    return [(header, "HEADER", "HEADER"), (footer, "FOOTER", "FOOTER")]


def _combine(results: list[MatchResult]) -> dict:
    found = [result for result in results if result.state == "FOUND"]
    if any(result.state == "AMBIGUOUS" for result in results) or len({r.value for r in found}) > 1:
        return {"value": None, "state": "AMBIGUOUS", "evidence": []}
    if any(result.state == "UNREADABLE" for result in results):
        return {"value": None, "state": "UNREADABLE", "evidence": []}
    if found:
        evidence = [proof for result in found for proof in result.evidence]
        return {"value": found[0].value, "state": "FOUND", "evidence": evidence}
    return {"value": None, "state": "NOT_FOUND", "evidence": []}


def _one_field(fields: list[dict]) -> dict:
    found = [field for field in fields if field["state"] == "FOUND"]
    if len({field["value"] for field in found}) > 1 or any(
        field["state"] == "AMBIGUOUS" for field in fields
    ):
        return {"value": None, "state": "AMBIGUOUS", "evidence": []}
    if found:
        return found[0]
    if any(field["state"] == "UNREADABLE" for field in fields):
        return {"value": None, "state": "UNREADABLE", "evidence": []}
    return {"value": None, "state": "NOT_FOUND", "evidence": []}


def _plural_product_codes(section: str, page: int) -> dict:
    """Keep plural product identifiers as evidence, never choose one Core code."""
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    for index, label in enumerate(lines):
        if not PLURAL_PRODUCT_IDS.fullmatch(label):
            continue
        source = [label]
        identifiers = []
        for line in lines[index + 1:]:
            tokens = line.split()
            if not tokens or not all(IDENTIFIER_TOKEN.fullmatch(token) for token in tokens):
                break
            identifiers.extend(tokens)
            source.append(line)
        if len(set(identifiers)) > 1:
            return {"value": None, "state": "AMBIGUOUS", "evidence": [{
                "page": page, "section": "1", "subsection": "1.1",
                "label": PLURAL_PRODUCT_IDS_LABEL, "source_text": "\n".join(source),
            }]}
    return {"value": None, "state": "NOT_FOUND", "evidence": []}


def _document(pages: list[str], start: int, end: int, ordinal: int, catalog: dict) -> dict:
    matches: dict[str, dict] = {}
    for alias_id, rule in catalog.items():
        if rule.status != "ACTIVE":
            continue
        results = []
        for page_number in (range(start, end + 1) if alias_id in {"A-001", "A-002", "A-003", "A-004", "A-007", "A-009", "A-010", "A-013"}
                            else sorted({start, end})):
            for content, section, location in _context(pages[page_number - 1], alias_id):
                if content:
                    results.append(match_active_alias(alias_id, content, page=page_number,
                                                      section=section, location=location,
                                                      catalog=catalog))
        matches[alias_id] = _combine(results)
    missing = {"value": None, "state": "NOT_FOUND", "evidence": []}
    plural_fields = [_plural_product_codes(_subsection(pages[page_number - 1], "1.1"), page_number)
                     for page_number in range(start, end + 1)]
    plural_proofs = [proof for field in plural_fields if field["state"] == "AMBIGUOUS"
                     for proof in field["evidence"]]
    plural = ({"value": None, "state": "AMBIGUOUS", "evidence": plural_proofs}
              if plural_proofs else missing)
    compound_identities = [match_compound_identity(
        _subsection(pages[page_number - 1], "1.1"), page=page_number)
        for page_number in range(start, end + 1)]
    compound_name = _combine([pair[0] for pair in compound_identities])
    compound_code = _combine([pair[1] for pair in compound_identities])
    code = plural if plural["state"] == "AMBIGUOUS" else _one_field(
        [matches["A-002"], compound_code])
    name = _one_field([matches["A-001"], matches["A-007"],
                       matches.get("A-010", missing), compound_name])
    if name["state"] == "FOUND":
        name = {**name, "value": name["value"].replace("®", "").replace("™", "")}
    card_revision = _combine([match_card_header_revision(pages[page_number - 1], page=page_number)
                              for page_number in range(start, end + 1)])
    if card_revision["state"] == "FOUND":
        card_revision["evidence"] = card_revision["evidence"][:1]
    edition_revision = _combine([match_edition_revision(pages[page_number - 1], page=page_number)
                                 for page_number in range(start, end + 1)])
    if edition_revision["state"] == "FOUND":
        edition_revision["evidence"] = edition_revision["evidence"][:1]
    english_headers = [match_english_revision_header(pages[page_number - 1], page=page_number)
                       for page_number in range(start, end + 1)]
    english_date = _combine([pair[0] for pair in english_headers])
    english_revision = _combine([pair[1] for pair in english_headers])
    for field in (english_date, english_revision):
        if field["state"] == "FOUND":
            field["evidence"] = field["evidence"][:1]
    named_roles = [result for page_number in range(start, end + 1)
                   for result in match_named_party_roles(
                       _subsection(pages[page_number - 1], "1.3"), page=page_number)]
    parties = [{"role": catalog[alias_id].role, "name": matches[alias_id]}
               for alias_id in ("A-003", "A-004", "A-009", "A-013")
               if alias_id in matches and matches[alias_id]["state"] != "NOT_FOUND"]
    parties.extend({"role": role, "name": _combine([result for result in named_roles
                                                     if result.role == role])}
                   for role in ("MANUFACTURER", "DISTRIBUTOR")
                   if any(result.role == role for result in named_roles))
    combined_supplier = _combine([match_combined_supplier(
        _subsection(pages[page_number - 1], "1.3"), page=page_number)
        for page_number in range(start, end + 1)])
    if combined_supplier["state"] != "NOT_FOUND":
        parties.append({"role": "SUPPLIER", "name": combined_supplier})
    distributor_results = [result for page_number in range(start, end + 1)
                           for result in match_distributor_blocks(
                               _subsection(pages[page_number - 1], "1.3"), page=page_number)]
    seen_distributors: set[str] = set()
    for result in distributor_results:
        if result.state == "FOUND":
            key = result.value.casefold()
            if key in seen_distributors:
                continue
            seen_distributors.add(key)
        parties.append({"role": "DISTRIBUTOR", "name": {
            "value": result.value, "state": result.state, "evidence": list(result.evidence)}})
    return {
        "document_key": f"DOC-{ordinal:03d}",
        "page_range": {"from": start, "to": end},
        "review_status": "PENDING_REVIEW",
        "product": {
            "product_name": name,
            "manufacturer_product_code": code,
        },
        "document_metadata": {
            "issue_date": _one_field([matches["A-005"], matches["A-008"], matches.get("A-011", missing), english_date]),
            "revision": _one_field([matches["A-006"], matches.get("A-012", missing),
                                    card_revision, edition_revision, english_revision]),
        },
        "parties": parties,
        "safety_profile": {},
        "components": [],
        "validation": {},
    }


def _fields(document: dict):
    for key, field in document["product"].items():
        yield key, field
    for key, field in document["document_metadata"].items():
        yield key, field
    for party in document["parties"]:
        yield "party", party["name"]


def _source_language(pages: list[str]) -> str:
    first = pages[0].casefold()
    polish = "karta charakterystyki" in first
    english = "safety data sheet" in first and bool(re.search(r"\bSECTION\s+1\b", first, re.IGNORECASE))
    if polish == english:
        return "und"
    return "pl" if polish else "en"


def validate_evidence(draft: dict, pages: list[str]) -> dict:
    """Run independent TDR-012 G1/G2/G3 checks; never approve the draft."""
    if not isinstance(draft, dict):
        return {"G1": {"status": "FAIL", "issues": ["ENVELOPE_SHAPE"]},
                "G2": {"status": "PASS", "issues": []},
                "G3": {"status": "PASS", "issues": []}}
    g1: list[str] = []
    g2: list[str] = []
    g3: list[str] = []
    if draft.get("schema") != "SDS-JSON-001" or draft.get("schema_version") != "0.1":
        g1.append("SCHEMA_VERSION")
    source = draft.get("source", {})
    if not isinstance(source, dict):
        source = {}
    if source.get("page_count") != len(pages) or not re.fullmatch(
        r"[0-9a-f]{64}", str(source.get("file_sha256", ""))
    ) or source.get("readability_status") not in {"READABLE", "PARTIALLY_READABLE", "UNREADABLE"} or not source.get(
        "original_filename"
    ) or not source.get("language"):
        g1.append("SOURCE_SHAPE")
    if source.get("readability_status") == "UNREADABLE":
        g2.append("SOURCE_UNREADABLE")
    documents = draft.get("documents", [])
    if not isinstance(documents, list) or not documents:
        g1.append("DOCUMENTS_REQUIRED")
        documents = []
    expected_start = 1
    catalog = load_catalog()
    rules_by_label = {rule.alias_text: rule for rule in catalog.values()}
    roles_by_label = {rule.alias_text: rule.role for rule in catalog.values()
                      if rule.canonical_field == "parties[].name"}
    for ordinal, doc in enumerate(documents, 1):
        prefix = f"DOC-{ordinal:03d}"
        if not isinstance(doc, dict):
            g1.append(f"{prefix}:DOCUMENT_SHAPE")
            continue
        page_range = doc.get("page_range") if isinstance(doc.get("page_range"), dict) else {}
        if doc.get("document_key") != prefix or page_range != {
            "from": expected_start, "to": page_range.get("to")
        }:
            g1.append(f"{prefix}:PAGE_RANGE_OR_KEY")
        end = page_range.get("to")
        if not isinstance(end, int) or end < expected_start or end > len(pages):
            g1.append(f"{prefix}:PAGE_END")
            end = expected_start
        if doc.get("review_status") != "PENDING_REVIEW" or not isinstance(doc.get("product"), dict) or not isinstance(
            doc.get("document_metadata"), dict
        ) or not isinstance(doc.get("parties"), list) or any(
            not isinstance(party, dict) or not isinstance(party.get("name"), dict)
            for party in doc.get("parties", []) if isinstance(doc.get("parties"), list)
        ) or doc.get("safety_profile") != {} or doc.get("components") != []:
            g1.append(f"{prefix}:DOCUMENT_SHAPE")
            continue
        if set(doc["product"]) != {"product_name", "manufacturer_product_code"} or set(
            doc["document_metadata"]
        ) != {"issue_date", "revision"}:
            g1.append(f"{prefix}:IDENTITY_FIELDS")
        for kind, field in _fields(doc):
            if not isinstance(field, dict):
                g1.append(f"{prefix}:FIELD_SHAPE")
                continue
            state = field.get("state")
            value = field.get("value")
            evidence = field.get("evidence")
            if kind == "party" and state == "FOUND" and isinstance(value, str) and (
                value.strip().casefold() in {"producent", "dystrybutor"}
            ):
                g2.append(f"{prefix}:PARTY_ROLE_WORD_AS_NAME")
            if state not in FIELD_STATES or not isinstance(evidence, list) or (
                state == "FOUND" and (value is None or not evidence)
            ) or (state != "FOUND" and value is not None) or (
                state in {"NOT_FOUND", "UNREADABLE"} and evidence
            ):
                g1.append(f"{prefix}:FIELD_STATE_EVIDENCE")
                continue
            for proof in evidence:
                if not isinstance(proof, dict):
                    g1.append(f"{prefix}:EVIDENCE_SHAPE")
                    continue
                page = proof.get("page")
                quote = proof.get("source_text")
                if not isinstance(page, int) or isinstance(page, bool) or page < expected_start or page > end:
                    g2.append(f"{prefix}:PAGE_OUTSIDE_SDS")
                    continue
                if not isinstance(quote, str) or not quote or any(
                    line.strip() not in pages[page - 1] for line in quote.splitlines() if line.strip()
                ):
                    g2.append(f"{prefix}:QUOTE_NOT_IN_PDF")
                    continue
                if proof.get("section") not in {"1", "HEADER", "FOOTER"} or (
                    proof.get("section") == "1" and proof.get("subsection") not in {"1.1", "1.3"}
                ) or not proof.get("label"):
                    g2.append(f"{prefix}:SECTION_OR_LABEL")
                expected_subsection = "1.3" if kind == "party" else (
                    "1.1" if kind in {"product_name", "manufacturer_product_code"} else None)
                if expected_subsection and proof.get("subsection") != expected_subsection:
                    g2.append(f"{prefix}:FIELD_SECTION_MISMATCH")
                if expected_subsection is None and proof.get("section") not in {"HEADER", "FOOTER"}:
                    g2.append(f"{prefix}:METADATA_LOCATION_MISMATCH")
                if state == "AMBIGUOUS" and kind == "manufacturer_product_code" and (
                    proof.get("label") == PLURAL_PRODUCT_IDS_LABEL
                ):
                    if _plural_product_codes(quote, page)["state"] != "AMBIGUOUS":
                        g2.append(f"{prefix}:PLURAL_CODE_EVIDENCE_MISMATCH")
                    continue
                if proof.get("label") in {"Trade name", "Nazwa handlowa",
                                          "Article number", "Numer artykułu"} and kind in {
                                              "product_name", "manufacturer_product_code"}:
                    confirmations = match_compound_identity(
                        _subsection(pages[page - 1], "1.1"), page=page)
                    confirmation = confirmations[0 if kind == "product_name" else 1]
                    if (confirmation.state != "FOUND" or confirmation.value != value or
                        proof not in confirmation.evidence):
                        g2.append(f"{prefix}:COMPOUND_IDENTITY_EVIDENCE_MISMATCH")
                    continue
                if kind == "revision" and proof.get("label") == "V":
                    confirmation = match_card_header_revision(pages[page - 1], page=page)
                    if (proof.get("section") != "HEADER" or
                        confirmation.state != "FOUND" or confirmation.value != value or
                        proof not in confirmation.evidence):
                        g2.append(f"{prefix}:CARD_REVISION_EVIDENCE_MISMATCH")
                    continue
                if kind == "revision" and proof.get("label") == "Edycja":
                    confirmation = match_edition_revision(pages[page - 1], page=page)
                    if (proof.get("section") != "HEADER" or
                        confirmation.state != "FOUND" or confirmation.value != value or
                        proof not in confirmation.evidence):
                        g2.append(f"{prefix}:EDITION_EVIDENCE_MISMATCH")
                    continue
                if proof.get("label") in {"Revision", "Version"} and kind in {"issue_date", "revision"}:
                    confirmations = match_english_revision_header(pages[page - 1], page=page)
                    confirmation = confirmations[0 if kind == "issue_date" else 1]
                    if (proof.get("section") != "HEADER" or
                        confirmation.state != "FOUND" or confirmation.value != value or
                        proof not in confirmation.evidence):
                        g2.append(f"{prefix}:ENGLISH_HEADER_EVIDENCE_MISMATCH")
                    continue
                if kind == "party" and proof.get("label") in {
                    "Manufacturer/Supplier", "Producent/Dostawcy"
                }:
                    confirmation = match_combined_supplier(
                        _subsection(pages[page - 1], "1.3"), page=page)
                    if (confirmation.state != "FOUND" or confirmation.value != value or
                        proof not in confirmation.evidence):
                        g2.append(f"{prefix}:COMBINED_SUPPLIER_EVIDENCE_MISMATCH")
                    continue
                if kind == "party" and proof.get("label") == "Identyfikacja dystrybutora":
                    confirmations = match_distributor_blocks(
                        _subsection(pages[page - 1], "1.3"), page=page)
                    if not any(result.state == state and result.value == value and
                               proof in result.evidence for result in confirmations):
                        g2.append(f"{prefix}:DISTRIBUTOR_EVIDENCE_MISMATCH")
                    continue
                if kind == "party" and proof.get("label") in {"Producent", "Dystrybutor"}:
                    confirmations = match_named_party_roles(
                        _subsection(pages[page - 1], "1.3"), page=page)
                    if not any(result.state == "FOUND" and result.value == value and
                               proof in result.evidence for result in confirmations):
                        g2.append(f"{prefix}:NAMED_PARTY_EVIDENCE_MISMATCH")
                    continue
                rule = rules_by_label.get(proof.get("label"))
                expected_field = "parties[].name" if kind == "party" else (
                    f"product.{kind}" if kind in {"product_name", "manufacturer_product_code"}
                    else f"document_metadata.{kind}")
                if rule is None or rule.canonical_field != expected_field:
                    g2.append(f"{prefix}:UNAPPROVED_EVIDENCE_LABEL")
                elif rule.binding == "supplier_next_line":
                    if not isinstance(value, str) or value not in quote:
                        g2.append(f"{prefix}:VALUE_NOT_SUPPORTED")
                else:
                    section = proof.get("subsection") or proof.get("section")
                    location = "SECTION" if proof.get("subsection") else proof.get("section")
                    confirmation = match_active_alias(rule.alias_id, quote, page=page,
                                                      section=section, location=location,
                                                      catalog=catalog)
                    confirmed_value = confirmation.value
                    if kind == "product_name" and isinstance(confirmed_value, str):
                        confirmed_value = confirmed_value.replace("®", "").replace("™", "")
                    if confirmation.state != "FOUND" or confirmed_value != value:
                        g2.append(f"{prefix}:VALUE_NOT_SUPPORTED")
        roles = [party.get("role") for party in doc["parties"]]
        found_pairs = [(party.get("role"), party["name"].get("value", "").strip().casefold())
                       for party in doc["parties"] if party["name"].get("state") == "FOUND"
                       and isinstance(party["name"].get("value"), str)]
        if any(role not in PARTY_ROLES for role in roles) or len(found_pairs) != len(set(found_pairs)):
            g3.append(f"{prefix}:INVALID_OR_DUPLICATE_ROLE")
        for party in doc["parties"]:
            if party["name"].get("state") == "FOUND" and any(
                ({"Producent": "MANUFACTURER", "Dystrybutor": "DISTRIBUTOR",
                  "Manufacturer/Supplier": "SUPPLIER", "Producent/Dostawcy": "SUPPLIER",
                  "Identyfikacja dystrybutora": "DISTRIBUTOR"}.get(
                    proof.get("label"), roles_by_label.get(proof.get("label"))) != party.get("role"))
                for proof in party["name"].get("evidence", [])
            ):
                g3.append(f"{prefix}:ROLE_EVIDENCE_MISMATCH")
        if any(party.get("role") == "DISTRIBUTOR" and party["name"].get("state") == "AMBIGUOUS"
               for party in doc["parties"]):
            g3.append(f"{prefix}:DISTRIBUTOR_IDENTITY_AMBIGUOUS")
        # Roles are evidence only; never infer a Core manufacturer from a
        # supplier, representative, distributor, or combined exporter role.
        if not any(party.get("role") == "MANUFACTURER" and party["name"].get("state") == "FOUND"
                   for party in doc["parties"]):
            g3.append(f"{prefix}:MANUFACTURER_REQUIRES_HUMAN_REVIEW")
        if doc["product"]["manufacturer_product_code"]["state"] == "AMBIGUOUS":
            g3.append(f"{prefix}:MANUFACTURER_PRODUCT_CODE_AMBIGUOUS")
        expected_start = end + 1
    if expected_start != len(pages) + 1:
        g1.append("PAGE_COVERAGE")
    extraction_report = draft.get("extraction_report") if isinstance(draft.get("extraction_report"), dict) else {}
    if extraction_report.get("logical_sds_count") != len(documents):
        g1.append("LOGICAL_SDS_COUNT")
    return {"G1": {"status": "FAIL" if g1 else "PASS", "issues": g1},
            "G2": {"status": "FAIL" if g2 else "PASS", "issues": g2},
            "G3": {"status": "FAIL" if any("INVALID" in issue or "MISMATCH" in issue for issue in g3) else "PASS",
                   "issues": g3}}


def extract_evidence(path: Path) -> tuple[dict, dict]:
    pages, sha256, readability = _read_pdf(path)
    catalog = load_catalog()
    if any(catalog.get(f"A-{number:03d}") is None or catalog[f"A-{number:03d}"].status != "ACTIVE"
           for number in range(1, 14)):
        raise ValueError("TASK-062-R5 ACTIVE alias catalog is required")
    ranges = _ranges(pages)
    draft = {
        "schema": "SDS-JSON-001", "schema_version": "0.1",
        "source": {"original_filename": path.name, "file_sha256": sha256,
                   "page_count": len(pages), "language": _source_language(pages),
                   "readability_status": readability},
        "documents": [_document(pages, start, end, index, catalog)
                      for index, (start, end) in enumerate(ranges, 1)],
        "extraction_report": {"logical_sds_count": len(ranges), "warnings": [], "errors": []},
    }
    gates = validate_evidence(draft, pages)
    for doc in draft["documents"]:
        doc["validation"] = {
            "status": "BLOCKED" if any(gate["status"] == "FAIL" for gate in gates.values())
            else "REQUIRES_HUMAN_REVIEW",
            "issues": [{"code": issue, "message": issue.replace("_", " ")}
                       for issue in gates["G3"]["issues"] if doc["document_key"] in issue],
        }
    draft["extraction_report"]["warnings"] = gates["G3"]["issues"] + (
        ["SOURCE_PARTIALLY_READABLE"] if readability == "PARTIALLY_READABLE" else [])
    draft["extraction_report"]["errors"] = gates["G1"]["issues"] + gates["G2"]["issues"]
    return draft, gates
