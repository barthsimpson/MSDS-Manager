# TASK-062-R15 — cyna i pasty: implementacja i regresja

**Status:** CLOSED po pozytywnej weryfikacji i publikacji na `main` (końcowy SHA podany w przekazaniu; commit nie może zawierać własnego SHA). **STOP po R15.** R14-C11 pozostaje wydzielony.

## Preflight i źródła

Przed zmianami: `main`, `HEAD`, `origin/main` i zdalny `main` = `2b5f05ee323fcf9283bb362d17c1ea8e44595a81`; pliki śledzone czyste. Zastane nieśledzone taski/raporty R8–R15 pozostawiono poza commitem. Katalog aliasów bez zmian: **13 ACTIVE A-001–A-013**. Oryginały z `data/sds/Paczki/paczka 6 cyna, pasty/`:

| ID | SHA-256 | Strony |
|---|---|---:|
| CP-01 | `6e11c52e3f9a44cfdf52f07420673208abdfa6bea06cf19ff195dc4ce4bf1c9e` | 8 |
| CP-02 | `52550499e07b697e644ba57f4ec7891a3be6c99676fe49a60de0253a00d33b7e` | 18 |
| CP-03 | `55ecd64dd7fddd55c2adbf6bb86f58826d81ad8d536daeb94b697a8616ea4e43` | 19 |
| CP-04 | `94cbbc8c8ccf816ce9e8f2e40fa27557ddf4c043687ef764ae8d571fceefe1ed` | 19 |
| CP-05 | `2ef0c919e9533e0a97cb47da8a40e55eb5f41ca47e7d832d457ad75d7b63ad37` | 12 |
| CP-06 | `715e4278b985e462b7c01e74090ed3d64232049e1d235ccc72d6cf21a3929558` | 9 |
| CP-07 | `00fd5a6f459721f231666cf43e1c50cfc260c8786be98c8bd1c202646bb99d1c` | 9 |
| CP-08 | `bad2a1cbe4749dbadefc9280162a749c51762237bcef3b19f56d7c251e74f7e0` | 9 |
| CP-09 | `5591d3d0c3af17ba4386a2f61108ba55def4c805d74221105cabc58edbeeb8c1` | 17 |

Wszystkie dziewięć SHA są różne i zgodne z R14. Źródła mają czytelną warstwę tekstową. Każdy wynik to **jeden DOC-001** o zakresie 1–liczba stron, bez rozdzielania nazw grupowych na produkty.

## R14-C01–C10: DRAFT przed → po, z dowodem z SDS

`N` = `NOT_FOUND/null`, `A` = `AMBIGUOUS/null`, `F` = `FOUND`. Wartości pochodzą z ponownie odczytanych `tmp/task062r15_cyna_pasty_verified/CP-0N.evidence.json` i odpowiadających `validation.json`, nie z nazwy pliku.

| ID | Nazwa produktu przed → po, cytat | Kod przed → po | Data / rewizja przed → po, cytat | Podmioty przed → po, cytat |
|---|---|---|---|---|
| CP-01 | N → F `Pasta lutownicza seria RMA-218`; s. 1 §1.1 źródłowe `11.1 Identyfikator produktu` / `Nazwa produktu: ...` | N → N; w §1.1 brak kodu | A/N → F `2020-12-14` / F `"2"`; nagłówek s. 1 `Data aktualizacji: 2020-12-14 ... Wydanie 2` | F `SUPPLIER: Reball.pl Roman Jędrzejewski` → bez zmian, s. 1 §1.3 |
| CP-02 | F `Anti-Seize Pasty montażowe Presspack` → bez zmian; s. 1 §1.1 | F `260001` → bez zmian; s. 1 `Kod produktu` | F `2022-12-16` / F `"4.03"` → bez zmian; stopka s. 1 `Data wydania/Data aktualizacji: 12/16/2022`, `Wersja: 4.03`, poprzednie `12/14/2022` wykluczone | F `SUPPLIER: WEICON GmbH & Co. KG` → bez zmian, s. 1 §1.3 |
| CP-03 | **F `NAZWA HANDLOWA:` (błąd)** → F `Spoiwo lutownicze bezołowiowe z topnikiem EVO / EVO11 / PRO / SW26 / 1.1.2 / EVO-H`; s. 1 §1.1 etykieta i następny wiersz w cytacie | N → N; wiele wariantów, brak jednego kodu grupowego | A/A → F `2025-07-08` / F `"5.0/PL"`; nagłówek s. 1 `Data wydania: 2015-12-12 Data aktualizacji: 2025-07-08 wersja: 5.0/PL` | puste → F `SUPPLIER: Cynel-Unipress Sp. z o.o.`; s. 2 §1.3, ten sam SDS |
| CP-04 | **F `NAZWA HANDLOWA:` (błąd)** → F `Spoiwo lutownicze bezołowiowe z topnikiem 1.1.3 /CF48`; s. 1 §1.1, zachowany odstęp przed `/CF48` | N → N; brak jednego kodu grupowego | A/A → F `2025-07-08` / F `"5.0/PL"`; nagłówek s. 1, `Data wydania: 2015-12-12` wykluczona | F `SUPPLIER: Cynel-Unipress Sp. z o.o.` → bez zmian, s. 1 §1.3 |
| CP-05 | F raw `INSTALFLUX TLA                   -4N` → F operacyjnie `INSTALFLUX TLA-4N`; raw pozostaje w dowodzie s. 1 §1.1, potwierdzenie s. 1/12 w stopce | N → N | N/N → F `2022-03-07` / **N**; s. 1 `Data sporządzenia/aktualizacji: 25.01.2016/26.03.2017 r. (1) / 07.03.2022 r. (2)`; `(2)` nie jest rewizją | A → F `SUPPLIER: LUT – SPAW Sp. z o.o.`; s. 1 §1.3 `Dostawca:` i następny wiersz |
| CP-06 | N → F `Pasta lutownicza seria 218, 223, 559, 4300, 321`; s. 1 `11.1` / `Nazwa produktu` | N → N; numery w nazwie nie są kodem | A/N → F `2020-12-14` / F `"3"`; nagłówek s. 1 `Data aktualizacji ... Wydanie 3` | F `SUPPLIER: Reball.pl Roman Jędrzejewski` → bez zmian, s. 1 §1.3 |
| CP-07 | F `Pasta termoprzewodząca H` → bez zmian; s. 1 §1.1 | N → N | F `2023-01-26` / F `"11.0"` → bez zmian; nagłówek s. 1 | F `MANUFACTURER: AG TermoPasty Grzegorz Gąsowski` → bez zmian; s. 1 §1.3 `Producent` |
| CP-08 | F `Topnik lutowniczy 559, 223, 218, 4300, 321` → bez zmian, jedna nazwa serii; s. 1 §1.1 | N → N; numery wariantów nie są kodem | A/N → F `2024-11-08` / F `"1.0"`; nagłówek s. 1 `Data opracowania:` / następny wiersz `08.11.2024`, `Data aktualizacji:-`, `Wersja 1.0` | A → F `SUPPLIER: REBALL TECHNOLOGY Sp. z o.o.`; s. 1 §1.3 `Nazwa i adres:` |
| CP-09 | F `Topnik TK 83` → bez zmian; s. 1 §1.1 | N → N; UFI nie jest kodem | F `2024-01-26` / F `"7.0"` → bez zmian; nagłówek s. 1 (rewizja źródłowa `7.0`, nie `07` z nazwy pliku) | F `MANUFACTURER: AG TermoPasty Grzegorz Gąsowski` → bez zmian, s. 1 §1.3 |

**C01–C03:** §1.1 z zapisem `11.1` działa wyłącznie w sekcji 1; `NAZWA HANDLOWA:` jest etykietą, a nie nazwą. G2 odrzuca nawet dowód o poprawnej stronie i cytacie, jeśli wartością jest sama etykieta (`PRODUCT_LABEL_AS_NAME`). §1.3 CP-03 na s. 2 pozostaje w obrębie tego samego SDS. **C04–C06:** parser zachowuje daty aktualizacji ISO, `Wydanie 2/3` i pełne `5.0/PL`, rozróżniając datę historyczną. **C07–C08:** CP-05 wybiera ostatnią jawną datę z sekwencji bez rewizji z `(2)`; CP-08 używa daty opracowania wyłącznie przy `Data aktualizacji:-` i `Wersja 1.0`. **C09–C10:** dwa źródłowe układy dostawcy potwierdzono jako `SUPPLIER`; nazwa CP-05 jest normalizowana tylko z potwierdzeniem w tym samym SDS, bez globalnej reguły usuwania spacji.

**R14-C11 pozostaje poza zakresem.** CP-03 §1.1 kończy nazwę grupową `/ EVO-H`, a powtarzana stopka `/ SW26`. Ekstraktor zachowuje dokładną nazwę z §1.1 i dodaje `DOC-001:SOURCE_PRODUCT_NAME_DISCREPANCY_REQUIRES_HUMAN_REVIEW` do istniejącego `extraction_report.warnings`. Nie rozstrzyga wariantów, nie tworzy produktów ani powiązań z PRODUCT. CP-04 zachowuje źródłowe `1.1.3 /CF48`. Do rozstrzygnięcia wariantów CP-03: **STOP** i weryfikacja przez człowieka.

## Weryfikacja, publikacja i kryteria

Niezmieniony CLI uruchomiono na 9 oryginałach z `--source-id CP-01..CP-09` i świeżym `--output-dir tmp/task062r15_cyna_pasty_verified`: **9/9 kod 0**, odczytane z dysku **9 Evidence + 9 validation JSON**. Dla wszystkich: `source.language=pl`, jeden `DOC-001`, `PENDING_REVIEW`, `REQUIRES_HUMAN_REVIEW`, G1/G2/G3 **PASS**, właściwy SHA/zakres stron, cytaty na stronach wskazanych w tabeli. `SUPPLIER` nie staje się automatycznie `MANUFACTURER`; dane pozostają DRAFT.

Testy skupione R15: **15 PASS** (9 oryginałów i negatywy etykiety jako nazwy, §11 `11.1`, granicy SDS, kontynuacji §1.3, błędnych i sprzecznych dat/rewizji, `(2)`, daty pierwszego wydania, fałszywych dostawców i normalizacji). Obowiązkowa regresja `pytest` R2/R3/R5/R7/R9/R11/R13/R15: **80 PASS, 0 FAIL, 0 SKIP**. Sprawdzono składnię AST i importy. `git diff --check` oraz `git diff --cached --check` bez błędów.

| ID | Dowód | Wynik |
|---|---|---|
| R15-1 | `HEAD=origin/main=remote`, 9 niezmienionych SHA, 13 ACTIVE, zastane pliki poza commitem | PASS |
| R15-2 | CP-01/03/04/06, dostawca CP-03 s. 2, G2 negatyw etykiety | PASS |
| R15-3 | `2020-12-14`, `2025-07-08`, `"2"`, `"3"`, `"5.0/PL"`; negatywy konfliktów | PASS |
| R15-4 | CP-05 data bez rewizji; CP-08 pierwsze wydanie i `1.0` | PASS |
| R15-5 | CP-05/08 pewni `SUPPLIER`; raw i operacyjna nazwa CP-05 | PASS |
| R15-6 | 9 × DOC-001, tylko jawny kod CP-02; CP-02/07/09 bez pogorszenia; CP-03 ostrzeżenie | PASS; warianty CP-03 do człowieka |
| R15-7 | 15 focused PASS; 80 regresyjnych PASS; 13 ACTIVE | PASS |
| R15-8 | 9 CLI, 18 plików JSON, statusy i G1/G2/G3 PASS | PASS |
| R15-9 | Dwa pliki ekstraktora, nowy test i ten raport; selektywny commit, zwykły push `main` | PASS po publikacji; SHA w przekazaniu |

Zakres Git obejmuje wyłącznie `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `tests/unit/test_task062_r15_cyna_pasty.py` i niniejszy raport. Bez zmian katalogu aliasów, Core, modelu PRODUCT–SDS, kontraktu SDS-JSON-001, PostgreSQL, importera, UI, PDF i danych w `tmp/`. **STOP po R15; bez kolejnej paczki i integracji.**
