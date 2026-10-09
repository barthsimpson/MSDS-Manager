# BATCH-001_CX — raport TASK-049

Status: **DRAFT / do przeglądu Cerberusa i człowieka**. Przetworzono wyłącznie wskazany katalog `Paczka1 cx`. PDF pozostawiono bez zmian. Nie użyto OCR ani nie importowano danych.

## 1. SUMMARY

- PDF wejściowe: **37**.
- Logiczne SDS: **35**.
- Evidence JSON DRAFT: **35**.
- READABLE: **35**; PARTIALLY_READABLE: **2**; UNREADABLE: **0**.
- COMPLETE: **19**; NEEDS_REVIEW: **16**; FAILED: **2**.
- HUMAN QUESTIONS: **5/5 RESOLVED**. Decyzje są zapisane w macierzy poniżej i w [Golden Data](BATCH-001_GOLDEN_DECISIONS.md). Nie zatwierdzają całych kart; JSON nadal mają `review_status=PENDING_REVIEW`.
- Statusy przetwarzania nie są stanami Core. Wszystkie JSON mają `review_status=PENDING_REVIEW`.
- Dwa `FAILED` to czytelne karty techniczne RC 72, które nie są SDS.

## 2. PROCESSED FILES

| ID | PDF | Logical SDS | Pages | JSON | Status |
|---|---|---:|---|---|---|
| B001-P001 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | 1–12 | [`B001-P001_DOC-001.json`](json/B001-P001_DOC-001.json) | COMPLETE |
| B001-P002 | AUTO WELD 24.01.2023 rew. 2.0.pdf | 1 | 1–10 | [`B001-P002_DOC-001.json`](json/B001-P002_DOC-001.json) | COMPLETE |
| B001-P003 | AUTO WELD utwardzacz 24.01.2023 rew. 2.0.pdf | 1 | 1–10 | [`B001-P003_DOC-001.json`](json/B001-P003_DOC-001.json) | COMPLETE |
| B001-P004 | BONDICX 23.01.2023 rew. 2.0.pdf | 1 | 1–9 | [`B001-P004_DOC-001.json`](json/B001-P004_DOC-001.json) | NEEDS_REVIEW |
| B001-P005 | BONDICX 48 26.01.2021 rew. 2.0.pdf | 1 | 1–9 | [`B001-P005_DOC-001.json`](json/B001-P005_DOC-001.json) | NEEDS_REVIEW |
| B001-P006 | BONDICX 96 23.01.2023 rew. 2.0.pdf | 1 | 1–9 | [`B001-P006_DOC-001.json`](json/B001-P006_DOC-001.json) | COMPLETE |
| B001-P007 | BONDICX GEL 23.01.2023 rew. 2.0.pdf | 1 | 1–8 | [`B001-P007_DOC-001.json`](json/B001-P007_DOC-001.json) | COMPLETE |
| B001-P008 | CLEANER PROF 30.01.2019 rew. 2.0.pdf | 1 | 1–11 | [`B001-P008_DOC-001.json`](json/B001-P008_DOC-001.json) | NEEDS_REVIEW |
| B001-P009 | cx 80 SMAR LITOWY AEROZOL 24.01.2023 rew. 2.0.pdf | 1 | 1–9 | [`B001-P009_DOC-001.json`](json/B001-P009_DOC-001.json) | COMPLETE |
| B001-P010 | cx 80 Smar molibdenowy 23.01.2023 rew. 2.0.pdf | 1 | 1–7 | [`B001-P010_DOC-001.json`](json/B001-P010_DOC-001.json) | COMPLETE |
| B001-P011 | CX CLEANER PROF liquid rew. 2.0 23.01.2023.pdf | 1 | 1–11 | [`B001-P011_DOC-001.json`](json/B001-P011_DOC-001.json) | COMPLETE |
| B001-P012 | CX CLEANER PROF rew. 2.0 23.01.2023.pdf | 1 | 1–12 | [`B001-P012_DOC-001.json`](json/B001-P012_DOC-001.json) | COMPLETE |
| B001-P013 | CX80 Aktywator do klejÃ³w anaerobowych_23.01.2023 rew.2.pdf | 1 | 1–9 | [`B001-P013_DOC-001.json`](json/B001-P013_DOC-001.json) | COMPLETE |
| B001-P014 | cx80 AKTYWATOR DO KLEJÓW CYJANOAKRYLOWYCH płyn 06.04.2022 rew. 1.0.pdf | 1 | 1–10 | [`B001-P014_DOC-001.json`](json/B001-P014_DOC-001.json) | COMPLETE |
| B001-P015 | cx80 BONDICX 06 rew02 23.01.2023.pdf | 1 | 1–9 | [`B001-P015_DOC-001.json`](json/B001-P015_DOC-001.json) | NEEDS_REVIEW |
| B001-P016 | cx80 BONDICX 20 2 rew02 23.01.2023.pdf | 1 | 1–8 | [`B001-P016_DOC-001.json`](json/B001-P016_DOC-001.json) | COMPLETE |
| B001-P017 | cx80 BONDICX 22 rew02 23.01.2023.pdf | 1 | 1–9 | [`B001-P017_DOC-001.json`](json/B001-P017_DOC-001.json) | COMPLETE |
| B001-P018 | cx80 BONDICX 60 rew02 23.01.2023.pdf | 1 | 1–9 | [`B001-P018_DOC-001.json`](json/B001-P018_DOC-001.json) | COMPLETE |
| B001-P019 | cx80 BONDICX rew03 05.02.2025.pdf | 1 | 1–10 | [`B001-P019_DOC-001.json`](json/B001-P019_DOC-001.json) | NEEDS_REVIEW |
| B001-P020 | cx80 CONTACX PCC.pdf | 1 | 1–12 | [`B001-P020_DOC-001.json`](json/B001-P020_DOC-001.json) | COMPLETE |
| B001-P021 | cx80 Label Remover Aerosol 30.01.2019 rew. 3.0.pdf | 1 | 1–10 | [`B001-P021_DOC-001.json`](json/B001-P021_DOC-001.json) | NEEDS_REVIEW |
| B001-P022 | cx80 PROTECTOR METAL 30.01.2019 rew.. 2.0.pdf | 1 | 1–9 | [`B001-P022_DOC-001.json`](json/B001-P022_DOC-001.json) | NEEDS_REVIEW |
| B001-P023 | CX80 PŁYN KONSERWUJĄCO NAPRAWCZY 01.01.2023 rew. 1.0.pdf | 1 | 1–9 | [`B001-P023_DOC-001.json`](json/B001-P023_DOC-001.json) | NEEDS_REVIEW |
| B001-P024 | cx80 SILIKON PROFESSIONAL 24.01.20123 rew. 2.0.pdf | 1 | 1–7 | [`B001-P024_DOC-001.json`](json/B001-P024_DOC-001.json) | NEEDS_REVIEW |
| B001-P025 | cx80 SMAR SILIKONOWY 26.04.2021 rew. 1.0.pdf | 1 | 1–7 | [`B001-P025_DOC-001.json`](json/B001-P025_DOC-001.json) | COMPLETE |
| B001-P026 | CX80 SUCHY SMAR TEFLON_karta charakterystyki.pdf | 1 | 1–10 | [`B001-P026_DOC-001.json`](json/B001-P026_DOC-001.json) | NEEDS_REVIEW |
| B001-P027 | cx80 TIRE PROTECTOR 30.01.2019 rew. 2.0.pdf | 1 | 1–9 | [`B001-P027_DOC-001.json`](json/B001-P027_DOC-001.json) | NEEDS_REVIEW |
| B001-P028 | Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf | 1 | 1–11 | [`B001-P028_DOC-001.json`](json/B001-P028_DOC-001.json) | NEEDS_REVIEW |
| B001-P029 | CX80_ Uszczelniacz niebieski A_rew01_06082025.pdf | 1 | 1–8 | [`B001-P029_DOC-001.json`](json/B001-P029_DOC-001.json) | COMPLETE |
| B001-P030 | CX80_ Uszczelniacz niebieski B_rew01_15052025.pdf | 1 | 1–7 | [`B001-P030_DOC-001.json`](json/B001-P030_DOC-001.json) | COMPLETE |
| B001-P031 | cx80_KCH SILV WELD (23.01.2023) rew. 2.pdf | 1 | 1–9 | [`B001-P031_DOC-001.json`](json/B001-P031_DOC-001.json) | COMPLETE |
| B001-P032 | KT CX RC72-1 (1).pdf | 0 | 1 | — | FAILED |
| B001-P033 | KT CX RC72-1 (2).pdf | 0 | 1 | — | FAILED |
| B001-P034 | ON RUST 30.01.2019 rew. 2.0.pdf | 1 | 1–10 | [`B001-P034_DOC-001.json`](json/B001-P034_DOC-001.json) | NEEDS_REVIEW |
| B001-P035 | RC20G 30.01.2019 rew. 2.0.pdf | 1 | 1–10 | [`B001-P035_DOC-001.json`](json/B001-P035_DOC-001.json) | NEEDS_REVIEW |
| B001-P036 | RC43 30.01.2019 rew. 2.0.pdf | 1 | 1–11 | [`B001-P036_DOC-001.json`](json/B001-P036_DOC-001.json) | NEEDS_REVIEW |
| B001-P037 | XBRAKE CLEANER 30.01.2019 rew. 3.0.pdf | 1 | 1–10 | [`B001-P037_DOC-001.json`](json/B001-P037_DOC-001.json) | NEEDS_REVIEW |

Techniczny [manifest](BATCH-001_MANIFEST.json) zapisuje SHA-256, liczbę stron, czytelność, granice logicznych SDS i wynik dla wszystkich 37 PDF. W każdej z 35 SDS sekcja 1 rozpoczyna się na s. 1 i nie powtarza się jako początek kolejnej karty. Zakres `DOC-001` obejmuje wszystkie strony danego PDF.

## 3. CLEAR

- Nazwy 35 produktów odczytano z sekcji 1.1; w nowszym układzie wartość jest w tym samym wierszu, w starszym — w kolejnym.
- Bieżącą datę SDS i wersję odczytano z nagłówka pierwszej strony. Gdy `Data aktualizacji` jest pusta, użyto jawnej `Data utworzenia`.
- Role `Producent` i `Dostawca` zachowano oddzielnie. B001-P023 jawnie podaje obie role dla tej samej literalnej nazwy.
- Kod produktu producenta nie został odnaleziony w żadnej SDS. `UFI`, wariant nazwy i zwrot `Kod produktu nadać w miejscu jego powstania` z sekcji 13 nie są dowodem kodu producenta.

## 4. AMBIGUITIES — RESOLVED

| Issue ID | PDF | Page | Section | Field / role | Codex observation | Why ambiguous | Human resolution |
|---|---|---:|---|---|---|---|---|
| B001-Q001 | cx80 BONDICX rew03 05.02.2025.pdf | 1 | 1.3 | parties[MANUFACTURER].name | `Producent` → `CX80 POLSKA, CX80 GmbH`; pierwotnie `name.state=AMBIGUOUS`, po decyzji `name.state=FOUND` i `name.value=CX80 POLSKA`. | Niejasna reprezentacja jednej literalnej etykiety zawierającej dwie nazwy. | Rozstrzygnięto: jeden rekord `MANUFACTURER` z nazwą kanoniczną `CX80 POLSKA`, pełny literal w evidence. |
| B001-Q002 | Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf | 1 | 1.3 | parties[MANUFACTURER].name | `Producent` → `CX80 POLSKA, CX80 GmbH`; pierwotnie `name.state=AMBIGUOUS`, po decyzji `name.state=FOUND` i `name.value=CX80 POLSKA`. | Niejasna reprezentacja jednej literalnej etykiety zawierającej dwie nazwy. | Rozstrzygnięto: jeden rekord `MANUFACTURER` z nazwą kanoniczną `CX80 POLSKA`, pełny literal w evidence. |
| B001-Q003 | CX80_ Uszczelniacz niebieski A_rew01_06082025.pdf | 1 | 1.3 | parties[MANUFACTURER].name | `Producent` → `CX80 POLSKA, CX80 GmbH`; pierwotnie `name.state=AMBIGUOUS`, po decyzji `name.state=FOUND` i `name.value=CX80 POLSKA`. | Niejasna reprezentacja jednej literalnej etykiety zawierającej dwie nazwy. | Rozstrzygnięto: jeden rekord `MANUFACTURER` z nazwą kanoniczną `CX80 POLSKA`, pełny literal w evidence. |
| B001-Q004 | CX80_ Uszczelniacz niebieski B_rew01_15052025.pdf | 1 | 1.3 | parties[MANUFACTURER].name | `Producent` → `CX80 POLSKA, CX80 GmbH`; pierwotnie `name.state=AMBIGUOUS`, po decyzji `name.state=FOUND` i `name.value=CX80 POLSKA`. | Niejasna reprezentacja jednej literalnej etykiety zawierającej dwie nazwy. | Rozstrzygnięto: jeden rekord `MANUFACTURER` z nazwą kanoniczną `CX80 POLSKA`, pełny literal w evidence. |
| B001-Q005 | ON RUST 30.01.2019 rew. 2.0.pdf | 1 | 1.3 | parties.role | `Wyłączny przedstawiciel` → `SBLCore s.r.o.`; nazwa zachowana, rola `OTHER`. | Pierwotnie brakowało decyzji, czy etykieta oznacza `EU_REPRESENTATIVE`. | Rozstrzygnięto: `OTHER`; nie mapować automatycznie na `EU_REPRESENTATIVE`. |

Wszystkie pięć wątpliwości rozstrzygnął człowiek. Pozostałe rozbieżności nazw plików i treści rozstrzygnięto zgodnie z TASK-049 na korzyść treści SDS; zostały odnotowane poniżej.

## 5. NOT FOUND

| PDF | Logical SDS | Expected field | Search area | Result |
|---|---|---|---|---|
| ALUCYNK 23.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| AUTO WELD 24.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| AUTO WELD utwardzacz 24.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| BONDICX 23.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| BONDICX 48 26.01.2021 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| BONDICX 96 23.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| BONDICX GEL 23.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CLEANER PROF 30.01.2019 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx 80 SMAR LITOWY AEROZOL 24.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx 80 Smar molibdenowy 23.01.2023 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX CLEANER PROF liquid rew. 2.0 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX CLEANER PROF rew. 2.0 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX80 Aktywator do klejÃ³w anaerobowych_23.01.2023 rew.2.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 AKTYWATOR DO KLEJÓW CYJANOAKRYLOWYCH płyn 06.04.2022 rew. 1.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 BONDICX 06 rew02 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 BONDICX 20 2 rew02 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 BONDICX 22 rew02 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 BONDICX 60 rew02 23.01.2023.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 BONDICX rew03 05.02.2025.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 CONTACX PCC.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 Label Remover Aerosol 30.01.2019 rew. 3.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 PROTECTOR METAL 30.01.2019 rew.. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX80 PŁYN KONSERWUJĄCO NAPRAWCZY 01.01.2023 rew. 1.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 SILIKON PROFESSIONAL 24.01.20123 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 SMAR SILIKONOWY 26.04.2021 rew. 1.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX80 SUCHY SMAR TEFLON_karta charakterystyki.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80 TIRE PROTECTOR 30.01.2019 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX80_ Uszczelniacz niebieski A_rew01_06082025.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| CX80_ Uszczelniacz niebieski B_rew01_15052025.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| cx80_KCH SILV WELD (23.01.2023) rew. 2.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| ON RUST 30.01.2019 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| RC20G 30.01.2019 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| RC43 30.01.2019 rew. 2.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |
| XBRAKE CLEANER 30.01.2019 rew. 3.0.pdf | DOC-001 | `manufacturer_product_code` | Sekcja 1.1 i jawne oznaczenia kodu w SDS | `NOT_FOUND` |

W B001-P008 i B001-P026 wyrażenie „Kod produktu nadać w miejscu jego powstania” w sekcji 13 dotyczy odpadów. Karty techniczne RC 72 nie są logicznymi SDS, więc pól SDS nie oznaczono dla nich jako `NOT_FOUND`.

## 6. UNREADABLE / PARTIALLY READABLE

| PDF | Pages | Problem | Impact |
|---|---|---|---|
| CLEANER PROF 30.01.2019 rew. 2.0.pdf | 1–11 | Warstwa tekstowa rozdziela znaki w części polskich słów. | `PARTIALLY_READABLE`; identyfikacja i metadane na s. 1 są czytelne. |
| CX80 SUCHY SMAR TEFLON_karta charakterystyki.pdf | 1–10 | Warstwa tekstowa rozdziela znaki w części polskich słów. | `PARTIALLY_READABLE`; identyfikacja i metadane na s. 1 są czytelne. |

Brak stron `UNREADABLE`. OCR nie był używany.

## 7. NEW PATTERNS / ALIAS CANDIDATES

Wszystkie wpisy mają status **CANDIDATE**. Nie zmieniono `SDS-ALIAS-001` i nie aktywowano aliasów.

| Candidate ID | PDF | Page | Canonical target | Observed label / pattern | Context |
|---|---|---:|---|---|---|
| B001-C001 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | `SDS_01_01_PRODUCT_IDENTIFIER / product_name` | `Identyfikator produktu` | Wartość w tym samym wierszu. |
| B001-C002 | BONDICX 48 26.01.2021 rew. 2.0.pdf | 1 | `SDS_DOCUMENT_METADATA / issue_date` | `Data utworzenia` | Użyta, gdy Data aktualizacji jest pusta. |
| B001-C003 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | `SDS_DOCUMENT_METADATA / issue_date` | `Data aktualizacji` | Nagłówek; osobna etykieta względem seeda. |
| B001-C004 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | `SDS_DOCUMENT_METADATA / revision` | `Numer wersji` | Nagłówek, często obok daty. |
| B001-C005 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | `SDS_01_03_SUPPLIER_DETAILS / MANUFACTURER` | `Producent` | Rola w sekcji 1.3. |
| B001-C006 | ALUCYNK 23.01.2023 rew. 2.0.pdf | 1 | `SDS_01_03_SUPPLIER_DETAILS / party.name` | `Nazwa lub nazwa handlowa` | Tylko w kontekście poprzedzającej roli. |
| B001-C007 | CLEANER PROF 30.01.2019 rew. 2.0.pdf | 1 | `SDS_01_03_SUPPLIER_DETAILS / MANUFACTURER` | `producent:` | Starszy układ; rola i nazwa w jednym wierszu. |
| B001-C008 | CX80 PŁYN KONSERWUJĄCO NAPRAWCZY 01.01.2023 rew. 1.0.pdf | 1 | `SDS_01_03_SUPPLIER_DETAILS / SUPPLIER` | `Dostawca` | Obok osobnego Producent. |
| B001-C009 | ON RUST 30.01.2019 rew. 2.0.pdf | 1 | `SDS_01_03_SUPPLIER_DETAILS / OTHER` | `Wyłączny przedstawiciel` | Decyzja B001-Q005: OTHER; alias pozostaje CANDIDATE. |

## 8. LAYOUT DIFFERENCES

- Nowszy układ SBLCore: nazwa produktu w wierszu `1.1` i daty w powtarzalnym nagłówku. Starsze B001-P008 i B001-P026: nazwa w następnym wierszu i numer strony `n/m` przy metadanych.
- B001-P005, B001-P014 i B001-P025 mają pustą `Data aktualizacji`. W B001-P029 i B001-P030 data oraz numer wersji są w osobnych wierszach.
- W B001-P019, B001-P028, B001-P029 i B001-P030 jedna etykieta `Producent` poprzedza dwie nazwy. B001-P023 ma osobne role `Dostawca` i `Producent`, a B001-P034 dodatkowo `Wyłączny przedstawiciel`.
- Wszystkie SDS mają jeden początek sekcji 1. B001-P032 i B001-P033 są kartami technicznymi bez struktury SDS.

### Różnice między nazwą pliku a SDS

| ID | Nazwa pliku | Treść SDS i skutek |
|---|---|---|
| B001-P004, P015 | Pierwszy plik pomija wariant 06. | `BONDICX 06` na s. 1 `1.1`; oba PDF mają identyczny SHA-256. |
| B001-P005 | `26.01.2021 rew. 2.0` | `Data utworzenia 26.02.2021`, `Numer wersji 1.0` na s. 1. |
| B001-P019 | `BONDICX` bez wariantu. | `BONDICX 01` na s. 1 `1.1`. |
| B001-P021, P022, P027, P034–P037 | Data 2019. | Aktualizacja 23.01.2023 lub 24.01.2023 na s. 1. |
| B001-P023 | `01.01.2023` | Aktualizacja 02.01.2023 na s. 1. |
| B001-P024 | Rok `20123` | Aktualizacja 24.01.2023 na s. 1. |
| B001-P028 | `XBRAKE CLEANER` | `XBRAKE CLEANER liquid` na s. 1 `1.1`. |
| B001-P013 | Znaki `klejÃ³w` w nazwie pliku. | W SDS czytelne `Aktywator do klejów anaerobowych` na s. 1 `1.1`. |

## 9. QUESTIONS FOR HUMAN — RESOLVED

### B001-Q001
PDF: cx80 BONDICX rew03 05.02.2025.pdf
PAGE: 1
SECTION: 1.3
CODEX OBSERVATION: `Producent` → `CX80 POLSKA, CX80 GmbH`.
QUESTION: Czy zapisać dwa odrębne podmioty MANUFACTURER czy jedną złożoną nazwę literalną?
HUMAN DECISION:
- Jeden rekord MANUFACTURER; `name.value=CX80 POLSKA`, `state=FOUND`; literal `CX80 POLSKA, CX80 GmbH` w evidence/source_text.
STATUS: RESOLVED

### B001-Q002
PDF: Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
PAGE: 1
SECTION: 1.3
CODEX OBSERVATION: `Producent` → `CX80 POLSKA, CX80 GmbH`.
QUESTION: Czy zapisać dwa odrębne podmioty MANUFACTURER czy jedną złożoną nazwę literalną?
HUMAN DECISION:
- Jeden rekord MANUFACTURER; `name.value=CX80 POLSKA`, `state=FOUND`; literal `CX80 POLSKA, CX80 GmbH` w evidence/source_text.
STATUS: RESOLVED

### B001-Q003
PDF: CX80_ Uszczelniacz niebieski A_rew01_06082025.pdf
PAGE: 1
SECTION: 1.3
CODEX OBSERVATION: `Producent` → `CX80 POLSKA, CX80 GmbH`.
QUESTION: Czy zapisać dwa odrębne podmioty MANUFACTURER czy jedną złożoną nazwę literalną?
HUMAN DECISION:
- Jeden rekord MANUFACTURER; `name.value=CX80 POLSKA`, `state=FOUND`; literal `CX80 POLSKA, CX80 GmbH` w evidence/source_text.
STATUS: RESOLVED

### B001-Q004
PDF: CX80_ Uszczelniacz niebieski B_rew01_15052025.pdf
PAGE: 1
SECTION: 1.3
CODEX OBSERVATION: `Producent` → `CX80 POLSKA, CX80 GmbH`.
QUESTION: Czy zapisać dwa odrębne podmioty MANUFACTURER czy jedną złożoną nazwę literalną?
HUMAN DECISION:
- Jeden rekord MANUFACTURER; `name.value=CX80 POLSKA`, `state=FOUND`; literal `CX80 POLSKA, CX80 GmbH` w evidence/source_text.
STATUS: RESOLVED

### B001-Q005
PDF: ON RUST 30.01.2019 rew. 2.0.pdf
PAGE: 1
SECTION: 1.3
CODEX OBSERVATION: `Wyłączny przedstawiciel` → `SBLCore s.r.o.`; zachowano rolę `OTHER`.
QUESTION: Czy zatwierdzoną rolą jest `EU_REPRESENTATIVE`, czy pozostaje `OTHER`?
HUMAN DECISION:
- `MANUFACTURER.name.value=CX80 POLSKA`; `SBLCore s.r.o.` ma rolę `OTHER`; oba literalne zapisy zachowane w evidence/source_text. Bez automatycznego mapowania na EU_REPRESENTATIVE.
STATUS: RESOLVED

## 10. HUMAN ANSWER MATRIX

| Issue ID | Human decision | Evidence page/section | Expected JSON result | Decision status |
|---|---|---|---|---|
| B001-Q001 | Jeden `MANUFACTURER = CX80 POLSKA`; literal `CX80 POLSKA, CX80 GmbH` w evidence | 1 / 1.3 | `parties[0].role=MANUFACTURER`; `name.value="CX80 POLSKA"`; `state=FOUND`; raw `source_text` | RESOLVED |
| B001-Q002 | Jeden `MANUFACTURER = CX80 POLSKA`; literal `CX80 POLSKA, CX80 GmbH` w evidence | 1 / 1.3 | `parties[0].role=MANUFACTURER`; `name.value="CX80 POLSKA"`; `state=FOUND`; raw `source_text` | RESOLVED |
| B001-Q003 | Jeden `MANUFACTURER = CX80 POLSKA`; literal `CX80 POLSKA, CX80 GmbH` w evidence | 1 / 1.3 | `parties[0].role=MANUFACTURER`; `name.value="CX80 POLSKA"`; `state=FOUND`; raw `source_text` | RESOLVED |
| B001-Q004 | Jeden `MANUFACTURER = CX80 POLSKA`; literal `CX80 POLSKA, CX80 GmbH` w evidence | 1 / 1.3 | `parties[0].role=MANUFACTURER`; `name.value="CX80 POLSKA"`; `state=FOUND`; raw `source_text` | RESOLVED |
| B001-Q005 | `MANUFACTURER = CX80 POLSKA`; `Wyłączny przedstawiciel = SBLCore s.r.o.` ma rolę `OTHER` | 1 / 1.3 | `parties[0].role=MANUFACTURER`, `name.value="CX80 POLSKA"`; `parties[1].role=OTHER`, `name.value="SBLCore s.r.o."`; oba `FOUND` i raw `source_text` | RESOLVED |

Pięć decyzji człowieka zostało zapisanych w odpowiednich JSON i w [Golden Data](BATCH-001_GOLDEN_DECISIONS.md). JSON pozostają szkicami dowodowymi, bez decyzji PRODUCT, CURRENT/ARCHIVED lub BHP.
