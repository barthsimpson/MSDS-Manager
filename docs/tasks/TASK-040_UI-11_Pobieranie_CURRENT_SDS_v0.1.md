# TASK-040 — UI-11 — Pobieranie CURRENT SDS

**Projekt:** MSDS Manager  
**Obszar:** UI-11 — dostęp do CURRENT SDS  
**Task ID:** TASK-040  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-01  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
INTEGRATION
```

## VALIDATION

```text
LEVEL 2
```

## REPORT

```text
SHORT / STANDARD INTEGRATION
```

---

# 1. GOAL

Wdrożyć `UI-11` zgodnie z `TDR-008 v1.0-approved`.

Rezultat:

```text
Produkt
→ CURRENT SDS
→ [Pobierz SDS]
→ controlled read
→ download jako original_filename
```

Bez zmiany lifecycle, schema, Core i storage model.

---

# 2. AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie niezbędny kontekst:

1. `TDR-008_Kontrolowany_dostep_do_CURRENT_SDS_v1.0-approved.md`
2. `BDR-003 — Dokument SDS, aktualność i wersjonowanie`
3. `BDR-007_Kontrolowany_import_SDS_v1.0-approved.md`
4. `TDR-006_Kontrolowany_import_SDS_v1.0-approved.md`
5. `CORE-001 v1.3-approved`
6. `TDR-003 — struktura warstw aplikacji`
7. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
8. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
9. root `AGENTS.md`

Nie wykonuj repo-wide discovery bez potrzeby.

Jeżeli implementacja wymaga decyzji spoza powyższego zakresu:

```text
STOP / BLOCKED
```

---

# 3. KNOWN STARTING POINTS

Minimalnie zlokalizuj:

```text
Presentation:
- Produkty
- Szczegóły produktu
- sekcja CURRENT SDS

Application:
- read model produktu / CURRENT SDS
- use case lub port pozwalający pobrać metadane CURRENT SDS

Infrastructure:
- SDS filesystem adapter używany przez DOC-01
- SDS_ROOT_PATH config

Tests:
- Product details
- SDS read model
- filesystem path safety
- Streamlit/AppTest
```

---

# 4. EXPECTED CHANGE SURFACE

Oczekiwane:

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
tests/
docs/task_reports/TASK-040_REPORT.md
```

Dopuszczalne minimalne read wiring:

```text
app/infrastructure/db/
```

Chronione:

```text
app/domain/
migrations/
Core docs
SDS lifecycle
BHP lifecycle
parser SDS
UNIT_OF_MEASURE
```

---

# 5. DO

## 5.1. UI

W `Produkty → Szczegóły produktu → SDS` dodaj:

```text
[Pobierz SDS]
```

dla wyświetlanego CURRENT SDS.

Nie dodawaj przycisku, jeśli produkt nie ma CURRENT SDS.

---

## 5.2. Download name

Pobrany plik ma być prezentowany użytkownikowi jako:

```text
original_filename
```

Nie jako techniczny UUID storage.

---

## 5.3. Application read use case

Dodaj lub rozszerz mały read use case, np.:

```text
GetCurrentSdsFile
```

Odpowiedzialności:

```text
1. potwierdź PRODUCT
2. pobierz CURRENT SDS
3. pobierz original_filename + relative_path
4. wywołaj filesystem adapter
5. zwróć bytes/stream + original_filename
```

Nazwy symboli dopasuj do repo.

---

## 5.4. Filesystem

Wykorzystaj istniejący adapter SDS z DOC-01, jeśli to możliwe.

Minimalne operacje:

```text
resolve_sds_path(relative_path)
check_availability(relative_path)
read_sds(relative_path)
```

Nie twórz generic storage frameworka.

---

## 5.5. Path safety

Fizyczny odczyt wyłącznie przez:

```text
SDS_ROOT_PATH + relative_path
```

Blokuj:

```text
absolute path
UNC path
../
..\
path traversal
resolved path poza SDS_ROOT_PATH
```

`original_filename` nie steruje ścieżką odczytu.

---

## 5.6. MISSING

Jeżeli rekord CURRENT SDS istnieje, ale pliku nie ma:

```text
MISSING
```

UI pokazuje czytelny komunikat, np.:

```text
Plik SDS jest obecnie niedostępny.
```

Nie:
- usuwaj rekordu,
- nie podstawiaj innego SDS,
- nie zmieniaj CURRENT / ARCHIVED,
- nie naprawiaj ścieżki heurystycznie.

---

## 5.7. Read-only

Download nie może:

- nadpisywać,
- modyfikować,
- usuwać,
- przenosić,
- zmieniać nazwy fizycznego PDF,
- tworzyć nowej rewizji SDS.

---

# 6. DO NOT

Nie:

- zmieniaj schema,
- twórz migracji,
- zmieniaj Core,
- zmieniaj CURRENT / ARCHIVED,
- zmieniaj storage model DOC-01,
- kopiuj PDF do innego katalogu jako element normalnego odczytu,
- dodawaj parsera,
- dodawaj OCR,
- dodawaj nowych zależności,
- przebudowuj całej sekcji Produkt,
- refaktoruj niezwiązanych obszarów.

---

# 7. VALIDATION — LEVEL 2

Potwierdź:

```text
1. produkt z CURRENT SDS i dostępnym PDF → download PASS
2. download filename = original_filename
3. UUID storage niewidoczne jako download filename
4. brak CURRENT SDS → brak aktywnego downloadu / kontrolowany stan
5. CURRENT SDS + brak PDF → MISSING
6. absolute path blocked
7. UNC path blocked
8. traversal blocked
9. resolved path poza root blocked
10. odczyt nie modyfikuje pliku
11. CURRENT / ARCHIVED bez zmian
12. Streamlit/AppTest PASS
13. focused Application/filesystem tests PASS
14. operator data preserved = YES
15. schema change = NONE
16. migration = NONE
17. Core change = NONE
18. new dependencies = NONE
19. git diff --check = PASS
```

Filesystem tests:

```text
isolated tmp directory
```

Nie modyfikuj danych operatora w testach.

---

# 8. ACCEPTANCE CONDITIONS

TASK-040 = DONE, jeżeli:

```text
CURRENT SDS
→ pobieralny z poziomu aplikacji
→ jako original_filename
→ controlled read
→ path safety
→ MISSING
→ read-only
→ brak zmian schema/Core/lifecycle
```

---

# 9. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. potrzebna jest zmiana schema,
2. potrzebna jest zmiana Core,
3. potrzebna jest migracja,
4. trzeba zmienić CURRENT / ARCHIVED,
5. nie można zagwarantować path confinement,
6. trzeba zgadywać CURRENT SDS,
7. trzeba heurystycznie naprawiać `relative_path`,
8. potrzebna jest nowa zależność,
9. poprawne wdrożenie wymaga kopiowania PDF,
10. trzeba przebudować cały moduł SDS zamiast lokalnego read use case.

---

# 10. REPORT

Utwórz:

```text
docs/task_reports/TASK-040_REPORT.md
```

Minimalna struktura:

```text
# TASK-040 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- UI
- Application
- filesystem
- read wiring, jeśli dotyczy
- tests

IMPLEMENTED:
- CURRENT SDS download
- original_filename
- path safety
- MISSING
- read-only

VALIDATION:
- focused tests
- Streamlit/AppTest
- filesystem isolation
- git diff --check

DATA SAFETY:
- operator data preserved: YES/NO

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- SDS lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY FOR CERBERUS REVIEW
- albo BLOCKED — <reason>
```

---

# 11. AUTHORIZATION BOUNDARY

```text
TASK-040
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Samo istnienie Tasku nie stanowi zgody na implementację.

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj TASK-040.
```
