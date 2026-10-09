# BATCH-001_CX — Golden Data: decyzje B001-Q001–Q005

**Status:** 5/5 RESOLVED przez człowieka. Artefakt referencyjny dla rozstrzygniętych pól sekcji 1.3; pozostałe pola i całe SDS pozostają Evidence JSON DRAFT z `review_status=PENDING_REVIEW`.

| Issue ID | Source PDF | Page / section | Raw source value | Human-approved canonical result | Expected JSON result | Status |
|---|---|---|---|---|---|---|
| B001-Q001 | cx80 BONDICX rew03 05.02.2025.pdf | 1 / 1.3 | `CX80 POLSKA, CX80 GmbH` | Jeden `MANUFACTURER`: `CX80 POLSKA` | `parties[0].role=MANUFACTURER`; `parties[0].name.value="CX80 POLSKA"`; `state=FOUND`; pełny literal w `evidence.source_text` | RESOLVED |
| B001-Q002 | Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf | 1 / 1.3 | `CX80 POLSKA, CX80 GmbH` | Jeden `MANUFACTURER`: `CX80 POLSKA` | `parties[0].role=MANUFACTURER`; `parties[0].name.value="CX80 POLSKA"`; `state=FOUND`; pełny literal w `evidence.source_text` | RESOLVED |
| B001-Q003 | CX80_ Uszczelniacz niebieski A_rew01_06082025.pdf | 1 / 1.3 | `CX80 POLSKA, CX80 GmbH` | Jeden `MANUFACTURER`: `CX80 POLSKA` | `parties[0].role=MANUFACTURER`; `parties[0].name.value="CX80 POLSKA"`; `state=FOUND`; pełny literal w `evidence.source_text` | RESOLVED |
| B001-Q004 | CX80_ Uszczelniacz niebieski B_rew01_15052025.pdf | 1 / 1.3 | `CX80 POLSKA, CX80 GmbH` | Jeden `MANUFACTURER`: `CX80 POLSKA` | `parties[0].role=MANUFACTURER`; `parties[0].name.value="CX80 POLSKA"`; `state=FOUND`; pełny literal w `evidence.source_text` | RESOLVED |
| B001-Q005 | ON RUST 30.01.2019 rew. 2.0.pdf | 1 / 1.3 | Producent: `CX80 POLSKA AGATA NADERA` / `DARIUSZ NADERA SPÓŁKA` / `KOMANDYTOWA`; Wyłączny przedstawiciel: `SBLCore s.r.o.` | `MANUFACTURER = CX80 POLSKA`; `OTHER = SBLCore s.r.o.` | `parties[0].role=MANUFACTURER`, `name.value="CX80 POLSKA"`, `state=FOUND`; `parties[1].role=OTHER`, `name.value="SBLCore s.r.o."`, `state=FOUND`; oba literalne zapisy w odpowiednich `evidence.source_text` | RESOLVED |

## Wzorzec oczekiwany dla B001-Q001–Q004

W każdym z czterech JSON pozostaje dokładnie jeden rekord `MANUFACTURER`. Kontrakt `SDS-JSON-001` nie ma osobnego pola na wartość kanoniczną; decyzję człowieka zapisano w istniejącym `name.value`. Przykład odpowiadający [B001-P019](json/B001-P019_DOC-001.json):

```json
{
  "role": "MANUFACTURER",
  "name": {
    "value": "CX80 POLSKA",
    "state": "FOUND",
    "evidence": [
      {
        "page": 1,
        "section": "1",
        "subsection": "1.3",
        "label": "Producent",
        "source_text": "Producent\nNazwa lub nazwa handlowa CX80 POLSKA, CX80 GmbH"
      }
    ]
  }
}
```

## Wzorzec oczekiwany dla B001-Q005

[B001-P034](json/B001-P034_DOC-001.json) zachowuje dwa różne podmioty i dwie różne role. Nazwa producenta jest zatwierdzona kanonicznie jako `CX80 POLSKA`, a pełne brzmienie z SDS pozostaje w `evidence.source_text`. `SBLCore s.r.o.` ma rolę `OTHER` i własny dowód źródłowy:

```json
[
  {
    "role": "MANUFACTURER",
    "name": {
      "value": "CX80 POLSKA",
      "state": "FOUND",
      "evidence": [
        {
          "page": 1,
          "section": "1",
          "subsection": "1.3",
          "label": "Producent",
          "source_text": "Producent\nNazwa lub nazwa handlowa CX80 POLSKA AGATA NADERA\nDARIUSZ NADERA SPÓŁKA\nKOMANDYTOWA"
        }
      ]
    }
  },
  {
    "role": "OTHER",
    "name": {
      "value": "SBLCore s.r.o.",
      "state": "FOUND",
      "evidence": [
        {
          "page": 1,
          "section": "1",
          "subsection": "1.3",
          "label": "Wyłączny przedstawiciel",
          "source_text": "Wyłączny przedstawiciel\nNazwa lub nazwa handlowa SBLCore s.r.o."
        }
      ]
    }
  }
]
```

## Reguła referencyjna i obserwacja

`Wyłączny przedstawiciel` nie oznacza automatycznie `EU_REPRESENTATIVE`. Takie mapowanie wymaga jawnego kontekstu UE w źródle, np. `EU Only Representative`, `Przedstawiciel w UE` lub `Wyłączny przedstawiciel w UE`.

Obserwacja do późniejszej decyzji architektonicznej:

```text
RAW PARTY NAME → HUMAN-APPROVED CANONICAL PARTY
"CX80 POLSKA, CX80 GmbH" → "CX80 POLSKA"
"CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA" → "CX80 POLSKA"
```

Nie utworzono automatycznej biblioteki normalizacji podmiotów ani nie zmieniono `SDS-SCHEMA-001`, `SDS-ALIAS-001` lub `SDS-JSON-001`. Nie wykonano importu do MSDS Manager.
