# TASK-062-R3 — PDF → Evidence JSON DRAFT

**STATUS:** DONE w zakresie R3; pełny TASK-062 pozostaje PARTIAL dla identyfikacji 3M. **Data:** 2026-11-10. Wyniki są testowymi propozycjami `PENDING_REVIEW`, bez decyzji operatora, importu ani zatwierdzonego Golden Set.

## Preflight i źródła

Praca wyłącznie w `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, `main`, HEAD i `origin/main` `8f82529da006615eed8b5ca96995873fd7aa9725`. Zastane pliki nieśledzone zachowano. Dziewięć aliasów A-001–A-009 ma status `ACTIVE` w wersjonowanym katalogu. Późniejsza decyzja Architekta o pierwotnym katalogu i `main` zastępuje historyczny wymóg dodatkowego worktree z TASK-062; nie tworzono gałęzi/worktree. Przejrzano `AGENTS.md`, GOV-001/002, CORE-001 v1.8, BDR-005 v1.1, TDR-012, SDS-JSON-001, SDS-SCHEMA-001, SDS-ALIAS-001, pierwotny TASK-062, raporty TASK-061 i R2, matcher R2 oraz historyczny `TASK-062_REPORT.md` odczytowo z lokalnej referencji integracyjnej (nie ma go w bieżącym `main`). Konstytucja/ARCH nie występują jako osobny plik w bieżącym repo; nie podejmowano decyzji Core. W CORE-001 v1.8 nagłówek i historia wskazują Approved, lecz §22 zachował tekst z etapu draft — rozbieżność redakcyjna do kontroli Cerberusa, bez wpływu na odczyt PDF i bez zmiany Core.

| Źródło | Strony | SHA-256 po preflight i przebiegu |
|---|---:|---|
| OPEX | 25 | `2de8f263567f82860fc229adc11a6fad20c4c65ab3972af5288e72c968905d3b` |
| B002-01 | 24 | `f078434cfe90d09238b81cf83f2df846f46ac93107a586a29e8a6db18a2aea72` |
| B002-02 | 25 | `de3640fd8e66dfa9bc8c313cfa90844f0c7e61a09a20f918ae0de296f69d4d3d` |
| B002-03 | 24 | `cbb38ba8ff6cb9bbfb8ab2e9b91b9476dfcb21a467f05c292ba2022c31c4bc45` |
| B002-04 | 20 | `add472a1e9d5b3cd09a4df7da4670398883ddf92df603684a671fe5df6feb5a9` |
| 3M DP-490 | 49 | `deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48` |

Hashe B002 są zgodne z TASK-061. Wszystkie źródła mają istniejącą warstwę tekstową; runtime nadał im `READABLE`. Nie użyto OCR.

## Wyniki runtime i walidacji

Jedno CLI: `.\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence '<PDF>' --output-dir tmp/task062r3_verified --source-id <ID>`. Dla każdego ID zapisano `tmp/task062r3_verified/<ID>.evidence.json` i `<ID>.validation.json`; macierz porównawcza jest w `tmp/task062r3_verified/QUALITY_MATRIX.md`. Katalog `tmp/` jest ignorowany przez Git i nie zawiera kopii PDF. Wszystkie sześć przebiegów: G1=PASS, G2=PASS, G3=PASS; każdy dokument ma `PENDING_REVIEW` i `REQUIRES_HUMAN_REVIEW`. G3 zachowuje ostrzeżenie o koniecznej decyzji człowieka co do producenta. Istniejący walidator struktury importowej `_validate_document` nie wykazuje błędów dla wszystkich pięciu wymaganych kart i trzech kart 3M; nie uruchomiono planera względem DB.

| ID / zakres stron | Nazwa z §1.1 | Data / rewizja z treści | Kod / podmioty |
|---|---|---|---|
| OPEX / DOC-001, 1–25 | `OPEX® Acrylic Clear Metal Lacquer` | `2022-11-25` / `8` | `T82C13`; The Sherwin-Williams Company = `MANUFACTURER_EXPORTER`, Valspar B.V. = `EU_REPRESENTATIVE` |
| B002-01 / DOC-001, 1–24 | `SYLGARD™ 160 Silicone Elastomer-Part A` | `2021-10-28` / `5.0` | kod `NOT_FOUND`; DOW POLSKA SP.Z O.O. = `SUPPLIER` |
| B002-02 / DOC-001, 1–25 | `SYLGARD™ 160 Silicone Elastomer-Part B` | `2022-11-01` / `5.0` | kod `NOT_FOUND`; DOW POLSKA SP.Z O.O. = `SUPPLIER` |
| B002-03 / DOC-001, 1–24 | `SYLGARD™ 170 Silicone Elastomer Part A` | `2021-10-26` / `4.1` | kod `NOT_FOUND`; DOW POLSKA SP.Z O.O. = `SUPPLIER` |
| B002-04 / DOC-001, 1–20 | `SYLGARD™ 170 Silicone Elastomer Part B` | `2022-11-07` / `7.0` | kod `NOT_FOUND`; DOW POLSKA SP.Z O.O. = `SUPPLIER` |
| 3M / DOC-001..003, 1–3 / 4–26 / 27–49 | `NOT_FOUND` | `NOT_FOUND` / `NOT_FOUND` | brak ACTIVE aliasów dla etykiet 3M; segmentacja potwierdzona, ekstrakcja identyfikacyjna **niezweryfikowana pozytywnie** |

Przykłady evidence: OPEX s. 1 §1.1 `Nazwa produktu : OPEX® Acrylic Clear Metal Lacquer`; OPEX s. 1/25 stopka `Data wydania/Data aktualizacji : 25, Listopad, 2022` przed `Data poprzedniego`; B002-02 s. 1 nagłówek `Aktualizacja: 2022/11/01`; B002-04 s. 1 nagłówek `Aktualizacja: 2022/11/07`. JSON zachowuje dosłowne `®`/`™`, stronę, sekcję/podsekcję i `source_text`. Daty B002-02/04 pochodzą z tekstu mimo sprzecznych sugestii nazw plików. `MANUFACTURER_EXPORTER` jest wyłącznie dowodem roli; żadna rola nie staje się automatycznie `PRODUCT.manufacturer_id`.

## R3-1–R3-8

| ID | Wynik i dowód |
|---|---|
| R3-1 | PASS z uwagami źródłowymi: pierwotne `main`, HEAD/zdalny HEAD wyżej, dziewięć ACTIVE, hashe sześciu PDF; brak nowych worktree. Historyczny raport TASK-062 odczytany z referencji integracyjnej, brak osobnego pliku Konstytucji/ARCH w repo. |
| R3-2 | PASS dla wymaganych pięciu PDF: pięć DRAFT o `schema=SDS-JSON-001`, `schema_version=0.1`, po jednym logicznym SDS; G1 i istniejący walidator struktury PASS. |
| R3-3 | PASS: testy sprawdzają oryginalne PDF i wymagają evidence dla każdego `FOUND`; G2 weryfikuje stronę w zakresie, sekcję, cytat w PDF, aktywną etykietę i zgodność wartości z cytatem. |
| R3-4 | PASS: OPEX ma dwie oddzielne role; cztery SYLGARD wyłącznie `SUPPLIER`; G3 wykrywa podmienioną rolę. Brak decyzji producenta. |
| R3-5 | PASS: test `NOT_FOUND` kodu SYLGARD/3M, `UNREADABLE` dla rzeczywistego U+FFFD w fixture, `AMBIGUOUS` i nieaktywny alias w R2; numer strony, historyczna data i nazwa PDF nie tworzą `FOUND`. |
| R3-6 | PASS: raport G1/G2/G3 na każdy PDF; negatywne testy brak evidence → G1 FAIL, cytat spoza PDF i błędna data → G2 FAIL, zamieniona rola → G3 FAIL, całkiem pusty PDF → G2 FAIL/BLOCKED i CLI nie zapisuje DRAFT. |
| R3-7 | PASS: nowe moduły importują tylko `pypdf`, matcher i standardową bibliotekę; brak wywołań repository/SQLAlchemy/Streamlit. Diff nie obejmuje Core, DB, migracji, UI ani PDF. |
| R3-8 | PASS: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py -q -p no:cacheprovider --basetemp tmp/task062r3_pytest_verified2` → **18 passed in 7.59s**. |

**Zmienione pliki:** nowy `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py`, `tests/unit/test_task062_r3_evidence.py`, niniejszy raport; testowe wyniki i macierz tylko pod `tmp/`. `git diff --check` czysty. HEAD bez zmiany, bez commit/push (R3 ich nie autoryzuje); zastane nieśledzone pliki pozostały nietknięte. Brak zapisu do PostgreSQL/Core i brak zmian źródłowych PDF.

**Pozostała luka:** trzy logiczne karty 3M są rozdzielone, lecz dziewięć aliasów ACTIVE nie obejmuje ich etykiet nazw/dat/rewizji. Nie utworzono zastępczych parserów ani nowych aliasów. Nie wykonano sekcji 2/3/11, operator review ani importu. Materiał wymaga kontroli Cerberusa; **STOP, bez kolejnego etapu**.
