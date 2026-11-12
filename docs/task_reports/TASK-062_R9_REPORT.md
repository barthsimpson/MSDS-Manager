# TASK-062-R9 — LOCTITE: data aktualizacji i pełna rewizja SDS

**Status:** implementacja i weryfikacja R9 zakończone; Evidence JSON pozostaje `PENDING_REVIEW`. **Data:** 2026-11-12. Punkt wyjścia: `main` i `origin/main` `802903af94f92b099a797fd7e21a2775d13c3565`; zastane nieśledzone raport i dyspozycje R8/R9 zachowano. Przed i po zmianie `load_catalog()` wskazuje 13 `ACTIVE` A-001–A-013.

## Zakres implementacji

- Istniejący A-008 `Aktualizacja` rozpoznaje dodatkowo kalendarzowo poprawne `DD.MM.YYYY` w swoim kontekście nagłówka. Zachowano dotychczasowe `YYYY/MM/DD`, oddzielenie `Data aktualizacji` od A-008 oraz daty R7/3M/OPEX. Dowodem `FOUND` jest wyłącznie wiersz `Aktualizacja`, nawet gdy `Data druku` ma identyczną datę.
- Zatwierdzoną regułę kontekstową `V...` ograniczono do nagłówka karty: obok `KC Numer` i znacznika strony/karty, przed treścią sekcji. Skanuje strony tylko w zakresie własnego logicznego SDS, zachowuje literalny token (`V005.1`, `V014.0`, `V013.0`), dopuszcza zgodne powtórzenia i zwraca `AMBIGUOUS/null` dla sprzecznych. W G2 potwierdzany jest dokładny token i cytat w źródłowym nagłówku. `KC Numer` nie staje się kodem produktu ani rewizją.
- Nie dodano aliasu ani parsera zależnego od marki, nazwy pliku, numeru strony lub twardych wartości LOCTITE. `config/sds_aliases.json`, CLI i kontrakt JSON pozostały bez zmian. `SUPPLIER` nie jest automatycznie `MANUFACTURER`.

## Wynik trzech oryginalnych PDF — przed R9 → po R9

Źródła: `data/sds/Paczki/paczka 5 loctite/`; SHA-256 wszystkich trzech jest zgodny z diagnostyką R8. Uruchomiono niezmieniony CLI z osobnymi ID `R9-L01..L03` do ignorowanego `tmp/task062r9_loctite/`. Każdy PDF ma jeden logiczny SDS, bez mieszania zakresów. Wszystkie trzy przebiegi CLI zakończyły się kodem 0; zapisano trzy `*.evidence.json` i trzy `*.validation.json`.

| ID / PDF / strony | `product_name` | `manufacturer_product_code` | `issue_date` przed → po | `revision` przed → po | `parties[]` | Walidacja |
|---|---|---|---|---|---|---|
| R9-L01 `Loctite 242 31.05.2022.pdf`, DOC-001 1–16 | `LOCTITE 242` `FOUND` | `NOT_FOUND/null` | `AMBIGUOUS/null` → **`FOUND/2022-07-11`** | `NOT_FOUND/null` → **`FOUND/V005.1`** | `SUPPLIER`, `FOUND/Henkel Polska Sp. z o.o.` | G1/G2/G3 PASS |
| R9-L02 `Loctite 243  rew 014.0 (27.03.2024).pdf`, DOC-001 1–24 | `LOCTITE 243` `FOUND` | `NOT_FOUND/null` | `AMBIGUOUS/null` → **`FOUND/2024-05-14`** | `NOT_FOUND/null` → **`FOUND/V014.0`** | `SUPPLIER`, `FOUND/Henkel Polska Sp. z o.o.` | G1/G2/G3 PASS |
| R9-L03 `Loctite 638 24.10.2022.PDF`, DOC-001 1–32 | `Loctite 638` `FOUND` | `NOT_FOUND/null` | `AMBIGUOUS/null` → **`FOUND/2022-10-24`** | `NOT_FOUND/null` → **`FOUND/V013.0`** | `SUPPLIER`, `FOUND/Henkel Polska Sp. z o.o.` | G1/G2/G3 PASS |

W każdym DRAFT `review_status=PENDING_REVIEW`, `validation.status=REQUIRES_HUMAN_REVIEW` i G3 zachowuje `MANUFACTURER_REQUIRES_HUMAN_REVIEW`. Przykładowe literalne dowody s. 1: L01 `Aktualizacja: 11.07.2022` oraz `KC Numer :  173036` / `V005.1`; L02 `Aktualizacja: 14.05.2024` oraz `KC Numer :  316211` / `V014.0`; L03 `Aktualizacja: 24.10.2022` oraz `KC Numer :  450822` / `V013.0`. Evidence zapisuje pełne `source_text`, `page=1`, `section=HEADER` i etykiety `Aktualizacja` / `V`. Źródłowa nazwa z §1.1 i dostawca z §1.3 pozostają niezmienione. L01/L02 nie pobierają dat z nazw PDF (`31.05.2022` / `27.03.2024`), bo są to daty po `Zastępuje wersje z`.

## Testy i kontrola negatywna

Komenda: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py tests/unit/test_task062_r5_3m_aliases.py tests/unit/test_task062_r7_weicon.py tests/unit/test_task062_r9_loctite.py -q -p no:cacheprovider --basetemp tmp/task062r9_regression_20261112` → **43 passed** (36 wcześniejszych R2/R3/R5/R7 + 7 nowych R9). Skupione R9 osobno: **7 passed**. Testy R9 sprawdzają trzy oryginalne SHA/PDF, dokładne daty i pełne tokeny `V`, bramki, evidence i zakresy; syntetycznie odrzucają datę wydruku, datę zastępowaną, niepoprawny dzień miesiąca, token `V` poza nagłówkiem/bez `KC Numer`, H-kod i wersję transportu. Zgodne powtórzenie `V` pozostaje `FOUND`; konflikt w jednym SDS jest `AMBIGUOUS`, a oddzielne logiczne SDS nie wymieniają rewizji. Zmieniona wartość lub strona dowodu rewizji daje G2 FAIL, a `KC Numer` podany jako kod produktu nie przechodzi G2. Dotychczasowe daty, rewizje, role i zakresy OPEX, czterech SYLGARD, 3M oraz WEICON przeszły regresję.

Komendy CLI: `.\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence '<PDF>' --output-dir tmp/task062r9_loctite --source-id R9-L01` (analogicznie L02/L03). Faktycznie odczytano zapisane JSON-y i walidacje: trzy różne SHA, 16/24/32 strony, 3 logiczne SDS, 9/9 bramek PASS, daty/rewizje i dowody jak wyżej. Artefakty pozostają w `tmp/`; nie uruchomiono DB ani importera.

| ID | Wynik i dowód |
|---|---|
| R9-1 | PASS: istniejący `main` na `802903a`, 13 `ACTIVE`, zastane nieśledzone pliki zachowane; źródłowe SHA zgodne z R8. |
| R9-2 | PASS: L01/L02/L03 mają `FOUND` 2022-07-11 / 2024-05-14 / 2022-10-24 z `Aktualizacja`, s. 1, HEADER. |
| R9-3 | PASS: `Data druku`, `Zastępuje wersje z`, data niemożliwa i nazwa PDF nie zastępują bieżącej daty; SYLGARD/WEICON/3M/OPEX bez regresji. |
| R9-4 | PASS: dokładne `FOUND/V005.1`, `FOUND/V014.0`, `FOUND/V013.0`, z pełnym cytatem nagłówka i zerami wiodącymi. |
| R9-5 | PASS: zgodne `V` nie jest konfliktowe, sprzeczne pozostaje `AMBIGUOUS`; `KC Numer`, strona, H-kod i inny SDS nie tworzą rewizji/kodu produktu. |
| R9-6 | PASS: 3 PDF → 3 osobne SDS 1–16 / 1–24 / 1–32; nazwy, kody, dostawca i statusy zgodne z decyzją; 3 DRAFT, 3 walidacje, 9/9 bramek PASS. |
| R9-7 | PASS: 7 testów skupionych + regresja R2/R3/R5/R7; 43/43 PASS. |
| R9-8 | PASS: zakres ograniczony do matchera, pomocniczej logiki pipeline, testu R9 i tego raportu; bez Core/DB/UI/importera/kontraktu JSON; bez następnej paczki. |

**Pliki R9 do selektywnego commita:** `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `tests/unit/test_task062_r9_loctite.py`, `docs/task_reports/TASK-062_R9_REPORT.md`. Nie dodawać PDF, danych ani JSON z `tmp/`. SHA commita oraz potwierdzenie `origin/main` zostaną podane po publikacji w komunikacie końcowym, ponieważ commit nie może zawierać własnego SHA w raporcie.

**Ograniczenie:** `SUPPLIER` pozostaje dowodem źródłowym do decyzji człowieka; G1/G2/G3 PASS nie zatwierdza producenta ani importu. **STOP po R9.**
