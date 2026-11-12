# TASK-061 — BATCH-002 SYLGARD: próbne przechwycenie, ekstrakcja i ocena jakości SDS

**Status:** AUTHORIZED — decyzja Architekta w rozmowie 2026-11-09  
**Tryb:** ograniczony eksperyment ekstrakcyjny / INTEGRATION, bez modyfikacji logiki aplikacji  
**Wykonawca:** Codex  
**Wynik:** 4 źródła PDF → wyniki odczytu / Evidence JSON DRAFT tam, gdzie wspiera to istniejący mechanizm → macierz jakości i obserwacji → raport, STOP.

## 1. Podstawa i granice

Źródła obowiązujące w zakresie zadania:
- `GOV-001_Zasady_wspolpracy_v1.0-approved.md`, `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`;
- `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md` (szczególnie rozdziały 2, 4–8, 11–16);
- aktualne zatwierdzone kontrakty `SDS-JSON-001`, `SDS-SCHEMA-001`, `SDS-ALIAS-001`, jeżeli są dostępne w repozytorium; nie zgaduj ich treści;
- `CHECKPOINT_TASK-060_BATCH-002_PREFLIGHT_REPORT.md` oraz aktualna zawartość repozytorium.

Nie zmieniaj CORE, BDR, TDR, schematu DB ani zatwierdzonych aliasów. Zakres niniejszego zadania to **ocena bieżącej zdolności do ekstrakcji**, a nie automatyczne trenowanie ML ani wdrażanie nowego parsera.

## 2. Kontekst

BATCH-002 zawiera cztery źródła w `data/sds/Paczki/paczka2 sylgard`:

| ID robocze | Plik źródłowy | Uwagi z preflight |
|---|---|---|
| B002-01 | `Sylgard 160 A rew. 5.0 (2021.10.28).pdf` | SHA-256 identyczny z zarejestrowanym `CURRENT` SDS Part A; **nie rejestrować drugi raz** |
| B002-02 | `Sylgard 160 part B rew. 5.0 (2022.22.01).pdf` | nazwa pliku zawiera niespójny zapis daty; sprawdzić datę z treści PDF |
| B002-03 | `sylgard-170-silicone-rew. 4.1_part-A_2021.10.26.pdf` | nowy materiał do oceny odczytu |
| B002-04 | `sylgard-170-silicone_rew 7_part-B_2021.10.26.pdf` | nowy materiał do oceny odczytu |

Identyfikatory `B002-*` są identyfikatorami roboczymi tej paczki, a nie istniejącymi identyfikatorami bazodanowymi. Zweryfikuj aktualną dostępność i integralność źródeł. Jeżeli nazwa/ścieżka nie zgadza się z preflightem, wyjaśnij odczytowo, nie modyfikuj źródeł.

Równolegle trwa przegląd gałęzi `integration/main-windows-docker-20261106` przez developera. **TASK-061 nie może zmieniać lokalnego `main`, gałęzi integracyjnej ani ich konfiguracji.** Dopuszczalne są wyłącznie artefakty robocze ekstrakcji i raport w odrębnym katalogu, bez commita/pusha/merge.

## 3. Cel i zakres wykonania

### A. Preflight wykonawczy
1. Potwierdź 4 pliki, rozmiary, SHA-256, możliwość odczytu tekstu i liczbę stron.
2. Sprawdź, jakie narzędzia/komendy istnieją już w repozytorium dla pipeline TDR-012. **Nie zakładaj, że zatwierdzony TDR oznacza gotową implementację.**
3. Potwierdź obowiązujący kontrakt wyników i zatwierdzony zakres pól. Nie używaj skryptu `task057_stage1_batch_import.py` do Paczki 2 — jest związany z BATCH-001_CX.

### B. Próbny odczyt, wyłącznie istniejącą ścieżką
1. Uruchom obecny mechanizm dla czterech źródeł, jeżeli jest dostępny i nie wymaga zmian kodu. Jeżeli nie ma wykonawczego ekstraktora zgodnego z TDR-012, **STOP dla automatycznej ekstrakcji**, a w raporcie wskaż precyzyjnie brakujący element i stan możliwych odczytów; nie zastępuj go improwizowanym parserem lub generowaniem danych przez Codexa.
2. Dla każdego PDF pokaż podział na logiczne SDS (nie zakładaj `1 PDF = 1 SDS`), rozpoznane sekcje i podsekcje, pola w zatwierdzonym zakresie, ich wartości/stany i wskazania źródła (strona, sekcja, cytowany fragment).
3. Gdy istniejący moduł potrafi wygenerować `Evidence JSON DRAFT`, zapisz DRAFT zgodnie z właściwym kontraktem, bez domyślania braków. `FOUND` wymaga evidence. Brak/niejednoznaczność/nieczytelność mają być oznaczone jawnie.
4. Zwróć szczególną uwagę na: identyfikację produktu i Part A/Part B; producenta kontra dostawca/representative; datę i rewizję SDS z **treści PDF**, a nie z nazwy; sekcje/pola występujące w różnych układach. W sekcjach wykraczających poza zatwierdzony zakres PoC wolno raportować obserwacje, lecz nie wolno potajemnie rozszerzać kontraktu ani parsera.

### C. Ocena jakości i materiał do przyszłego ML
1. Przygotuj jedną zwięzłą macierz dla każdego dokumentu/logicznego SDS: `source_pdf`, `sha256`, `document_key`, `page_range`, `section/field`, `extracted_value`, `state`, `evidence (page/section/source_text)`, `validation_result`, `operator_review_needed`, `observation`.
2. Oddziel **surowy wynik automatycznego odczytu** od ocen lub korekt wykonanych później przez człowieka. Nie oznaczaj żadnej wartości jako operator-approved bez rzeczywistej decyzji.
3. Wskaż typowe błędy i propozycje ich usunięcia; **nie zmieniaj reguł ani aliasów w tym zadaniu**. Nierozpoznane aliasy to wyłącznie `CANDIDATE`, nigdy automatycznie `ACTIVE`.
4. SYLGARD 160 Part A wykorzystaj jako referencję powtarzalności ekstrakcji (ten sam PDF); zgodność SHA-256 jest sygnałem o identyczności pliku, **nie jest automatyczną zgodą na rejestrację ani dowodem poprawności wszystkich pól**.
5. Nie ucz modelu ML. Zapisz tylko materiał, który pozwoli później utworzyć jakościowy Golden Set: dokument, rozpoznanie, dowód, stan, uwaga oraz miejsce na zatwierdzoną korektę.

### D. Podsumowanie decyzji, bez importu
Dla każdego źródła wskaż roboczą klasyfikację Stage 1 (`EXACT_EXISTING / CANDIDATE_NEW_SDS / REVIEW / OTHER`) z jej dowodem i wyraźnie oznacz `PROPOSAL`, nie decyzję zatwierdzoną. Jeśli obecne dane nie wystarczają do klasyfikacji, wpisz `REVIEW` z konkretną przyczyną. Bez wykonania Stage 1 CREATE, bez zmiany PRODUCT/SDS/BHP.

## 4. Dozwolone zapisy i wyłączenia

**Wolno:** przygotować osobny katalog wyników `docs/sds_bootstrap/BATCH-002_SYLGARD/` z manifestem roboczym, rzeczywiście wygenerowanymi DRAFT JSON, macierzą obserwacji i krótkim raportem; w razie ryzyka konfliktu w repozytorium użyj katalogu roboczego poza repozytorium i podaj lokalizację. Zachowaj oryginalne pliki PDF bez zmian.

**Nie wolno:** edytować kodu `app/`, `scripts/`, `tests/`, schematu PostgreSQL, migracji, plików konfiguracyjnych obu środowisk, kontraktów i słowników; wykonywać migracji, zapisu do bazy operatora, commita, push, merge/rebase, aktualizować CORE lub włączać zewnętrzne usługi AI do runtime. Nie twórz nowej implementacji extractora „przy okazji”.

## 5. Kryteria akceptacji

| ID | Wymóg | Dowód |
|---|---|---|
| T61-1 | Wykaz 4 wejść z integralnością, liczbą stron i czytelnością | manifest / preflight |
| T61-2 | Jawna informacja, czy aktualny extractor TDR-012 istnieje i został uruchomiony; brak symulowania wyników | wskazanie modułu/komendy i logu lub konkretnej blokady |
| T61-3 | Dla każdego przetworzonego logicznego SDS: zakres stron, sekcje, odczyty pól ze stanami i evidence | DRAFT JSON / macierz; `FOUND` tylko z dowodem |
| T61-4 | Rozdzielenie wyniku ekstrakcji od człowieczej oceny; lista błędów i kandydatów aliasów | macierz jakości / REVIEW |
| T61-5 | Rozstrzygnięte na poziomie obserwacji: dokładny PDF SYLGARD 160 A i data SYLGARD 160 B z treści dokumentu (lub jawne UNVERIFIED) | porównanie SHA; evidence z PDF |
| T61-6 | Propozycje klasyfikacji czterech źródeł bez wykonania importu | macierz decyzji ze statusem PROPOSAL |
| T61-7 | Brak zmian kodu, DB operatora, Git `main` i gałęzi integracyjnej | git status, wykaz nowych artefaktów, zakres operacji |
| T61-8 | Raport zakończony STOP i rekomendacją jednego następnego kroku | raport wykonania |

Jeśli T61-2 wykazuje brak mechanizmu ekstrakcji, T61-3–T61-6 oceniaj uczciwie jako częściowo niewykonane / BLOCKED; nie generuj fikcyjnego sukcesu.

## 6. Raport wykonania

Zapisz `TASK-061_REPORT.md`: źródła, komenda lub przyczyna niewykonania, mapowanie wejść→wyjścia, wynik T61-1…T61-8, przykłady udanego i błędnego odczytu z odniesieniem do PDF, ograniczenia i jeden rekomendowany następny krok. Przekaż ścieżki do rzeczywistych artefaktów. Zwięźle, zgodnie z GOV-002.

## 7. STOP

Zatrzymaj zadanie i zgłoś blokadę, jeżeli potrzebne są: nowe reguły bez decyzji, nowy extractor, zmiana kontraktu, OCR, zmiana CORE/DB, usługa AI w runtime, ingerencja w Git/integrację lub zapis PRODUCT/SDS. Wystaw raport częściowy zamiast rozszerzania zakresu.

**STOP po raporcie. Nie uruchamiaj importu Paczki 2.**
