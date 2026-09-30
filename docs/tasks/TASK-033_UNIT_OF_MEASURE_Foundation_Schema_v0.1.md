# TASK-033 — UNIT_OF_MEASURE Foundation + Schema

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-007 — DATA-01 — Słownik jednostek miary  
**Task:** TASK-033  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-09-29  

## MODE

```text
INTEGRATION
```

---

## GOAL

Wdrożyć techniczny fundament `UNIT_OF_MEASURE` zgodnie z zatwierdzonym:

```text
BDR-006
CORE-001 v1.2-approved
TDR-005 v1.0-approved
SPRINT-007 v1.0-approved
```

Rezultat TASK-033:

```text
Domain
+ ORM
+ PostgreSQL schema
+ Alembic migration
+ seed jednostek
+ FK w PRODUCT_USAGE_LOCATION
+ FK w PRODUCT_USAGE_LOCATION_HISTORY
```

Bez finalnej integracji Streamlit UI — ta należy do TASK-034.

---

## AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie niezbędny kontekst:

1. `CORE-001_MSDS_Manager_v1.2-approved`
2. `BDR-006_Slownik_jednostek_miary_v1.0-approved`
3. `TDR-005_UNIT_OF_MEASURE_v1.0-approved`
4. `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved`
5. `SPRINT-007_DATA-01_Slownik_jednostek_v1.0-approved`
6. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
7. root `AGENTS.md`

Nie wykonuj repo-wide discovery bez potrzeby.

W razie sprzeczności lub braku decyzji:

```text
STOP / BLOCKED
```

Nie zgaduj.

---

## KNOWN STARTING POINTS

Minimalnie sprawdź istniejące miejsca odpowiedzialne za:

```text
Domain:
ProductUsageLocation
history snapshot model

Infrastructure:
SQLAlchemy ORM models
ProductUsageLocation repository
ProductUsageLocationHistory repository

Migrations:
migrations/versions/

Tests:
testy quantity/history/schema/migrations
```

Jeżeli nazwy plików różnią się od oczekiwanych, znajdź ich bezpośrednie odpowiedniki i nie rozszerzaj eksploracji poza niezbędny zakres.

---

## EXPECTED CHANGE SURFACE

Oczekiwane obszary zmian:

```text
app/domain/
app/infrastructure/db/
migrations/versions/
tests/
```

Dopuszczalne minimalne zmiany w Application wyłącznie wtedy, gdy są konieczne do utrzymania spójnych kontraktów Domain/Repository po zmianie typu jednostki.

Nie implementuj jeszcze finalnego Streamlit UI dla wyboru jednostek.

---

## DO

### 1. Domain — UNIT_OF_MEASURE

Dodaj minimalny model domenowy odpowiadający:

```text
UnitOfMeasure
├── unit_id
├── code
├── name
├── category
└── status
```

Kategorie:

```text
VOLUME
MASS
COUNT
```

Statusy:

```text
ACTIVE
INACTIVE
```

Nie dodawaj conversion factor ani base unit.

---

### 2. Domain — PRODUCT_USAGE_LOCATION

Zastąp techniczną reprezentację swobodnego tekstu jednostki referencją jednostki.

Docelowa semantyka:

```text
peak_quantity_value
peak_quantity_unit_id

monthly_consumption_value
monthly_consumption_unit_id
```

Zachowaj:

```text
peak >= 0
monthly >= 0 jeśli podane
0 != NULL
monthly value NULL → monthly unit NULL
monthly value NOT NULL → monthly unit NOT NULL
```

Nie wprowadzaj automatycznych konwersji.

---

### 3. ORM — UNIT_OF_MEASURE

Dodaj tabelę:

```text
unit_of_measure
```

Minimalnie:

```text
unit_id UUID PK
code VARCHAR NOT NULL UNIQUE
name VARCHAR NOT NULL
category VARCHAR NOT NULL
status VARCHAR NOT NULL
```

Dodaj zatwierdzone constraints:

```text
category IN ('VOLUME', 'MASS', 'COUNT')
status IN ('ACTIVE', 'INACTIVE')
```

---

### 4. ORM — current state

W `product_usage_locations`:

```text
peak_quantity_unit
→ peak_quantity_unit_id FK

monthly_consumption_unit
→ monthly_consumption_unit_id FK
```

Reguły:

```text
peak_quantity_unit_id NOT NULL
monthly pair spójne
```

---

### 5. ORM — history

W `product_usage_location_history`:

```text
peak_quantity_unit
→ peak_quantity_unit_id FK

monthly_consumption_unit
→ monthly_consumption_unit_id FK
```

Jednostka jest częścią snapshotu historycznego.

Nie zmieniaj modelu historii TDR-004.

---

### 6. Alembic

Utwórz dokładnie jedną nową rewizję Alembic dla TASK-033.

Migracja musi:

```text
CREATE unit_of_measure
seed l/ml/kg/g/szt
dodać unit_id columns do current
dodać unit_id columns do history
dodać FK/constraints
usunąć stare tekstowe unit columns
```

Minimalny seed:

```text
l    litr        VOLUME ACTIVE
ml   mililitr    VOLUME ACTIVE
kg   kilogram    MASS   ACTIVE
g    gram        MASS   ACTIVE
szt  sztuka      COUNT  ACTIVE
```

Seed ma być deterministyczny.

---

### 7. Preflight istniejących danych

Nie implementuj heurystycznego mapowania istniejących tekstowych jednostek.

Przed wykonaniem migracji na niepustym schema sprawdź obecność rekordów w:

```text
product_usage_locations
product_usage_location_history
```

Jeżeli rekordy istnieją i migracja nie może zostać bezpiecznie wykonana bez ich mapowania:

```text
STOP / BLOCKED
```

Nie usuwaj danych automatycznie.

Nie buduj mappera danych testowych.

W izolowanych testach migration fixture może używać pustych tabel zgodnie z TDR-005.

---

### 8. Downgrade

Downgrade musi odtworzyć tekstowe kolumny przy użyciu kanonicznego:

```text
unit_of_measure.code
```

Następnie poprawnie usunąć FK / unit columns / `unit_of_measure`.

Wymagany test:

```text
upgrade
→ downgrade
→ re-upgrade
```

---

### 9. Repositories

Dostosuj persistence tak, aby current state i history zapisywały `unit_id`, nie tekst jednostki.

Jeżeli minimalny repository `UnitOfMeasureRepository` jest konieczny dla testów/integracji warstw, można wprowadzić:

```text
get_by_id()
list_active()
```

Nie twórz pełnego CRUD frameworka.

---

## DO NOT

Nie:

- implementuj TASK-034,
- zmieniaj finalnego UI Streamlit,
- dodawaj ekranu administracji słownikiem,
- implementuj `Stan na dzień`,
- implementuj `Analizy`,
- dodawaj konwersji,
- dodawaj `base_unit`,
- dodawaj `conversion_factor`,
- importuj Excel,
- heurystycznie mapuj legacy text,
- automatycznie usuwaj operator data,
- zmieniaj mechanizmu historii TDR-004,
- dodawaj triggerów PostgreSQL,
- dodawaj JSONB audit framework,
- twórz nowego Unit of Work,
- refaktoruj niezwiązanych obszarów.

---

## VALIDATION

**LEVEL 2 — INTEGRATION**

Wykonaj focused + integration validation dla zmienionego zakresu.

Minimum:

```text
1. Domain UnitOfMeasure tests
2. ProductUsageLocation quantity/unit tests
3. ORM mapping tests
4. repository current-state tests
5. history snapshot tests
6. migration upgrade
7. migration downgrade
8. migration re-upgrade
9. seed verification
10. FK / CHECK / UNIQUE verification
11. Alembic current
12. Alembic check
13. schema drift check
14. SAWarning check dla uruchamianego zestawu
```

Nie wymagamy jeszcze pełnego checkpointu całego Sprintu; pełna regresja należy do TASK-035.

Jeżeli zmiany naruszają istniejące focused tests z powodu zatwierdzonej zmiany kontraktu, dostosuj je tylko w zakresie wynikającym z BDR-006/TDR-005.

---

## ACCEPTANCE CONDITIONS

TASK-033 = DONE tylko jeśli:

```text
unit_of_measure istnieje
seed 5 jednostek istnieje
code UNIQUE działa
category/status constraints działają
current state używa FK unit_id
history używa FK unit_id
monthly NULL semantics zachowane
0 != NULL zachowane
upgrade/downgrade/re-upgrade PASS
Alembic check PASS
schema drift NONE
brak conversion engine
brak legacy mapper
brak automatycznego cleanup operator data
```

---

## STOP CONDITIONS

Zatrzymaj Task jako `BLOCKED`, jeżeli:

1. zatwierdzone dokumenty są sprzeczne,
2. aktualny schema różni się od zakładanego i wymaga decyzji architektonicznej,
3. migracja wymaga automatycznego mapowania istniejących danych,
4. wykonanie wymaga zmiany Core poza BDR-006,
5. zachowanie historii wymaga odejścia od TDR-004,
6. odkryjesz więcej niż jeden Alembic head wymagający decyzji,
7. bez rozszerzenia scope nie można zachować integralności danych.

Nie rozwiązuj tych punktów opportunistycznie.

---

## REPORT

**SHORT REPORT**

Raport ma zawierać:

```text
STATUS: DONE / BLOCKED

CHANGED:
- Domain
- ORM
- Migration
- Repositories
- Tests

MIGRATION:
- revision id
- previous head
- new head
- upgrade/downgrade/re-upgrade

VALIDATION:
- focused tests result
- Alembic current
- Alembic check
- schema drift
- SAWarning

DATA SAFETY:
- operator DB touched? YES/NO
- automatic cleanup? YES/NO

DEVIATIONS:
- NONE albo lista

NEXT:
- READY FOR TASK-034 / BLOCKED
```

Nie twórz długiego repo-wide raportu bez potrzeby.

---

## AUTHORIZATION

```text
TASK-033
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Task może zostać wykonany dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-033
```
