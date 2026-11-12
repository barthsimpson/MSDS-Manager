# TASK-062-R8 — diagnostyka paczki 5 LOCTITE

**Status:** diagnostyka wykonana, kandydaci wyłącznie `CANDIDATE`; STOP przed zmianą aliasów i ekstraktora. **Data:** 2026-11-12. Praca na istniejącym `main`, bez brancha i worktree.

## 1. Preflight i źródła

Lokalny `HEAD` i `origin/main` przed pracą: `802903af94f92b099a797fd7e21a2775d13c3565` (`802903a`, po R7 `17abc9a`). Śledzone pliki były czyste; zastany nieśledzony plik dyspozycji R8 pozostawiono. `load_catalog()` potwierdził dokładnie 13 `ACTIVE` A-001–A-013. Przeczytano dyspozycję R8, raporty R6/R7, obecny katalog i ekstraktor oraz niezbędne granice AGENTS/GOV/TDR-012/SDS-ALIAS-001/SDS-JSON-001/BDR-005/CORE-001. Nie zmieniono źródłowych PDF ani historii Git.

Trzy PDF w `data/sds/Paczki/paczka 5 loctite/` są śledzone przez Git i mają warstwę tekstową na każdej stronie (`_read_pdf`, bez OCR). SHA-256 poniżej pochodzi z istniejącego ekstraktora i identyfikuje badane źródło; trzy różne SHA wykluczają identyczne duplikaty w tej paczce. W każdym PDF znacznik `SEKCJA 1` pojawia się na s. 1, bez kolejnego początku §1; rzeczywista segmentacja daje **jeden logiczny SDS na PDF**, obejmujący wszystkie strony. Nie stwierdzono niepewności granic ani wycieku dowodów między kartami.

| ID / źródło | Strony / tekstowe | SHA-256 | Logiczny SDS | CLI / G1,G2,G3 / review |
|---|---:|---|---|---|
| R8-L01 `Loctite 242 31.05.2022.pdf` | 16/16 | `6c1da6c8164c8bb52aa1631508cc6e28a862ee783c2af6ef09db11f4f6a9b6af` | DOC-001, 1–16 | kod 0; PASS,PASS,PASS; `PENDING_REVIEW` |
| R8-L02 `Loctite 243  rew 014.0 (27.03.2024).pdf` | 24/24 | `803058b5358f90c90bd3d8007b7761ccddc1d4513588f6080702f8d988b3c39d` | DOC-001, 1–24 | kod 0; PASS,PASS,PASS; `PENDING_REVIEW` |
| R8-L03 `Loctite 638 24.10.2022.PDF` | 32/32 | `2b8264bb9021c5c0f952539a9f91da7f80909137d666fc157e2dddac8b7ff1b6` | DOC-001, 1–32 | kod 0; PASS,PASS,PASS; `PENDING_REVIEW` |

Wszystkie trzy walidacje mają `G3.issues=[DOC-001:MANUFACTURER_REQUIRES_HUMAN_REVIEW]`, a każdy dokument `validation.status=REQUIRES_HUMAN_REVIEW`. PASS bramek oznacza spójność utworzonego DRAFT, **nie** kompletność daty i rewizji względem czytelnego źródła. Nie uruchamiano importera ani połączenia z DB.

## 2. Pola identyfikacyjne i dowody

`F` = `FOUND`, `N` = `NOT_FOUND`, `A` = `AMBIGUOUS`. Zapis źródłowy nazwy i nazwa operacyjna są identyczne w każdym z trzech dokumentów; w §1.1 nie ma `®`/`™`. Stany w tabeli są **aktualnym wynikiem CLI**, bez dopisywania oczekiwanych wartości do JSON.

| SDS | `product_name` źródłowe = operacyjne | `manufacturer_product_code` | `issue_date` | `revision` | `parties[]` z rolą źródłową |
|---|---|---|---|---|---|
| R8-L01 / DOC-001 | F `LOCTITE 242`, s. 1 §1.1 | N `null` | A `null` | N `null` | `SUPPLIER`, F `Henkel Polska Sp. z o.o.`, s. 1 §1.3 |
| R8-L02 / DOC-001 | F `LOCTITE 243`, s. 1 §1.1 | N `null` | A `null` | N `null` | `SUPPLIER`, F `Henkel Polska Sp. z o.o.`, s. 1 §1.3 |
| R8-L03 / DOC-001 | F `Loctite 638`, s. 1 §1.1 | N `null` | A `null` | N `null` | `SUPPLIER`, F `Henkel Polska Sp. z o.o.`, s. 1 §1.3 |

We wszystkich trzech kartach A-010 poprawnie rozpoznaje s. 1 §1.1, np. `1.1. Identyfikator produktu` / `LOCTITE 242`; A-013 poprawnie rozpoznaje s. 1 §1.3 `Dane dotyczące dostawcy karty charakterystyki` / `Henkel Polska Sp. z o.o.`. Evidence JSON zachowuje pełne literalne `source_text`, stronę, etykietę i podsekcję przy tych polach. W §1.1 jest jedna nazwa produktu i brak etykiety kodu produktu; `KC Numer :  173036` / `316211` / `450822` leży w nagłówku karty i nie jest dowodem `manufacturer_product_code`. Nie ma podstaw do wstawiania kodu z nazwy pliku lub z numeru karty. W §1.3 każdej SDS jest jeden podmiot pod nagłówkiem dostawcy; `ul. Domaniewska 41`, telefon i e-mail nie są nazwami podmiotów. Nie ma źródłowej podstawy do automatycznej roli `MANUFACTURER`.

S. 1 wszystkich kart pokazuje bieżącą `Aktualizacja` oraz osobno `Data druku` i `Zastępuje wersje z`. R8-L01: `Aktualizacja: 11.07.2022`, `Data druku: 30.11.2022`, `Zastępuje wersje z: 31.05.2022`. R8-L02: odpowiednio `14.05.2024`, `14.05.2024`, `27.03.2024` — zgodność bieżącej daty z datą wydruku nie zmienia znaczenia etykiet. R8-L03: `24.10.2022`, `19.07.2023`, `25.03.2022`. Nazwy plików L01 i L02 odzwierciedlają **datę zastępowaną**, nie aktualną. A-008 widzi literalną etykietę `Aktualizacja`, lecz jego parser `YYYY/MM/DD` nie obsługuje `DD.MM.YYYY`, więc daje `AMBIGUOUS` bez evidence. Surowe cytaty są w niniejszym raporcie; JSON pozostaje zgodny z obecnym kontraktem.

W nagłówku s. 1 oraz w nagłówkach kolejnych stron jest `V005.1` (L01, 16 stron), `V014.0` (L02, 24 strony), `V013.0` (L03, 32 strony); na s. 1 poprzedza je `KC Numer`, np. `KC Numer :  173036` / `V005.1`. W żadnym z trzech nagłówków nie ma aktywnej literalnej etykiety `Wersja` ani `Numer wersji`, stąd obecne `revision=NOT_FOUND`. Powtarzany token `V...` wskazuje prawdopodobny numer rewizji karty, ale jego reprezentacja w kanonicznym `revision` wymaga decyzji Architekta przed aktywacją reguły. Liczb stron `1 z 16`, `1 z 24`, `1 z 32` nie wolno używać jako rewizji.

Układ jest jednokartowy, bez wieloskładnikowego zestawu, wielu kodów produktu lub wielu podmiotów w §1.3. Wszystkie trzy PDF są po polsku; angielskie nazwy marki i adresy e-mail nie tworzą osobnego języka SDS. Powtarzają się nagłówki `KC Numer` / `V...`, nie bieżąca data na każdej stronie. Nie zaobserwowano konfliktu wartości `V...` w obrębie danego PDF.

## 3. Deduplikowana macierz kandydatów

Żadnego kandydata nie dodano do katalogu. R8-C01 i R8-C02 są **CANDIDATE** do decyzji Architekta, a nie zatwierdzonymi regułami produkcyjnymi. Nie tworzono osobnych kandydatów dla trzech identycznych układów.

| ID / priorytet | Źródło, etykieta/układ/rola, dowód | Pole / przyczyna i obecny stan | Oczekiwane zachowanie po zatwierdzeniu | Negatywy, wpływ na ACTIVE/R7, proponowany test |
|---|---|---|---|---|
| **R8-C01 / wysoki** | L01/L02/L03 DOC-001, s. 1 nagłówek: `Aktualizacja: 11.07.2022` / `14.05.2024` / `24.10.2022`; na tym samym wierszu jest nazwa produktu. Rola: bieżąca data SDS. | `document_metadata.issue_date`; **parser formatu przy istniejącym A-008**, nie brak aliasu. Dziś `AMBIGUOUS/null`, bo `DD.MM.YYYY` nie pasuje do `YYYY/MM/DD`. | W kontekście nagłówka po `Aktualizacja` rozpoznać kalendarzowo poprawne `DD.MM.YYYY` i dać odpowiednio `FOUND/2022-07-11`, `FOUND/2024-05-14`, `FOUND/2022-10-24` z cytatem s. 1. Bez użycia nazwy PDF. | Nie pobierać `Zastępuje wersje z` (31.05.2022 / 27.03.2024 / 25.03.2022), `Data druku` (30.11.2022 / 14.05.2024 / 19.07.2023) ani dat w treści. Test trzech oryginalnych PDF, daty niemożliwej, złej kolumny oraz regresja A-008 SYLGARD (`YYYY/MM/DD`), A-005/R7 WEICON i A-011 3M. Pozostałe 13 ACTIVE bez redefinicji. |
| **R8-C02 / średni; decyzja o reprezentacji wymagana** | L01/L02/L03 DOC-001, s. 1 nagłówek karty: `KC Numer :  173036` / `V005.1`; `KC Numer :  316211` / `V014.0`; `KC Numer :  450822` / `V013.0`. Token `V...` powtarza się na wszystkich stronach każdej SDS. Rola: prawdopodobna rewizja karty. | `document_metadata.revision`; **nowy układ/token, brak aktywnej etykiety**. Dziś `NOT_FOUND/null`. Jest to kontekst karty, nie prosty alias produktu. | Po potwierdzeniu semantyki `V...` pobierać go tylko z własnego nagłówka logicznego SDS, z zachowaniem literalnego dowodu. Do decyzji: przechowywać `V005.1`/`V014.0`/`V013.0` dosłownie czy wartość bez prefiksu `V`; nie obcinać zer ani prefiksu bez zatwierdzenia. | Nie używać `KC Numer` jako kodu produktu/rewizji, numeru strony, `H`-kodów z §16, tokenu z innej logicznej SDS ani sprzecznych `V...` bez `AMBIGUOUS`. Test trzech PDF, powtarzanego zgodnego tokenu, sztucznego konfliktu, numeru strony; regresja A-006 OPEX/SYLGARD i R7 oraz A-012 3M. 13 ACTIVE bez automatycznej modyfikacji. |

`manufacturer_product_code=NOT_FOUND` jest tu prawidłowym bezpiecznym wynikiem i **nie** tworzy R8-C03. Odczyt nazw i dostawcy działa już przez A-010/A-013. Nie stwierdzono błędu segmentacji ani niedostępnego tekstu; data to parser, rewizja to nowy układ nagłówka i nierozstrzygnięta reprezentacja domenowa. Część dotycząca R8-C02 jest wstrzymana przed implementacją do decyzji Architekta; niezależna diagnostyka R8 jest kompletna.

## 4. Komendy, kontrola R8-1…R8-6 i zakończenie

Uruchomiono istniejący CLI dla każdego źródła: `.\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence '<PDF>' --output-dir tmp/task062r8_loctite --source-id R8-L01` (analogicznie L02/L03). **3/3 kod 0**. Powstały `tmp/task062r8_loctite/R8-L01..L03.evidence.json` oraz odpowiadające `.validation.json`; wszystkie sześć plików pozostaje w ignorowanym `tmp/`. Odczyt `pypdf` i `_ranges` potwierdził 16/24/32 stron z tekstem i po jednym `SEKCJA 1` na s. 1. Nie uruchamiano regresji kodu, ponieważ w R8 nic w nim nie zmieniono.

| ID | Wynik / dowód |
|---|---|
| R8-1 | PASS: `main` na `802903a`, 13 `ACTIVE`, śledzone pliki czyste przed diagnostyką; zastane pliki i historia zachowane. |
| R8-2 | PASS: wszystkie 3 wskazane PDF obecne, śledzone i `READABLE` 16/16, 24/24, 32/32; bez OCR. |
| R8-3 | PASS: każdy PDF ma jeden logiczny SDS 1–16, 1–24, 1–32; źródłowy §1 na s. 1, bez drugiego początku. |
| R8-4 | PASS diagnostyczny: tabela pól i evidence wyżej, 3 DRAFT, G1/G2/G3 PASS, `PENDING_REVIEW`; daty `AMBIGUOUS`, rewizje `NOT_FOUND` jawnie wskazane. |
| R8-5 | PASS: dwie deduplikowane pozycje CANDIDATE z cytatami, negatywami, wpływem i testami; 0 zmian ACTIVE. |
| R8-6 | PASS: 3 przebiegi CLI, raport i zalecana decyzja R8-C01/R8-C02; brak zmian produkcyjnych, Core/DB/UI/importera/PDF. |

**Faktycznie dodany plik poza `tmp/`:** wyłącznie `docs/task_reports/TASK-062_R8_REPORT.md`. Nie wykonano `git add`, commita ani push. **Ryzyko:** G1/G2/G3 PASS przy niepełnym `issue_date` i `revision`; dla `V...` potrzebna jest decyzja co do semantyki i reprezentacji. Bez decyzji nie wprowadzać R8-C02. **STOP po R8; bez implementacji kandydatów i następnej paczki.**
