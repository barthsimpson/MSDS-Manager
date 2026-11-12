# TASK-062-R8 — LOCTITE (paczka 5): diagnostyka ekstrakcji i kandydaci aliasów

**Status:** READY / AUTHORIZED — decyzja Architekta: przechodzimy do paczki LOCTITE po zamknięciu R7  
**TASK MODE:** DIAGNOSTIC / DISCOVERY — bez zmian produkcyjnej logiki  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repo:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`, bez nowych branchy/worktree  
**Punkt odniesienia:** R7 CLOSED, commit implementacyjny `17abc9a`; dodatkowy commit `802903a` opublikował paczki źródłowych PDF za zgodą Architekta. Przed pracą sprawdź faktyczny `HEAD`, upstream i stan roboczy; nie resetuj ani nie czyść zastanych plików.

## 1. Cel i granice

W R6 zinwentaryzowano 134 PDF w 16 paczkach; R7 poprawił reguły WEICON i potwierdził regresję (raport: 36 PASS). **R8 obejmuje wyłącznie diagnostykę kolejnej paczki `data/sds/Paczki/paczka 5 loctite/` na aktualnym ekstraktorze i przygotowanie deduplikowanej macierzy kandydatów do decyzji Architekta.** Nie poprawiaj jeszcze matcherów ani nie aktywuj aliasów; nie przechodź automatycznie do następnej paczki.

Trzy rzeczywiste źródła według rejestru R6 (wszystkie miały pełną warstwę tekstową):

1. `data/sds/Paczki/paczka 5 loctite/Loctite 242 31.05.2022.pdf` — 16 stron;
2. `data/sds/Paczki/paczka 5 loctite/Loctite 243  rew 014.0 (27.03.2024).pdf` — 24 strony;
3. `data/sds/Paczki/paczka 5 loctite/Loctite 638 24.10.2022.PDF` — 32 strony.

**Nazwa pliku służy wyłącznie wskazaniu źródła**, nigdy do ustalania nazwy produktu, rewizji, daty ani producenta. Faktyczną liczbę logicznych SDS określ z treści każdego PDF; 1 PDF nie musi oznaczać 1 SDS.

## 2. Kontekst autorytatywny i znane punkty startowe

- `docs/task_reports/TASK-062_R6_REPORT.md` i `TASK-062_R6_INVENTORY.md` — zakres i status paczek; nie inwentaryzuj ponownie 134 dokumentów.
- `docs/task_reports/TASK-062_R7_REPORT.md` — zatwierdzona logika dat, dostawców, rewizji i wynik regresji; R7 był już zamknięty przez Cerberusa.
- `config/sds_aliases.json` — 13 aliasów ACTIVE A-001–A-013; bez modyfikacji w R8.
- `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py` — jedyny istniejący ekstraktor/CLI.
- `AGENTS.md`, GOV-001 v1.0-approved, GOV-002 v1.0-approved, TDR-012, SDS-ALIAS-001, SDS-JSON-001, BDR-005 v1.2-approved i CORE-001 v1.9-approved — wyłącznie fragmenty potrzebne do granic R8.
- Zatwierdzone zasady: kod producenta opcjonalny; `SUPPLIER` nie jest automatycznie `MANUFACTURER`; operator rozstrzyga tożsamość przed zapisem do Core; tylko znaki `®`/`™` usuwać z operacyjnej nazwy; cytaty źródłowe zachować. Przy dwuznacznej dacie liczbowej bez jednoznacznego źródłowego kontekstu stosuj polski priorytet DD/MM/YYYY (np. `02/03/2022` = `2022-03-02`), ale nie wypieraj jawnie udokumentowanego odmiennego formatu.
- GOV-002: minimalna eksploracja, brak niepotrzebnych testów pełnego repo, bez prac przy okazji.

## 3. Wykonanie — tylko paczka 5

### A. Odczyt i segmentacja

1. Potwierdź obecność trzech PDF, liczbę stron, faktyczną czytelność warstwy tekstowej i niezmienność źródeł; sprawdź SHA tylko jeśli potrzebne do wykazania duplikatu lub ochrony źródła.
2. Uruchom istniejące CLI na każdym PDF, zapisując osobne `*.evidence.json` i `*.validation.json` w ignorowanym `tmp/task062r8_loctite/`, np. `python -B -m scripts.extract_sds_evidence <PDF> --output-dir tmp/task062r8_loctite --source-id R8-L01` (odpowiednio L02/L03).
3. Dla każdego PDF podaj liczbę logicznych SDS, zakresy stron i źródłowe punkty graniczne. Jeśli automatyczna segmentacja zawodzi, wskaż faktyczne sekcje i przyczynę; nie koryguj produkcyjnego parsera w R8.

### B. Diagnoza pól i Evidence

Dla **każdego logicznego SDS** przedstaw: `product_name` (źródłowa i operacyjna, jeśli różne), opcjonalny `manufacturer_product_code`, bieżący `issue_date`, `revision`, `parties[]` z literalną rolą, a także stany `FOUND / NOT_FOUND / AMBIGUOUS / UNREADABLE`, numer strony/sekcję i krótki cytat dla kluczowych dopasowań i luk. Przedstaw G1/G2/G3 oraz `review_status`; PASS bramek **nie** jest dowodem kompletności wartości.

Sprawdź odrębnie, czy występują układy wieloskładnikowe, wiele kodów, kilka podmiotów w §1.3, różne języki, daty bieżące i zastępowane, powtórzenia stopki albo różne układy etykiet. Nie zakładaj żadnej z tych cech bez dowodu PDF. Nie wyciągaj danych z innych logicznych SDS ani z nazwy PDF.

### C. Kandydaci do decyzji Architekta

Przygotuj **jedną deduplikowaną macierz** nowych przypadków. Kolumny: `CANDIDATE ID` (`R8-C01...`), źródło i logiczny SDS, rzeczywista etykieta / układ / rola, strona i sekcja + literalny cytat, pole docelowe, obecne zachowanie, oczekiwane zachowanie, rodzaj przyczyny (alias / kontekst / parser / segmentacja / tekst / rzeczywista niejednoznaczność), przypadki negatywne, wpływ na 13 ACTIVE i R7, proponowany test oraz priorytet.

- Nie mnoż aliasów na różnice kosmetyczne; wskaż użycie istniejącego aliasu z regułą kontekstową, jeśli wystarczy.
- Nie proponuj kodu produktu, jeżeli SDS go nie podaje; `NOT_FOUND` może być prawidłowe.
- Nie utożsamiaj nazwy dostawcy, dystrybutora, przedstawiciela UE ani właściciela praw autorskich z producentem bez źródłowego uzasadnienia. Propozycje producenta są tylko do późniejszego zatwierdzenia.
- Każdy kandydat ma status **CANDIDATE**, bez zmian w katalogu. Jeśli nie ma nowych przypadków, napisz wprost „brak nowych kandydatów”.

## 4. Kryteria akceptacji

| ID | Wymagany wynik / dowód |
|---|---|
| R8-1 | Preflight: aktualny `main` i HEAD, 13 aliasów ACTIVE, brak ingerencji w zastane pliki, PDF i historię Git. |
| R8-2 | Wszystkie 3 konkretne PDF LOCTITE zbadane; dostępność i czytelność potwierdzona, bez OCR. |
| R8-3 | Liczba i granice **rzeczywistych logicznych SDS** osobno dla każdego PDF; opis niepewności, jeśli wystąpi. |
| R8-4 | Dla każdego logicznego SDS czytelna tabela pól, stanów, dowodów, G1/G2/G3, review status; brak mieszania dowodów i zgadywania. |
| R8-5 | Macierz nieduplikowanych kandydatów z konkretnymi cytatami, negatywami i proponowanymi testami albo jawny brak kandydatów; 0 zmian ACTIVE. |
| R8-6 | Raport z komendami i wynikami 3 przebiegów CLI, odchyleniami i zalecaną decyzją; brak zmian Core, DB, UI, importera, aliasów, matcherów i źródłowych PDF. |

## 5. Zakazy, STOP i raport

**Nie zmieniaj:** kodu ekstraktora, CLI, testów produkcyjnych, `config/sds_aliases.json`, CORE/BDR/TDR, schematów JSON, ORM/migracji, PostgreSQL, UI, importera, danych Core ani źródłowych PDF. Nie uruchamiaj OCR/LLM, nie twórz drugiego parsera, brancha/worktree, nie wykonuj `git add .`, nie sprzątaj zastanych nieśledzonych pozycji. Opublikowane źródłowe PDF są **autoryzowaną bazą testową**; nie oznacza to zgody na publikowanie plików tymczasowych lub danych wrażliwych.

Przy sprzeczności z wymaganiami, konieczności rozszerzenia kontraktu/Core, istotnie błędnej segmentacji uniemożliwiającej wiarygodną diagnozę albo nowej nierozstrzygniętej decyzji domenowej: **STOP w dotkniętym zakresie**; opisz blokadę i dokończ pozostałą niezależną diagnostykę. Nie naprawiaj przy okazji.

**Dostarcz** `docs/task_reports/TASK-062_R8_REPORT.md`: tabela R8-1…R8-6 (dowód/wynik), tabela dla wszystkich źródeł i logicznych SDS, macierz kandydatów, komendy/wyjścia i jawne ograniczenia. Wszystkie robocze Evidence JSON i validation JSON pozostają w `tmp/`. Raport może pozostać lokalny do przeglądu Cerberusa; **nie wykonuj automatycznie commita/push** w zadaniu wyłącznie diagnostycznym. **STOP po R8; bez implementacji kandydatów i bez następnej paczki.**
