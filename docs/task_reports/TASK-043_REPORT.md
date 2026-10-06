# TASK-043 REPORT

STATUS:
DONE

IMPLEMENTED:
- `location_code: str | None` w Domain, ORM i kontraktach odczytu; legacy `NULL` jest zwracany bez zastępowania go UUID.
- `CreateUsageLocationInput` wymaga symbolu. Use case wykonuje trim, uppercase i walidację formatu `^[A-Z0-9][A-Z0-9_-]{0,31}$`; duplikat zwraca `DuplicateLocationCodeError`, również przy konflikcie UNIQUE w bazie.
- Istniejący prosty formularz tworzenia lokalizacji przyjmuje symbol. Tabela Stanowiska i akcje wierszy pozostały bez przebudowy.
- Alembic `c7e5a82d9043`: `usage_locations.location_code VARCHAR(32) NULL`, CHECK formatu i UNIQUE dla wartości nie-NULL. Bez backfill, zmiany FK i zmiany tabel historii.

VALIDATION:
- Izolowany PostgreSQL 17: upgrade z `b379f54c12a0` do head, istniejąca lokalizacja i wpis historii zachowane, legacy `NULL` odczytywalne.
- Focused unit + integration + powiązana regresja: 73 passed.
- `alembic current`: `c7e5a82d9043`; `alembic check`: No new upgrade operations detected.
- `git diff --check` dla zmian śledzonych: bez błędów białych znaków.

DATA SAFETY:
- Dane operatora nie były modyfikowane. Migracja i testy zostały uruchomione wyłącznie na usuniętym po walidacji klastrze testowym.
- Katalog testowy po przerwanej pierwszej próbie został usunięty po potwierdzeniu, że proces PostgreSQL już nie działa.

DEVIATIONS / KNOWN ISSUE:
- Starszy test E2E `test_task016_sprint2_end_to_end_acceptance` zatrzymuje się przed przepływem lokalizacji: oczekuje tabeli produktów bez istniejącej kolumny „Rewizja SDS” (72 passed, 1 failed w tej rozszerzonej próbie). Widoku produktów nie zmieniano w TASK-043.
- Zastane usunięcia pod `.pytest_tmp/` i nowe dokumenty w `docs/tasks/` pozostawiono bez zmian.

NEXT:
- READY FOR CERBERUS REVIEW.
