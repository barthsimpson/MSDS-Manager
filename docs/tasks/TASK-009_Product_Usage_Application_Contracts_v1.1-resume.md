# TASK-009 — Product & Usage Application Contracts

**Projekt:** MSDS Manager  
**Task ID:** TASK-009  
**Wersja:** 1.1-resume  
**Sprint:** SPRINT-002 v1.2-approved — Rejestr produktów i miejsc stosowania  
**Status wejściowy:** READY — wznowienie po zaakceptowanym TASK-009-ALIGN  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel rewizji / wznowienia

TASK-009 został wcześniej prawidłowo zatrzymany jako `BLOCKED`, ponieważ zatwierdzone źródła nie określały semantyki `USAGE_LOCATION.status`.

Blocker został rozstrzygnięty przez:

```text
BDR-002 v1.2-approved
CORE-001 v1.2-approved
TASK-009-ALIGN — ACCEPTED
```

TASK-009 jest teraz wznowiony jako **ten sam Task**.

Nie należy odtwarzać ani cofać zmian wykonanych w TASK-009-ALIGN.

Celem pozostaje rozszerzenie warstwy `application` o minimalne kontrakty potrzebne do pracy z istniejącym PRODUCT, USAGE_LOCATION i PRODUCT_USAGE_LOCATION.

---

## 2. Aktualny stan wejściowy

Stan po zaakceptowanym TASK-009-ALIGN:

```text
CORE                    v1.2-approved
UsageLocationStatus     ACTIVE / INACTIVE
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Tests                   63 passed
Schema drift            none
Business records        0
```

`UsageLocation` posiada już:

```text
status: UsageLocationStatus

new location → ACTIVE

deactivate()
ACTIVE → INACTIVE

reactivate()
INACTIVE → ACTIVE
```

PostgreSQL wymusza:

```text
usage_locations.status IN ('ACTIVE', 'INACTIVE')
```

TASK-009 nie zmienia tego modelu.

---

## 3. Źródła i hierarchia decyzji

Implementacja musi być zgodna z:

1. `CORE-001 v1.2-approved`,
2. `BDR-002 v1.2-approved`,
3. pozostałymi zatwierdzonymi `BDR-001..005`,
4. `TDR-001..003`,
5. `SPRINT-002 v1.2-approved`,
6. zaakceptowanym `TASK-009-ALIGN`,
7. zaakceptowanymi rezultatami TASK-007 i TASK-008,
8. wcześniejszym raportem `TASK-009_REPORT.md` ze statusem BLOCKED,
9. root `AGENTS.md`.

Jeżeli do poprawnej realizacji potrzebna jest nowa decyzja niewynikająca z tych źródeł:

```text
STOP
```

---

# CZĘŚĆ A — PRODUCT

## 4. PRODUCT istnieje przed wejściem do kontraktów Sprintu 2

TASK-009 nie definiuje:

```text
CreateProduct
CreateManufacturer
```

Nowy PRODUCT powstanie później w workflow SDS.

Kontrakty TASK-009 pracują wyłącznie z istniejącym PRODUCT.

## 5. Minimalny zakres PRODUCT

Zdefiniuj:

```text
ListProducts
GetProductDetails
UpdateProductAdministrativeData
```

Administracyjna aktualizacja może obejmować wyłącznie:

```text
use_description
use_restriction
waste_type
waste_code
```

Nie może obejmować pól tożsamości:

```text
product_name
manufacturer_product_code
manufacturer_id
```

## 6. Granica usage_status

`usage_status` jest odczytywane, ale TASK-009 nie tworzy swobodnego:

```text
SetProductStatus
```

ani nie pozwala zmieniać `usage_status` przez `UpdateProductAdministrativeData`.

Nie implementuj przejść SDS/BHP.

## 7. ListProducts

Minimalny wynik:

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

Bez ORM, SQLAlchemy, SDS/BHP/SafetyProfile.

## 8. GetProductDetails

Minimalny wynik obejmuje PRODUCT oraz:

```text
usage_locations[]
```

Każda pozycja co najmniej:

```text
location_id
location_name
location_status
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Brak produktu ma być reprezentowany przez jednoznaczny kontrakt application/domain, nie wyjątek SQLAlchemy.

---

# CZĘŚĆ B — MANUFACTURER

## 9. ListManufacturers

Zachowaj istniejące:

```text
ManufacturerRepositoryPort
ListManufacturers
```

Nie dodawaj:

```text
CreateManufacturer
UpdateManufacturer
DeleteManufacturer
```

---

# CZĘŚĆ C — USAGE_LOCATION

## 10. UsageLocationRepositoryPort

Zdefiniuj minimalny port potrzebny przez:

```text
ListUsageLocations
CreateUsageLocation
DeactivateUsageLocation
ReactivateUsageLocation
```

Nie twórz generic CRUD repository.

Port ma opisywać potrzeby application, a nie API SQLAlchemy.

## 11. ListUsageLocations

Zdefiniuj:

```text
ListUsageLocations
```

Minimalny wynik:

```text
location_id
location_name
status
```

Lista może prezentować zarówno `ACTIVE`, jak i `INACTIVE`.

Jeżeli potrzebny jest kontrakt wyboru lokalizacji dla **nowego przypisania PRODUCT**, musi udostępniać wyłącznie `ACTIVE`.

Nie ukrywaj jednak `INACTIVE` z ogólnego słownika/listy administracyjnej.

## 12. CreateUsageLocation

Minimalne wejście:

```text
location_name
```

Nowa domenowa `UsageLocation` otrzymuje status:

```text
ACTIVE
```

Nie dodawaj dodatkowych pól, hierarchii ani kodów lokalizacji.

## 13. DeactivateUsageLocation

Zdefiniuj:

```text
DeactivateUsageLocation(location_id)
```

Semantyka:

```text
ACTIVE → INACTIVE
```

Use case korzysta z zatwierdzonego zachowania Domain.

Nie implementuj:

```text
DeleteUsageLocation
```

Nie usuwaj rekordu i nie projektuj historii.

## 14. ReactivateUsageLocation

Zdefiniuj:

```text
ReactivateUsageLocation(location_id)
```

Semantyka:

```text
INACTIVE → ACTIVE
```

Reaktywacja dotyczy istniejącego rekordu i zachowuje `location_id`.

Nie twórz nowej lokalizacji jako substytutu reaktywacji.

Nie projektuj historii.

---

# CZĘŚĆ D — PRODUCT_USAGE_LOCATION

## 15. ProductUsageLocationRepositoryPort

Zdefiniuj minimalny port potrzebny do:

```text
AssignProductUsageLocation
UpdateProductUsageLocation
```

Nie twórz generic CRUD.

Nie dodawaj:

```text
DeleteProductUsageLocation
RemoveProductUsageLocation
```

dopóki polityka historii relacji nie zostanie zatwierdzona.

## 16. AssignProductUsageLocation

Minimalne wejście:

```text
product_id
location_id
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Reguły:

```text
peak_quantity_value >= 0
peak_quantity_unit required

monthly_consumption_value = NULL
↔ monthly_consumption_unit = NULL

monthly_consumption_value >= 0 when present

0 != NULL
```

Ilości używają:

```text
Decimal
```

Nie `float`.

Peak i monthly mogą mieć różne jednostki.

Brak automatycznej konwersji.

### 16.1. Status lokalizacji przy nowym przypisaniu

Nowe przypisanie PRODUCT może powstać wyłącznie dla:

```text
USAGE_LOCATION.status = ACTIVE
```

Kontrakt application musi wymagać możliwości sprawdzenia statusu lokalizacji przez port.

Nie implementuj persistence ani SQLAlchemy.

Próba przypisania do `INACTIVE` musi zakończyć się jednoznacznym błędem application/domain.

Nie projektuj rozbudowanego frameworka błędów.

## 17. UpdateProductUsageLocation

Aktualizuje wyłącznie:

```text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie zmienia:

```text
product_id
location_id
```

Nie implementuj fizycznego usuwania relacji.

---

# CZĘŚĆ E — PORTY I DTO

## 18. Minimalny zestaw portów

Po TASK-009 application powinno posiadać:

```text
ManufacturerRepositoryPort
ProductRepositoryPort
UsageLocationRepositoryPort
ProductUsageLocationRepositoryPort
```

Porty:

- należą do `app/application/ports/`,
- nie importują infrastructure,
- nie importują SQLAlchemy,
- nie ujawniają Session/Query/ORM/PostgreSQL,
- operują na Domain / application DTO.

Bez:

```text
GenericRepository
CRUDRepository
BaseRepository
```

## 19. DTO

Twórz tylko DTO potrzebne na granicy application.

Przykładowo:

```text
ProductListItem
ProductDetails
ProductUsageLocationDetails

UpdateProductAdministrativeDataInput
CreateUsageLocationInput
AssignProductUsageLocationInput
UpdateProductUsageLocationInput
```

Możesz dodać minimalne DTO potrzebne dla reaktywacji/dezaktywacji, jeśli rzeczywiście upraszczają kontrakt.

Nie używaj Pydantic ani nowej biblioteki.

---

# CZĘŚĆ F — GRANICA TRANSAKCJI

## 20. Bez persistence TASK-010

TASK-009 definiuje application contracts.

Nie implementuj nowych adapterów SQLAlchemy dla:

```text
Product
UsageLocation
ProductUsageLocation
```

Nie implementuj:

```text
commit
rollback
UnitOfWork
transaction manager
```

Persistence i granica transakcji należą do TASK-010.

---

# CZĘŚĆ G — TESTY

## 21. Testy jednostkowe application

Użyj prostych fake/stub repositories.

Potwierdź co najmniej:

### Product

1. `ListProducts` zwraca istniejące produkty bez ORM.
2. `GetProductDetails` zwraca producenta i przypisane lokalizacje.
3. `UpdateProductAdministrativeData` przyjmuje wyłącznie zatwierdzone pola.
4. nie można przez ten kontrakt zmienić tożsamości PRODUCT.
5. nie można swobodnie zmienić `usage_status`.
6. brak publicznego `CreateProduct`.

### Manufacturer

7. `ListManufacturers` nadal działa.
8. brak publicznego `CreateManufacturer`.

### UsageLocation

9. `ListUsageLocations` zwraca `ACTIVE` i `INACTIVE`.
10. `CreateUsageLocation` tworzy domenową lokalizację ze statusem `ACTIVE`.
11. `DeactivateUsageLocation` wykonuje `ACTIVE → INACTIVE`.
12. `ReactivateUsageLocation` wykonuje `INACTIVE → ACTIVE`.
13. dezaktywacja nie jest delete.
14. reaktywacja zachowuje `location_id`.

### ProductUsageLocation

15. przypisanie do `ACTIVE` jest dopuszczone.
16. przypisanie do `INACTIVE` jest odrzucone.
17. `AssignProductUsageLocation` używa `Decimal`.
18. peak `0` jest akceptowane.
19. monthly `None/None` jest akceptowane.
20. monthly `0 + unit` jest akceptowane.
21. ujemne wartości są odrzucane.
22. monthly value bez unit jest odrzucane.
23. monthly unit bez value jest odrzucane.
24. peak i monthly mogą mieć różne jednostki.
25. `UpdateProductUsageLocation` nie zmienia `product_id/location_id`.
26. brak automatycznej konwersji jednostek.

## 22. Granice architektury

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
```

Nie dodawaj nowego narzędzia dependency-analysis.

## 23. Pełna regresja

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Stan bazowy to **63 testy** po TASK-009-ALIGN.

Wszystkie dotychczasowe i nowe testy muszą przejść bez `SAWarning`.

---

# CZĘŚĆ H — SCHEMA / POSTGRESQL / ALEMBIC

## 24. Schema pozostaje bez zmian

TASK-009 nie zmienia ORM ani PostgreSQL.

Oczekiwany stan końcowy:

```text
Alembic revisions       4
PostgreSQL current      d2b4f6a8c190 (head)
Application tables      9
Schema drift            none
Business records        0
```

Nie twórz piątej migracji.

Nie modyfikuj:

- modeli ORM,
- constraintów TASK-006,
- quantity CHECK TASK-008,
- `usage_location_status_values` z TASK-009-ALIGN,
- innych enumowych CHECK,
- konfiguracji/filtra Alembic.

Uruchom:

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe check
```

Oczekiwane:

```text
d2b4f6a8c190 (head)
No new upgrade operations detected.
```

Jeżeli application contracts wymagają zmiany schema:

```text
STOP
```

---

# CZĘŚĆ I — HISTORIA

## 25. Twarda granica historii

Nie twórz:

- audit/history tables,
- event log,
- snapshotów,
- temporal model,
- version columns,
- triggerów,
- history repository,
- history DTO/use case.

Zmiana `ACTIVE ↔ INACTIVE` nie upoważnia do zaprojektowania mechanizmu historii.

---

# CZĘŚĆ J — POZA ZAKRESEM

## 26. TASK-009 NIE implementuje

Nie implementuj:

- CreateProduct,
- CreateManufacturer,
- SDS workflow,
- BHP workflow,
- SetProductStatus,
- persistence TASK-010,
- transaction infrastructure,
- Streamlit/UI,
- historii/audytu,
- DeleteUsageLocation,
- Delete/RemoveProductUsageLocation,
- importu Excel,
- REACH,
- dostawców,
- magazynu,
- BDO,
- osobnego modułu odpadów,
- słownika jednostek,
- konwersji jednostek,
- generic CRUD,
- CQRS/event/command bus,
- nowych bibliotek.

---

# CZĘŚĆ K — STOP

## 27. STOP conditions

Raportuj `PARTIAL/BLOCKED`, jeżeli:

- stan repozytorium/DB różni się istotnie od zaakceptowanego TASK-009-ALIGN,
- potrzebna jest kolejna zmiana schema/migracja,
- potrzebny jest CreateProduct/CreateManufacturer,
- potrzebne jest wejście w SDS/BHP,
- potrzebna jest nowa reguła Product.usage_status,
- potrzebna jest fizyczna operacja delete,
- potrzebna jest decyzja dotycząca historii,
- potrzebna jest nowa biblioteka,
- pojawia się konflikt CORE/BDR/TDR/SPRINT,
- zakres zaczyna implementować persistence TASK-010,
- zakres zaczyna implementować UI.

Nie zatrzymuj Tasku z powodu statusu początkowego/dezaktywacji/reaktywacji `USAGE_LOCATION` — te kwestie są już rozstrzygnięte przez Core v1.2 i BDR-002 v1.2.

---

# CZĘŚĆ L — KRYTERIA AKCEPTACJI

## 28. TASK-009 = DONE, jeżeli

1. istnieje minimalny `ProductRepositoryPort`,
2. istnieje minimalny `UsageLocationRepositoryPort`,
3. istnieje minimalny `ProductUsageLocationRepositoryPort`,
4. istniejący `ManufacturerRepositoryPort` pozostaje działający,
5. istnieje `ListProducts`,
6. istnieje `GetProductDetails`,
7. istnieje `UpdateProductAdministrativeData`,
8. administracyjna aktualizacja nie przyjmuje pól tożsamości,
9. nie umożliwia swobodnej zmiany `usage_status`,
10. `ListManufacturers` nadal działa,
11. brak `CreateManufacturer`,
12. istnieje `ListUsageLocations`,
13. istnieje `CreateUsageLocation`,
14. istnieje `DeactivateUsageLocation`,
15. istnieje `ReactivateUsageLocation`,
16. nowa lokalizacja ma `ACTIVE`,
17. dezaktywacja realizuje `ACTIVE → INACTIVE`,
18. reaktywacja realizuje `INACTIVE → ACTIVE` z zachowaniem `location_id`,
19. istnieje `AssignProductUsageLocation`,
20. przypisanie do `INACTIVE` jest blokowane,
21. istnieje `UpdateProductUsageLocation`,
22. brak `CreateProduct`,
23. quantity używa `Decimal`,
24. zachowana semantyka peak/monthly i `0 != NULL`,
25. brak konwersji jednostek,
26. DTO są minimalne i nie zawierają ORM,
27. application nie importuje infrastructure/SQLAlchemy/psycopg,
28. nowe testy application przechodzą,
29. pełna regresja przechodzi bez `SAWarning`,
30. brak zmian ORM,
31. brak nowej migracji,
32. PostgreSQL nadal ma 9 tabel,
33. PostgreSQL pozostaje na `d2b4f6a8c190 (head)`,
34. `alembic check` nie wykazuje rzeczywistego driftu,
35. brak historii,
36. brak UI,
37. brak nowych bibliotek,
38. brak danych testowych/biznesowych po testach,
39. utworzono raport TASK-009,
40. TASK-010 nie został rozpoczęty.

---

# CZĘŚĆ M — RAPORT

## 29. Wymagany raport

Zaktualizuj / zastąp wcześniejszy raport BLOCKED:

```text
docs/task_reports/TASK-009_REPORT.md
```

Raport ma jednoznacznie wskazać:

```text
TASK-009 resumed after accepted TASK-009-ALIGN
```

oraz zawierać:

1. status,
2. stan wejściowy po TASK-009-ALIGN,
3. porty,
4. DTO,
5. use case'y,
6. ochronę tożsamości PRODUCT,
7. granicę `usage_status`,
8. `ListManufacturers`,
9. kontrakty UsageLocation,
10. `ReactivateUsageLocation`,
11. blokadę przypisania do INACTIVE,
12. kontrakt ProductUsageLocation,
13. Decimal / 0 / NULL / jednostki,
14. testy application,
15. test architektury,
16. pełny pytest / SAWarning,
17. potwierdzenie braku zmian ORM/schema,
18. `alembic current`,
19. `alembic check`,
20. finalny stan PostgreSQL,
21. Git/bezpieczeństwo,
22. odstępstwa,
23. problemy/ryzyka,
24. następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-010.
```

---

# CZĘŚĆ N — AUTORYZACJA

## 30. Autoryzacja

Obecność zrewidowanego pliku TASK-009 w repozytorium nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wznów TASK-009.
```

Po zakończeniu tworzy raport i zatrzymuje się.

Nie rozpoczyna TASK-010.

---

## 31. Oczekiwany stan końcowy

```text
TASK-009 initial attempt
        ↓
BLOCKED / VALID STOP
        ↓
BDR-002 v1.2-approved
        ↓
CORE-001 v1.2-approved
        ↓
TASK-009-ALIGN ACCEPTED
        ↓
TASK-009 resumed
        ↓
Application contracts
        ↓
ports + DTO + use cases
        ↓
unit + architecture tests green
        ↓
schema unchanged at d2b4f6a8c190
        ↓
READY FOR CERBERUS REVIEW
```
