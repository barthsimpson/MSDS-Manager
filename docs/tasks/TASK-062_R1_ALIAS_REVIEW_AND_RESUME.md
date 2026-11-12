# TASK-062-R1 — Odblokowanie aliasów i warunkowe wznowienie PoC ekstraktora

**Status:** AUTHORIZED — przegląd i przygotowanie dowodów; aktywacja aliasów wymaga jawnej decyzji Architekta.
**Projekt:** MSDS Manager | **Data:** 2026-11-10
**Charakter:** korekta blokady istniejącego TASK-062, bez nowego numeru TASK.

## 1. Obowiązujące środowisko

- Jedyny katalog roboczy: `C:\Users\bartosz.murawski\Projects\MSDS-Manager`.
- Gałąź: lokalny `main`; punkt odniesienia po DYSP-063-R2: `f97c1e28996ace2087f774aeabec4ca7a9bc91cd`.
- Praca bez Dockera i bez nowych branchy/worktree. Istniejące nieśledzone artefakty zachować.
- Przed zmianami sprawdzić odczytowo `git status`, HEAD i obecność źródeł. Nie resetować ani nie usuwać żadnych plików.

## 2. Podstawa i problem

Źródła: TDR-012 v1.0-approved; `docs/tasks/SDS-ALIAS-001_Biblioteka_aliasow_i_reguly_rozszerzania_v1.0-approved.md`; obowiązujący TASK-062; TASK-061_REPORT; TASK-062_REPORT; macierz BATCH-002; kontrakty SDS-SCHEMA-001 i SDS-JSON-001 dostępne lokalnie. W razie rozbieżności z tym opisem obowiązują zatwierdzone źródła repozytorium i decyzja Architekta.

TASK-062 jest BLOCKED: sześć seedów A-001..A-006 ma status CANDIDATE, nie ma ACTIVE. TDR-012 wymaga: obserwacja -> ocena człowieka -> APPROVED -> regresja -> ACTIVE. Runtime nie może sam awansować kandydatów ani używać ich jak ACTIVE.

## 3. Etap pierwszy — odblokowanie decyzyjne (WYKONAJ TERAZ)

1. Odczytaj lokalny TASK-062, SDS-ALIAS-001, SDS-SCHEMA-001, SDS-JSON-001 oraz TDR-012. Porównaj zakres istniejących pól i definicję przejścia CANDIDATE -> ACTIVE; nie dopisuj własnych wyjątków.
2. Na rzeczywistych PDF zweryfikuj osobno A-001..A-006 (OPEX) oraz etykiety `Nazwa wyrobu`, `Aktualizacja`, `Wersja` i podmiot sekcji 1.3 (SYLGARD 160/170 A/B). Dla każdego przypadku zapisz: literalną etykietę, literalną wartość, pole docelowe, rolę podmiotu, stronę, sekcję/podsekcję, krótki cytat źródłowy, ryzyko błędnego przypisania, oczekiwany wynik. Oddziel widoczność etykiety od pewności powiązania wartości.
3. Uwzględnij sytuacje krytyczne: producent != dostawca != przedstawiciel UE; data aktualnego SDS != data zastępowanej wersji; `Wersja` może występować w różnym układzie; nazwa pliku nie jest dowodem wartości domenowej; nierozpoznana wartość = jawny brak/AMBIGUOUS/UNREADABLE, nie zgadywanie.
4. Przygotuj minimalną macierz propozycji: `APPROVE PROPOSED` / `REVIEW` / `REJECT PROPOSED`, z argumentem i testem regresyjnym dla każdego aliasu. Jeśli brak reguły wiązania etykiety z wartością, zaproponuj ją do decyzji, nie ukrywaj jako implementacji.
5. Wskaż najmniejszy sensowny zestaw aliasów pozwalający ruszyć z PoC, bez pozornej obietnicy kompletnego ekstraktora. Przygotuj testy/fixture lub plan testów na rzeczywistych źródłach, jeżeli nie wymaga to aktywacji aliasów.
6. Zakończ raportem decyzyjnym dla Architekta. **STOP przed zmianą statusu któregokolwiek aliasu na ACTIVE.** Nie rozpoczynaj jeszcze implementacji ekstraktora na aliasach CANDIDATE.

## 4. Etap drugi — po zatwierdzeniu przez Architekta (NIE TERAZ)

Po odrębnej jawnej decyzji, wskazującej dokładnie zatwierdzone aliasy/reguły: wprowadzić zatwierdzone zmiany do biblioteki, uruchomić regresję, dopiero po pozytywnej regresji oznaczyć odpowiednie aliasy ACTIVE i kontynuować istniejący TASK-062 według jego oryginalnych kryteriów. Przestrzegać TDR-012: PDF -> segmentacja logiczna -> sekcje/podsekcje -> ACTIVE aliasy -> evidence -> G1/G2/G3 -> SDS-JSON-001 Evidence JSON DRAFT. Testować 4 SYLGARD, OPEX i wielokartowy 3M DP-490; nie zakładać 1 PDF = 1 SDS.

## 5. Granice bez zmian

Bez zapisów do operator PostgreSQL, bez migracji/zmian Core, bez zmiany lifecycle SDS/BHP, bez OCR, AI/LLM, Dockera i nowych zależności bez autoryzacji; bez modyfikacji UI; bez nowych gałęzi/worktree. Nie edytować ani nie usuwać źródłowych PDF. Nie dodawać danych roboczych do commita. Bez automatycznego awansowania aliasów.

## 6. Kryteria akceptacji pierwszego etapu

| ID | Kryterium | Dowód |
|---|---|---|
| R1-1 | Praca w poprawnym katalogu i `main` bez zmian środowiska | HEAD, status, lista operacji |
| R1-2 | Każdy istniejący A-001..A-006 ma ocenę ze wskazaniem źródła | Macierz + strona/sekcja/cytat |
| R1-3 | Warianty SYLGARD są ocenione bez wnioskowania z nazwy pliku | Macierz czterech PDF |
| R1-4 | Role podmiotów i daty są rozróżnione; niejednoznaczności jawne | Przypadki negatywne |
| R1-5 | Jest konkretny pakiet do decyzji Architekta i plan regresji | Propozycje zatwierdzenia/odrzucenia |
| R1-6 | Nie aktywowano aliasów ani nie zmieniono Core/DB/UI | Diff / deklaracja i kontrola |

Raport: krótki opis, macierz, źródła, ewentualne zmienione pliki, wyniki i ograniczenia, jednoznaczne decyzje oczekiwane od Architekta. **STOP**.

## 7. Warunki przerwania

Brak autentycznego PDF, niezgodność zatwierdzonych źródeł, konieczność zmiany modelu/kontraktu lub nieusuwalna niejednoznaczność oznaczają REVIEW/STOP danej części; nie wolno zastąpić ich zgadywaniem. Pozostałą pracę odczytową można zakończyć i przedstawić częściowy raport.
