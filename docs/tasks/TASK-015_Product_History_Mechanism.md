# TASK-015 — Product History Mechanism

**Projekt:** MSDS Manager  
**Task ID:** TASK-015  
**Sprint:** SPRINT-002 v1.2-approved  
**Status:** READY  
**Decyzja odblokowująca:** TDR-004 v1.0-approved  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI

## 1. Cel

Zaimplementować minimalny mechanizm historii istotnych danych Core zgodnie z `TDR-004 v1.0-approved`, wystarczający do zamknięcia Sprintu 2 i wykonania TASK-016.

Historia ma odpowiadać:
- co się zmieniło,
- kiedy,
- jaki był zatwierdzony stan / jaka była ilość.

Nie budować uniwersalnego systemu audytu.

## 2. Źródła obowiązujące

Przed implementacją przeczytaj:
- `TDR-004 v1.0-approved` — nadrzędne źródło mechanizmu historii,
- `CORE-001 v1.2-approved`,
- `BDR-002 v1.2-approved`,
- `SPRINT-002 v1.2-approved`,
- TDR-001, TDR-003,
- aktualny root `AGENTS.md`,
- zaakceptowane implementacje/raporty TASK-009..014.

W razie konfliktu: **STOP — nie zgaduj.**

## 3. Baseline

Przed zmianami:
- uruchom pełny pytest,
- `alembic current`,
- `alembic check`,
- ustal aktualną liczbę tabel i rewizji,
- sprawdź rzeczywisty stan repozytorium.

Nie zakładaj numeru kolejnej rewizji z Tasku.

## 4. Zakres persistence

Dodaj trzy jawne obszary historii:

```text
PRODUCT_HISTORY
USAGE_LOCATION_HISTORY
PRODUCT_USAGE_LOCATION_HISTORY
```

Historia:
- snapshot,
- append-only w standardowym workflow,
- bez generic `AUDIT_LOG`,
- bez JSONB audit framework,
- bez triggerów,
- bez event sourcing.

## 5. PRODUCT_HISTORY

Snapshot co najmniej:

```text
history_id
product_id
usage_status
use_description
use_restriction
waste_type
waste_code
changed_at
```

Snapshot twórz przy istniejącym `UpdateProductAdministrativeData`.

`usage_status` ma być elementem snapshotu, ale TASK-015 **nie tworzy** `SetProductStatus` ani nowego workflow statusu.

Nie rozszerzaj edycji pól tożsamości:
`product_name`, `manufacturer_product_code`, `manufacturer_id`.

## 6. USAGE_LOCATION_HISTORY

Snapshot co najmniej:

```text
history_id
location_id
status
changed_at
```

Historia rejestruje istniejące:
- `DeactivateUsageLocation`: ACTIVE → INACTIVE,
- `ReactivateUsageLocation`: INACTIVE → ACTIVE.

Ten sam `location_id`. Bez DELETE.

Nie dodawaj historii `CreateUsageLocation` tylko „dla kompletności”, jeżeli nie jest wymagana przez TDR-004.

## 7. PRODUCT_USAGE_LOCATION_HISTORY

Snapshot co najmniej:

```text
history_id
product_id
location_id
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
changed_at
```

Snapshot powstaje:
1. przy `AssignProductUsageLocation` — pierwszy stan,
2. przy `UpdateProductUsageLocation` — kolejny stan.

Zachowaj `Decimal`, brak konwersji jednostek oraz semantykę:
- peak 0 = prawidłowe zero,
- monthly NULL = brak informacji,
- monthly 0 = świadome zero.

## 8. changed_at

Każdy snapshot ma `changed_at`.

Odczyt historii musi być deterministyczny:
`changed_at`, a przy remisie `history_id`.

Nie dodawaj `changed_by`, `user_id`.

`change_type` jest opcjonalne: dodaj tylko, jeśli rzeczywiście upraszcza minimalną implementację. Nie buduj słownika eventów.

## 9. Application

Historia jest koordynowana przez Application.

Minimalnie dostosuj istniejące write use case'y:
- `UpdateProductAdministrativeData`,
- `DeactivateUsageLocation`,
- `ReactivateUsageLocation`,
- `AssignProductUsageLocation`,
- `UpdateProductUsageLocation`.

Nie twórz równoległych historycznych wersji use case'ów.

## 10. Porty i repozytoria

Dodaj minimalne jawne porty/repozytoria, np.:
- `ProductHistoryRepositoryPort`,
- `UsageLocationHistoryRepositoryPort`,
- `ProductUsageLocationHistoryRepositoryPort`.

Nazwy dostosuj do istniejącej konwencji.

Zakazane:
- GenericHistoryRepository,
- AuditRepository[T],
- GenericAuditService,
- GenericHistoryService.

## 11. Odczyt historii

Zapewnij minimalny techniczny odczyt potrzebny do testów i TASK-016:
- historia po `product_id`,
- historia po `location_id`,
- historia relacji po `product_id + location_id`.

Pełny ekran historii Streamlit nie jest wymagany.

## 12. PostgreSQL / ORM

Dodaj jawne modele ORM i tabele historii.

Każda tabela:
- własny PK `history_id`,
- właściwe identyfikatory Core,
- snapshot zatwierdzonych pól,
- brak standardowego UPDATE/DELETE w workflow.

Nie stosuj `ON DELETE CASCADE` z Core do historii.

Jeśli poprawny model FK wymaga niezatwierdzonej decyzji: **STOP**.

## 13. Alembic

Preferuj jedną spójną migrację TASK-015 dla trzech tabel historii i minimalnych indeksów.

Wymagane:
- upgrade,
- downgrade,
- re-upgrade,
- `alembic check`.

Nie zmieniaj istniejących tabel/enumów/constraintów Core poza zakresem niezbędnym dla zatwierdzonej historii.

Minimalnie rozważ indeksy:
- `(product_id, changed_at)`,
- `(location_id, changed_at)`,
- `(product_id, location_id, changed_at)`.

Bez optymalizacji „na przyszłość”.

## 14. Transakcje — krytyczne

Obowiązuje:

```text
current state change
+
history snapshot
=
ONE TRANSACTION
```

Użyj istniejącego `TransactionExecutor`.

Nie twórz nowego Unit of Work ani transaction managera.

Repozytoria nie wykonują commit/rollback.

Wymagania:
- current OK + history OK → commit obu,
- history FAIL → rollback current,
- current FAIL → brak history.

## 15. Append-only

Nie implementuj:
- UpdateHistory,
- DeleteHistory,
- PurgeHistory,
- RetentionCleanup.

Korekta = nowy current state + nowy snapshot. Stary snapshot pozostaje.

## 16. Testy

### Application/unit
Potwierdź:
- Product admin update tworzy pełny snapshot PRODUCT,
- identity nadal chronione,
- brak SetProductStatus/CreateProduct,
- deactivate tworzy INACTIVE snapshot,
- reactivate tworzy ACTIVE snapshot dla tego samego location_id,
- assignment tworzy initial snapshot,
- quantity update tworzy kolejny snapshot,
- Decimal/0/NULL/jednostki zachowują semantykę.

### PostgreSQL/integration
Potwierdź na rzeczywistym PostgreSQL:
- zapis wszystkich trzech rodzajów historii,
- deterministyczny odczyt,
- Decimal,
- NULL vs 0,
- istniejące constraints Core pozostają.

### Atomicity
Obowiązkowo:
1. current OK + history OK → commit obu,
2. kontrolowany history INSERT FAIL → rollback current,
3. current FAIL → brak history snapshot.

Nie obchodź `TransactionExecutor`.

Po testach nie pozostawiaj danych testowych.

## 17. UI

Nie buduj pełnego UI historii.

Nie dodawaj:
- timeline,
- dashboardu,
- eksportu,
- filtrów audytowych,
- „kto zmienił”,
- przeglądów okresowych,
- kodów kreskowych.

Jeśli minimalny read-only UI nie jest konieczny do TASK-015/TASK-016 — **nie dodawaj go**.

## 18. Poza zakresem

Bezwzględnie poza TASK-015:
- CreateProduct / CreateManufacturer,
- SetProductStatus,
- RemoveProductUsageLocation,
- DeleteUsageLocation,
- SDS/BHP/SAFETY_PROFILE/SDS_COMPONENT/REACH,
- generic audit,
- triggery,
- event sourcing,
- temporal framework,
- changed_by/users/permissions,
- correction_reason,
- retention/purge,
- backup,
- audyt/przegląd okresowy,
- barcode scanning.

## 19. Zasada MVP

Jeżeli istnieją dwa poprawne rozwiązania, wybierz prostsze, jeśli spełnia TDR-004, integralność, transakcyjność i testy.

Nie twórz abstrakcji „na przyszłość”.

## 20. Definition of Done

TASK-015 = DONE tylko gdy:
1. działają trzy jawne obszary historii,
2. Product admin update tworzy snapshot,
3. deactivate/reactivate tworzą snapshoty,
4. assignment/update quantity tworzą snapshoty,
5. historia jest append-only,
6. `changed_at` i deterministyczne sortowanie działają,
7. current + history są atomowe,
8. failure historii rollbackuje current,
9. failure current nie pozostawia historii,
10. Decimal i NULL/0 są zachowane,
11. Alembic upgrade/downgrade/re-upgrade działa,
12. `alembic check` bez rzeczywistego driftu,
13. wcześniejsze constraints Core zachowane,
14. pełny pytest przechodzi,
15. brak `SAWarning`,
16. brak nowych niezatwierdzonych zależności,
17. brak danych testowych w finalnej bazie,
18. brak triggerów/generic audit/event sourcing,
19. TASK-016 nie został rozpoczęty,
20. zakres TDR-004 nie został rozszerzony.

## 21. Raport

Utwórz:

```text
docs/task_reports/TASK-015_REPORT.md
```

Raport ma zawierać:
- DONE / PARTIAL / BLOCKED,
- zmienione pliki,
- modele/tabele historii,
- porty/repozytoria,
- podłączone use case'y,
- atomicity current + history,
- migrację revision/down_revision,
- indeksy/FK,
- testy unit/application/PostgreSQL/rollback,
- pełny pytest i SAWarning,
- `alembic current`,
- liczbę rewizji i tabel,
- `alembic check`,
- brak danych testowych,
- potwierdzenie braku triggerów/generic audit/event sourcing,
- odstępstwa i ryzyka.

## 22. STOP CONDITIONS

STOP, jeśli wymagane byłoby:
- nowe znaczenie/status/enum biznesowy,
- zmiana tożsamości PRODUCT,
- publiczny CreateProduct,
- SetProductStatus,
- usuwanie relacji/lokalizacji historycznej,
- trigger/generic audit/UoW framework,
- model użytkowników,
- niezatwierdzona polityka FK/usuwania,
- zmiana Core poza zatwierdzonym zakresem.

## 23. Oczekiwany stan końcowy

```text
PRODUCT + PRODUCT_HISTORY
USAGE_LOCATION + USAGE_LOCATION_HISTORY
PRODUCT_USAGE_LOCATION + PRODUCT_USAGE_LOCATION_HISTORY
        ↓
Application-controlled snapshots
        ↓
existing TransactionExecutor
        ↓
PostgreSQL
```

Po akceptacji TASK-015 następnym krokiem będzie TASK-016, ale nie jest częścią tego Tasku.

## 24. Autoryzacja

Sama obecność pliku nie oznacza zgody na wykonanie.

Codex rozpoczyna dopiero po poleceniu:

```text
Wykonaj TASK-015.
```

Raport zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-016.
```
