# TASK-DRAFT — TDR-014 Technical Precheck (READ-ONLY)

**Projekt:** MSDS Manager  
**Tryb:** ARCHITECTURE PRECHECK / READ-ONLY  
**GOV-002:** Context Locality / Minimal Exploration First; brak implementacji i testów mutujących dane  
**Status:** READY FOR HANDOFF — autoryzacja dotyczy wyłącznie prechecku  
**Numer wykonawczy:** do sprawdzenia w rejestrze repozytorium przed nadaniem; nie zakładać automatycznie TASK-060  
**Zleceniodawca:** Architekt Operacyjny poprzez Cerberusa  
**Obowiązujący Core:** CORE-001 v1.8-approved_BDR012 (zatwierdzony 2026-11-03)  
**TDR:** TDR-014 v0.1-draft — przed zatwierdzeniem, bez upoważnienia do implementacji

## 1. Cel i jedyny rezultat

Przeprowadź kontrolę wykonalności **TDR-014 v0.1-draft** względem faktycznego kodu i schematu MSDS Manager. Rezultatem ma być wyłącznie **`TDR-014_TECHNICAL_PRECHECK_REPORT.md`** z oceną zgodności i konkretnymi referencjami do istniejących elementów repozytorium. Nie implementuj funkcjonalności.

## 2. Authoritative context (w kolejności)

1. Obowiązujące `CORE-001_MSDS_Manager_v1.8-approved_BDR012.md` (nie używaj wersji Draft jako obowiązującej).
2. `BDR-012_Wycofanie_blednie_zarejestrowanego_SDS_v1.1-approved.md` — funkcjonalne wymagania i skutki biznesowe.
3. `TDR-014_Wycofanie_blednie_zarejestrowanego_SDS_v0.1-draft.md` — sprawdzany projekt techniczny, niezatwierdzony.
4. Istniejące `AGENTS.md`, `GOV-001`, `GOV-002` i lokalne konwencje repo.
5. Tylko w zakresie napotkanej zależności: BDR-003/004/007, TDR-003/004/006/007/013, UI-GUIDE-001.

Jeżeli w repozytorium brakuje wskazanych dokumentów, zgłoś brak; nie rekonstruuj ich z pamięci. Nie czytaj rutynowo całego repozytorium ani wszystkich dokumentów; rozpocznij od punktów startowych poniżej.

## 3. Minimalna ścieżka inspekcji

Najpierw sprawdź indeks/nazwy źródeł repo oraz aktualny stan gałęzi. Wyszukuj lokalnie symbole i pliki związane z: `Sds`, `document_status`, `AddSdsRevision`, `RegisterBhpDecision`, `CorrectBhpDecision`, `BHP_DECISION`, `record_status`, `registered_at`, `PRODUCT_HISTORY`, `usage_status`, `PENDING_APPROVAL`, `DECISION_EVIDENCE`, `SDS_ROOT_PATH`, Product Card / SDS history, migration `b7d4a1f03962`. Rozszerz przegląd tylko, gdy zależności tego wymagają. Zweryfikuj realną lokalizację kodu; wymienione symbole są wskazówkami wyszukiwania, nie stwierdzeniem ich istnienia.

**Bez poleceń wykonujących zapis do DB i bez uruchamiania testów korzystających z bazy operatorowej.** Dopuszczalne są bezpieczne, nieinwazyjne odczyty schematu/kodu i metadanych; gdy nie można zagwarantować odczytu, opisz niewykonaną kontrolę w raporcie.

## 4. Zamknięte kontrole

| ID | Obszar | Sprawdź i opisz |
|---|---|---|
| C1 | SDS schema/lifecycle | Faktyczne wartości statusów, constraints, indeksy i ochrona maksimum jednego CURRENT na PRODUCT; wykonalność rozszerzenia o INVALIDATED bez zmiany semantyki dotychczasowych statusów. |
| C2 | Audit/transaction | Wykonalność tabeli `sds_invalidation` i atomowej zmiany SDS, opcjonalnego restore, PRODUCT oraz PRODUCT_HISTORY; rzeczywiste granice transakcji i kolejność blokad. |
| C3 | PRODUCT history | Jak zapisywany jest `usage_status` i jego historia; czy przejście do PENDING_APPROVAL przy invalidation CURRENT może wykorzystać istniejące ścieżki. |
| C4 | BHP lifecycle (krytyczne) | Jak `RegisterBhpDecision` i ewentualna korekta/supersede obsługują historyczny CURRENT na tym samym `sds_id`; czy możliwa jest NOWA decyzja po restore bez silent overwrite i bez dwóch skutecznych decyzji. Rozdziel **fizyczny `record_status=CURRENT`** od **operacyjnej skuteczności decyzji**. |
| C5 | Temporal gate | Czy `registered_at` istnieje, jaka jest jego semantyka i źródło czasu; czy `registered_at > latest_restore_at` jest wystarczające przy równych timestampach, konkurencji i wielokrotnych przywróceniach. Nie projektuj samodzielnie nowego porządku zdarzeń; opisz konieczne rozstrzygnięcie, jeżeli istnieje luka. |
| C6 | Safety/Evidence/read model | Czy po invalidation CURRENT i ewentualnym restore nieaktywne BHP/Safety/Components przestają sterować aktualnym widokiem, a Stage 1 bez Safety nadal blokuje BHP. Wskaż wyłącznie konkretne punkty integracyjne. |
| C7 | UI contract | Rzeczywiste miejsce akcji na Product Card/historii SDS; możliwość prezentacji CURRENT/ARCHIVED/INVALIDATED, wyboru replacement bez domyślnego wyboru, reason, checkboxu, stale-state i historii; bez projektowania UI. |
| C8 | Alembic/downgrade | Rzeczywista migracja head i sposób status constraint; wykonalność bezpiecznego upgrade, kontrolowanego downgrade z blokadą przy danych INVALIDATED/eventach, bez modyfikacji istniejących danych. |
| C9 | Filesystem/data safety | Czy invalidation może być całkowicie bez zapisów do `SDS_ROOT_PATH` i bez zmian oryginalnego PDF/SDS relative_path oraz historiografii. |
| C10 | BDR/Core consistency | Wskaż dokładne punkty, w których TDR-014 odpowiada BDR-012 v1.1 i Core v1.8 lub wymaga doprecyzowania. Zwłaszcza nie zmieniaj polityki braku automatycznej reaktywacji BHP. |

## 5. Szczególna sytuacja do oceny — przywrócenie SDS

Rozważ istniejący SDS A (`ARCHIVED`) z historycznym rekordem `BHP_DECISION` o `record_status=CURRENT`; SDS B jest aktywny jako `CURRENT`. Operator unieważnia SDS B i świadomie przywraca SDS A, pozostawiając PRODUCT w `PENDING_APPROVAL`.

Wykaż na podstawie **aktualnej implementacji**, czy:

- wcześniejsza decyzja A pozostaje wyłącznie historyczna z perspektywy bieżącej skuteczności;
- nowa decyzja BHP dla SDS A może zostać poprawnie zarejestrowana przez istniejący workflow;
- żadna kontrola/indeks/constraint nie blokuje tego legalnego scenariusza;
- nie wystąpi automatyczne przejście PRODUCT z `PENDING_APPROVAL` na stan zatwierdzony przez użycie starej decyzji;
- jeżeli to niemożliwe, jaka dokładnie zależność powoduje STOP (bez wdrażania obejścia).

## 6. Kryteria akceptacji prechecku

1. Raport zawiera wiersz **PASS / GAP / BLOCKER / NOT_VERIFIED** dla każdej kontroli C1–C10 i podaje plik/funkcję/tabelę/constraint jako dowód; nie myl deklaracji z wynikiem testu.
2. C4 i C5 zawierają osobne, jednoznaczne wnioski oraz potencjalny wpływ na TDR-014.
3. Raport odróżnia: zgodność techniczną, propozycję techniczną i pytanie wymagające decyzji Architekta/Cerberusa.
4. Raport zawiera minimalną listę korekt TDR-014, jeśli potrzebne; nie zmienia zatwierdzonych CORE i BDR.
5. Na końcu jednoznaczne zalecenie: **TDR-014 READY FOR APPROVAL** albo **TDR-014 CORRECTION REQUIRED / BLOCKED** z uzasadnieniem.
6. Raport podaje przeglądnięte pliki/fragmenty, zastosowane odczytowe polecenia, kontrole niewykonane, ryzyka i potwierdzenie braku zmian poza plikiem raportu.
7. Żaden plik aplikacji, skrypt, test, migracja, dokument zatwierdzony ani dane operatora nie zostały zmodyfikowane.

## 7. Raport wykonawczy

Zapisz **jeden** plik `TDR-014_TECHNICAL_PRECHECK_REPORT.md` w istniejącej lokalnej konwencji raportów. Jeżeli repozytorium nie ma takiej konwencji, przyjmij `docs/task_reports/`. Raport musi zawierać:

- commit/branch albo inną jednoznaczną identyfikację sprawdzanego stanu kodu;
- status C1–C10 z lokalizacjami dowodów;
- opis scenariusza przywrócenia SDS i BHP;
- zgodności, luki, blokery, rozstrzygnięcia potrzebne przed TDR approval;
- brak wykonania implementacji i brak zmian w danych;
- listę niezweryfikowanych obszarów.

## 8. Granice i STOP

**DOZWOLONE:** odczyt dokumentów, kodu, definicji schematu i bezpieczny odczyt metadanych; zapis wyłącznie raportu.

**ZAKAZANE:** implementacja `InvalidateSds`, migracje/upgrade/downgrade, tworzenie tabeli, UPDATE/INSERT/DELETE DB, zmiana PDF, refaktoryzacja, edycja TDR/BDR/CORE, uruchamianie Paczki2, Stage 2, uruchamianie testów mutujących bazę, autoprzeskok do kolejnego zadania.

**STOP i raport** przy sprzeczności źródeł, braku autorytatywnego dokumentu, niemożności uzyskania bezpiecznego trybu odczytowego, niejasnej semantyce BHP lub konieczności zmiany zatwierdzonego Core/BDR.

Po zakończeniu **zatrzymaj się na raporcie**. Implementacja TDR-014 wymaga osobnego zatwierdzonego TDR, zamkniętego TASK i jawnej autoryzacji Architekta Operacyjnego.
