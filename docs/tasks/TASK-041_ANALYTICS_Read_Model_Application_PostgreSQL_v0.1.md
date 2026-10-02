# TASK-041 — ANALYTICS Read Model + Application + PostgreSQL Integration

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 / ANALYTICS-02 — `Analizy` / `Zestawienie zbiorcze`  
**Task:** TASK-041  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

> Uwaga governance: TASK-041 jest przygotowany wykonawczo, ale nie jest zgodą na start. Jawna autoryzacja wykonania pozostaje osobnym krokiem zgodnie z GOV/PDP.

---

## MODE

```text
INTEGRATION
```

---

## GOAL

Wdrożyć warstwę danych dla pierwszego przyrostu `Analizy` zgodnie z zatwierdzonym:

```text
ANALYTICS-01 UX Contract v1.0-approved
BDR-009 v1.0-approved
TDR-009 v1.0-approved
MODEL A — DYNAMIC READ MODEL
```

Rezultat TASK-041:

```text
Application analytics DTO / query contract
+ analytics read port
+ PostgreSQL read adapter
+ ProductAnalyticsFact = 1 rekord / PRODUCT
+ KPI / status / alert semantics
+ SDS trend read model
+ PRODUCT × USAGE_LOCATION detail read model
+ runtime file availability overlay
+ focused unit/integration tests
```

TASK-041 nie implementuje jeszcze finalnego dashboardu Streamlit, wykresów ani UX targetu.

---

## AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie:

1. `TDR-009_ANALYTICS_Dynamic_Read_Model_Dashboard_v1.0-approved.md`
2. `BDR-009_ANALYTICS_Zestawienie_zbiorcze_KPI_i_agregacje_v1.0-approved.md`
3. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved.md`
4. `CORE-001_MSDS_Manager_v1.3-approved_DECISION_EVIDENCE.md`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
6. root `AGENTS.md`

Dodatkowo tylko jeśli potrzebne do bezpośredniej implementacji:

```text
TDR-003 — warstwy aplikacji
TDR-007 v1.1-approved — evidence availability/read
TDR-008 — CURRENT SDS read/download
```

Nie wykonuj repo-wide rediscovery.

Jeżeli nazwy plików / klas różnią się od poniższych punktów startowych, znajdź ich bezpośrednie odpowiedniki i nie rozszerzaj eksploracji poza potrzebny zakres.

Jeżeli implementacja wymaga zmiany biznesowej, Core lub schema:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

### Existing read-side pattern

W repo istnieje zatwierdzony wzorzec read model:

```text
app/application/dto/supervisory.py
app/application/use_cases/list_supervisory_products.py
app/infrastructure/db/repositories/supervisory_query.py
```

Użyj go jako wzorca granic warstw, nie kopiuj mechanicznie całej implementacji.

### CURRENT SDS read/access

Istnieją co najmniej:

```text
app/application/use_cases/get_current_sds_file.py
app/infrastructure/db/repositories/current_sds_query.py
app/infrastructure/filesystem/sds_pdf_storage.py
```

TASK-040 potwierdził kontrolowany read CURRENT SDS i bezpieczną obsługę MISSING.

### DECISION_EVIDENCE read/access

TASK-037 wdrożył:

```text
dedykowany BHP filesystem adapter
kontrolowany read/download evidence
MISSING bez niszczenia historii
Application use cases dla evidence
```

Zlokalizuj bezpośrednie pliki/symbole w tym obszarze i wykorzystaj istniejące reguły path safety.

Nie twórz drugiego mechanizmu dostępu do evidence.

### Existing PRODUCT × USAGE_LOCATION

W istniejącym supervisory read model dostępne są już dane:

```text
PRODUCT
×
USAGE_LOCATION
peak quantity
monthly consumption
units
```

Rozszerzaj przez nowy analytics read-side; nie przebudowuj istniejącego widoku nadzorczego.

---

## EXPECTED CHANGE SURFACE

Oczekiwany zakres zmian:

```text
app/application/dto/
app/application/ports/
app/application/use_cases/

app/infrastructure/db/repositories/
app/infrastructure/filesystem/     # tylko jeśli potrzebny mały read-only availability contract

tests/unit/
tests/integration/

docs/task_reports/TASK-041_REPORT.md
```

Nie oczekuje się zmian w:

```text
app/presentation/streamlit/
app/domain/
migrations/
pyproject.toml
CORE / BDR / TDR
parser SDS
lifecycle SDS
lifecycle BHP
```

Jeżeli zmiana w którymkolwiek chronionym obszarze okaże się konieczna:

```text
STOP / BLOCKED
```

---

# DO

## 1. Analytics DTO / contracts

Dodaj minimalne read-side DTO zgodne z TDR-009.

Co najmniej:

```text
AnalyticsFilters
ProductAnalyticsFact
AnalyticsKpiDto
BhpStatusDistributionDto
SdsTrendPoint
ManufacturerSummaryRow
ProductLocationAnalyticsRow
AttentionSummaryDto
AnalyticsDashboardDto
```

Nazwy mogą być dostosowane do istniejącej konwencji repo, ale semantyka ma pozostać jednoznaczna.

Nie twórz encji Domain `Analytics`.

---

## 2. AnalyticsFilters

Minimalne pola:

```text
manufacturer_id: UUID | None
sds_status: CURRENT_PRESENT | CURRENT_MISSING | None
bhp_status: APPROVED | REJECTED | NO_DECISION | None
usage_location_id: UUID | None
include_no_active_location: bool
trend_date_from: date
trend_date_to: date
```

Walidacja Application:

```text
trend_date_from <= trend_date_to
```

Filtry producenta i lokalizacji używają ID, nie nazw tekstowych.

---

## 3. ProductAnalyticsFact

Zapewnij read model:

```text
1 PRODUCT = 1 ProductAnalyticsFact
```

Minimalnie zachowaj:

```text
product_id
product_name
usage_status

manufacturer_id
manufacturer_name

has_current_sds
current_sds_id
current_sds_original_filename
current_sds_relative_path
current_sds_registered_at

bhp_category
current_bhp_decision_id

current_evidence_id
current_evidence_original_filename
current_evidence_relative_path

active_location_count
has_active_location

latest_sds_registered_at
```

Dozwolone read-side `bhp_category`:

```text
APPROVED
REJECTED
NO_DECISION
NOT_APPLICABLE_NO_CURRENT_SDS
```

`NOT_APPLICABLE_NO_CURRENT_SDS`:

```text
jest technicznym stanem read modelu
≠ nowy status domenowy
```

---

## 4. PostgreSQL query — bez zwielokrotnienia PRODUCT

Zbuduj dedykowany analytics read adapter/query.

Wymaganie:

```text
jeden rekord wynikowy na PRODUCT
```

Przy joinach do:

```text
SDS
BHP_DECISION
DECISION_EVIDENCE
PRODUCT_USAGE_LOCATION
USAGE_LOCATION
```

unikaj zwielokrotnienia.

Dopuszczalne:

```text
EXISTS
CTE
subquery
GROUP BY
LEFT JOIN do podzapytania 1:1
DISTINCT tam, gdzie semantycznie uzasadnione
```

Zabronione:

```text
load all PRODUCT
→ query SDS per PRODUCT
→ query BHP per PRODUCT
→ query location per PRODUCT
```

czyli:

```text
N+1 = FAIL
```

---

## 5. Semantyka CURRENT SDS

Dla każdego PRODUCT:

```text
has_current_sds = True
```

wyłącznie, jeśli istnieje:

```text
SDS.status = CURRENT
```

Nie utożsamiaj:

```text
ARCHIVED
```

z bieżącym SDS.

Nie wyznaczaj CURRENT na podstawie:

```text
issue_date
revision
filename
```

---

## 6. Semantyka BHP

Dla CURRENT SDS:

```text
APPROVED
= CURRENT BHP_DECISION + decision_status APPROVED

REJECTED
= CURRENT BHP_DECISION + decision_status REJECTED

NO_DECISION
= CURRENT SDS istnieje
  + brak CURRENT BHP_DECISION
```

Jeżeli brak CURRENT SDS:

```text
NOT_APPLICABLE_NO_CURRENT_SDS
```

Nie dodawaj:

```text
PENDING
W_TRAKCIE
```

jako statusu BHP.

---

## 7. KPI assembly

Z `ProductAnalyticsFact[]` zbuduj:

```text
products_total
current_sds_count
bhp_approved_count
attention_products_count
```

Reguły:

```text
products_total
= DISTINCT PRODUCT po filtrach

current_sds_count
= PRODUCT z CURRENT SDS

bhp_approved_count
= PRODUCT z APPROVED dla CURRENT SDS

attention_products_count
= DISTINCT PRODUCT spełniające >= 1 regułę attention
```

Nie licz jednego PRODUCT wielokrotnie, jeśli ma kilka braków.

---

## 8. Active locations KPI

Licz:

```text
COUNT(DISTINCT ACTIVE USAGE_LOCATION)
```

w aktualnym zakresie filtra PRODUCT.

Nie licz:

```text
SUM(ProductAnalyticsFact.active_location_count)
```

bo jedna lokalizacja może być współdzielona przez wiele produktów.

Jeżeli nie ma filtra PRODUCT/producenta/BHP/SDS:

```text
aktywnych stanowisk = wszystkie ACTIVE USAGE_LOCATION
```

Jeżeli aktywne są filtry produktowe:

```text
aktywnych stanowisk = DISTINCT ACTIVE USAGE_LOCATION
powiązane z aktualnym zbiorem PRODUCT
```

---

## 9. Attention rules

Zaimplementuj zgodnie z BDR-009:

### A — brak CURRENT SDS

```text
PRODUCT bez CURRENT SDS
```

### B — brak decyzji BHP

```text
CURRENT SDS istnieje
+ brak CURRENT BHP_DECISION
```

### C — brak aktywnej lokalizacji

Tylko dla:

```text
PRODUCT.usage_status = ACTIVE
lub
PRODUCT.usage_status = PENDING_APPROVAL
```

i:

```text
brak powiązania z ACTIVE USAGE_LOCATION
```

Nie oznaczaj z tego powodu:

```text
REJECTED
INACTIVE
```

### D — niedostępny dokument

```text
CURRENT SDS = MISSING
lub
CURRENT BHP evidence = MISSING
```

---

## 10. Runtime availability overlay

Nie próbuj ustalać fizycznej dostępności pliku wyłącznie z PostgreSQL.

Po pobraniu ProductAnalyticsFact:

```text
CURRENT SDS candidate
CURRENT evidence candidate
        ↓
existing safe filesystem availability
        ↓
AVAILABLE / MISSING / CHECK_FAILED
```

Zasady:

```text
MISSING
→ attention = YES

CHECK_FAILED / UNKNOWN
→ nie licz automatycznie jako MISSING
→ zachowaj stan techniczny do dalszej prezentacji
```

Nie czytaj zawartości dokumentów.

Nie wykonuj write/delete/move/rename.

Nie duplikuj path safety.

Użyj istniejących mechanizmów TASK-037 / TASK-040.

---

## 11. SDS trend

Dodaj read query:

```text
registered_at
→ bucket MONTH
→ NEW / UPDATED
```

Definicja:

```text
NEW
= pierwszy SDS dla PRODUCT

UPDATED
= każdy kolejny SDS dla PRODUCT
```

Do deterministycznej kolejności użyj:

```text
registered_at
+ stabilny tie-breaker, np. sds_id
```

Nie używaj do kolejności:

```text
issue_date
revision
filename
```

Minimalny wynik:

```text
period_start
new_sds_count
updated_sds_count
```

---

## 12. Filtry a trend

Najpierw ustal bieżący zbiór PRODUCT według filtrów wymiarowych:

```text
manufacturer
SDS status
BHP status
location
```

Następnie trend pokazuje zdarzenia SDS tych PRODUCT w:

```text
trend_date_from
trend_date_to
```

Zakres trendu:

```text
nie zmienia KPI current-state
```

---

## 13. Manufacturer summary

Zbuduj:

```text
ManufacturerSummaryRow
```

Minimalnie:

```text
manufacturer_id
manufacturer_name
products_count
current_sds_count
bhp_approved_count
attention_products_count
latest_sds_registered_at
```

`latest_sds_registered_at`:

```text
MAX(SDS.registered_at)
```

Nie używaj `issue_date`.

---

## 14. PRODUCT × USAGE_LOCATION detail

Dodaj read query / read model:

```text
ProductLocationAnalyticsRow
```

Minimalnie:

```text
product_id
product_name
manufacturer_name

location_id | None
location_name | None

peak_quantity_value
peak_quantity_unit_code

monthly_consumption_value | None
monthly_consumption_unit_code | None

product_usage_status
current_sds_revision | None
current_sds_issue_date | None
bhp_category
```

Zasady:

```text
MAX = peak_quantity
monthly = informacja pomocnicza
```

PRODUCT bez aktywnej lokalizacji:

```text
nie może zniknąć przy braku filtra lokalizacji
```

Dopuszczalne:

```text
location_id = None
location_name = None
```

dla reprezentacji `BRAK`.

---

## 15. GetAnalyticsDashboard

Dodaj jeden Application use case, preferowany:

```text
GetAnalyticsDashboard
```

który:

```text
1. waliduje AnalyticsFilters
2. pobiera ProductAnalyticsFact[]
3. nakłada runtime availability overlay
4. liczy KPI
5. liczy attention
6. pobiera active locations count
7. pobiera SDS trend
8. buduje manufacturer summary
9. zwraca AnalyticsDashboardDto
```

Szczegółowy PRODUCT × USAGE_LOCATION może być:

```text
A. częścią AnalyticsDashboardDto
lub
B. osobnym read use case
```

Preferowane dla przyszłego lazy load UI:

```text
B. osobny use case
```

np.:

```text
ListAnalyticsProductLocations
```

Nie jest to drugi framework analityczny; to tylko odrębny cięższy read detail.

---

## 16. Query count / NO N+1

Dla pełnego dashboard DTO liczba query SQL:

```text
musi być stała względem liczby PRODUCT
```

Nie wymagamy dokładnie 3 czy 4 zapytań.

W raporcie podaj faktyczny układ, np.:

```text
Q1 product facts
Q2 active locations count
Q3 trend
```

Manufacturer summary może być:

```text
agregowany w Application z facts
lub
osobny stały query
```

Wybierz prostszy wariant bez N+1.

---

# DO NOT

Nie implementuj w TASK-041:

```text
Streamlit Analizy screen
sidebar item
KPI cards UI
charts
CSS
Monday-style layout
expander UI
aktywny eksport
React
custom JS
cache biznesowy
materialized view
analytics schema
new table
Alembic migration
```

Nie zmieniaj:

```text
PRODUCT lifecycle
SDS CURRENT / ARCHIVED
BHP CURRENT / SUPERSEDED
BHP APPROVED / REJECTED
UNIT_OF_MEASURE
history model
Core
```

Nie wykonuj opportunistic refactor istniejącego `supervisory_query.py`.

Nie przenoś obecnego Widoku nadzorczego do Analytics.

Nie dodawaj nowej dependency.

---

# VALIDATION

```text
LEVEL 2 — INTEGRATION
REPORT: SHORT / STANDARD INTEGRATION
```

## A. Unit / Application

Potwierdź co najmniej:

1. `products_total` = DISTINCT PRODUCT,
2. `current_sds_count` liczy PRODUCT, nie rekordy SDS,
3. brak CURRENT SDS nie staje się ARCHIVED,
4. APPROVED dotyczy CURRENT decision dla CURRENT SDS,
5. REJECTED ≠ NO_DECISION,
6. brak CURRENT SDS nie trafia do BHP NO_DECISION,
7. attention deduplikuje PRODUCT z wieloma brakami,
8. alert lokalizacji dotyczy tylko ACTIVE/PENDING_APPROVAL,
9. `0` nie jest traktowane jak brak danych,
10. trend date validation działa,
11. okres trendu nie zmienia KPI current-state.

## B. PostgreSQL integration — isolated

Użyj izolowanego PostgreSQL / transakcji rollback zgodnie z obecnym test harness.

Scenariusze:

```text
PRODUCT bez SDS
PRODUCT z jednym CURRENT SDS
PRODUCT z CURRENT + ARCHIVED
CURRENT SDS bez BHP
CURRENT SDS + APPROVED
CURRENT SDS + REJECTED
wiele BHP_DECISION z jedną CURRENT
wiele lokalizacji jednego PRODUCT
jedna lokalizacja współdzielona przez wiele PRODUCT
PRODUCT bez lokalizacji
INACTIVE USAGE_LOCATION
dwóch producentów
pierwszy + kolejny SDS dla trendu
tie registered_at → deterministyczna klasyfikacja
```

## C. Filesystem availability — isolated tmp

Potwierdź:

```text
CURRENT SDS AVAILABLE
CURRENT SDS MISSING
evidence AVAILABLE
evidence MISSING
outside-root / traversal blocked
check failure ≠ automatic MISSING
no filesystem mutation
```

## D. Architecture / scope

Potwierdź:

```text
schema change: NO
migration: NONE
Core change: NO
Domain entity change: NO
Streamlit change: NO
new dependency: NO
operator data preserved: YES
```

## E. Regression

Uruchom focused regressions dla:

```text
supervisory read model
CURRENT SDS read
evidence controlled read
```

Nie wykonuj pełnej regresji repo, o ile focused tests nie ujawnią powiązanego problemu.

---

# STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. poprawna implementacja wymaga zmiany schema,
2. potrzebna jest migracja Alembic,
3. potrzebna jest zmiana Core,
4. trzeba dodać nowy status biznesowy,
5. nie da się wyznaczyć CURRENT BHP dla CURRENT SDS bez zgadywania,
6. istniejące dane nie pozwalają odróżnić pierwszego i kolejnego SDS deterministycznie,
7. availability wymaga duplikacji lub osłabienia path safety,
8. poprawna implementacja wymaga bezpośredniego SQL w Streamlit,
9. liczba query rośnie wraz z liczbą PRODUCT,
10. potrzebna jest nowa dependency,
11. test wymaga trwałej modyfikacji operator DB lub operator filesystem,
12. implementation zaczyna wymagać przebudowy istniejącego supervisory read model.

Nie naprawiaj blockerów przez rozszerzenie zakresu.

---

# REPORT

Utwórz:

```text
docs/task_reports/TASK-041_REPORT.md
```

Format SHORT / STANDARD INTEGRATION:

```text
# TASK-041 REPORT

STATUS:
DONE
lub
BLOCKED

CHANGED:
- ...

IMPLEMENTED:
- ProductAnalyticsFact:
- AnalyticsFilters:
- GetAnalyticsDashboard:
- SDS trend:
- Product x Location detail:
- availability overlay:

VALIDATION:
- unit/application:
- PostgreSQL integration:
- filesystem:
- focused regressions:
- query-count / N+1:
- git diff --check:

DATA SAFETY:
- operator data preserved:
- operator filesystem preserved:

SCOPE:
- schema change:
- migration:
- Core change:
- Domain entity change:
- Streamlit change:
- new dependencies:

DEVIATIONS:
- ...

NEXT:
- READY FOR CERBERUS REVIEW
lub
- BLOCKED — <reason>
```

Nie twórz długiego raportu narracyjnego, jeśli nie ma odchyleń.

---

# AUTHORIZATION

TASK-041 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-041.
```

Po wykonaniu:

```text
Codex report
→ Cerberus review
→ Architekt acceptance
→ dopiero potem TASK-042 — Streamlit dashboard / UX
```
