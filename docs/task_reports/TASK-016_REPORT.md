# TASK-016 — Sprint 2 End-to-End Acceptance

## 1. Status

DONE — acceptance scenariusza Sprintu 2 zakończony pozytywnie.

Rekomendacja: `READY FOR SPRINT-002 CLOSURE`.

Raport nie podejmuje formalnej decyzji o zamknięciu Sprintu. Nie rozpoczęto R4 ani workflow SDS.

## 2. Zakres zmian

TASK-016 nie wymagał zmian produkcyjnych, Core, BDR, TDR, schematu ani zależności.

Dodano wyłącznie:

- `tests/integration/test_task016_acceptance.py` — kontrolowany test acceptance z AppTest, istniejącym composition root, Application/use case'ami, PostgreSQL, historią i cleanupem.
- `docs/task_reports/TASK-016_REPORT.md` — niniejszy raport.

Zmiany produkcyjne TASK-015 pozostają wcześniejszym stanem roboczym repozytorium i nie zostały odwrócone.

## 3. Baseline

Wykonano przed testem acceptance:

- `git status --short` — repozytorium zawiera niezatwierdzone zmiany z TASK-015; brak zmian TASK-016 przed dodaniem testu.
- `alembic current` — `e0dd7d6468bf (head)`.
- `alembic check` — `No new upgrade operations detected.`
- pełny pytest z `SAWarning` jako error — `99 passed`.
- `git diff --check` i `git diff --cached --check` — brak błędów diffu; występują wyłącznie ostrzeżenia Git o konwersji LF/CRLF.

Walidacja wymagała aktywnego środowiska Windows:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
```

## 4. Fixture E2E

Test tworzy technicznie:

- jednego MANUFACTURER,
- jednego PRODUCT,
- dwie USAGE_LOCATION,
- przypisania i snapshoty historii.

Identyfikatory mają prefiks `task016-` i są generowane z losowym sufiksem. PRODUCT/MANUFACTURER nie są tworzone przez publiczny workflow użytkownika, nie ma publicznego `CreateProduct` ani `CreateManufacturer`, trwałego seeda ani przycisku UI.

Cleanup usuwa wyłącznie fixture TASK-016, w kolejności zgodnej z FK: historie, relacje, lokalizacje, produkt i producent.

Końcowy stan PostgreSQL:

- `task016_fixture_rows=0`,
- `manufacturers=0`,
- `products=0`,
- `usage_locations=0`,
- `product_history=0`,
- `usage_location_history=0`,
- `product_usage_location_history=0`.

## 5. Przebieg E2E

Test `test_task016_sprint2_end_to_end_acceptance` wykonuje:

1. Seed techniczny MANUFACTURER/PRODUCT.
2. Start rzeczywistego Streamlit przez `AppTest.from_file(...)`.
3. Potwierdzenie braku wyjątków, widoku `Produkty`, produktu na liście i danych szczegółowych.
4. Odczyt przez `build_shell_composition()` oraz istniejący `GetProductDetails`.
5. Edycję `use_description`, `use_restriction`, `waste_type` i `waste_code` przez `ShellComposition.update_product_administrative_data`.
6. Utworzenie dwóch lokalizacji przez istniejący `CreateUsageLocation` w kontrolowanym fixture.
7. Przypisanie produktu do obu lokalizacji.
8. Weryfikację `peak=0`, `monthly=NULL`, `monthly=0`, Decimal i braku konwersji jednostek.
9. Aktualizację ilości pierwszej lokalizacji.
10. Dezaktywację drugiej lokalizacji.
11. Potwierdzenie odrzucenia nowego przypisania do lokalizacji INACTIVE.
12. Reaktywację tej samej lokalizacji po tym samym `location_id`.
13. Odczyt current state i trzech obszarów historii z PostgreSQL.
14. Cleanup w `finally`.

Wszystkie operacje zapisu przechodzą przez istniejący `TransactionExecutor`. Test nie wykonuje SQL, commit ani rollback z poziomu Streamlit view.

## 6. Dowód Streamlit → Application → PostgreSQL

- Streamlit uruchomiono przez `AppTest` z rzeczywistym `app.py` i konfiguracją PostgreSQL.
- Composition root pobiera dane przez `ListProducts` i `GetProductDetails`.
- Operacje zapisu w composition root delegują do Application use case'ów.
- Use case'y korzystają z portów/repozytoriów infrastruktury.
- Transakcje wykonuje `TransactionExecutor`.
- Stan końcowy oraz snapshoty potwierdzono bezpośrednio przez SQLAlchemy repositories i modele PostgreSQL.

## 7. Historia

Potwierdzono na rzeczywistym PostgreSQL:

- `PRODUCT_HISTORY` — jeden snapshot po zmianie danych administracyjnych, z nowymi wartościami odpadowymi i zachowanym `usage_status`.
- `USAGE_LOCATION_HISTORY` — `INACTIVE`, następnie `ACTIVE` dla tego samego `location_id`.
- `PRODUCT_USAGE_LOCATION_HISTORY` — initial snapshot `peak=0`, `monthly=NULL` oraz kolejny snapshot `peak=3.25`, `monthly=0`.
- wcześniejszy snapshot nie został nadpisany,
- kolejność jest deterministyczna przez `changed_at`, a następnie `history_id`.

## 8. Wyniki walidacji

Test acceptance:

```text
1 passed in 6.81s
```

Pełna regresja po dodaniu testu:

```text
100 passed in 3.80s
```

Komenda regresji:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Brak `SAWarning`.

## 9. Alembic i schema

- `alembic current` — `e0dd7d6468bf (head)`.
- `alembic check` — `No new upgrade operations detected.`
- rewizje — brak nowej rewizji TASK-016; nadal head `e0dd7d6468bf`.
- tabele biznesowe — `12` (9 Core + 3 history).
- drift — brak.
- dane fixture po teście — brak.

## 10. Architektura

PASS:

- presentation korzysta z Application przez composition root,
- Application korzysta z portów,
- Infrastructure implementuje porty i obsługuje SQLAlchemy/PostgreSQL,
- Streamlit view nie zawiera ORM, SQL, commit ani rollback,
- Domain nie importuje Infrastructure ani SQLAlchemy,
- Application nie importuje Infrastructure,
- repozytoria nie wykonują commit/rollback per method,
- brak publicznego `CreateProduct` i `CreateManufacturer`,
- brak nowego frameworku historii, audytu, statusu, migracji i zależności.

Kontrola importów wskazała importy infrastruktury w `presentation/streamlit/composition.py`, który jest istniejącym composition root i właściwym miejscem ich podłączenia. Widoki `app.py` i `product_registry.py` nie importują SQLAlchemy ani repozytoriów.

## 11. DoD Sprintu 2

| # | Kryterium | Status |
|---:|---|---|
| 1 | Lista istniejących produktów | PASS |
| 2 | Szczegóły produktu | PASS |
| 3 | Producent | PASS |
| 4 | Ochrona tożsamości | PASS |
| 5 | Edycja danych administracyjnych | PASS |
| 6 | `waste_type` / `waste_code` | PASS |
| 7 | Osobny słownik stanowisk | PASS |
| 8 | Dodawanie / dezaktywacja stanowiska | PASS |
| 9 | Przypisanie produktu do wielu stanowisk | PASS |
| 10 | `peak_quantity >= 0` | PASS |
| 11 | Opcjonalne `monthly_consumption >= 0` | PASS |
| 12 | Semantyka `0` / `NULL` | PASS |
| 13 | UI nie omija Application | PASS |
| 14 | PostgreSQL jako źródło operacyjne | PASS |
| 15 | Historia istotnych zmian | PASS |
| 16 | Testy przechodzą | PASS |
| 17 | E2E na kontrolowanych danych | PASS |
| 18 | Brak publicznego `CreateProduct` / `CreateManufacturer` | PASS |
| 19 | Nie rozpoczęto SDS / BHP / AI / REACH | PASS |

## 12. Git i bezpieczeństwo

- `git status --short` — repozytorium pozostaje niezatwierdzone zgodnie ze stanem TASK-015; nie wykonano commit ani push.
- Nie odwracano cudzych ani wcześniejszych zmian.
- `git diff --check` — brak błędów treściowych.
- Nie zmieniono `pyproject.toml` ani listy zależności.
- Nie znaleziono śledzonych `.env`, dumpów, backupów, PDF ani MSG.
- Nie dodano sekretów ani pełnego `DATABASE_URL` do kodu/testu.
- Brak trwałego seeda; finalne tabele są puste.

## 13. Odstępstwa i ryzyka

- W TASK-016 wskazano źródło `BDR-002 v1.2-approved`, ale taki plik nie występuje w repozytorium. Nie stwierdzono jednak konfliktu decyzji ani potrzeby nowej decyzji; zakres został zweryfikowany względem dostępnych zatwierdzonych źródeł i istniejącej implementacji.
- Test automatyczny uruchamia rzeczywisty Streamlit AppTest i composition root, natomiast operacje zapisu są wywoływane przez istniejącą warstwę composition/application w teście, co jest równoważnym scenariuszem dopuszczonym przez TASK-016. Nie dodano interaktywnego workflow tworzenia PRODUCT.
- Repozytorium zawiera wcześniejsze, niezatwierdzone zmiany TASK-015; nie są one zmianami wprowadzonymi przez TASK-016.

## 14. Rekomendacja

`READY FOR SPRINT-002 CLOSURE`

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM R4 ANI WORKFLOW SDS.
