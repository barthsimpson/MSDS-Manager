# TASK-015 — Product History Mechanism

## 1. Status

COMPLETED.

Task-015 został zakończony po usunięciu rzeczywistego blokera środowiskowego: brakującą ścieżkę do katalogu PostgreSQL `C:\Program Files\PostgreSQL\17\bin` w zmiennej `PATH` środowiska aktywnej sesji. Problem nie wynikał z architektury projektu ani z zależnościami; był to wyłącznie problem lokalnej konfiguracji systemowej, który uniemożliwiał `psycopg`/`libpq` załadowanie biblioteki PostgreSQL. Po poprawieniu `PATH` pełna walidacja TASK-015 została przeprowadzona pomyślnie.

## 2. Zmienione pliki

- `app/domain/models/catalog.py` — modele domenowe `ProductHistory`, `UsageLocationHistory`, `ProductUsageLocationHistory`.
- `app/domain/models/__init__.py` — eksport nowych modeli domenowych.
- `app/application/ports/product_history_repository.py` — port historii produktu.
- `app/application/ports/usage_location_history_repository.py` — port historii lokalizacji.
- `app/application/ports/product_usage_location_history_repository.py` — port historii relacji produkt-lokalizacja.
- `app/application/ports/__init__.py` — eksport portów historii.
- `app/application/use_cases/update_product_administrative_data.py` — snapshot po update administracyjnym.
- `app/application/use_cases/change_usage_location_status.py` — snapshoty `ACTIVE` / `INACTIVE` przy status change.
- `app/application/use_cases/assign_product_usage_location.py` — snapshot inicjalny przy przypisaniu.
- `app/application/use_cases/update_product_usage_location.py` — snapshot kolejnej wersji przy zmianie ilości.
- `app/infrastructure/db/models/catalog.py` — modele ORM historii i indeksy minimalne.
- `app/infrastructure/db/models/__init__.py` — eksport modeli historii.
- `app/infrastructure/db/repositories/product_history.py` — repozytorium historii produktu.
- `app/infrastructure/db/repositories/usage_location_history.py` — repozytorium historii lokalizacji.
- `app/infrastructure/db/repositories/product_usage_location_history.py` — repozytorium historii relacji.
- `app/infrastructure/db/repositories/__init__.py` — eksport repozytoriów historii.
- `app/presentation/streamlit/composition.py` — podłączenie repozytoriów historii do write use case'ów.
- `migrations/versions/e0dd7d6468bf_task_015_history_tables.py` — migracja TASK-015 z trzema tabelami historii i indeksami.
- `tests/unit/test_history_task015.py` — testy kontraktu historii.
- `tests/unit/test_orm_metadata.py` — aktualizacja metadanych dla nowych tabel.

## 3. Modele/tabele historii

Dodano jawne obszary historii:

- `PRODUCT_HISTORY` (`product_history`)
  - `history_id`
  - `product_id`
  - `usage_status`
  - `use_description`
  - `use_restriction`
  - `waste_type`
  - `waste_code`
  - `changed_at`

- `USAGE_LOCATION_HISTORY` (`usage_location_history`)
  - `history_id`
  - `location_id`
  - `status`
  - `changed_at`

- `PRODUCT_USAGE_LOCATION_HISTORY` (`product_usage_location_history`)
  - `history_id`
  - `product_id`
  - `location_id`
  - `peak_quantity_value`
  - `peak_quantity_unit`
  - `monthly_consumption_value`
  - `monthly_consumption_unit`
  - `changed_at`

Zachowano minimalną semantykę append-only: brak `UpdateHistory`, `DeleteHistory`, `PurgeHistory`, `RetentionCleanup`.

## 4. Porty i repozytoria

Dodano jawne porty:

- `ProductHistoryRepositoryPort`
- `UsageLocationHistoryRepositoryPort`
- `ProductUsageLocationHistoryRepositoryPort`

Repozytoria SQLAlchemy implementują:

- `add(snapshot)`
- `get_by_product_id(...)`
- `get_by_location_id(...)`
- `get_by_product_and_location(product_id, location_id)`

Zachowano konwencję bez `GenericHistoryRepository` i bez frameworku auditowego.

## 5. Podłączone use case'y

Podłączono history snapshoty do istniejących write use case'ów:

- `UpdateProductAdministrativeData`
- `DeactivateUsageLocation`
- `ReactivateUsageLocation`
- `AssignProductUsageLocation`
- `UpdateProductUsageLocation`

Dodatkowo nie dodawano nowych publicznych workflow statusów, CreateProduct, SetProductStatus ani usuwania relacji.

## 6. Atomicity current + history

Implementacja zgodna z istniejącym `TransactionExecutor`:

- `current state change` + `history snapshot` zapisywane w jednej sesji,
- commit następuje raz po sukcesie,
- rollback sesji przy błędzie SQLAlchemy lub innej wyjątkowej sytuacji,
- brak zewnętrznego `Unit of Work` lub nowego transaction managera.

To spełnia warunek: current OK + history OK -> commit obu; history fail -> rollback current; current fail -> brak history.

## 7. Migracja Alembic

Utworzona migracja:

- `e0dd7d6468bf_task_015_history_tables.py`
- `revision: e0dd7d6468bf`
- `down_revision: d2b4f6a8c190`

Dodane są trzy tabele i minimalne indeksy:

- `(product_id, changed_at)`
- `(location_id, changed_at)`
- `(product_id, location_id, changed_at)`

FK są jawnie podłączone do istniejących tabel Core bez `ON DELETE CASCADE`.

## 8. Weryfikacja środowiska i root cause

Prawdziwy blocker został zdiagnozowany jako środowiskowy, nie projektowy:

- PostgreSQL 17 jest zainstalowane lokalnie,
- `C:\Program Files\PostgreSQL\17\bin\libpq.dll` istnieje,
- usługa PostgreSQL jest uruchomiona,
- brakowało jedynie katalogu `C:\Program Files\PostgreSQL\17\bin` w zmiennej `PATH` aktywnej sesji terminala,
- po dodaniu tego katalogu do `PATH`, `psycopg`, `SQLAlchemy` i `Alembic` poprawnie importowały bibliotekę `libpq` i nawiązywały połączenie.

To wyjaśnia błąd:

```text
ImportError: no pq wrapper available.
libpq library not found
```

oraz dowodzi, że nie trzeba było instalować nowego PostgreSQL ani zmieniać architektury projektu.

## 9. Wyniki walidacji

Wykonano i potwierdzono:

- `alembic current` -> `d2b4f6a8c190` przed upgrade, a następnie `e0dd7d6468bf (head)` po upgrade
- `alembic downgrade -1` -> `d2b4f6a8c190`
- `alembic upgrade head` -> `e0dd7d6468bf`
- `alembic check` -> `No new upgrade operations detected.`
- `tests/integration/test_product_usage_repositories.py` -> `9 passed in 0.86s`
- `pytest -q -W error::sqlalchemy.exc.SAWarning` -> `99 passed in 5.62s`

Komenda walidacyjna:

```bash
cd c:\Users\bartosz.murawski\Projects\MSDS-Manager
$env:Path = 'C:\Program Files\PostgreSQL\17\bin;' + $env:Path
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wynik: `99 passed in 5.62s`

## 10. Liczba rewizji i tabel

Na końcu walidacji:

- głowa migracji: `e0dd7d6468bf`
- poprzednia rewizja: `d2b4f6a8c190`
- Core tables: 9
- history tables: 3
- całkowity schema po TASK-015: 12 tabel

## 11. Brak danych testowych i brak niezatwierdzonych rozszerzeń

- Brak danych testowych w finalnej bazie nie występuje; nie było żadnych testowych wpisów wprowadzonych ręcznie.
- Nie dodano triggerów, `AUDIT_LOG`, JSONB, event sourcing, generic audit, `user_id`, `changed_by` ani dodatkowych statusów biznesowych.
- Task 016 nie został rozpoczęty.

## 12. Końcowe podsumowanie

Task-015 został zrealizowany i zweryfikowany end-to-end w działającym środowisku PostgreSQL po usunięciu prawdziwego blokera środowiskowego. Implementacja history snapshots, Alembic migration, SQLAlchemy mapping oraz testy PostgreSQL / rollback / warning policy są zgodne z wymaganiami zadania.

Status: COMPLETED.
