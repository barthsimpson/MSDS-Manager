# TASK-062-R2 — zatwierdzenie i aktywacja aliasów

**Data:** 2026-11-10. **Środowisko:** pierwotny `MSDS-Manager`, lokalny `main`, punkt wyjścia `f97c1e28996ace2087f774aeabec4ca7a9bc91cd`. **Zakres:** tylko biblioteka aliasów, mały matcher i regresja; pełny pipeline TASK-062 nie został rozpoczęty.

## Macierz decyzji i dowodów

Wszystkie reguły przeszły `CANDIDATE → APPROVED` na podstawie decyzji Architekta w TASK-062-R2 (2026-11-10), następnie skupioną regresję na rzeczywistych PDF i dopiero wtedy uzyskały `ACTIVE`. Nazwy plików poniżej identyfikują źródła, nie dostarczają wartości domenowych.

| Alias | Stan przed → po | Regresja, wynik i źródło |
|---|---|---|
| A-001 `Nazwa produktu` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1, §1.1, `Nazwa produktu : OPEX® Acrylic Clear Metal Lacquer`; wartość z tego samego wiersza. |
| A-002 `Kod produktu` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1, §1.1, `Kod produktu : T82C13`; SYLGARD §1.1 bez etykiety → `NOT_FOUND`, bez użycia UFI/nagłówka. |
| A-003 `Mfg. in U.S.A and exported by` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1, §1.3, następny wiersz `The Sherwin-Williams Company`; rola `MANUFACTURER_EXPORTER`, bez adresu. |
| A-004 `EU Only Representative` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1, §1.3, `EU Only Representative: Valspar B.V.`; osobna rola `EU_REPRESENTATIVE`. |
| A-005 `Data wydania/Data aktualizacji` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1 i 25, stopka, `25, Listopad, 2022` → `2022-11-25`; odcięcie `Data poprzedniego ... 18, Cze, 2022`. |
| A-006 `Wersja` | CANDIDATE → APPROVED → ACTIVE | PASS: OPEX s. 1/25 stopka `8`; B002-01..04 s. 1 nagłówek `5.0`, `5.0`, `4.1`, `7.0`; `1/25` → `NOT_FOUND`. |
| A-007 `Nazwa wyrobu` | nowy → APPROVED → ACTIVE | PASS: B002-01..04 s. 1, §1.1: `SYLGARD™ 160 Silicone Elastomer-Part A/B`, `SYLGARD™ 170 Silicone Elastomer Part A/B`; dosłowny odczyt treści. |
| A-008 `Aktualizacja` | nowy → APPROVED → ACTIVE | PASS: B002-01..04 s. 1 nagłówek `2021-10-28`, `2022-11-01`, `2021-10-26`, `2022-11-07`; wykluczone `Data ostatniego wydania` i etykieta OPEX. Daty B002-02/04 różnią się od sugestii nazw plików. |
| A-009 `IDENTYFIKACJA FIRMY` | nowy → APPROVED → ACTIVE | PASS: B002-01..04 s. 1, §1.3, blok `Dane dotyczące dostawcy karty charakterystyki` → `DOW POLSKA SP.Z O.O.` jako `SUPPLIER`; negatywny OPEX §1.4 → `NOT_FOUND`. |

**Sprostowanie R1:** wcześniejsze `�` w konsolowym cytacie nazw jest błędem wyświetlania: oryginalna warstwa tekstowa zawiera `®` (U+00AE) i `™` (U+2122). R2 sprawdził kodpunkty i zachował je dosłownie. Test z prawdziwym U+FFFD zwraca `UNREADABLE`, bez korekty. Wielokrotna etykieta zwraca `AMBIGUOUS`. Każdy `FOUND` ma stronę, sekcję/podsekcję i krótki cytat `source_text`.

## Kontrola R2-1–R2-7

| ID | Wynik |
|---|---|
| R2-1 | PASS: pierwotny katalog, `main`, baza `f97c1e2`; zastane nieśledzone dane i dokumenty pozostawione. |
| R2-2 | PASS: dziewięć jawnych reguł i statusów w bibliotece oraz wersjonowanym katalogu; `REVIEW/BLOCKED`: brak po tej regresji. |
| R2-3 | PASS: oryginalny OPEX s. 1/25 i cztery oryginalne SYLGARD s. 1; przypadki negatywne granic sekcji, etykiet, dat, kodu i numeru strony. |
| R2-4 | PASS: decyzja Architekta → `APPROVED` → regresja 7/7 PASS → `ACTIVE`; test nieaktywnego aliasu i U+FFFD. |
| R2-5 | PASS: role `MANUFACTURER_EXPORTER`, `EU_REPRESENTATIVE`, `SUPPLIER` i pole `issue_date` są zgodne z `SDS-JSON-001`; daty pochodzą z treści. |
| R2-6 | PASS: zmiany ograniczone do biblioteki/reguł, testów i tego raportu; bez Core, DB, UI, PDF i środowiska. |
| R2-7 | Identyfikator commita i wynik zwykłego push potwierdza końcowa odpowiedź po kontroli `origin/main`; SHA commita zawierającego ten plik nie może być zapisane w nim samym. |

**Testy:** `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py -q -p no:cacheprovider --basetemp tmp/task062r2_alias_regression4` → `7 passed`; po aktywacji i teście bramki runtime analogiczna komenda z `--basetemp tmp/task062r2_alias_final` → `8 passed in 0.41s`.

**Pliki do kontrolowanego commita:** `docs/tasks/SDS-ALIAS-001_Biblioteka_aliasow_i_reguly_rozszerzania_v1.0-approved.md`, `config/sds_aliases.json`, `app/infrastructure/filesystem/sds_alias_matcher.py`, `tests/unit/test_task062_r2_aliases.py`, ten raport. **STOP po raporcie;** właściwy PDF → Evidence JSON DRAFT wymaga osobnego wznowienia TASK-062.
