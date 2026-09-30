# TASK-033 REPORT

STATUS: **DONE** — wznowienie po usunięciu blokady danych.

CHANGED:
- Domain: model UnitOfMeasure, kategorie VOLUME/MASS/COUNT, status ACTIVE/INACTIVE; ilości wskazują unit_id.
- ORM: unit_of_measure oraz FK jednostek w stanie bieżącym i historii.
- Migration: jedna rewizja a97e2cb7f31d z deterministycznym seedem pięciu jednostek, kontrolą pustych tabel i downgrade przywracającym kody.
- Repositories: zapis i odczyt unit_id; minimalne get_by_id/list_active.
- Tests: testy domeny, kontraktów, ORM i repozytoriów oraz test integracyjny słownika; skrypt walidacyjny sprawdza migrację i odtworzenie kodów podczas downgrade.

MIGRATION:
- Revision ID / new head: a97e2cb7f31d.
- Previous head: e0dd7d6468bf.
- Na izolowanym PostgreSQL: upgrade → zapis przykładowych rekordów → downgrade → potwierdzenie kodu kg w obu tabelach → usunięcie wyłącznie tych rekordów fixture → re-upgrade: PASS.
- Baza operatora była już na a97e2cb7f31d podczas preflight wznowienia. Nie ustalono, kiedy ani przez kogo wykonano wcześniejszy upgrade. Ponowne alembic upgrade head zakończyło się bez nowej operacji migracyjnej.

VALIDATION:
- Focused tests: 74 passed, 0 failed, 0 skipped na izolowanym PostgreSQL.
- Seed: l, ml, kg, g, szt; w bazie operatora potwierdzono pięć zatwierdzonych kodów, nazw, kategorii i status ACTIVE.
- UNIQUE, CHECK, FK, monthly NULL oraz 0 != NULL: PASS w testach integracyjnych.
- Alembic current: a97e2cb7f31d (head), zarówno na izolowanej bazie, jak i w bazie operatora.
- Alembic check: No new upgrade operations detected; schema drift: NONE.
- SAWarning: NONE przy uruchomieniu testów z -W error::sqlalchemy.exc.SAWarning.
- git diff --check dla śledzonych zmienionych plików w zakresie Tasku: PASS.

DATA SAFETY:
- Preflight wznowienia: product_usage_location_history = 0, product_usage_locations = 0. Obie tabele pozostały puste po walidacji.
- Cleanup bazy operatora w tym wznowieniu: nie wykonywano DELETE, bo obie tabele były już puste. Wcześniejszy raport wykazywał 6 i 4 rekordy, ale nie potwierdzał ich usunięcia; wykonawca i czas późniejszego cleanupu są nieustalone. DELETE dotyczył wyłącznie rekordów fixture w izolowanym klastrze walidacyjnym.
- Operator DB touched? YES — odczyty, alembic current/check i idempotentne alembic upgrade head. Bez downgrade na bazie operatora.
- Automatic cleanup? NO. Brak heurystycznego mapowania jednostek i usuwania plików lub schematu.

DEVIATIONS:
- Izolowany PostgreSQL wymagał uruchomienia poza sandboxem; po uzyskaniu zgody walidacja przeszła. Pierwsza próba w sandboxie nie uruchomiła serwera i usunęła wyłącznie własny tymczasowy klaster.
- Baza operatora była już zmigrowana przed czynnościami w tym wznowieniu; nie przypisuję tego upgrade do bieżącego wykonania.

NEXT:
- TASK-033 DONE; fundament słownika jest gotowy do TASK-034 po odrębnym, jawnym poleceniu. Finalnego UI wyboru jednostek nie implementowano w TASK-033.
