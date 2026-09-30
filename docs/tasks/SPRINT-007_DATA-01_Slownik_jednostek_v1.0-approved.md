# SPRINT-007 — DATA-01 — Słownik jednostek miary

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-007  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-09-29  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel Sprintu

Celem SPRINT-007 jest wdrożenie zatwierdzonego `DATA-01`:

```text
centralny UNIT_OF_MEASURE
→ kontrolowane jednostki dla MAX i monthly consumption
→ referencje w current state
→ referencje w historii
→ wybór jednostki z listy ACTIVE w UI
```

Sprint ma przygotować stabilny fundament danych przed dalszym rozwojem `Analizy`.

---

## 2. Źródła nadrzędne

Sprint należy realizować zgodnie z:

- `BDR-006_Slownik_jednostek_miary_v1.0-approved`,
- `CORE-001_MSDS_Manager_v1.2-approved`,
- `TDR-005_UNIT_OF_MEASURE_v1.0-approved`,
- `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved`,
- `TDR-001_MSDS_Manager`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`,
- `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED`.

W razie konfliktu:

```text
STOP
```

Codex nie zgaduje.

---

## 3. Zakres funkcjonalny

Po zakończeniu Sprintu użytkownik:

1. nie wpisuje jednostki MAX jako swobodnego tekstu,
2. nie wpisuje jednostki monthly consumption jako swobodnego tekstu,
3. wybiera jednostkę z kontrolowanego słownika,
4. widzi w aplikacji kod jednostki (`l`, `kg`, `szt` itd.),
5. zachowuje istniejącą semantykę:
   - MAX obowiązkowe,
   - monthly optional,
   - `0` różne od `NULL`,
6. nie ma dostępu do automatycznych konwersji jednostek.

---

## 4. Zakres techniczny

Sprint obejmuje:

```text
UNIT_OF_MEASURE
Domain
Application
Repositories
SQLAlchemy ORM
PostgreSQL
Alembic
PRODUCT_USAGE_LOCATION
PRODUCT_USAGE_LOCATION_HISTORY
Streamlit usage forms
Supervisory read model
Tests
```

---

## 5. Poza zakresem Sprintu

SPRINT-007 nie obejmuje:

- `Analizy`,
- `Stan na dzień`,
- snapshotów przeglądów fizycznych,
- konwersji `kg ↔ g`, `l ↔ ml`,
- tabel współczynników konwersji,
- importu starego Excela,
- migracji legacy,
- parsera SDS,
- PARSER-02 / PARSER-03,
- DOC-01,
- UI-11 / UI-14,
- REACH,
- osobnego ekranu administracyjnego CRUD dla słownika,
- automatycznego kasowania danych operatora.

---

## 6. Seed słownika

Minimalny seed:

| Kod | Nazwa | Kategoria |
|---|---|---|
| `l` | litr | VOLUME |
| `ml` | mililitr | VOLUME |
| `kg` | kilogram | MASS |
| `g` | gram | MASS |
| `szt` | sztuka | COUNT |

Wszystkie rekordy startowe:

```text
status = ACTIVE
```

---

## 7. Zasada danych lokalnych operatora

Aktualna lokalna baza może zawierać dane testowe.

Sprint nie ma tworzyć heurystycznego mapowania takich danych.

Przed zastosowaniem migracji na lokalnej bazie operatora:

```text
jeżeli istnieją rekordy w:
PRODUCT_USAGE_LOCATION
lub
PRODUCT_USAGE_LOCATION_HISTORY

→ STOP migracji operator DB
→ jawny manual cleanup danych testowych
→ ponowne uruchomienie migracji
```

Codex nie usuwa automatycznie lokalnych danych operatora.

Testy i acceptance korzystają z izolowanego środowiska zgodnie z dotychczasową praktyką projektu.

---

## 8. Plan wykonawczy

Sprint dzieli się na trzy Taski.

### TASK-033 — UNIT_OF_MEASURE Foundation + Schema

**MODE:** INTEGRATION

Cel:

```text
wdrożyć model Domain/ORM/PostgreSQL
+ migrację Alembic
+ seed
+ FK w current/history
```

Zakres:

- model `UnitOfMeasure`,
- `unit_id`,
- `code`,
- `name`,
- `category`,
- `status`,
- status `ACTIVE / INACTIVE`,
- kategorie `VOLUME / MASS / COUNT`,
- tabela `unit_of_measure`,
- `peak_quantity_unit_id`,
- `monthly_consumption_unit_id`,
- analogiczne referencje w historii,
- constraints,
- upgrade/downgrade,
- zachowanie TDR-004.

Nie obejmuje jeszcze finalnego Streamlit UX.

Walidacja: LEVEL 2 + schema checks.

---

### TASK-034 — Application + UI Integration

**MODE:** INTEGRATION

Cel:

```text
zastąpić free-text jednostek kontrolowanym wyborem ACTIVE
```

Zakres:

- minimalny repository/port jednostek,
- `list_active()`,
- `get_by_id()`,
- integracja z `AssignProductUsageLocation`,
- integracja z `UpdateProductUsageLocation`,
- reguła ACTIVE dla nowych/edytowanych wartości,
- DTO/read models,
- Product details,
- Widok nadzorczy,
- formularz dodania przypisania,
- formularz edycji przypisania,
- miesięczne zużycie nadal opcjonalne,
- kody jednostek widoczne użytkownikowi,
- UUID jednostek niewidoczne w normalnym workflow.

Walidacja: LEVEL 2 + focused UI/integration tests.

---

### TASK-035 — SPRINT-007 Acceptance / Checkpoint

**MODE:** ACCEPTANCE

Cel:

```text
udowodnić pełną spójność DATA-01
i brak regresji istniejącego MVP
```

Zakres walidacji:

- pełny pytest,
- E2E,
- SAWarning,
- Alembic current,
- Alembic check,
- upgrade/downgrade/re-upgrade,
- schema drift,
- historia current + snapshot,
- UI unit selection,
- supervisory display,
- operator data preserved,
- brak importu legacy,
- brak conversion engine.

Walidacja: LEVEL 3.

---

## 9. Definition of Done

SPRINT-007 jest gotowy do zamknięcia, jeżeli:

| # | Kryterium | Oczekiwany wynik |
|---|---|---|
| 1 | `unit_of_measure` istnieje | PASS |
| 2 | seed `l/ml/kg/g/szt` istnieje | PASS |
| 3 | `code` jest unikalny | PASS |
| 4 | category ograniczone do zatwierdzonych wartości | PASS |
| 5 | status ograniczony do ACTIVE/INACTIVE | PASS |
| 6 | MAX wskazuje jednostkę przez kontrolowaną referencję | PASS |
| 7 | monthly wskazuje jednostkę przez kontrolowaną referencję | PASS |
| 8 | monthly NULL → unit NULL | PASS |
| 9 | `0` ≠ `NULL` | PASS |
| 10 | INACTIVE nie może być nowym wyborem | PASS |
| 11 | INACTIVE pozostaje czytelne historycznie | PASS |
| 12 | zmiana jednostki tworzy snapshot historii | PASS |
| 13 | current + history są atomowe | PASS |
| 14 | UI nie ma free-text dla jednostki | PASS |
| 15 | UI pokazuje kod jednostki | PASS |
| 16 | UUID jednostki nie jest użytkowym elementem UI | PASS |
| 17 | brak automatycznej konwersji | PASS |
| 18 | brak importu legacy | PASS |
| 19 | pełna regresja przechodzi | PASS |
| 20 | Alembic check bez driftu | PASS |

---

## 10. Ryzyka i kontrola

### RYZYKO 1 — istniejące dane testowe operatora

Kontrola:

```text
preflight
→ STOP
→ manual cleanup
```

Nie tworzymy jednorazowego mappera.

### RYZYKO 2 — regresja historii

Kontrola:

```text
TDR-004 pozostaje nadrzędny
current + history = jedna transakcja
```

### RYZYKO 3 — rozszerzenie do conversion engine

Kontrola:

```text
poza zakresem
```

Każda taka propozycja wymaga STOP / osobnej decyzji.

---

## 11. Granice dla Codexa

Codex nie może w ramach Sprintu:

- rozszerzać kategorii bez potrzeby,
- dodawać konwersji,
- tworzyć generycznego frameworka słowników,
- automatycznie czyścić operator DB,
- mapować historycznych tekstów jednostek,
- zmieniać mechanizmu historii,
- implementować `Analizy`,
- implementować parsera SDS,
- wykonywać opportunistic refactor poza zakresem.

---

## 12. Kryterium biznesowe Sprintu

Po SPRINT-007 system powinien osiągnąć stan:

```text
PRODUCT × LOCATION
      │
      ├── MAX + kontrolowana jednostka
      └── monthly + kontrolowana jednostka
                     │
                     ▼
               UNIT_OF_MEASURE
```

Daje to stabilny fundament dla kolejnego planowanego obszaru:

```text
ANALYTICS
```

bez wprowadzania konwersji jednostek.

---

## 13. Authorization boundary

`SPRINT-007 v1.0-approved` zatwierdza zakres Sprintu i kolejność:

```text
TASK-033
→ TASK-034
→ TASK-035
```

Sprint autoryzuje przygotowanie wskazanych Tasków, ale nie stanowi samodzielnego polecenia ich wykonania.

Każdy Task wymaga osobnej, jawnej autoryzacji wykonania dla Codexa.

Migracja lokalnej operator DB oraz ewentualny cleanup danych testowych pozostają kontrolowanymi działaniami zgodnie z TDR-005.

---

## 14. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-29 | Draft | Pierwszy Sprint DATA-01: UNIT_OF_MEASURE, schema/history, integracja Application/UI i acceptance |
| 1.0-approved | 2026-09-29 | Approved | Architekt Operacyjny zatwierdził zakres SPRINT-007 bez zmian merytorycznych |
