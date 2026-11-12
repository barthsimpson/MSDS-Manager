# BATCH-002 SYLGARD — macierz diagnostyczna TASK-061

**Status:** obserwacje robocze, bez zatwierdzenia operatora. `DOC-001` i zakresy stron poniżej są **propozycją po ręcznym przeglądzie warstwy tekstowej**, nie wynikiem segmentacji TDR-012. W każdym PDF widoczny jest jeden ciąg stron 1–N z sekcjami 1–16; runtime nie potwierdził liczby logicznych SDS. Cytaty zachowują znak `�` z odczytu pypdf. Pełne surowe DTO jest w `RAW_MINIMAL_EXTRACTOR.json`.

Kolumna `state` opisuje **stan kontraktowy pola**. `UNASSIGNED` oznacza, że minimalny extractor nie wytworzył stanów SDS-JSON-001; żadne jego pole nie może być oznaczone `FOUND` bez evidence. `validation_result` jest oceną diagnostyczną po odczycie, a nie wynikiem walidatora TDR-012. `approved_correction` pozostaje puste do przyszłej decyzji człowieka.

## B002-01

`source_pdf`: `Sylgard 160 A rew. 5.0 (2021.10.28).pdf` · `sha256`: `f078434cfe90d09238b81cf83f2df846f46ac93107a586a29e8a6db18a2aea72` · `document_key`: `DOC-001` (PROPOSAL) · `page_range`: 1–24 (PROPOSAL).

| section/field | extracted_value (raw) | state | evidence (page/section/source_text) | validation_result | operator_review_needed | observation / approved_correction |
|---|---|---|---|---|---|---|
| 1.1/product_name | `��Znak towarowy The Dow Chemical Company (�DOW�) lub sp�ek` | UNASSIGNED | 1 / 1.1 / `Nazwa wyrobu: SYLGARD� 160 Silicone Elastomer-Part A` | FAIL: raw value is not product | YES | First-page trademark footer was taken as name; correction: — |
| 1.1/manufacturer_product_code | `odradzane` | UNASSIGNED | 1 / 1.2 / `... zastosowania odradzane` | FAIL: word from heading is not code | YES | No justified product code; correction: — |
| header/issue_date | null | UNASSIGNED | 1 / header / `Aktualizacja: 2021/10/28` | BLOCKED: date not extracted | YES | Source date is visible; correction: — |
| header/revision | `5.0` | UNASSIGNED | 1 / header / `Wersja: 5.0` | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 1.3/parties | `manufacturer_name=null` | UNASSIGNED | 1 / 1.3 / `Dane dotycz�ce dostawcy karty charakterystyki ... DOW POLSKA SP.Z O.O.` | BLOCKED: supplier role not modeled | YES | Do not equate supplier with manufacturer; correction: — |
| 2.1/classification_clp | `Zagro�enie d�ugotrwa�e (przewlek�e) dla �rodowiska wodnego - Kategoria 3 - H412` | UNASSIGNED | 1 / 2.1 / same source phrase | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success only; correction: — |
| 3.2/components | 0 rows | UNASSIGNED | 2 / 3.2 / `Nr CAS 14808-60-7 ... Kwarc STOT RE 1; H372` | FAIL: source contains composition | YES | Layout uses `Nr CAS`, not `CAS:`; correction: — |

## B002-02

`source_pdf`: `Sylgard 160 part B rew. 5.0 (2022.22.01).pdf` · `sha256`: `de3640fd8e66dfa9bc8c313cfa90844f0c7e61a09a20f918ae0de296f69d4d3d` · `document_key`: `DOC-001` (PROPOSAL) · `page_range`: 1–25 (PROPOSAL).

| section/field | extracted_value (raw) | state | evidence (page/section/source_text) | validation_result | operator_review_needed | observation / approved_correction |
|---|---|---|---|---|---|---|
| 1.1/product_name | `��Znak towarowy The Dow Chemical Company (�DOW�) lub sp�ek` | UNASSIGNED | 1 / 1.1 / `Nazwa wyrobu: SYLGARD� 160 Silicone Elastomer-Part B` | FAIL | YES | Part B visible in PDF; correction: — |
| 1.1/manufacturer_product_code | `odradzane` | UNASSIGNED | 1 / 1.2 / `... zastosowania odradzane` | FAIL | YES | Heading fragment mistaken for code; correction: — |
| header/issue_date | null | UNASSIGNED | 1 / header / `Aktualizacja: 2022/11/01` | BLOCKED: date not extracted | YES | PDF says **2022-11-01**; filename `2022.22.01` is invalid and disagrees; correction: — |
| header/revision | `5.0` | UNASSIGNED | 1 / header / `Wersja: 5.0` | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 1.3/parties | `manufacturer_name=null` | UNASSIGNED | 1 / 1.3 / `Dane dotycz�ce dostawcy karty charakterystyki ... DOW POLSKA SP.Z O.O.` | BLOCKED | YES | Supplier only shown here; manufacturer unresolved; correction: — |
| 2.1/classification_clp | `Szkodliwe dzia�anie na rozrodczo�� - Kategoria 1B - H360F` | UNASSIGNED | 1 / 2.1 / same source phrase | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 2.2/hazard_statements | [] | UNASSIGNED | 2 / 2.2 / `H360F Mo�e dzia�a� szkodliwie na p�odno��.` | FAIL: missed alphanumeric H code | YES | `_h_codes` accepts three digits only; correction: — |

## B002-03

`source_pdf`: `sylgard-170-silicone-rew. 4.1_part-A_2021.10.26.pdf` · `sha256`: `cbb38ba8ff6cb9bbfb8ab2e9b91b9476dfcb21a467f05c292ba2022c31c4bc45` · `document_key`: `DOC-001` (PROPOSAL) · `page_range`: 1–24 (PROPOSAL).

| section/field | extracted_value (raw) | state | evidence (page/section/source_text) | validation_result | operator_review_needed | observation / approved_correction |
|---|---|---|---|---|---|---|
| 1.1/product_name | `��Znak towarowy The Dow Chemical Company (�DOW�) lub sp�ek` | UNASSIGNED | 1 / 1.1 / `Nazwa wyrobu: SYLGARD� 170 Silicone Elastomer Part A` | FAIL | YES | Part A visible in PDF; correction: — |
| 1.1/manufacturer_product_code | `odradzane` | UNASSIGNED | 1 / 1.2 / `... zastosowania odradzane` | FAIL | YES | No justified code; correction: — |
| header/issue_date | null | UNASSIGNED | 1 / header / `Aktualizacja: 2021/10/26` | BLOCKED | YES | Source date visible; correction: — |
| header/revision | `4.1` | UNASSIGNED | 1 / header / `Wersja: 4.1` | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 1.3/parties | `manufacturer_name=null` | UNASSIGNED | 1 / 1.3 / `Dane dotycz�ce dostawcy karty charakterystyki ... DOW POLSKA SP.Z O.O.` | BLOCKED | YES | Manufacturer unresolved; correction: — |
| 2.1/classification_clp | `Zagro�enie d�ugotrwa�e (przewlek�e) dla �rodowiska wodnego - Kategoria 3 - H412` | UNASSIGNED | 1 / 2.1 / same source phrase | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 3.2/components | 0 rows | UNASSIGNED | 2 / 3.2 / `Nr CAS 14808-60-7 ... Kwarc STOT RE 1; H372` | FAIL | YES | Composition rows missed; correction: — |

## B002-04

`source_pdf`: `sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf` · `sha256`: `add472a1e9d5b3cd09a4df7da4670398883ddf92df603684a671fe5df6feb5a9` · `document_key`: `DOC-001` (PROPOSAL) · `page_range`: 1–20 (PROPOSAL).

| section/field | extracted_value (raw) | state | evidence (page/section/source_text) | validation_result | operator_review_needed | observation / approved_correction |
|---|---|---|---|---|---|---|
| 1.1/product_name | `��Znak towarowy The Dow Chemical Company (�DOW�) lub sp�ek` | UNASSIGNED | 1 / 1.1 / `Nazwa wyrobu: SYLGARD� 170 Silicone Elastomer Part B` | FAIL | YES | Part B visible in PDF; correction: — |
| 1.1/manufacturer_product_code | `odradzane` | UNASSIGNED | 1 / 1.2 / `... zastosowania odradzane` | FAIL | YES | No justified code; correction: — |
| header/issue_date | null | UNASSIGNED | 1 / header / `Aktualizacja: 2022/11/07` | BLOCKED | YES | PDF says **2022-11-07**, filename suggests 2021-10-26; correction: — |
| header/revision | `7.0` | UNASSIGNED | 1 / header / `Wersja: 7.0` | OBSERVED_MATCH, no automated evidence | YES | Filename only says `rew 7`; correction: — |
| 1.3/parties | `manufacturer_name=null` | UNASSIGNED | 1 / 1.3 / `Dane dotycz�ce dostawcy karty charakterystyki ... DOW POLSKA SP.Z O.O.` | BLOCKED | YES | Manufacturer unresolved; correction: — |
| 2.1/classification_clp | `Nie jest substancj� ani mieszanin� niebezpieczn� ...` | UNASSIGNED | 1 / 2.1 / `Nie jest substancj� ani mieszanin� niebezpieczn� w rozumieniu rozporz�dzenia (WE) 1272/2008.` | OBSERVED_MATCH, no automated evidence | YES | Diagnostic success; correction: — |
| 3.2/components | 0 rows | UNASSIGNED | 2 / 3.2 / `Nr CAS 14808-60-7 ... Kwarc STOT RE 1; H372` | FAIL | YES | Composition rows missed; correction: — |

## Struktura, błędy i kandydaci

Odczyt tekstu pokazuje sekcje 1–16 w każdym pliku; sekcje 1–2 zaczynają się na s. 1, sekcja 3 na s. 2. Podsekcje 1.1, 1.2, 1.3 i 2.1, 2.2, 2.3 są widoczne na s. 1 lub s. 2. To obserwacja ręczna, nie wynik detektora. Odczyt pypdf zawiera zastępcze `�` w polskich znakach.

Potencjalne aliasy do **osobnej oceny CANDIDATE**: `Nazwa wyrobu` (1.1, nazwa produktu), `Aktualizacja` (nagłówek, data), `Zastosowania zidentyfikowane` (1.2, zastosowanie), `Nr CAS` (3.2, identyfikator składnika). `Wersja` ma już seed A-006 ze statusem CANDIDATE. Etykieta `Dane dotyczące dostawcy karty charakterystyki` określa kontekst dostawcy; nie zatwierdza automatycznie producenta. Żaden alias nie został aktywowany.

Zalecany przyszły zakres implementacji po osobnej autoryzacji: segmentacja logicznych kart, rozpoznawanie sekcji i podsekcji, dopasowanie zatwierdzonych aliasów, dowody strona/sekcja/tekst, walidacja strukturalna i semantyczna, obsługa układu tabeli 3.2 oraz test regresyjny na tym identycznym PDF Part A. W tym tasku nie zmieniono reguł.
