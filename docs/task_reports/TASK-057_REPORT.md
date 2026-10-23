# TASK-057 REPORT — BATCH-001_CX Stage 1 Batch Commit

## Status

**DONE.** Pełny preflight zakończył się PASS, wykonano 22 kontrolowane commity Stage 1. Każda pozycja była osobną transakcją. Nie było błędu commitu. **STOP po BATCH-001_CX**; nie uruchomiono Paczki2 ani kolejnego sprintu.

## Zakres i pliki

- `scripts/task057_stage1_batch_import.py` — read-only preflight 37 pozycji, źródła PDF z runtime `--source-root`, exact SHA-256, jawna decyzja producenta, rozstrzygnięcie produktu/SDS, zatwierdzony plan i revalidation przed każdym controlled commit; globalny STOP przy BLOCKED_SOURCE/BLOCKED_DATA i STOP dalszych itemów po awarii.
- `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_BATCH_DECISION.json` — decyzja obowiązująca tylko tę paczkę: canonical `CX80 POLSKA` → istniejący `CX80 Polska`. Nie zapisano reguły normalizacji do biblioteki.
- `tests/integration/test_task057_stage1_batch.py` — scenariusz mieszany oraz odmowy/rollback na izolowanym PostgreSQL i tymczasowym SDS root.
- `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md` — pełna macierz 37 manifest entries z oczekiwanym i rzeczywistym SHA, klasyfikacją, kandydatami, działaniem i ID.

Bez zmian Core, schematu, migracji, zależności ani Streamlit w TASK-057.

## Preflight operatorowy

Manifest: **37 PDF**, w tym **35 logical SDS / 35 Evidence JSON** oraz **2 techniczne karty RC72**. Wszystkie 35 SDS miały obecny i parsowalny JSON, dokładną relację manifest → JSON → `DOC-001` → PDF oraz SHA-256 realnych bajtów zgodne z manifestem i JSON. `--source-root` zastąpił wyłącznie fizyczną lokalizację `input_directory`; nie wystarczyło dopasowanie nazwy pliku. Wszystkie 22 READY przeszły także budowę `ApprovedImportPlan` przed pierwszym zapisem.

| Klasyfikacja | Liczba |
|---|---:|
| READY_CREATE | 22 |
| READY_ADD_REVISION | 0 |
| SKIP_EXACT_EXISTING | 1 |
| SKIP_DUPLICATE_SOURCE | 1 |
| REVIEW_IDENTITY | 11 |
| BLOCKED_SOURCE | 0 |
| BLOCKED_DATA | 0 |
| EXCLUDED_NON_SDS | 2 |

Operator Alembic: `b7d4a1f03962 (head)`; `alembic check`: **No new upgrade operations detected**. Preflight wykonał zero zapisów operatorowych.

## Commity i identyfikatory

| Manifest ID | product_id | sds_id |
|---|---|---|
| B001-P002 | e7e27a6d6bda4f18b6a76c572a68517e | a67a4b62c3134bd4a90e5a50c23b8ec1 |
| B001-P003 | 3577f38e493e4902bd99c4598ccf0281 | baeb14fe96ed476990053853f9d2e248 |
| B001-P004 | f77411b0bdd843b5a81f27ff17893d68 | 72dfbe8477ba428d916d85f3fa1dbd5d |
| B001-P006 | 0d90af8504e345a994aff70b41550352 | a9e0ca917ce84c1e86c7b4c884a5e859 |
| B001-P007 | 1828a9dd7d5c4ecb827f1cbffde5c112 | ad7d58a3dd47411e8788545ec1bf67e7 |
| B001-P009 | 80094d17bb6b465b813fd85237f2c53c | 48e9d9c170f94b88ba5e46634e7b6af0 |
| B001-P010 | 884a21e49b18476e8eb63da4e16ff30c | 8d53ab84112d49989f2aa543fa9c906d |
| B001-P013 | 0b0ddd7ab04e4b0683c84255c34ab8cd | 4fc9cf64f2b4490299133565e9bdd8e3 |
| B001-P016 | 9d9e82579d874bb6955a96474cce36ec | d823be2c336241b4bde9c9ef88d11808 |
| B001-P017 | 43cd072dc80149a1a7ca9f424f70e0b1 | c15617ea5cfc472e850385bbd837b8a1 |
| B001-P018 | aac98e0b58844b0986676ac02ccedfc7 | d033fb8fa98e4fca95a437e369242d2c |
| B001-P019 | 3daa6e11a7664bcaa0ef677a3ffcee91 | 080991a191754906ad750270e0e8b8e4 |
| B001-P020 | d5f151a8d87140acbf47a41e604740ed | 8697bff9a6e24bf6a4a87d99a7b02256 |
| B001-P021 | 1e23e4e363da402a944f29753b8e366b | 89282ea0600443f095c41d4347e99d59 |
| B001-P022 | 3afdadf05b0b47a6985d5cdc1074e02e | 00dde1649d5249369abbe9a15fc448f4 |
| B001-P024 | 5987c15ec95147f1920cf3692c3eb400 | 56652f44ddb54199a1c91c70e973b350 |
| B001-P027 | f92df9851ce1423592b9a6b6eb8f66df | 85611891b2974fdf9c0e96061f147b62 |
| B001-P029 | 4ce791fd8c7b455096be7c5aa691d24b | e6532392c22f4a928fe882e015aab267 |
| B001-P030 | a585acb459df41bfa63363df16f21395 | 4bc1d2cb1e51480484779fa8922330af |
| B001-P034 | 593d34e47b6f493b8b5b2e04d4e20d93 | 69996966663b4208884566c3667331be |
| B001-P035 | e2d7b18568c54b1990cb3cd4ec848c0a | cae275e592eb404c97d28e24663d0d4f |
| B001-P036 | 2561b410a43b4d4ab1edb216dd0fe412 | abe5088f64a043509325068ffb39a021 |

Wynik: **COMMITTED 22; FAILED_DURING_COMMIT 0; NOT_ATTEMPTED wśród READY 0**. Wszystkie nowe SDS mają status `CURRENT`, datę i rewizję z JSON oraz poprawny powiązany PRODUCT. W 22 nowych PRODUCT i 22 wpisach PRODUCT_HISTORY pola `use_description` i `use_restriction` są rzeczywistym `NULL`. Dla nowych SDS: 0 SAFETY_PROFILE, 0 SDS_COMPONENT i 0 BHP_DECISION.

## Pominięte i do przeglądu

- `B001-P001` ALUCYNK: **SKIP_EXACT_EXISTING**. Zgodne PRODUCT `8691276f0dbd4bc6846ae14e02b79a60`, SDS `3c361a8019d64589b8fcf7ff9479654d`, data, rewizja i SHA PDF. Odczyt po batchu wykazał dokładnie jeden PRODUCT o nazwie ALUCYNK; nie powstał drugi SDS/PDF.
- `B001-P015`: **SKIP_DUPLICATE_SOURCE**, ten sam SHA i tożsamość Stage 1 co `B001-P004`.
- `B001-P032`, `B001-P033`: **EXCLUDED_NON_SDS**, dokładnie karty techniczne `KT CX RC72-1 (1).pdf` i `KT CX RC72-1 (2).pdf`.
- `B001-P005`, `P008`, `P011`, `P012`, `P014`, `P025`, `P026`, `P031`: **REVIEW_IDENTITY — MANUFACTURER_CANONICAL_NOT_APPROVED**. Canonical z ich JSON nie jest zatwierdzoną parą `CX80 POLSKA → CX80 Polska`.
- `B001-P023`, `P028`, `P037`: **REVIEW_IDENTITY — SIMILAR_OR_CODE_CONFLICT_PRODUCT**. Możliwe istniejące produkty pod `CX80` / `Cx80`, w tym `CX80 Płyn Konserwująco Naprawczy` oraz `XBRAKE CLEANER`; bez automatycznego LINK, scalania czy utworzenia duplikatu.
- **BLOCKED_SOURCE 0; BLOCKED_DATA 0.** Pełne szczegóły i konkretni kandydaci są w macierzy batchowej.

## Operator writes i kontrola po commicie

Dokładnie **22 PRODUCT + 22 SDS + 22 PRODUCT_HISTORY = 66 nowych wierszy**, **0 MANUFACTURER**, **0 SAFETY_PROFILE**, **0 SDS_COMPONENT**, **0 BHP_DECISION**; **22 nowe PDF** w `SDS_ROOT_PATH`. Odczytano każdy z 22 PDF z docelowej ścieżki i ponownie sprawdzono jego SHA względem manifestu. Operator DB po batchu ma 5 producentów, 27 produktów, 29 SDS i 33 wpisy historii; 22 zestawy nowych ID są unikalne i obecne. Istniejący producent `CX80 Polska` zachował ID `a11c4d78f64b41f89de6ec0196a9254b`; istniejące produkty ALUCYNK, `CX80 Płyn Konserwująco Naprawczy`, `XBRAKE CLEANER` i `Cleaner prof` pozostały pojedyncze. Nie zmieniono ich tożsamości ani `manufacturer_id`.

## Walidacja

- Izolowany PostgreSQL i tymczasowy SDS root: dwa CREATE, SKIP_EXACT_EXISTING, READY_ADD_REVISION z `CURRENT → ARCHIVED`, REVIEW_IDENTITY, duplicate source, hash mismatch z globalnym STOP przed zapisami oraz wstrzyknięta awaria drugiego commitu z rollbackiem DB, kompensacją PDF i zatrzymaniem trzeciego itemu.
- Focused/integration regression TASK-053/055/056 oraz TASK-057: **61 passed**.
- `git diff --check`: exit 0, bez błędów whitespace; Git zgłaszał wyłącznie ostrzeżenia dla starych katalogów `.pytest_tmp` z odmową dostępu oraz konwersji LF/CRLF. Nowe pliki TASK-057 sprawdzono osobno bez błędów whitespace.
- Operator `alembic current`: `b7d4a1f03962 (head)`; operator `alembic check`: PASS.
- Odczytowa kontrola wszystkich 37 wierszy raportu, 22 rekordów DB, 22 PDF i ALUCYNK: PASS.

## Odchylenia i ryzyka

`V:` z manifestu nie był dostępny. Runtime `--source-root` wskazał rzeczywisty katalog źródłowy, a exact SHA wszystkich 35 SDS był zgodny; nie przyjęto żadnego pliku po samej nazwie. Jedenaście pozycji REVIEW pozostaje poza importem i wymaga odrębnej jawnej decyzji; TASK-057 jej nie zastępuje. Nie wystąpił runtime failure ani częściowy commit.

**STOP po BATCH-001_CX. Nie uruchamiać Paczki2 ani następnego Tasku bez osobnego polecenia.**
