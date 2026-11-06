# TASK-GIT-001 — Raport kontrolowanej integracji main

**Data:** 2026-11-06
**Podstawa:** `docs/tasks/TASK-GIT-001_Controlled_Main_Integration_AUTHORIZED.md`, GOV-001, GOV-002 (LEVEL 2)
**Rekomendacja:** **READY FOR ARCHITECT REVIEW**. Integracja pozostaje lokalną propozycją. Testy Docker/Compose na stanowisku developera są otwartą kontrolą przed decyzją o pełnej zgodności obu środowisk.

## Referencje i izolacja

| Referencja | Przed | Po wykonaniu i testach |
|---|---|---|
| Oryginalny `main` / HEAD | `018fc6535503f2e9b15c664a08cf7041cef9b2b0` | bez zmiany: `018fc6535503f2e9b15c664a08cf7041cef9b2b0` |
| `origin/main` | `ce7ca7ba386ba3e56905eb427ed6d2b23786bffa` | bez zmiany: `ce7ca7ba386ba3e56905eb427ed6d2b23786bffa` |
| Wspólny przodek | `3411f6dd3f503042d9636ab32384bda49ca7da43` | 1 commit lokalny, 6 zdalnych względem przodka |
| `backup/main-before-git-integration-20261106` | nazwa wolna | `018fc6535503f2e9b15c664a08cf7041cef9b2b0` |
| `integration/main-windows-docker-20261106` | nazwa wolna | merge `93d6241eb0bb7b1975d0d7d7fc14ee787ead524c`, następnie poprawki `061117328c1d85e431e017b25b9b2d90f6e363aa` |

Aktualność zdalnego `main` potwierdzono przez `git ls-remote --heads origin main`. Oddzielny worktree: `C:\Users\bartosz.murawski\Projects\MSDS-Manager-git-integration-20261106`. Zwykły merge `--no-ff` zachował obu rodziców (`018fc65`, `ce7ca7b`); `git merge-base --is-ancestor` potwierdza obie historie w `0611173`. Nie użyto rebase ani force push. Indeks oryginalnego checkoutu pozostał pusty; jego istniejące pliki nieśledzone w `tmp/` i dokument autoryzacyjny pozostały nietknięte.

## Rozstrzygnięcia scalania i pliki

Merge nie miał konfliktów tekstowych. Sprawdzono semantykę czterech plików zmienianych po obu stronach:

| Plik | Rozstrzygnięcie |
|---|---|
| `app/application/dto/__init__.py` | Zachowano eksporty `InvalidateSdsInput` i `SdsHistoryItem`; usunięcie eksportu legacy stanowisk pozostało skuteczne. |
| `app/application/use_cases/__init__.py` | Zachowano `InvalidateSds`; usunięcie `AssignLegacyUsageLocationCode` pozostało skuteczne. |
| `app/presentation/streamlit/composition.py` | Zachowano historię SDS i `list_sds_history`, usunięto ścieżkę legacy stanowisk; dodano brakujący import `SupervisoryReadError`. |
| `app/presentation/streamlit/product_registry.py` | Zachowano widok bieżącego/wycofanego SDS i historię; pozostawiono uproszczone renderowanie `location_code` ze zmian developera. |

**Pliki zmienione przez merge względem lokalnego `main` (44):**

- Konfiguracja i dokumentacja: `.dockerignore`, `.gitignore`, `.run/MSDS Manager (Docker).run.xml`, `Dockerfile`, `README.md`, `docker-compose.test.yml`, `docker-compose.yml`.
- Kod: `app/application/dto/__init__.py`, `app/application/dto/usage_locations.py`, `app/application/exceptions.py`, `app/application/ports/usage_location_repository.py`, `app/application/use_cases/__init__.py`, `app/application/use_cases/assign_legacy_usage_location_code.py` (usunięty), `app/infrastructure/db/repositories/usage_location.py`, `app/presentation/streamlit/composition.py`, `app/presentation/streamlit/product_registry.py`.
- Testy: `tests/integration/safety_fixtures.py`, `test_core_integrity.py`, `test_patch006_sds_revision.py`, `test_patch008_delete_product.py`, `test_streamlit_shell.py`, `test_task016_acceptance.py`, `test_task023_bhp_decision.py`, `test_task025_sprint4_acceptance.py`, `test_task026_supervisory_read_model_postgresql.py`, `test_task033_unit_of_measure.py`, `test_task034_unit_integration.py`, `test_task037_bhp_evidence.py`, `test_task041_analytics_postgresql.py`, `test_task043_location_code.py`, `test_task045_legacy_code_postgresql.py` (usunięty), `tests/unit/test_orm_metadata.py`, `test_task040_current_sds_download.py`, `test_task045_stanowiska_view.py`, `test_task045_usage_location_code.py` (usunięty). Ścieżki skróconych nazw testów są w podanych katalogach.
- Dziewięć śledzonych testowych PDF pod `.pytest_tmp/` usuniętych przez zdalny commit, wyłącznie w izolowanym worktree.

**Minimalne poprawki po merge (`0611173`, 3 pliki):** `app/presentation/streamlit/composition.py` (import wyjątku), `tests/unit/test_task040_current_sds_download.py` (dubel `list_sds_history` i test mapowania wyjątku), `tests/unit/test_orm_metadata.py` (oczekiwania dla istniejącej tabeli `sds_invalidation` i jej PK). Dwa błędy ORM ujawnione w pierwszym przebiegu wynikały z oczekiwań zdalnego testu nieobejmujących lokalnej migracji TASK-060. Nie zmieniano schematu ani migracji. Pliki Docker/Compose, `.run/` i `.gitignore` są identyczne z `origin/main` (`git diff --quiet` = 0). Nie włączono `origin/chore/dependency-lock`.

## Walidacja Windows i PostgreSQL

Wszystkie poniższe testy uruchomiono w worktree przez istniejące `.venv\Scripts\python.exe` z oryginalnego repozytorium, bez Dockera:

| Kontrola | Wynik |
|---|---|
| Focused suite: `tests/unit/test_product_registry_view.py`, `test_task060_sds_invalidation_ui.py`, `test_task040_current_sds_download.py`, `test_task045_stanowiska_view.py`, `test_orm_metadata.py`, `test_task052_evidence_json_plan.py`, `tests/integration/test_task060_sds_invalidation.py` | **99 passed, 1 skipped** po poprawce ORM; początkowo 97 passed, 1 skipped, 2 failed (właśnie nieaktualne oczekiwania ORM). |
| Izolowane testy PostgreSQL `tests/integration/test_task058_review_identity.py`, `test_task059_close_reviews.py` | **6 passed**. Fixture utworzyły i usunęły bazy `task054_<uuid>`. |
| Migracja pustej, izolowanej bazy do `e4c6f21a9d80`, potem `tests/integration/test_task043_location_code.py` | **2 passed**; baza `taskgit001_<uuid>` usunięta w `finally`. Pierwsza próba samego uruchomienia skryptu miała błąd składni polecenia PowerShell/Python przed utworzeniem bazy; poprawiony runner przeszedł. |
| Ponowny focused test po dodaniu testu wyjątku: `tests/unit/test_task040_current_sds_download.py` | **15 passed, 1 skipped**. Skip dotyczy tworzenia symlinków niedostępnego w tym środowisku Windows. |
| Natywny start Streamlit na porcie 8502 i `/_stcore/health` | **HTTP 200, `ok`**; proces zatrzymano. Kontrola potwierdza start serwera, nie pełną ręczną ocenę ekranów. |
| `git diff --check HEAD^ HEAD` dla commita poprawek | **PASS**. `git diff --check main HEAD` wykazuje jedną odziedziczoną ze zdalnej gałęzi pustą linię na końcu `app/application/dto/usage_locations.py`; szersza różnica względem `origin/main` zawiera też zastane odstępy w lokalnych dokumentach i testowych PDF. Nie poprawiano ich poza zakresem. |

Ustawienia połączenia PostgreSQL odczytano tylko do procesu testów z oryginalnego `.env`; nie ujawniano sekretów. Testy pisały wyłącznie do własnych baz o losowych nazwach, nie do bazy operatora. Nie uruchamiano Docker/Compose na Windows. Testy Docker/Compose na stanowisku developera: **NOT RUN / PENDING**.

## Stan `.pytest_tmp/`

Oryginalny `git status --porcelain=v1 --untracked-files=no` przed i po pokazuje te same **9 śledzonych PDF jako ` D`**. `Test-Path` i `Get-Item` katalogu `.pytest_tmp/` potwierdzają katalog, lecz `Get-Acl` katalogu oraz `Get-Item` każdego z dziewięciu PDF zwracają `UnauthorizedAccessException`. **Fizyczna obecność PDF i przyczyna zgłoszenia ` D`: UNVERIFIED** z powodu uprawnień. Nie kasowano, nie przywracano i nie zmieniano uprawnień w oryginalnym checkoutcie. Merge odzwierciedlił usunięcia zdalnego commita tylko w osobnym worktree.

## Kryteria G1–G8

| ID | Wynik | Dowód / ograniczenie |
|---|---|---|
| G1 | **PASS z ograniczeniem** | `main` przed/po `018fc65`, backup `018fc65`, indeks pusty; stan 9 PDF nierozstrzygnięty opisano wyżej. |
| G2 | **PASS** | Oddzielny worktree i gałąź, merge `93d6241`, obie historie są przodkami `0611173`. |
| G3 | **PASS w wykonanym zakresie** | Semantyka czterech plików, testy TASK-058–060, Stage 1, historia/wycofanie SDS i stanowiska; brak refaktoryzacji. |
| G4 | **PARTIAL / PENDING DOCKER** | Natywna `.venv` + izolowany PostgreSQL i Streamlit działają bez Dockera; konfiguracja Docker identyczna z `origin/main`; kontrola developera pozostaje otwarta. |
| G5 | **PASS** | Dwa wskazane problemy naprawione; dodatkowo konieczna korekta testu ORM po ujawnieniu dwóch błędów. |
| G6 | **UNVERIFIED fizycznie** | 9 PDF ma status ` D`, dostęp blokuje `UnauthorizedAccessException`; nie wykonano działań destrukcyjnych. |
| G7 | **PASS z ograniczeniami** | Focused suites 99+6+2 passed oraz ponowny test 15 passed; 1 Windows symlink skip, brak testów Docker i pełnej historycznej regresji. |
| G8 | **PASS** | Oryginalny `main` i `origin/main` bez zmiany; bez push i bez zapisów w bazie operatora. |

## Otwarte obserwacje i STOP

Zastany `README.md` nadal odwołuje się do CORE v1.3; korekta dokumentacyjna wymaga osobnego zakresu. Uprawnienia `.pytest_tmp/` wymagają oceny właściciela środowiska, jeśli fizyczny stan PDF ma zostać rozstrzygnięty. Zgodność Docker/Compose wymaga uruchomienia testów przez developera na jego stanowisku. Nie zmieniono Core/BDR/TDR, mechanizmu SDS/BHP ani zależności. **STOP przed zmianą `main` i przed `push`; dalsza publikacja wymaga decyzji Architekta po ocenie Cerberusa.**
