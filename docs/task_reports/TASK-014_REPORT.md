# TASK-014 — raport wykonania

## 1. Status i stan wejściowy

**DONE**. Wejście: TASK-013, istniejące kontrakty Application, 4 rewizje Alembic, PostgreSQL head `d2b4f6a8c190`, 9 tabel i 0 rekordów biznesowych.

## 2. Zmienione pliki

- `app/presentation/streamlit/app.py` — podłączenie widoku Stanowiska.
- `app/presentation/streamlit/composition.py` — composition root dla odczytów i zapisów.
- `app/presentation/streamlit/product_registry.py` — administracja produktu, lokalizacji i przypisań.
- `tests/integration/test_streamlit_shell.py` — aktualizacja oczekiwań dla Stanowisk.
- `tests/unit/test_product_registry_view.py` — test prezentacji i identyfikacji po `product_id`.
- `pyproject.toml` — zapisywalny `basetemp` i wyłączenie niedostępnego cache pytest z TASK-013.

## 3. Zakres funkcjonalny

- Cztery pola administracyjne produktu są edytowalne przez `UpdateProductAdministrativeData`; po zapisie następuje ponowny `GetProductDetails`.
- `product_name`, kod producenta, producent i `usage_status` pozostają read-only. Nie ma CreateProduct, CreateManufacturer ani SetProductStatus.
- Stanowiska pokazują ACTIVE i INACTIVE, umożliwiają `CreateUsageLocation`, `DeactivateUsageLocation` i `ReactivateUsageLocation`; reaktywacja używa tego samego `location_id`.
- Przypisanie korzysta z `AssignProductUsageLocation` i oferuje wyłącznie nieprzypisane lokalizacje ACTIVE. Brak operacji remove/delete.
- Ilości są edytowane przez `UpdateProductUsageLocation`. UI parsuje wartości do `Decimal`, zachowuje `0` kontra `None`, wymaga jednostek i nie konwertuje ich.

## 4. Transakcje i błędy

Każdy zapis przechodzi przez `TransactionExecutor`. UI nie wykonuje SQL, `commit()` ani `rollback()`. Błędy Application/Domain i persistence są ograniczane do krótkiego komunikatu bez SQL, tracebacku, sekretów i pełnego `DATABASE_URL`.

## 5. Testy i walidacja

- Pełny pytest: **96 passed**.
- `-W error::sqlalchemy.exc.SAWarning`: brak `SAWarning`.
- Testy Streamlit i widoku: **5 passed**.
- Granice architektury: **3 passed**.
- Manualny odpowiednik smoke przez Streamlit AppTest: start, Produkty empty state, Stanowiska i brak danych po testach potwierdzone. Nie dodawano trwałego seeda.

## 6. PostgreSQL / schema

- `alembic current`: `d2b4f6a8c190 (head)`.
- `alembic check`: `No new upgrade operations detected`.
- Tabele aplikacyjne: **9**.
- Rekordy biznesowe po testach: **0**.
- Brak migracji #5 i zmian Domain, Application contracts, ORM, constraints oraz schema.

## 7. Git i bezpieczeństwo

`git diff --check` i `git diff --cached --check` bez błędów. Nie wykonano commit/push. Nie dodano bibliotek, dumpów, backupów, PDF, MSG ani sekretów.

## 8. Odstępstwa i ryzyka

Brak blockerów. Wąski interfejs korzysta ze zwykłych kontrolek Streamlit zamiast formularzy, aby uniknąć błędu zagnieżdżonych formularzy podczas rerunów AppTest. Nie zmienia to granicy transakcji ani kontraktów Application.

## 9. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-015 ANI TASK-016.