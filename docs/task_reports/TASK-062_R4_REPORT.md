# TASK-062-R4 — 3M DP-490: rozpoznanie aliasów

**Status:** DONE — macierz do decyzji Architekta; nowe aliasy pozostają `CANDIDATE`, bez aktywacji. **Data:** 2026-11-10. Wynik diagnostyczny nie jest zatwierdzonym Golden Set ani kompletnym Evidence JSON DRAFT.

## Preflight i przebieg

- Pierwotne repozytorium `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, gałąź `main`, HEAD i `origin/main`: `7f6e86c70ea51e72ae6540d5e3def273395d5999`. Nie tworzono gałęzi ani worktree; zastane pliki robocze pozostawiono.
- Źródło przebiegu: śledzony `docs/sds_Work/3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf`. Kopia pod `data/sds/Paczki/paczka 17 inne/` ma identyczny SHA-256. **SHA-256:** `deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48` przed i po odczycie. PDF ma 49 stron; wszystkie 49 mają warstwę tekstową, a pipeline oznacza źródło `READABLE`. Bez OCR. Nazwa pliku służy wyłącznie lokalizacji źródła, nie ustaleniu wartości domenowych.
- Istniejący pipeline R3: `app/infrastructure/filesystem/sds_evidence_pipeline.py` i `scripts/extract_sds_evidence.py`; katalog `config/sds_aliases.json` zawiera dokładnie dziewięć `ACTIVE`: A-001 `Nazwa produktu`, A-002 `Kod produktu`, A-003 `Mfg. in U.S.A and exported by`, A-004 `EU Only Representative`, A-005 `Data wydania/Data aktualizacji`, A-006 `Wersja`, A-007 `Nazwa wyrobu`, A-008 `Aktualizacja`, A-009 `IDENTYFIKACJA FIRMY`.
- Przebieg: `.\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence 'docs/sds_Work/3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf' --output-dir tmp/task062r4_3m_diagnostic_20261110 --source-id 3M-DP490-R4`. Pliki `3M-DP490-R4.evidence.json` i `.validation.json` są w ignorowanym `tmp/`.
- Runtime: trzy dokumenty `PENDING_REVIEW`; G1/G2/G3 = `PASS`, bez błędów strukturalnych; G3 zgłasza dla każdego `MANUFACTURER_REQUIRES_HUMAN_REVIEW`. `product_name`, `manufacturer_product_code`, `issue_date` i `revision` są we wszystkich trzech `NOT_FOUND`, `parties=[]`. PASS bramek oznacza poprawność struktury i brak niepopartych wartości, **nie** udaną identyfikację 3M.

## Trzy odrębne SDS i granice

| Dokument | Zakres PDF | Dowód odrębności z tekstu PDF |
|---|---|---|
| `DOC-001` — zestaw | 1–3 | S. 1, §1.1: `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Kit`; nagłówek zawiera fragmenty `ID dokumentu:` i `19-3248-2`; s. 1: `Numery ID dokumentów` ... `składowych zestawu:` oraz `19-2630-2, 19-2691-4`; stopka s. 3 oznacza stronę 3 z 3. Na s. 1 jest nagłówek `IDENTYFIKACJA SUBSTANCJI/MIESZANINY I IDENTYFIKACJA` / `PRZEDSIĘBIORSTWA`, lecz bez literalnego `SEKCJA 1:`. |
| `DOC-002` — Part B | 4–26 | S. 4, `SEKCJA 1`, §1.1: `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part B`; nagłówek zawiera `ID dokumentu:` i `19-2630-2`; stopki s. 4/26 oznaczają 1 z 23 / 23 z 23. |
| `DOC-003` — Part A | 27–49 | S. 27, `SEKCJA 1`, §1.1: `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part A`; nagłówek zawiera `ID dokumentu:` i `19-2691-4`; stopki s. 27/49 oznaczają 1 z 23 / 23 z 23. |

Obecna segmentacja poprawnie otwiera `DOC-002` i `DOC-003` na stronach z nową `SEKCJA 1`; `DOC-001` zaczyna się na pierwszej stronie PDF. Identyfikatory `19-...` w nagłówku to **ID dokumentów**, nie kod produktu producenta. Źródło zestawu wskazuje numery dokumentów części, ale ich wartości nie wolno przenosić do pól produktu zestawu.

## Macierz identyfikacyjna: źródło, obecny stan, oczekiwane zachowanie

W kolumnie „cytat” podano krótkie dosłowne fragmenty z właściwej strony; wielokropek między fragmentami oznacza pominięte odstępy lub tekst, a nie nowy cytat. Wartości oczekiwane są **propozycjami do decyzji**, nie wynikami obecnego extractora. `®` i `™` usuwa się tylko z nazwy operacyjnej; cytat Evidence zachowuje oryginał.

| SDS / pole PoC | Strona, kontekst i krótki cytat z PDF | Teraz | Oczekiwane zachowanie / luka ACTIVE |
|---|---|---|---|
| Zestaw — `product_name` | S. 1, §1.1: `1.1. Identyfikator produktu` → `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Kit` | `NOT_FOUND` | `FOUND`; operacyjnie `3M Scotch-Weld DP-490 Black Structural Adhesive Kit`, w Evidence pełny cytat. Brak etykiety `Identyfikator produktu` i reguły wartości w następnej linii; dodatkowo brak drukowanego `SEKCJA 1`. |
| Zestaw — `manufacturer_product_code` | S. 1, §1.1: `Numery` ... `identyfikacyjne produktu`, `UU-0101-3332-8 ... UU-0101-3333-6 ... UU-0101-3334-4`, `7100200499 ... 7100200500 ... 7100200501` | `NOT_FOUND` | `AMBIGUOUS`: sześć identyfikatorów, brak podstawy do wyboru jednego skalarnego kodu. Żaden `19-...` z nagłówka nie jest kodem produktu. Wymagana decyzja o obsłudze wielowartościowości; bez niej `value=null`. |
| Zestaw — `issue_date` | S. 1, nagłówek: `Data aktualizacji:` ... `06/07/2023`; obok `Zastępuje wersję` ... `17/11/2022` | `NOT_FOUND` | `FOUND` `2023-07-06` z bieżącej daty DD/MM/YYYY; `17/11/2022` jest historyczna. Brak `Data aktualizacji` i reguły dwóch kolumn. |
| Zestaw — `revision` | S. 1, nagłówek: `Numer` ... `wersji:` ... `13.00`; niżej `Numer wersji transportu:` bez wartości | `NOT_FOUND` | `FOUND` `13.00`. Brak etykiety `Numer wersji` z tolerancją odstępów i wykluczeniem wersji transportu. |
| Zestaw — podmioty | S. 1, §1.3: `Dane dotyczące dostawcy karty` ... `charakterystyki`; wiersz `Adres:` zawiera `3M Poland Sp. z o.o.` | `NOT_FOUND` (`parties=[]`) | `FOUND` tylko `SUPPLIER` = `3M Poland Sp. z o.o.` z cytatem i rolą źródłową. Brak reguły wydobycia nazwy z wiersza adresowego; producent źródłowy pozostaje nierozstrzygnięty. |
| Part B — `product_name` | S. 4, `SEKCJA 1`, §1.1: `1.1. Identyfikator produktu` → `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part B` | `NOT_FOUND` | `FOUND`; operacyjnie `3M Scotch-Weld DP-490 Black Structural Adhesive Part B`, Evidence dosłowne. Brak etykiety/reguły następnej linii; nie używać nazwy zestawu ani Part A. |
| Part B — `manufacturer_product_code` | S. 4, §1.1: `Numery` ... `identyfikacyjne produktu`, `UU-0096-8394-5 ... UU-0115-9462-7`, `7100199097 ... 7100269978` | `NOT_FOUND` | `AMBIGUOUS`: cztery identyfikatory, brak uprawnionego wyboru jednego kodu. Nagłówkowe `19-2630-2` jest ID SDS, nie kodem produktu. |
| Part B — `issue_date` | S. 4, nagłówek: `Data aktualizacji:` ... `06/07/2023`; `Zastępuje wersję` ... `19/12/2022` | `NOT_FOUND` | `FOUND` `2023-07-06`; `19/12/2022` pozostaje datą poprzedniej wersji. Brak aliasu bieżącej daty i reguły sąsiedniej kolumny. |
| Part B — `revision` | S. 4, nagłówek: `Numer` ... `wersji:` ... `14.00` | `NOT_FOUND` | `FOUND` `14.00`; nie pobierać `13.00` zestawu ani `19-2630-2`. Brak etykiety/wariantu odstępów. |
| Part B — podmioty | S. 4, §1.3: `Dane dotyczące dostawcy karty` ... `charakterystyki`; wiersz `Adres:` zawiera `3M Poland Sp. z o.o.` | `NOT_FOUND` (`parties=[]`) | `FOUND` tylko `SUPPLIER`; nazwa przed adresem pocztowym, bez przypisania producenta. Brak reguły kontekstowej. |
| Part A — `product_name` | S. 27, `SEKCJA 1`, §1.1: `1.1. Identyfikator produktu` → `3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part A` | `NOT_FOUND` | `FOUND`; operacyjnie `3M Scotch-Weld DP-490 Black Structural Adhesive Part A`, Evidence dosłowne. Brak etykiety/reguły następnej linii; nie używać Part B. |
| Part A — `manufacturer_product_code` | S. 27, §1.1: po nazwie bezpośrednio `1.2. Istotne zidentyfikowane zastosowania`; brak bloku `Numery identyfikacyjne produktu` | `NOT_FOUND` | `NOT_FOUND`, `value=null`; nie pożyczać kodów z zestawu/Part B ani ID SDS `19-2691-4`. Brak aliasu nie uzasadnia `FOUND`. |
| Part A — `issue_date` | S. 27, nagłówek: `Data aktualizacji:` ... `26/04/2023`; `Zastępuje wersję` ... `19/12/2022` | `NOT_FOUND` | `FOUND` `2023-04-26`; data poprzednia nie jest bieżącą. Brak aliasu/reguły. |
| Part A — `revision` | S. 27, nagłówek: `Numer` ... `wersji:` ... `14.00` | `NOT_FOUND` | `FOUND` `14.00`; nie pobierać `13.00` zestawu. Brak etykiety/wariantu odstępów. |
| Part A — podmioty | S. 27, §1.3: `Dane dotyczące dostawcy karty` ... `charakterystyki`; wiersz `Adres:` zawiera `3M Poland Sp. z o.o.` | `NOT_FOUND` (`parties=[]`) | `FOUND` tylko `SUPPLIER`, bez automatycznego `PRODUCT.manufacturer_id`. Brak reguły kontekstowej. |

W §1.3 każdej karty wskazano dostawcę karty charakterystyki. Nie stwierdzono tam literalnych ról `MANUFACTURER`, `MANUFACTURER_EXPORTER` ani `EU_REPRESENTATIVE`; dla tych ról stan docelowy to `NOT_FOUND`. Fragmenty `3M` ... `Company` występują w bloku praw autorskich, nie jako jawnie oznaczony producent w §1.3. Zgodnie z BDR-005 v1.2/CORE-001 v1.9 `SUPPLIER` może być wyłącznie kandydatem dla operatora, z zachowaniem roli źródłowej; producent pozostaje do rozstrzygnięcia przez człowieka.

## Pakiet do jednej decyzji Architekta

**Pięć nowych etykiet CANDIDATE, żadna ACTIVE.** C-01–C-05 są identyfikatorami wyłącznie tej macierzy, nie numerami w katalogu aliasów. A-001–A-009 nie są powielane: ich etykiety nie odpowiadają poniższym obserwacjom, a A-008 jawnie odrzuca prefiks `Data `.

| ID / typ | Zaobserwowana etykieta i przykład | Pole / kontekst | Łączenie wartości i przypadek negatywny |
|---|---|---|---|
| C-01 — nowa etykieta + reguła układu | `Identyfikator produktu`; s. 1/4/27, §1.1 | `product.product_name`; `SECTION 1.1` | Następny niepusty wiersz przed blokiem numerów/§1.2; rozdziel `Kit`, `Part B`, `Part A`. Nie brać nagłówka strony ani wiersza `Numery identyfikacyjne produktu`. Źródłowe `™` pozostaje w evidence, wartość operacyjna bez `™`. |
| C-02 — etykieta do rozpoznania, **bez bezpośredniej aktywacji pola skalarnego** | `Numery` ... `identyfikacyjne produktu`; s. 1/4, §1.1 | Potencjalne źródło dla `product.manufacturer_product_code`; decyzja o wielowartościowości wymagana | Kilka `UU-...` i `710...` → `AMBIGUOUS`, nie pierwszy numer. S. 27 brak → `NOT_FOUND`. Nagłówkowe `ID dokumentu:` i `Numery ID dokumentów` ... `składowych zestawu:` są negatywnymi przykładami. |
| C-03 — nowa etykieta + reguła daty | `Data aktualizacji`; s. 1/4/27, nagłówek | `document_metadata.issue_date` | DD/MM/YYYY z bieżącej kolumny → ISO. Nie wiązać sąsiedniego `Zastępuje wersję`, nazwy pliku ani daty praw autorskich. A-008 `Aktualizacja` pozostaje odrębnym aliasem SYLGARD. |
| C-04 — nowa etykieta + reguła układu | `Numer wersji` (PDF rozdziela wyrazy wieloma spacjami); s. 1/4/27, nagłówek | `document_metadata.revision` | Zachować `13.00`/`14.00`; tolerować zmienne odstępy i równoległe `Numer ID dokumentu`. Nie brać `Numer wersji transportu` ani wersji poprzedniej. A-006 `Wersja` nie jest tą etykietą. |
| C-05 — nowa etykieta roli + reguła wiersza adresowego | `Dane dotyczące dostawcy karty` ... `charakterystyki`; s. 1/4/27, §1.3 | `parties[].name`, rola `SUPPLIER` | Z pierwszego `Adres:` wyodrębnić `3M Poland Sp. z o.o.` przed ulicą; zachować dosłowny cytat nazwy, nagłówka roli i adresowego wiersza. Nie brać e-maila, ulicy, bloku praw autorskich z `3M` ... `Company` ani danych z §1.4; nie podnosić roli do `MANUFACTURER`. |

**Pięć reguł kontekstowych do osobnego zatwierdzenia technicznego:** (R-01) dopuścić zestawową stronę z §1.1/§1.3 i nagłówkiem identyfikacji bez literalnego `SEKCJA 1`, ale tylko w obrębie `DOC-001`; (R-02) wiązać nazwę z następnym wierszem §1.1 i normalizować wyłącznie operacyjne `®`/`™`; (R-03) czytać dwukolumnowy nagłówek, zmienne odstępy i bieżącą datę DD/MM/YYYY oraz wersję bez przeniesienia pól sąsiadujących; (R-04) wydobywać nazwę dostawcy z `Adres:` wyłącznie pod nagłówkiem §1.3; (R-05) traktować pluralne identyfikatory produktu jako nierozstrzygnięte wobec skalarnego kodu, bez wyboru pierwszego. To reguły layoutu/interpretacji, nie proste dopisanie tekstu do `config/sds_aliases.json`.

### Testy po zatwierdzeniu, przed ewentualnym ACTIVE

1. Dla oryginalnego SHA powyżej: dokładnie `DOC-001` 1–3, `DOC-002` 4–26, `DOC-003` 27–49; granice potwierdzają ID `19-3248-2` / `19-2630-2` / `19-2691-4` i stopki 3/3, 23/23, 23/23. Zestaw bez `SEKCJA 1` nadal ma §1.1/§1.3.
2. C-01/R-02: trzy różne nazwy i części z właściwych §1.1; `™` usunięte tylko z wartości operacyjnej, pozostawione w krótkim `source_text`; żadna nazwa nie przechodzi między zakresami.
3. C-03/C-04/R-03: bieżące daty `2023-07-06`, `2023-07-06`, `2023-04-26` i rewizje `13.00`, `14.00`, `14.00`, zawsze z własnej pierwszej strony. `17/11/2022` i `19/12/2022` po `Zastępuje wersję` oraz `Numer wersji transportu` nie tworzą bieżących pól; błędny format daty daje stan wymagający przeglądu, nie zgadywanie.
4. C-02/R-05: zestaw i Part B pozostają `AMBIGUOUS` bez arbitralnego kodu; Part A `NOT_FOUND`. `19-...` z nagłówka i odsyłaczy do części nigdy nie staje się kodem produktu.
5. C-05/R-04: każda karta ma jednego `SUPPLIER` z dowodem §1.3, bez automatycznego producenta, eksportera lub przedstawiciela; `3M Company` z copyright i adres/e-mail nie stają się nazwą producenta.
6. G1/G2/G3: każdy `FOUND` ma stronę w swoim `page_range`, sekcję, literalny cytat obecny w PDF i zatwierdzoną etykietę; cytat z innej karty, fałszywa rola, nieaktywny alias albo brak dowodu są odrzucane. Dokumenty pozostają `PENDING_REVIEW`.
7. Regresja OPEX oraz B002-01..04 i testy R2/R3: istniejące dziewięć ACTIVE nadal daje poprzednie wyniki, bez false positive dla nowych etykiet. Osobne negatywne przypadki dla nazw plików, poprzedniej daty i sąsiednich kolumn.

Obecne testy są dostępne i uruchomione bez zmian kodu: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py -q -p no:cacheprovider --basetemp tmp/task062r4_pytest_20261110` → **18 passed in 15.70s**. Powyższe nowe przypadki są planem regresji **po** decyzji, nie testami już zaimplementowanymi.

## R4-1–R4-6 i granice

| Kryterium | Wynik |
|---|---|
| R4-1 | PASS: pierwotny `main`, zgodność HEAD/origin, śledzony PDF z SHA-256 i 49 stronami tekstu; bez nowych worktree. |
| R4-2 | PASS: trzy `document_key` i rozłączne `page_range` z cytatami nagłówków, §1.1, ID dokumentów i stopek. |
| R4-3 | PASS diagnostyczny: 15 wierszy macierzy zawiera stan obecny, źródłową stronę/sekcję/cytat, oczekiwany stan i konkretną lukę; brak aliasów nie został zamieniony w pozorne `FOUND`. |
| R4-4 | PASS jako propozycja: pięć niedublujących się etykiet CANDIDATE, pięć odrębnych reguł kontekstowych i siedem grup przyszłych testów; brak automatycznego ACTIVE. |
| R4-5 | PASS dla rozpoznania: zakresy nie nachodzą na siebie; daty bieżące i poprzednie, role oraz ID SDS/kody są rozdzielone; nie wykorzystano nazwy pliku jako dowodu domenowego. |
| R4-6 | PASS: jedynym nowym plikiem poza ignorowanymi diagnostykami `tmp/` jest ten raport. Bez zmiany PDF, katalogu aliasów, matcherów, Core, Safety, UI, migracji i PostgreSQL; bez commit/push. |

**Decyzja wymagana przed kontynuacją:** zatwierdzić lub odrzucić C-01–C-05 oraz R-01–R-05, w szczególności sposób traktowania pluralnych identyfikatorów wobec skalarnego `manufacturer_product_code`. Do tego czasu trzy wyniki 3M pozostają niekompletnymi DRAFT do przeglądu. **STOP.**
