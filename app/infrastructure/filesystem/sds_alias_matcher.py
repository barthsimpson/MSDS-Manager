"""Small, local label/value matcher for the approved SDS-ALIAS-001 rules.

The caller supplies text from one verified section, header, or footer of one
logical SDS. PDF reading, document segmentation, and Evidence JSON belong to
the later TDR-012 pipeline, not to this module.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATALOG_PATH = Path(__file__).resolve().parents[3] / "config" / "sds_aliases.json"
STATES = frozenset({"CANDIDATE", "APPROVED", "ACTIVE", "REJECTED"})
PARTY_ROLES = frozenset({"MANUFACTURER_EXPORTER", "EU_REPRESENTATIVE", "SUPPLIER"})
POLISH_MONTHS = {
    "styczen": 1, "stycznia": 1, "luty": 2, "lutego": 2,
    "marzec": 3, "marca": 3, "kwiecien": 4, "kwietnia": 4,
    "maj": 5, "maja": 5, "czerwiec": 6, "cze": 6, "czerwca": 6,
    "lipiec": 7, "lipca": 7, "sierpien": 8, "sierpnia": 8,
    "wrzesien": 9, "wrzesnia": 9, "pazdziernik": 10, "pazdziernika": 10,
    "listopad": 11, "listopada": 11, "grudzien": 12, "grudnia": 12,
}
POLISH_FOLD = str.maketrans("ąćęłńóśźż", "acelnoszz")


class InactiveAliasError(ValueError):
    """An alias not yet ACTIVE cannot be used by runtime code."""


@dataclass(frozen=True)
class AliasRule:
    alias_id: str
    alias_text: str
    canonical_field: str
    canonical_section: str | None
    role: str
    location: str
    binding: str
    status: str
    source_document: str


@dataclass(frozen=True)
class MatchResult:
    alias_id: str
    canonical_field: str
    role: str
    value: str | None
    state: str
    evidence: tuple[dict[str, str | int | None], ...] = ()
    observed_text: str | None = None


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, AliasRule]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "SDS-ALIAS-001" or payload.get("schema_version") != "1.0":
        raise ValueError("Unsupported SDS alias catalog")
    rules = [AliasRule(**entry) for entry in payload["aliases"]]
    if len({rule.alias_id for rule in rules}) != len(rules):
        raise ValueError("Duplicate alias ID")
    for rule in rules:
        if rule.status not in STATES:
            raise ValueError(f"Invalid status for {rule.alias_id}")
        if rule.canonical_field == "parties[].name" and rule.role not in PARTY_ROLES:
            raise ValueError(f"Invalid party role for {rule.alias_id}")
    return {rule.alias_id: rule for rule in rules}


def match_active_alias(
    alias_id: str, text: str, *, page: int, section: str, location: str,
    catalog: dict[str, AliasRule] | None = None,
) -> MatchResult:
    rule = (catalog or load_catalog())[alias_id]
    if rule.status != "ACTIVE":
        raise InactiveAliasError(f"{alias_id} is {rule.status}, not ACTIVE")
    return evaluate_binding(rule, text, page=page, section=section, location=location)


def evaluate_binding(
    rule: AliasRule, text: str, *, page: int, section: str, location: str,
) -> MatchResult:
    """Regression probe for APPROVED rules; not a production bypass for status."""
    if page < 1:
        raise ValueError("Evidence page must be positive")
    empty = MatchResult(rule.alias_id, rule.canonical_field, rule.role, None, "NOT_FOUND")
    if rule.canonical_section is not None and section != rule.canonical_section:
        return empty
    if rule.canonical_section is None and section != location:
        return empty
    if rule.location != "HEADER_OR_FOOTER" and location != rule.location:
        return empty
    if rule.location == "HEADER_OR_FOOTER" and location not in {"HEADER", "FOOTER"}:
        return empty
    if rule.binding == "supplier_next_line" and "dostawcy karty charakterystyki" not in text.lower():
        return empty

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if rule.binding == "section_next_line_name":
        heading = re.compile(r"1\.1\.?\s+" + r"\s+".join(map(re.escape, rule.alias_text.split())) + r"\s*$",
                             re.IGNORECASE)
        candidates = []
        for index, line in enumerate(lines):
            if not heading.fullmatch(line):
                continue
            raw = lines[index + 1] if index + 1 < len(lines) else ""
            if re.match(r"(?:1\.[2-4]\b|Numery\b|Nazwa\s+(?:produktu|wyrobu)\s*:)", raw, re.IGNORECASE):
                continue
            candidates.append((raw or None, line + "\n" + raw, raw))
        return _finish_candidates(rule, candidates, page, location)
    if rule.binding == "supplier_address_line":
        heading = re.compile(r"1\.3\.?\s+" + r"\s+".join(map(re.escape, rule.alias_text.split())) + r"\s*$",
                             re.IGNORECASE)
        headings = [index for index, line in enumerate(lines) if heading.fullmatch(line)]
        if not headings:
            return empty
        candidates = []
        for line in lines:
            address = re.fullmatch(r"Adres:\s*(.+)", line, re.IGNORECASE)
            if address is None:
                continue
            street = re.search(r"\s+(?:ul\.|al\.|pl\.|os\.|aleja\b|ulica\b)", address.group(1), re.IGNORECASE)
            value = address.group(1)[:street.start()].strip(" ,;") if street else None
            short_address = line[:address.start(1) + street.end()].rstrip() if street else line
            candidates.append((value, lines[headings[0]] + "\n" + short_address,
                               address.group(1)))
        if not candidates:
            for index in headings:
                raw = lines[index + 1] if index + 1 < len(lines) else ""
                if not raw:
                    continue
                if re.fullmatch(r"IDENTYFIKACJA\s+FIRMY", raw, re.IGNORECASE):
                    # A-009 owns this supplier block.
                    continue
                # The next line is a supplier only when it is a name, not an
                # address, contact detail, subsection, or copyright notice.
                if (re.search(r"\d|[@:]|\bwww\.|\b(?:Str\.|Street\b|Straße\b)",
                              raw, re.IGNORECASE)
                    or re.match(r"(?:1\.[1-4]\b|SEKCJA\b|Adres\b|ul\.|al\.|pl\.|os\."
                                r"|Phone\b|Fax\b|Tel\b|Telefon\b|Internet\b|E-?mail\b"
                                r"|Numer\b|Copyright\b|Prawa autorskie\b)", raw, re.IGNORECASE)):
                    candidates.append((None, lines[index] + "\n" + raw, raw))
                    continue
                candidates.append((raw, lines[index] + "\n" + raw, raw))
        return _finish_candidates(rule, candidates, page, location)
    suffix = r"\s*$" if rule.binding == "supplier_next_line" else r"\s*:\s*(.*)"
    label = r"\s+".join(map(re.escape, rule.alias_text.split()))
    pattern = re.compile(r"(?<!\w)" + label + suffix, re.IGNORECASE)
    candidates: list[tuple[str | None, str, str]] = []
    for index, line in enumerate(lines):
        match = pattern.search(line)
        if match is None:
            continue
        if rule.alias_id == "A-008" and re.search(r"\bData\s+$", line[:match.start()], re.IGNORECASE):
            # "Data aktualizacji" is a different label from the approved
            # SYLGARD header label "Aktualizacja".
            continue
        raw = match.group(1).strip() if rule.binding != "supplier_next_line" else ""
        source = line
        if rule.binding in {"next_line", "supplier_next_line"}:
            raw = lines[index + 1] if index + 1 < len(lines) else ""
            source = line + "\n" + raw
            if not raw or re.match(r"\d|(?:SEKCJA|Phone|Numer telefonu)\b", raw, re.IGNORECASE):
                raw = ""
        value = _bind_value(rule.binding, raw)
        candidates.append((value, source, raw))
    return _finish_candidates(rule, candidates, page, location)


def _finish_candidates(rule: AliasRule, candidates: list[tuple[str | None, str, str]],
                       page: int, location: str) -> MatchResult:
    if not candidates:
        return MatchResult(rule.alias_id, rule.canonical_field, rule.role, None, "NOT_FOUND")
    if (candidates[0][0] is None or
        (len(candidates) != 1 and (rule.binding != "version" or
                                   any(item[0] != candidates[0][0] for item in candidates[1:])))):
        return MatchResult(rule.alias_id, rule.canonical_field, rule.role, None, "AMBIGUOUS",
                           observed_text="\n".join(item[1] for item in candidates))

    # For identical revision repeats, the last occurrence is the page footer.
    value, source, raw = candidates[-1]
    if "�" in raw:
        return MatchResult(rule.alias_id, rule.canonical_field, rule.role, None, "UNREADABLE",
                           observed_text=source)
    proof = {
        "page": page,
        "section": "1" if rule.canonical_section else location,
        "subsection": rule.canonical_section,
        "label": rule.alias_text,
        "source_text": source,
    }
    return MatchResult(rule.alias_id, rule.canonical_field, rule.role, value, "FOUND", (proof,))


def _bind_value(binding: str, raw: str) -> str | None:
    if binding in {"same_line", "next_line", "supplier_next_line"}:
        return raw or None
    if binding == "version":
        match = re.match(r"([0-9]+(?:\.[0-9]+)?)(?=\s|$)", raw)
        return match.group(1) if match else None
    if binding == "iso_slash_date":
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", raw):
            return None
        try:
            return date.fromisoformat(raw.replace("/", "-")).isoformat()
        except ValueError:
            return None
    if binding == "dmy_current_date":
        match = re.match(r"(\d{2})/(\d{2})/(\d{4})(?=\s|$)", raw)
        if match is None:
            return None
        try:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
        except ValueError:
            return None
    if binding == "polish_current_date":
        current = re.split(r"\s+Data poprzedniego\b", raw, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        match = re.fullmatch(r"(\d{1,2}),\s*([A-Za-ząćęłńóśźż]+),\s*(\d{4})", current, re.IGNORECASE)
        if match is None:
            numeric = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", current)
            if numeric is None:
                return None
            first, second, year = map(int, numeric.groups())
            day_month = _valid_date(year, second, first)
            month_day = _valid_date(year, first, second)
            if day_month is None and month_day is None:
                return None
            if day_month is None:
                return month_day
            if month_day is None:
                return day_month
            # A neighboring, unequivocal date can establish the source format.
            previous = re.search(r"\bData poprzedniego(?: wydania)?\s*:\s*"
                                 r"(\d{1,2})/(\d{1,2})/(\d{4})", raw, re.IGNORECASE)
            if previous:
                peer_first, peer_second, peer_year = map(int, previous.groups())
                peer_day_month = _valid_date(peer_year, peer_second, peer_first)
                peer_month_day = _valid_date(peer_year, peer_first, peer_second)
                if peer_day_month is None and peer_month_day is not None:
                    return month_day
                if peer_month_day is None and peer_day_month is not None:
                    return day_month
            return day_month  # Approved Polish default when the source is silent.
        month = POLISH_MONTHS.get(match.group(2).lower().translate(POLISH_FOLD))
        if month is None:
            return None
        try:
            return date(int(match.group(3)), month, int(match.group(1))).isoformat()
        except ValueError:
            return None
    raise ValueError(f"Unsupported binding: {binding}")


def _valid_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None
