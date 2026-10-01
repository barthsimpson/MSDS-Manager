# TASK-038 — DECISION_EVIDENCE — original_filename Foundation + Schema

**Projekt:** MSDS Manager  
**Obszar:** UI-14 / DOC-02 — DECISION_EVIDENCE  
**Task ID:** TASK-038  
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
LEVEL 2 + SCHEMA CHECKS
```

## REPORT

```text
SHORT / STANDARD INTEGRATION
```

---

# 1. GOAL

Usunąć blocker TASK-037 przez wdrożenie zatwierdzonego fundamentu danych:

```text
DECISION_EVIDENCE.original_filename
```

zgodnie z:

```text
BDR-008 v1.0-approved
TDR-007 v1.1-approved
CORE-001 v1.3-approved
```

Rezultat TASK-038:

```text
Domain
+ ORM
+ PostgreSQL schema
+ Alembic migration
+ repository/mapping
+ focused tests
```

Bez implementacji finalnego UI uploadu / preview / download z TASK-037.

---

# 2. AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie niezbędny kontekst:

1. `BDR-008_Kontrolowany_dowod_BHP_v1.0-approved.md`
2. `TDR-007_Kontrolowany_import_i_dostep_DECISION_EVIDENCE_v1.1-approved.md`
3. `CORE-001_MSDS_Manager_v1.3-approved_DECISION_EVIDENCE.md`
4. `BDR-004 — Decyzja BHP, jej zakres i historia`
5. `TDR-003 — struktura warstw aplikacji`
6. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
7. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
8. root `AGENTS.md`
9. `TASK-037_REPORT.md` wyłącznie jako opis blockera

Nie wykonuj repo-wide discovery bez potrzeby.

W razie sprzeczności:

```text
STOP / BLOCKED
```

Nie zgaduj.

---

# 3. KNOWN STARTING POINTS

Minimalnie zlokalizuj:

```text
Domain:
- DecisionEvidence

ORM:
- DecisionEvidenceModel

DB:
- table decision_evidence
- repository / mapper
- initial migration history

Application:
- create/register evidence contract, tylko jeśli wymagane do utrzymania spójnego mappingu

Tests:
- evidence model/repository
- BHP decision integration
- migration/schema checks
```

Raport TASK-037 wskazuje obecny model:

```text
evidence_id
relative_path
evidence_type
file_format
file_status
```

i brak:

```text
original_filename
```

---

# 4. EXPECTED CHANGE SURFACE

Oczekiwane:

```text
app/domain/
app/infrastructure/db/
migrations/versions/
tests/
docs/task_reports/TASK-038_REPORT.md
```

Minimalne zmiany w `app/application/` są dopuszczalne tylko wtedy, gdy istniejący kontrakt tworzenia evidence musi przenosić `original_filename`.

Chronione:

```text
app/presentation/streamlit/
app/infrastructure/filesystem/
SDS workflow
PRODUCT
UNIT_OF_MEASURE
BHP lifecycle
Core docs / BDR / TDR
```

Nie implementuj jeszcze wznowienia TASK-037.

---

# 5. DO

## 5.1. Domain

Rozszerz `DecisionEvidence` o:

```text
original_filename
```

Semantyka:

```text
original_filename
= nazwa pliku dostarczonego / wskazanego jako dowód źródłowy
≠ relative_path
≠ evidence_id
```

Pole musi być zachowywane niezależnie od technicznej nazwy storage.

---

## 5.2. ORM / persistence

Rozszerz `DecisionEvidenceModel` i mapowanie o:

```text
original_filename
```

Typ:
- tekst / VARCHAR zgodny z przyjętą konwencją repo,
- długość dobrana zgodnie z istniejącymi metadanymi plików, bez tworzenia nowego wzorca bez potrzeby.

Nie zmieniaj innych pól evidence bez konieczności.

---

## 5.3. Schema / Alembic

Dodaj standardową migrację Alembic:

```text
decision_evidence
+ original_filename
```

Zasady:
- migracja jawna i odwracalna,
- downgrade usuwa wyłącznie nowo dodaną kolumnę,
- brak zmian innych tabel,
- brak danych binarnych w DB.

---

## 5.4. Istniejące rekordy

Przed ustaleniem `NOT NULL` sprawdź, czy lokalny / testowy model może zawierać istniejące rekordy `DECISION_EVIDENCE`.

Nie zgaduj wartości `original_filename` z `relative_path`, jeżeli nie jest to jednoznaczne.

Jeżeli istniejące rekordy uniemożliwiają bezpieczne wdrożenie wymaganej semantyki:

```text
STOP / BLOCKED
```

i zgłoś konkretny konflikt danych.

Nie wykonuj heurystycznego backfillu typu:

```text
basename(relative_path) = original_filename
```

dla rekordów, których źródłowa nazwa nie jest znana.

Dla czystego / izolowanego schema nowa kolumna może być wymagana zgodnie z zatwierdzonym modelem.

---

## 5.5. Repository / mapping

Zapewnij pełny round-trip:

```text
Domain
→ ORM
→ PostgreSQL
→ ORM
→ Domain
```

dla `original_filename`.

Nie zapisuj `original_filename` w `notes`.

Nie wyliczaj jej z `relative_path`.

---

## 5.6. Application contract

Jeżeli istniejący use case tworzący `DECISION_EVIDENCE` posiada jawny input DTO / command:

- dodaj `original_filename`,
- nie zmieniaj lifecycle BHP,
- nie implementuj jeszcze uploadu filesystem.

Jeżeli Application nie wymaga zmiany dla foundation schema/mapping:

```text
nie zmieniaj
```

---

# 6. DO NOT

Nie:

- implementuj UI z TASK-037,
- implementuj file uploader,
- implementuj preview/download,
- implementuj filesystem storage,
- implementuj compensation,
- zmieniaj `BHP_DECISION 1:1 DECISION_EVIDENCE`,
- zmieniaj `APPROVED / REJECTED`,
- zmieniaj `CURRENT / SUPERSEDED`,
- zmieniaj PRODUCT,
- zmieniaj SDS,
- dodawaj parsera MSG / OCR / DMS,
- wykonuj heurystycznego backfillu,
- dodawaj nowych zależności,
- refaktoruj niezwiązanych obszarów.

---

# 7. VALIDATION — LEVEL 2 + SCHEMA CHECKS

Potwierdź co najmniej:

```text
1. Domain DecisionEvidence ma original_filename
2. ORM DecisionEvidenceModel ma original_filename
3. migration upgrade dodaje kolumnę
4. migration downgrade usuwa kolumnę
5. repository/mapping round-trip zachowuje original_filename
6. evidence_id bez zmian
7. relative_path bez zmian
8. evidence_type bez zmian
9. file_format bez zmian
10. file_status bez zmian
11. BHP_DECISION 1:1 DECISION_EVIDENCE bez zmian
12. CURRENT / SUPERSEDED bez zmian
13. APPROVED / REJECTED bez zmian
14. brak zmian SDS lifecycle
15. brak zmian PRODUCT
16. brak BLOB storage
17. focused domain/repository tests PASS
18. PostgreSQL integration PASS
19. Alembic upgrade PASS
20. Alembic downgrade/upgrade PASS albo równoważny istniejący migration test
21. alembic current = head w izolowanym środowisku
22. alembic check / schema drift = PASS, jeśli projekt ma ten mechanizm
23. operator data preserved = YES
24. new dependencies = NONE
25. git diff --check = PASS
```

Testy DB wykonuj na izolowanym PostgreSQL / rollback.

Nie modyfikuj trwałych danych operatora.

---

# 8. ACCEPTANCE CONDITIONS

TASK-038 = DONE, jeżeli:

```text
DECISION_EVIDENCE.original_filename
→ istnieje w Domain
→ istnieje w ORM/schema
→ przechodzi migration
→ zachowuje round-trip
→ nie jest wyliczane z relative_path
→ nie zmienia lifecycle BHP
→ nie rozszerza zakresu do UI/filesystem
```

Po akceptacji TASK-038 blocker TASK-037 jest usunięty i TASK-037 może zostać wznowiony na zatwierdzonym TDR-007 v1.1.

---

# 9. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. bezpieczna migracja wymaga zgadywania historycznych `original_filename`,
2. konieczna jest zmiana relacji 1:1,
3. konieczna jest zmiana lifecycle BHP,
4. konieczna jest zmiana innych tabel poza minimalnym FK/contract effect wynikającym bezpośrednio z evidence,
5. implementacja wymaga nowych zależności,
6. istniejące dane operatora wymagają automatycznego cleanupu,
7. repozytorium ma sprzeczny zatwierdzony kontrakt, którego nie da się pogodzić z CORE-001 v1.3 / TDR-007 v1.1,
8. trzeba implementować UI/filesystem z TASK-037, aby foundation działało.

---

# 10. REPORT

Utwórz:

```text
docs/task_reports/TASK-038_REPORT.md
```

Minimalna struktura:

```text
# TASK-038 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- Domain
- ORM
- migration
- repository/mapping
- Application contract, jeśli dotyczy
- tests

IMPLEMENTED:
- original_filename semantics
- schema
- round-trip
- migration upgrade/downgrade

VALIDATION:
- focused tests
- PostgreSQL integration
- Alembic
- schema drift
- git diff --check

DATA SAFETY:
- operator data preserved: YES/NO
- existing evidence rows found: YES/NO
- backfill performed: NO

SCOPE:
- UI change: NO
- filesystem change: NO
- BHP lifecycle change: NO
- SDS lifecycle change: NO
- PRODUCT change: NO
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY TO RESUME TASK-037
- albo BLOCKED — <reason>
```

---

# 11. AUTHORIZATION BOUNDARY

```text
TASK-038
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj TASK-038.
```
