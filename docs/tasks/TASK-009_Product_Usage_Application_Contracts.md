# TASK-009 — Product & Usage Application Contracts

**Projekt:** MSDS Manager  
**Task ID:** TASK-009  
**Sprint:** SPRINT-002 — Rejestr produktów i miejsc stosowania  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Rozszerzyć warstwę `application` o **minimalne kontrakty aplikacyjne** potrzebne do pracy z już istniejącym `PRODUCT` oraz z jego miejscami stosowania.

TASK-009 ma zdefiniować:

- porty repozytoriów wymagane przez przypadki użycia,
- minimalne DTO wejściowe/wyjściowe tam, gdzie rzeczywiście upraszczają granice,
- use case'y dla odczytu i administracyjnej obsługi istniejącego PRODUCT,
- use case'y dla słownika `USAGE_LOCATION`,
- use case'y dla przypisań `PRODUCT_USAGE_LOCATION`.

TASK-009 **nie implementuje jeszcze persistence SQLAlchemy dla nowych kontraktów**, nie buduje UI i nie tworzy nowego PRODUCT.

Oczekiwany przyrost:

```text
Domain
   ↑
Application contracts
   ├── ports
   ├── DTO
   └── use cases
```

Persistence dla tych kontraktów powstaje dopiero w TASK-010.

---

## 2. Stan wejściowy

TASK-008 jest zakończony i zaakceptowany.

Stan projektu:

```text
CORE                    v1.1 aligned
Domain                  aligned
ORM                     aligned
Alembic revisions       3
PostgreSQL head         c41d8e2f7a90
Application tables      9
Tests                   59 passed
Schema drift            none
Business records        0
```

Istnieje już pion aplikacyjny z TASK-007:

```text
ManufacturerRepositoryPort
        ↓
ListManufacturers
        ↓
SqlAlchemyManufacturerRepository
```

TASK-009 ma go zachować i rozszerzyć w sposób minimalny.

---

## 3. Źródła i hierarchia decyzji

Implementacja musi być zgodna w następującej kolejności:

1. `CORE-001 v1.1-approved`,
2. `BDR-001..005`,
3. `TDR-001..003`,
4. `SPRINT-002 v1.2-approved`,
5. zaakceptowany rezultat `TASK-008`,
6. istniejący rezultat `TASK-007`,
7. root `AGENTS.md`.

Jeżeli do poprawnej implementacji potrzebna jest nowa decyzja biznesowa albo techniczna niewynikająca z tych źródeł:

```text
STOP
```

Codex nie uzupełnia brakującej decyzji własnym założeniem.

---

# CZĘŚĆ A — ZASADA NADRZĘDNA TASK-009

## 4. PRODUCT istnieje przed wejściem do kontraktów Sprintu 2

W obowiązującym `SPRINT-002 v1.2-approved` nowy PRODUCT powstaje później jako część zatwierdzonego workflow:

```text
Dodaj nowy SDS
        ↓
walidacja
        ↓
ekstrakcja
        ↓
DRAFT
        ↓
akceptacja użytkownika
        ↓
PRODUCT + SDS + dane zatwierdzone
```

Dlatego TASK-009 **nie może definiować publicznego use case'u**:

```text
CreateProduct
```

ani żadnego równoważnego kontraktu pozwalającego utworzyć PRODUCT poza workflow SDS.

Nie twórz także:

```text
CreateManufacturer
```

Producent może zostać utworzony później w workflow SDS, ale nie jest to operacja publiczna Sprintu 2.

---

## 5. Zakres pracy z PRODUCT w TASK-009

Kontrakty aplikacyjne mają pracować z **już istniejącym PRODUCT**.

Minimalny zakres:

```text
ListProducts
GetProductDetails
UpdateProductAdministrativeData
```

Dopuszczalne operacje administracyjne dotyczą wyłącznie pól zatwierdzonych jako edytowalne:

```text
use_description
use_restriction
waste_type
waste_code
```

Pola tożsamości:

```text
product_name
manufacturer_product_code
manufacturer_id
```

nie mogą występować w kontrakcie administracyjnej aktualizacji.

---

## 6. `usage_status` — twarda granica

`usage_status` jest administracyjnie istotnym polem PRODUCT, ale jego przejścia są związane z workflow SDS/BHP.

Sprint 2 nie implementuje jeszcze:

```text
PENDING_APPROVAL → ACTIVE
PENDING_APPROVAL → REJECTED
```

ponieważ wynikają one z decyzji BHP.

TASK-009 nie może stworzyć ogólnego mechanizmu:

```text
SetProductStatus(any_status)
UpdateProductAdministrativeData(... usage_status=...)
```

który pozwalałby ominąć przyszły workflow SDS/BHP.

Jeżeli istniejąca zatwierdzona decyzja jednoznacznie wymaga w tym Tasku osobnego use case'u dla `ACTIVE/REJECTED/INACTIVE`, a implementacja nie może zachować granicy bez nowej reguły przejścia:

```text
STOP
```

W TASK-009 preferowane jest pozostawienie `usage_status` jako danych odczytywanych, bez publicznego kontraktu jego swobodnej zmiany.

---

# CZĘŚĆ B — KONTRAKTY ODCZYTOWE PRODUCT

## 7. `ListProducts`

Zdefiniuj minimalny use case:

```text
ListProducts
```

który:

- pobiera istniejące produkty przez port application,
- nie zna SQLAlchemy,
- nie zna PostgreSQL,
- nie zwraca obiektów ORM,
- nie tworzy ani nie modyfikuje danych.

Wynik ma zawierać dane potrzebne przyszłemu widokowi rejestru, co najmniej:

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

Jeżeli najprostszy kontrakt wymaga osobnego DTO listy, utwórz je.

Nie dodawaj danych SDS/BHP/SafetyProfile.

---

## 8. `GetProductDetails`

Zdefiniuj:

```text
GetProductDetails(product_id)
```

Use case ma zwracać szczegóły istniejącego produktu wraz z informacją potrzebną do odpowiedzi:

> gdzie produkt jest stosowany i jakie ilości są tam zadeklarowane?

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
usage_locations[]
```

Każda pozycja `usage_locations[]` powinna reprezentować co najmniej:

```text
location_id
location_name
location_status
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie implementuj jeszcze sumowania `peak_factory_quantity` w application, jeśli nie jest ono konieczne do kontraktu. Istniejąca czysta reguła domenowa pozostaje bez zmian.

Brak produktu powinien być reprezentowany przez jednoznaczny kontrakt application/domain, a nie przez wyjątek SQLAlchemy.

Nie projektuj rozbudowanego systemu błędów.

---

# CZĘŚĆ C — ADMINISTRACYJNA AKTUALIZACJA PRODUCT

## 9. `UpdateProductAdministrativeData`

Zdefiniuj use case:

```text
UpdateProductAdministrativeData
```

który umożliwia zmianę wyłącznie:

```text
use_description
use_restriction
waste_type
waste_code
```

Kontrakt wejściowy **nie może zawierać**:

```text
product_name
manufacturer_product_code
manufacturer_id
```

Nie dodawaj „opcjonalnych pól na przyszłość”, które pozwoliłyby później przypadkowo zmieniać tożsamość.

Nie dodawaj swobodnej zmiany `usage_status` zgodnie z granicą z sekcji 6.

TASK-009 definiuje kontrakt i koordynację aplikacyjną. Realny zapis PostgreSQL przez nowe repozytoria będzie implementowany w TASK-010.

---

# CZĘŚĆ D — MANUFACTURER

## 10. `ListManufacturers`

Zachowaj istniejący:

```text
ManufacturerRepositoryPort
ListManufacturers
```

z TASK-007.

Nie przepisuj działającego pionu bez potrzeby.

Możesz wykonać minimalne dostosowanie kontraktu wyłącznie wtedy, gdy jest technicznie konieczne dla spójności nowych kontraktów.

Nie dodawaj:

```text
CreateManufacturer
UpdateManufacturer
DeleteManufacturer
```

Nie dodawaj dostawcy handlowego.

---

# CZĘŚĆ E — USAGE_LOCATION

## 11. Minimalny port `UsageLocationRepository`

Zdefiniuj port application wymagany przez:

```text
ListUsageLocations
CreateUsageLocation
DeactivateUsageLocation
```

Port opisuje potrzebę application, a nie API SQLAlchemy.

Minimalne operacje portu mają wynikać wyłącznie z powyższych use case'ów.

Nie twórz generic CRUD repository.

---

## 12. `ListUsageLocations`

Zdefiniuj:

```text
ListUsageLocations
```

Wynik minimalnie:

```text
location_id
location_name
status
```

Use case nie wykonuje bezpośrednich zapytań SQLAlchemy.

---

## 13. `CreateUsageLocation`

Zdefiniuj:

```text
CreateUsageLocation
```

dla utworzenia nowego stanowiska/miejsca stosowania.

Minimalne dane wejściowe:

```text
location_name
```

Status początkowy ma wynikać z istniejącego modelu `UsageLocation` i zatwierdzonych enumów.

Nie dodawaj hierarchii:

```text
zakład → hala → obszar → linia → stanowisko
```

Nie dodawaj kodów lokalizacji, opisów, właścicieli ani innych pól, których Core nie wymaga.

Jeżeli obecny model nie pozwala jednoznacznie ustalić zatwierdzonego statusu początkowego bez zgadywania:

```text
STOP
```

---

## 14. `DeactivateUsageLocation`

Zdefiniuj:

```text
DeactivateUsageLocation(location_id)
```

Operacja oznacza wycofanie stanowiska z bieżącego użycia.

Nie implementuj:

```text
DeleteUsageLocation
```

Nie usuwaj fizycznie lokalizacji.

TASK-009 nie projektuje mechanizmu historii.

Jeżeli dokładna zmiana statusu lokalizacji nie wynika jednoznacznie z istniejącego modelu domenowego:

```text
STOP
```

zamiast dodawać nowy enum/status.

---

# CZĘŚĆ F — PRODUCT_USAGE_LOCATION

## 15. Port relacji Product–UsageLocation

Zdefiniuj minimalny port potrzebny do:

```text
AssignProductUsageLocation
UpdateProductUsageLocation
```

Port nie może zawierać ogólnego CRUD „na przyszłość”.

Nie definiuj fizycznego delete relacji, jeżeli wymagałoby to nierozstrzygniętej polityki historii.

---

## 16. `AssignProductUsageLocation`

Zdefiniuj:

```text
AssignProductUsageLocation
```

dla przypisania istniejącego PRODUCT do istniejącego USAGE_LOCATION.

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

Typ ilości:

```text
Decimal
```

Nie `float`.

Peak i monthly mogą posiadać różne jednostki.

Brak automatycznej konwersji jednostek.

Walidacja zatwierdzona w Domain z TASK-008 powinna być wykorzystana, a nie duplikowana w Streamlit czy persistence.

---

## 17. `UpdateProductUsageLocation`

Zdefiniuj:

```text
UpdateProductUsageLocation
```

dla aktualizacji danych ilościowych istniejącego przypisania.

Dozwolony zakres:

```text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie zmieniaj przez ten use case:

```text
product_id
location_id
```

Jeżeli produkt ma zostać przypisany do innego stanowiska, jest to inne powiązanie biznesowe, a nie edycja tożsamości istniejącej relacji.

Nie implementuj:

```text
DeleteProductUsageLocation
RemoveProductUsageLocation
```

dopóki polityka historii/dezaktywacji relacji nie zostanie zatwierdzona.

---

# CZĘŚĆ G — PORTY

## 18. Minimalny zestaw portów

Po TASK-009 application powinno posiadać minimalne porty odpowiadające rzeczywistym potrzebom use case'ów, np.:

```text
ManufacturerRepositoryPort        istniejący / read
ProductRepositoryPort
UsageLocationRepositoryPort
ProductUsageLocationRepositoryPort
```

Nazwy mogą być dostosowane do istniejącej konwencji repozytorium.

Porty:

- należą do `app/application/ports/`,
- nie importują SQLAlchemy,
- nie importują infrastructure,
- operują na Domain / application DTO,
- nie ujawniają `Session`, `Query`, ORM models ani technicznych szczegółów PostgreSQL.

Nie buduj wspólnej klasy bazowej typu:

```text
GenericRepository[T]
CRUDRepository[T]
BaseRepository
```

---

# CZĘŚĆ H — DTO

## 19. Zasada DTO

DTO twórz tylko tam, gdzie rzeczywiście stanowią granicę application.

Preferowane są małe jawne struktury, np.:

```text
ProductListItem
ProductDetails
ProductUsageLocationDetails

UpdateProductAdministrativeDataInput
CreateUsageLocationInput
AssignProductUsageLocationInput
UpdateProductUsageLocationInput
```

Dokładne nazwy mogą zostać dostosowane do istniejącej konwencji.

Nie twórz:

- jednego ogromnego `ProductDTO`,
- osobnych DTO 1:1 dla każdego modelu bez potrzeby,
- modeli Pydantic — nowa biblioteka nie jest potrzebna,
- DTO zawierających obiekty ORM.

Użyj standardowych mechanizmów Pythona zgodnych z istniejącym projektem.

---

# CZĘŚĆ I — GRANICA TRANSAKCJI

## 20. TASK-009 nie implementuje jeszcze transaction infrastructure

TASK-009 definiuje kontrakty aplikacyjne.

Nie implementuj jeszcze:

- nowych adapterów SQLAlchemy dla Product/UsageLocation/ProductUsageLocation,
- `commit()` / `rollback()` w nowych repozytoriach,
- Unit of Work framework,
- transaction manager framework,
- nowych integration repositories.

Pełna persistence i granica transakcji należą do:

```text
TASK-010
```

Use case'y zapisu mogą wyrażać potrzebę operacji repozytorium przez port, ale nie mogą importować SQLAlchemy ani infrastructure.

Jeżeli poprawna realizacja use case'u wymaga podjęcia decyzji o sposobie commit/rollback:

```text
nie rozwiązuj tego w TASK-009
```

Zostaw implementację techniczną do TASK-010.

---

# CZĘŚĆ J — TESTY

## 21. Testy jednostkowe kontraktów application

Dodaj testy bez realnego PostgreSQL dla nowych use case'ów.

Użyj prostych fake/stub repositories implementujących porty.

Nie wprowadzaj frameworka mocków, jeżeli standardowe proste klasy testowe wystarczą.

Potwierdź co najmniej:

### Product

1. `ListProducts` zwraca dane istniejących produktów bez ORM.
2. `GetProductDetails` zwraca producenta i przypisane lokalizacje.
3. `UpdateProductAdministrativeData` przekazuje wyłącznie dozwolone pola.
4. kontrakt aktualizacji nie pozwala zmienić:
   - `product_name`,
   - `manufacturer_product_code`,
   - `manufacturer_id`.
5. nie istnieje publiczny `CreateProduct`.

### Manufacturer

6. istniejący `ListManufacturers` nadal działa.
7. nie istnieje publiczny `CreateManufacturer`.

### UsageLocation

8. `ListUsageLocations` zwraca listę lokalizacji.
9. `CreateUsageLocation` tworzy kontrakt tylko dla lokalizacji.
10. `DeactivateUsageLocation` nie usuwa fizycznie lokalizacji w kontrakcie.

### ProductUsageLocation

11. `AssignProductUsageLocation` używa `Decimal`.
12. peak `0` jest akceptowane.
13. monthly `None/None` jest akceptowane.
14. monthly `0 + unit` jest akceptowane.
15. ujemne wartości są odrzucane przez zatwierdzoną walidację Domain.
16. monthly value bez unit jest odrzucane.
17. monthly unit bez value jest odrzucane.
18. peak i monthly mogą mieć różne jednostki.
19. `UpdateProductUsageLocation` nie zmienia `product_id/location_id`.
20. brak automatycznej konwersji jednostek.

Testy powinny potwierdzać zachowanie kontraktu, a nie implementację przyszłego SQLAlchemy adaptera.

---

## 22. Test granic architektury

Zachowaj i rozszerz istniejącą prostą kontrolę architektoniczną z TASK-007.

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

Infrastructure może implementować application ports.

Nie wprowadzaj nowego narzędzia dependency-analysis.

---

## 23. Pełna regresja

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Oczekiwane:

- wszystkie dotychczasowe 59 testów pozostają zielone,
- nowe testy TASK-009 przechodzą,
- brak `SAWarning`.

---

# CZĘŚĆ K — SCHEMA / POSTGRESQL / ALEMBIC

## 24. Brak zmiany schema

TASK-009 nie wymaga zmiany ORM ani PostgreSQL.

Oczekiwany stan po Tasku:

```text
Alembic revisions       3
PostgreSQL current      c41d8e2f7a90 (head)
Application tables      9
Schema drift            none
Business records        0
```

Nie twórz czwartej migracji.

Nie modyfikuj:

- modeli ORM,
- constraints TASK-006,
- quantity CHECK constraints TASK-008,
- 18 enum CHECK constraints,
- filtra Alembic.

Uruchom:

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe check
```

Oczekiwane:

```text
c41d8e2f7a90 (head)
No new upgrade operations detected.
```

Jeżeli kontrakty application wymagają zmiany schema:

```text
STOP
```

---

# CZĘŚĆ L — POZA ZAKRESEM

## 25. TASK-009 NIE implementuje

Nie implementuj:

- `CreateProduct`,
- `CreateManufacturer`,
- workflow `Dodaj nowy SDS`,
- rejestracji SDS,
- parsera PDF,
- ekstrakcji,
- DRAFT SDS,
- SAFETY_PROFILE,
- SDS_COMPONENT,
- BHP_DECISION,
- DECISION_EVIDENCE,
- przejścia `PENDING_APPROVAL → ACTIVE/REJECTED`,
- ogólnego `SetProductStatus`,
- repozytoriów SQLAlchemy dla nowych portów,
- transaction/UoW framework,
- Streamlit,
- listy ekranowej,
- formularzy,
- historii/audytu,
- soft delete,
- fizycznego usuwania UsageLocation,
- usuwania ProductUsageLocation,
- importu Excel,
- REACH,
- dostawców,
- magazynu,
- BDO,
- modułu gospodarki odpadami,
- słownika jednostek,
- konwersji jednostek,
- generic CRUD,
- event bus,
- command bus,
- CQRS,
- nowych bibliotek.

---

# CZĘŚĆ M — HISTORIA

## 26. Twarda granica historii

Mechanizm historii pozostaje nierozstrzygnięty.

TASK-009 nie może tworzyć:

- audit/history tables,
- event log,
- snapshotów,
- temporal model,
- version columns,
- triggerów,
- `created_by`,
- `updated_by`,
- history repository,
- history DTO/use case.

Jeżeli którykolwiek kontrakt wymaga rozstrzygnięcia, jak historyzować zmianę:

```text
STOP
```

Nie projektuj mechanizmu tylko dlatego, że przyszły TASK-015 będzie go potrzebował.

---

# CZĘŚĆ N — GIT I BEZPIECZEŃSTWO

## 27. Kontrole

Wykonaj:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Nie wykonuj commit ani push bez jawnego polecenia.

Potwierdź:

- `.env` ignored i nietrackowany,
- brak ujawnienia sekretów,
- brak dumpów/backupów,
- brak dokumentów SDS/BHP w repozytorium,
- brak pozostawionych danych testowych,
- brak nowych bibliotek,
- brak niezamówionych zmian `pyproject.toml`.

---

# CZĘŚĆ O — STOP CONDITIONS

## 28. STOP

Raportuj `PARTIAL` albo `BLOCKED`, jeżeli:

- stan repozytorium/DB istotnie różni się od stanu po zaakceptowanym TASK-008,
- potrzebna jest zmiana schema/migracja,
- potrzebny jest `CreateProduct` albo `CreateManufacturer`,
- potrzebne jest wejście w workflow SDS/BHP,
- potrzebna jest nowa reguła przejścia `usage_status`,
- status początkowy/dezaktywacja UsageLocation nie wynika z istniejącego modelu,
- potrzebna jest fizyczna operacja usunięcia relacji wymagająca decyzji historii,
- potrzebna jest nowa biblioteka,
- pojawia się konflikt CORE/BDR/TDR/SPRINT,
- poprawne wykonanie wymaga historii,
- zakres zaczyna implementować persistence TASK-010,
- zakres zaczyna implementować UI TASK-012.

Nie obchodź STOP przez rozszerzenie kontraktów „na przyszłość”.

---

# CZĘŚĆ P — KRYTERIA AKCEPTACJI

## 29. TASK-009 = DONE, jeżeli

1. istnieje minimalny `ProductRepositoryPort`,
2. istnieje minimalny `UsageLocationRepositoryPort`,
3. istnieje minimalny port dla `ProductUsageLocation`,
4. istniejący `ManufacturerRepositoryPort` pozostaje działający,
5. `ListProducts` istnieje,
6. `GetProductDetails` istnieje,
7. `UpdateProductAdministrativeData` istnieje,
8. aktualizacja administracyjna nie przyjmuje pól tożsamości,
9. aktualizacja administracyjna nie umożliwia swobodnej zmiany `usage_status`,
10. `ListManufacturers` nadal działa,
11. brak `CreateManufacturer`,
12. `ListUsageLocations` istnieje,
13. `CreateUsageLocation` istnieje albo Task zatrzymał się prawidłowo na nierozstrzygniętym statusie początkowym,
14. `DeactivateUsageLocation` istnieje albo Task zatrzymał się prawidłowo na nierozstrzygniętej semantyce statusu,
15. `AssignProductUsageLocation` istnieje,
16. `UpdateProductUsageLocation` istnieje,
17. brak `CreateProduct`,
18. kontrakty quantity używają `Decimal`,
19. zachowana semantyka peak/monthly i `0 != NULL`,
20. brak konwersji jednostek,
21. DTO są minimalne i nie zawierają ORM,
22. application nie importuje infrastructure/SQLAlchemy/psycopg,
23. nowe testy application przechodzą,
24. pełna regresja przechodzi bez `SAWarning`,
25. brak zmian ORM,
26. brak nowej migracji,
27. PostgreSQL nadal ma 9 tabel,
28. PostgreSQL pozostaje na `c41d8e2f7a90 (head)`,
29. `alembic check` nie wykazuje rzeczywistego driftu,
30. brak historii,
31. brak UI,
32. brak nowych bibliotek,
33. brak danych testowych/biznesowych po testach,
34. utworzono raport TASK-009,
35. TASK-010 nie został rozpoczęty.

Jeżeli kryterium 13 lub 14 ujawni rzeczywistą lukę decyzyjną, prawidłowym wynikiem jest `PARTIAL/BLOCKED + STOP`, nie zgadywanie.

---

# CZĘŚĆ Q — WYMAGANY RAPORT

## 30. Raport

Utwórz:

```text
docs/task_reports/TASK-009_REPORT.md
```

Raport ma zawierać:

1. status `DONE` / `PARTIAL` / `BLOCKED`,
2. potwierdzony stan wejściowy,
3. listę dodanych/zmienionych portów,
4. listę DTO,
5. listę use case'ów,
6. sposób ochrony pól tożsamości PRODUCT,
7. sposób zachowania granicy `usage_status`,
8. zachowanie istniejącego `ListManufacturers`,
9. kontrakt UsageLocation,
10. kontrakt ProductUsageLocation,
11. semantykę `Decimal`, `0`, `NULL` i jednostek,
12. testy jednostkowe application,
13. test granic architektury,
14. wynik pełnego pytest i `SAWarning`,
15. potwierdzenie braku zmian ORM/schema,
16. `alembic current`,
17. `alembic check`,
18. finalny stan PostgreSQL,
19. Git/bezpieczeństwo,
20. odstępstwa,
21. problemy/ryzyka i kandydatów do przyszłych decyzji — bez implementacji,
22. następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-010.
```

---

# CZĘŚĆ R — AUTORYZACJA

## 31. Autoryzacja wykonania

Obecność pliku:

```text
docs/tasks/TASK-009_Product_Usage_Application_Contracts.md
```

w repozytorium **nie stanowi zgody na wykonanie Tasku**.

Codex rozpoczyna wyłącznie po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-009.
```

Po zakończeniu:

- tworzy raport,
- zatrzymuje się,
- nie rozpoczyna TASK-010.

---

## 32. Oczekiwany stan końcowy

```text
TASK-008 ACCEPTED
        ↓
Domain / ORM / PostgreSQL aligned
        ↓
TASK-009
Application contracts
        ↓
ports + DTO + use cases
        ↓
unit + architecture tests green
        ↓
schema unchanged
        ↓
READY FOR CERBERUS REVIEW
```
