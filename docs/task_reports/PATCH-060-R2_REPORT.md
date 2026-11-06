# PATCH-060-R2 — raport kontrolowanej migracji bazy operatora

**Data:** 2026-11-03

**Wynik techniczny:** **PASS**. Odbiór fizyczny GUI przez operatora pozostaje **PENDING**.
**Podstawa:** `docs/tasks/PATCH-060-R2_Operator_DB_Migration_AUTHORIZED.md`.

## Cel i preflight

Pracowano w repozytorium `C:\Users\bartosz.murawski\Projects\MSDS-Manager`. Lokalny `.env` jest źródłem konfiguracji; efektywna konfiguracja wskazuje PostgreSQL `localhost:5432`, bazę **`msds_manager`**. Nie ujawniano poświadczeń ani connection stringa. W chwili preflight port aplikacji `8501` nie nasłuchiwał. Tożsamość celu potwierdzono dodatkowo przez dokładnie ten sam produkt i SDS, dla których PATCH-060-R1 odtworzył `UndefinedTable`: `SYLGARD 160 Silicone Elastomer-Part A`, `product_id=8385e28101e6409c8110d33febbfdc86`, bieżący SDS `760c7058df7e4bb58337fc6501a1da51`, rewizja `5.0`.

`alembic heads`: jeden head `e4c6f21a9d80`. `alembic current` i `alembic_version` przed migracją: `b7d4a1f03962`. W bazie nie było `sds_invalidation`; kolumna `sds_documents.document_status` miała długość 8 i CHECK dopuszczający `CURRENT`/`ARCHIVED`. Istniał częściowy unikalny indeks `uq_sds_documents_one_current_per_product`. Nie stwierdzono osieroconych SDS ani produktów z więcej niż jednym `CURRENT`. `pg_stat_activity` nie wykazał innych sesji w bazie, nie było cudzych blokad doradczych; port `8501` był wyłączony. Nie zatrzymywano innych usług. Bezpośrednio przed upgrade powtórzono kontrolę: właściwa baza, ta sama rewizja i liczniki, brak innych sesji.

## Backup i próbne odtworzenie — bramka przed migracją

Pełny backup utworzono `pg_dump -Fc` narzędziem PostgreSQL 17.11, z poświadczeniem przekazanym wyłącznie przez środowisko procesu. Archiwum znajduje się **poza repozytorium Git** i poza katalogiem tymczasowym:

`C:\Users\bartosz.murawski\Projects\MSDS-Manager-backups\msds_manager_patch060_r2_20261103T135733Z_4e4876be.dump`

| Kontrola | Wynik |
|---|---|
| Czas utworzenia | 2026-11-03 13:57:34 UTC |
| `pg_dump` | Exit 0; plik ma 56 634 bajty |
| SHA-256 | `30b2d7190b2e3fbcc2eb06bf9b901272c01108c6388ab4feace3f7447766a6f3` |
| `pg_restore --list` | Exit 0; 88 wpisów archiwum, w tym `products`, `sds_documents`, `bhp_decisions`, `decision_evidence` |
| Ponowny SHA-256 przed restore | Zgodny |
| Próbne odtworzenie | `createdb` i `pg_restore --exit-on-error --single-transaction`: oba exit 0, do nowej bazy `msds_patch060_r2_restore_7ab529178818` |
| Kontrola odtworzonej bazy | 17 tabel z `alembic_version`, rewizja `b7d4a1f03962`, **wszystkie** liczniki istniejących tabel zgodne z bazą źródłową, w tym `PRODUCT=36`, `SDS=38`; wskazany bieżący SDS zgodny |

Testowa baza odtworzeniowa pozostaje odizolowana i została zachowana jako dowód. Nie odtwarzano backupu do bazy operatora. Migrację rozpoczęto dopiero po pozytywnym wyniku odtworzenia.

## Migracja i liczniki

Wykonano wyłącznie standardową komendę projektu:

```powershell
.\.venv\Scripts\alembic.exe upgrade e4c6f21a9d80
```

Exit 0; log Alembic: `Running upgrade b7d4a1f03962 -> e4c6f21a9d80`. Nie wykonywano `stamp`, `downgrade`, ręcznego DDL ani innej migracji.

| Tabela | Przed | Po |
|---|---:|---:|
| `manufacturers` | 6 | 6 |
| `products` | 36 | 36 |
| `sds_documents` | 38 | 38 |
| `product_history` | 42 | 42 |
| `bhp_decisions` | 4 | 4 |
| `safety_profiles` | 7 | 7 |
| `sds_components` | 6 | 6 |
| `decision_evidence` | 4 | 4 |
| `physical_reviews` | 2 | 2 |
| `physical_review_items` | 3 | 3 |
| `product_identity_changes` | 2 | 2 |
| `product_usage_locations` | 2 | 2 |
| `product_usage_location_history` | 3 | 3 |
| `usage_locations` | 3 | 3 |
| `usage_location_history` | 0 | 0 |
| `unit_of_measure` | 5 | 5 |
| `sds_invalidation` | brak tabeli | 0 |

## Postcheck read-only

`alembic current` i bezpośredni odczyt `alembic_version` wskazują `e4c6f21a9d80 (head)`. Tabela `sds_invalidation` istnieje i jest pusta; żaden SDS nie ma statusu `INVALIDATED`. `document_status` ma długość 11 i CHECK obejmuje `INVALIDATED`; częściowy indeks unikalności jednego `CURRENT` ma identyczną definicję jak przed migracją. Wszystkie istniejące liczniki są niezmienione, nie ma osieroconych SDS, duplikatów `CURRENT` ani niewalidowanych constraints.

Odczyt `ShellComposition.list_sds_history` dla wskazanego produktu przeszedł **bez wyjątku** i zwrócił jeden SDS `CURRENT`, rewizja `5.0`, ten sam identyfikator i metadane co przed migracją. Ścieżka PDF mieści się w skonfigurowanym katalogu SDS; plik istnieje i ma 761 136 bajtów. Nie otwierano go w GUI ani nie zmieniano. Po uruchomieniu aplikacji ponowiono postcheck z tym samym wynikiem.

Aplikację uruchomiono według istniejącego entry pointu `app/presentation/streamlit/main.py`, na `127.0.0.1:8501`, z konfiguracją bieżącego repozytorium. Health endpoint i strona główna zwróciły HTTP 200. Adres dla operatora: [http://127.0.0.1:8501](http://127.0.0.1:8501). Do oględzin: **Produkty → SYLGARD 160 Silicone Elastomer-Part A → karta → historia SDS → otwarcie PDF → obecność akcji „Wycofaj błędnie zarejestrowany SDS”**. Nie należy zatwierdzać wycofania rzeczywistego SDS podczas tej kontroli.

## Granice i wynik

Nie zmieniono kodu aplikacji ani Core/BDR/TDR. Nie wykonano zapisów danych biznesowych, nie wycofano SDS i nie zmieniono plików PDF ani mechanizmu BHP. Zmiany w bazie operatora ograniczyły się do zatwierdzonej migracji schematu i wpisu `alembic_version`. Dodano wyłącznie ten raport oraz tymczasowe skrypty i wyniki diagnostyczne w `tmp/`; zastane zmiany repozytorium pozostawiono bez ingerencji.

**PATCH-060-R2: PASS technicznie.** Fizyczne potwierdzenie przez operatora widoku karty, historii, otwarcia PDF i akcji pozostaje niezweryfikowane; nie deklaruje się zamknięcia odbioru TASK-060. **STOP po raporcie.**
