# TASK-061 — BATCH-002 SYLGARD: raport częściowy i STOP

**Data:** 2026-11-09. **Tryb:** odczyt i diagnostyka bez importu, zmian kodu, DB i Git. **Wynik:** 4/4 PDF czytelne tekstowo; brak wykonawczego extractora zgodnego z TDR-012, więc automatyczna ekstrakcja Evidence JSON DRAFT jest **BLOCKED**.

## Źródła i artefakty

Źródła: `data/sds/Paczki/paczka2 sylgard/`. Wykonano odczyt plików przez `pypdf.PdfReader` oraz próbny odczyt istniejącym `app.infrastructure.filesystem.pdf_sds_extractor.PdfSdsExtractor.extract(path)` dla wszystkich czterech PDF, przez `.venv/Scripts/python.exe -` z kodem diagnostycznym podanym na stdin. Nie wywoływano importera Stage 1 ani bazy. Wynik istniejącego DTO zachowano bez poprawek w `docs/sds_bootstrap/BATCH-002_SYLGARD/RAW_MINIMAL_EXTRACTOR.json`; kontrolę wejścia w `BATCH-002_MANIFEST_WORKING.json`, a odrębną ocenę w `QUALITY_MATRIX.md`. **Nie ma plików Evidence JSON DRAFT**: nie były wygenerowane przez obecny moduł i ich ręczne złożenie pozorowałoby wynik TDR-012.

| ID | Źródło PDF → wyjście diagnostyczne | Bajty | SHA-256 | Strony / warstwa tekstowa |
|---|---|---:|---|---|
| B002-01 | `Sylgard 160 A rew. 5.0 (2021.10.28).pdf` → rekord 1 raw, macierz | 761136 | `f078434cfe90d09238b81cf83f2df846f46ac93107a586a29e8a6db18a2aea72` | 24; tekst na każdej stronie |
| B002-02 | `Sylgard 160 part B rew. 5.0 (2022.22.01).pdf` → rekord 2 raw, macierz | 780927 | `de3640fd8e66dfa9bc8c313cfa90844f0c7e61a09a20f918ae0de296f69d4d3d` | 25; tekst na każdej stronie |
| B002-03 | `sylgard-170-silicone-rew. 4.1_part-A_2021.10.26.pdf` → rekord 3 raw, macierz | 760841 | `cbb38ba8ff6cb9bbfb8ab2e9b91b9476dfcb21a467f05c292ba2022c31c4bc45` | 24; tekst na każdej stronie |
| B002-04 | `sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf` → rekord 4 raw, macierz | 654555 | `add472a1e9d5b3cd09a4df7da4670398883ddf92df603684a671fe5df6feb5a9` | 20; tekst na każdej stronie |

Wszystkie zaczynają się od `%PDF-`; rozmiary i SHA-256 są zgodne z checkpointem z 2026-11-06. Nazwy i ścieżki odpowiadają preflightowi. `pypdf` wydobywa tekst, lecz część polskich znaków zastępuje `�`; to ograniczenie jakości odczytu, nie dowód pełnej wierności. Ręczny przegląd tekstu sugeruje po jednej logicznej karcie `DOC-001` na zakresach 1–24, 1–25, 1–24, 1–20. W każdej widoczne są sekcje 1–16 oraz podsekcje 1.1–1.3 i 2.1–2.3. Moduł nie wykonuje segmentacji, więc liczba logicznych SDS i granice są **PROPOSAL/UNVERIFIED_BY_RUNTIME**.

## Blokada TDR-012 i jakość minimalnego odczytu

`PdfSdsExtractor` z `app/infrastructure/filesystem/pdf_sds_extractor.py` jest starszym, minimalnym ekstraktorem do DTO `ExtractedSdsData`. W repozytorium nie ma wykonawczej ścieżki PDF → segmentacja logicznych SDS → sekcje/podsekcje → ACTIVE aliases → pola ze stanami i evidence → trzy poziomy walidacji → `SDS-JSON-001` DRAFT. `PrepareSdsDraft` przenosi DTO do edytowalnego draftu aplikacji; `plan_evidence_json_import.py` waliduje już przygotowany JSON do późniejszego importu. Żaden z tych modułów nie wytwarza Evidence JSON ze źródłowego PDF. Zatwierdzone TDR-012, SDS-SCHEMA-001, SDS-ALIAS-001 i SDS-JSON-001 opisują kontrakt, ale nie dostarczają tej implementacji.

Próba minimalnym extractorem zakończyła się technicznie dla 4/4 PDF, lecz wykazała błędy domenowe. Przykład udanego **surowego** odczytu: dla B002-03 `revision=4.1`, zgodnie z `Wersja: 4.1` na s. 1; także tekst klasyfikacji H412 z sekcji 2.1 został odczytany. Przykład błędny: dla wszystkich czterech `product_name` jest pierwszym wierszem znaku towarowego, chociaż sekcja 1.1 na s. 1 zawiera właściwe `Nazwa wyrobu: SYLGARD� ... Part A/B`; `manufacturer_product_code=odradzane` pochodzi z nagłówka podsekcji 1.2. Dla B002-02 sekcja 2.2 na s. 2 zawiera `H360F`, lecz `hazard_statements=[]`, bo obecny regex przyjmuje tylko trzy cyfry. Składniki sekcji 3.2 są pomijane (`components=[]`) mimo widocznych `Nr CAS` i wierszy na s. 2. Wszystkie daty i nazwy producenta w surowym DTO są null. Domyślne `NO_DATA` w profilu bezpieczeństwa nie mają dowodów z PDF i nie są zwalidowanym odczytem.

Żadna wartość DTO nie otrzymała stanu `FOUND` ani statusu operator-approved. Ocena porównawcza, fragmenty PDF, kandydaci aliasów ze statusem tylko `CANDIDATE` i puste miejsce na zatwierdzoną korektę są w macierzy. Ten materiał może zasilić przyszły Golden Set dopiero po implementacji pipeline i decyzjach operatora.

## Obserwacje tożsamości i propozycje Stage 1

| ID | Obserwacja z dokumentu / checkpointu | Stage 1 (wyłącznie `PROPOSAL`) | Przyczyna ograniczenia |
|---|---|---|---|
| B002-01 | S. 1: SYLGARD 160 Part A, `Aktualizacja: 2021/10/28`, `Wersja: 5.0`; SHA zgodny z istniejącym `CURRENT` SDS `760c7058df7e4bb58337fc6501a1da51` według odczytowego checkpointu 2026-11-06. | `EXACT_EXISTING` | Identyczność bajtów nie zatwierdza ekstrakcji ani nowej rejestracji; aktualnego stanu DB nie odczytywano w TASK-061. |
| B002-02 | S. 1: SYLGARD 160 Part B, `Aktualizacja: 2022/11/01`, `Wersja: 5.0`. Nazwa pliku ma błędne `2022.22.01`. | `REVIEW` | Brak porównania pełnej tożsamości z aktualną bazą i zatwierdzonego JSON. |
| B002-03 | S. 1: SYLGARD 170 Part A, `Aktualizacja: 2021/10/26`, `Wersja: 4.1`. | `REVIEW` | Brak porównania pełnej tożsamości z aktualną bazą i zatwierdzonego JSON. |
| B002-04 | S. 1: SYLGARD 170 Part B, `Aktualizacja: 2022/11/07`, `Wersja: 7.0`; nazwa pliku sugeruje inną datę (`2021.10.26`). | `REVIEW` | Brak porównania pełnej tożsamości z aktualną bazą i zatwierdzonego JSON. |

Na s. 1 sekcja 1.3 każdego PDF nazywa `DOW POLSKA SP.Z O.O.` w kontekście **dostawcy karty charakterystyki**. Nie ma podstaw do automatycznego zapisania tego podmiotu jako producenta. Nie wykonano Stage 1 CREATE, zmiany PRODUCT/SDS/BHP ani klasyfikacji zatwierdzonej przez operatora.

## T61-1–T61-8

| Kryterium | Wynik | Dowód / ograniczenie |
|---|---|---|
| T61-1 | PASS | 4 pliki, bajty, SHA-256, `%PDF-`, liczba stron i liczba znaków tekstu per strona w manifeście. |
| T61-2 | PASS — blokada wykazana | Uruchomiono istniejący `PdfSdsExtractor` 4/4; surowe DTO zapisano. Nie istnieje wykonawcza ścieżka TDR-012 do Evidence JSON. |
| T61-3 | BLOCKED | Tylko ręcznie obserwowane zakresy, sekcje i fragmenty PDF. Runtime nie wytworzył `document_key`, `page_range`, stanów, evidence ani DRAFT JSON; nie symulowano ich. |
| T61-4 | PARTIAL | Surowe DTO oddzielone od macierzy oceny; lista błędów i `CANDIDATE` aliasów. Bez operator-approved korekt i automatycznego raportu walidacji. |
| T61-5 | PASS na poziomie obserwacji | B002-01 SHA identyczny z wpisem checkpointu; B002-02 data z nagłówka PDF to `2022/11/01`, nie z nazwy. B002-04 ma także rozbieżność daty. |
| T61-6 | PARTIAL | Cztery klasyfikacje `PROPOSAL` powyżej; dla trzech źródeł `REVIEW`, bez weryfikacji tożsamości w DB i bez importu. |
| T61-7 | PASS w zakresie wykonanych operacji | Powstały tylko trzy artefakty w `docs/sds_bootstrap/BATCH-002_SYLGARD/` i ten raport. `git status` przed raportem: `main...origin/main [ahead 1, behind 6]`, zastane nieśledzone `TASK-GIT-001_REPORT.md` i dwa pliki tasków oraz nowy katalog BATCH-002. Bez checkout/commit/push/merge/rebase, zmian kodu, migracji i wywołań zapisu DB. |
| T61-8 | PASS | Niniejszy raport, jedna rekomendacja i STOP. |

**Jeden rekomendowany następny krok:** osobno autoryzować implementacyjny Task dla minimalnego pipeline TDR-012 z kontraktowym Evidence JSON i regresją na BATCH-002 oraz przypadku wielokartowego PDF. Nie uruchamiać importu na podstawie tego materiału.

**STOP po raporcie.**
