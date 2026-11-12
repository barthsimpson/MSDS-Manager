# TASK-062-R15 — Cyna i pasty: wdrożenie R14-C01–C10 i regresja

**Status:** READY / AUTHORIZED przez Architekta, 2026-11-12  
**TASK MODE:** PATCH (rozszerzenie istniejącego ekstraktora oraz jego kontroli Evidence; bez integracji z Core)  
**Poprzedni etap:** TASK-062-R14 — diagnostyka ACCEPTED; R14-C11 jawnie wyłączony.  
**Punkt startowy wg R14:** `main = origin/main = 2b5f05ee323fcf9283bb362d17c1ea8e44595a81`, 13 ACTIVE A-001–A-013. Jeśli HEAD się zmienił, udokumentuj stan i sprawdź zgodność, nie resetuj pracy użytkownika.

## GOAL

Poprawić istniejącą ekstrakcję i kontrolę Evidence tak, aby dziewięć oryginalnych SDS z `data/sds/Paczki/paczka 6 cyna, pasty/` generowało poprawne, źródłowo uzasadnione propozycje nazw grupowych, dat, rewizji i podmiotów; nie wprowadzać automatycznego rozbijania SDS na produkty. Potwierdzić brak regresji wcześniejszych paczek.

## AUTHORITATIVE CONTEXT

1. `docs/task_reports/TASK-062_R14_REPORT.md` — macierz CP-01..CP-09 i kandydaci R14-C01..C11 (źródłowe cytaty i negatywy).
2. Dziewięć oryginalnych PDF z paczki 6 — jedyne źródło wartości; nazwy plików i stopki nie zastępują dowodu z właściwego kontekstu.
3. Obowiązujące `SDS-JSON-001`, reguły ekstraktora, `GOV-001`, `GOV-002`, `AGENTS.md` i obowiązujący Core — czytaj tylko potrzebne fragmenty, nie zmieniaj chronionych kontraktów.
4. Decyzja Architekta po R14: **zatwierdzone R14-C01–C10** z rozstrzygnięciami: `5.0/PL` jest pełnym literalnym numerem rewizji; `(2)` CP-05 **nie** mapuje się automatycznie na `revision`; CP-08 `Data opracowania` jest datą dokumentu wyłącznie w jednoznacznym kontekście pierwszego wydania; **R14-C11 osobno / poza R15**.

## KNOWN STARTING POINTS / CHANGE SURFACE

- `app/infrastructure/filesystem/sds_alias_matcher.py` oraz `app/infrastructure/filesystem/sds_evidence_pipeline.py` — istniejące dopasowania, kontekst §1, normalizacja i bramki G2/G3.
- `scripts/extract_sds_evidence.py` — użyć istniejącego CLI, bez zmiany jego publicznego zachowania.
- `config/sds_aliases.json` — preflight i regresja; **nie dodawaj ACTIVE ani nie zmieniaj katalogu bez potrzeby i osobnej decyzji**.
- `tests/unit/test_task062_r15_cyna_pasty.py` — nowe testy układów i negatywów. Istniejące testy R2/R3/R5/R7/R9/R11/R13 — regresja.
- Raport końcowy: `docs/task_reports/TASK-062_R15_REPORT.md`.

## DO — zatwierdzone reguły

| Kandydat | Wymagane zachowanie i bezpieczne granice |
|---|---|
| **C01** | W kontekście sekcji 1 rozpoznawać źródłowy zapis `11.1 Identyfikator produktu` CP-01/CP-06 i następującą po nim etykietę `Nazwa produktu`; nie traktować `11.1` z sekcji 11 jako §1.1. |
| **C02** | CP-03/CP-04: etykieta `NAZWA HANDLOWA:` nie może być `product_name=FOUND`; pobierać nazwę z kolejnego wiersza §1.1 z cytatem obu wierszy. G2 ma odrzucać samą etykietę jako wartość, również przy poprawnej stronie i cytacie. |
| **C03** | CP-03: §1.3 i podmiot na s. 2 w obrębie **tego samego** SDS; `SUPPLIER=Cynel-Unipress Sp. z o.o.`. Nie przenosić danych między SDS ani uznawać adresu/e-maila za nazwę. Zachować prawidłowy CP-04 na s. 1. |
| **C04** | `Data aktualizacji: YYYY-MM-DD` dla CP-01/06 = `2020-12-14`, CP-03/04 = `2025-07-08`; odrzucić historyczne `Data wydania: 2015-12-12`, daty z nazw plików i wartości kalendarzowo niemożliwe. Spójne powtórzenia nie są konfliktem, sprzeczne — `AMBIGUOUS/null`. |
| **C05** | `Wydanie 2` CP-01 → `revision="2"`; `Wydanie 3` CP-06 → `revision="3"`. Samo słowo `Wydanie` bez liczby nie jest rewizją i nie unieważnia poprawnych dowodów. |
| **C06** | CP-03/CP-04 `wersja: 5.0/PL` → **dokładnie** `revision="5.0/PL"`, bez obcinania `/PL`, z kontekstem nagłówka i dowodem źródłowym. |
| **C07** | CP-05: ze źródłowej sekwencji dat `25.01.2016/26.03.2017 r. (1) / 07.03.2022 r. (2)` wybrać bieżącą, ostatnią jawnie datowaną aktualizację `2022-03-07` z cytatem obejmującym sekwencję. Nie mapować `(2)` ani `Aktualizacja (2)` na `revision`; przy braku innego jednoznacznego źródła `revision=NOT_FOUND/null`. Nie wybierać wcześniejszych dat. |
| **C08** | CP-08: przy `Data opracowania: 08.11.2024`, `Data aktualizacji: -`, `Wersja 1.0` → `issue_date=2024-11-08`, `revision="1.0"`. Źródłowa etykieta musi pozostać jawna w Evidence; data opracowania jest fallbackiem **tylko** przy jednoznacznym pierwszym wydaniu i braku rzeczywistej daty aktualizacji. Nie podstawiać kreski jako daty. |
| **C09** | CP-05 `Dostawca:` → `SUPPLIER: LUT – SPAW Sp. z o.o.`; CP-08 `Nazwa i adres:` w §1.3 → `SUPPLIER: REBALL TECHNOLOGY Sp. z o.o.`. Nie pobierać etykiety, adresu, numeru telefonu ani osoby odpowiedzialnej jako nazwy firmy; G2/G3 powinny weryfikować kontekst i rolę. |
| **C10** | CP-05: zachować raw `INSTALFLUX TLA                   -4N` w dowodzie, a jako nazwę operacyjną zaproponować `INSTALFLUX TLA-4N` wyłącznie dlatego, że identyczna postać jest potwierdzona w tej samej SDS. Nie wdrażać globalnego usuwania spacji przy znakach `-`/`/`. |

**Oczekiwane wyniki pozostałych dokumentów:** CP-02 zachowuje `Anti-Seize Pasty montażowe Presspack`, kod `260001`, datę `2022-12-16`, rewizję `4.03`, `SUPPLIER WEICON`; CP-07 zachowuje `Pasta termoprzewodząca H`, `2023-01-26`, `11.0`, `MANUFACTURER AG TermoPasty`; CP-09 zachowuje `Topnik TK 83`, `2024-01-26`, `7.0`, ten sam `MANUFACTURER`. Dla wszystkich bez jawnego kodu `manufacturer_product_code=NOT_FOUND/null` — bez UFI, CAS czy liczby wariantu jako zamiennika.

## DO NOT — granica R14-C11 i ochrony

- **Nie realizuj C11:** bez modelowania listy wariantów, powiązań jeden SDS → wiele PRODUCT, automatycznego tworzenia produktów, rozbijania na osobne logiczne SDS po przecinku/ukośniku i zmiany Core/kontraktu JSON. Zachowaj jedno logiczne SDS na plik i źródłową nazwę grupową.
- **CP-03:** występuje rozbieżność §1.1 `/ EVO-H` versus stopka `/ SW26`; zachowaj dokładną nazwę grupową z §1.1 i nie rozstrzygaj listy wariantów ani nie nadpisuj jej stopką. Raport musi jawnie wykazać nierozstrzygniętą rozbieżność oraz STOP powiązań z PRODUCT; jeśli istniejący kontrakt dopuszcza ostrzeżenie/niejednoznaczność, użyj zgodnego mechanizmu bez zmiany schematu.
- **CP-04:** zachowaj źródłowy zapis `Spoiwo lutownicze bezołowiowe z topnikiem 1.1.3 /CF48`; nie usuwaj odstępu przed `/CF48` bez odrębnej zatwierdzonej reguły (C10 dotyczy wyłącznie udowodnionego przypadku CP-05).
- Nie ruszaj PostgreSQL, importera, UI, Safety, Components, modelu ról, zatwierdzania producentów ani Core; bez OCR/LLM, bez zmiany PDF i bez wymuszania instalacji narzędzi.
- Nie wykonuj `git add .`, nie dodawaj przypadkowych nieśledzonych TASK/REPORT, `tmp/` i plików źródłowych; nie twórz branch/worktree na potrzeby R15.

## VALIDATION — proporcjonalne do ryzyka

1. **Preflight:** istniejący `main`, aktualny HEAD/upstream, stan plików śledzonych i nieśledzonych, lista 9 PDF i SHA z R14, 13 ACTIVE. Nie resetować ani usuwać cudzych plików.
2. **Focused tests R15:** dziewięć oryginalnych źródeł + syntetyczne negatywy: etykieta jako nazwa (G2 FAIL); `11.1` w §11; §1.3 na kolejnej stronie i granica obcego SDS; pusta/sprzeczna data, ISO i chronologia, konflikt rewizji, `5.0/PL`, `(2)` bez rewizji, data opracowania wobec rzeczywistej aktualizacji, brak nazwy dostawcy, CP-05 normalizacja wyłącznie z potwierdzeniem. Testy złączonych SDS dla ryzyka kontekstu/segmentacji.
3. **Regresja obowiązkowa:** uruchomić istniejące testy R2/R3/R5/R7/R9/R11/R13 + R15, wykazać łączne PASS/FAIL/SKIP i brak zmian w wynikach wcześniejszych źródeł (OPEX/SYLGARD/3M/WEICON/LOCTITE/KCH/COMPOUND). Nie maskować niepowodzeń aktualizacją oczekiwań bez uzasadnienia.
4. **Rzeczywisty CLI:** 9 unikalnych oryginalnych PDF → świeży ignorowany `tmp/task062r15_cyna_pasty_final/`, 9 zapisanych `evidence.json` + 9 `validation.json` odczytanych po zapisie, źródłowe cytaty, numery stron/sekcji, zachowane `PENDING_REVIEW`, `REQUIRES_HUMAN_REVIEW`, poprawne G1/G2/G3. PASS bramek nie oznacza zatwierdzenia danych w Core.
5. **Kontrola zakresu:** diff, `git diff --check`, brak zmian katalogu aliasów (13 ACTIVE), Core, DB, UI, importer, PDF i kontraktu JSON; wyjątkowy konieczny konflikt → STOP.

## KRYTERIA AKCEPTACJI

| ID | Kryterium | Dowód w raporcie |
|---|---|---|
| **R15-1** | Preflight, 9 PDF/9 SHA, 13 ACTIVE, brak naruszenia pracy użytkownika | HEAD/upstream, SHA i lista zmian |
| **R15-2** | C01–C03: prawidłowe nazwy CP-01/03/04/06, dostawca CP-03 s. 2 i G2 wyklucza samą etykietę | Porównanie PDF–Evidence, cytaty, testy negatywne |
| **R15-3** | C04–C06: daty ISO, `Wydanie 2/3`, pełne `5.0/PL` | Wyniki czterech źródeł, konflikt i regresja |
| **R15-4** | C07–C08: CP-05 `2022-03-07` bez rewizji z `(2)`; CP-08 `2024-11-08` i `1.0` w zatwierdzonym kontekście | Odczyt JSON, cytaty, negatywy chronologii |
| **R15-5** | C09–C10: dwóch dostawców `SUPPLIER`, raw vs operacyjna nazwa `INSTALFLUX TLA-4N` bez globalnej normalizacji | Dowody §1.1/§1.3, G2/G3, negatywy |
| **R15-6** | Wszystkie 9 SDS: pojedynczy DOC-001, brak zmyślonych kodów i produktów, CP-02/07/09 bez pogorszenia, CP-03 konflikt wariantów jawnie nierozstrzygnięty | Macierz dziewięciu zapisanych Evidence JSON |
| **R15-7** | Nowe testy focused i regresja R2/R3/R5/R7/R9/R11/R13/R15 bez FAIL; bez zmiany 13 ACTIVE | Konkretne komendy i wyniki |
| **R15-8** | 9 przebiegów CLI, 9 DRAFT + 9 walidacji; prawidłowe dowody, statusy human review i bramki | Zapisane artefakty, lokalizacje, odczyt wyników |
| **R15-9** | Zmiany ograniczone do ekstraktora/testów/raportu, kontrolowany commit i push na main po testach; STOP bez C11 i kolejnej paczki | Diff, lista commitowanych plików; SHA i potwierdzenie origin/main po publikacji |

## REPORT — `docs/task_reports/TASK-062_R15_REPORT.md`

Raport krótki, ale kompletny: macierz CP-01..CP-09 **przed → po** z nazwą, kodem, datą, rewizją, rolami, stroną i dowodem; rozliczenie C01–C10 i R15-1..R15-9; lista zmodyfikowanych plików, testy i ich wyniki, ewentualne odstępstwa, potwierdzenie odrębności C11 oraz nierozstrzygniętej rozbieżności CP-03. Nie opisuj jako `FOUND` danych niepewnych. Podaj SHA końcowego commita po publikacji (w komunikacie wykonawczym, jeśli raport został już commitowany).

## STOP CONDITIONS

Sprzeczność z obowiązującym kontraktem Evidence; konieczność zmiany Core, struktury PRODUCT–SDS, normalizacji wariantów lub katalogu aliasów bez autoryzacji; nieodróżnialne dane wymagające zgadywania; niesprawna regresja; konieczność wychodzenia poza paczkę. W takim przypadku zakończ bez części wykraczającej poza zakres, opisz konkretną blokadę i przedstaw Architektowi. Nie rozpoczynaj R16 ani integracji po R15.

**AUTORYZACJA:** decyzja Architekta zatwierdzająca R14-C01–C10, z wydzieleniem R14-C11 oraz precyzyjną semantyką CP-05 i CP-08.
