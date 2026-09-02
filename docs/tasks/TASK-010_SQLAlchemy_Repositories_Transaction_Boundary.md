# TASK-010 — SQLAlchemy Repositories + Transaction Boundary

**Projekt:** MSDS Manager  
**Task ID:** TASK-010  
**Sprint:** SPRINT-002 v1.2-approved — Rejestr produktów i miejsc stosowania  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Zaimplementować adaptery persistence SQLAlchemy dla kontraktów application zatwierdzonych w TASK-009 oraz ustanowić kontrolowaną granicę transakcji dla operacji zapisujących dane.

TASK-010 ma połączyć:

```text
Application Ports
        ↓
SQLAlchemy Repositories
        ↓
SQLAlchemy Session
        ↓
PostgreSQL
```

bez zmiany znaczenia domeny i bez wejścia w UI.

Zakres obejmuje persistence dla:

```text
PRODUCT
USAGE_LOCATION
PRODUCT_USAGE_LOCATION
MANUFACTURER (read-only — istniejący adapter)
```

---

## 2. Stan wejściowy

Po zaakceptowanym TASK-009:

```text
CORE                    v1.2-approved
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Tests                   81 passed
Schema drift            none
Business records        0
```

Warstwa application posiada:

```text
ProductRepositoryPort
UsageLocationRepositoryPort
ProductUsageLocationRepositoryPort
ManufacturerRepositoryPort
```

oraz use case'y:

```text
ListProducts
GetProductDetails
UpdateProductAdministrativeData

ListManufacturers

ListUsageLocations
CreateUsageLocation
DeactivateUsageLocation
ReactivateUsageLocation

AssignProductUsageLocation
UpdateProductUsageLocation
```

TASK-010 nie zmienia ich semantyki.

---

## 3. Źródła nadrzędne

Implementacja musi być zgodna z:

1. `CORE-001 v1.2-approved`,
2. `BDR-002 v1.2-approved`,
3. pozostałymi zatwierdzonymi `BDR-001..005`,
4. `TDR-001..003`,
5. `SPRINT-002 v1.2-approved`,
6. zaakceptowanymi rezultatami TASK-008, TASK-009-ALIGN i TASK-009,
7. root `AGENTS.md`.

Jeżeli poprawna implementacja wymaga nowej decyzji biznesowej lub zmiany Core:

```text
STOP
```

---

# CZĘŚĆ A — ZASADA ARCHITEKTONICZNA

## 4. Kierunek zależności

Obowiązuje:

```text
presentation
     ↓
application
     ↓
domain

infrastructure
     ↑
implementuje application ports
```

Repozytoria SQLAlchemy:

- należą do `app/infrastructure/db/repositories/`,
- implementują porty z `app/application/ports/`,
- mogą importować Domain i ORM,
- nie mogą definiować nowych reguł biznesowych,
- nie mogą zmieniać kontraktów application dla wygody ORM.

Application nie importuje infrastruktury.

---

## 5. Brak generic repository

Nie implementuj:

```text
GenericRepository
BaseRepository
CRUDRepository
Repository[T]
```

Każdy adapter ma obsługiwać wyłącznie operacje wymagane przez odpowiadający port.

---

# CZĘŚĆ B — PRODUCT REPOSITORY

## 6. `SqlAlchemyProductRepository`

Zaimplementuj adapter dla `ProductRepositoryPort`.

Musi obsługiwać operacje wymagane przez TASK-009, co najmniej:

```text
list_products()
get_product_details(product_id)
update_administrative_data(...)
```

Nazwy techniczne mogą odpowiadać rzeczywistemu portowi.

### 6.1. ListProducts

Zapytanie ma zwracać dane zgodne z application DTO, w tym:

```text
product_id
product_name
manufacturer_product_code
manufacturer_id
manufacturer_name
usage_status
use_description
use_restriction
waste_type
waste_code
```

Nie zwracaj ORM poza infrastructure.

### 6.2. GetProductDetails

Odczyt szczegółów produktu ma obejmować:

```text
PRODUCT
MANUFACTURER
PRODUCT_USAGE_LOCATION
USAGE_LOCATION
```

Dane lokalizacji:

```text
location_id
location_name
location_status
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie włączaj SDS/BHP/SafetyProfile.

Brak produktu ma zostać przetłumaczony do kontraktu oczekiwanego przez application, bez ujawniania SQLAlchemy exception.

### 6.3. UpdateProductAdministrativeData

Aktualizuj wyłącznie:

```text
use_description
use_restriction
waste_type
waste_code
```

Nie wolno aktualizować:

```text
product_name
manufacturer_product_code
manufacturer_id
usage_status
```

Nie wykonuj pełnego merge encji, jeżeli mógłby przypadkowo nadpisać chronione pola.

---

# CZĘŚĆ C — USAGE_LOCATION REPOSITORY

## 7. `SqlAlchemyUsageLocationRepository`

Zaimplementuj adapter dla `UsageLocationRepositoryPort`.

Musi obsługiwać co najmniej:

```text
list
get_by_id
add
update_status
```

zgodnie z portem TASK-009.

### 7.1. List

Ogólna lista administracyjna zwraca:

```text
ACTIVE
INACTIVE
```

Nie filtruj automatycznie `INACTIVE` z ogólnej listy.

### 7.2. Get by ID

Zwracaj model domenowy `UsageLocation` lub kontrakt zgodny z portem.

Nie zwracaj ORM do application.

### 7.3. Add

Persistuj nową domenową `UsageLocation`.

Status nowej lokalizacji wynika z Domain:

```text
ACTIVE
```

Nie dodawaj DB-side business default poza istniejącym Core.

### 7.4. Update status

Zapisuj wynik zatwierdzonych przejść:

```text
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Repozytorium nie podejmuje decyzji, czy przejście jest dozwolone — otrzymuje wynik z Domain/use case.

Nie implementuj delete.

---

# CZĘŚĆ D — PRODUCT_USAGE_LOCATION REPOSITORY

## 8. `SqlAlchemyProductUsageLocationRepository`

Zaimplementuj adapter dla `ProductUsageLocationRepositoryPort`.

Musi obsługiwać:

```text
add
get / exists — jeśli wymaga tego port
update_quantities
```

wyłącznie w zakresie istniejącego kontraktu.

### 8.1. Add

Persistuj:

```text
product_id
location_id
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie duplikuj w repository walidacji Domain:

- `>= 0`,
- `0 != NULL`,
- monthly value/unit pair.

PostgreSQL constraints pozostają drugą linią ochrony.

### 8.2. Lokalizacja INACTIVE

Reguła:

```text
nowe przypisanie tylko do ACTIVE
```

jest regułą Application/Core i została już zaimplementowana w TASK-009.

Repository nie powinno tworzyć alternatywnego mechanizmu biznesowego, ale musi poprawnie współpracować z use case'em i nie omijać jego decyzji.

Nie dodawaj bezpośredniej publicznej metody pozwalającej UI ominąć use case.

### 8.3. Update quantities

Aktualizuj wyłącznie:

```text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie zmieniaj:

```text
product_id
location_id
```

Nie implementuj delete/remove.

---

# CZĘŚĆ E — MANUFACTURER

## 9. Istniejący adapter

Zachowaj istniejący:

```text
SqlAlchemyManufacturerRepository
```

z TASK-007.

Możesz go minimalnie dostosować wyłącznie, jeśli jest to konieczne dla zgodności technicznej po TASK-009.

Nie dodawaj:

```text
CreateManufacturer
UpdateManufacturer
DeleteManufacturer
```

---

# CZĘŚĆ F — MAPPING ORM ↔ DOMAIN / DTO

## 10. Jawny mapping

Mapping ma być jawny i czytelny.

Nie przekazuj ORM poza infrastructure.

Dopuszczalne podejścia:

- małe funkcje mapper,
- prywatne metody adaptera,
- prosty moduł mapperów w `infrastructure/db/`.

Nie twórz rozbudowanego automapper framework.

### 10.1. Decimal

Wartości `Numeric` muszą zostać zachowane jako:

```text
Decimal
```

Nie konwertuj do `float`.

### 10.2. Enumy

ORM `VARCHAR + CHECK` ma zostać mapowany na odpowiednie enumy Domain, w tym:

```text
ProductUsageStatus
UsageLocationStatus
```

Nie używaj surowych stringów w application, jeśli zatwierdzony kontrakt Domain używa enumu.

---

# CZĘŚĆ G — GRANICA TRANSAKCJI

## 11. Cel transakcji

Operacje zapisujące muszą mieć jednoznaczną granicę:

```text
use case
   ↓
session transaction
   ↓
repository operations
   ↓
commit OR rollback
```

TASK-010 nie może zostawić `commit()` rozproszonego przypadkowo po repozytoriach i UI.

---

## 12. Minimalne rozwiązanie

Preferuj najprostszy mechanizm zgodny z istniejącą architekturą.

Dopuszczalne jest np.:

```text
Session / session factory
+
application service / transaction wrapper
```

lub równoważne rozwiązanie, jeśli wynika z istniejącego kodu.

Nie buduj pełnego frameworka Unit of Work, jeśli nie jest potrzebny.

### 12.1. Zasada

Repository:

- wykonuje operacje na przekazanej sesji,
- nie powinno samodzielnie arbitralnie wykonywać `commit()` po każdej metodzie.

Granica transakcji powinna być wyżej niż pojedynczy repository call.

### 12.2. Rollback

W przypadku błędu:

```text
rollback
```

musi przywrócić spójny stan.

Nie pozostawiaj częściowo zapisanych zmian.

---

## 13. Zakres transakcji w TASK-010

Obowiązkowo przetestuj transakcyjnie co najmniej operacje zapisujące:

```text
UpdateProductAdministrativeData
CreateUsageLocation
DeactivateUsageLocation
ReactivateUsageLocation
AssignProductUsageLocation
UpdateProductUsageLocation
```

Nie implementuj jeszcze wieloetapowych transakcji SDS/BHP.

---

# CZĘŚĆ H — OBSŁUGA BŁĘDÓW

## 14. Translacja błędów infrastruktury

Nie ujawniaj application:

- `IntegrityError`,
- `NoResultFound`,
- `SQLAlchemyError`,
- psycopg exceptions.

Mapuj tylko to, co jest potrzebne do istniejących application/domain errors.

Nie projektuj rozbudowanej hierarchii wyjątków „na przyszłość”.

---

## 15. Konflikty integralności

Jeśli PostgreSQL odrzuci zapis z powodu istniejącego zatwierdzonego constraintu:

- wykonaj rollback,
- nie zmieniaj constraintu,
- nie obchodź reguły przez retry z innymi danymi,
- przetłumacz błąd na kontrolowany wyjątek tylko wtedy, gdy istniejący kontrakt application tego wymaga.

Jeżeli trzeba wymyślić nową semantykę konfliktu:

```text
STOP
```

---

# CZĘŚĆ I — TESTY INTEGRACYJNE POSTGRESQL

## 16. Realny PostgreSQL

Nowe testy persistence używają rzeczywistego PostgreSQL.

Nie używaj SQLite.

Testy muszą po sobie sprzątać.

---

## 17. Product repository tests

Potwierdź co najmniej:

1. lista produktów zwraca poprawne dane producenta,
2. szczegóły produktu zwracają lokalizacje i quantity,
3. `Decimal` pozostaje `Decimal`,
4. aktualizacja administracyjna zmienia tylko dozwolone pola,
5. tożsamość produktu pozostaje bez zmian,
6. `usage_status` pozostaje bez zmian,
7. brak produktu daje kontrolowany rezultat/wyjątek application.

---

## 18. UsageLocation repository tests

Potwierdź:

1. zapis nowej `ACTIVE`,
2. odczyt `ACTIVE`,
3. dezaktywację do `INACTIVE`,
4. reaktywację do `ACTIVE`,
5. zachowanie `location_id`,
6. brak fizycznego delete,
7. lista administracyjna zawiera oba statusy.

---

## 19. ProductUsageLocation repository tests

Potwierdź:

1. zapis przypisania,
2. peak `0`,
3. monthly `NULL/NULL`,
4. monthly `0 + unit`,
5. różne jednostki peak/monthly,
6. aktualizację ilości bez zmiany PK,
7. PostgreSQL odrzuca niepoprawne ilości zgodnie z istniejącymi CHECK,
8. rollback usuwa skutki nieudanego zapisu.

---

# CZĘŚĆ J — TESTY TRANSAKCYJNE

## 20. Commit

Potwierdź, że poprawna operacja zapisu:

```text
commit
```

utrwala zmianę i jest widoczna w nowej sesji.

## 21. Rollback

Zaprojektuj test, w którym jedna operacja transakcyjna zawiera poprawną zmianę oraz następnie celowy błąd persistence.

Po rollback:

```text
żadna część transakcji nie pozostaje utrwalona
```

Nie testuj wyłącznie `session.rollback()` w izolacji — test ma potwierdzić realny efekt w PostgreSQL.

---

# CZĘŚĆ K — APPLICATION + INFRASTRUCTURE INTEGRATION

## 22. Pionowe testy use case → repository → PostgreSQL

Dodaj minimalne testy integracyjne potwierdzające co najmniej:

```text
CreateUsageLocation
        ↓
SqlAlchemyUsageLocationRepository
        ↓
PostgreSQL
```

oraz:

```text
UpdateProductAdministrativeData
        ↓
SqlAlchemyProductRepository
        ↓
PostgreSQL
```

oraz:

```text
AssignProductUsageLocation
        ↓
repositories
        ↓
PostgreSQL
```

Nie testuj UI.

---

# CZĘŚĆ L — SCHEMA / ALEMBIC

## 23. Brak zmiany schematu

TASK-010 nie wymaga zmian ORM ani schema.

Oczekiwany stan:

```text
Alembic revisions       4
PostgreSQL current      d2b4f6a8c190 (head)
Application tables      9
Schema drift            none
```

Nie twórz piątej migracji.

Nie zmieniaj:

- ORM models,
- enum CHECK constraints,
- TASK-006 constraints,
- TASK-008 quantity constraints,
- `usage_location_status_values`,
- Alembic config/filter.

Jeżeli persistence wymaga zmiany schema:

```text
STOP
```

---

## 24. Kontrola Alembic

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
d2b4f6a8c190 (head)
No new upgrade operations detected.
```

---

# CZĘŚĆ M — ARCHITEKTURA

## 25. Granice

Potwierdź:

```text
application
  NIE importuje infrastructure
  NIE importuje SQLAlchemy
  NIE importuje psycopg

domain
  NIE importuje application
  NIE importuje infrastructure
  NIE importuje SQLAlchemy

infrastructure
  może importować application/domain
```

Nie przenoś Session do Domain/Application.

---

# CZĘŚĆ N — HISTORIA

## 26. Historia poza zakresem

Nie implementuj:

- history tables,
- audit log,
- temporal tables,
- event sourcing,
- snapshotów,
- triggerów historii,
- history repository.

TASK-010 nie rozwiązuje TASK-015.

---

# CZĘŚĆ O — POZA ZAKRESEM

## 27. TASK-010 NIE implementuje

Nie implementuj:

- Streamlit,
- Product Registry View,
- formularzy,
- CreateProduct,
- CreateManufacturer,
- SDS workflow,
- BHP workflow,
- SetProductStatus,
- DeleteUsageLocation,
- RemoveProductUsageLocation,
- historii,
- importu Excel,
- REACH,
- BDO,
- modułu odpadów,
- słownika/konwersji jednostek,
- generic repository,
- pełnego Unit of Work framework,
- CQRS,
- event bus,
- nowych bibliotek.

---

# CZĘŚĆ P — ZALEŻNOŚCI

## 28. Brak nowych bibliotek

Nie dodawaj nowych zależności.

Użyj istniejących:

- SQLAlchemy,
- psycopg,
- pytest.

Jeżeli poprawne wykonanie wymaga nowej biblioteki:

```text
STOP
```

---

# CZĘŚĆ Q — GIT I BEZPIECZEŃSTWO

## 29. Kontrole

Wykonaj:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:

- `.env` ignored i untracked,
- brak sekretów,
- brak dumpów/backupów,
- brak PDF/MSG,
- brak danych testowych,
- brak nowych zależności.

Nie wykonuj commit/push bez jawnego polecenia.

---

# CZĘŚĆ R — STOP CONDITIONS

## 30. STOP

Raportuj `PARTIAL/BLOCKED`, jeżeli:

- stan repo/DB różni się istotnie od zaakceptowanego TASK-009,
- potrzebna jest zmiana ORM/schema,
- potrzebna jest nowa migracja,
- port wymaga zmiany kontraktu Core,
- poprawna obsługa konfliktu wymaga nowej decyzji biznesowej,
- transakcja wymaga rozbudowanego UoW/frameworka nieuzasadnionego obecnym zakresem,
- potrzebna jest nowa biblioteka,
- zakres wchodzi w UI/TASK-012,
- zakres wchodzi w historię/TASK-015,
- zakres wchodzi w SDS/BHP.

---

# CZĘŚĆ S — KRYTERIA AKCEPTACJI

## 31. TASK-010 = DONE, jeżeli

1. istnieje `SqlAlchemyProductRepository`,
2. implementuje aktualny `ProductRepositoryPort`,
3. istnieje `SqlAlchemyUsageLocationRepository`,
4. implementuje aktualny `UsageLocationRepositoryPort`,
5. istnieje `SqlAlchemyProductUsageLocationRepository`,
6. implementuje aktualny `ProductUsageLocationRepositoryPort`,
7. istniejący `SqlAlchemyManufacturerRepository` nadal działa,
8. ORM nie wycieka do application,
9. mapping ORM ↔ Domain/DTO jest jawny,
10. `Decimal` nie jest konwertowany do float,
11. Product update zmienia tylko dozwolone pola,
12. UsageLocation add/status działa,
13. deactivate/reactivate zachowuje `location_id`,
14. ProductUsageLocation add/update działa,
15. brak delete/remove,
16. jest jednoznaczna granica transakcji,
17. repozytoria nie robią przypadkowego commit-per-method,
18. poprawny zapis kończy się commit,
19. błąd powoduje rollback,
20. rollback nie pozostawia częściowych zmian,
21. błędy infrastruktury nie wyciekają do application w niekontrolowany sposób,
22. testy repository na PostgreSQL przechodzą,
23. testy transakcji przechodzą,
24. pionowe testy application → repository → PostgreSQL przechodzą,
25. pełna regresja przechodzi bez `SAWarning`,
26. application/domain boundaries pozostają czyste,
27. brak zmian ORM,
28. brak piątej migracji,
29. PostgreSQL nadal ma 9 tabel,
30. current = `d2b4f6a8c190 (head)`,
31. `alembic check` nie wykazuje driftu,
32. brak danych testowych po testach,
33. brak nowych bibliotek,
34. brak historii,
35. brak UI,
36. utworzono raport TASK-010,
37. TASK-011 nie został rozpoczęty.

---

# CZĘŚĆ T — RAPORT

## 32. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-010_REPORT.md
```

Raport ma zawierać:

1. Status.
2. Stan wejściowy.
3. Utworzone/zmienione repository adapters.
4. Mapping ORM ↔ Domain/DTO.
5. Product repository behavior.
6. UsageLocation repository behavior.
7. ProductUsageLocation repository behavior.
8. Manufacturer adapter — potwierdzenie regresji.
9. Granicę transakcji.
10. Miejsce commit/rollback.
11. Translację błędów infrastruktury.
12. Testy repository.
13. Testy transaction commit/rollback.
14. Pionowe testy application → PostgreSQL.
15. Pełny pytest i `SAWarning`.
16. Kontrolę granic architektury.
17. Potwierdzenie braku zmian schema.
18. `alembic current`.
19. `alembic check`.
20. Finalny stan PostgreSQL.
21. Git/bezpieczeństwo.
22. Odstępstwa.
23. Problemy/ryzyka.
24. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-011.
```

---

# CZĘŚĆ U — AUTORYZACJA

## 33. Autoryzacja wykonania

Obecność pliku:

```text
docs/tasks/TASK-010_SQLAlchemy_Repositories_Transaction_Boundary.md
```

w repozytorium **nie stanowi zgody na wykonanie Tasku**.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wykonaj TASK-010.
```

Po zakończeniu:

- tworzy raport,
- zatrzymuje się,
- nie rozpoczyna TASK-011.

---

## 34. Oczekiwany stan końcowy

```text
TASK-009 ACCEPTED
        ↓
Application contracts
        ↓
TASK-010
        ↓
SQLAlchemy repositories
        ↓
transaction boundary
        ↓
PostgreSQL integration tests
        ↓
schema unchanged
        ↓
READY FOR CERBERUS REVIEW
```
