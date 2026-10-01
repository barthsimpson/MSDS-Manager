# TASK-039 — Zastosowanie migracji DECISION_EVIDENCE na bazie operatora

**Projekt:** MSDS Manager  
**Task:** TASK-039  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-01  
**Cel:** wdrożenie zatwierdzonej migracji `b379f54c12a0` na właściwej bazie operatora i weryfikacja stanu przed wznowieniem TASK-037

---

## MODE

```text
INTEGRATION / CONTROLLED MIGRATION
```

## VALIDATION

```text
LEVEL 2 + OPERATOR DB SAFETY CHECK
```

---

# 1. GOAL

Zastosować na bazie operatora zatwierdzoną migrację:

```text
a97e2cb7f31d
→
b379f54c12a0
```

która dodaje:

```text
DECISION_EVIDENCE.original_filename
```

bez modyfikowania istniejących danych biznesowych i bez heurystycznego backfillu.

Po poprawnym zakończeniu TASK-039 środowisko operatora ma być gotowe do wznowienia TASK-037.

---

# 2. AUTHORITATIVE CONTEXT

Przeczytaj:

1. `CORE-001_MSDS_Manager_v1.3-approved_DECISION_EVIDENCE.md`
2. `TDR-007_Kontrolowany_import_i_dostep_DECISION_EVIDENCE_v1.1-approved.md`
3. `BDR-008_Kontrolowany_dowod_BHP_v1.0-approved.md`
4. `TASK-038_REPORT.md`
5. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
6. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
7. root `AGENTS.md`

Nie wykonuj zmian funkcjonalnych.

---

# 3. KNOWN STARTING POINT

Raport TASK-038 potwierdził:

```text
operator DB schema = a97e2cb7f31d
existing DECISION_EVIDENCE rows = 3
backfill = NONE
target migration = b379f54c12a0
```

Nowa kolumna jest nullable dla danych historycznych.

Nowe rejestracje wymagają niepustego `original_filename` na poziomie Application.

---

# 4. PRE-FLIGHT

Przed migracją:

1. potwierdź aktualny `alembic current`,
2. potwierdź liczbę rekordów `DECISION_EVIDENCE`,
3. potwierdź, że istniejące 3 rekordy są zachowane,
4. nie zmieniaj ich ręcznie,
5. nie wykonuj backfillu,
6. jeżeli baza nie jest na oczekiwanym revision `a97e2cb7f31d` → `STOP / BLOCKED`.

---

# 5. DO

Wykonaj standardową migrację Alembic do:

```text
b379f54c12a0
```

Następnie potwierdź:

```text
decision_evidence.original_filename istnieje
3 istniejące rekordy nadal istnieją
ich original_filename = NULL
pozostałe pola rekordów bez zmian
alembic current = b379f54c12a0
alembic check = PASS
```

Nie twórz nowych rekordów biznesowych na bazie operatora tylko po to, aby sprawdzić migrację.

Jeżeli konieczny jest test zapisu nowego rekordu, wykonaj go w izolowanym PostgreSQL lub w transakcji zakończonej rollbackiem.

---

# 6. DO NOT

Nie:
- wykonuj backfillu `original_filename`,
- zgaduj nazwy z `relative_path`,
- usuwaj rekordów,
- zmieniaj danych operatora poza zmianą schema zatwierdzoną migracją,
- wdrażaj TASK-037,
- zmieniaj UI,
- zmieniaj filesystem,
- twórz kolejnych migracji,
- zmieniaj Core / BDR / TDR.

---

# 7. VALIDATION

Wymagane:

```text
1. pre-flight revision = a97e2cb7f31d
2. pre-flight evidence rows = 3
3. alembic upgrade → PASS
4. current = b379f54c12a0
5. original_filename column exists
6. historical rows preserved = 3
7. historical original_filename = NULL
8. no backfill
9. no unintended data changes
10. alembic check = PASS
11. focused related tests = PASS
12. git diff --check = PASS
13. operator data preserved = YES
```

---

# 8. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. operator DB nie jest na `a97e2cb7f31d`,
2. liczba / stan istniejących evidence różni się od oczekiwanego w sposób wymagający decyzji,
3. migracja próbuje wymusić wartość dla historycznych rekordów,
4. wymagany byłby backfill,
5. migracja dotyka tabel innych niż wynika z TASK-038,
6. `alembic upgrade` lub `alembic check` FAIL,
7. zachowanie danych operatora nie może być zagwarantowane.

---

# 9. REPORT

Utwórz:

```text
docs/task_reports/TASK-039_REPORT.md
```

Minimalna struktura:

```text
# TASK-039 REPORT

STATUS:
DONE / BLOCKED

PRE-FLIGHT:
- revision before:
- evidence rows before:

MIGRATION:
- applied:
- revision after:
- schema result:

DATA SAFETY:
- evidence rows after:
- historical original_filename:
- backfill:
- operator data preserved:

VALIDATION:
- alembic current:
- alembic check:
- focused tests:
- git diff --check:

DEVIATIONS:
- NONE / list

NEXT:
- READY TO RESUME TASK-037
- albo BLOCKED — <reason>
```

---

# 10. AUTHORIZATION

```text
TASK-039
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-039.
```
