# TASK-014 — Product Administration & Usage Workflow

**Projekt:** MSDS Manager  
**Task ID:** TASK-014  
**Sprint:** SPRINT-002 v1.2-approved  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt

## 1. Cel

Rozszerzyć read-only Product Registry o kontrolowane operacje administracyjne dla **istniejącego PRODUCT**.

Zakres:
- edycja `use_description`, `use_restriction`, `waste_type`, `waste_code`,
- słownik `USAGE_LOCATION`,
- tworzenie, dezaktywacja i reaktywacja lokalizacji,
- przypisywanie ACTIVE lokalizacji do istniejącego PRODUCT,
- zapis/edycja `peak_quantity`,
- zapis/edycja opcjonalnego `monthly_consumption`.

Bez tworzenia PRODUCT/MANUFACTURER i bez zmiany tożsamości lub `usage_status`.

## 2. Stan wejściowy

```text
CORE                    v1.2-approved
Tests                   96 passed
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Schema drift            none
Business records        0
Product Registry        working
```

Dostępne use case'y:

```text
UpdateProductAdministrativeData
ListUsageLocations
CreateUsageLocation
DeactivateUsageLocation
ReactivateUsageLocation
AssignProductUsageLocation
UpdateProductUsageLocation
ListProducts
GetProductDetails
```

## 3. Źródła nadrzędne

1. `CORE-001 v1.2-approved`
2. `BDR-002 v1.2-approved`
3. pozostałe zatwierdzone BDR-001..005
4. TDR-001..003
5. `SPRINT-002 v1.2-approved`
6. zaakceptowane TASK-008..013 i TASK-009-ALIGN
7. root `AGENTS.md`

Brak jednoznacznej reguły = **STOP**.

## 4. PRODUCT — granica

TASK-014 pracuje tylko z istniejącym PRODUCT.

Nie implementuj:
- `CreateProduct`,
- `CreateManufacturer`,
- `Dodaj produkt`,
- bezpośredniego INSERT z UI.

Nowy PRODUCT powstanie później przez workflow SDS.

## 5. Tożsamość i status — read-only

Nie umożliwiaj edycji:

```text
product_name
manufacturer_product_code
manufacturer_id
usage_status
```

Producent i status są tylko prezentowane.

Nie implementuj `SetProductStatus`. Sprint 2 nie implementuje przejść SDS/BHP.

## 6. Edycja administracyjna

Formularz może zmieniać wyłącznie:

```text
use_description
use_restriction
waste_type
waste_code
```

Użyj:

```text
UpdateProductAdministrativeData
```

Nie dodawaj walidacji prawnej waste/BDO, słowników ani nowych reguł obowiązkowości.

Po zapisie:
1. operacja przez `TransactionExecutor`,
2. commit,
3. ponowny `GetProductDetails`,
4. prezentacja danych odczytanych z Application.

## 7. Widok Stanowiska

Rozwiń placeholder `Stanowiska` do minimalnego słownika `USAGE_LOCATION`.

Źródło:

```text
ListUsageLocations
```

Lista administracyjna pokazuje zarówno ACTIVE, jak i INACTIVE.

## 8. Create UsageLocation

Użyj:

```text
CreateUsageLocation
```

Nowa lokalizacja:

```text
status = ACTIVE
```

Nie pokazuj pola statusu podczas tworzenia.

## 9. Deactivate / Reactivate

ACTIVE:

```text
DeactivateUsageLocation
ACTIVE → INACTIVE
```

INACTIVE:

```text
ReactivateUsageLocation
INACTIVE → ACTIVE
```

Zachowaj ten sam `location_id`.

Nie wykonuj DELETE i nie twórz rekordu zastępczego.

## 10. Przypisanie lokalizacji do PRODUCT

Nowe przypisanie może dotyczyć tylko ACTIVE lokalizacji.

UI może filtrować wybór do ACTIVE, ale Application pozostaje warstwą ochrony i nadal musi odrzucać INACTIVE.

Użyj:

```text
AssignProductUsageLocation
```

Nie zapisuj relacji bezpośrednio przez repository.

## 11. Brak REMOVE

Nie implementuj:

```text
RemoveProductUsageLocation
DeleteProductUsageLocation
```

Brak zatwierdzonej polityki historii dla usuwania relacji.

## 12. Peak quantity

Obsłuż:

```text
peak_quantity_value >= 0
peak_quantity_unit wymagane
```

`0` jest prawidłową wartością biznesową.

Przed przekazaniem do Application zachowaj `Decimal`. Nie wprowadzaj biznesowej semantyki opartej na `float` i nie wykonuj niezatwierdzonego zaokrąglania.

## 13. Monthly consumption

Zachowaj rozróżnienie:

```text
None / None = brak informacji
0 + unit    = świadome zero
```

UI musi umożliwić użytkownikowi jednoznaczny wybór „brak danych” vs `0`.

Preferowany prosty mechanizm:
- checkbox `Podaj miesięczne zużycie`,
- zaznaczony → value + unit,
- niezaznaczony → `None/None`.

Reguły:
- value >= 0,
- unit wymagane przy value,
- `None/None` poprawne,
- `0 + unit` poprawne.

Walidacja Domain/Application pozostaje źródłem prawdy.

## 14. Jednostki

Nie twórz słownika ani konwersji jednostek.

`peak_quantity_unit` i `monthly_consumption_unit` pozostają tekstem i mogą być różne.

Nie implementuj kg↔g ani l↔ml.

## 15. Edycja istniejącego przypisania

Użyj:

```text
UpdateProductUsageLocation
```

Edytowalne tylko:

```text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Nie umożliwiaj zmiany:

```text
product_id
location_id
```

## 16. Minimalny UX

Preferowana struktura `Produkty`:

```text
Produkt
├── Dane podstawowe        read-only
├── Dane administracyjne  edit
└── Miejsca stosowania
    ├── istniejące przypisania
    ├── edycja quantity
    └── nowe przypisanie
```

Preferowana struktura `Stanowiska`:

```text
Stanowiska
├── lista
├── status
├── dodaj lokalizację
└── deactivate/reactivate
```

Nie przebudowuj TASK-013 tylko dla estetyki.

## 17. Transakcje

Wszystkie zapisy:

```text
UpdateProductAdministrativeData
CreateUsageLocation
DeactivateUsageLocation
ReactivateUsageLocation
AssignProductUsageLocation
UpdateProductUsageLocation
```

muszą przechodzić przez istniejący `TransactionExecutor`.

UI nie wykonuje `commit()` ani `rollback()`.

## 18. Obsługa błędów

Istniejące błędy Application/Domain, np. `EntityNotFoundError` i `InactiveUsageLocationError`, pokazuj jako krótkie kontrolowane komunikaty.

`PersistenceError` pozostaje neutralnym błędem technicznym.

Nie pokazuj tracebacku, SQL, pełnego DATABASE_URL ani sekretów.

Nie buduj parsera constraintów PostgreSQL.

## 19. Test — administracja PRODUCT

Potwierdź:
- wybór istniejącego PRODUCT,
- edycję czterech dozwolonych pól,
- zapis przez Application,
- ponowny odczyt,
- brak zmiany `product_name`,
- brak zmiany `manufacturer_product_code`,
- brak zmiany producenta,
- brak zmiany `usage_status`.

## 20. Test — lifecycle UsageLocation

Potwierdź:

```text
Create → ACTIVE
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Ten sam `location_id`, brak DELETE, lista zawiera ACTIVE i INACTIVE.

## 21. Test — assignment

Potwierdź:
- ACTIVE dostępna do nowego przypisania,
- INACTIVE nie jest oferowana,
- Application nadal odrzuca INACTIVE,
- poprawne przypisanie zapisuje peak/monthly,
- szczegóły PRODUCT pokazują przypisanie,
- PRODUCT może mieć wiele lokalizacji.

## 22. Test — quantities

Peak:

```text
0        → OK
positive → OK
negative → reject
```

Monthly:

```text
None/None       → OK
0 + unit        → OK
positive + unit → OK
negative        → reject
value bez unit  → reject
```

Potwierdź różne jednostki peak/monthly i brak konwersji.

## 23. Test — update assignment

Potwierdź:
- zmianę peak,
- zmianę monthly,
- zapis przez `UpdateProductUsageLocation`,
- ponowny odczyt,
- niezmienione `product_id/location_id`.

## 24. Test — UI read-only boundary

Nie mogą istnieć kontrolki zapisujące dla:

```text
product_name
manufacturer_product_code
manufacturer
usage_status
```

Nie ma:
- Add Product,
- Create Manufacturer,
- Delete Location,
- Remove Assignment,
- Set Product Status.

## 25. PostgreSQL vertical

Dla nowych operacji UI potwierdź odpowiedni pion:

```text
Streamlit action
→ Application
→ TransactionExecutor
→ Repository
→ PostgreSQL
→ new session read
```

Nie duplikuj całego pakietu persistence TASK-010/011.

Fixture może technicznie tworzyć MANUFACTURER/PRODUCT tylko w setupie testu.

Po testach: `0 business records`.

## 26. Architektura

Obowiązuje:

```text
presentation → application → domain
composition root → infrastructure
```

Widoki nie importują SQLAlchemy, psycopg ani ORM.

Application nie importuje presentation/Streamlit/infrastructure.

Domain nie importuje presentation/Streamlit/application/infrastructure.

Nie osłabiaj testów AST.

## 27. Schema / Alembic

TASK-014 nie zmienia:
- Domain model shape,
- Application contracts,
- ORM,
- constraints,
- tabel.

Nie twórz migracji #5.

Jeżeli workflow wymaga którejkolwiek z tych zmian: **STOP**.

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

## 28. Pełna regresja

Stan bazowy:

```text
96 passed
```

Zachowaj testową konfigurację katalogu tymczasowego przyjętą podczas domknięcia TASK-013.

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie testy muszą przejść bez `SAWarning`.

## 29. Manual Streamlit smoke

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/app.py
```

Na pustej bazie potwierdź:
- aplikacja startuje,
- Produkty mają poprawny empty state,
- Stanowiska działa,
- można utworzyć lokalizację bez PRODUCT,
- brak `Dodaj produkt`,
- brak `Dodaj nowy SDS`.

Scenariusze wymagające PRODUCT realizuj fixture/testami, nie trwałym seedem.

## 30. Git i bezpieczeństwo

Uruchom:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored/nietrackowany,
- brak sekretów i pełnego DATABASE_URL,
- brak dumpów/backupów/PDF/MSG,
- brak pozostawionych fixture,
- brak nowych bibliotek,
- brak commit/push bez jawnego polecenia.

## 31. Poza zakresem

TASK-014 NIE implementuje:
- CreateProduct,
- CreateManufacturer,
- zmian identity PRODUCT,
- zmian ProductUsageStatus,
- SDS/BHP/SafetyProfile/SDS_COMPONENT,
- historii/audytu,
- DeleteUsageLocation,
- RemoveProductUsageLocation,
- inventory/warehouse,
- BDO/waste module,
- REACH,
- importu Excel,
- słownika/konwersji jednostek,
- nowych bibliotek,
- nowych tabel,
- migracji #5.

## 32. STOP

Raportuj `PARTIAL/BLOCKED`, jeżeli:
- istniejące use case'y/DTO/porty nie wystarczają,
- potrzebna jest zmiana Application contract,
- potrzebna jest zmiana Domain/ORM/schema/migracja,
- potrzebny jest CreateProduct/CreateManufacturer,
- potrzebna jest zmiana ProductUsageStatus,
- potrzebny jest Remove/Delete relacji,
- potrzebna jest decyzja historii,
- potrzebna jest walidacja prawna waste/BDO,
- potrzebny jest słownik/konwersja jednostek,
- potrzebna jest nowa biblioteka,
- zakres wchodzi w TASK-015/TASK-016/SDS/BHP.

## 33. Kryteria DONE

TASK-014 = DONE, jeśli:
1. Product Registry nadal działa,
2. cztery pola administracyjne są edytowalne,
3. zapis używa `UpdateProductAdministrativeData`,
4. identity i `usage_status` są read-only,
5. Stanowiska pokazują ACTIVE/INACTIVE,
6. można Create/Deactivate/Reactivate lokalizację,
7. reaktywacja zachowuje `location_id`,
8. brak DELETE lokalizacji,
9. ACTIVE można przypisać do PRODUCT,
10. INACTIVE nie jest oferowana i Application nadal ją blokuje,
11. PRODUCT może mieć wiele lokalizacji,
12. peak >= 0 i peak=0 działają,
13. monthly None i zero są rozróżnione,
14. monthly >=0 działa,
15. błędne monthly są odrzucane,
16. brak konwersji jednostek,
17. można edytować quantity istniejącej relacji,
18. identity relacji pozostaje niezmienna,
19. brak RemoveProductUsageLocation,
20. wszystkie zapisy przechodzą przez TransactionExecutor,
21. UI nie wykonuje SQL/commit/rollback,
22. błędy są kontrolowane,
23. testy UI/PostgreSQL/architektury przechodzą,
24. pełna regresja przechodzi bez SAWarning,
25. brak zmian Domain/Application contracts/ORM/schema,
26. brak migracji #5,
27. PostgreSQL = 9 tabel,
28. `alembic current = d2b4f6a8c190 (head)`,
29. `alembic check` bez driftu,
30. po testach 0 rekordów biznesowych,
31. brak nowych bibliotek,
32. brak historii/SDS/BHP,
33. utworzono TASK-014_REPORT,
34. TASK-015 i TASK-016 nie zostały rozpoczęte.

## 34. Raport

Utwórz:

```text
docs/task_reports/TASK-014_REPORT.md
```

Raport zawiera co najmniej:
1. Status i stan wejściowy.
2. Zmienione pliki.
3. Product administrative form.
4. Ochronę identity/status.
5. UsageLocation list/create/deactivate/reactivate.
6. ACTIVE-only assignment.
7. Peak/monthly i Decimal boundary.
8. Update assignment.
9. Brak remove/delete.
10. TransactionExecutor i błędy.
11. Testy UI/PostgreSQL/architektury.
12. Manual Streamlit smoke.
13. Pełny pytest / SAWarning.
14. Brak zmian Domain/Application contracts/ORM/schema.
15. `alembic current/check`.
16. Finalny stan PostgreSQL.
17. Git/bezpieczeństwo.
18. Odstępstwa i ryzyka.
19. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-015 ANI TASK-016.
```

## 35. Autoryzacja

Obecność pliku:

```text
docs/tasks/TASK-014_Product_Administration_Usage_Workflow.md
```

nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po:

```text
Wykonaj TASK-014.
```

Po raporcie zatrzymuje się. Nie rozpoczyna TASK-015 ani TASK-016.

## 36. Oczekiwany stan końcowy

```text
TASK-013 ACCEPTED
        ↓
Product Registry
        ↓
TASK-014
        ↓
Product Administration
+ UsageLocation Administration
+ Product ↔ Location
+ Peak / Monthly
        ↓
existing Application contracts
        ↓
TransactionExecutor
        ↓
PostgreSQL
        ↓
schema unchanged
        ↓
DECISION GATE: HISTORY
```
