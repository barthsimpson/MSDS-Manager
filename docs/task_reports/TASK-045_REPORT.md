# TASK-045 REPORT

STATUS:
DONE

PRECONDITION:
- `TASK-044_REPORT.md`: DONE; operator DB przed pracą: `c7e5a82d9043 (head)`.
- `usage_locations`: 3 rekordy, wszystkie `location_code = NULL`; `usage_location_history`: 0; `product_usage_locations`: 1.

IMPLEMENTED:
- `AssignLegacyUsageLocationCode` przyjmuje `location_id` i symbol użytkownika. Wymaga istniejącej lokalizacji z `NULL`, normalizuje i sprawdza format oraz unikalność. Istniejący nie-NULL symbol nie może być zmieniony.
- Repozytorium wykonuje warunkowy UPDATE tylko dla wskazanego `location_id` z `location_code IS NULL`; konflikt UNIQUE zgłasza jako kontrolowany błąd.
- Stanowiska: kolumny `Symbol | Lokalizacja | Status | Akcja`, `BRAK SYMBOLU` dla legacy, pole i przycisk `Uzupełnij` przy właściwym wierszu, lifecycle `Dezaktywuj` / `Reaktywuj` przy właściwym wierszu. UUID nie jest pokazywany jako wartość biznesowa. Widoczny licznik `Brak symbolu: N`.
- Formularz nowej lokalizacji zawiera wymagany symbol i nazwę.

VALIDATION:
- Unit/Application/AppTest: 22 focused PASS; powiązana regresja widoku i shell: 33 PASS.
- Izolowany PostgreSQL: 83 PASS, w tym warunkowy zapis, duplicate UNIQUE, zachowanie innych lokalizacji, historii i przypisań produktu; `alembic check` bez driftu.
- Odczytowy test nawigacji na bazie operatora: 3 PASS łącznie z testami widoku; bez zapisu danych.
- `git diff --check` dla zmian śledzonych: PASS.

OPERATOR DATA:
- Przed i po: 3 lokalizacje, 0 wpisów historii, 1 przypisanie produktu, `c7e5a82d9043`; wszystkie 3 symbole nadal `NULL`.
- SHA-256 pól `location_id`, `location_name`, `status`, `location_code`: `0bc770dd33b40b57ba162224a25f5d7360ea46873fd4ceeb253d5aa9605fc681` przed i po.
- Żaden symbol nie został zgadnięty ani przypisany na bazie operatora. Backfill następuje wyłącznie po wpisaniu symbolu przez użytkownika w UI.

SCOPE:
- Schema change: NO. Nowa migracja: NONE. NOT NULL hardening: NO.
- Zmiana historii, FK, ANALYTICS, Core i zależności: NONE.

DEVIATIONS:
- Test PostgreSQL użył istniejącego narzędzia `scripts/verify_task043.py`, rozszerzonego o testy TASK-045; migracje wykonane przez to narzędzie dotyczyły tylko usuniętego po testach klastra izolowanego.
- Zastane zmiany TASK-043/TASK-044 i usunięcia w `.pytest_tmp` pozostawiono bez zmian.

NEXT:
- READY FOR CERBERUS REVIEW.
