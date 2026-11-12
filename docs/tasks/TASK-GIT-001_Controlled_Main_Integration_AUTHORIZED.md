# TASK-GIT-001 — Kontrolowana integracja lokalnego i zdalnego main

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — decyzja Architekta z 2026-11-06  
**TASK MODE:** INTEGRATION (GOV-002, LEVEL 2)  
**Wykonawca:** Codex  
**Zasady:** GOV-001 v1.0-approved; GOV-002 v1.0-approved; Konstytucja projektu; aktualne `AGENTS.md` repozytorium, jeżeli istnieje.  
**Numeracja:** odrębna techniczna seria TASK-GIT; nie zajmuje numeru TASK-061 z planowanego BATCH-002.

## 1. Cel i stan wejściowy

Zintegrować na **oddzielnej gałęzi roboczej** dwa ciągi zmian w MSDS Manager bez utraty funkcji TASK-058–060, bez wymuszania Dockera na firmowej stacji Windows i bez naruszenia konfiguracji Docker developera. Wynikiem ma być **lokalna, przetestowana propozycja scalenia**, a nie aktualizacja `main` lub publikacja do GitHub.

Ustalenia diagnostyczne (zweryfikuj stan referencji przed działaniem):

- lokalny `main`: `018fc65` (`paczka 2_apka dziala`);
- `origin/main`: `ce7ca7b`;
- wspólny przodek: `3411f6d`;
- 1 commit wyłącznie lokalny i 6 wyłącznie zdalnych;
- 4 pliki zmienione w obu historiach: `app/application/dto/__init__.py`, `app/application/use_cases/__init__.py`, `app/presentation/streamlit/composition.py`, `app/presentation/streamlit/product_registry.py`;
- symulacja `git merge-tree` bez markerów konfliktów tekstowych, **nie** wyklucza konfliktów semantycznych;
- odnotowany brak `list_sds_history` w teście `test_task040_current_sds_download.py` i brak importu `SupervisoryReadError` w `composition.py`;
- dziewięć śledzonych PDF w `.pytest_tmp/` zgłoszonych jako usunięte, przy błędach uprawnień; nie wiadomo, czy fizycznie zniknęły;
- `origin/feature/docker-dev-and-tests` ma drzewo zgodne z `origin/main`; `origin/chore/dependency-lock` ma dodatkowe, niewłączone zmiany — **poza zakresem**.

## 2. Wiążące decyzje Architekta

1. Wspólna gałąź docelowa `main` z jednym kodem aplikacji; **dwa niezależne środowiska uruchomieniowe**: firmowy Windows + `.venv` + lokalny PostgreSQL oraz Docker/Compose po stronie developera.
2. Na Windows Docker **nie jest dostępny i nie wolno go wymagać** do uruchomienia ani podstawowych testów.
3. Zmiany developera w Docker/Compose/README mają zostać zachowane; zmiany funkcjonalne TASK-058–060 i Stage 1 również.
4. Integracja na osobnej gałęzi, zwykły merge zachowujący obie historie, bez rebase historii opublikowanej i bez force push.
5. **STOP przed jakąkolwiek zmianą `main` i przed `push`.** Przejście na `main` i publikacja wymagają nowej autoryzacji po raporcie.

## 3. Dozwolony zakres i kolejność

### A. Bezpieczny preflight

- Odczytaj `AGENTS.md` (jeśli istnieje), potwierdź `HEAD`, aktualność `origin/main`, `git status`, stan indeksu i uprawnienia dotyczące `.pytest_tmp/`.
- Nie zakładaj, że stan roboczy jest czysty tylko na podstawie pojedynczego wcześniejszego `git status`. **Nie stosuj** `reset --hard`, `git clean`, wymuszonego przywracania/checkoutu ani kasowania PDF. Zapisz w raporcie, czy pliki PDF są fizycznie dostępne i dlaczego Git zgłasza usunięcie; jeśli uprawnienia blokują rozpoznanie, oznacz `UNVERIFIED`.
- Jeśli zdalne referencje istotnie zmieniły się od podanych SHA, albo istnieje nierozpoznana lokalna praca mogąca zostać naruszona — **STOP i raport**, bez integracji. Rutynowo wolno odczytać lokalne referencje; nie wykonuj samodzielnego `pull`.
- Utwórz lokalny wskaźnik zabezpieczający `backup/main-before-git-integration-20261106`, jeśli nazwa wolna; jeśli już istnieje, zweryfikuj jego cel i nie przesuwaj go. Nie usuwaj istniejących referencji.

### B. Izolowana integracja

- Preferuj **oddzielny `git worktree` poza katalogiem roboczym** (lub równie bezpieczny wariant izolacji), startujący z lokalnego commita `018fc65`, oraz gałąź `integration/main-windows-docker-20261106` — tylko jeśli te nazwy nie są zajęte. Nie przemieszczaj ani nie nadpisuj istniejącej pracy w głównym katalogu.
- Scal `origin/main` do tej gałęzi z zachowaniem obydwu historii (merge commit). W przypadku konfliktu rozstrzygaj wyłącznie uzasadnione obszary, dokumentuj decyzję i rezultat; przy sprzeczności domenowej — STOP.
- Skontroluj semantykę czterech wspólnych plików: funkcje wycofania i historii SDS oraz wyeliminowanie legacy `location_code` muszą współistnieć.
- Dopuszczalne są **minimalne naprawy integracyjne**: aktualizacja testowego dubla w `test_task040_current_sds_download.py` o wymagany interfejs `list_sds_history` oraz brakujący import `SupervisoryReadError` w `composition.py`, jeśli potwierdzony. Inne poprawki tylko jeśli bezpośrednio niezbędne do scalenia i wskazane w raporcie; nie naprawiaj innych testów „przy okazji”.
- Zachowaj pliki Docker/Compose, konfigurację `.run/`, `.gitignore` i działającą natywną ścieżkę `.venv`; bez zmian wymuszających Docker w Windows. `README.md` może zawierać zastane nieaktualne odniesienie do CORE v1.3: **zgłoś do korekty dokumentacyjnej**, nie rozszerzaj zakresu bez potrzeby.
- Nie włączaj `origin/chore/dependency-lock` i nie aktualizuj zależności/lockfile.

### C. Walidacja proporcjonalna do ryzyka

- Sprawdź `git diff --check`, listę zmian względem obu rodziców oraz obecność historii obu stron (`merge-base`, `log`).
- Uruchom na natywnym Windows w `.venv` bez Dockera: focused tests TASK-058–060, testy stanowisk / `location_code`, test pobierania bieżącego i historycznego SDS, AppTest listy i karty produktu; w miarę dostępności izolowaną integrację DB. Nie zapisuj do rzeczywistej bazy operatora; testy DB wyłącznie na wyraźnie izolowanym środowisku.
- Jeśli możliwe bez ingerencji w dane/operatora, wykonaj kontrolę startu aplikacji Streamlit na Windows; gdy port 8501 jest zajęty, nie zatrzymuj istniejącej aplikacji bez potrzeby, użyj osobnego portu lub wyjaśnij ograniczenie.
- **Nie uruchamiaj Docker na Windows.** Testy Docker/Compose wykonywane przez developera na jego stanowisku traktuj jako osobną, otwartą kontrolę przed końcową decyzją o pełnej zgodności obu środowisk. Nie przedstawiaj ich jako PASS, jeśli nie były wykonane.
- Jeżeli testy ujawnią regresję wymagającą zmian poza dozwolonym zakresem, STOP z opisem problemu; nie rozszerzaj zadania samodzielnie.

## 4. Wyłączenia i granice bezpieczeństwa

**Zabronione w tym TASK:** `git pull` na `main`, zmiana lokalnego lub zdalnego `main`, `push`, `force push`, `rebase`, `reset --hard`, `git clean`, usunięcie lub nadpisanie PDF w `.pytest_tmp/` i innych katalogach, modyfikacja bazy operatora, migracje, zmiany CORE/BDR/TDR, przebudowa Stage 1/SDS/BHP, obowiązkowy Docker na Windows, scalanie `chore/dependency-lock`, refaktoryzacja niezwiązanych modułów.

**Uwaga o stanie `.pytest_tmp/`:** zdalny `main` usunął dziewięć śledzonych testowych PDF; sam merge może odzwierciedlić tę zmianę **w izolowanym worktree**, ale nie jest zgodą na kasowanie plików z oryginalnego katalogu Windows. Wszelkie niejasności dotyczące oryginalnych plików odnotuj i pozostaw bez zmian.

## 5. Kryteria akceptacji

| ID | Wymaganie | Dowód |
|---|---|---|
| G1 | Oryginalny lokalny `main` i dane robocze pozostały nietknięte; istnieje weryfikowalny wskaźnik backup | SHA przed/po, `git status`, referencja backup |
| G2 | Integracja znajduje się wyłącznie na odrębnej gałęzi / w odrębnym worktree; obie historie zachowane | `git log --graph`, `merge-base`, nazwa gałęzi i SHA |
| G3 | Funkcje TASK-058–060, Stage 1, historia/wycofanie SDS oraz zmiany stanowisk zachowane | przegląd czterech wspólnych plików, konkretne testy |
| G4 | Windows `.venv` + PostgreSQL pozostaje niezależne od Dockera; konfiguracja Docker developera zachowana | kontrola uruchomienia natywnego, przegląd plików konfiguracji; Docker test oznaczony zgodnie z faktycznym stanem |
| G5 | Dwa znane problemy zgodności zostały naprawione minimalnie albo mają uzasadniony status BLOCKED | diff + test `test_task040_current_sds_download.py` i import `SupervisoryReadError` |
| G6 | Uprawnienia i status 9 PDF `.pytest_tmp/` wyjaśnione albo jawnie oznaczone jako nierozstrzygnięte; bez destrukcyjnych działań | odczyt stanu i wyjaśnienie w raporcie |
| G7 | Zakres testów adekwatny, wyniki i ograniczenia jawne; bez regresji w wykonanych kontrolach | nazwy komend/testów, PASS/FAIL/SKIP, izolacja DB |
| G8 | Nie zmieniono `main`, nie wykonano `push`, nie zmieniono danych operatora | stan referencji przed/po; raport STOP |

## 6. Raport i STOP

Zapisz `docs/task_reports/TASK-GIT-001_REPORT.md` (jeśli w repozytorium obowiązuje inna istniejąca konwencja raportów, zastosuj ją). Raport powinien zawierać: HEAD/gałęzie/referencje przed i po, sposób izolacji i lokalizację gałęzi, listę zmienionych plików, rozstrzygnięcia czterech wspólnych plików, wyniki G1–G8, konkretne testy, status `.pytest_tmp/`, ograniczenie Docker, odstępstwa oraz rekomendację `READY FOR ARCHITECT REVIEW` albo `BLOCKED`.

**STOP po raporcie.** Nie przełączaj głównego checkoutu na gałąź integracyjną, nie aktualizuj `main`, nie wykonuj `push` i nie rozpoczynaj następnego zadania. Dalsza publikacja wymaga decyzji Architekta po ocenie Cerberusa.
