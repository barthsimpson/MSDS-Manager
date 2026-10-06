# TASK-044 REPORT

STATUS:
DONE

PRE-FLIGHT:
- revision before: `b379f54c12a0` (`alembic current` i `alembic_version`); jeden head repozytorium: `c7e5a82d9043`.
- usage_locations rows before: 3.
- usage_location_history rows before: 0.
- location_code column before: NO.
- existing-data fingerprint (SHA-256 pól `location_id`, `location_name`, `status`, uporządkowanych po `location_id`): `5423016c034eb432b07ca27e25767f864b9a98c3862bf506d917df87dab4e3b0`.

MIGRATION:
- applied: `alembic upgrade c7e5a82d9043` dokładnie raz na bazie operatora.
- revision after: `c7e5a82d9043`.
- schema result: `usage_locations.location_code VARCHAR(32) NULL`; CHECK `ck_usage_locations_location_code_format`; UNIQUE `uq_usage_locations_location_code` dla wartości nie-NULL.
- backfill: NO.

DATA SAFETY:
- usage_locations rows after: 3.
- usage_location_history rows after: 0.
- legacy location_code: `NULL` dla wszystkich 3 istniejących rekordów.
- existing-data fingerprint after: `5423016c034eb432b07ca27e25767f864b9a98c3862bf506d917df87dab4e3b0`.
- operator data preserved: YES — porównanie snapshotu pól istniejących lokalizacji oraz liczby rekordów przed i po migracji jest identyczne.
- new business rows: 0.

VALIDATION:
- alembic current: `c7e5a82d9043 (head)`.
- alembic check: `No new upgrade operations detected.`
- focused tests: 11 passed, 25 deselected (`test_application_contracts.py -k usage_location`), bez zapisu do bazy operatora.
- application read smoke: 3 legacy lokalizacje odczytane przez repozytorium; wszystkie `location_code = NULL`.
- git diff --check: PASS dla śledzonych zmian z wyłączeniem zastanych usunięć w `.pytest_tmp`.

DEVIATIONS:
- NONE. Tymczasowy snapshot zawierający pola lokalizacji usunięto po walidacji.
- Zastane zmiany repozytorium z TASK-043 oraz usunięcia w `.pytest_tmp` pozostawiono bez zmian.

NEXT:
- READY FOR TASK-045 po osobnym poleceniu użytkownika.
