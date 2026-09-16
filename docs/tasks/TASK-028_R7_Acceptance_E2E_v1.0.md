# TASK-028 — R7 Acceptance / E2E „Widok nadzorczy”

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-005 — R7  
**Status:** READY  
**MODE:** ACCEPTANCE  
**VALIDATION:** LEVEL 3  
**REPORT:** SHORT

## GOAL

Potwierdzić E2E, że TASK-026 + TASK-027 tworzą działający, spójny i read-only Widok nadzorczy R7.

TASK-028 nie dodaje funkcjonalności:

```text
zweryfikować R7 → brak regresji → raport do closure R7
```

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:
- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten TASK,
- `TASK-026_REPORT.md`,
- `TASK-027_REPORT.md`.

Nie czytaj ponownie całego CORE/BDR/TDR ani historii projektu, chyba że konkretny wynik walidacji ujawni sprzeczność.

## KNOWN STARTING POINTS

```text
SupervisoryProductRow
ListSupervisoryProducts
SqlAlchemySupervisoryQuery
Streamlit — Widok nadzorczy
```

Baseline po TASK-027:

```text
pytest: 175 passed
Alembic: e0dd7d6468bf (head)
drift: none
SAWarning: none
```

Znane obszary:
- `app/application/dto/supervisory.py`
- `app/application/use_cases/list_supervisory_products.py`
- `app/infrastructure/db/repositories/supervisory_query.py`
- `app/presentation/streamlit/app.py`
- `app/presentation/streamlit/composition.py`
- `app/presentation/streamlit/supervisory.py`
- `tests/unit/test_streamlit_supervisory.py`
- `tests/integration/test_streamlit_shell.py`

Nie wykonuj repo-wide discovery, jeżeli te punkty wystarczają.

## EXPECTED CHANGE SURFACE

Domyślnie:

```text
NO PRODUCT CODE CHANGES
NO TEST CHANGES
NO SCHEMA/MIGRATION CHANGES
NO DEPENDENCY CHANGES
```

Dozwolony nowy plik:
`docs/task_reports/TASK-028_REPORT.md`

Jeżeli Acceptance wymaga zmiany kodu lub testów → `STOP / BLOCKED`. Nie naprawiaj w TASK-028.

## DO

### 1. Real composition
Potwierdź przepływ:

```text
PostgreSQL
→ SqlAlchemySupervisoryQuery
→ ListSupervisoryProducts
→ Streamlit Widok nadzorczy
```

### 2. Kompletny produkt
Potwierdź scenariusz produktu z CURRENT SDS, APPROVED BHP, aktywną lokalizacją i bez problemu.

Oczekiwane:
```text
SDS: CURRENT
BHP: APPROVED
Wymaga działania: OK
```

### 3. Produkt wymagający działania
Potwierdź scenariusz produktu wymagającego działania, np. PENDING_APPROVAL. UI ma prezentować gotowe `action_reasons` z Application, nie wyliczać reguły.

### 4. Read-only
Potwierdź, że sam Widok nadzorczy nie zmienia PRODUCT, SDS, BHP_DECISION, lokalizacji/relacji, statusów ani file_status i nie tworzy danych biznesowych.

### 5. Zachowanie UI
Potwierdź istniejącymi testami:
- jeden PRODUCT = jeden wiersz,
- lokalizacje w jednej komórce,
- trzy filtry,
- pustą listę,
- kontrolowany błąd read-side.

Nie rozbudowuj testów, jeżeli TASK-027 już to wystarczająco potwierdza.

## DO NOT

Nie implementuj funkcji, nie poprawiaj UI, nie refaktoryzuj, nie zmieniaj Core/Domain/ORM/schema/migracji/dependencies/reguł TASK-026, nie analizuj R8 i nie rozpoczynaj kolejnego Tasku.

TASK-028 jest walidacją, nie implementacją.

## VALIDATION — LEVEL 3

Najpierw wykorzystaj istniejące testy/mechanizmy. Nie twórz nowego frameworka ani skryptu, jeśli obecne wystarczają.

### Full regression

```powershell
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Oczekiwane:
```text
>= 175 passed
0 failed
no SAWarning
```

Brak nowych testów w TASK-028 jest prawidłowy.

### Alembic

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:
```text
e0dd7d6468bf (head)
No new upgrade operations detected.
```

Nie wykonuj dodatkowej, drugiej walidacji Alembic na kolejnej bazie, jeżeli nie jest potrzebna.

### Cleanup
Jeżeli E2E tworzy fixture, użyj istniejącej izolacji/rollback. Nie pozostawiaj trwałych danych.

Nie twórz nowego tymczasowego klastra PostgreSQL, jeśli istniejący mechanizm wystarcza.

### Git
Sprawdź tylko zakres potrzebny do potwierdzenia braku zmian kodu produktu. Bez analizy historii Git. Bez commit/push/reset.

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:
1. test regresyjny FAIL,
2. pojawi się SAWarning,
3. Alembic wykryje drift,
4. Widok wykonuje zapis,
5. real composition omija read-side TASK-026,
6. Acceptance wymaga zmiany kodu/testów,
7. wystąpi sprzeczność z zaakceptowanym TASK-026/027.

Nie naprawiaj problemu w tym Tasku.

## REPORT — SHORT

Utwórz `docs/task_reports/TASK-028_REPORT.md`:

```text
# TASK-028 REPORT

STATUS: DONE / BLOCKED

R7 E2E:
- complete product: PASS / FAIL
- action-required product: PASS / FAIL
- real composition: PASS / FAIL
- read-only: PASS / FAIL
- filters / empty / controlled error: PASS / FAIL

VALIDATION:
- pytest:
- SAWarning:
- Alembic current:
- Alembic check:
- cleanup:

CHANGES:
- product code: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE / ...

R7 ACCEPTANCE RECOMMENDATION:
READY FOR CERBERUS REVIEW / NOT READY

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
```

Nie powtarzaj opisów implementacji TASK-026/027.

## DEFINITION OF DONE

DONE, gdy:
1. PostgreSQL → Application → Streamlit potwierdzony,
2. kompletny produkt daje `CURRENT / APPROVED / OK`,
3. produkt wymagający działania pokazuje gotowy powód,
4. read-only potwierdzony,
5. podstawowe UI R7 potwierdzone,
6. pełny pytest PASS,
7. brak SAWarning,
8. Alembic `e0dd7d6468bf (head)`,
9. `alembic check` bez zmian,
10. cleanup PASS,
11. brak zmian kodu/schema/migracji/dependencies,
12. raport rekomenduje R7 do Cerberus review,
13. nie rozpoczęto kolejnego Tasku.

Formalne closure R7 wykonuje Cerberus po raporcie.

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-028.
```
