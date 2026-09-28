# TASK-032-R1 — Acceptance Regression Alignment + Diagnostics

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Parent:** TASK-032 — UI MVP Acceptance / Checkpoint  
**Task ID:** TASK-032-R1  
**MODE:** ACCEPTANCE  
**VALIDATION:** LEVEL 3 po zamknięciu diagnostyki  
**REPORT:** FULL  
**Status:** READY  
**Wykonawca:** Codex OpenAI

---

## GOAL

Domknąć pięć porażek wykrytych przez TASK-032 i jednoznacznie sklasyfikować każdą z nich jako:

```text
A. OBSOLETE TEST / CONTRACT ALIGNMENT
B. TEST FIXTURE / ISOLATION DEFECT
C. ENVIRONMENTAL TEST DEFECT
D. REAL PRODUCTION DEFECT
```

Następnie:

```text
jeżeli A/B/C
→ popraw wyłącznie test / fixture / harness
→ uruchom ponownie pełny checkpoint LEVEL 3

jeżeli D
→ STOP / BLOCKED
→ opisz konkretny defekt
→ NIE poprawiaj production code w TASK-032-R1
```

Celem R1 jest **usunąć wątpliwości diagnostyczne**, a nie rozwijać aplikację.

---

# 1. AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `SPRINT-006_UI_MVP_v1.0-approved.md`,
- `TASK-032_UI_MVP_Acceptance_Checkpoint.md`,
- `TASK-032_REPORT.md`,
- raporty:
  - `PATCH-006_REPORT.md`,
  - `PATCH-008_REPORT.md`,
  - `TASK-025_REPORT.md`,
  - `TASK-030_REPORT.md`,
  - `TASK-031_REPORT.md`,
- pięć bezpośrednio failing test files.

Nie czytaj repo-wide history bez potrzeby.

---

# 2. ZNANE FAILURES Z TASK-032

Dokładnie pięć:

```text
1. tests/integration/test_patch006_sds_revision.py::
   test_add_revision_preserves_product_usage_and_previous_bhp

2. tests/integration/test_patch008_delete_product.py::
   test_delete_product_removes_owned_records_and_preserves_shared_data

3. tests/integration/test_task016_acceptance.py::
   test_task016_sprint2_end_to_end_acceptance

4. tests/integration/test_task021_sprint3_acceptance.py::
   test_task021_real_sds_ui_to_postgresql_and_second_current

5. tests/integration/test_task025_sprint4_acceptance.py::
   test_task025_bhp_ui_postgresql_acceptance
```

Nie analizuj innych obszarów, dopóki te pięć nie zostanie sklasyfikowane.

---

# 3. FAZA 1 — TARGETED DIAGNOSTICS

## 3.1. Uruchom każdy FAIL osobno

Uruchom każdy test osobno na izolowanym środowisku PostgreSQL / istniejącym harnessie z pełnym tracebackiem.

Preferuj:

```powershell
.\.venv\Scripts\python.exe -m pytest <test>::<name> -vv -x --tb=long -W error::sqlalchemy.exc.SAWarning
```

Nie uruchamiaj pełnej regresji przed ustaleniem przyczyn.

Dla każdego testu zapisz:

```text
actual exception / assertion
file + line
expected
actual
production path involved
fixture/harness involved
classification A/B/C/D
```

---

# 4. FAILURE 3 — TASK-016 / UUID

## Known evidence

TASK-032 wykazał, że stary test oczekuje `product_id` w tabeli `Produkty`.

SPRINT-006 zatwierdził:

```text
UUID hidden in normal UI
```

Fizyczny walkthrough potwierdził poprawny rejestr produktów bez UUID.

## Expected classification

Preferowana:

```text
A — OBSOLETE TEST / CONTRACT ALIGNMENT
```

jeżeli test rzeczywiście wymaga obecności UUID w użytkowej tabeli.

## Allowed change

Zmień wyłącznie acceptance assertion/selectors tak, aby test potwierdzał aktualny kontrakt:

```text
Produkt
Kod producenta
Producent
Status
SDS
BHP
```

oraz wybór produktu po stabilnej wartości biznesowej / row selection.

**Nie przywracaj UUID do UI.**

Jeżeli test wymaga UUID tylko technicznie do fixture/assertion backendu, może używać go poza użytkową tabelą.

---

# 5. FAILURE 4 — TASK-021 / `30470-second.pdf`

## Known evidence

TASK-032:

```text
ValueError: '30470-second.pdf' is not in list
```

zgłoszone przy kontrolce klasyfikacji / AppTest po przebudowie formularza `Dodaj SDS`.

SPRINT-006 zmienił:

```text
układ sekcji
expandery
kolejność widgetów
oznaczenia required
```

ale nie zmienił workflow AcceptSds.

## Diagnostic question

Sprawdź, czy test:

```text
wybiera widget po indeksie / kolejności
```

zamiast po:

```text
stabilnym key
label
explicit widget identity
```

Jeżeli tak:

```text
A — OBSOLETE TEST / CONTRACT ALIGNMENT
```

i popraw test.

Jeżeli produkcyjny selectbox pliku faktycznie nie zawiera kontrolowanego `30470-second.pdf`, mimo poprawnego SDS_ROOT_PATH:

```text
D — REAL PRODUCTION DEFECT
→ STOP
```

Nie naprawiaj produkcji w R1.

## Allowed test alignment

Preferuj stabilną identyfikację widgetów:

```text
key
label
```

Nie uzależniaj acceptance od pozycji widgetu na stronie.

---

# 6. FAILURE 5 — TASK-025 / `ACTIVE` w komunikacie

## Known evidence

Stary E2E oczekuje, że komunikat sukcesu zawiera literalne:

```text
ACTIVE
```

SPRINT-006 świadomie usunął techniczne/enumowe treści z podstawowych komunikatów.

TASK-030 wymaga:

```text
po decyzji BHP UI wykonuje rerun / ponowny odczyt
i pokazuje faktyczny aktualny status produktu
```

Fizyczny walkthrough potwierdził:

```text
PENDING_APPROVAL
→ APPROVED
→ Produkt: Aktywny
→ BHP: Dopuszczony
```

bez ręcznego refreshu.

## Expected classification

Jeżeli jedyny FAIL wynika z literalnego oczekiwania `ACTIVE` w komunikacie:

```text
A — OBSOLETE TEST / CONTRACT ALIGNMENT
```

## Allowed change

Acceptance ma sprawdzać:

```text
success exists
+
po rerun rzeczywisty produkt ma ACTIVE
+
UI pokazuje użytkowe "Aktywny"
+
bieżąca decyzja = APPROVED / "Dopuszczony"
```

Nie przywracaj technicznego `ACTIVE` do komunikatu sukcesu tylko dla testu.

Jeżeli backend po decyzji faktycznie pozostaje PENDING_APPROVAL:

```text
D — REAL PRODUCTION DEFECT
→ STOP
```

---

# 7. FAILURE 1 — PATCH-006 / NOWA REWIZJA SDS

To jest przypadek wymagający rzeczywistej diagnostyki.

Wcześniej potwierdzono:

```text
product_id unchanged
old CURRENT → ARCHIVED
new SDS → CURRENT
PRODUCT → PENDING_APPROVAL
usage relations preserved
previous BHP preserved as history
previous BHP not inherited
```

oraz fizyczny walkthrough przeszedł.

## Required diagnostic

Dla isolated failure ustal dokładnie:

```text
które assertion FAIL
czy problem występuje przed/po commit
czy fixture tworzy dane zgodne z aktualnym modelem
czy read model / DTO zmieniony w Sprint-006 wpływa tylko na test
czy production lifecycle faktycznie jest naruszony
```

## Classification

Jeżeli FAIL wynika z:

- starego kształtu DTO,
- starego UI assertion,
- fixture niezgodnego z aktualnym kontraktem,
- założenia o kolejności danych,
- zmian test harness,

to:

```text
A/B — popraw test/fixture
```

Jeżeli którykolwiek realny invariant lifecycle jest złamany:

```text
D — REAL PRODUCTION DEFECT
→ STOP / BLOCKED
```

Nie poprawiaj `AddSdsRevision` ani persistence w R1.

---

# 8. FAILURE 2 — PATCH-008 / SAFE DELETE

To również wymaga rzeczywistej diagnostyki.

Wcześniej potwierdzono:

```text
explicit confirmation
product deleted
dependent DB records deleted
shared usage locations preserved
shared manufacturer preserved
SDS source files preserved
BHP evidence files preserved
transaction rollback
```

Fizyczny walkthrough potwierdził:

```text
DB record removed
UI no longer sees product
source PDF remains on filesystem
```

## Required diagnostic

Ustal:

```text
które assertion FAIL
jaki rekord pozostał / zniknął
czy fixture współdzieli manufacturer/location poprawnie
czy aktualny history model wpływa na cleanup
czy fail wynika z izolacji/fixture, czy z production delete
```

## Classification

Jeżeli problem jest w fixture/test expectation:

```text
B — TEST FIXTURE DEFECT
→ popraw test/fixture
```

Jeżeli production delete usuwa współdzielone dane lub zostawia owned orphan:

```text
D — REAL PRODUCTION DEFECT
→ STOP / BLOCKED
```

Nie poprawiaj `DeleteProduct` w R1.

---

# 9. DO

Możesz zmieniać wyłącznie:

```text
tests/**
scripts/verify_task026.py        # tylko jeśli przyczyna leży w harnessie
docs/task_reports/TASK-032-R1_REPORT.md
```

Dopuszczalne są minimalne helpery testowe, jeśli eliminują kruchość selektorów/fixture.

Każda zmiana testu musi być uzasadniona zatwierdzonym obecnym kontraktem.

---

# 10. DO NOT

Nie zmieniaj:

```text
app/**
migrations/**
pyproject.toml
Core/BDR/TDR
```

Nie:

- dostosowuj produkcji do starego testu,
- przywracaj UUID do UI,
- przywracaj `ACTIVE` do toastu tylko dla testu,
- zmieniaj lifecycle SDS/BHP,
- zmieniaj safe delete,
- zmieniaj schema,
- dodawaj dependencies,
- ruszaj parsera,
- realizuj backlogu UI-11/DATA-01/etc.

Jeżeli realny production defect jest potwierdzony:

```text
STOP
```

---

# 11. FAZA 2 — TARGETED RETEST

Po każdej dozwolonej korekcie test/harness:

uruchom ponownie dokładnie pięć wcześniej failing testów.

Wymagane:

```text
5 passed
0 failed
0 SAWarning
```

Jeżeli nadal FAIL:

```text
STOP
→ raport
```

Nie przechodź jeszcze do full checkpoint.

---

# 12. FAZA 3 — FULL LEVEL 3 RECHECK

Dopiero gdy:

```text
5/5 targeted PASS
```

uruchom ponownie pełny checkpoint:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:

```text
0 failed
0 errors
SAWarning = NONE
```

Następnie:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Wymagane:

```text
current = head
No new upgrade operations detected.
```

Sprawdź również:

```text
schema drift = NONE
fixture cleanup = PASS
operator data untouched
git diff --check = PASS
git diff --cached --check = PASS
```

---

# 13. ACCEPTANCE DECISION

## READY

Jeżeli wszystkie pięć failures sklasyfikowano jako A/B/C, testy/harness poprawiono bez zmian produkcyjnych i LEVEL 3 przechodzi:

```text
STATUS:
DONE — TASK-032 REGRESSION UNCERTAINTIES RESOLVED

RECOMMENDATION:
TASK-032 may be reclassified as
READY FOR SPRINT-006 CLOSURE
```

## BLOCKED

Jeżeli choć jeden jest D:

```text
STATUS:
BLOCKED — REAL PRODUCTION DEFECT CONFIRMED

RECOMMENDATION:
SPRINT-006 NOT READY FOR CLOSURE
```

Podaj:

```text
konkretny invariant
minimalny reproduction
failing assertion
warstwa odpowiedzialna
```

Nie naprawiaj produkcji.

---

# 14. REPORT — FULL

Utwórz:

```text
docs/task_reports/TASK-032-R1_REPORT.md
```

Format:

```text
# TASK-032-R1 REPORT

STATUS:
DONE / BLOCKED

DIAGNOSTIC MATRIX:

| Failure | Root cause | Classification | Changed? | Result |
|---|---|---|---|---|
| PATCH-006 revision | ... | A/B/C/D | ... | PASS/FAIL |
| PATCH-008 delete | ... | A/B/C/D | ... | PASS/FAIL |
| TASK-016 UUID | ... | A/B/C/D | ... | PASS/FAIL |
| TASK-021 second PDF | ... | A/B/C/D | ... | PASS/FAIL |
| TASK-025 ACTIVE message | ... | A/B/C/D | ... | PASS/FAIL |

TEST CHANGES:
- ...

PRODUCTION CODE:
- changes: NONE

TARGETED RETEST:
- 5 failures: X passed / Y failed
- SAWarning: ...

FULL LEVEL 3:
- pytest:
- SAWarning:
- E2E:
- Alembic current:
- Alembic check:
- schema drift:
- cleanup:
- operator data preserved:

GIT / SECURITY:
- ...

FINAL CONCLUSION:
- uncertainties resolved: YES / NO
- real production defect found: YES / NO
- TASK-032 closure recommendation:
  READY / NOT READY

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO SPRINTU.
```

---

# AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-032-R1.
```
