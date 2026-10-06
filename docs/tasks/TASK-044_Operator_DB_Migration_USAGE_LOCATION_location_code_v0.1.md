# TASK-044 — Operator DB Migration — USAGE_LOCATION location_code Foundation

**Projekt:** MSDS Manager  
**Obszar:** USAGE_LOCATION / Stanowiska  
**Task:** TASK-044  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-05  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
ACCEPTANCE / OPERATOR MIGRATION
```

---

## GOAL

Zastosować na **bazie operatora** zaakceptowaną migrację foundation z TASK-043:

```text
c7e5a82d9043
```

tak aby baza operatora otrzymała:

```text
usage_locations.location_code VARCHAR(32) NULL
+ CHECK formatu
+ UNIQUE dla wartości nie-NULL
```

bez:

```text
backfill
zgadywania symboli
zmiany istniejących lokalizacji
zmiany historii
zmiany FK
```

TASK-044 jest wyłącznie kontrolowanym wdrożeniem istniejącej migracji na operator DB.

---

## AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie:

1. `BDR-010_USAGE_LOCATION_Symbol_biznesowy_v1.0-approved.md`
2. `CORE-001_MSDS_Manager_v1.4-approved_USAGE_LOCATION_CODE.md`
3. `TDR-010_USAGE_LOCATION_location_code_Schema_Migration_v1.0-approved.md`
4. `TASK-043_REPORT.md`
5. `TASK-039_REPORT.md` — jako wzorzec bezpiecznej migracji operator DB
6. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
7. root `AGENTS.md`

Nie wykonuj repo-wide zmian.

---

## KNOWN STARTING POINT

Ostatni potwierdzony operator DB po TASK-039:

```text
Alembic revision = b379f54c12a0
```

TASK-043 potwierdził na izolowanym PostgreSQL:

```text
upgrade b379f54c12a0 → c7e5a82d9043 = PASS
legacy rows preserved
legacy location_code = NULL
alembic check = clean
```

TASK-044 musi jednak samodzielnie potwierdzić rzeczywisty stan operator DB przed migracją.

---

## DO

### 1. Pre-flight operator DB

Przed jakąkolwiek zmianą potwierdź i zapisz:

```text
alembic current
liczba usage_locations
liczba usage_location_history
kolumna location_code istnieje? YES/NO
```

Dodatkowo wykonaj snapshot danych istniejących lokalizacji, co najmniej:

```text
location_id
location_name
status
```

i wylicz stabilny fingerprint / hash danych przed migracją.

Jeżeli operator revision nie jest zgodny z oczekiwaną linią migracji:

```text
STOP / BLOCKED
```

Nie rozwiązuj rozbieżności opportunistycznie.

---

### 2. Apply migration

Jeżeli pre-flight PASS:

```text
alembic upgrade c7e5a82d9043
```

Nie używaj:

```text
alembic upgrade head
```

jeżeli head repo może zawierać nowsze, niezwiązane migracje.

Celem TASK-044 jest dokładnie:

```text
c7e5a82d9043
```

---

### 3. Post-migration verification

Po migracji potwierdź:

```text
alembic current = c7e5a82d9043
```

Schema:

```text
usage_locations.location_code exists
type = VARCHAR(32)
nullable = YES
CHECK exists
UNIQUE / unique index exists for non-NULL
```

Dane:

```text
liczba usage_locations przed = po
liczba usage_location_history przed = po
istniejące location_id bez zmian
location_name bez zmian
status bez zmian
location_code = NULL dla legacy
```

Fingerprint istniejących pól musi pozostać identyczny.

---

### 4. No backfill

TASK-044 ma potwierdzić:

```text
backfill = NO
```

Nie wpisuj:

```text
MZT
UTR
REG
ani żadnych innych symboli
```

Nie wyliczaj symbolu z nazwy.

---

### 5. Alembic validation

Po migracji wykonaj:

```text
alembic current
alembic check
```

Wymagane:

```text
current = c7e5a82d9043
No new upgrade operations detected
```

Jeżeli `alembic check` wykazuje drift:

```text
STOP / BLOCKED
```

---

### 6. Application smoke / focused validation

Uruchom tylko focused tests potrzebne do potwierdzenia, że:

```text
legacy NULL jest czytelne
nowy CreateUsageLocation wymaga location_code
existing location list nadal działa
lifecycle ACTIVE/INACTIVE nadal działa
```

Testy nie mogą pisać do operator DB.

---

## DO NOT

Nie wykonuj w TASK-044:

```text
backfill location_code
TASK-045
zmian UI Stanowiska
NOT NULL hardening
nowej migracji
zmian Domain/Application
zmian Core/BDR/TDR
edycji nazw lokalizacji
dezaktywacji/reaktywacji lokalizacji
nowych rekordów biznesowych
```

---

## DATA SAFETY

Operator DB jest środowiskiem docelowym.

Dlatego:

```text
NO DELETE
NO UPDATE business rows
NO INSERT business rows
NO heuristic mapping
```

Jedyną dozwoloną zmianą jest schema wynikająca z istniejącej migracji:

```text
c7e5a82d9043
```

---

## VALIDATION

```text
LEVEL 2 — OPERATOR MIGRATION
REPORT: SHORT / STANDARD
```

Acceptance:

```text
pre-flight revision confirmed
migration applied exactly once
operator revision = c7e5a82d9043
location_code exists
legacy location_code = NULL
location rows preserved
history rows preserved
fingerprint unchanged
backfill = NO
alembic check = clean
focused tests = PASS
```

---

## STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. operator DB nie jest na oczekiwanej linii Alembic,
2. `location_code` już istnieje w niezgodnej postaci,
3. istnieje więcej niż jeden head / branch wymagający decyzji,
4. migracja chce zmieniać dane biznesowe,
5. migracja wymaga backfill,
6. liczba lokalizacji lub historii zmienia się po migracji,
7. fingerprint istniejących pól różni się przed/po,
8. `alembic check` wykazuje drift,
9. poprawne wykonanie wymaga zmian kodu lub nowej migracji.

Nie naprawiaj blockerów w tym Tasku.

---

## REPORT

Utwórz:

```text
docs/task_reports/TASK-044_REPORT.md
```

Minimalny format:

```text
# TASK-044 REPORT

STATUS:
DONE / BLOCKED

PRE-FLIGHT:
- revision before:
- usage_locations rows before:
- usage_location_history rows before:
- location_code column before:
- existing-data fingerprint:

MIGRATION:
- applied:
- revision after:
- schema result:
- backfill:

DATA SAFETY:
- usage_locations rows after:
- usage_location_history rows after:
- legacy location_code:
- existing-data fingerprint after:
- operator data preserved:
- new business rows:

VALIDATION:
- alembic current:
- alembic check:
- focused tests:
- git diff --check:

DEVIATIONS:
- ...

NEXT:
- READY FOR TASK-045
lub
- BLOCKED — <reason>
```

---

## AUTHORIZATION

TASK-044 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-044.
```

Po `DONE / ACCEPTED`:

```text
TASK-045
→ legacy symbol assignment
→ Stanowiska UX
→ row-specific Dezaktywuj / Reaktywuj
```
