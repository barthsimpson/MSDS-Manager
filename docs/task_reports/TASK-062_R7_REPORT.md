# TASK-062-R7 — WEICON: data, dostawca, powtórzona rewizja

**Status:** wykonano zakres R7; wyniki Evidence JSON pozostają `PENDING_REVIEW`. **Data:** 2026-11-12. Punkt wyjścia: lokalny i zdalny `main` `4188b4ffd6c293e97c4426fd42d6306b8d93a7ec`. Zastanych plików nieśledzonych nie czyszczono. Przed pracą katalog zawierał dokładnie A-001–A-013 `ACTIVE`.

## Zmiana i decyzja daty

Zmiany ograniczono do istniejącego matchera:

- A-005 wybiera bieżącą datę po `Data wydania/Data aktualizacji`. Dla dat liczbowych `10/20/2022` niepodważalny wyróżnik (`20` nie może być miesiącem) daje `2022-10-20`; dla izolowanego `02/03/2022` zatwierdzony polski priorytet daje **`2022-03-02` i `FOUND`**. Gdy sąsiednia data źródłowa jednoznacznie wskazuje układ `MM/DD/YYYY`, parser zachowuje ten udokumentowany kontekst. `Data poprzedniego wydania` i `Data wydruku` nie są wybierane jako bieżąca data. Daty niemożliwe pozostają nierozstrzygnięte.
- A-013 zachowuje wariant 3M `Adres:` i obsługuje nazwę dostawcy w następnym niepustym wierszu §1.3. Wiersze ulicy, telefonu, e-maila, copyright i znacznik `IDENTYFIKACJA FIRMY` nie stają się nazwą; ten ostatni nadal należy do A-009. Rola źródłowa pozostaje `SUPPLIER`.
- A-006 uznaje zgodne powtórzenia `Wersja` w jednym kontekście za `FOUND`, z dowodem ostatniego wystąpienia w stopce. Sprzeczne wartości pozostają `AMBIGUOUS`; numer strony i wersja transportu nie są traktowane jako rewizja.

Nie dodano aliasów ani nie zmieniono `config/sds_aliases.json`; nadal dokładnie 13 `ACTIVE`. Nie zmieniono pipeline’u, CLI ani kontraktu Evidence JSON.

## Ponowne przetworzenie paczki 3

Oryginalne cztery PDF z `data/sds/Paczki/paczka3 silicon/` przetworzono istniejącym CLI do ignorowanego `tmp/task062r7_publish_20261112/`. Każdy plik daje jeden logiczny SDS i osobny `P3-01..04.evidence.json` oraz `.validation.json`. SHA-256 wszystkich źródeł jest identyczny z diagnostyką R6. Każdy wynik ma G1/G2/G3 = **PASS/PASS/PASS**, `review_status=PENDING_REVIEW`, `validation.status=REQUIRES_HUMAN_REVIEW` i ostrzeżenie o koniecznej decyzji człowieka co do producenta. Nie uruchamiano importera ani DB.

| PDF / zakres | `product_name` | `manufacturer_product_code` | `issue_date` przed → po | `revision` przed → po | `parties[]` przed → po |
|---|---|---|---|---|---|
| P3-01 `Repair Stick Steel 10.19.2022 rew.3.01.pdf`, DOC-001 1–14 | `Repair Stick Steel` `FOUND` | `105330` `FOUND` | `AMBIGUOUS/null` → `FOUND/2022-10-20` | `FOUND/3.01` → bez zmiany | puste → `SUPPLIER`, `FOUND/WEICON GmbH & Co. KG` |
| P3-02 `Silicon F Weicon 10.19.2022 rew. 3.01.pdf`, DOC-001 1–12 | `Silicone F` `FOUND` | `132000` `FOUND` | `AMBIGUOUS/null` → `FOUND/2022-10-20` | `AMBIGUOUS/null` → `FOUND/3.01` | puste → `SUPPLIER`, `FOUND/WEICON GmbH & Co. KG` |
| P3-03 `silikon A DOWSIL  CN-8760-PL rew.05 20230106.pdf`, DOC-001 1–17 | `DOWSIL CN-8760 Encapsulant Part A` `FOUND` | `NOT_FOUND/null` | `FOUND/2023-01-06` → bez zmiany | `FOUND/5.0` → bez zmiany | `SUPPLIER`, `FOUND/DOW POLSKA SP.Z O.O.` → bez zmiany |
| P3-04 `silikon B DOWSIL  CN-8760 PL rew.05 20240725.pdf`, DOC-001 1–29 | `DOWSIL CN-8760 Encapsulant Part B` `FOUND` | `NOT_FOUND/null` | `FOUND/2024-07-25` → bez zmiany | `FOUND/5.0` → bez zmiany | `SUPPLIER`, `FOUND/DOW POLSKA SP.Z O.O.` → bez zmiany |

Dowody WEICON z oryginalnych PDF: P3-01/02 s. 1 stopka `Data wydania/Data aktualizacji :10/20/2022   Data poprzedniego wydania :10/19/2022` → bieżąca data `2022-10-20`; s. 1 §1.3 `Dane dotyczące dostawcy karty charakterystyki` / `WEICON GmbH & Co. KG` → `SUPPLIER`; P3-02 s. 12 `Wersja : 3.01` w §16 oraz `Wersja :3.01 12/12` w stopce → jedna zgodna wartość `3.01`. Każde pole `FOUND` ma literalny `source_text`, stronę i sekcję/podsekcję. Nie pobrano ulicy `Königsberger Str. 255`, danych kontaktowych ani poprzedniej daty jako wartości. `Silicone F` pochodzi z §1.1, mimo odmiennego `Silicon F` w nazwie PDF.

## Weryfikacja

Komenda końcowa: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py tests/unit/test_task062_r5_3m_aliases.py tests/unit/test_task062_r7_weicon.py -q -p no:cacheprovider --basetemp tmp/task062r7_final_regression2_20261112` → **36 passed**, w tym 23 wcześniejsze R2/R3/R5 oraz 13 nowych przypadków R7. Izolowany test `02/03/2022` daje `2022-03-02` z `FOUND` i literalnym dowodem; test `10/20/2022` daje `2022-10-20`. Testy negatywne obejmują datę kalendarzowo niemożliwą (również jako niewiarygodną wskazówkę formatu), datę poprzednią i wydruku, ulicę, kontakt, §1.4, blok A-009, konflikt rewizji, numer strony, wersję transportu i fałszywą zamianę daty na poprzednią. Regresja PDF OPEX, czterech SYLGARD i trzech logicznych SDS 3M jest PASS, w tym daty/role dotychczasowych układów.

Ponadto: kontrola AST dwóch zmienionych/dodanych plików Python i importów trzech modułów uruchomieniowych = PASS. CLI wykonano 4/4 razy z kodem 0; osobna kontrola zapisanych JSON i walidacji potwierdziła 4 DRAFT, 4 walidacje, 12 bramek PASS, zakresy stron, źródłowe dowody i niezmienione SHA czterech PDF. Komendy diagnostyczne `tmp/task062r7_run_cli.py` i `tmp/task062r7_verify_outputs.py` oraz JSON-y pozostają wyłącznie pod ignorowanym `tmp/`.

| ID | Wynik i dowód |
|---|---|
| R7-1 | PASS: istniejący `main` na bazie R5, 13 `ACTIVE`; zastany stan roboczy i źródłowe SHA zachowane. |
| R7-2 | PASS: oba WEICON mają `FOUND/2022-10-20`, dowód bieżącej daty s. 1; `2022-10-19` i `10/21/2022` wykluczone. |
| R7-3 | PASS: izolowane `02/03/2022` → `FOUND/2022-03-02`, `10/20/2022` → `FOUND/2022-10-20`; niemożliwe daty nie dają `FOUND`; OPEX/3M/DOWSIL bez regresji. |
| R7-4 | PASS: oba WEICON mają `SUPPLIER=WEICON GmbH & Co. KG` z §1.3 s. 1; testy negatywne ulicy, kontaktu i §1.4; bez automatycznego producenta. |
| R7-5 | PASS: P3-02 `FOUND/3.01` przy zgodnych powtórzeniach; konflikt nadal `AMBIGUOUS`, transport i `12/12` nie są rewizją. |
| R7-6 | PASS: 4 PDF → 4 logiczne SDS o zakresach 1–14, 1–12, 1–17, 1–29; nazwy, kody, daty, rewizje i role jak wyżej; G1/G2/G3 PASS. |
| R7-7 | PASS: 36 testów R2/R3/R5/R7; wcześniejsze formaty i role zachowane. |
| R7-8 | PASS: zmiany ograniczone do matchera, testu R7 i tego raportu; DRAFT tylko `tmp/`; bez Core/DB/UI/importera/PDF. |

**Pliki R7:** `app/infrastructure/filesystem/sds_alias_matcher.py`, `tests/unit/test_task062_r7_weicon.py`, `docs/task_reports/TASK-062_R7_REPORT.md`. Nie dołączano wcześniejszych nieśledzonych raportów R6, danych ani roboczych JSON. SHA kontrolowanego commita i wynik zwykłego push zostaną podane po publikacji w komunikacie końcowym; SHA commita zawierającego raport nie można wpisać do tego samego commita.

**Ryzyko:** reguła `02/03/2022` jest zatwierdzoną interpretacją przy braku jednoznacznego wyróżnika, a nie dowodem formatu każdego źródła. `SUPPLIER` jest nadal propozycją do ludzkiego przeglądu. **STOP po R7; bez paczki 5 i integracji aplikacji.**
