# TASK-043 — USAGE_LOCATION location_code — Foundation + Schema Migration A

**Projekt:** MSDS Manager  
**Task:** TASK-043  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-05  

## MODE

```text
INTEGRATION
```

## GOAL

Wdrożyć ETAP A z TDR-010:

```text
USAGE_LOCATION.location_code
+ Domain
+ ORM
+ Application create/read contracts
+ Alembic migration A
+ focused tests
```

bez zgadywania symboli istniejących lokalizacji i bez finalnego UI Stanowiska.

## AUTHORITATIVE CONTEXT

1. `BDR-010_USAGE_LOCATION_Symbol_biznesowy_v1.0-approved.md`
2. `CORE-001_MSDS_Manager_v1.4-approved_USAGE_LOCATION_CODE.md`
3. `TDR-010_USAGE_LOCATION_location_code_Schema_Migration_v1.0-approved.md`
4. `BDR-002 v1.2-approved`
5. `TDR-004 v1.0-approved`
6. `GOV-002 v1.0-approved`
7. root `AGENTS.md`

## DO

Dodaj `location_code` do Domain / ORM / read DTO.

`CreateUsageLocation`:
- symbol required,
- trim,
- uppercase,
- format validation,
- duplicate handled as controlled error.

Migration A:

```text
usage_location.location_code VARCHAR(32) NULL
CHECK format
UNIQUE for non-NULL
NO BACKFILL
```

Legacy NULL musi pozostać odczytywalne.

Testy:
- existing rows survive,
- NULL legacy survives,
- create without code rejected,
- `mzt` → `MZT`,
- duplicate rejected,
- invalid format rejected,
- lifecycle unchanged,
- history unchanged,
- migration isolated PostgreSQL,
- `alembic check` no drift.

## DO NOT

Nie implementuj:
- finalnego NOT NULL,
- backfill operator data,
- UI row actions,
- zmian tabeli Stanowiska,
- edycji location_code,
- historii location_code,
- hierarchii lokalizacji.

## STOP CONDITIONS

STOP, jeśli:
- potrzeba automatycznego backfill,
- potrzebna zmiana FK,
- potrzebna zmiana history model,
- potrzebna nowa dependency,
- operator data musiałyby zostać usunięte lub zmienione bez jawnej mapy.

## REPORT

Utwórz:

```text
docs/task_reports/TASK-043_REPORT.md
```

## AUTHORIZATION

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po:

```text
Wykonaj TASK-043.
```
