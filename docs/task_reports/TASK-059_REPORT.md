# TASK-059 REPORT — domknięcie P012 i P037 w BATCH-001_CX

**STATUS: DONE.** `Remaining REVIEW = 0`. Wykonano jedną kontrolowaną korektę PRODUCT P037; P012 i historyczny PDF P037 nie spowodowały zapisu PRODUCT/SDS/PDF.

## Preflight i decyzje

| Pozycja | Potwierdzony stan wejściowy | Zatwierdzona decyzja | Wynik |
|---|---|---|---|
| B001-P012 | Evidence JSON `B001-P012_DOC-001.json`: `CLEANER PROF`; istniejący `Cleaner prof` `ba2c9debc0c04ab3899ae1ce1f059e7f` pod `CX80 Polska`; SDS `f7eb70cce36b49c7a83bfe12f8c0a8b7` `CURRENT`, `2023-01-23 / 2.0`. SHA manifestu = JSON = źródłowego PDF = PDF istniejącego SDS: `a1fbc73a93bdf2681f86f155f2d4be206c2bd9d8fba53569fcbaac395d677203`. Brak nowego P012 PRODUCT/SDS po TASK-058. | Jawny human-approved LINK do tego PRODUCT tylko dla P012. | `SKIP_EXACT_EXISTING`; 0 nowych PRODUCT/SDS/PDF; 0 business writes P012. |
| B001-P037 | Evidence JSON `B001-P037_DOC-001.json`: `XBRAKE CLEANER`, `2023-01-24 / 3.0`; SHA manifestu = JSON = PDF źródłowego: `9a55d855164ba2a0fd222473cd44831ac8acc1ede75c3002b10cfa3825b94556`. PRODUCT `833c0080c0a34bd1a40f5b2be18b82a6` miał nazwę `XBRAKE CLEANER`, kod `CX80 XBRAKE CLEANER`, producenta `Cx80`, trzy wcześniejsze SDS i dokładnie jeden `CURRENT` z `2026-09-01`. Żaden istniejący SDS nie miał SHA źródła P037. | Korekta wyłącznie producenta do `CX80 Polska` z audytem `CORRECTION`; źródło historyczne pominąć. | Korekta wykonana; `SKIP_HISTORICAL_SOURCE`; 0 nowych SDS/PDF. |

Fizyczne nazwy obu źródeł odczytano z manifestu, a ich bajty ponownie zahashowano. Dla P012 identyczność PDF potwierdzono względem pliku wskazanego przez `SDS.relative_path`; podobna nazwa bez identycznego PDF jest blokowana przez preflight. Decyzje human-approved zapisano w `BATCH-001_STAGE1_TASK059_DECISIONS.json`; nie utworzono globalnej reguły case-insensitive ani mechanizmu rejestracji historycznego SDS jako `ARCHIVED`.

## Operator writes i stan po transakcji

Jedyny zapis danych biznesowych TASK-059: `UPDATE products.manufacturer_id` dla PRODUCT P037 z `a635199aa44944bbbf31cb63808f58d3` (`Cx80`) na `a11c4d78f64b41f89de6ec0196a9254b` (`CX80 Polska`) oraz jeden `PRODUCT_IDENTITY_CHANGE` `870dd7471743493393174e47a0d5f638`, `change_kind=CORRECTION`, w tej samej transakcji. Audit zachowuje równe stare/nowe: nazwę `XBRAKE CLEANER` i kod `CX80 XBRAKE CLEANER`. Preflight wykonano ponownie po blokadzie tabel przed wywołaniem istniejącego `CorrectProductIdentity`; błąd audytu powoduje rollback korekty.

| P037 SDS | Przed | Po |
|---|---|---|
| `3da9cedfc58a47158694746b015bbaf2` (`2026-09-01`) | `CURRENT` | `CURRENT` |
| `3e8346e132bf4bb69016fc5524434472` | `ARCHIVED` | `ARCHIVED` |
| `ecba2904093f40bf96e2762b6a9ebf09` | `ARCHIVED` | `ARCHIVED` |

Operator DB po TASK-059: 5 MANUFACTURER, 35 PRODUCT, 37 SDS, 41 PRODUCT_HISTORY, 2 PRODUCT_IDENTITY_CHANGE (P023 z TASK-058 i P037 z TASK-059). W TASK-059: **0 nowych MANUFACTURER, PRODUCT, SDS, PDF, SAFETY_PROFILE, SDS_COMPONENT, BHP_DECISION**. Źródłowy PDF P037 pozostał w katalogu batcha; nie powstała kopia w `imported/`.

## Końcowy bilans BATCH-001_CX

| Rozłączna kategoria | Liczba | Pozycje |
|---|---:|---|
| Registered/imported w batchu | 30 | 22 TASK-057 + 8 TASK-058 |
| Exact existing/skipped | 3 | P001, P012, P023 |
| Duplicate source | 1 | P015 |
| Historical source skipped | 1 | P037 |
| **Logical SDS** | **35** | 30 + 3 + 1 + 1 |
| Excluded non-SDS | 2 | P032, P033 |
| **Pliki manifestu** | **37** | 35 + 2 |
| **Remaining REVIEW** | **0** | — |

## Walidacja

- Izolowany PostgreSQL i tymczasowy SDS root: exact P012 LINK/SKIP, brak LINK przy innym PDF, P037 correction-only i pojedynczy audit, rollback po wstrzykniętym błędzie audytu, idempotencja, niezmieniony SDS/PDF/lifecycle i 0 nowych Safety/Components/BHP/Manufacturer: **2 passed**.
- Powiązana regresja TASK-058 + TASK-059: **6 passed**. Pierwsze wywołanie pytest trafiło na niedostępny stary `.pytest_tmp`; ponowiono z izolowanym `--basetemp` i testy przeszły.
- Operatorowy read-only postcheck: PRODUCT P037 ma nowego producenta i zachowane nazwę/kod; dokładnie jeden nowy audit P037; trzy SDS P037 niezmienione, jeden `CURRENT` z `2026-09-01`; P012 nadal ma jeden wcześniejszy SDS i nie powstał nowy PRODUCT/PDF.
- `SDS_ROOT_PATH`: 175 PDF łącznie, 33/33 PDF w `imported/` mają referencję DB, 0 nowych plików i 0 orphan PDF przypisywalnych TASK-059. Starsze 139 plików bez referencji oraz wcześniejsza wspólna ścieżka dwóch archiwalnych SDS pozostają opisane w raporcie TASK-058-AUDIT.
- Alembic `current`: `b7d4a1f03962 (head)`; `heads`: pojedynczy `b7d4a1f03962 (head)`; `check`: `No new upgrade operations detected.` Nie zmieniono schema ani migracji.
- `git diff --check` dla zmian Tasku: PASS (bez błędów whitespace); nie zmieniono Core ani zależności.

## Odstępstwa i ryzyka

P037 PDF z 2023 r. jest świadomie pominiętym historycznym źródłem; jego SHA i decyzja są utrwalone w batchu. Starsze pliki bez referencji i podwójna referencja archiwalna nie powstały w TASK-059 i nie były naprawiane. Nie uruchomiono Paczki2 ani Stage 2.

**STOP po BATCH-001_CX. Oczekuję na jawne polecenie kolejnego Tasku.**
