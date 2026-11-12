# TASK-062-R5 — 3M DP-490: aktywacja zatwierdzonych reguł i Evidence JSON DRAFT

**Status:** READY / AUTHORIZED przez Architekta, 2026-11-10  
**Projekt:** MSDS Manager  
**Wykonawca:** Codex  
**Miejsce pracy:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main` (bez nowego worktree/brancha)  
**Ostatni potwierdzony punkt odniesienia:** `7f6e86c70ea51e72ae6540d5e3def273395d5999` (przed rozpoczęciem sprawdź HEAD i origin/main; nie resetuj cudzej pracy).

## 1. Podstawa i cel

Źródła obowiązujące: `TASK-062-R4_REPORT.md` (macierz dowodów na oryginalnym 3M DP-490, 49 stron, SHA-256 `deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48`), TDR-012 v1.0-approved, SDS-ALIAS-001, SDS-JSON-001, BDR-005 v1.2-approved, CORE-001 v1.9-approved oraz działające artefakty R2/R3.

**Decyzja Architekta:** zatwierdzone do wdrożenia i testów C-01–C-05 oraz reguły R-01–R-05 z R4, przy czym C-02 nie może wyznaczać jednego kodu spośród wielu. Decyzja obejmuje dalsze przetwarzanie *kolejnych paczek* tym samym mechanizmem; przyszły proces zatwierdzania w UI ma korzystać z tego modułu, lecz **integracja z UI / kontrolowanym importem jest odrębnym etapem**.

**Wynik R5:** trzy poprawnie odseparowane, źródłowo udokumentowane logiczne SDS w `Evidence JSON DRAFT` dla 3M DP-490; aktywacja wyłącznie przetestowanych reguł; bez zapisów do Core.

## 2. Zakres wykonania

1. Preflight: przeczytaj obowiązujące kontrakty i bieżący kod R2/R3; sprawdź lokalny `main`, stan roboczy, dziewięć istniejących ACTIVE, SHA PDF i rozbieżności. Pracuj na obecnym mechanizmie `sds_evidence_pipeline.py`, matcherze, katalogu aliasów i CLI; nie buduj osobnego parsera 3M.
2. Wprowadź **C-01** (`Identyfikator produktu` → `product.product_name`) z wartością z następnego właściwego wiersza §1.1, wyłącznie w obrębie logicznego SDS. Z normalizacji operacyjnej usuń tylko `®` i `™`; w `source_text` i surowym dowodzie pozostaw zapis literalny.
3. Wprowadź **C-03** (`Data aktualizacji` → `document_metadata.issue_date`) z poprawnym powiązaniem daty bieżącej w dwukolumnowym nagłówku, `DD/MM/YYYY` → ISO. `Zastępuje wersję` musi być wykluczone.
4. Wprowadź **C-04** (`Numer wersji` → `document_metadata.revision`) z tolerancją rozdzielonych wyrazów/odstępów; zachowaj `13.00`, `14.00`, `14.00`, wyklucz wersję transportu i numer ID dokumentu.
5. Wprowadź **C-05** (`Dane dotyczące dostawcy karty charakterystyki` → `parties[]`, rola `SUPPLIER`) jako regułę ograniczoną do §1.3, wyciągając nazwę `3M Poland Sp. z o.o.` z odpowiedniego wiersza `Adres:`. Nie zapisuj `3M Company` z copyright, ulicy ani e-maila jako nazwy podmiotu i nie zmieniaj roli na `MANUFACTURER`.
6. **C-02:** rozpoznaj kontekst `Numery identyfikacyjne produktu`, ale bez aktywowania arbitralnego mapowania wielu identyfikatorów na pojedyncze `manufacturer_product_code`. Dla zestawu i Part B wynik `AMBIGUOUS`, `value=null`, z dowodem i uzasadnieniem; dla Part A `NOT_FOUND`. Jeżeli obecny kontrakt ACTIVE nie pozwala prawidłowo reprezentować samego wykrycia wielości, zostaw C-02 poza ACTIVE i zapewnij równoważne, jawne `AMBIGUOUS` przez zatwierdzoną regułę kontekstową, bez zmiany Core/kontraktu. Nie wprowadzaj nowego pola listowego.
7. Zaimplementuj R-01–R-05 jako **reguły ogólne zależne od sekcji, etykiety i układu**, nie od nazw 3M, nazw plików, pozycji strony lub twardych wartości. Szczególnie R-01: zestaw może mieć §1.1 i §1.3 bez literalnego `SEKCJA 1`, ale nie wolno dopuścić przechodzenia danych między `DOC-001/002/003`.
8. Po testach zgodnych z SDS-ALIAS-001 odnotuj drogę `CANDIDATE → APPROVED (decyzja Architekta) → regresja → ACTIVE` dla tych aliasów, które rzeczywiście nadają się do ACTIVE. Zachowaj dziewięć dotychczasowych ACTIVE i ich wyniki; nie promuj aliasów nieprzetestowanych.
9. Uruchom CLI R3 na rzeczywistym 3M PDF i wygeneruj trzy logiczne wyniki DRAFT oraz raport walidacji w `tmp/` (bez zapisu danych do DB). Raport musi pokazać faktyczne pola, ich statusy i evidence.

## 3. Oczekiwane wyniki na 3M

| Document key | PDF strony | Nazwa operacyjna | issue_date | revision | manufacturer_product_code | parties |
|---|---|---|---|---|---|---|
| DOC-001 | 1–3 | `3M Scotch-Weld DP-490 Black Structural Adhesive Kit` | `2023-07-06` | `13.00` | `AMBIGUOUS`, NULL (wiele kodów) | `3M Poland Sp. z o.o.` jako `SUPPLIER` |
| DOC-002 | 4–26 | `3M Scotch-Weld DP-490 Black Structural Adhesive Part B` | `2023-07-06` | `14.00` | `AMBIGUOUS`, NULL (wiele kodów) | `3M Poland Sp. z o.o.` jako `SUPPLIER` |
| DOC-003 | 27–49 | `3M Scotch-Weld DP-490 Black Structural Adhesive Part A` | `2023-04-26` | `14.00` | `NOT_FOUND`, NULL | `3M Poland Sp. z o.o.` jako `SUPPLIER` |

Wartości oczekiwane z macierzy R4 to **asercje do weryfikacji na oryginalnym PDF**, nie podstawa do hardcodowania. `19-3248-2`, `19-2630-2`, `19-2691-4` są identyfikatorami dokumentów, nie kodami produktów. `MANUFACTURER` nie jest automatycznie zatwierdzony; `SUPPLIER` jest wyłącznie potencjalnym kandydatem do późniejszej decyzji operatora wg CORE-001 v1.9.

## 4. Kryteria akceptacji

| ID | Wymaganie | Dowód |
|---|---|---|
| R5-1 | Preflight w oryginalnym repozytorium, zgodne PDF, bez naruszenia zastanych plików | HEAD/origin, status, SHA, wykaz ACTIVE |
| R5-2 | Dokładnie trzy logiczne SDS i nienachodzące zakresy `1–3`, `4–26`, `27–49` | Wynik CLI + asercje granic |
| R5-3 | Nazwy, daty, rewizje i supplier zgodne z §1.1/§1.3 oraz własnym nagłówkiem każdego SDS | Test na oryginalnym PDF, `FOUND` z page/section/source_text |
| R5-4 | Kody: zestaw i B `AMBIGUOUS`/NULL; A `NOT_FOUND`/NULL; brak użycia ID dokumentów, UFI i nazw pliku | Test pozytywny/negatywny, źródłowy cytat |
| R5-5 | Dowody G1/G2/G3, brak automatycznego producenta i zapisu do Core; wyniki `PENDING_REVIEW` | Validation JSON + kontrola braku zapisów i zależności DB |
| R5-6 | Alias może stać się ACTIVE dopiero po zatwierdzeniu (udzielonym) i pozytywnym teście; istniejące 9 ACTIVE bez regresji | macierz aliasów i test stanu inactive/ACTIVE |
| R5-7 | Regresja OPEX, czterech SYLGARD i R2/R3; także błędne sąsiednie kolumny, „Zastępuje wersję”, transport, copyright, mieszanie kart i znaki ®/™ | komendy testowe, liczba PASS/FAIL i przykłady |
| R5-8 | Raport pokazuje komplet 3M DRAFT i ograniczenie zmian do ekstraktora, aliasów i testów | lista plików, diff, ścieżki artefaktów, wynik walidacji |

## 5. Wyłączenia i granice

**Nie zmieniaj:** schematu PostgreSQL, migracji, Core, BDR/TDR, UI Streamlit, workflow akceptacji, danych rejestrowych, historii, Safety/Components, OCR/LLM, Dockera, konfiguracji środowiska, systemu importu BATCH-001/BATCH-002. Nie rejestruj produktu ani SDS w bazie. Nie przetwarzaj teraz nowych paczek masowo. Nie dodawaj stałych dopasowań po nazwie produktu/producenta.

Plan **późniejszy, nie R5**: wykorzystać ten sam ekstraktor do kolejnych paczek oraz bieżącego przeglądu i zatwierdzania nowych SDS w aplikacji; przygotować zbiorczy plan kontrolowanego importu oparty o obecny workflow, a nie alternatywny mechanizm zapisu.

## 6. Raport i STOP

Zapisz `TASK-062_R5_REPORT.md` w istniejącej konwencji raportów i uwzględnij: R5-1…R5-8 (dowód i wynik), nowe/zmienione aliasy wraz ze stanami, zestawienie trzech SDS, walidację, testy i komendy, listę plików, odstępstwa i ryzyka. Przedstaw commit SHA i wynik zwykłego push **tylko jeśli** zgodnie z lokalnym GOV i bieżącymi zasadami prace są w tym zadaniu utrwalane; nie wykonuj force push. Nie obejmuj commitem niezwiązanych plików.

**STOP** przy sprzeczności kontraktu, potrzebie zmian Core, niejednoznacznym odczycie pola poza bezpiecznym `AMBIGUOUS`/`NOT_FOUND`, błędach regresji albo konieczności naruszenia granic. Nie „naprawiaj przy okazji”. Po raporcie nie uruchamiaj integracji z aplikacją ani kolejnego etapu bez kontroli Cerberusa.
