"""Minimal text-layer SDS extraction using pypdf."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from app.application.dto import (
    ExtractedSdsData,
    SdsComponentDraft,
    SdsSafetyProfileDraft,
)
from app.application.ports import SdsExtractorPort
from app.domain.enums import SafetyInformationStatus


class SdsPdfExtractionError(ValueError):
    """The PDF cannot provide a usable text layer."""


class PdfSdsExtractor(SdsExtractorPort):
    def extract(self, pdf_path: Path) -> ExtractedSdsData:
        if not pdf_path.is_file():
            raise SdsPdfExtractionError(f"SDS PDF does not exist: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise SdsPdfExtractionError(f"SDS file is not a PDF: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("SDS PDF requires a password")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as error:
            raise SdsPdfExtractionError(f"Could not read SDS PDF: {pdf_path}") from error

        text = _clean_text(text)
        if not text:
            raise SdsPdfExtractionError(
                f"SDS PDF has no readable text layer: {pdf_path}"
            )

        section_1 = _section(text, 1)
        section_2 = _section(text, 2)
        section_3 = _section(text, 3)
        section_11 = _section(text, 11)
        product_name = _product_name(text)

        return ExtractedSdsData(
            product_name=product_name,
            manufacturer_product_code=_first_match(
                r"(?m)^([0-9A-Za-z][0-9A-Za-z./-]{2,})$", section_1
            ),
            manufacturer_name=None,
            use_description=_first_present(
                section_1,
                "Farba lub inna podobna substancja.",
                "Paint or similar material.",
            ),
            use_restriction=_first_present(
                section_1,
                "Jedynie do stosowania przemysłowego.",
                "For industrial use only.",
            ),
            issue_date=_issue_date(text),
            revision=_first_match(r"Wersja\s*:\s*([0-9]+(?:\.[0-9]+)?)", text),
            detected_language="PL" if _looks_polish(text) else None,
            language_valid=True if _looks_polish(text) else None,
            safety_profile=_safety_profile(section_2, section_11),
            components=_components(section_3),
        )


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _section(text: str, number: int) -> str:
    start_match = re.search(rf"(?m)^SEKCJA {number}:.*$", text)
    if start_match is None:
        return ""
    end_match = re.search(r"(?m)^SEKCJA \d+:.*$", text[start_match.end() :])
    end = start_match.end() + end_match.start() if end_match else len(text)
    return text[start_match.end() : end]


def _product_name(text: str) -> str | None:
    before_header = text.split("KARTA CHARAKTERYSTYKI", 1)[0]
    lines = [line.strip() for line in before_header.splitlines() if line.strip()]
    return lines[0] if lines else None


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        return None
    return match.group(1).strip() if match.lastindex else match.group(0).strip()


def _first_present(text: str, *values: str) -> str | None:
    for value in values:
        if value in text:
            return value
    return None


def _issue_date(text: str) -> date | None:
    match = re.search(
        r"Data wydania/Data aktualizacji\s*:\s*([0-9]{1,2}),\s*([A-Za-ząćęłńóśźż]+),\s*([0-9]{4})",
        text,
        re.IGNORECASE,
    )
    if match is None:
        return None
    months = {
        "styczeń": 1,
        "stycznia": 1,
        "luty": 2,
        "lutego": 2,
        "marzec": 3,
        "marca": 3,
        "kwiecień": 4,
        "kwietnia": 4,
        "maj": 5,
        "maja": 5,
        "czerwiec": 6,
        "czerwca": 6,
        "lipiec": 7,
        "lipca": 7,
        "sierpień": 8,
        "sierpnia": 8,
        "wrzesień": 9,
        "września": 9,
        "październik": 10,
        "października": 10,
        "listopad": 11,
        "listopada": 11,
        "grudzień": 12,
        "grudnia": 12,
    }
    month = months.get(match.group(2).lower())
    return date(int(match.group(3)), month, int(match.group(1))) if month else None


def _looks_polish(text: str) -> bool:
    return "KARTA CHARAKTERYSTYKI" in text and "SEKCJA 1:" in text


def _safety_profile(section_2: str, section_11: str) -> SdsSafetyProfileDraft:
    not_classified = "nie został sklasyfikowany" in section_2.lower()
    return SdsSafetyProfileDraft(
        product_definition=_first_match(r"Definicja produktu\s*:\s*(.+)", section_2),
        hazardous_classification_status=(
            SafetyInformationStatus.NO if not_classified else None
        ),
        clp_classification_text=_first_match(
            r"Klasyfikacja[^\n]*:\s*(.+)", section_2
        ),
        signal_word=_first_match(r"Hasło ostrzegawcze\s*:\s*(.+)", section_2),
        hazard_statements=_h_codes(section_2),
        supplemental_hazard_statements=[],
        pbt_status=SafetyInformationStatus.NO_DATA,
        vpvb_status=SafetyInformationStatus.NO_DATA,
        endocrine_section_2_status=SafetyInformationStatus.NO_DATA,
        carcinogenicity_status=SafetyInformationStatus.NO_DATA,
        germ_cell_mutagenicity_status=SafetyInformationStatus.NO_DATA,
        reproductive_toxicity_status=SafetyInformationStatus.NO_DATA,
        endocrine_section_11_status=SafetyInformationStatus.NO_DATA,
        skin_sensitization_status=SafetyInformationStatus.NO_DATA,
        respiratory_sensitization_status=SafetyInformationStatus.NO_DATA,
    )


def _h_codes(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\bH[0-9]{3}\b", text)))


def _components(section_3: str) -> list[SdsComponentDraft]:
    components: list[SdsComponentDraft] = []
    cas_matches = list(re.finditer(r"CAS:\s*([0-9-]+)", section_3))
    previous_end = 0
    for match in cas_matches:
        record_prefix = section_3[previous_end : match.start()]
        markers = list(re.finditer(r"(?:REACH #|WE):", record_prefix))
        marker = markers[0] if markers else None
        name_prefix = record_prefix[: marker.start()] if marker else record_prefix
        name = _component_name(name_prefix)
        component_start = match.start()
        next_marker = re.search(r"(?:REACH #|WE):", section_3[match.end() :])
        component_end = (
            match.end() + next_marker.start() if next_marker else len(section_3)
        )
        component_text = section_3[component_start:component_end]
        identifiers = record_prefix[marker.start() :] if marker else record_prefix
        components.append(
            SdsComponentDraft(
                component_name=name,
                cas_number=match.group(1),
                ec_number=_first_match(r"WE:\s*([0-9-]+)", identifiers),
                reach_registration_number=_first_match(
                    r"REACH #:\s*([0-9-]+)", identifiers
                ),
                concentration_text=_first_match(
                    r"(?m)^(<|≤|≥)?[0-9]+(?:\.[0-9]+)?(?:\s*-\s*(?:<|≤|≥)?[0-9]+)?$",
                    component_text,
                ),
                classification_text=_classification_text(component_text),
                hazard_statements=_h_codes(component_text),
            )
        )
        previous_end = match.end()
    return components


def _component_name(prefix: str) -> str | None:
    lines = [line.strip() for line in prefix.splitlines() if line.strip()]
    if not lines:
        return None
    excluded = {"Nazwa produktu/", "składnika", "Identyfikatory", "%"}
    names = [line for line in lines if line not in excluded]
    if "czynniki M i ATE" in names:
        names = names[names.index("czynniki M i ATE") + 1 :]
    for index, line in enumerate(names):
        if "Nie sklasyfikowany" in line:
            names = names[index + 1 :]
    return " ".join(names[-3:]).strip() or None


def _classification_text(text: str) -> str | None:
    lines = [line for line in text.splitlines() if "H" in line or "Tox." in line]
    return " ".join(lines) if lines else None
