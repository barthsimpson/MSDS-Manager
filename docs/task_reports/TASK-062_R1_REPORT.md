# TASK-062-R1 — etap 1: macierz aliasów do decyzji Architekta

**Status:** PROPOSAL / PENDING ARCHITECT REVIEW, 2026-11-10. Pracę wykonano w `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, na lokalnym `main` `f97c1e28996ace2087f774aeabec4ca7a9bc91cd`. Przed zapisem raportu `git status --short --branch` pokazywał tylko zastane nieśledzone `data/`, dokumenty TASK/DYSP i BATCH-002; `main` był równy `origin/main`. Nie zmieniono źródłowych PDF.

## Podstawa i źródła

`TDR-012` §5 wymaga użycia wyłącznie aliasów `ACTIVE`, a `SDS-ALIAS-001` §§4, 6–9 przewiduje `CANDIDATE → APPROVED → test regresyjny → ACTIVE`. W bibliotece jest sześć seedów A-001…A-006 ze statusem `CANDIDATE`, zero `ACTIVE`. `SDS-SCHEMA-001` lokuje identyfikator produktu w 1.1, podmioty w 1.3. `SDS-JSON-001` przewiduje `product.product_name`, opcjonalny `manufacturer_product_code`, `document_metadata.issue_date/revision` i `parties[]` z rozłącznymi rolami. `FOUND` wymaga krótkiego dowodu z właściwego logicznego SDS; nazwa PDF nie jest dowodem. TASK-062 pozostaje BLOCKED do odrębnej decyzji i regresji. Raport TASK-062 odczytano z lokalnej referencji gałęzi integracyjnej jako kontekst historyczny, bez użycia tego worktree jako źródła kodu.

Źródła odczytano przez istniejące `.venv\Scripts\python.exe -B` i `pypdf.PdfReader.extract_text(extraction_mode="layout")`, bez zapisu plików. OPEX: `data/sds/Paczki/paczka 14 farba/T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf`, 25 stron, SHA-256 `2de8f263567f82860fc229adc11a6fad20c4c65ab3972af5288e72c968905d3b`. SYLGARD: cztery PDF z `data/sds/Paczki/paczka2 sylgard/`, SHA-256 i strony poniżej. Warstwa tekstowa zastępuje część znaków symbolem `�`; cytaty zachowują ten znak i **nie potwierdzają** jego właściwej postaci graficznej. Widoczność etykiety i powiązanie wartości oceniono osobno; w razie braku wiarygodnego powiązania przyszły extractor powinien użyć `AMBIGUOUS` albo `UNREADABLE`, nigdy zgadywać.

## OPEX — istniejące seedy A-001…A-006

| ID / literalna etykieta | Literalna wartość i dowód (strona, sekcja) | Pole / rola; widoczność i powiązanie | Ryzyko; oczekiwany wynik po zatwierdzeniu reguły | Propozycja i regresja |
|---|---|---|---|---|
| A-001 `Nazwa produktu` | `Nazwa produktu : OPEX� Acrylic Clear Metal Lacquer` (s. 1, 1.1) | `product.product_name`; etykieta widoczna, wartość w tym samym wierszu układu | Odczyt bez układu przestawia wiersze; nie naprawiać automatycznie znaku `�`. Oczekiwane: nazwa z 1.1, z dowodem lub `UNREADABLE` dla nierozstrzygniętego znaku. | **APPROVE PROPOSED** dla etykiety; test: ten sam wiersz 1.1, brak przejęcia pierwszego wiersza strony. |
| A-002 `Kod produktu` | `Kod produktu : T82C13` (s. 1, 1.1) | `product.manufacturer_product_code`; etykieta i wiązanie w tym samym wierszu | `T82C13` jest też w nagłówku; nie opierać odczytu wyłącznie na nim. Oczekiwane: `T82C13` z 1.1. | **APPROVE PROPOSED**; test: kod tylko po etykiecie w 1.1, brak kodu → `NOT_FOUND`. |
| A-003 `Mfg. in U.S.A and exported by` | Etykieta i następny wiersz `The Sherwin-Williams Company` (s. 1, 1.3) | `parties[].name`, rola `MANUFACTURER_EXPORTER`; etykieta widoczna, nazwa w następnym wierszu | Nie włączyć adresu do nazwy ani nie zastąpić tej roli `SUPPLIER`. Oczekiwany osobny rekord podmiotu. | **APPROVE PROPOSED**; test: następny wiersz nazwy, stop przed adresem i następną rolą. |
| A-004 `EU Only Representative` | `EU Only Representative: Valspar B.V.` (s. 1, 1.3) | `parties[].name`, rola `EU_REPRESENTATIVE`; etykieta i wartość w jednym wierszu | Nie utożsamiać z producentem/eksporterem. Oczekiwany drugi rekord podmiotu. | **APPROVE PROPOSED**; test: dwa osobne rekordy 1.3, bez zamiany ról. |
| A-005 `Data wydania/Data aktualizacji` | `Data wydania/Data aktualizacji : 25, Listopad, 2022` obok `Data poprzedniego ... :18, Cze, 2022` (s. 1 i 25, stopka) | `document_metadata.issue_date`; etykieta widoczna, bieżąca wartość po własnym dwukropku | Obie daty są blisko; pobranie daty poprzedniego wydania byłoby błędem. Oczekiwane `2022-11-25` tylko po zatwierdzeniu reguły daty i porównaniu obu stopek. | **REVIEW** reguły wiązania: od etykiety do następnej etykiety `Data poprzedniego`, normalizacja polskiego miesiąca; test obu dat i s. 1/25. |
| A-006 `Wersja` | `Wersja :8` w tej samej stopce (s. 1 i 25) | `document_metadata.revision`; etykieta widoczna, wartość po dwukropku | Stopka zawiera też `1/25` albo `25/25`; nie przyjąć numeru strony za rewizję. Oczekiwane `8`. | **APPROVE PROPOSED** z lokalizacją nagłówek/stopka logicznego SDS; test `8` ≠ `1/25`. |

`Dostawca` na s. 1 OPEX występuje ponadto w podsekcji **1.4** obok numeru telefonu. To negatywny przykład: nie jest dowodem nazwy ani roli podmiotu 1.3.

## SYLGARD — cztery rzeczywiste SDS, bez wnioskowania z nazwy pliku

W każdej komórce podano literalną etykietę i wartość z **s. 1**, związaną ze wskazanym polem. Sekcja 1.1 zawiera powtórzoną nazwę produktu, nagłówek zawiera datę i wersję, a sekcja 1.3 zawiera blok podmiotu. Nazwy plików służą tylko do identyfikacji źródła.

| ID / SHA-256 / strony | `Nazwa wyrobu` → `product_name` (1.1) | `Aktualizacja` → `issue_date` (nagłówek) | `Wersja` → `revision` (nagłówek) | 1.3 podmiot / rola; ryzyko i oczekiwany wynik |
|---|---|---|---|---|
| B002-01 / `f078434cfe90d09238b81cf83f2df846f46ac93107a586a29e8a6db18a2aea72` / 24 | `Nazwa wyrobu: SYLGARD� 160 Silicone Elastomer-Part A` | `Aktualizacja: 2021/10/28` | `Wersja: 5.0` | `1.3 Dane dotycz�ce dostawcy karty charakterystyki` → `IDENTYFIKACJA FIRMY` → `DOW POLSKA SP.Z O.O.`; kandydat `SUPPLIER`, **nie** dowód `MANUFACTURER`. `Data ostatniego wydania: 2020/06/19` nie jest bieżącą datą. |
| B002-02 / `de3640fd8e66dfa9bc8c313cfa90844f0c7e61a09a20f918ae0de296f69d4d3d` / 25 | `Nazwa wyrobu: SYLGARD� 160 Silicone Elastomer-Part B` | `Aktualizacja: 2022/11/01` | `Wersja: 5.0` | Ten sam blok 1.3: `DOW POLSKA SP.Z O.O.` jako kandydat `SUPPLIER`; `Data ostatniego wydania: 2022/03/30` jest historyczna. Nazwa PDF `2022.22.01` nie zmienia wartości z SDS. |
| B002-03 / `cbb38ba8ff6cb9bbfb8ab2e9b91b9476dfcb21a467f05c292ba2022c31c4bc45` / 24 | `Nazwa wyrobu: SYLGARD� 170 Silicone Elastomer Part A` | `Aktualizacja: 2021/10/26` | `Wersja: 4.1` | Ten sam blok 1.3: `DOW POLSKA SP.Z O.O.` jako kandydat `SUPPLIER`; `Data ostatniego wydania: 2021/09/15` jest historyczna. |
| B002-04 / `add472a1e9d5b3cd09a4df7da4670398883ddf92df603684a671fe5df6feb5a9` / 20 | `Nazwa wyrobu: SYLGARD� 170 Silicone Elastomer Part B` | `Aktualizacja: 2022/11/07` | `Wersja: 7.0` | Ten sam blok 1.3: `DOW POLSKA SP.Z O.O.` jako kandydat `SUPPLIER`; `Data ostatniego wydania: 2020/10/29` jest historyczna. Nazwa PDF sugeruje inną datę i nie jest dowodem. |

Etykiety i wartości są widoczne w warstwie tekstowej z zachowaniem układu. Powiązanie `Nazwa wyrobu` z nazwą jest mocniejsze w 1.1 niż w powtarzalnym nagłówku. `Aktualizacja` i `Wersja` są w nagłówku właściwej karty; nie wolno przenosić ich między logicznymi SDS. `DOW POLSKA SP.Z O.O.` występuje pod nagłówkiem dostawcy karty, więc **nie wolno** wnioskować z samej nazwy firmy o producencie. Pole kodu producenta pozostaje opcjonalne; występujące w niektórych źródłach `UFI` nie jest jego dowodem. Dla nierozstrzygniętego kodu nie podstawiać `odradzane` z nagłówka 1.2 (błąd starego extractora z TASK-061).

## Pakiet decyzji i plan regresji

| Wariant / reguła do decyzji | Propozycja | Reguła wiązania i test na realnym PDF |
|---|---|---|
| `Nazwa wyrobu` → nazwa produktu | **APPROVE PROPOSED** jako nowy alias 1.1 | Wartość po dwukropku w 1.1; nagłówek tej samej logicznej karty jako kontrola zgodności. Test B002-01…04 Part A/B; bez wykorzystania nazwy PDF. Znak `�` wymaga oceny człowieka przed kanonizacją. |
| `Aktualizacja` → bieżąca data SDS | **APPROVE PROPOSED** jako nowy alias metadanych | Wartość po etykiecie w nagłówku tej karty, odrębna od `Data ostatniego wydania`. Test B002-02 `2022-11-01` i B002-04 `2022-11-07` mimo nazw plików. |
| `Wersja` A-006 również w nagłówku SYLGARD | **APPROVE PROPOSED** rozszerzenie reguły lokalizacji, bez nowego aliasu | OPEX: stopka `8`; SYLGARD: nagłówek `5.0/4.1/7.0`; numer strony nigdy rewizją. |
| `Dane dotyczące dostawcy…` / `IDENTYFIKACJA FIRMY` → nazwa w 1.3 | **REVIEW** przed dopuszczeniem roli `SUPPLIER` | Proponowana reguła kontekstowa: tylko w 1.3, po `IDENTYFIKACJA FIRMY`, pierwszy wiersz nazwy przed adresem; nigdy automatyczny `MANUFACTURER`. Test czterech SYLGARD oraz negatywny `Dostawca` w 1.4 OPEX. |
| A-005 data OPEX | **REVIEW** | Jawnie zatwierdzić granicę wartości przed etykietą poprzedniego wydania i normalizację miesiąca; test stopek s. 1/25. |

Najmniejszy sensowny **pakiet do decyzji** dla identyfikacyjnego PoC na OPEX + SYLGARD: A-001…A-004 i A-006, nowy `Nazwa wyrobu`, nowy `Aktualizacja`, oraz rozstrzygnięcie A-005 i kontekstowej roli `SUPPLIER`. Bez dwóch ostatnich decyzji pipeline może co najwyżej zwrócić jawny stan niepewności dla części dat/ról; nie wolno obiecać kompletnej ekstrakcji. A-002 jest potrzebny dla OPEX, ale brak kodu w SYLGARD jest dopuszczalny. Żaden z tych wpisów **nie jest dziś APPROVED ani ACTIVE**.

Plan focused regresji po decyzji Architekta: (1) OPEX s. 1/25 — sześć seedów, dwie role i data bieżąca kontra poprzednia; (2) B002-01…04 — nazwa/Part/data/wersja z treści, role 1.3, brak kodu/UFI; (3) B002-02 i B002-04 — sprzeczna nazwa PDF nie zmienia wartości; (4) prawdziwy 3M DP-490 — osobne zakresy i metadane każdej logicznej karty, bez założenia 1 PDF = 1 SDS; (5) `FOUND` bez evidence oraz alias nieaktywny/nieznany są odrzucane. To **plan**, nie uruchomione testy TASK-062.

## Kryteria i STOP

| Kryterium | Wynik |
|---|---|
| R1-1 | PASS — pierwotny katalog, lokalny `main` `f97c1e2`; tylko raport jest nowym zapisem. |
| R1-2 | PASS z ograniczeniem glifów — A-001…A-006 sprawdzone na rzeczywistym OPEX, s. 1/25. |
| R1-3 | PASS na poziomie obserwacji — cztery PDF SYLGARD, dowody z s. 1, bez odczytu domenowego z nazw. |
| R1-4 | PASS — role i daty rozdzielone; nierozstrzygnięte powiązania oznaczono `REVIEW`. |
| R1-5 | PASS — konkretne propozycje, reguły do zatwierdzenia i plan regresji. |
| R1-6 | PASS — bez zmian aliasów, kodu, Core, DB, UI i PDF; brak implementacji extractora. |

**Decyzje oczekiwane od Architekta:** zatwierdzić albo odrzucić wskazane aliasy A-001…A-006 i dwa warianty SYLGARD, rozstrzygnąć regułę daty A-005 oraz mapowanie bloku firmy z 1.3 na `SUPPLIER`. Potem dopiero etap drugi TASK-062-R1: zapis zatwierdzonych aliasów/reguł, regresja i ewentualne ACTIVE. **STOP.**
