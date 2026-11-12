# TASK-062-R10 — paczka 4 KCH: diagnostyka ekstrakcji i kandydaci aliasów

**Status:** READY / AUTHORIZED — Architekt zatwierdził przejście do R10  
**TASK MODE:** DIAGNOSTIC / DISCOVERY — bez implementacji zmian  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repozytorium:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`; bez branchy i worktree.  
**Punkt odniesienia:** TASK-062-R9 CLOSED, potwierdzony `HEAD = origin/main` na commicie `3a6aad9` (`Implement TASK-062-R9 LOCTITE date and revision`). Przed pracą zweryfikuj aktualny stan; nie resetuj nowszych zmian i nie czyść zastanych nieśledzonych dokumentów.

## 1. Cel i oczekiwany wynik

Zdiagnozować działanie **istniejącego** ekstraktora PDF → Evidence JSON DRAFT na całej paczce `data/sds/Paczki/paczka 4 KCH/`, ocenić rzeczywiste logiczne SDS, kompletność i poprawność ekstrakcji tożsamości oraz przygotować **deduplikowaną macierz kandydatów R10-C01...** do decyzji Architekta. Na tym etapie **nie implementuj** nowych reguł ani nie aktywuj aliasów.

Inwentaryzacja R6 wykazała **7 PDF, 6 unikalnych bitowo** i pełną warstwę tekstową. Para `KCH EGR CLEANER...` ma wspólne SHA-256 `30187c7f8a32c58e9148c02e0b7892cb90d5dffb5919d3d34c08c939307e02de` (**D-02**). Potwierdź tę parę lokalnie; uruchom ekstrakcję **raz na unikalny PDF**, ale uwzględnij oba wystąpienia w raporcie i wyraźnie zapisz powiązanie duplikatu. Nie usuwaj plików.

## 2. Konkretne źródła — zakres zamknięty

Katalog `data/sds/Paczki/paczka 4 KCH/` według rejestru R6:

| ID | Ścieżka/nazwa PDF | Strony wg R6 | Uwagi |
|---|---|---:|---|
| KCH-01 | `KCH EGR CLEANER rew. 2.0 23.01.2023.pdf` | 8 | Para D-02, analiza raz |
| KCH-01-DUP | `KCH EGR CLEANER.pdf` | 8 | Ten sam SHA D-02; nie uruchamiaj drugi raz |
| KCH-02 | `KCH RC72-1 23.01.2023 rew. 02.pdf` | 11 | Unikalny |
| KCH-03 | `KCH Topnik RF 800 PL 25.01.2024 rew. 12.pdf` | 13 | Unikalny |
| KCH-04 | `KCH-Lakier-PVB-16-PL (1).pdf` | 13 | Unikalny |
| KCH-05 | `KCH-Lakier-PVB-60-PL 26.02.2024 rew. 12.pdf` | 14 | Unikalny |
| KCH-06 | `KCH2 Farba  KONTUR żółty 17.07.2025_rew.4.pdf` | 17 | Unikalny |

Powyższe nazwy i liczby stron są **danymi inwentaryzacji**, nie dowodami pól domenowych. Potwierdź faktyczne strony i odczyt. Nazwa pliku nigdy nie jest źródłem nazwy produktu, daty, rewizji, producenta ani kodu.

## 3. Kontekst autorytatywny — minimalny odczyt

- `docs/task_reports/TASK-062_R6_INVENTORY.md`, `TASK-062_R6_REPORT.md` — inwentaryzacja, D-02, status paczek; **nie** inwentaryzuj ponownie 134 PDF.
- `docs/task_reports/TASK-062_R9_REPORT.md` oraz w razie potrzeby R8/R7 — aktualna ekstrakcja LOCTITE, daty, rewizje i regresja (raport R9: 43 PASS). Stan w repo ma pierwszeństwo przed raportowanym historycznym wynikiem.
- `config/sds_aliases.json` — dotychczas 13 ACTIVE A-001–A-013; potwierdź bieżący stan, **nie edytuj**.
- `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py` — istniejąca implementacja i CLI.
- W zakresie niezbędnym: `AGENTS.md`, GOV-001, GOV-002, TDR-012, SDS-ALIAS-001, SDS-JSON-001, zatwierdzone BDR-005 v1.2 / CORE-001 v1.9. Nie rozszerzaj rutynowo eksploracji poza te źródła.

**Wiążące zasady:** `manufacturer_product_code` opcjonalny; `SUPPLIER`/dystrybutor/przedstawiciel UE nie jest automatycznie `MANUFACTURER`; operator zatwierdza tożsamość przed zapisem Core. Zachowuj dosłowny cytat i rolę źródłową. Operacyjnie z nazwy wolno usuwać tylko `®`/`™`. Dla niejednoznacznej daty liczbowej bez rozstrzygającego kontekstu stosuj zatwierdzony priorytet polskiego DD/MM/YYYY; jednoznaczny kontekst innego formatu pozostaje nadrzędny. Tokeny dokumentowe (`KC Numer`, UFI, numer SDS) nie są bez dowodu kodem produktu.

## 4. DO — diagnostyka sześciu unikalnych PDF

**A. Preflight i odczyt**

1. Potwierdź lokalny `main`, upstream, `git status`, stan 13 ACTIVE i brak nieautoryzowanych zmian. Nie czyść zastanych plików roboczych.
2. Zweryfikuj 7 ścieżek, ilość stron, dostępność warstwy tekstowej i dokładną parę SHA D-02; nie porównuj samych nazw ani przybliżonej treści jako dowodu bitowej identyczności. Przy niezgodności SHA analizuj oba pliki oddzielnie i wyjaśnij odstępstwo.
3. Rozróżnij rzeczywiste SDS od ewentualnych kart technicznych/pozostałych typów dokumentów. Nie zakładaj „1 PDF = 1 SDS”; wykryj liczbę i zakres stron logicznych SDS z treści, także przy nietypowych oznaczeniach §1.

**B. Przebieg istniejącego CLI**

4. Uruchom istniejące `python -B -m scripts.extract_sds_evidence <PDF> --output-dir tmp/task062r10_kch --source-id KCH-0N` dla każdej **unikalnej** karty z tabeli; przyjmij stabilne source-id KCH-01…KCH-06. Użyj `.venv` na Windows zgodnie z repo. Nie twórz nowego skryptu produkcyjnego ani specjalnego parsera KCH.
5. Zapisz i **odczytaj z dysku** `*.evidence.json` oraz `*.validation.json`. Przedstaw rzeczywistą liczbę logicznych SDS na źródło, ich strony, G1/G2/G3, `review_status`, `validation.status` i ostrzeżenia. Jeśli pipeline nie utworzył wyniku lub źródło nie jest SDS, wyjaśnij stan — nie generuj pozornych sukcesów.

**C. Audyt pól względem PDF**

6. Dla każdego logicznego SDS porównaj treść źródła i DRAFT dla: `product_name` (surowy/operacyjny), `manufacturer_product_code` (opcjonalny), `issue_date` (bieżąca, nie druk/poprz. wersja), `revision`, `parties[]` (dosłowna rola, pełna nazwa). Podaj `FOUND / NOT_FOUND / AMBIGUOUS / UNREADABLE` i krótkie cytaty z numerami strony, sekcji albo nagłówka dla sukcesów i luk, wraz z oczekiwaną wartością **tylko tam, gdzie jest bezpośredni dowód w PDF**.
7. Oddziel: brak danych w źródle, znaną etykietę lecz nierozpoznany układ, nową etykietę, błędny parser daty/rewizji, wieloznaczność rzeczywistą, ograniczenie tekstu, błąd segmentacji. Sprawdź role i zapobiegaj przeciekaniu dowodów między logicznymi SDS. Nie wnioskuj na podstawie tytułu PDF.
8. **G1/G2/G3 PASS oznacza poprawność strukturalną/źródłową DRAFT, nie kompletność pól.** Wymień wszelkie brakujące informacje istotne dla rejestracji pomimo PASS.

**D. Macierz kandydatów i priorytety**

9. Zbierz nieduplikowane kandydatury `R10-C01...` z kolumnami: źródło + logiczny SDS, etykieta/układ/rola, strona/sekcja + dosłowny cytat, pole docelowe, aktualny wynik, bezpieczny wynik oczekiwany, typ przyczyny (alias/kontekst/parser/segmentacja/odczyt/niejednoznaczność), wpływ na 13 ACTIVE i regresję R7/R9, negatywne przypadki oraz proponowany focused test i priorytet.
10. Nie mnoż kandydatów dla kilku PDF o tym samym układzie. Rozróżnij **nowy alias** od poprawki istniejącej reguły. `NOT_FOUND` przy braku kodu nie tworzy automatycznie kandydata. Wszystko pozostaje `CANDIDATE`; wyraźnie wskaż nierozstrzygnięte decyzje domenowe wymagające Architekta.

## 5. Kryteria akceptacji

| ID | Warunek i wymagany dowód |
|---|---|
| **R10-1** | Preflight: istniejący `main`, faktyczny HEAD/upstream, stan roboczy, 13 ACTIVE lub jawnie opisane odstępstwo; bez zmian historii i zastanych plików. |
| **R10-2** | Wszystkie 7 pozycji paczki rozliczone; potwierdzona D-02 przez SHA i 6 unikalnych przebiegów (lub odstępstwo przy SHA); strony, czytelność i typ dokumentu podane. |
| **R10-3** | Dla każdego unikalnego PDF określona liczba i zakres rzeczywistych logicznych SDS oraz punkty graniczne, bez założenia 1:1. |
| **R10-4** | Dla każdego logicznego SDS tabela pól i stanów, źródłowe cytaty/strony, G1/G2/G3, status review i rzetelny wykaz braków względem PDF. |
| **R10-5** | Macierz nieduplikowanych kandydatów R10-C01... z negatywami, testami i priorytetem albo wyraźny brak nowych; bez aktywacji i bez kodowych poprawek. |
| **R10-6** | Raport z komendami, kodami powrotu, liczbą wygenerowanych rzeczywistych JSON/validation, ograniczeniami i następną rekomendacją; zakres wyłącznie diagnostyczny, bez importu. |

## 6. Zakazy, raport, Git i STOP

**DO NOT TOUCH:** ekstraktor/matcher/CLI i testy, `config/sds_aliases.json`, Core/BDR/TDR, JSON schema, DB/ORM/migracje, importer, UI, oryginalne PDF, konfiguracja projektu. Nie uruchamiaj OCR/LLM, nie instaluj zależności, nie zaczynaj innej paczki. Nie dodawaj nowych branchy/worktree, nie używaj `git add .`, resetu ani force push. Autoryzowana obecność źródłowych PDF w Git **nie** oznacza autoryzacji dla roboczych JSON z `tmp/`.

**Zwróć** `docs/task_reports/TASK-062_R10_REPORT.md` z tabelą R10-1…R10-6, wykazem 7 pozycji/6 unikalnych źródeł, tabelami każdej logicznej SDS, kandydatami R10-C01..., komendami/wynikami, ograniczeniami i rekomendacją. Robocze JSON-y wyłącznie w `tmp/task062r10_kch/` (ignorowanym). Zadanie diagnostyczne **nie wymaga commita ani push**; raport pozostaw do kontroli Cerberusa przed decyzją Architekta.

**STOP** w dotkniętej części przy niezgodności źródeł, nierozstrzygniętej semantyce, niedostępnym PDF, niemożliwym do wiarygodnego określenia granic dokumentu lub konieczności zmiany kontraktu/Core. Opisz blokadę i kontynuuj pozostałe niezależne pliki. **STOP po raporcie R10.** Bez implementacji aliasów, kolejnej paczki ani integracji z aplikacją.

**Zasada nadrzędna:** Automatyzacja proponuje, człowiek zatwierdza, Core pozostaje chroniony.
