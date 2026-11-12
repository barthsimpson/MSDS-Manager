# TASK-062 — Minimalny pipeline PDF SDS → Evidence JSON DRAFT (TDR-012 PoC)

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — decyzja Architekta Operacyjnego, 2026-11-09  
**TASK MODE:** INTEGRATION / GOV-002 LEVEL 2  
**Wykonawca:** Codex  
**Warunek zakończenia:** raport i STOP; bez importu, merge ani push.

## 1. Cel i źródła wiążące

Wdrożyć minimalną **autonomiczną, lokalną, wykonawczą** ścieżkę TDR-012, której obecność została wykluczona w `TASK-061_REPORT.md`:

`PDF → odczyt → logiczne SDS → sekcje/podsekcje → ACTIVE aliases → pola z evidence i stanem → walidacja G1/G2/G3 → SDS-JSON-001 Evidence JSON DRAFT`.

**Źródła pierwszeństwa (odczytaj dokładne zatwierdzone wersje w repozytorium):**
- `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md`, zwłaszcza §§1–12;
- `SDS-SCHEMA-001`, `SDS-ALIAS-001`, `SDS-JSON-001` — zatwierdzone kontrakty, ich aktywne pola, aliasy i format wyniku;
- `TDR-003` — granice warstw, `GOV-001`, `GOV-002`, `AGENTS.md`;
- `TASK-061_REPORT.md` oraz rzeczywiste pliki w `docs/sds_bootstrap/BATCH-002_SYLGARD/`;
- aktualna implementacja: `app/infrastructure/filesystem/pdf_sds_extractor.py`, `PrepareSdsDraft`, `plan_evidence_json_import.py` — jako punkty startowe, bez automatycznego utożsamiania starego DTO z kontraktem TDR-012.

**NOWA, ZATWIERDZONA ZASADA ARCHITEKTA:** nazwa pliku PDF **nie jest źródłem wiążącym danych domenowych**. Wartości produktu, Part A/B, daty, rewizji, producenta i dostawcy pochodzą **wyłącznie z treści logicznego SDS**, wraz z dowodem źródłowym. Nazwa/ścieżka pliku służy tylko do identyfikacji technicznej źródła. Rozbieżność nazwa–treść nie jest sama w sobie błędem SDS i nie może nadpisywać zawartości dokumentu. Jeżeli sam dokument jest niejednoznaczny, użyj `AMBIGUOUS` / REVIEW; nie zgaduj.

## 2. Ścisły zakres pierwszego PoC

Implementacja obejmuje **zatwierdzony początkowy zakres §12 TDR-012**, nie pełną ekstrakcję sekcji 2, 3, 11:
1. Walidacja PDF, SHA-256, liczba stron i stan `READABLE / PARTIALLY_READABLE / UNREADABLE`; odczyt istniejącej warstwy tekstowej, bez OCR.
2. Segmentacja `1 PDF → 1..N logicznych SDS`, `document_key`, `page_range`, granice stron. Nie zakładaj `1 PDF = 1 SDS`.
3. Rozpoznanie struktury sekcji/podsekcji zgodnie z `SDS-SCHEMA-001`, z odniesieniem do stron.
4. Mapowanie **wyłącznie aliasów ACTIVE** z `SDS-ALIAS-001`, bez automatycznego dopisywania lub aktywowania aliasów. Nowe warianty mogą trafić tylko do osobnego rejestru obserwacji `CANDIDATE`.
5. Ekstrakcja identyfikacyjna: nazwa produktu, kod producenta **jeśli występuje** (opcjonalny, bez zgadywania), role podmiotów z sekcji 1.3, data wydania/aktualizacji SDS, rewizja/wersja; zgodnie z dokładnym zakresem i strukturą kontraktu. Nie utożsamiaj dostawcy SDS z producentem. Nie utożsamiaj daty dokumentu z datą wersji zastępowanej.
6. Każde pole: `value`, `state` (`FOUND / NOT_FOUND / AMBIGUOUS / UNREADABLE`) i `evidence[]` wg kontraktu. `FOUND` wymaga dowodu (strona, sekcja/podsekcja, źródłowy fragment) faktycznie potwierdzającego wartość. `NOT_FOUND` nie znaczy „nie występuje” ani „NO”. Nie wstawiaj wartości domyślnych bez dowodu.
7. Oddzielna walidacja strukturalna, źródłowa i semantyczna (G1/G2/G3) oraz **rzeczywiście wygenerowany** Evidence JSON DRAFT zgodny z `SDS-JSON-001` wraz z raportem walidacji. DRAFT nie jest zatwierdzeniem operatora.
8. Jeden jawny lokalny punkt uruchomienia (Application use case albo kontrolowane CLI) z minimalną obsługą błędów i wyjściem do katalogu roboczego; żadnego mikroserwisu ani zewnętrznej usługi.

**Nie implementować w TASK-062:** pełnego `SAFETY_PROFILE` z sekcji 2, składników CAS/stężeń z sekcji 3, toksykologii 11, klasyfikacji BHP/CLP, Stage 1 CREATE, porównania z DB operatora, uczenia ML, OCR, LLM, automatycznego REVIEW approval ani UI. Zaobserwowane w TASK-061 braki `H360F`, CAS i składników zachowaj jako **backlog**, nie ukrytą rozbudowę PoC.

## 3. Bezpieczeństwo Git i środowisk

Trwa uzgadnianie integracji `integration/main-windows-docker-20261106` (w raporcie TASK-GIT-001: `0611173`) z developerem. **Nie pracuj na starym rozbieżnym `main`.**

- Przed rozpoczęciem zweryfikuj lokalne referencje, istniejące worktree i status plików; upewnij się, że `0611173` pozostaje dostępne i jest wynikiem kontrolowanej integracji. Jeżeli wspólny `main` został już zatwierdzony i przesunięty, wskaż stan i wybierz aktualną zatwierdzoną bazę; przy niejasności STOP.
- Utwórz **nową, odrębną lokalną gałąź i worktree** (np. `feature/task-062-tdr012-poc`) od zweryfikowanego punktu integracji. Nie przełączaj i nie modyfikuj oryginalnego checkoutu `main` ani gałęzi integracyjnej.
- Nie modyfikuj plików Docker/Compose, `.env`, `.venv`, migracji ani schematu; uruchamiaj natywnie na Windows istniejącym interpreterem. Bez Dockera na stanowisku Architekta.
- Dozwolone są zapisy **wyłącznie w nowym worktree**, testach i katalogu artefaktów PoC. Nie zmieniaj bazy operatora ani żadnej istniejącej bazy aplikacyjnej. Testy bez DB; jeśli test technicznie wymaga DB — tylko izolowana baza testowa i jawne uzasadnienie.
- **Bez commit, push, merge, rebase i force push** w tym zadaniu. W raporcie pokaż gałąź bazową i diff.
- Nie usuwaj ani nie naprawiaj „przy okazji” niedostępnych `.pytest_tmp/` i historycznych PDF testowych.

## 4. Wykonanie i dane referencyjne

### A. Minimalne punkty startowe

Zidentyfikuj kontrakty, ich wersje i testy kontraktowe; wykorzystaj istniejący kod PDF i walidatory, jeśli faktycznie nadają się do użycia, bez podwójnej implementacji. Jeśli dokumentacja kontraktów nie istnieje, jest sprzeczna lub wymaga decyzji spoza §12 TDR-012 — zgłoś STOP zamiast wymyślać pola JSON.

### B. PoC na BATCH-002

Uruchom implementację na **wszystkich czterech** PDF w `data/sds/Paczki/paczka2 sylgard/`, z identyfikatorami roboczymi `B002-01..04`. Zachowaj oryginalne źródła i SHA. Udokumentuj zgodność wykrytych nazw/Part, dat i rewizji **z treścią** (a nie nazwami plików). Szczególnie:
- B002-01: SYLGARD 160 Part A; `2021/10/28`, `5.0` według TASK-061.
- B002-02: SYLGARD 160 Part B; `2022/11/01`, `5.0` według TASK-061; błędnie wyglądająca nazwa pliku nie ma pierwszeństwa.
- B002-03: SYLGARD 170 Part A; `2021/10/26`, `4.1` według TASK-061.
- B002-04: SYLGARD 170 Part B; `2022/11/07`, `7.0` według TASK-061; nazwa sugeruje inną datę, lecz nie jest źródłem danych.

Wartości z TASK-061 są **obserwacjami diagnostycznymi**, nie ręcznie zakodowanymi oczekiwaniami produkcyjnymi parsera. Potwierdź je na źródłowych PDF, w razie niejednoznaczności oznacz REVIEW.

### C. Regresja i wielokartowość

Uruchom co najmniej jeden **rzeczywiście dostępny** PDF wielokartowy z zaakceptowanego zestawu referencyjnego (w TDR-012: 3M DP-490), z oczekiwaną liczbą dokumentów i zakresem stron potwierdzonym na źródle. Jeżeli takiego źródła nie ma, nie symuluj pełnego PASS — test syntetyczny może badać algorytm, ale regresję rzeczywistego PDF oznacz `NOT VERIFIED`.

Dodaj skupione testy: 1-PDF/1-SDS; wielokartowość i granice stron; brak sekcji/pola; `FOUND` bez evidence → błąd; nazwa pliku sprzeczna z treścią → wartość z treści; producent vs dostawca; data zastępowanego SDS vs data bieżącego; nieaktywny/nieznany alias; częściowo nieczytelny PDF; struktura JSON / trzy walidacje. Testuj minimalnie obszar dotknięty zmianą, bez pełnej regresji projektu.

### D. Materiał do kolejnych iteracji

Obok **surowych wyników runtime** zapisz krótką macierz błędów: PDF + `document_key` + pole + rozpoznanie + stan + evidence + obserwacja + miejsce na późniejszą korektę operatora. Nie przedstawiaj korekt Codexa jako decyzji operatora i nie oznaczaj przykładów jako zatwierdzony Golden Set bez człowieka.

## 5. Kryteria odbioru

| ID | Wymaganie | Dowód |
|---|---|---|
| T62-1 | Izolowana gałąź/worktree od poprawnej bazy; `main`, gałąź integracyjna, konfiguracje i DB operatora nietknięte | `git branch`, `git status`, porównanie referencji, opis zakresu |
| T62-2 | PDF walidowany technicznie, jawny status czytelności, bez OCR i bez zgadywania | wynik uruchomienia / test wejść nieczytelnych |
| T62-3 | Segmentacja 1..N logicznych SDS z `document_key` i `page_range`, w tym test prawdziwego PDF wielokartowego albo jawne `NOT VERIFIED` | JSON + testy / dowód źródła |
| T62-4 | Sekcje/podsekcje i wyłącznie ACTIVE aliasy zgodne z zatwierdzonymi danymi; nowe jako CANDIDATE, bez aktywacji | testy, raport aliasów |
| T62-5 | Pola identyfikacyjne §12 poprawne lub jawnie niepewne; **treść SDS ma pierwszeństwo przed nazwą pliku**; rozdzielenie party roles | 4 wyniki SYLGARD z evidence, test sprzecznych dat |
| T62-6 | `FOUND` tylko z dowodem, nieobecne/niejednoznaczne/nieczytelne bez zgadywania | unit tests i próbki JSON |
| T62-7 | Wykonawczy Evidence JSON DRAFT w dokładnym kontrakcie `SDS-JSON-001` oraz niezależne G1/G2/G3 | pliki DRAFT, raport walidacji i testy kontraktu |
| T62-8 | Brak importu, zmian DB / CORE / BDR / TDR, OCR, ML, Docker, zmian git main/integration; brak nieautoryzowanej rozbudowy sekcji 2/3/11 | diff, lista plików, komendy |
| T62-9 | Krótki raport z realnymi PASS/PARTIAL/FAIL/BLOCKED, ograniczeniami i STOP | `TASK-062_REPORT.md` |

## 6. Raport i STOP

Zapisz `TASK-062_REPORT.md` w bieżącym izolowanym worktree / właściwym katalogu raportów wg projektu. Podaj: HEAD bazy i gałąź; zmienione pliki; komendę uruchomienia; listę JSON dla czterech PDF i ewentualnego pliku wielokartowego; kryteria T62-1..T62-9 z wynikami testów; raport trzech walidacji; odchylenia względem treści źródeł; przykłady błędów i kandydatów aliasów; brak zapisu DB; zakres niewykonany (w szczególności sekcje 2/3/11); ewentualną blokadę. **Nie oceniaj sukcesu wyłącznie przez generowanie pliku** — weryfikuj zgodność ze źródłem i kontraktem.

Jeśli potrzebna jest zmiana zatwierdzonego kontraktu, nowa reguła domenowa, zmiana w Core/DB, tworzenie lub aktywowanie aliasów, instalacja usług AI/OCR, niebezpieczna ingerencja w repozytorium albo nie można potwierdzić bazy Git: **STOP i raport blokady**.

**Po raporcie STOP — żadnego importu SDS do PostgreSQL, commita ani push bez odrębnej decyzji Architekta.**
