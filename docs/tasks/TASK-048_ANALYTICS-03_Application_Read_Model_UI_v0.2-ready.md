# TASK-048 — ANALYTICS-03 Application + Read Model + UI

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-008 — ANALYTICS-03  
**Task:** TASK-048  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-06  
**Wykonawca:** Codex OpenAI  

## MODE

```text
INTEGRATION
```

## GOAL

Zaimplementować kompletny workflow użytkowy ANALYTICS-03 na fundamencie zaakceptowanego TASK-047:

```text
CreatePhysicalReview
UpdateReviewObservedQuantity
DiscardPhysicalReviewDraft
FinalizePhysicalReview
read models
latest FINAL for ANALYTICS-02
Streamlit Raport przeglądu
```

Bez zmian schema.

## AUTHORITATIVE CONTEXT

Po odblokowaniu przeczytaj wyłącznie:

```text
CORE-001 v1.5-approved
TDR-011 v1.1-approved
TASK-047_REPORT.md
GOV-002 v1.0-approved
root AGENTS.md
```

TASK-047 ma `STATUS: DONE` i został zaakceptowany przez Architekta Operacyjnego. Aktualny Alembic head po TASK-047: `9f62c4e8b7a1`.

## KNOWN STARTING POINTS

Minimalnie zlokalizuj:

```text
nowe modele/repositories z TASK-047
istniejący TransactionExecutor / granicę transakcji
analytics Application/read model
app/presentation/streamlit/analytics.py
app/presentation/streamlit/composition.py
powiązane focused tests Analytics
```

Nie wykonuj repo-wide discovery.

## EXPECTED CHANGE SURFACE

```text
app/application/
app/infrastructure/db/repositories/
app/presentation/streamlit/analytics.py
app/presentation/streamlit/composition.py
tests/
docs/task_reports/TASK-048_REPORT.md
```

Schema change: NO.
Migration: NONE.

## DO

### 1. CreatePhysicalReview

```text
CreatePhysicalReview(review_date)
```

W jednej transakcji:

```text
sprawdź brak DRAFT
utwórz header DRAFT
odczytaj PRODUCT_USAGE_LOCATION dla ACTIVE lokalizacji
skopiuj pełną populację z baseline MAX + baseline_unit_id
COMMIT
```

Brak populacji:

```text
EmptyReviewPopulationError
→ rollback
→ brak pustego DRAFT
```

### 2. UpdateReviewObservedQuantity

Dopuszczalne:

```text
None
Decimal >= 0
```

Tylko dla parent DRAFT.

FINAL → `FinalReviewImmutableError`.

### 3. DiscardPhysicalReviewDraft

Tylko DRAFT.

W jednej transakcji:

```text
delete items
delete header
```

FINAL nigdy nieusuwalny tym workflow.

### 4. FinalizePhysicalReview

```text
DRAFT → FINAL
finalized_at = now
```

Nie modyfikuj items.
Nie wypełniaj NULL zerem.
Nie aktualizuj MAX.

Przed finalizacją udostępnij:

```text
total_items
observed_items
unobserved_items
```

### 5. Latest FINAL dla ANALYTICS-02

Dla każdego `PRODUCT × LOCATION`:

```text
ORDER BY review_date DESC, finalized_at DESC
```

Jeżeli najnowszy FINAL ma `observed_quantity = NULL`:

```text
nie cofaj się do starszego wyniku
```

`difference` wyliczaj, nie zapisuj.

### 6. UI

W istniejącym:

```text
Analizy → Raport przeglądu
```

minimalny workflow:

```text
brak DRAFT
→ wybierz datę
→ Utwórz przegląd

DRAFT
→ tabela pozycji
→ Product
→ Symbol/Nazwa lokalizacji
→ MAX + jednostka
→ Stan na dzień (edytowalny)
→ Różnica
→ Zatwierdź przegląd
→ Odrzuć draft

FINAL
→ read-only
```

Przed FINAL z NULL pokaż liczbę niesprawdzonych pozycji i wymagaj świadomego potwierdzenia.

Normalny UI nie pokazuje UUID.

### 7. Integracja Zestawienia zbiorczego

Po istnieniu FINAL dodaj informację:

```text
Stan na dzień
Różnica +/-
```

zgodnie z latest FINAL semantics.

Brak FINAL lub latest NULL nie może być prezentowany jako `0`.

## DO NOT

Nie zmieniaj:

```text
schema
Alembic
Core
BDR/TDR
MAX
UOM
USAGE_LOCATION lifecycle
history Core
```

Nie dodawaj:

```text
export
barcode / QR
mobile
evidence
schedule
notifications
roles
approved_by
conversion engine
```

Nie przebudowuj całego analytics module bez konieczności.

## VALIDATION

```text
LEVEL 2
```

Focused:

```text
Application use cases
transaction rollback
single DRAFT behavior
DRAFT discard
FINAL immutability
NULL vs 0
latest FINAL ordering
latest NULL no fallback
difference
Streamlit/AppTest
Analytics-02 integration
no UUID in normal UI
git diff --check
```

Powiązana regresja Analytics tylko w zakresie bezpośrednio dotkniętym.

Bez pełnego E2E / full pytest.

Operator data safety:
- testy zapisujące wykonuj na izolowanym PostgreSQL,
- nie twórz rzeczywistego REVIEW w operator DB bez świadomej akcji użytkownika.

## STOP CONDITIONS

STOP / BLOCKED, jeżeli:

```text
TASK-047 nie jest ACCEPTED
schema nie odpowiada TDR-011
potrzebna nowa migracja
potrzebny nowy status REVIEW
potrzebne FINAL → DRAFT
potrzebna edycja/delete FINAL
latest FINAL wymaga zmiany semantyki
NULL/0 jest niejednoznaczne
nie da się zachować transakcyjności
potrzebny repo-wide refactor / nowa dependency
```

## REPORT

```text
SHORT / STANDARD INTEGRATION
docs/task_reports/TASK-048_REPORT.md
```

## AUTHORIZATION

Warunek wejścia został spełniony:

```text
TASK-047 = DONE / ACCEPTED
Alembic head = 9f62c4e8b7a1
TDR-011 v1.1-approved
```

Status:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-048.
```
