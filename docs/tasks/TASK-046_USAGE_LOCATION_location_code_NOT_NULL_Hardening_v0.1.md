# TASK-046 — USAGE_LOCATION location_code — NOT NULL Hardening

**Projekt:** MSDS Manager  
**Obszar:** USAGE_LOCATION / Stanowiska  
**Task:** TASK-046  
**Wersja:** 0.1  
**Status:** AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-05  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

## MODE

`INTEGRATION / OPERATOR MIGRATION`

## GOAL

Domknąć zatwierdzony model `USAGE_LOCATION.location_code` przez zmianę:

`location_code VARCHAR(32) NULL`

na:

`location_code VARCHAR(32) NOT NULL`

dopiero po potwierdzeniu, że wszystkie istniejące lokalizacje operatora mają poprawny i unikalny symbol.

TASK-046 nie nadaje symboli i nie poprawia danych biznesowych.

## AUTHORITATIVE CONTEXT

1. `BDR-010_USAGE_LOCATION_Symbol_biznesowy_v1.0-approved.md`
2. `CORE-001_MSDS_Manager_v1.4-approved_USAGE_LOCATION_CODE.md`
3. `TDR-010_USAGE_LOCATION_location_code_Schema_Migration_v1.0-approved.md`
4. `TASK-043_REPORT.md`
5. `TASK-044_REPORT.md`
6. `TASK-045_REPORT.md`
7. `BDR-002_MSDS_Manager_v1.2-approved.md`
8. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
9. root `AGENTS.md`

Nie wykonuj repo-wide discovery.

## KNOWN STARTING POINT

Operator schema po TASK-044:

```text
Alembic head = c7e5a82d9043
usage_locations.location_code VARCHAR(32) NULL
CHECK format istnieje
UNIQUE istnieje
```

TASK-045 dostarczył kontrolowany workflow uzupełnienia symboli. Physical UX Review TASK-045 = PASS.

## PHASE 1 — PRE-FLIGHT OPERATOR DB

Przed jakąkolwiek zmianą schema sprawdź:

```text
alembic current = c7e5a82d9043
COUNT(location_code IS NULL) = 0
COUNT(location_code = '') = 0
duplicate location_code count = 0
format violations = 0
```

Format:

`^[A-Z0-9][A-Z0-9_-]{0,31}$`

Zapisz snapshot:
- `location_id`
- `location_code`
- `location_name`
- `status`

oraz fingerprint / SHA-256 przed migracją.

Jeżeli NULL, blank, duplicate albo format violation > 0:

`STOP / BLOCKED`

Nie poprawiaj danych w TASK-046.

## PHASE 2 — HARDENING MIGRATION

Jeżeli pre-flight PASS, utwórz minimalną migrację Alembic po `c7e5a82d9043`.

Migracja ma wykonać wyłącznie:

```text
ALTER TABLE usage_locations
ALTER COLUMN location_code SET NOT NULL
```

lub równoważną poprawną operację Alembic/PostgreSQL.

Nie zmieniaj:
- CHECK,
- UNIQUE,
- location_id,
- location_name,
- status,
- FK,
- historii,
- PRODUCT_USAGE_LOCATION.

Backfill = NO.

## PHASE 3 — ISOLATED VALIDATION

Przed operatorem sprawdź na izolowanym PostgreSQL:

1. upgrade z `c7e5a82d9043` przy kompletnych kodach → PASS,
2. upgrade przy NULL → FAIL / BLOCK,
3. downgrade → kolumna ponownie nullable,
4. re-upgrade → PASS,
5. CHECK zachowany,
6. UNIQUE zachowany,
7. dane lokalizacji zachowane,
8. history / assignments zachowane,
9. `alembic check` clean.

## PHASE 4 — APPLY TO OPERATOR DB

Tylko po PASS faz 1–3:

`alembic upgrade <TASK-046_REVISION>`

Po migracji potwierdź:

```text
alembic current = TASK-046 revision / head
location_code nullable = NO
CHECK exists
UNIQUE exists
```

## PHASE 5 — DATA SAFETY

Po migracji:

```text
usage_locations row count before = after
usage_location_history row count before = after
product_usage_locations row count before = after
fingerprint before = after
```

Jedyną dopuszczalną zmianą jest constraint `NOT NULL`.

## DO NOT

Nie wykonuj:
- backfill,
- auto-generation `location_code`,
- edycji symboli,
- zmian UI,
- zmian Application,
- zmian lifecycle,
- zmian historii,
- zmian ANALYTICS,
- nowych dependencies,
- refactoru repo.

Nie usuwaj workflow `AssignLegacyUsageLocationCode` przy okazji tego Tasku.

## VALIDATION

`LEVEL 2 — INTEGRATION / OPERATOR MIGRATION`

Minimum:

```text
pre-flight operator PASS
isolated upgrade PASS
isolated NULL rejection PASS
downgrade PASS
re-upgrade PASS
operator upgrade PASS
alembic current = new head
alembic check = clean
schema drift = NONE
CHECK preserved
UNIQUE preserved
row counts preserved
fingerprint preserved
focused location tests PASS
git diff --check PASS
```

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. choć jeden `location_code IS NULL`,
2. pusty symbol,
3. duplikat symbolu,
4. symbol niezgodny z formatem,
5. operator DB nie jest na `c7e5a82d9043`,
6. istnieje nieoczekiwany Alembic branch / multiple heads,
7. migracja wymaga zmiany danych,
8. CHECK lub UNIQUE nie można zachować,
9. row count / fingerprint zmieni się,
10. poprawne wykonanie wymaga zmian poza schema hardening.

## REPORT

Utwórz `docs/task_reports/TASK-046_REPORT.md`.

Minimalny format:

```text
STATUS: DONE / BLOCKED

PRE-FLIGHT:
- revision before
- usage_locations
- NULL codes
- blank codes
- duplicate codes
- format violations
- fingerprint before

MIGRATION:
- revision id
- previous head
- new head
- operation
- backfill

ISOLATED VALIDATION:
- upgrade
- NULL rejection
- downgrade
- re-upgrade
- CHECK
- UNIQUE

OPERATOR DB:
- upgrade
- nullable after
- row counts before/after
- fingerprint after
- operator data preserved

VALIDATION:
- alembic current
- alembic check
- focused tests
- git diff --check

SCOPE:
- business data changed: NO
- UI change: NO
- Application change: NO
- Core change: NO
- dependencies: NO

DEVIATIONS:
- ...

NEXT:
- READY FOR CERBERUS REVIEW
```

## AUTHORIZATION

Architekt Operacyjny zatwierdził wykonanie:

`Wykonaj TASK-046.`

**EXECUTION: AUTHORIZED**

Autoryzacja nie znosi STOP CONDITIONS.
