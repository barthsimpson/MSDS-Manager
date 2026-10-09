# SDS-JSON-001 — Kontrakt pliku pośredniego Evidence JSON DRAFT

**Projekt:** MSDS Manager  
**Dokument:** SDS-JSON-001  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-09  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — projektowanie i kontrola, poza runtime aplikacji  
**Podstawa:** SDS-SCHEMA-001, SDS-ALIAS-001 v1.0-approved, BDR-005, CORE-001  

---

## 1. Cel

Dokument definiuje kanoniczny plik pośredni pomiędzy autonomicznym modułem odczytu SDS a MSDS Managerem.

Docelowy przepływ:

```text
PDF SDS
→ parser / extractor
→ SDS-SCHEMA + SDS-ALIAS + przyszłe SDS-LAYOUT
→ Evidence JSON DRAFT
→ walidator
→ HUMAN REVIEW
→ Application use case
→ PostgreSQL
```

JSON jest artefaktem roboczym i dowodowym. Samo jego utworzenie NIE oznacza akceptacji danych ani autoryzacji zapisu do Core.

---

## 2. Zasady nadrzędne

### 2.1. Brak LLM w runtime

```text
runtime extractora / importera
→ bez LLM
→ bez Work
→ bez Cerberusa
→ bez zewnętrznej usługi AI
```

### 2.2. Każda wartość musi posiadać źródło

```text
NO SOURCE EVIDENCE
→ NO IMPORTABLE VALUE
```

### 2.3. Brak danych nie oznacza odpowiedzi negatywnej

```text
NOT_FOUND / AMBIGUOUS / UNREADABLE
≠
NO
```

### 2.4. Brak confidence score

Kontrakt nie zawiera procentowej „pewności” extractora.

Zamiast niej stosowane są jawne stany ekstrakcji i dowody źródłowe.

### 2.5. Jeden PDF może zawierać wiele logicznych kart SDS

Kontrakt MUSI obsługiwać:

```text
1 source PDF
→ 1..N logical SDS documents
```

Każdy logiczny SDS otrzymuje własny zakres stron oraz własne dane produktu, daty i rewizji.

---

## 3. Stany ekstrakcji pola

Dozwolone stany warstwy roboczej:

```text
FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE
```

Znaczenie:

- `FOUND` — wartość odczytana i posiada dowód źródłowy,
- `NOT_FOUND` — parser odczytał właściwy obszar, ale wartości nie znalazł,
- `AMBIGUOUS` — istnieje więcej niż jedna sensowna interpretacja,
- `UNREADABLE` — właściwego obszaru nie dało się wiarygodnie odczytać.

Tylko `FOUND` może przenosić wartość jako kandydat do importu.

---

## 4. Minimalny model dowodu pola

Każde pole ekstrakcyjne ma postać logicznie równoważną:

```json
{
  "value": "...",
  "state": "FOUND",
  "evidence": [
    {
      "page": 1,
      "section": "1",
      "subsection": "1.1",
      "label": "Nazwa produktu",
      "source_text": "..."
    }
  ]
}
```

Dla pola nieodczytanego:

```json
{
  "value": null,
  "state": "UNREADABLE",
  "evidence": []
}
```

`source_text` powinien być możliwie krótkim fragmentem pozwalającym człowiekowi zweryfikować wartość, a nie pełną kopią sekcji SDS.

---

## 5. Koperta pliku JSON

Minimalna struktura pliku:

```json
{
  "schema": "SDS-JSON-001",
  "schema_version": "0.1",
  "source": {},
  "documents": [],
  "extraction_report": {}
}
```

---

## 6. `source` — dane pliku źródłowego

```json
{
  "source": {
    "original_filename": "example.pdf",
    "file_sha256": "...",
    "page_count": 25,
    "language": "pl",
    "readability_status": "READABLE"
  }
}
```

Dozwolone `readability_status`:

```text
READABLE
PARTIALLY_READABLE
UNREADABLE
```

`original_filename` identyfikuje plik, ale NIE jest źródłem prawdy dla produktu, daty ani rewizji.

`file_sha256` służy identyfikowalności konkretnego pliku wejściowego; nie stanowi automatycznej reguły deduplikacji biznesowej.

---

## 7. `documents[]` — logiczne karty SDS w pliku

Każdy element reprezentuje jedną logiczną kartę SDS.

Minimalna struktura:

```json
{
  "document_key": "DOC-001",
  "page_range": {
    "from": 1,
    "to": 25
  },
  "review_status": "PENDING_REVIEW",
  "product": {},
  "document_metadata": {},
  "parties": [],
  "safety_profile": {},
  "components": [],
  "validation": {}
}
```

`document_key` jest identyfikatorem roboczym w JSON, a nie `sds_id` z Core.

Dozwolone `review_status`:

```text
PENDING_REVIEW
APPROVED
REJECTED
```

Extractor zawsze tworzy `PENDING_REVIEW`.

Zmiana na `APPROVED` lub `REJECTED` wymaga świadomej decyzji człowieka.

---

## 8. `product` — dane identyfikacyjne produktu

Minimalny model:

```json
{
  "product": {
    "product_name": {
      "value": "OPEX® Acrylic Clear Metal Lacquer",
      "state": "FOUND",
      "evidence": []
    },
    "manufacturer_product_code": {
      "value": "T82C13",
      "state": "FOUND",
      "evidence": []
    }
  }
}
```

Dane te są kandydatem do ustalenia tożsamości PRODUCT.

Extractor NIE rozstrzyga samodzielnie:

```text
NEW PRODUCT
EXISTING PRODUCT
NEW REVISION
```

Takie rozstrzygnięcie należy do walidacji względem MSDS Managera i weryfikacji użytkownika.

---

## 9. `document_metadata` — metadane SDS

```json
{
  "document_metadata": {
    "issue_date": {
      "value": "2022-11-25",
      "state": "FOUND",
      "evidence": []
    },
    "revision": {
      "value": "8",
      "state": "FOUND",
      "evidence": []
    }
  }
}
```

Data i rewizja muszą pochodzić z treści / nagłówka / stopki właściwej logicznej karty SDS.

Nie wolno ustalać ich wyłącznie z nazwy pliku.

---

## 10. `parties[]` — podmioty i role

Sekcja 1.3 może zawierać wiele podmiotów.

Model:

```json
{
  "parties": [
    {
      "role": "MANUFACTURER_EXPORTER",
      "name": {
        "value": "The Sherwin-Williams Company",
        "state": "FOUND",
        "evidence": []
      }
    },
    {
      "role": "EU_REPRESENTATIVE",
      "name": {
        "value": "Valspar B.V.",
        "state": "FOUND",
        "evidence": []
      }
    }
  ]
}
```

Role nie są wzajemnie zastępowalne.

Przykładowe role robocze:

```text
MANUFACTURER
MANUFACTURER_EXPORTER
SUPPLIER
IMPORTER
DISTRIBUTOR
EU_REPRESENTATIVE
OTHER
```

Nowe role wymagają kontrolowanej decyzji projektowej; extractor nie tworzy ich dynamicznie.

---

## 11. `safety_profile` — wybrane dane bezpieczeństwa

Kontrakt przewiduje pola odpowiadające zatwierdzonemu Core, m.in.:

```text
classification_clp
hazardous_status
signal_word
hazard_statements
supplemental_hazard_information
pbt
vpvb
carcinogenicity
mutagenicity
reproductive_toxicity
endocrine_disrupting_section_2
endocrine_disrupting_section_11
skin_sensitization
respiratory_sensitization
```

Wartości domenowe takie jak:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

są oddzielone od stanu ekstrakcji.

Przykład:

```json
{
  "carcinogenicity": {
    "domain_value": "NO_DATA",
    "state": "FOUND",
    "evidence": [
      {
        "page": 12,
        "section": "11",
        "subsection": "11.1",
        "source_text": "Brak dostępnych danych..."
      }
    ]
  }
}
```

To oznacza:

```text
state = FOUND
```

bo parser odczytał informację ze źródła, a jednocześnie:

```text
domain_value = NO_DATA
```

bo taki jest sens informacji zawartej w SDS.

---

## 12. `components[]` — składniki z sekcji 3

Minimalny model pojedynczego składnika:

```json
{
  "component_name": {},
  "cas_number": {},
  "ec_number": {},
  "reach_registration_number": {},
  "concentration_text": {},
  "classification_text": {},
  "hazard_statements": {},
  "row_evidence": []
}
```

Składnik musi zachować kontekst wiersza / tabeli źródłowej.

Reguła krytyczna:

```text
hazard składnika z sekcji 3
≠
klasyfikacja całego produktu z sekcji 2
```

---

## 13. `validation` — wynik automatycznej kontroli draftu

Walidator nie zatwierdza danych. Wskazuje jedynie wynik reguł technicznych i semantycznych.

Przykład:

```json
{
  "validation": {
    "status": "REQUIRES_HUMAN_REVIEW",
    "issues": [
      {
        "code": "MULTIPLE_PARTIES_SECTION_1_3",
        "message": "W sekcji 1.3 wykryto więcej niż jedną rolę podmiotu."
      }
    ]
  }
}
```

Dozwolone statusy:

```text
READY_FOR_HUMAN_REVIEW
REQUIRES_HUMAN_REVIEW
BLOCKED
```

`READY_FOR_HUMAN_REVIEW` NIE oznacza automatycznej akceptacji.

---

## 14. `extraction_report` — wynik całego przebiegu

Minimalnie:

```json
{
  "extraction_report": {
    "logical_sds_count": 1,
    "warnings": [],
    "errors": []
  }
}
```

Dla przypadku 3M:

```json
{
  "logical_sds_count": 3
}
```

Każdy z trzech dokumentów musi posiadać własny `page_range`, produkt, datę i rewizję.

---

## 15. Warunki dopuszczenia pola do importu

Pole może zostać przekazane do Application jako kandydat do zatwierdzonego zapisu tylko wtedy, gdy jednocześnie:

```text
state = FOUND
+
evidence != empty
+
dokument = APPROVED przez człowieka
+
walidacja domenowa Application = PASS
```

W przeciwnym razie wartość nie może zostać automatycznie zapisana do Core.

---

## 16. Tryb dry-run importera

Przed zapisem do PostgreSQL importer powinien obsługiwać tryb:

```text
DRY RUN
```

który wykonuje co najmniej:

- walidację formatu JSON,
- walidację wymaganych dowodów,
- porównanie z istniejącymi PRODUCT/SDS,
- identyfikację potencjalnego `NEW PRODUCT`, `EXISTING PRODUCT`, `NEW REVISION`, `AMBIGUOUS`,
- walidację reguł Core,
- raport bez COMMIT.

Dopiero osobna, świadoma operacja może uruchomić zapis przez Application.

---

## 17. Zakres pierwszego PoC

Pierwszy PoC NIE musi implementować całego kontraktu.

Zakres minimalny:

```text
source
+ documents[]
+ page_range
+ product_name
+ manufacturer_product_code
+ parties[]
+ issue_date
+ revision
+ evidence
+ validation
```

Pierwszy zestaw testowy:

```text
OPEX
→ prosty przypadek jedno-SDS

3M DP-490
→ MULTI_SDS_IN_SINGLE_PDF
```

Dopiero po stabilizacji identyfikacji rozszerzamy extractor o:

```text
Sekcja 2
Sekcja 3
Sekcja 11
```

zgodnie z polami wymaganymi przez Core.

---

## 18. Ochrona zakresu

SDS-JSON-001 nie autoryzuje:

- bezpośrednich INSERT/UPDATE do PostgreSQL poza Application,
- automatycznego zatwierdzania produktu lub SDS,
- automatycznej decyzji BHP,
- dynamicznego tworzenia aliasów,
- użycia LLM w runtime,
- zmiany Core,
- zmiany lifecycle `CURRENT / ARCHIVED`.

---

## 19. Następne artefakty

Po zatwierdzeniu SDS-JSON-001 logiczne następstwa to:

```text
SDS-LAYOUT-001
→ wzorce technicznego odczytu layoutów PDF

GOLDEN-SDS-001
→ zestaw referencyjnych SDS + ręcznie zatwierdzone oczekiwane wyniki

następnie
→ BDR/TDR dla autonomicznego extractora i importera
→ Task dla Codexa
```

Nie uruchamiamy implementacji przed zatwierdzeniem wymaganych decyzji projektowych.

---

## 20. Status

```text
SDS-JSON-001
VERSION: 1.0-approved
STATUS: APPROVED
IMPLEMENTATION: NOT AUTHORIZED
```
