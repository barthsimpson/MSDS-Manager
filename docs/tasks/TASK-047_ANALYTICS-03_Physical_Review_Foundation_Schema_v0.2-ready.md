# TASK-047 — ANALYTICS-03 Physical Review Foundation + Schema

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-008 — ANALYTICS-03  
**Task:** TASK-047  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-06  
**Wykonawca:** Codex OpenAI  

## MODE

```text
INTEGRATION
```

## GOAL

Wdrożyć techniczny fundament `REVIEW / REVIEW_ITEM`:

```text
Domain
+ ORM
+ PostgreSQL schema
+ Alembic migration
+ repository foundation
+ constraints/indexes
```

Bez Application workflow i bez Streamlit UI.

## AUTHORITATIVE CONTEXT

Przeczytaj wyłącznie:

```text
CORE-001 v1.5-approved
TDR-011 v1.0-approved
GOV-002 v1.0-approved
root AGENTS.md
```

Jeżeli istniejące nazwy techniczne różnią się od dokumentu, znajdź ich bezpośrednie odpowiedniki. Nie wykonuj repo-wide rediscovery.

## KNOWN STARTING POINTS

Minimalnie sprawdź:

```text
app/domain/
app/infrastructure/db/
migrations/versions/
tests/unit/
tests/integration/
```

Znany Alembic head po CHECKPOINT-009:

```text
d8f3a21c6046
```

Pre-flight obowiązkowy:

```text
alembic current
alembic heads
alembic check
```

Jeżeli stan repo posiada nowszy pojedynczy, jawnie zaakceptowany head — użyj go i odnotuj. Multiple heads / niejasny stan → STOP.

## EXPECTED CHANGE SURFACE

```text
app/domain/
app/infrastructure/db/models/
app/infrastructure/db/repositories/
migrations/versions/
tests/
docs/task_reports/TASK-047_REPORT.md
```

Minimalne zmiany Application tylko jeśli konieczne do kontraktów repozytorium; bez workflow biznesowego.

## DO

Wdróż:

```text
PhysicalReview
PhysicalReviewItem
ReviewStatus = DRAFT | FINAL
```

Tabela:

```text
physical_reviews
review_id UUID PK
review_date DATE NOT NULL
status VARCHAR NOT NULL
created_at TIMESTAMPTZ NOT NULL
finalized_at TIMESTAMPTZ NULL
```

Constraints:

```text
status IN ('DRAFT','FINAL')
DRAFT → finalized_at IS NULL
FINAL → finalized_at IS NOT NULL
```

Wymuś maksymalnie jeden DRAFT poprzez częściowy UNIQUE index.

Tabela:

```text
physical_review_items
review_item_id UUID PK
review_id UUID NOT NULL FK
product_id UUID NOT NULL FK
location_id UUID NOT NULL FK
baseline_max_quantity NUMERIC NOT NULL
baseline_unit_id UUID NOT NULL FK
observed_quantity NUMERIC NULL
```

Zachowaj ten sam typ / precision / scale ilości co istniejące `peak_quantity_value`.

Constraints:

```text
baseline_max_quantity >= 0
observed_quantity IS NULL OR observed_quantity >= 0
UNIQUE(review_id, product_id, location_id)
```

FK do PRODUCT / USAGE_LOCATION / UNIT_OF_MEASURE bez cascade delete; preferuj RESTRICT / NO ACTION zgodnie z bieżącą konwencją.

Nie twórz `observed_unit_id`.
Nie twórz kolumny `difference`.

Migracja:

```text
jedna rewizja Alembic
upgrade + downgrade
bez backfill
bez zmian istniejących danych
```

## DO NOT

Nie implementuj jeszcze:

```text
CreatePhysicalReview
UpdateReviewObservedQuantity
DiscardPhysicalReviewDraft
FinalizePhysicalReview
latest FINAL query
Streamlit UI
export
barcode
roles/permissions
DB trigger dla immutability
nowego Unit of Work
```

Nie zmieniaj:

```text
PRODUCT
PRODUCT_USAGE_LOCATION
UNIT_OF_MEASURE
USAGE_LOCATION lifecycle
historii Core
CORE / BDR / TDR
dependencies
```

## VALIDATION

```text
LEVEL 2
```

Wymagane:

```text
focused Domain tests
schema/constraint tests
isolated PostgreSQL migration
upgrade
second DRAFT rejected
quantity constraints
FK/index verification
downgrade
re-upgrade
alembic check
operator DB data safety
git diff --check
```

Nie uruchamiaj pełnego E2E ani pełnego pytest bez konkretnego powodu.

Operator DB:
- przed migracją snapshot revision + counts istotnych tabel,
- upgrade dopiero po PASS izolowanego PostgreSQL,
- po migracji potwierdź nowe puste tabele i brak zmian biznesowych.

## STOP CONDITIONS

STOP / BLOCKED, jeżeli:

```text
Core != v1.5-approved
multiple Alembic heads
potrzebny backfill
potrzebna zmiana istniejących danych
schema wymaga dodatkowych pól biznesowych
nie da się zapewnić single DRAFT zgodnie z TDR
potrzebny DB trigger / nowa dependency / repo-wide refactor
typ quantity jest niejednoznaczny
```

Nie zgaduj.

## REPORT

```text
SHORT / STANDARD INTEGRATION
docs/task_reports/TASK-047_REPORT.md
```

Raport ma zawierać:
- STATUS,
- revision before/after,
- changed,
- validation,
- operator data safety,
- deviations,
- NEXT.

## AUTHORIZATION

Warunek wejścia został spełniony:

```text
SPRINT-008 v1.0-approved
```

Status:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-047.
```
