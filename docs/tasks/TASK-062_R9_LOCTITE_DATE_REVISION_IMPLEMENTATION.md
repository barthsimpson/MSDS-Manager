# TASK-062-R9 — LOCTITE: data aktualizacji i pełny identyfikator rewizji SDS

**Status:** READY / AUTHORIZED — decyzja Architekta z 2026-11-12  
**TASK MODE:** PATCH (ograniczona implementacja + regresja powiązanych formatów)  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repozytorium:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`; istniejący `main`, bez nowego brancha/worktree.  
**Punkt odniesienia:** R8 ACCEPTED (diagnostyka); ostatni potwierdzony przed R8 `main`: `802903af94f92b099a797fd7e21a2775d13c3565`. Przed pracą sprawdź aktualny HEAD, upstream i stan roboczy; **nie resetuj** nowszych zmian.

## 1. AUTHORITATIVE CONTEXT / decyzje

1. `docs/task_reports/TASK-062_R8_REPORT.md` — diagnostyka trzech LOCTITE, cytaty, SHA i kandydaci **R8-C01/R8-C02**.
2. `docs/task_reports/TASK-062_R7_REPORT.md` — poprzednio zaakceptowany odczyt dat/rewizji i regresja WEICON, OPEX, SYLGARD, 3M.
3. `config/sds_aliases.json` — 13 aliasów `ACTIVE` (A-001–A-013); `SDS-ALIAS-001` i `SDS-JSON-001` w zakresie pól, dowodów i statusów.
4. `AGENTS.md`, właściwe fragmenty GOV-001, GOV-002, TDR-012, BDR-005 v1.2-approved, CORE-001 v1.9-approved — tylko w zakresie istotnym dla tego PATCH.
5. **Decyzja Architekta (wiążąca):** zatwierdzono **R8-C01 oraz R8-C02**; wartość `document_metadata.revision` zachowuje **dokładnie cały token z `V` i zerami wiodącymi** (`V005.1`, `V014.0`, `V013.0`). Nie normalizuj go do liczby ani `5.1`/`14.0`/`13.0`.

## 2. GOAL

Rozszerzyć **istniejący ekstraktor Evidence JSON DRAFT**, aby bez domysłów rozpoznawał w trzech kartach LOCTITE bieżącą datę `Aktualizacja` w formacie `DD.MM.YYYY` oraz rewizję dokumentu w postaci `V...` z nagłówka właściwego logicznego SDS. Następnie ponownie przetworzyć 3 PDF, wykonać ukierunkowaną regresję i przygotować raport. Bez połączenia z importerem lub bazą danych.

## 3. KNOWN STARTING POINTS

- `app/infrastructure/filesystem/sds_alias_matcher.py` — obecny matcher i ekstrakcja wartości `issue_date`/`revision`.
- `app/infrastructure/filesystem/sds_evidence_pipeline.py` — segmentacja i wytwarzanie DRAFT, sprawdź tylko potrzebny fragment, **bez przebudowy**.
- `config/sds_aliases.json` — A-008 `Aktualizacja` (już ACTIVE), A-006 `Wersja`, A-012 `Numer wersji`; nie twórz nowego aliasu literalnego bez konieczności.
- `scripts/extract_sds_evidence.py` — istniejący CLI.
- `tests/unit/test_task062_r2_aliases.py`, `test_task062_r3_evidence.py`, `test_task062_r5_3m_aliases.py`, `test_task062_r7_weicon.py` — dotychczasowa regresja.
- Źródłowe PDF (nie modyfikuj):
  - `data/sds/Paczki/paczka 5 loctite/Loctite 242 31.05.2022.pdf` (R8-L01; 16 stron);
  - `data/sds/Paczki/paczka 5 loctite/Loctite 243  rew 014.0 (27.03.2024).pdf` (R8-L02; 24 strony);
  - `data/sds/Paczki/paczka 5 loctite/Loctite 638 24.10.2022.PDF` (R8-L03; 32 strony).

## 4. DO — zatwierdzone reguły

### R8-C01: bieżąca data, istniejący A-008

- Rozpoznaj **bieżącą** wartość po etykiecie `Aktualizacja` w nagłówku logicznego SDS, w formacie `DD.MM.YYYY` (również gdy etykieta współdzieli wiersz z innymi elementami). Wynik ISO `YYYY-MM-DD`, `FOUND`, z literalnym `source_text`, etykietą i stroną.
- Oczekiwane: R8-L01 `11.07.2022` → `2022-07-11`; R8-L02 `14.05.2024` → `2024-05-14`; R8-L03 `24.10.2022` → `2022-10-24`.
- **Nie wybieraj** `Data druku`, `Zastępuje wersje z`, dat w tekście, daty z nazwy PDF ani innej kolumny. Przykładowo L02 `Data druku: 14.05.2024` pokrywa się z bieżącą datą, ale dowodem nadal musi być **Aktualizacja**. Waliduj poprawność kalendarzową.
- Zachowaj wcześniejsze `YYYY/MM/DD` (SYLGARD/DOWSIL), WEICON (w tym zatwierdzony priorytet PL w niejednoznacznych zapisach) oraz nagłówki dat 3M i OPEX; nie wprowadzaj globalnego, ślepego parsera kropek.

### R8-C02: rewizja LOCTITE z tokenu `V...`

- Rozpoznawaj tokeny `V005.1`, `V014.0`, `V013.0` **wyłącznie jako oznaczenie rewizji karty w kontekście nagłówka LOCTITE**, we własnym logicznym SDS. To kontekstowy odczyt, **nie** odczyt kodu producenta ani identyfikatora dokumentu.
- Wartość kanonicznego pola `document_metadata.revision` ma być **tekstowo identyczna** ze źródłowym tokenem: zachowaj wielką literę `V`, zera wiodące i kropkę. Pole `FOUND` ma zawierać dosłowny dowód, stronę/nagłówek i niezmieniony `source_text`.
- Powtórzenia identycznego tokenu `V...` na stronach **tej samej** karty nie tworzą `AMBIGUOUS`; sprzeczne tokeny w rzeczywistym kontekście rewizji tego samego SDS → `AMBIGUOUS`, `value=null`, bez arbitralnego wyboru pierwszego lub ostatniego.
- **Wyklucz** `KC Numer` (np. `173036`, `316211`, `450822`) jako `revision` i `manufacturer_product_code`; numery stron (`1 z 16`, itd.), kody H, etykiety transportowe, tokeny spoza nagłówka oraz rewizje z innych logicznych dokumentów.
- Reguła musi być ograniczona semantyką i pozycją nagłówka, **nie** stałą nazwą produktu, nazwą pliku, numerem strony ani wartościami `V005.1`/`V014.0`/`V013.0` wpisanymi na sztywno. Nie wpływaj na konwencję rewizji `3.01`, `5.0`, `13.00`, `14.00` wcześniejszych SDS.

### Pozostałe pola

- `product_name`: L01 `LOCTITE 242`, L02 `LOCTITE 243`, L03 `Loctite 638` — nadal `FOUND` z §1.1.
- `manufacturer_product_code`: dla wszystkich trzech **`NOT_FOUND`, `null`**; numer `KC Numer` NIE jest kodem produktu.
- `parties[]`: `Henkel Polska Sp. z o.o.` pozostaje `SUPPLIER`, `FOUND`, a **nie** automatycznie `MANUFACTURER`.
- Wszystkie dokumenty pozostają `PENDING_REVIEW` / `REQUIRES_HUMAN_REVIEW`. `G1/G2/G3=PASS` nie stanowi decyzji o producencie i nie uruchamia importu.

## 5. EXPECTED CHANGE SURFACE / DO NOT TOUCH

**Oczekiwane zmiany:** minimalny fragment istniejącego `sds_alias_matcher.py` (w razie bezpośredniej konieczności pomocnicza logika pipeline), nowy `tests/unit/test_task062_r9_loctite.py` i `docs/task_reports/TASK-062_R9_REPORT.md`. Aktualizuj inne pliki tylko gdy jest to konieczne do funkcji i uzasadnij.

**Nie zmieniaj:** Core/BDR/TDR; modeli domenowych, ORM, migracji PostgreSQL, API, UI, importera, JSON schema i pola `manufacturer_product_code`; źródłowych PDF; zasad zatwierdzania przez człowieka. Nie dodawaj OCR/LLM, zależności, osobnego parsera LOCTITE, nowej gałęzi/worktree. `config/sds_aliases.json`: domyślnie **bez zmian**, nadal 13 ACTIVE — nowy odczyt `V...` może być regułą kontekstową, nie musi być nowym aliasem.

## 6. ACCEPTANCE CRITERIA

| ID | Wymóg i sposób sprawdzenia |
|---|---|
| **R9-1** | Preflight: aktualny `main` i upstream, 13 aliasów `ACTIVE`, zachowanie zastanych nieśledzonych plików i nienaruszenie źródeł PDF. |
| **R9-2** | LOCTITE L01/L02/L03: `issue_date` = `2022-07-11` / `2024-05-14` / `2022-10-24`, każda `FOUND` z bieżącej `Aktualizacja`, właściwej strony i cytatu. |
| **R9-3** | Testy negatywne dat: `Data druku`, `Zastępuje wersje z`, nazwa pliku, sąsiedni wiersz/kolumna i data niemożliwa nie zastępują bieżącej daty. SYLGARD/WEICON/3M/OPEX bez regresji. |
| **R9-4** | `revision` = **`V005.1` / `V014.0` / `V013.0`** dokładnie (włącznie z `V` i zerami); `FOUND` z dowodem z nagłówka własnego SDS. |
| **R9-5** | Powtórzony identyczny `V...` nie wywołuje `AMBIGUOUS`; sprzeczny token wywołuje `AMBIGUOUS`, bez wyboru wartości. `KC Numer`, numer strony, H-kod i inny SDS nie są rewizją/kodem produktu. |
| **R9-6** | Wszystkie trzy PDF: po jednym logicznym SDS (strony 1–16 / 1–24 / 1–32), bez mieszania danych; pozostałe pola jak w §4; 3 Evidence JSON DRAFT i 3 walidacje, `G1/G2/G3=PASS`, `PENDING_REVIEW`, bez DB. |
| **R9-7** | Focused tests R9 + proporcjonalna regresja dotkniętych R2/R3/R5/R7: PASS, w tym zachowanie dat i rewizji poprzednich układów. |
| **R9-8** | Raport: wyniki przed/po, testy i CLI, zmienione pliki, rozliczenie zakresu, odstępstwa; brak zmian Core/DB/UI/importera. Bez automatycznego rozpoczęcia następnej paczki. |

## 7. VALIDATION / REPORT / GIT / STOP

1. Uruchom testy R9 dla 3 realnych źródeł + niewielkie syntetyczne przypadki negatywne; następnie regresję testów R2/R3/R5/R7 (poprzednio 36 PASS według raportu R7). Nie wymagamy pełnego pytest repo, ponieważ to lokalny PATCH bez zmiany kontraktu.
2. Uruchom istniejący CLI ponownie na **wszystkich 3 PDF** LOCTITE; zapisz Evidence JSON DRAFT i `.validation.json` w ignorowanym `tmp/task062r9_loctite/`. Zweryfikuj **faktyczne zapisane pliki**: wartości, stany, `source_text`, strony, G1/G2/G3, status człowieka, bez cross-document leakage; wskaż ograniczenia, jeśli któryś plik źródłowy jest niedostępny.
3. Przy pozytywnych kontrolach wykonaj **kontrolowany commit i zwykły push** na istniejący `main`, wyłącznie plików R9 (kod, test, raport). Używaj jawnego `git add <konkretne pliki>` i kontroli `git diff --cached`; **nie** `git add .`, force push, reset, czyszczenie historii ani automatyczny rebase. Opublikowane wcześniej paczki PDF są zaakceptowaną bazą testową, ale R9 nie wymaga ponownego ich dodawania. Potwierdź `HEAD` / `origin/main` i SHA; jeśli publikacja nie nastąpiła, jawnie to wskaż.
4. Raport `docs/task_reports/TASK-062_R9_REPORT.md`: tabela R9-1...R9-8 ze źródłowymi wynikami, krótkie zestawienie 3 SDS *przed/po*, komenda/wynik testów, trzy wyjścia CLI, lista plików i odchyleń oraz informacja o commicie. Nie wpisuj zmyślonego SHA do raportu, jeżeli commit go dopiero obejmie; SHA można przekazać w osobnym komunikacie.
5. **STOP / BLOCKED** przy konieczności zmiany Core/schema/kontraktu JSON, sprzecznych dowodach znaczenia tokenu `V...`, nowej nieuzgodnionej semantyce, regresji, brakujących źródłach krytycznych lub konflikcie Git. Bez prac pobocznych. Po raporcie **STOP** — nie zaczynaj paczki 4 KCH ani integracji aplikacji.

**Zasada projektu:** Automatyzacja proponuje, człowiek zatwierdza, Core pozostaje chroniony.
