# TASK-062-R6 — inwentaryzacja paczek i diagnostyka aliasów

**Status:** diagnostyka zakończona, kandydaci wyłącznie `CANDIDATE`; STOP przed decyzją Architekta. **Data:** 2026-11-12. Praca na istniejącym `main`, bez zmian kodu, katalogu aliasów, PDF, Core, PostgreSQL, UI i importera.

## 1. Preflight i metoda

Punkt wyjścia: lokalny `HEAD` i `origin/main` = `4188b4ffd6c293e97c4426fd42d6306b8d93a7ec` (zamknięty R5). Zastane nieśledzone pliki pozostawiono. `load_catalog()` potwierdził dokładnie 13 aliasów `ACTIVE` A-001–A-013. Przeczytano dyspozycję R6, AGENTS.md, niezbędny GOV-001/GOV-002, raport R5, katalog i bieżący pipeline/CLI; granice TDR-012, SDS-ALIAS-001, SDS-JSON-001 oraz zatwierdzonych BDR/CORE zastosowano bez zmiany ich treści.

Inwentaryzacja objęła **całe** `data/sds/Paczki/`: liczby plików, stron i stron z tekstem z `pypdf` (`extract_text(extraction_mode="layout")`), bez OCR. SHA-256 obliczono tylko w czterech parach o identycznym rozmiarze; każda para okazała się bitowo identyczna. Techniczny wynik odczytu: `tmp/task062r6_inventory.json`; pełna lista 134 względnych ścieżek, stron, czytelności, statusu analizy i par duplikatów jest w [rejestrze R6](TASK-062_R6_INVENTORY.md). `TEXT_ALL` oznacza tekst na każdej stronie, a nie poprawność semantyczną SDS.

## 2. Rejestr paczek

| Paczka | PDF | Inne | Warstwa tekstowa | Stan opracowania |
|---|---:|---:|---|---|
| `Paczka1 cx` | 37 | 0 | 37 pełne | Osobna wcześniejsza analiza BATCH-001: 35 logicznych SDS i 2 karty techniczne; nie jest to Golden Set R2–R5. Para D-03 wewnątrz paczki. |
| `paczka2 sylgard` | 4 | 0 | 4 pełne | Wszystkie 4 były Golden Set R2–R5. |
| `paczka3 silicon` | 4 | 0 | 4 pełne | Pierwsza kolejna nieopracowana; wszystkie 4 objęte wyłącznie diagnostyką R6. |
| `paczka 4 KCH` | 7 | 0 | 7 pełne | Nieanalizowana w R2–R6; para D-02 wewnątrz paczki. |
| `paczka 5 loctite` | 3 | 0 | 3 pełne | Nieanalizowana w R2–R6. |
| `paczka 6 cyna, pasty` | 9 | 0 | 9 pełne | Nieanalizowana w R2–R6. |
| `paczka 7 Noyen` | 5 | 0 | 5 pełne | Nieanalizowana w R2–R6. |
| `paczka 9 smary` | 7 | 0 | 7 pełne | Nieanalizowana w R2–R6. |
| `paczka 10 compound` | 3 | 0 | 3 pełne | Nieanalizowana w R2–R6. |
| `paczka 11 plyny oleje` | 15 | 0 | 15 pełne | Nieanalizowana w R2–R6; D-04 jest także w paczce 15. |
| `paczka 12 lakiery` | 4 | 0 | 3 pełne, 1 częściowa | Nieanalizowana w R2–R6; `Lakier MG Chem 4228a-l pl pol.pdf` ma tekst na 16/18 stronach. |
| `paczka 13 mikrokulka ksztaltki` | 3 | 0 | 3 pełne | Nieanalizowana w R2–R6. |
| `paczka 14 farba` | 18 | 0 | 18 pełne | Tylko OPEX/T82C13 był Golden Set R2–R5; 17 pozostałych nieanalizowanych. Para D-01 wewnątrz paczki. |
| `paczka 15 rozpuszczalniki` | 7 | 0 | 7 pełne | Nieanalizowana w R2–R6; D-04 jest także w paczce 11. |
| `paczka 16 kleje` | 1 | 0 | 1 pełny | Nieanalizowana w R2–R6. |
| `paczka 17 inne` | 7 | 0 | 6 pełnych, 1 bez tekstu | Tylko 3M DP-490 był Golden Set R5; 6 pozostałych nieanalizowanych. `3M Scotch 1601 rew. 11.02, 08.02.2021.pdf` ma 0/21 stron z tekstem, więc nie nadaje się do tego ekstraktora bez osobnej decyzji o OCR. |
| **Razem** | **134** | **0** | **132 pełne, 1 częściowa, 1 bez tekstu** | 6 plików Golden R2–R5 (8 logicznych SDS), 37 plików z odrębnej wcześniejszej analizy BATCH-001, 4 diagnostyczne R6, 87 nadal niebadanych w tych etapach. |

Nie wykryto zaszyfrowanych ani nieparsowalnych PDF. Pary D-01–D-04 i ich pełne SHA są w rejestrze; nie oznaczają podobnych wersji za duplikaty bez zgodnego SHA. Status pojedynczego PDF nie oznacza stanu `DONE` całej paczki.

## 3. Wybór i wykonanie diagnostyki

Wybrano `paczka3 silicon`, następną po pełnym Golden Set `paczka2 sylgard`: cztery czytelne PDF, dwa układy (§1 WEICON i DOWSIL), brak identycznych duplikatów. **Zbadano wszystkie cztery**, nie pozostał w tej paczce niebadany PDF. Każdy ma jedną sekcję 1 na stronie 1 i jeden rzeczywisty logiczny SDS obejmujący cały PDF; nie stwierdzono niepewności segmentacji ani przechodzenia dowodów między kartami. Wynik `_ranges` zweryfikowano z wystąpieniami `SEKCJA 1` na stronach. Źródłem wartości jest treść, nie nazwa pliku: P3-02 nosi w nazwie `Silicon F`, a §1.1 podaje `Silicone F`.

CLI uruchomiono dla każdego PDF jako `python -B -m scripts.extract_sds_evidence <PDF> --output-dir tmp/task062r6_paczka3 --source-id P3-0N`. Cztery uruchomienia zakończyły się kodem 0 i zapisały `P3-01..04.evidence.json` oraz `P3-01..04.validation.json`; zestawienie techniczne jest w `tmp/task062r6_paczka3/summary.json`. Wszystkie źródła są `READABLE`, wszystkie dokumenty mają `PENDING_REVIEW` i `REQUIRES_HUMAN_REVIEW`, a G1/G2/G3 = **PASS/PASS/PASS**. Każde G3 zachowuje ostrzeżenie `MANUFACTURER_REQUIRES_HUMAN_REVIEW`. PASS bramek oznacza spójność wygenerowanego DRAFT, nie kompletność wszystkich pól względem oryginalnej karty.

W tabeli `F` = `FOUND`, `N` = `NOT_FOUND`, `A` = `AMBIGUOUS`. Wartości po dwukropku są wartościami aktualnego DRAFT, nie proponowaną korektą.

| ID / PDF | Logiczny SDS | `product_name` | `manufacturer_product_code` | `issue_date` | `revision` | `parties[]` (dosłowna rola) | G1/G2/G3 |
|---|---|---|---|---|---|---|---|
| P3-01 `Repair Stick Steel 10.19.2022 rew.3.01.pdf` | DOC-001, 1–14 | F: `Repair Stick Steel` | F: `105330` | A: `null` | F: `3.01` | puste, choć §1.3 podaje WEICON | PASS/PASS/PASS |
| P3-02 `Silicon F Weicon 10.19.2022 rew. 3.01.pdf` | DOC-001, 1–12 | F: `Silicone F` | F: `132000` | A: `null` | A: `null` | puste, choć §1.3 podaje WEICON | PASS/PASS/PASS |
| P3-03 `silikon A DOWSIL  CN-8760-PL rew.05 20230106.pdf` | DOC-001, 1–17 | F: `DOWSIL CN-8760 Encapsulant Part A` | N: `null` | F: `2023-01-06` | F: `5.0` | `SUPPLIER` F: `DOW POLSKA SP.Z O.O.` | PASS/PASS/PASS |
| P3-04 `silikon B DOWSIL  CN-8760 PL rew.05 20240725.pdf` | DOC-001, 1–29 | F: `DOWSIL CN-8760 Encapsulant Part B` | N: `null` | F: `2024-07-25` | F: `5.0` | `SUPPLIER` F: `DOW POLSKA SP.Z O.O.` | PASS/PASS/PASS |

P3-01 i P3-02: s. 1 §1.1 ma literalne `Nazwa produktu : Repair Stick Steel` / `Nazwa produktu : Silicone F` i `Kod produktu : 105330` / `Kod produktu : 132000`; istniejące A-001/A-002 poprawnie zwracają `FOUND`. P3-03/04: s. 1 §1.1 `Nazwa wyrobu: DOWSIL™ CN-8760 Encapsulant Part A/B`, nagłówek `Aktualizacja: 2023/01/06` / `2024/07/25`, `Wersja: 5.0`, a §1.3 `IDENTYFIKACJA FIRMY` → `DOW POLSKA SP.Z O.O.`; A-006–A-009 działają. Symbol `™` pozostaje w evidence, a operacyjna nazwa jest normalizowana zgodnie z R5. W §1.1 DOWSIL brak literalnego kodu produktu; stan `NOT_FOUND` nie wymaga nowego aliasu.

## 4. Macierz kandydatów i rozdzielenie przyczyn

Wszystkie poniższe pozycje są **regułami kontekstowymi dla istniejących etykiet**, nie propozycjami natychmiastowego włączenia nowych `ACTIVE`. Nie wykryto nowej literalnej etykiety wymagającej prostego aliasu. Kandydatów nie wpisano do `config/sds_aliases.json`.

| CANDIDATE ID / priorytet | PDF / SDS, etykieta i pole | Źródło oraz obecny stan | Proponowana reguła i oczekiwane zachowanie | Negatywy, wpływ na 13 ACTIVE i test regresyjny |
|---|---|---|---|---|
| **R6-C01 / wysoki** — parsowanie daty, nie brak aliasu | P3-01 i P3-02, DOC-001; `Data wydania/Data aktualizacji`, stopka; `document_metadata.issue_date` | S. 1 obu: `Data wydania/Data aktualizacji :10/20/2022   Data poprzedniego wydania :10/19/2022`; A-005 rozpoznaje etykietę, lecz zwraca `AMBIGUOUS`, `null`, bez evidence, bo jego parser oczekuje polskiego zapisu miesiąca. | Wyłącznie dla jednoznacznego formatu `MM/DD/YYYY` przy bieżącej etykiecie parsować `10/20/2022` na `2022-10-20` i zachować literalny cytat. Jeśli obie liczby mogą być miesiącem, pozostawić `AMBIGUOUS` do decyzji; nie opierać się na nazwie pliku. | Nie pobierać `Data poprzedniego wydania :10/19/2022` ani s. 12/14 `Data wydruku : 10/21/2022`. Rozszerzenie zachowania A-005 wymaga testów obu WEICON, OPEX (`25, Listopad, 2022`), 3M `DD/MM/YYYY` i niejednoznacznego `02/03/2022`; A-001–A-004/A-006–A-013 bez zmiany. |
| **R6-C02 / wysoki** — układ §1.3, nie nowa rola | P3-01 i P3-02, DOC-001; `1.3 Dane dotyczące dostawcy karty charakterystyki`; `parties[].name`, rola źródłowa `SUPPLIER` | S. 1 obu: `1.3 Dane dotyczące dostawcy karty charakterystyki` / następny wiersz `WEICON GmbH & Co. KG` / `Königsberger Str. 255`. Obecnie `parties=[]`: A-013 oczekuje `Adres:`, A-009 oczekuje `IDENTYFIKACJA FIRMY`. | W obrębie §1.3, po nagłówku dostawcy, pobrać bezpośredni następny wiersz nazwy podmiotu, z literalnym dowodem i rolą `SUPPLIER`; bez automatycznego `MANUFACTURER`. To wariant układu dla A-013, a nie drugi alias tej samej etykiety. | Nie pobierać ulicy, `Phone`, `Internet`, `Adres e-mail osoby : msds@weicon.de` ani treści §1.4. Test obu WEICON oraz negatywnych wierszy kontaktowych; regresja 3M A-013 (`Adres:`), SYLGARD A-009 i OPEX A-003/A-004. Pozostałe ACTIVE bez wpływu. |
| **R6-C03 / średni** — kontekst powtórzonej rewizji | P3-02 DOC-001; `Wersja`, stopka i §16; `document_metadata.revision` | S. 12 §16: `Wersja : 3.01`; na dole tej samej strony `Data wydania/Data aktualizacji :10/20/2022 ... Wersja :3.01 12/12`. A-006 widzi dwa wystąpienia w ostatnich 16 wierszach i zwraca `AMBIGUOUS`, `null`, mimo zgodnej wartości; s. 1 stopka ma też `Wersja :3.01`. P3-01 zwraca `FOUND 3.01`. | Ograniczyć odczyt do właściwej stopki dokumentu albo uznać powtórzenia wyłącznie wtedy, gdy pochodzą z tej samej logicznej SDS i mają identyczną wartość; w P3-02 oczekiwane `FOUND 3.01` z dowodem s. 1/12. Nie łączyć sprzecznych rewizji. | Negatyw: wersja transportu, numer strony `12/12`, odmienne rewizje w jednym SDS nadal `AMBIGUOUS`. Test P3-02 i P3-01 oraz regresja A-006 OPEX/SYLGARD i A-012 3M; bez poszerzania kontekstu innych ACTIVE. |

Rozpoznanie przyczyn: P3-01/02 data = **parser formatu**; WEICON party = **układ/kontekst przy istniejącej etykiecie**; P3-02 rewizja = **duplikat wystąpienia w zbyt szerokim kontekście**, nie niejednoznaczność źródła. Nie stwierdzono błędu segmentacji ani niedostępnego tekstu w wybranej paczce. Brak kodu w DOWSIL pozostaje `NOT_FOUND`, bez sztucznego kandydata. Oryginalny skan bez tekstu w paczce 17 jest ograniczeniem odczytu, nie problemem aliasu; nie wykonywano OCR.

## 5. Kolejność dalszych paczek

**Następna proponowana:** `paczka 5 loctite` — trzy PDF z pełną warstwą tekstową, odrębny producent i prawdopodobnie inny układ niż WEICON/DOWSIL; hipotezę układu trzeba sprawdzić w treści podczas osobnego Tasku. Dalej: `paczka 4 KCH` (7 PDF, ale tylko 6 unikalnych bitowo), `paczka 10 compound` (3), `paczka 6 cyna, pasty` (9), `paczka 7 Noyen` (5), `paczka 9 smary` (7), `paczka 13 mikrokulka ksztaltki` (3), `paczka 16 kleje` (1), następnie bardziej mieszane i większe `paczka 12 lakiery` (1 PDF częściowo tekstowy), `paczka 15 rozpuszczalniki` (duplikat z 11), `paczka 11 plyny oleje`, `paczka 14 farba` (17 jeszcze niebadanych, duplikat wewnętrzny) i `paczka 17 inne` (6 jeszcze niebadanych, w tym 1 bez tekstu). Jest to plan przeglądu, nie rozpoczęcie drugiej paczki. Przy każdej przyszłej próbie trzeba pominąć identyczne SHA i rozdzielić PDF niebędące SDS.

## 6. Kontrola R6-1–R6-6 i zakończenie

| ID | Wynik i dowód |
|---|---|
| R6-1 | PASS: `main` na SHA R5, 13 ACTIVE, zastany stan roboczy zachowany. |
| R6-2 | PASS: 16 katalogów, 134 PDF, 0 innych plików; pełna lista w rejestrze, 4 pary identycznych SHA, 132 pełne / 1 częściowa / 1 bez tekstu. |
| R6-3 | PASS: jedna nowa paczka `paczka3 silicon`, wszystkie 4 PDF w CLI, 0 pozostałych; artefakty wyłącznie w `tmp/`. |
| R6-4 | PASS diagnostyczny: 4 logiczne SDS, zakresy 1–14 / 1–12 / 1–17 / 1–29, pola i G1/G2/G3 wyżej; jawnie opisane 3 luki WEICON. |
| R6-5 | PASS: 3 deduplikowane reguły `CANDIDATE` z cytatami, negatywami, wpływem i testami; 0 aktywacji. |
| R6-6 | PASS: proponowana kolejność, rozróżnienie parsera/kontekstu/odczytu; żadnych zmian Core, DB, UI, ACTIVE, PDF ani integracji. |

Komendy diagnostyczne: `python -B tmp/task062r6_inventory_scan.py` → 134 PDF, 4 pary SHA; `python -B -m tmp.task062r6_run_paczka3` → cztery przebiegi CLI kod 0, G1/G2/G3 PASS; `python -B tmp/task062r6_write_inventory.py` → 134 wpisy w rejestrze. Pomocnicze skrypty i JSON są tylko w ignorowanym `tmp/`. Faktycznie dodane pliki poza `tmp/`: ten raport i `docs/task_reports/TASK-062_R6_INVENTORY.md`. Nie uruchamiano nowych testów regresyjnych, ponieważ kod nie uległ zmianie. Nie wykonano commita ani push zgodnie z R6.

**Ograniczenie:** DRAFT z G1/G2/G3 PASS może mieć `AMBIGUOUS` i niepełne `parties[]`; kandydaci wymagają decyzji Architekta, osobnej implementacji i regresji przed ewentualną aktywacją. **STOP po raporcie.**
