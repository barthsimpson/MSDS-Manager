# TASK-058 REPORT — BATCH-001_CX Review Identity

## Status

**DONE z dwoma wyjątkami REVIEW.** Pełny read-only preflight 11 pozycji zakończył się PASS bez `BLOCKED_SOURCE` i `BLOCKED_DATA`. Wykonano 8 kontrolowanych Stage 1 CREATE oraz korektę istniejącego PRODUCT P023. P012 i P037 pozostały bez zapisu z konkretnym powodem. **STOP po BATCH-001_CX.**

## Wynik 11 pozycji

| Manifest | Poprzednio | Zatwierdzona decyzja | Wynik | product_id / sds_id |
|---|---|---|---|---|
| B001-P005 | REVIEW_IDENTITY | M1 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `5a3712d5c76249d9b8e3d89c99a1ddc5` / `607a5a70214f44ea9998ab6bfca772a5` |
| B001-P008 | REVIEW_IDENTITY | M2 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `21fad0631ef44cf9a8cf2beff32bcdb8` / `57a5bf2c635742249e3e4a87cc78fdad` |
| B001-P011 | REVIEW_IDENTITY | M3 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `62612d215f4648cfa23df5fd1cfe9c20` / `dcbfd55af29b485ea1d74368767c1972` |
| B001-P012 | REVIEW_IDENTITY | M3 → `CX80 Polska`; produkt `CLEANER PROF` nie ma zatwierdzonego LINK do `Cleaner prof` | REVIEW_IDENTITY, bez zapisu: wariant wielkości liter i ten sam PDF nie uprawniają do automatycznego połączenia | — |
| B001-P014 | REVIEW_IDENTITY | M1 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `c4295622539748a988ab2a8c60490253` / `0df8111fce2c4006a70f9c3b5e35fcac` |
| B001-P023 | REVIEW_IDENTITY | Istniejący PRODUCT, zachowaj nazwę i kod; istniejący SDS ma exact datę, rewizję i SHA | CORRECTION ONLY; bez nowego SDS/PDF | `e8d4fa16679240adb1bf094578367f05` / `ba4ecda7d9d1479782acbb84bd5ccf48` |
| B001-P025 | REVIEW_IDENTITY | M1 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `bf41c711241e4c0da9c01ffbe15623f1` / `53b7a9ec15ff40bf9f49107c2cbcbd4a` |
| B001-P026 | REVIEW_IDENTITY | M2 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `55e85d17b6004ddf8c9aafb6ae1a384a` / `b1c6f751031f40bc80642c06e95cafa3` |
| B001-P028 | REVIEW_IDENTITY | Jawny CREATE odrębnego `XBRAKE CLEANER liquid` z code `NULL` pod istniejącym producentem | CREATE; bez LINK do `XBRAKE CLEANER` | `4be209382f24438f8d6d7ad92df78c72` / `d1ce1d9b6ed0451695deaace0e0f0500` |
| B001-P031 | REVIEW_IDENTITY | M3 → `CX80 Polska`; brak dokładnego PRODUCT | CREATE | `3b45f284e03c4992a006782767825108` / `a39635fb5a414dde93bcf179f0bec6b0` |
| B001-P037 | REVIEW_IDENTITY | Istniejący `XBRAKE CLEANER` z zachowanym kodem, lecz incoming PDF różni się od istniejących SDS | REVIEW_SOURCE_CONFLICT, bez zapisu: CURRENT ma datę `2026-09-01`, incoming `2023-01-24`; brak jednoznacznej decyzji o zastąpieniu CURRENT | `833c0080c0a34bd1a40f5b2be18b82a6` / — |

Wszystkie 11 JSON i realnych PDF były dostępne. Dla każdego ponownie przeliczono exact SHA-256 i sprawdzono relację manifest ↔ JSON ↔ PDF. Pełna macierz z expected/actual SHA, kandydatami, wszystkimi istniejącymi SDS, planowaną korektą i działaniem jest w `BATCH-001_STAGE1_IMPORT_REPORT.md` w sekcji TASK-058.

## Korekta PRODUCT i audyt

P023 zachował `product_id=e8d4fa16679240adb1bf094578367f05`, display name `CX80 Płyn Konserwująco Naprawczy` i znany kod `0300-F0DT-500F-GJ25`. `CorrectProductIdentity` zmienił tylko `manufacturer_id`: `5a43d93166e845d597a296986f2798f7` (`CX80`) → `a11c4d78f64b41f89de6ec0196a9254b` (`CX80 Polska`). `PRODUCT_IDENTITY_CHANGE.change_id=30f1f944d7244a43bfb017658bb775a6`, `change_kind=CORRECTION`, zawiera stare/nowe ID producenta i niezmieniony kod/nazwę. Korekta i audyt były jedną transakcją; istniejący SDS `ba4ecda7d9d1479782acbb84bd5ccf48` pozostał `CURRENT`. P037 nie został skorygowany, ponieważ dokument nie miał jednoznacznego planu końcowego.

## Operator writes i kontrola

TASK-058: **8 PRODUCT + 8 SDS + 8 PRODUCT_HISTORY, 1 UPDATE istniejącego PRODUCT, 1 PRODUCT_IDENTITY_CHANGE**, 0 nowych MANUFACTURER, 0 SAFETY_PROFILE, 0 SDS_COMPONENT, 0 BHP_DECISION. W `SDS_ROOT_PATH` powstało dokładnie **8 nowych PDF**; odczytano każdy i potwierdzono SHA-256 względem manifestu. Nowe PRODUCT i wpisy historii zachowują `use_description=NULL`, `use_restriction=NULL`. Wszystkie nowe SDS są `CURRENT`. Po zapisie operator DB ma 5 producentów, 35 produktów, 37 SDS i 41 wpisów PRODUCT_HISTORY. P028 ma odrębny `product_id` od starego `XBRAKE CLEANER`; P012/P037 nie zostały zmienione.

## Finalne liczniki BATCH-001_CX

| Stan | Liczba | Pozycje |
|---|---:|---|
| Imported/registered logical SDS | 32 | 22 z TASK-057, 8 z TASK-058, wcześniej zarejestrowane P001 i P023 |
| Exact existing / skipped source | 2 | P001, P023 |
| Duplicate source | 1 | P015 |
| Excluded non-SDS | 2 | P032, P033 |
| Remaining REVIEW | 2 | P012, P037 |

## Decyzje batchowe i implementacja

`BATCH-001_STAGE1_REVIEW_DECISIONS.json` utrwala M1/M2/M3 jako `human_approved=true`, `APPROVED_BATCH_DECISION`, z dokładnym `observed_value`, celem ID/nazwą oraz identyfikatorami manifestu. Nie dodano globalnej reguły normalizacji ani hardcode tych wariantów w resolverze production. Runner `scripts/task058_resolve_review_identity.py` wykonuje tylko 11 pozycji, odczytowy re-preflight, per-item revalidation i kontrolowane commity. Dla ścieżki korekta + nowa rewizja dodano `CorrectAndRegisterStage1Sds`: `CorrectProductIdentity` i `RegisterStage1Sds` działają we wspólnej transakcji, a `ImportSds` zapewnia write-once PDF oraz kompensację przy rollbacku. Ta ścieżka została sprawdzona izolowanym testem; operatorowy P023 wymagał tylko korekty, P037 pozostał REVIEW.

## Walidacja

- Isolated PostgreSQL i tymczasowy SDS root: M1/M2/M3 do istniejącego producenta, 8 CREATE, P028 odrębny mimo podobnego produktu, P023 korekta + audyt, dokładny istniejący SDS, korekta z nową rewizją i `CURRENT → ARCHIVED`, konflikt tych samych metadanych z innym SHA, hash mismatch z globalnym STOP oraz wstrzyknięty błąd po zapisie SDS z rollbackiem korekty/audytu/SDS i kompensacją PDF: **4 passed**.
- Related regression TASK-051-R1 / 053 / 056 / 057 wraz z focused TASK-058: **71 passed, 3 skipped**. Trzy testy TASK-051 wymagają osobnej bazy o prefiksie `task051_`; odpowiednia korekta i rollback są bezpośrednio pokryte nowymi testami TASK-058.
- `git diff --check`: exit 0, bez błędów whitespace; Git zgłosił ostrzeżenia odczytu starych `.pytest_tmp` i LF/CRLF. Operator `alembic current`: `b7d4a1f03962 (head)`; `alembic check`: PASS.
- Odczytowa kontrola 11 wierszy raportu, 8 nowych PRODUCT/SDS/PDF, P023 `CORRECTION` i braku zmian P012/P037: PASS.

## Odchylenia / ryzyka

P012 ma ten sam fizyczny PDF co `Cleaner prof` pod `CX80 Polska`, lecz nazwa Evidence JSON to `CLEANER PROF`; brak jawnej decyzji LINK tego PRODUCT. P037 ma odmienny incoming PDF i istniejący `CURRENT` SDS z późniejszą datą; Task nie zatwierdza zamiany tego CURRENT na dokument z 2023 r. Zgodnie z granicą Tasku oba przypadki pozostały REVIEW bez zapisu. `V:` z manifestu jest niedostępny, więc `--source-root` podał rzeczywisty katalog, przy zachowaniu exact SHA wszystkich 11 źródeł. Nie zmieniono Core, schematu, Alembic ani zależności.

**STOP po BATCH-001_CX. Nie uruchomiono Paczki2, biblioteki normalizacji ani Stage 2.**
