# DYSP-063 — Przywrócenie publikacji main i odczytowy precheck aliasów

Status: AUTHORIZED — decyzja Architekta w rozmowie. Dwa krótkie etapy; STOP po raporcie.

## Punkt odniesienia
- Jedyny obowiązujący katalog: `C:\Users\bartosz.murawski\Projects\MSDS-Manager`.
- Lokalny `main` i HEAD: `018fc6535503f2e9b15c664a08cf7041cef9b2b0`.
- Aplikacja Streamlit uruchomiona natywnie na Windows, odczyt karty SDS potwierdzony przez operatora.
- Poprzedni zdalny `origin/main` wynosił `ce7ca7ba386ba3e56905eb427ed6d2b23786bffa`; należy sprawdzić aktualny stan, nie zakładać, że się nie zmienił.
- Historyczne gałęzie integracyjne i worktree pozostają nietknięte.

## A. Git — minimalna bezpieczna synchronizacja
1. W pierwotnym katalogu sprawdź `pwd`, `git status --porcelain=v1`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v`; nie ujawniaj sekretów.
2. Jeśli HEAD nie jest wskazanym `018fc65`, drzewo zawiera niezabezpieczone zmiany lub występuje nieoczekiwany stan plików testowych — STOP i raportuj; żadnego reset, checkout ani czyszczenia.
3. Ustal aktualny identyfikator zdalnego `main` (`git ls-remote --heads origin main`) oraz potwierdź, że nie trwa uzgodniony proces scalania z developerem. Jeżeli zdalny main zmienił się względem `ce7ca7b` albo istnieją nowe prace do rozstrzygnięcia — STOP przed zmianą main.
4. Utwórz i zweryfikuj **zdalną** gałąź zabezpieczającą wskazującą dokładnie aktualny zdalny `main`, np. `backup/main-before-restore-20261110`. Użyj niestandardowej nazwy, jeśli już istnieje; nigdy nie nadpisuj istniejącego backupu. Zweryfikuj przez `git ls-remote`.
5. Dopiero po dowodzie skutecznego backupu, zgodności oczekiwanych identyfikatorów i braku blokad wykonaj kontrolowane przywrócenie `main` przez `git push --force-with-lease=refs/heads/main:<zweryfikowany_pełny_SHA_zdalny> origin main:refs/heads/main`. Nie używaj `--force` ani ogólnego `--force-with-lease` bez wskazania SHA. Jeśli serwer odrzuci aktualizację lub gałąź jest chroniona — STOP; nie obchodź polityki.
6. Odczytowo potwierdź równość zdalnego main z `018fc65`, ustawienie tracking i `git status -sb`. Nie zmieniaj ustawień ochrony gałęzi, nie usuwaj worktree i nie ingeruj w bazę/operatora.
7. Przed zmianą historii zdalnego `main` przekaż informację, że inne klony developera będą wymagały świadomej synchronizacji; nie nakazuj mu `reset --hard`.

## B. Aliasy — tylko analiza, bez zmian domenowych
1. W tym samym pierwotnym katalogu sprawdź bieżące `SDS-ALIAS-001`, `TDR-012`, `TASK-062` i aktualne źródła/artefakty BATCH-002 dostępne w tym checkoutcie.
2. Wypisz wszystkie seedy `CANDIDATE`, źródła ich dowodów i minimalny zbiór wymagający decyzji operatora dla pól PoC: nazwa wyrobu, data aktualizacji, wersja, role podmiotów. Zasadą jest treść SDS, nigdy nazwa PDF.
3. Przedstaw małą tabelę `alias -> fragment SDS + strona + pole -> wynik weryfikacji -> proponowana decyzja ACTIVE/pozostaw CANDIDATE/REVIEW` z wyraźnym rozróżnieniem propozycji od zatwierdzenia.
4. Nie aktywuj aliasów automatycznie, nie pisz kodu TASK-062 i nie rejestruj SDS bez późniejszej decyzji Architekta. Nie traktuj odrębnych worktree jako bieżącego źródła kodu.

## Raport i STOP
Jedna krótka odpowiedź: identyfikatory lokalny/zdalny i backup, wynik Git (PASS/BLOCKED), potwierdzenie czy zwykły `git push` jest ponownie możliwy, tabela aliasów z dowodami i jedna rekomendacja najbliższego działania. Gdy część A zostanie zablokowana, wykonaj nadal niezależny odczytowy precheck B, jeśli bezpieczny. STOP. Bez nowych branchy/worktree, refaktoryzacji, migracji, importu lub kolejnego tasku.
