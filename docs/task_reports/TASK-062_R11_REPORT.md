# TASK-062-R11 — implementacja reguł KCH i regresja

**Status:** R11-1…R11-8 zweryfikowane 2026-11-12; sześć Evidence JSON nadal wymaga zatwierdzenia przez człowieka. **Punkt wyjścia:** `main`, `HEAD=origin/main=3a6aad90d01f1c8478a23d1317a71f66dc413489`; śledzone pliki czyste. Zastane nieśledzone raporty i dyspozycje R8/R10/R11 pozostawiono.

## Zakres i decyzje

Zrealizowano zatwierdzone R10-C01–C09 w istniejących `sds_alias_matcher.py` i `sds_evidence_pipeline.py`. Katalog `config/sds_aliases.json` nadal zawiera **13 ACTIVE A-001–A-013**; nie był edytowany. Nie trzeba było tworzyć nowego aliasu literalnego: A-010/A-011/A-012/A-013 obsługują dodatkowe układy, a `Producent`/`Dystrybutor` i `Edycja` są wąskimi regułami kontekstowymi z osobną weryfikacją dowodu w G2/G3.

`SDS-JSON-001` §10 **już dopuszcza `DISTRIBUTOR`** (podobnie `MANUFACTURER`, `SUPPLIER`), a runtime walidatora miał te role w enum. Nie zmieniono kontraktu JSON ani Core. Źródłowe `Producent` daje `MANUFACTURER`, `Dystrybutor` daje `DISTRIBUTOR`, ogólny blok dostawcy KCH-06 daje `SUPPLIER`. G2 odrzuca `FOUND`, gdy sama nazwa podmiotu jest słowem `Producent` lub `Dystrybutor`, i potwierdza pełny cytat z właściwego §1.3; G3 sprawdza zgodność roli z etykietą. Źródłową rolę traktujemy jako propozycję, bez utworzenia relacji w Core.

W KCH-01/02 trzy linie nazwy łączone są pojedynczymi spacjami **bez utraty segmentów**: `CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA`. Evidence zachowuje źródłowe trzy linie wraz z ich odstępami, etykietą `Nazwa lub nazwa handlowa`, markerem `Producent`, stroną 1 i §1.3. Kontynuację dopuszcza tylko wyrównanie do kolumny nazwy; kończy ją kolejna etykieta §1.3. Dla KCH-06 `Edycja` mapuje się na dosłowne `revision="04"`, zachowując zero. Nagłówek dwurowy jest odczytywany tylko przed sekcją i tylko przy pełnej kolejności trzech kolumn. Segmentator rozpoznaje `SEKCJA 1.` oraz dotychczasowe `SEKCJA 1:`.

## Sześć unikalnych oryginalnych PDF — przed R11 → po R11

Źródło wszystkich wyników: oryginalne PDF z `data/sds/Paczki/paczka 4 KCH/` oraz **odczytane z dysku** `tmp/task062r11_kch_final/KCH-01..06.evidence.json` i odpowiadające `.validation.json`. Wszystkie podane pola po R11 mają `FOUND` z cytatem, s. 1 i właściwą sekcją/nagłówkiem. `manufacturer_product_code` pozostaje `NOT_FOUND/null`; UFI nie jest kodem produktu. D-02: `KCH EGR CLEANER rew. 2.0 23.01.2023.pdf` i `KCH EGR CLEANER.pdf` mają ten sam SHA-256 `30187c7f8a32c58e9148c02e0b7892cb90d5dffb5919d3d34c08c939307e02de`; drugi plik nie był przetwarzany powtórnie.

| ID / DOC-001 | Nazwa przed → po | Data przed → po | Rewizja przed → po | `parties[]` przed → po | Walidacja po |
|---|---|---|---|---|---|
| KCH-01, s. 1–8 | N/null → `EGR CLEANER` | N/null → `2023-01-23` | N/null → `2.0` | fałszywe `SUPPLIER/Producent` → `MANUFACTURER/CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA` | G1/G2/G3 PASS |
| KCH-02, s. 1–11 | N/null → `RC72` | N/null → `2023-01-23` | N/null → `2.0` | fałszywe `SUPPLIER/Producent` → pełna nazwa CX80 jak wyżej, `MANUFACTURER` | G1/G2/G3 PASS |
| KCH-03, s. 1–13 | N/null → `Topnik RF 800` | N/null → `2024-01-25` | N/null → `13.0` | fałszywe `SUPPLIER/Dystrybutor` → `DISTRIBUTOR/AG TermoPasty Grzegorz Gąsowski` | G1/G2/G3 PASS; ostrzeżenie o producencie |
| KCH-04, s. 1–13 | N/null → `Lakier PVB 16` | N/null → `2024-02-27` | N/null → `6.0` | fałszywe `SUPPLIER/Producent` → `MANUFACTURER/AG TermoPasty Grzegorz Gąsowski` | G1/G2/G3 PASS |
| KCH-05, s. 1–14 | N/null → `Lakier PVB 60` | N/null → `2024-01-26` | N/null → `12.0` | fałszywe `SUPPLIER/Producent` → `MANUFACTURER/AG TermoPasty Grzegorz Gąsowski` | G1/G2/G3 PASS |
| KCH-06, s. 1–17 | błędne F `Nazwa handlowa produktu: Farba KONTUR ŻOŁTY.` → `Farba KONTUR ŻOŁTY.` | N/null → `2025-07-17` | N/null → dosłownie `04` | brak → `SUPPLIER/KON-TUR sp. z o. o. sp. k.` | G1/G2/G3 PASS; ostrzeżenie o producencie |

Wszystkie sześć DRAFT: `READABLE`, `logical_sds_count=1`, `DOC-001`, `PENDING_REVIEW`, `validation.status=REQUIRES_HUMAN_REVIEW`; **18/18 bramek PASS**. KCH-03 i KCH-06 mają G3 issue `DOC-001:MANUFACTURER_REQUIRES_HUMAN_REVIEW`, bo SDS wskazuje tylko dystrybutora albo dostawcę. KCH-01/02/04/05 mają źródłowy `MANUFACTURER`, więc istniejący G3 nie dodaje tego ostrzeżenia; ich status nadal wymaga zatwierdzenia tożsamości przez człowieka. G1/G2 issues są puste, `extraction_report.errors=[]`. Każdy źródłowy SHA i liczba stron są zgodne z R10; 7 PDF daje 6 unikalnych SHA.

Przykładowe źródłowe rozróżnienia, których nie zastąpiono nazwą pliku: KCH-03 s. 1 `Numer wersji 13.0` mimo `rew. 12` w nazwie PDF; KCH-05 s. 1 `Data aktualizacji 26.01.2024` mimo `26.02.2024` w nazwie; KCH-06 s. 1 `Data wydania 08.01.2021` obok bieżącej `Data aktualizacji 17.07.2025`. Dowody nazw pochodzą z §1.1, podmiotów z §1.3. KCH-06 `Nazwa handlowa produktu:` pozostaje w `source_text`, lecz nie w wartości kanonicznej; kropka i polskie znaki są zachowane.

## Testy, CLI i kryteria R11-1…R11-8

Test skupiony: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r11_kch.py -q -p no:cacheprovider --basetemp tmp/task062r11_focused_verified_20261112` → **13 PASS, 0 FAIL, 0 SKIP**. Regresja: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py tests/unit/test_task062_r5_3m_aliases.py tests/unit/test_task062_r7_weicon.py tests/unit/test_task062_r9_loctite.py tests/unit/test_task062_r11_kch.py -q -p no:cacheprovider --basetemp tmp/task062r11_regression_verified_20261112` → **56 PASS, 0 FAIL, 0 SKIP**. Obejmuje OPEX, SYLGARD, 3M, WEICON i LOCTITE oraz sześć KCH. Testy negatywne obejmują słowa ról jako nazwy, zamienioną rolę, cudzą nazwę i słaby cytat, niepoprawną datę, brak/przestawienie kolumn, sprzeczne daty i rewizje obu układów, niepewną sąsiednią kolumnę nazwy oraz segmentację złączonych SDS przy `SEKCJA 1.`.

CLI bez zmiany: `.\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence '<oryginalny PDF>' --output-dir tmp/task062r11_kch_final --source-id KCH-0N` dla N=1…6. **6/6 końcowych przebiegów: kod 0**, faktycznie zapisane i ponownie odczytane 6 Evidence JSON + 6 validation JSON. Pierwszy zestaw w `tmp/task062r11_kch/` też zakończył się 6/6 kodem 0. Próba ponownego zapisu na te same ścieżki po ostatniej poprawce dała 6/6 kod 1 z oczekiwanym komunikatem CLI `artifact already exists; use a fresh output directory`; użyto nowego, ignorowanego katalogu bez nadpisywania artefaktów. Dla duplikatu D-02 nie uruchomiono CLI. Nie instalowano zależności ani nie używano OCR/LLM.

| ID | Wynik i dowód |
|---|---|
| R11-1 | PASS: istniejący `main`, `origin/main`, 13 ACTIVE, 7 PDF / 6 SHA, zastane pliki zachowane; źródłowe SHA zgodne z R10. |
| R11-2 | PASS: pięć nazw, dat i rewizji KCH-01…05 dokładnie jak w tabeli, każda `FOUND` z s. 1; negatywy dat/kolumn i regresja. |
| R11-3 | PASS: pełne nazwy i role `MANUFACTURER`/`DISTRIBUTOR`, bez nazw `Producent`/`Dystrybutor`; test G2 wykrywa rolę udającą nazwę, G3 rolę niezgodną z dowodem. |
| R11-4 | PASS: KCH-06 nazwa bez prefiksu, `2025-07-17`, dosłowne `04`, `SUPPLIER/KON-TUR...`, cytaty i negatywy. |
| R11-5 | PASS: KCH-06 1–17; test złączonych stron z dwoma `SEKCJA 1.` daje 1–2 i 3–4, bez podziału na `SEKCJA 10.`/`16.` lub `1.1.`; R5/3M bez regresji. |
| R11-6 | PASS: sześć końcowych przebiegów CLI w świeżym katalogu, 6 DRAFT + 6 walidacji odczytanych z dysku, 18/18 bramek PASS, wszystkie statusy human review; D-02 tylko raz. |
| R11-7 | PASS: 13 focused + 56 łącznej regresji, 0 FAIL/SKIP; badane formaty R2/R3/R5/R7/R9 i KCH. |
| R11-8 | PASS: ograniczony diff — matcher, pomocnicza logika pipeline/G2, test R11 i raport R11; bez zmiany katalogu, Core, DB, UI, importera, JSON contract i PDF. |

**Pliki do selektywnego commita:** `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `tests/unit/test_task062_r11_kch.py`, `docs/task_reports/TASK-062_R11_REPORT.md`. Robocze JSON pozostają w ignorowanym `tmp/`. **Odstępstwa:** brak od zatwierdzonej semantyki; jedyna zmiana walidatora jest lokalnym potwierdzeniem istniejącego kontraktu. SHA commita i potwierdzenie zdalnego `main` są przekazywane po publikacji w komunikacie końcowym, ponieważ commit nie może zawierać własnego SHA. **STOP po R11.**
