# TASK-062-R11 — KCH: poprawna tożsamość, role podmiotów, metadane i segmentacja SDS

**Status:** READY / AUTHORIZED — decyzja Architekta 2026-11-12  
**TASK MODE:** PATCH — ograniczona implementacja ekstraktora + regresja powiązanych układów  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repo:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`, bez branchy/worktree.  
**Punkt odniesienia:** R10 ACCEPTED (diagnostyka); przed R10 `HEAD=origin/main=3a6aad90d01f1c8478a23d1317a71f66dc413489`. Na początku sprawdź **rzeczywisty** HEAD/upstream/status; nie resetuj ani nie sprzątaj nowszych lub nieśledzonych plików.

## 1. AUTHORITATIVE CONTEXT i decyzje

1. `docs/task_reports/TASK-062_R10_REPORT.md` — sześć unikalnych SDS KCH, źródłowe cytaty, SHA, macierz **R10-C01–C09** i negatywy. To źródło konkretnych oczekiwanych danych.
2. `docs/tasks/TASK-062_R10_KCH_DIAGNOSTYKA_ALIASOW.md`, `docs/task_reports/TASK-062_R9_REPORT.md`; R6 inventory tylko jeśli potrzebna weryfikacja duplikatu D-02. Nie powtarzaj inwentaryzacji 134 plików.
3. `AGENTS.md` oraz odpowiednie fragmenty GOV-001 v1.0-approved, GOV-002 v1.0-approved, TDR-012 v1.0-approved, SDS-ALIAS-001, SDS-JSON-001, BDR-005 v1.2-approved i CORE-001 v1.9-approved. Jeśli dokumentu nie ma lokalnie, zgłoś brak; nie odtwarzaj zasad z pamięci.
4. **Wiążąca decyzja Architekta:** zatwierdza **R10-C01–C09**. `Producent` → rola źródłowa **`MANUFACTURER`**, `Dystrybutor` → **`DISTRIBUTOR`**, ogólne dane dostawcy → **`SUPPLIER`**. `Edycja 04` → `document_metadata.revision="04"` (tekst, z zachowanym zerem). Zatwierdzenie dotyczy **Evidence DRAFT**, NIE automatycznej tożsamości producenta w Core ani zapisu do DB.
5. Reguła nadrzędna: **automatyzacja proponuje, człowiek zatwierdza, Core pozostaje chroniony**. Kod producenta opcjonalny; UFI, nazwa PDF, stopka, identyfikator dokumentu nie są jego substytutami. Evidence zachowuje oryginalny cytat/rolę; nazwa operacyjna usuwa wyłącznie `®` i `™`.

## 2. GOAL

Poprawić istniejący, autonomiczny ekstraktor PDF → **Evidence JSON DRAFT**, tak aby sześć unikalnych PDF paczki 4 KCH dawało prawidłowe nazwy produktów, daty aktualizacji, tekstowe rewizje, **pełne nazwy i role** podmiotów oraz wykrywanie początku `SEKCJA 1.`. Zminimalizować fałszywe `FOUND` (zwłaszcza `parties[].name="Producent"` / `"Dystrybutor"`) i zachować poprawne wcześniejsze układy OPEX/SYLGARD/3M/WEICON/LOCTITE.

## 3. KNOWN STARTING POINTS / DOZWOLONA POWIERZCHNIA

- `app/infrastructure/filesystem/sds_alias_matcher.py`: A-010, A-011, A-012, A-013, daty/rewizje/nazwy i §1.3.
- `app/infrastructure/filesystem/sds_evidence_pipeline.py`: `_ranges`, segmentacja oraz walidacja dowodów G1/G2/G3; tylko rzeczywiście potrzebne fragmenty.
- `config/sds_aliases.json`: spodziewane **13 ACTIVE A-001–A-013**; nie dodawaj aliasów bez wykazanej konieczności. Jeśli nowy literalny alias jest konieczny, stosuj zatwierdzone CANDIDATE→APPROVED→focused tests→ACTIVE i opisz decyzję/rezultat, bez dublowania etykiet.
- `scripts/extract_sds_evidence.py`: istniejący CLI — nie modyfikuj bez konieczności.
- `tests/unit/test_task062_r2_aliases.py`, `test_task062_r3_evidence.py`, `test_task062_r5_3m_aliases.py`, `test_task062_r7_weicon.py`, `test_task062_r9_loctite.py`: regresja; dodaj `tests/unit/test_task062_r11_kch.py`.
- Źródła (bez modyfikacji): `data/sds/Paczki/paczka 4 KCH/`, sześć unikalnych PDF oznaczonych KCH-01…06 w R10. **KCH-01-DUP** identyczny SHA D-02 — nie uruchamiaj powtórnej ekstrakcji, lecz ujmij w raporcie.

Jeżeli istniejący kontrakt Evidence lub enum ról nie obsługuje literalnego `DISTRIBUTOR`, **nie zapisuj fałszywego `SUPPLIER`** ani nie zmieniaj po cichu Core/schema. Zatrzymaj wyłącznie blokowany fragment, opisz minimalny konflikt kontraktowy i decyzję potrzebną do naprawy; niezależne C01–C03/C05–C09 możesz dokończyć. Dozwolona jest lokalna poprawka walidatora Evidence wyłącznie wtedy, gdy zachowuje zatwierdzony kontrakt — wykaż to testem; nie rozciągaj tasku na model domenowy/importer.

## 4. DO — dziewięć zatwierdzonych reguł

### R10-C01 — nazwy KCH-01…05, ten sam wiersz §1.1
Rozpoznaj wartość po `Identyfikator produktu`, także gdy etykieta i nazwa są w jednej linii / kolumnach layout. Oczekiwane `FOUND`: `EGR CLEANER`, `RC72`, `Topnik RF 800`, `Lakier PVB 16`, `Lakier PVB 60`. Zachowaj dosłowny cytat, stronę 1, §1.1. Nie pobieraj tytułu strony, UFI, zastosowania ani nazwy PDF.

### R10-C02 — bieżąca data KCH-01…05
Z nagłówka/etykiety `Data aktualizacji` bez dwukropka, obok `Numer wersji`, odczytaj daty `DD.MM.YYYY` → `2023-01-23`, `2023-01-23`, `2024-01-25`, `2024-02-27`, `2024-01-26`. Nie bierz `Data utworzenia`, SBLCore/stopki ani błędnych dat z nazwy PDF. Uwzględnij powtórzenia nagłówka i poprawność kalendarza; rzeczywisty konflikt → `AMBIGUOUS`.

### R10-C03 — rewizja KCH-01…05
Odczytaj z `Numer wersji` w tym samym nagłówku: kolejno dokładnie **`"2.0"`, `"2.0"`, `"13.0"`, `"6.0"`, `"12.0"`**; zachowaj tekst, nie normalizuj. Powtórzenia zgodne w jednym SDS są `FOUND`, sprzeczne `AMBIGUOUS/null`; nie pobieraj wersji z nazwy PDF, stopki SBLCore, transportu, daty, UFI ani numeru strony.

### R10-C04 — priorytet krytyczny: poprawna nazwa i rola §1.3
Pod etykietą roli `Producent` / `Dystrybutor` znajdź właściwą wartość `Nazwa lub nazwa handlowa` i ewentualną kontynuację nazwy na kolejnych wierszach **tego samego §1.3 i logicznego SDS**. Nie traktuj słowa `Producent`/`Dystrybutor` jako nazwy firmy. Dla KCH-01/02 oczekiwana jest **pełna wielowierszowa nazwa** z części `CX80 POLSKA AGATA NADERA` + `DARIUSZ NADERA SPÓŁKA` + `KOMANDYTOWA` zachowana bez utraty segmentów; dokładne odstępy łączenia dobierz z dowodów PDF i udokumentuj. Dla KCH-03 `AG TermoPasty Grzegorz Gąsowski` z rolą `DISTRIBUTOR`; KCH-04/05 ta sama nazwa z rolą `MANUFACTURER`; KCH-01/02 rola `MANUFACTURER`. Zachowaj dosłowną rolę i cytaty. Wyklucz osobę kontaktową, adres, NIP/REGON, stopkę oraz przeskok między kartami. W G2 dodaj / dostosuj **wąską kontrolę semantyczną**: rola nie może udawać nazwy podmiotu, `FOUND` wymaga dowodu faktycznej nazwy w §1.3. Nie rozszerzaj G2 na niepowiązane pola.

### R10-C05 — nazwa handlowa KCH-06
Dla §1.1 `Nazwa handlowa produktu: Farba KONTUR ŻOŁTY.` wynik `FOUND` ma mieć **samą nazwę** `Farba KONTUR ŻOŁTY.`. Cytat źródłowy pozostaje pełny z etykietą; zachowaj kropkę i polskie znaki. Nie usuwaj innej interpunkcji niż dozwolone symbole znaku towarowego w nazwie operacyjnej.

### R10-C06 — aktualizacja z dwóch wierszy kolumn KCH-06
Dla nagłówka `Edycja | Data wydania | Data aktualizacji` i następnego wiersza `04 | 08.01.2021 | 17.07.2025` odczytaj **`issue_date=2025-07-17`** z właściwej kolumny i cytatu. Nie zastępuj jej datą wydania `08.01.2021`, numerem edycji ani numerem strony. Brak/zmiana kolejności kolumn nie uprawnia do przypuszczeń.

### R10-C07 — `Edycja` jako rewizja KCH-06
Z **tej samej, jednoznacznie powiązanej kolumny** zapisz `revision="04"` (bez zamiany w `4` lub `V04`). Brak → `NOT_FOUND`; sprzeczne odczyty → `AMBIGUOUS`; nie korzystaj z `rew.4` w nazwie PDF, `2/PL`, UFI, dat ani numeracji stron.

### R10-C08 — §1.3 KCH-06
Dla `1.3. Dane dotyczące dostawcy karty charakterystyki:` rozpoznaj następną nazwę `KON-TUR sp. z o. o. sp. k.`, `FOUND`, z rolą `SUPPLIER`. Dwukropek na końcu nagłówka nie może blokować ekstrakcji. Nie pobieraj ulicy, telefonu, §1.4 ani frazy `Telefon alarmowy producenta`; nie podnoś roli do `MANUFACTURER`.

### R10-C09 — segmentacja `SEKCJA 1.`
Rozpoznawaj początek logicznego SDS także przy `SEKCJA 1.` (dotychczas `SEKCJA 1:`). Na oryginalnym KCH-06 pozostaje **DOC-001 1–17**. Syntetyczny lub testowy PDF z **dwoma** SDS, w tym kolejnym początkiem `SEKCJA 1.`, musi zostać podzielony poprawnie, bez fałszywego podziału na `SEKCJA 10.`, `SEKCJA 16.`, `1.1.` lub nagłówek powtórzony na stronie. Unikaj twardego dopasowania do marki i indeksu strony. Zachowaj dotychczasowe granice 3M i innych formatów.

## 5. EXPECTED OUTPUT — oryginalne PDF i dowody

| ID | Strony | product_name | issue_date | revision | parties[].role i nazwa |
|---|---:|---|---|---|---|
| KCH-01 | 1–8 | `EGR CLEANER` | `2023-01-23` | `2.0` | `MANUFACTURER`, pełna nazwa CX80 (wielowierszowa) |
| KCH-02 | 1–11 | `RC72` | `2023-01-23` | `2.0` | `MANUFACTURER`, pełna nazwa CX80 (wielowierszowa) |
| KCH-03 | 1–13 | `Topnik RF 800` | `2024-01-25` | `13.0` | `DISTRIBUTOR`, `AG TermoPasty Grzegorz Gąsowski` |
| KCH-04 | 1–13 | `Lakier PVB 16` | `2024-02-27` | `6.0` | `MANUFACTURER`, `AG TermoPasty Grzegorz Gąsowski` |
| KCH-05 | 1–14 | `Lakier PVB 60` | `2024-01-26` | `12.0` | `MANUFACTURER`, `AG TermoPasty Grzegorz Gąsowski` |
| KCH-06 | 1–17 | `Farba KONTUR ŻOŁTY.` | `2025-07-17` | `04` | `SUPPLIER`, `KON-TUR sp. z o. o. sp. k.` |

Dla wszystkich sześciu: `manufacturer_product_code=NOT_FOUND/null` (UFI nie jest kodem producenta); odpowiednie `FOUND` mają poprawny `source_text` + stronę/sekcję/nagłówek; wynik ma pozostać `PENDING_REVIEW`, `REQUIRES_HUMAN_REVIEW`, z koniecznością zatwierdzenia producenta. **`G1/G2/G3 PASS` nie oznacza, że można zapisać produkt do Core.**

## 6. ACCEPTANCE CRITERIA

| ID | Kryterium / dowód |
|---|---|
| **R11-1** | Preflight: lokalny `main`, upstream i stan katalogu 13 ACTIVE (albo uzasadnione, zatwierdzone zmiany), 7 PDF / 6 unikalnych SHA, nienaruszone źródła i zastane pliki. |
| **R11-2** | KCH-01…05: pięć nazw, pięć dat aktualizacji i pięć wersji dokładnie jak w tabeli; `FOUND` z właściwego źródła, testami negatywnymi. |
| **R11-3** | KCH-01…05: pełne nazwy podmiotów i role MANUFACTURER/DISTRIBUTOR, bez `parties[].name="Producent"`/`"Dystrybutor"`; wąska negatywna kontrola G2 z wykrywalnym błędem semantycznym. |
| **R11-4** | KCH-06: nazwa bez prefiksu, aktualizacja 2025-07-17, rewizja dosłownie `04`, dostawca KON-TUR jako SUPPLIER, prawidłowe dowody i negatywy. |
| **R11-5** | Segmentacja: KCH-06 1–17 + test złączenia dwóch SDS przy `SEKCJA 1.`, bez nieprawidłowych cięć i bez regresji 3M. |
| **R11-6** | CLI na 6 unikalnych PDF: 6 Evidence DRAFT + 6 walidacji odczytanych z dysku; G1/G2/G3, `PENDING_REVIEW` i ostrzeżenia human review; duplikat D-02 nieprzetwarzany drugi raz. |
| **R11-7** | Focused tests R11 (w tym złe role, daty, brak/konflikt rewizji, kolumny, wielowierszowe nazwy) + ukierunkowana regresja R2/R3/R5/R7/R9 i OPEX/SYLGARD/3M/WEICON/LOCTITE; raportuj komendy, liczbę PASS/FAIL/SKIP. |
| **R11-8** | Minimalny diff i raport; bez nieautoryzowanych zmian Core/DB/UI/importera/kontraktu JSON/PDF, bez OCR/LLM, bez automatycznej rejestracji podmiotu. |

## 7. Raport, Git i STOP

Zapisz `docs/task_reports/TASK-062_R11_REPORT.md`: tabela **R11-1…R11-8** z dowodami, osobno wynik każdego PDF (przed→po), szczegóły reprezentacji ról i wielowierszowej nazwy, diff/zmienione pliki, testy i komendy, odchylenia, ograniczenia. Wskaż wprost czy dotychczasowy kontrakt Evidence obsługuje `DISTRIBUTOR`; gdy nie, nie maskuj problemu fałszywą rolą ani nie rozszerzaj samodzielnie domeny.

Po pozytywnych testach i braku STOP **wykonaj selektywny commit i zwykły push do `origin/main`**, obejmujący tylko potrzebny kod, test R11 i raport R11. Przed commitem sprawdź `git diff --cached --stat` i `git diff --cached --check`; uwzględnij, że w repo są wcześniej nieśledzone dokumenty — **bez `git add .`**. Podaj SHA i wynik `HEAD=origin/main`; jeśli publikacja nie nastąpi, wyraźnie to zaraportuj. Dopuszczone przez Architekta źródłowe PDF już istnieją w Git, ale **nie dodawaj** roboczych JSON/`tmp/`, sekretów ani niepowiązanej dokumentacji. Nie wykonuj force-push, resetów, zmian historii.

**STOP** przy: sprzeczności z zatwierdzonym kontraktem `parties.role`, niemożności wyodrębnienia pełnej nazwy podmiotu z dowodem, konieczności zmiany Core/schema/importera, niewyjaśnionej regresji lub wyniku sprzecznym ze źródłem. Raportuj blokadę i wykonane niezależne części; nie maskuj jej `PASS`. **Nie rozpoczynaj następnej paczki ani integracji z UI/DB.**
