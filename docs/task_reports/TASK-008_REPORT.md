# TASK-008 REPORT

## 1. Status

DONE

Implementacja Domain, ORM i PostgreSQL została wyrównana do
`CORE-001 v1.1-approved`. Utworzono dokładnie jedną trzecią rewizję Alembic,
przetestowano upgrade, downgrade i re-upgrade, a końcowy schemat nie wykazuje
driftu względem metadanych ORM.

## 2. Stan wejściowy

Przed zmianami potwierdzono:

- PostgreSQL `msds_manager` dostępny,
- bieżąca rewizja `bae33dc76391 (head)`,
- 2 rewizje Alembic,
- 9 tabel aplikacyjnych,
- 0 rekordów biznesowych (jedyny rekord techniczny znajdował się w
  `alembic_version`),
- 18 enumowych CHECK constraints,
- brak driftu ORM ↔ DB (`No new upgrade operations detected.`),
- pełna regresja: 47 passed, brak `SAWarning`.

Trzy dokumenty wejściowe Core/Sprint/Task były nieśledzone już na wejściu.
Pozostawiono je bez modyfikacji.

## 3. Zmiany Domain

`Product` otrzymał opcjonalne pola:

- `waste_type: str | None = None`,
- `waste_code: str | None = None`.

Nie zmieniono tożsamości PRODUCT ani statusów.

`ProductUsageLocation` zawiera obecnie:

- wymagane `peak_quantity_value: Decimal`,
- wymagane `peak_quantity_unit: str`,
- opcjonalne `monthly_consumption_value: Decimal | None`,
- opcjonalne `monthly_consumption_unit: str | None`.

Walidacja domenowa odrzuca ujemny peak, ujemne monthly oraz niespójną parę
monthly value/unit. Zachowano odrębną semantykę `None` i `Decimal("0")`.
Stare pola `quantity_value` / `quantity_unit` nie występują w aktualnym modelu
domenowym.

## 4. Zmiany ORM

`products` otrzymało nullable `waste_type` i `waste_code`.

`product_usage_locations` reprezentuje:

```text
peak_quantity_value       NUMERIC NOT NULL
peak_quantity_unit        VARCHAR NOT NULL
monthly_consumption_value NUMERIC NULL
monthly_consumption_unit  VARCHAR NULL
```

Nie użyto `Float`. Nie dodano tabel, FK, UNIQUE ani indeksów poza zakresem.
Nie zmieniono modeli SDS/BHP/SafetyProfile/SdsComponent ani enumów.

## 5. Migracja Alembic

- revision id: `c41d8e2f7a90`,
- nazwa: `align_core_v1_1_product_usage`,
- plik: `migrations/versions/c41d8e2f7a90_align_core_v1_1_product_usage.py`,
- `down_revision = "bae33dc76391"`,
- liczba rewizji po Tasku: dokładnie 3.

Upgrade:

- dodaje nullable `products.waste_type` i `products.waste_code`,
- wykonuje rename `quantity_value → peak_quantity_value`,
- wykonuje rename `quantity_unit → peak_quantity_unit`,
- dodaje dwa nullable pola monthly,
- dodaje trzy zatwierdzone CHECK constraints.

Downgrade odwraca powyższe operacje, w tym przywraca stare nazwy przez rename.
Nie zastosowano destrukcyjnego DROP + ADD dla dotychczasowych danych ilościowych.

## 6. Review migracji przed upgrade

Migrację odczytano i zweryfikowano przed pierwszym `upgrade head`.
Potwierdzono, że obejmuje wyłącznie dozwolone kolumny, rename i CHECK-i.
Nie zawiera zmian tabel, seed data, enumów, SDS/BHP ani constraints TASK-006.
Nie stwierdzono nieoczekiwanego driftu.

## 7. Nowe CHECK constraints

- `ck_product_usage_locations_peak_quantity_nonnegative` — wymusza
  `peak_quantity_value >= 0`,
- `ck_product_usage_locations_monthly_consumption_nonnegative` — dopuszcza
  NULL, a podaną wartość wymusza jako `>= 0`,
- `ck_product_usage_locations_monthly_consumption_pair` — wymusza jednoczesne
  NULL/NULL albo jednoczesne NOT NULL/NOT NULL dla monthly value/unit.

## 8. Ochrona constraints TASK-006

Po upgrade, downgrade i re-upgrade potwierdzono obecność i działanie:

- `uq_sds_documents_one_current_per_product`,
- `uq_bhp_decisions_one_current_per_sds`,
- `uq_sds_documents_sds_product`,
- `fk_bhp_decisions_sds_product`.

Ich nazwy i semantyka nie zostały zmienione.

## 9. Enumowe CHECK constraints

Potwierdzono 18/18 istniejących type-bound enumowych CHECK constraints zarówno
przed zmianą, po downgrade, jak i w finalnym schemacie. Filtr Alembic z TASK-006
nie został poszerzony ani zmieniony.

## 10. Testy Domain

Dodano lub zaktualizowano testy dla:

- domyślnych `waste_type=None`, `waste_code=None`,
- tekstowych wartości pól odpadowych,
- peak `0`,
- odrzucenia ujemnego peak,
- monthly `None/None`,
- monthly `0 + unit`,
- monthly dodatniego z jednostką,
- odrzucenia ujemnego monthly,
- odrzucenia monthly value bez unit,
- odrzucenia monthly unit bez value,
- różnych jednostek peak i monthly.

## 11. Testy PostgreSQL

Na rzeczywistym PostgreSQL test integracyjny potwierdził:

- peak `0` — dozwolone,
- peak `< 0` — odrzucone przez nazwany CHECK,
- monthly `NULL/NULL` — dozwolone,
- monthly `0 + unit` — dozwolone,
- monthly `< 0` — odrzucone przez nazwany CHECK,
- monthly value bez unit — odrzucone przez CHECK pary,
- monthly unit bez value — odrzucone przez CHECK pary.

Test działa w kontrolowanej transakcji i nie pozostawia danych.

## 12. Test agregacji

Reguła `sum_product_quantity` korzysta wyłącznie z pól peak. Testy potwierdzają:

- sumowanie zgodnych peak units bez utraty precyzji Decimal,
- poprawny wynik dla peak `0`,
- odrzucenie mixed peak units istniejącym `MixedQuantityUnitsError`,
- brak konwersji jednostek,
- brak wpływu monthly consumption na wynik, także gdy monthly ma inną jednostkę.

Reguły nie rozszerzono o pobieranie aktywnych lokalizacji z bazy.

## 13. Pełna regresja i SAWarning

Końcowe polecenie:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **59 passed**, kod wyjścia 0, brak `SAWarning`.

Zestaw obejmuje 5 testów integracyjnych PostgreSQL i 54 testy jednostkowe oraz
architektoniczne.

## 14. Upgrade / downgrade / re-upgrade

Przebieg zakończony powodzeniem:

```text
bae33dc76391
→ upgrade
c41d8e2f7a90 (head)
→ downgrade -1
bae33dc76391
→ upgrade head
c41d8e2f7a90 (head)
```

Po downgrade potwierdzono 9 tabel, stare `quantity_value` / `quantity_unit`,
brak pól waste/monthly, 18 enum CHECK-ów, constraints TASK-006 i 0 rekordów
biznesowych.

## 15. Finalny stan PostgreSQL

- database: `msds_manager`,
- current revision: `c41d8e2f7a90 (head)`,
- rewizje Alembic: 3,
- tabele aplikacyjne: 9,
- kolumny usage: 6 zatwierdzonych kolumn Core v1.1,
- stare nazwy `quantity_value` / `quantity_unit`: nieobecne,
- pola waste: obecne i nullable,
- enum CHECK: 18,
- nowe quantity CHECK: 3,
- rekordy biznesowe: 0.

## 16. Drift ORM ↔ DB

Po finalnym re-upgrade wykonano `alembic check`.

Wynik:

```text
No new upgrade operations detected.
```

Rzeczywisty drift nie występuje.

## 17. Granice architektury

Zachowano kierunki zależności. Domain nie importuje persistence ani
frameworków. ORM pozostaje w `app/infrastructure/db/models/`, a migracja w
`migrations/versions/`. Nie dodano use case'ów, portów, repozytoriów, UI,
historii, workflow, modułu odpadowego, konwersji jednostek ani bibliotek.
`ListManufacturers` i `ManufacturerRepositoryPort` nie zostały zmienione.

## 18. Git i bezpieczeństwo

- commit/push: NIE,
- `git diff --check`: kod 0,
- `git diff --cached --check`: kod 0,
- `.env` ignored i nietrackowany: TAK,
- `.env` nie został odczytany ani ujawniony w raporcie: TAK,
- nowe zależności / zmiana `pyproject.toml`: NIE,
- dumpy/backupy: BRAK,
- pliki SDS/BHP i obrazy danych: BRAK,
- seed data / lokalne dane testowe: BRAK,
- finalna liczba rekordów biznesowych: 0.

Git zgłasza wyłącznie informacyjne ostrzeżenia o przyszłej normalizacji LF do
CRLF; kontrole whitespace zakończyły się kodem 0.

## 19. Odstępstwa

BRAK.

## 20. Problemy, ryzyka i przyszłe decyzje

- Testy integracyjne wymagają działającego lokalnego PostgreSQL 17 i poprawnej
  konfiguracji `.env`.
- Szczegółowy mechanizm historii PRODUCT–USAGE_LOCATION nadal wymaga osobnej
  zatwierdzonej decyzji; zgodnie z granicą Tasku nie został zaprojektowany.
- Lista/konwersja jednostek oraz rozwinięcie pól odpadowych pozostają poza
  zakresem i nie zostały zaimplementowane.

Brak blokerów dla przeglądu TASK-008.

## 21. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-009.
