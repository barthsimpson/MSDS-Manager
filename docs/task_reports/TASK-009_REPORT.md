# TASK-009 — raport wykonania

## 1. Status

**DONE**

**TASK-009 resumed after accepted TASK-009-ALIGN.** Wcześniejszy prawidłowy
status `BLOCKED` został zastąpiony po usunięciu blockera przez Core v1.2,
BDR-002 v1.2 i zaakceptowany TASK-009-ALIGN.

## 2. Stan wejściowy po TASK-009-ALIGN

- `UsageLocationStatus`: `ACTIVE`, `INACTIVE`.
- Nowa lokalizacja: `ACTIVE`.
- Przejścia Domain: `ACTIVE -> INACTIVE` i `INACTIVE -> ACTIVE`.
- Alembic revisions: 4.
- PostgreSQL: `d2b4f6a8c190 (head)`.
- Tabele aplikacyjne: 9.
- Testy bazowe: 63 passed.
- Drift: brak.
- Rekordy biznesowe: 0.

## 3. Porty

Dodano minimalne porty application:

- `ProductRepositoryPort`: lista, szczegóły i aktualizacja wyłącznie danych
  administracyjnych,
- `UsageLocationRepositoryPort`: lista, odczyt po ID, dodanie i aktualizacja
  statusu,
- `ProductUsageLocationRepositoryPort`: dodanie przypisania i aktualizacja jego
  ilości.

Istniejący `ManufacturerRepositoryPort` pozostał bez zmian. Nie utworzono
generic CRUD, portu delete ani zależności od infrastructure/SQLAlchemy.

## 4. DTO

Dodano niezmienne dataclasses:

- `ProductListItem`,
- `ProductDetails`,
- `ProductUsageLocationDetails`,
- `UpdateProductAdministrativeDataInput`,
- `CreateUsageLocationInput`,
- `AssignProductUsageLocationInput`,
- `UpdateProductUsageLocationInput`.

DTO nie zawierają modeli ORM ani pól „na przyszłość”.

## 5. Use case'y

Dodano:

- `ListProducts`,
- `GetProductDetails`,
- `UpdateProductAdministrativeData`,
- `ListUsageLocations`,
- `CreateUsageLocation`,
- `DeactivateUsageLocation`,
- `ReactivateUsageLocation`,
- `AssignProductUsageLocation`,
- `UpdateProductUsageLocation`.

Nie dodano `CreateProduct`, `CreateManufacturer`, `SetProductStatus`, delete,
UI, persistence ani infrastruktury transakcyjnej.

## 6. Ochrona tożsamości PRODUCT

`UpdateProductAdministrativeDataInput` zawiera dokładnie:

```text
product_id
use_description
use_restriction
waste_type
waste_code
```

`product_id` identyfikuje aktualizowany rekord. Kontrakt nie przyjmuje
`product_name`, `manufacturer_product_code` ani `manufacturer_id`, więc nie
pozwala zmieniać pól tożsamości.

## 7. Granica `usage_status`

Status PRODUCT jest dostępny wyłącznie w DTO odczytowych. Nie występuje w DTO
aktualizacji administracyjnej. Nie dodano ogólnego ustawiania statusu ani
przejść SDS/BHP.

## 8. `ListManufacturers`

Istniejące `ManufacturerRepositoryPort` i `ListManufacturers` zachowano bez
zmian. Dotychczasowy test integracyjny oraz nowy test z fake repository
przechodzą.

## 9. Kontrakty UsageLocation

- `ListUsageLocations` zwraca pełną listę administracyjną obejmującą `ACTIVE` i
  `INACTIVE`.
- `CreateUsageLocation` przyjmuje tylko `location_name`, tworzy domenowy obiekt
  z nowym ID i zatwierdzonym domyślnym statusem `ACTIVE`, po czym przekazuje go
  do portu `add`.
- `DeactivateUsageLocation` pobiera istniejący obiekt, używa domenowego
  `deactivate()` i przekazuje wynik do `update_status`; nie wykonuje delete.
- Braki encji są reprezentowane przez technologicznie niezależny
  `EntityNotFoundError`.

## 10. `ReactivateUsageLocation`

Use case pobiera istniejącą lokalizację, korzysta z domenowego `reactivate()` i
aktualizuje status przez port. Zachowuje ten sam `location_id`, nie tworzy
zastępczej lokalizacji i nie implementuje historii.

## 11. Blokada przypisania do `INACTIVE`

`AssignProductUsageLocation` wymaga `UsageLocationRepositoryPort`, odczytuje
lokalizację i dopuszcza nowe przypisanie wyłącznie przy
`UsageLocationStatus.ACTIVE`. Lokalizacja `INACTIVE` powoduje jednoznaczny
`InactiveUsageLocationError`, zanim port przypisania otrzyma dane.

## 12. Kontrakt ProductUsageLocation

- `AssignProductUsageLocation` tworzy domenowy `ProductUsageLocation` i
  przekazuje go do wąskiego portu `add`.
- `UpdateProductUsageLocation` tworzy zwalidowany obiekt z tym samym
  `product_id/location_id` i przekazuje do `update_quantities`.
- Nie dodano zmiany tożsamości relacji ani operacji delete/remove.
- Brak przypisania przy aktualizacji jest reprezentowany przez
  `EntityNotFoundError`.

## 13. `Decimal`, `0`, `NULL` i jednostki

DTO quantity używają `Decimal`. Use case'y budują istniejący model Domain, więc
ponownie wykorzystują walidację TASK-008:

- peak `0` jest poprawne,
- monthly `None/None` jest poprawne,
- monthly `0 + unit` jest poprawne i różne od `NULL`,
- wartości ujemne są odrzucane,
- monthly value/unit muszą występować razem,
- peak i monthly zachowują niezależne jednostki,
- brak automatycznej konwersji jednostek.

## 14. Testy application

Dodano `tests/unit/test_application_contracts.py` z prostymi fake repositories.
Plik zawiera 18 testów pokrywających kontrakty Product, Manufacturer,
UsageLocation i ProductUsageLocation, w tym warianty błędne walidacji Domain.

Wynik nowych testów application oraz istniejących testów granic:

```text
20 passed
```

## 15. Test architektury

Istniejąca kontrola AST potwierdza:

- application nie importuje infrastructure, SQLAlchemy, psycopg ani Alembic,
- domain nie importuje application, infrastructure, SQLAlchemy, psycopg,
  Alembic ani Streamlit.

Wynik: 2 passed.

## 16. Pełny pytest / `SAWarning`

Uruchomiono wymaganą komendę:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **81 passed**, kod wyjścia 0, brak `SAWarning`.

## 17. Brak zmian ORM/schema

Wznowiony TASK-009 zmienił wyłącznie warstwę application, jej testy i ten
raport. Nie zmodyfikował zaakceptowanego ORM/migracji z TASK-009-ALIGN,
constraintów, konfiguracji Alembic ani `pyproject.toml`. Nie utworzono piątej
migracji.

## 18. `alembic current`

```text
d2b4f6a8c190 (head)
```

Liczba rewizji: 4.

## 19. `alembic check`

```text
No new upgrade operations detected.
```

Rzeczywisty drift ORM ↔ PostgreSQL: brak.

## 20. Finalny stan PostgreSQL

- current/head: `d2b4f6a8c190`,
- tabele aplikacyjne: 9,
- rekordy w każdej z 9 tabel: 0,
- dane testowe pozostawione: nie,
- schema i constraints po TASK-009-ALIGN: bez zmian.

## 21. Git/bezpieczeństwo

- `git diff --check`: bez błędów (wyłącznie ostrzeżenia konwersji LF/CRLF),
- `git diff --cached --check`: bez błędów,
- `.env`: ignorowany przez Git i nietrackowany,
- nowe biblioteki / zmiany `pyproject.toml`: brak,
- dumpy, backupy, PDF-y i pliki MSG w repozytorium: brak,
- ujawnione sekrety: brak,
- commit/push: nie wykonano,
- wcześniejsze niezatwierdzone zmiany TASK-008/TASK-009-ALIGN zachowano.

## 22. Odstępstwa

Brak odstępstw od `TASK-009 v1.1-resume`. Oczekiwania starej wersji dotyczące
3 rewizji i head `c41d8e2f7a90` zostały prawidłowo zastąpione przez stan po
zaakceptowanym TASK-009-ALIGN: 4 rewizje i `d2b4f6a8c190`.

## 23. Problemy/ryzyka

Brak blockerów. Techniczna implementacja nowych portów, granicy transakcji i
obsługi konfliktów zapisu pozostaje świadomie poza zakresem TASK-009 i wymaga
osobnej, jawnej realizacji przyszłego Tasku. Nie zaprojektowano historii ani
polityki usuwania relacji.

## 24. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-010.
