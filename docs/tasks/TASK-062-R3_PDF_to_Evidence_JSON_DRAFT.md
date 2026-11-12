# TASK-062-R3 — Wznowienie PDF → Evidence JSON DRAFT (OPEX + SYLGARD)

**Projekt:** MSDS-Manager  
**Status:** TASK-DRAFT / do weryfikacji preflight przed wykonaniem  
**Data:** 2026-11-10  
**Typ:** zamknięty etap implementacyjny, wyłącznie ekstrakcja i walidacja bez zapisu do Core  
**Poprzedni etap:** TASK-062-R2 — aktywacja dziewięciu aliasów, raport `TASK-062_R2_REPORT.md` (8 testów PASS według raportu)

## 1. Źródła i pierwszeństwo

Przed zmianami odczytaj **aktualne wersje z repozytorium**: `AGENTS.md`, `GOV-001`, `GOV-002`, obowiązujące ARCH/konstytucję, `TASK-062` (oryginalny zakres i kryteria), `TDR-012`, `SDS-JSON-001`, `SDS-SCHEMA-001`, `SDS-ALIAS-001`, `BDR-005 v1.1-approved_STAGE1`, aktualny zatwierdzony `CORE-001`, `TASK-061_REPORT.md`, `TASK-062_REPORT.md`, `TASK-062_R2_REPORT.md` oraz istniejący matcher i testy R2. Jeśli TASK-062 narzuca mniejszy zakres, nie rozszerzaj go tym plikiem. W razie sprzeczności wymagającej decyzji Architekta: STOP.

**Decyzja Architekta z 2026-11-10 (zatwierdzona w rozmowie):** rola `MANUFACTURER_EXPORTER` jest dowodem źródłowym, a nie automatyczną akceptacją producenta. Żadnego `PRODUCT` ani relacji `PRODUCT → MANUFACTURER` nie zapisuje się bez jawnego rozstrzygnięcia producenta przez użytkownika; źródłowy PDF i DRAFT pozostają dostępne. Nie jest to autoryzacja zmiany Core, DB ani planera importu.

## 2. Cel i rezultat

Usunąć blokadę TASK-062 wynikającą uprzednio z braku aliasów `ACTIVE` i uruchomić **odczyt oryginalnych PDF → zgodny z kontraktem `SDS-JSON-001` Evidence JSON DRAFT → raport walidacji i evidence** dla OPEX i czterech kart SYLGARD z TASK-061. Wszystkie `FOUND` muszą pochodzić z logicznego SDS i zawierać wskazanie źródła. Wynik ma być wyłącznie propozycją do dalszej weryfikacji operatora — **bez jakiegokolwiek commit do Core / PostgreSQL**.

## 3. Zakres dopuszczony

1. Preflight: sprawdź właściwy katalog/worktree, gałąź, HEAD, `git status`, zgodność oryginalnych PDF z checkpointem TASK-061 (SHA-256), wersję i statusy aliasów oraz decyzje o repo/commicie. **R2 wykonano w pierwotnym `main`, natomiast wcześniejszy TASK-062 był przygotowywany w worktree integracyjnym — nie zakładaj synchronizacji ani nie zmieniaj gałęzi w ciemno.** Jeśli brak ustalonej, aktualnej autoryzacji miejsca implementacji albo aliasów ACTIVE w tym worktree, STOP i raport rozbieżności.
2. Zaimplementuj tylko brakującą ścieżkę ekstrakcji i walidacji dla uzgodnionego zakresu TASK-062: wykrywanie logicznego SDS i jego sekcji/podsekcji, odczyt zaakceptowanych pól i ról przez aliasy `ACTIVE`, wytworzenie Evidence JSON DRAFT oraz trzy poziomy walidacji G1/G2/G3 **w semantyce rzeczywiście zapisanej w TDR-012 / SDS-JSON-001**. Nie wymyślaj definicji bramek.
3. Użyj 9 aliasów ACTIVE z R2. Dla OPEX oczekiwane rozróżnienie: `The Sherwin-Williams Company` = `MANUFACTURER_EXPORTER`, `Valspar B.V.` = `EU_REPRESENTATIVE`; nie zamieniaj tego w automatycznie zatwierdzonego producenta. Dla SYLGARD `DOW POLSKA SP.Z O.O.` występujące w bloku dostawcy = `SUPPLIER`, nie `MANUFACTURER`.
4. Dla nieodczytanych, niejednoznacznych lub nieczytelnych danych używaj wyłącznie stanów dopuszczonych w zatwierdzonych kontraktach (`NOT_FOUND`, `AMBIGUOUS`, `UNREADABLE`, jeśli zgodne); nie dopisuj wartości ze ścieżki/nazwy pliku, nazwy handlowej, UFI ani heurystyk spoza ACTIVE aliases.
5. Zachowaj dokładne wartości i identyfikatory źródła, w tym symbole `®` i `™`, stronę, sekcję i krótki cytat dla każdego `FOUND`. Zachowaj źródłowy PDF niezmieniony.
6. Zapisz DRAFT oraz raporty wyłącznie do bezpiecznej, testowej lokalizacji artefaktów zgodnie z zasadami repo. Bez importu produktu, producenta, SDS ani Safety.

## 4. Wyłączenia

- Brak zmian `CORE-001`, BDR, modelu DB, migracji Alembic, danych operatora, mechanizmu zapisu Stage 1, UI i procesu decyzji BHP.
- Brak automatycznego rozstrzygania `MANUFACTURER_EXPORTER → MANUFACTURER`, tworzenia `manufacturer_id`, `PRODUCT` lub `PRODUCT → MANUFACTURER`.
- Brak pełnego OCR/ML, nowej biblioteki aliasów lub automatycznej aktywacji aliasów. Wystąpienie nowej etykiety to materiał do osobnego R1/R2, nie obejście kontraktu.
- Brak rozszerzania zakresu na kompletne wydobycie wszystkich sekcji SDS 2/3/11, jeśli nie jest to wyraźnie wymagane przez pierwotny TASK-062; nie przypisuj niewykonanych pól statusu `FOUND`.
- Brak merge/force push i modyfikacji środowiska poza zatwierdzonym zakresem.

## 5. Kryteria akceptacji

| ID | Wymaganie | Weryfikacja |
|---|---|---|
| R3-1 | Preflight potwierdza właściwe worktree, gałąź, baseline, PDF, aliasy ACTIVE i upoważnienie do pracy | Raport z identyfikatorami i SHA-256 |
| R3-2 | Oryginalny OPEX i cztery SYLGARD tworzą odpowiednie logiczne SDS oraz DRAFT zgodne z `SDS-JSON-001` | Walidator schematu i przegląd pięciu wyników |
| R3-3 | `FOUND` posiada evidence z prawidłowym numerem strony, sekcją i cytatem; wartości pochodzą wyłącznie z treści karty | Testy źródłowe na oryginalnych PDF |
| R3-4 | OPEX zachowuje oddzielne role `MANUFACTURER_EXPORTER` i `EU_REPRESENTATIVE`; SYLGARD `SUPPLIER` nie staje się producentem | Testy regresji ról + oględziny DRAFT |
| R3-5 | `NOT_FOUND` / `AMBIGUOUS` / `UNREADABLE` zachowują semantykę kontraktu; błędna nazwa pliku, numer strony lub U+FFFD nie daje pozornego `FOUND` | Negatywne testy dopasowania |
| R3-6 | Wystawiany jest raport G1/G2/G3 wg kontraktu; nieudana bramka nie jest przedstawiana jako poprawny DRAFT | Walidacje pozytywne i negatywne |
| R3-7 | Nie występuje zapis do Core, DB ani UI; żaden PRODUCT ani MANUFACTURER nie jest tworzony automatycznie | Diff + kontrola wywołań persistence, testy izolacji |
| R3-8 | Po wdrożeniu działają testy R2 i nowe testy R3 bez regresji | Dokładne komendy, liczba testów i wynik |

## 6. Raport wykonania

Zapisz `docs/task_reports/TASK-062-R3_REPORT.md` (albo lokalizację wynikającą z bieżących zasad). W raporcie podaj: zakres i dowód źródłowy, zmienione pliki, macierz R3-1…R3-8 z konkretnymi dowodami, pięć wyników PDF, ścieżki DRAFT/raportów, wyniki G1/G2/G3, komendy i wyniki testów, pozostawione luki, `git status`, commit/push wyłącznie gdy autoryzowane. Odróżnij wynik testowy od sprawdzenia operatora. Nie deklaruj wykonania pełnego TASK-062, jeśli jego pierwotne wymagania pozostały niewykonane.

## 7. Warunek STOP

STOP przed implementacją lub przed zapisem, gdy: źródła są sprzeczne, alias ACTIVE nie istnieje w wybranym worktree, trzeba aktywować nowy alias, brak upoważnienia do użytej gałęzi, wymagane są zmiany Core/DB albo nie da się spełnić kontraktu bez nowej decyzji. Opisz blokadę z minimalną propozycją dla Architekta. Nie wykonuj napraw pobocznych ani nie rozpoczynaj następnego etapu.

**Koniec etapu:** przekaż raport Cerberusowi do kontroli. Nie uruchamiaj importu operatora.
