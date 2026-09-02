# TASK-011 — Product Business Rules & Integration Tests

**Projekt:** MSDS Manager  
**Task ID:** TASK-011  
**Sprint:** SPRINT-002 v1.2-approved  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

## 1. Cel

Domknąć i zweryfikować reguły biznesowe Sprintu 2 dla **istniejącego PRODUCT** poprzez testy application + infrastructure + PostgreSQL.

TASK-011 ma potwierdzić:
- odczyt produktu,
- ochronę tożsamości PRODUCT,
- edycję danych administracyjnych,
- cykl życia USAGE_LOCATION,
- przypisanie produktu do jednej i wielu lokalizacji,
- peak quantity,
- monthly consumption,
- blokadę przypisań do INACTIVE,
- commit/rollback,
- brak automatycznej konwersji jednostek.

TASK-011 nie buduje UI i nie zmienia modelu danych.

## 2. Stan wejściowy

Po zaakceptowanym TASK-010:

```text
CORE                    v1.2-approved
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Tests                   88 passed
Schema drift            none
Business records        0
```

Dostępne są use case'y TASK-009 oraz adaptery SQLAlchemy i `TransactionExecutor` z TASK-010.

## 3. Źródła nadrzędne

1. CORE-001 v1.2-approved
2. BDR-002 v1.2-approved
3. pozostałe zatwierdzone BDR-001..005
4. TDR-001..003
5. SPRINT-002 v1.2-approved
6. zaakceptowane TASK-008, TASK-009-ALIGN, TASK-009, TASK-010
7. root AGENTS.md

Brak jednoznacznej reguły = **STOP**. Codex nie dopisuje decyzji biznesowej w testach.

## 4. Zasada wykonania

TASK-011 jest przede wszystkim Taskiem walidacyjnym.

Najpierw testuj istniejące zachowanie. Kod produkcyjny zmieniaj tylko wtedy, gdy test ujawnia rzeczywistą niezgodność z zatwierdzonym Core.

Nie refaktoryzuj „przy okazji”.

## 5. Dane testowe

Ponieważ Sprint 2 nie posiada publicznego `CreateProduct`, integracyjne dane wejściowe mogą być tworzone technicznie w setupie testowym.

Dopuszczalne setupy:
- MANUFACTURER,
- PRODUCT,
- USAGE_LOCATION.

Setup:
- nie staje się funkcją produkcyjną,
- nie tworzy seeda,
- nie pozostawia danych w DB,
- nie omija testowanego use case'u dla właściwej operacji.

## 6. Product — odczyt

Potwierdź na realnym PostgreSQL:

1. `ListProducts` na pustej bazie zwraca pustą listę.
2. Istniejący PRODUCT pojawia się na liście.
3. Producent jest poprawnie powiązany.
4. `usage_status` jest poprawnie mapowany.
5. `waste_type` i `waste_code` mogą być NULL.
6. `GetProductDetails` zwraca producenta i przypisane lokalizacje.
7. Quantity pozostają `Decimal`.
8. Brak produktu daje kontrolowany `EntityNotFoundError`.
9. ORM exceptions nie wyciekają poza infrastructure/application.

## 7. Ochrona tożsamości PRODUCT

Tożsamość:

```text
product_name
manufacturer_product_code
manufacturer_id
```

musi pozostać niezmienna podczas `UpdateProductAdministrativeData`.

Test ma odczytać wartości przed i po operacji.

Dozwolona aktualizacja dotyczy wyłącznie:

```text
use_description
use_restriction
waste_type
waste_code
```

`usage_status` również ma pozostać bez zmian.

Nie twórz `SetProductStatus`.

## 8. USAGE_LOCATION — create/deactivate/reactivate

Potwierdź pionowo:

```text
CreateUsageLocation
→ repository
→ TransactionExecutor
→ PostgreSQL
```

Nowa lokalizacja ma:

```text
status = ACTIVE
```

Dezaktywacja:

```text
ACTIVE → INACTIVE
```

Reaktywacja:

```text
INACTIVE → ACTIVE
```

W obu przypadkach:
- zachowaj ten sam `location_id`,
- nie twórz drugiego rekordu,
- nie wykonuj DELETE.

`ListUsageLocations` ma zwracać zarówno ACTIVE, jak i INACTIVE.

## 9. PRODUCT ↔ USAGE_LOCATION

### Jedno przypisanie

Potwierdź:

```text
PRODUCT → ACTIVE USAGE_LOCATION
```

przez `AssignProductUsageLocation`.

Po commit:
- relacja istnieje,
- GetProductDetails ją zwraca,
- quantity są poprawne.

### Wiele lokalizacji

Potwierdź:

```text
PRODUCT
├── LOCATION A
└── LOCATION B
```

Obie ACTIVE, oba przypisania istnieją jednocześnie.

### INACTIVE

Próba przypisania do INACTIVE:

```text
AssignProductUsageLocation
→ InactiveUsageLocationError
```

Nie może pozostawić relacji ani częściowych danych.

## 10. Peak quantity

Potwierdź:

- `Decimal("0")` jest poprawne i po odczycie nadal oznacza zero,
- wartość dodatnia jest poprawna,
- wartość ujemna jest odrzucana przez istniejącą walidację Domain,
- brak automatycznej konwersji jednostek.

## 11. Monthly consumption

Potwierdź:

```text
None / None
```
= brak informacji.

Potwierdź:

```text
Decimal("0") + unit
```
= świadome zerowe zużycie.

Potwierdź dodatnią wartość.

Odrzuć:
- wartość ujemną,
- value bez unit,
- unit bez value.

Peak i monthly mogą mieć różne jednostki.

## 12. UpdateProductUsageLocation

Potwierdź pionowo:

```text
UpdateProductUsageLocation
→ repository
→ commit
→ PostgreSQL
```

Aktualizowane są wyłącznie:
- peak_quantity_value,
- peak_quantity_unit,
- monthly_consumption_value,
- monthly_consumption_unit.

`product_id` i `location_id` pozostają bez zmian.

## 13. Agregacja

Zachowaj istniejące testy domenowe `peak_factory_quantity`:

- zgodne jednostki → suma,
- różne jednostki → istniejący błąd domenowy,
- monthly consumption nie wpływa na wynik.

Nie twórz nowej usługi agregacji bazodanowej, jeśli jej jeszcze nie ma.

## 14. Commit

Dla poprawnych operacji zapisujących potwierdź, że zmiana jest widoczna w nowej sesji po commit.

Dotyczy co najmniej:
- UpdateProductAdministrativeData,
- CreateUsageLocation,
- DeactivateUsageLocation,
- ReactivateUsageLocation,
- AssignProductUsageLocation,
- UpdateProductUsageLocation.

## 15. Rollback

Zachowaj testy rollback z TASK-010 i potwierdź co najmniej jeden pionowy scenariusz:

1. poprawna zmiana w transakcji,
2. późniejszy błąd persistence,
3. rollback całości,
4. nowa sesja potwierdza brak częściowego zapisu.

Nie twórz nowej biznesowej semantyki konfliktu.

## 16. Błędy

Potwierdź `EntityNotFoundError` co najmniej dla:
- brak PRODUCT w GetProductDetails,
- brak USAGE_LOCATION dla deactivate/reactivate,
- brak PRODUCT_USAGE_LOCATION dla update quantities.

Potwierdź, że SQLAlchemy/PostgreSQL error przechodzący przez `TransactionExecutor`:
- wykonuje rollback,
- jest tłumaczony na `PersistenceError`,
- zachowuje oryginalny wyjątek jako `__cause__`,
- nie otrzymuje niezatwierdzonej interpretacji biznesowej.

## 17. PostgreSQL

Testy integracyjne używają rzeczywistego PostgreSQL, nie SQLite.

Po testach:
- 0 danych biznesowych/testowych,
- 9 tabel aplikacyjnych,
- brak zmian constraints.

## 18. Brak zmian schema

TASK-011 nie wymaga:
- zmian ORM,
- nowej migracji,
- nowych constraints,
- nowych tabel.

Stan końcowy:

```text
Alembic revisions       4
PostgreSQL current      d2b4f6a8c190 (head)
Application tables      9
Schema drift            none
```

Jeżeli zatwierdzona reguła wymaga zmiany schema:

```text
STOP
```

Nie twórz migracji #5.

## 19. Alembic

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

## 20. Architektura

Potwierdź:

```text
application
  NIE importuje infrastructure / SQLAlchemy / psycopg

domain
  NIE importuje application / infrastructure / persistence

infrastructure
  implementuje application ports
```

Nie osłabiaj istniejących testów AST.

## 21. Poza zakresem

Nie implementuj:
- Streamlit,
- Product Registry View,
- formularzy,
- CreateProduct,
- CreateManufacturer,
- SDS workflow,
- BHP workflow,
- SetProductStatus,
- historii/audytu,
- DeleteUsageLocation,
- RemoveProductUsageLocation,
- importu Excel,
- REACH,
- BDO,
- modułu gospodarki odpadami,
- słownika jednostek,
- konwersji jednostek,
- nowych bibliotek,
- nowej migracji.

## 22. Historia

TASK-011 nie implementuje mechanizmu historii.

Fakt, że INACTIVE pozostaje w tabeli, nie jest pełną historyzacją.

TASK-015 pozostaje osobnym, warunkowym Taskiem.

## 23. Pełna regresja

Stan bazowy:

```text
88 passed
```

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie testy muszą przejść bez `SAWarning`.

## 24. Git i bezpieczeństwo

Wykonaj:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored i nietrackowany,
- brak sekretów,
- brak dumpów/backupów,
- brak PDF/MSG,
- brak danych testowych,
- brak nowych bibliotek,
- brak commit/push bez jawnego polecenia.

## 25. STOP

Raportuj `PARTIAL/BLOCKED`, jeżeli:
- zatwierdzona reguła nie ma jednoznacznej semantyki,
- potrzebny jest nowy status,
- potrzebna jest zmiana schema/migracja,
- potrzebny jest CreateProduct/CreateManufacturer,
- potrzebna jest nowa polityka delete/history,
- potrzebna jest konwersja jednostek,
- potrzebna jest nowa biblioteka,
- test ujawnia konflikt CORE/BDR/TDR,
- zakres wchodzi w UI TASK-012,
- zakres wchodzi w historię TASK-015.

## 26. Kryteria akceptacji

TASK-011 = DONE, jeżeli:

1. pusty ListProducts działa,
2. lista produktów działa,
3. GetProductDetails działa,
4. brak produktu daje EntityNotFoundError,
5. Product update zmienia tylko pola administracyjne,
6. tożsamość PRODUCT pozostaje niezmienna,
7. usage_status pozostaje niezmieniony,
8. CreateUsageLocation tworzy ACTIVE,
9. Deactivate daje INACTIVE,
10. Reactivate daje ACTIVE,
11. reaktywacja zachowuje location_id,
12. lista lokalizacji zawiera ACTIVE i INACTIVE,
13. można przypisać produkt do jednej ACTIVE lokalizacji,
14. można przypisać produkt do wielu ACTIVE lokalizacji,
15. nie można przypisać produktu do INACTIVE,
16. peak 0 jest poprawne,
17. peak dodatnie jest poprawne,
18. peak ujemne jest odrzucane,
19. monthly NULL/NULL jest poprawne,
20. monthly 0 + unit jest poprawne,
21. monthly dodatnie jest poprawne,
22. monthly ujemne jest odrzucane,
23. błędne pary monthly value/unit są odrzucane,
24. peak/monthly mogą mieć różne jednostki,
25. brak automatycznej konwersji,
26. UpdateProductUsageLocation aktualizuje tylko quantity,
27. PK relacji pozostaje niezmienny,
28. poprawne operacje są commitowane,
29. błąd powoduje rollback całej transakcji,
30. PersistenceError nie nadaje niezatwierdzonej semantyki,
31. integracja używa PostgreSQL tam, gdzie wymagane,
32. pełna regresja przechodzi bez SAWarning,
33. brak zmian ORM/schema,
34. brak migracji #5,
35. PostgreSQL nadal ma 9 tabel,
36. current = d2b4f6a8c190 (head),
37. alembic check bez driftu,
38. po testach 0 danych,
39. brak nowych bibliotek,
40. brak UI,
41. brak historii,
42. utworzono raport TASK-011,
43. TASK-012 nie został rozpoczęty.

## 27. Raport

Utwórz:

```text
docs/task_reports/TASK-011_REPORT.md
```

Raport ma zawierać:

1. Status.
2. Stan wejściowy.
3. Zakres zmian kodu.
4. Product read tests.
5. Ochronę tożsamości PRODUCT.
6. Aktualizację danych administracyjnych.
7. UsageLocation create/deactivate/reactivate.
8. Jedną i wiele lokalizacji produktu.
9. Blokadę INACTIVE.
10. Peak quantity scenarios.
11. Monthly consumption scenarios.
12. Jednostki i brak konwersji.
13. UpdateProductUsageLocation.
14. EntityNotFoundError.
15. PersistenceError.
16. Commit tests.
17. Rollback tests.
18. Testy PostgreSQL.
19. Pełny pytest / SAWarning.
20. Granice architektury.
21. Potwierdzenie braku zmian ORM/schema.
22. alembic current.
23. alembic check.
24. Finalny stan PostgreSQL.
25. Git/bezpieczeństwo.
26. Odstępstwa.
27. Problemy/ryzyka.
28. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-012.
```

## 28. Autoryzacja

Obecność pliku:

```text
docs/tasks/TASK-011_Product_Business_Rules_Integration_Tests.md
```

nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po poleceniu:

```text
Wykonaj TASK-011.
```

Po zakończeniu tworzy raport i nie rozpoczyna TASK-012.

## 29. Oczekiwany stan końcowy

```text
TASK-010 ACCEPTED
        ↓
repositories + transactions
        ↓
TASK-011
        ↓
business rules verified
        ↓
PostgreSQL integration verified
        ↓
full regression green
        ↓
schema unchanged
        ↓
READY FOR FIRST STREAMLIT SHELL
```
