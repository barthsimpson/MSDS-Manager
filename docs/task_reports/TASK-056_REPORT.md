# TASK-056 REPORT

## STATUS

**DONE — jeden realny COMMIT ALUCYNK wykonany; STOP po nim.** Wznowienie nastąpiło na podstawie jawnej decyzji Architekta/Cerberusa dopuszczającej cztery kolumny nullable i prawdziwy snapshot `NULL` w historii. Lokalizacja realnego PDF została wskazana przez `--source-root`.

## CHANGED FILES

- `migrations/versions/b7d4a1f03962_task_056_stage1_administrative_null.py`, `app/infrastructure/db/models/catalog.py` — cztery kolumny nullable.
- `app/domain/models/catalog.py`, `app/application/dto/sds.py`, `app/application/dto/approved_import.py`, `app/application/dto/products.py`, `app/application/dto/supervisory.py` — kontrakty dopuszczające Stage 1 `NULL`.
- `app/application/use_cases/register_stage1_sds.py`, `app/application/use_cases/controlled_evidence_import.py` — plan i zapis Stage 1 z `NULL`, zachowana walidacja ręcznego workflow.
- `app/infrastructure/db/repositories/bhp_decision.py`, `app/infrastructure/db/repositories/bhp_decision_query.py`, `app/application/dto/bhp_decisions.py`, `app/application/ports/bhp_decision.py`, `app/presentation/streamlit/bhp_decision.py` — bramka BHP i jej prezentacja.
- `app/presentation/streamlit/composition.py`, `app/presentation/streamlit/product_registry.py` — typowanie i prezentacja brakujących danych administracyjnych.
- `app/application/use_cases/automatic_stage1_import.py`, `scripts/task056_stage1_import.py`, `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_DECISION.json` — jawna decyzja batchowa i runner jednego Evidence JSON; `--source-root` nadpisuje tylko lokalizację PDF.
- `app/infrastructure/filesystem/evidence_source_pdf.py` — opcjonalny katalog źródłowy przy zachowaniu identyfikacji i SHA z manifestu.
- `tests/integration/test_task056_stage1_automatic.py` — cykl migracji, automatyczny precheck/commit na izolowanym PostgreSQL oraz przypadki odmowne.
- `docs/task_reports/TASK-056_REPORT.md` — raport.

## SCHEMA / MIGRATION IMPACT AND NULL SEMANTICS

- Jedna migracja Alembic zmienia tylko `products.use_description`, `products.use_restriction`, `product_history.use_description`, `product_history.use_restriction` z `NOT NULL` na `NULLABLE`. Bez backfillu, placeholderów i zmiany istniejących wartości.
- `NULL` znaczy „administrative data not yet provided”. Przy Stage 1 CREATE historia jest zapisywana normalnie z tymi samymi dwoma `NULL` co PRODUCT.
- Na jednorazowej bazie PostgreSQL wykonano **upgrade → downgrade → re-upgrade → alembic check: PASS**. Sprawdzono cztery flagi nullable i zachowanie istniejących niepustych wartości przez cykl. Bazę operatora zaktualizowano kontrolowaną migracją `c6a8f1d2940e → b7d4a1f03962`; późniejszy operatorowy `alembic check` wykazał brak driftu.

## BHP GATE

Finalna decyzja jest blokowana, gdy CURRENT SDS nie ma `SAFETY_PROFILE` albo PRODUCT ma `NULL` w którymkolwiek z dwóch pól zastosowania. Repozytorium sprawdza warunki również w transakcji zapisu. Read model i UI wskazują brak danych oraz blokują przycisk. Test izolowany sprawdził brak Safety, następnie obecny Safety z oboma `NULL`, jednym `NULL` i wreszcie oboma polami uzupełnionymi.

## RUNNER ENTRYPOINT

`scripts/task056_stage1_import.py <evidence_json> --manifest <manifest> --decision <batch_decision> [--source-root <katalog>] [--commit]` obsługuje jeden dokument. Bez `--commit` wykonuje tylko precheck. `--source-root` zastępuje wyłącznie fizyczne `input_directory`; manifest nadal wyznacza nazwę PDF, docelowy JSON z kluczem `DOC-001` zakodowanym w nazwie pliku, liczbę logical SDS i oczekiwany SHA-256. Runner przelicza SHA bajtów PDF i odrzuca inną zawartość pod tą samą nazwą. Sprawdza też fingerprint JSON, pola planu, dokładnie jeden rekord producenta o jawnie zatwierdzonej nazwie DB oraz brak produktu dla wybranego `manufacturer_id`. Po sprawdzeniu Alembic head/check plan zamraża ID i snapshot kandydatów. `--commit` używa istniejących `ApprovedImportPlan`, `ControlledEvidenceImport`, `RegisterStage1Sds` i `ImportSds`, z revalidation w zablokowanej transakcji oraz kompensacją PDF.

Artefakt batchowy zatwierdza tylko `B001-P001_DOC-001.json`: canonical `CX80 POLSKA` → dokładna nazwa rekordu DB `CX80 Polska`. Produkcyjny resolver nie zawiera tej pary, nie wykonuje automatycznego fuzzy/case-insensitive LINK, nie dodaje aliasu ani reguły normalizacji. Zatwierdzenie batchowe nie pozoruje potwierdzenia nieistniejących ręcznych pól.

## ISOLATED VALIDATION

- **96 passed** w focused/integration regression TASK-053/054/055/056, BHP, ręcznego SDS i karty produktu.
- Po dodaniu `--source-root`: **10 passed** w focused testach TASK-056 i source binding TASK-054-R1, w tym nadpisanie samej lokalizacji oraz odrzucenie PDF o prawidłowej nazwie i błędnym SHA.
- CLI wykonało precheck oraz dokładnie jeden commit dla kopii JSON z SHA testowego PDF, testowego manifestu, jednorazowej bazy PostgreSQL i tymczasowego SDS root. Powstał jeden PRODUCT, jeden SDS CURRENT, jeden PDF i prawdziwy wpis PRODUCT_HISTORY z dwoma `NULL`; użyto istniejącego producenta. Kod produktu pozostał `NULL`, data `2023-01-23`, rewizja `2.0`. Odczyt CURRENT PDF z karty produktu działa. Liczby `SAFETY_PROFILE`, `SDS_COMPONENT` i decyzji BHP: 0.
- Sprawdzono blokadę duplikatu, zmianę snapshotu producenta, zmianę PDF, błąd bazy po zapisie SDS z rollbackiem oraz awarię filesystem bez zapisu DB. Ręczne `AcceptSds` nadal wymaga obu pól zastosowania.
- `git diff --check -- app migrations scripts tests`: PASS dla śledzonych plików.

## OPERATOR PRECHECK

- Dokładny fingerprint repozytoryjnego JSON: `9b8b107cb6d5fb8c61ab6cd2ddbf63cfe6cff8f3399229d431095c339da902f9` — zgodny z decyzją batchową.
- Manifest i JSON wskazują `ALUCYNK 23.01.2023 rew. 2.0.pdf` oraz oczekiwany SHA-256 `a5078d259e7d34ff1b89b54e39925ba0b642873a2a6ab22a21ed8af834c81442`.
- `--source-root C:\Users\bartosz.murawski\Projects\MSDS-Manager\data\sds\Paczki\Paczka1 cx` wskazał realny PDF. SHA-256 jego bajtów: `a5078d259e7d34ff1b89b54e39925ba0b642873a2a6ab22a21ed8af834c81442` — **PASS**. Dysk `V:` pozostał niedostępny, lecz nie był już potrzebny do odczytu PDF.
- Odczyt operator DB przed migracją: dokładnie jeden `CX80 Polska` (`a11c4d78f64b41f89de6ec0196a9254b`), zero ALUCYNK dla tego producenta, SDS root dostępny. Początkowy precheck wykazał stary head `c6a8f1d2940e`; po zatwierdzonej migracji pełny precheck: Alembic head `b7d4a1f03962`, `alembic check` bez nowych operacji, plan dokładnie jednego CREATE PRODUCT + SDS i LINK producenta — **PASS**.

## ALUCYNK EXPECTED / ACTUAL

| Pole | Oczekiwane | Wynik |
|---|---|---|
| Evidence / logical SDS | `B001-P001_DOC-001.json` / `DOC-001` | Zgodne w manifeście/JSON i planie |
| PRODUCT | CREATE `ALUCYNK`, kod `NULL` | Jeden operatorowy PRODUCT `8691276f0dbd4bc6846ae14e02b79a60`, kod `NULL` |
| Producent | canonical `CX80 POLSKA` → istniejący `CX80 Polska` | LINK do istniejącego ID `a11c4d78f64b41f89de6ec0196a9254b`; bez zapisu producenta |
| Data / rewizja | `2023-01-23` / `2.0` | Zgodne w operatorowym SDS CURRENT |
| Pola administracyjne | `NULL` / `NULL` | Zgodne w PRODUCT i jednym wpisie PRODUCT_HISTORY |
| Safety / BHP | enrichment pending / 0 decyzji | 0 profili, 0 składników, 0 decyzji BHP |
| Realny PDF | exact SHA-256 `a5078d…c81442` | Zaimportowany plik ma exact SHA-256 `a5078d…c81442` |

## OPERATOR WRITES

- Operator DB: **1 migracja schematu**, potem dokładnie **1 PRODUCT, 1 SDS, 1 PRODUCT_HISTORY**; **0 MANUFACTURER, 0 SAFETY_PROFILE, 0 SDS_COMPONENT, 0 BHP_DECISION**.
- Operator `SDS_ROOT_PATH`: dokładnie **1 nowy PDF** pod `imported/b1c7703c-651d-4b9c-b089-f850e43b9947.pdf`.
- Realny COMMIT: **1**. `product_id=8691276f0dbd4bc6846ae14e02b79a60`, `sds_id=3c361a8019d64589b8fcf7ff9479654d`, manufacturer ID/name `a11c4d78f64b41f89de6ec0196a9254b` / `CX80 Polska`, SDS **CURRENT**. Odczytowa kontrola po COMMIT potwierdziła jeden PRODUCT/SDS/historię i SHA zaimportowanego PDF.

## DEVIATIONS / RISKS

Źródłowa ścieżka `V:` z manifestu nadal nie jest dostępna; operatorowy `--source-root` wskazał tę samą zawartość PDF i exact SHA-256. Manifest nie zawiera osobnego pola `document_key`; runner wiąże `DOC-001` z nazwą `B001-P001_DOC-001.json` z manifestu oraz sprawdza jeden dokument o tym kluczu w JSON. Nie dopuszczono akceptacji po samej nazwie PDF.

## NEXT

**STOP → Cerberus review.** Nie importować kolejnej pozycji. Mechanizm przyszłej biblioteki normalizacji RAW → canonical/existing z jawną akceptacją człowieka i osobnym governance ACTIVE pozostaje poza TASK-056.
