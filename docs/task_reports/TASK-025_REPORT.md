# TASK-025 — Sprint 4 End-to-End Acceptance

## 1. Status

`DONE`

Acceptance Sprintu 4 wykonany. Nie rozpoczęto kolejnego etapu Roadmapy.

## 2. Baseline

Przed acceptance:

- pytest: `137 passed`,
- brak `SAWarning`,
- Alembic: `e0dd7d6468bf (head)`,
- `alembic check`: brak nowych operacji,
- wcześniejsze zmiany TASK-015–024 pozostały nietknięte.

## 3. Zmienione pliki

TASK-025 nie zmienił production code, Domain, ORM ani schema. Dodano wyłącznie:

- `tests/integration/test_task025_sprint4_acceptance.py`,
- `docs/task_reports/TASK-025_REPORT.md`.

Test wykorzystuje istniejący UI TASK-024, `RegisterBhpDecision`, validator evidence, repozytorium i `TransactionExecutor`.

## 4. Setup PRODUCT/CURRENT SDS

Test tworzy kontrolowany fixture techniczny w PostgreSQL:

- MANUFACTURER,
- PRODUCT z `usage_status = PENDING_APPROVAL`,
- jeden SDS `CURRENT`,
- jeden SDS `ARCHIVED` do scenariusza błędu.

Po teście wszystkie rekordy są usuwane przez techniczny cleanup testu. Nie dodano publicznego use case delete.

## 5. Setup BHP_EVIDENCE_ROOT_PATH

Test tworzy tymczasowy katalog i pliki:

- `approved.pdf`,
- `correction.msg`,
- `rejected.jpg`.

Pliki zawierają wyłącznie techniczną treść fixture. Aplikacja sprawdza istnienie i rozszerzenie, ale nie analizuje zawartości. Po teście katalog tymczasowy jest usuwany przez pytest.

## 6. Scenariusz APPROVED

Prawdziwy `ShellComposition` i AppTest uruchamiają widok `Decyzja BHP`. Potwierdzono:

- produkt z `PENDING_APPROVAL` jest widoczny,
- CURRENT SDS jest powiązany z produktem,
- evidence `approved.pdf` jest dostępne,
- notes trafiają do `RegisterBhpDecisionInput`,
- zapis przechodzi przez Application i PostgreSQL,
- decyzja ma `APPROVED` i `CURRENT`,
- PRODUCT przechodzi na `ACTIVE`,
- evidence istnieje z właściwą ścieżką,
- ProductHistory zawiera snapshot `ACTIVE`,
- UI pokazuje sukces i bieżącą decyzję.

## 7. Scenariusz korekty REJECTED

W tym samym UI wybrano `correction.msg`, status `REJECTED` i nowe notes. PostgreSQL potwierdził:

- decyzja #1 pozostaje w bazie jako `SUPERSEDED`,
- decyzja #2 ma `REJECTED` i `CURRENT`,
- oba evidence pozostają,
- dokładnie jedna decyzja CURRENT istnieje dla SDS,
- PRODUCT przechodzi na `REJECTED`,
- ProductHistory zawiera kolejno `ACTIVE` i `REJECTED`.

## 8. Brak evidence

Dla drugiej kompozycji z pustym katalogiem evidence UI pokazuje kontrolowaną informację, nie ma wybranego dowodu i nie wykonuje skutecznego zapisu. Nie powstaje fałszywy komunikat sukcesu ani nowa decyzja.

## 9. ARCHIVED SDS

Próba rejestracji decyzji dla przygotowanego SDS `ARCHIVED` kończy się kontrolowanym błędem `SDS is not CURRENT`. Nie powstają evidence, decyzja, zmiana produktu ani historia.

## 10. Rollback korekty

Test wymusza błąd po utworzeniu evidence i po oznaczeniu poprzedniej decyzji jako `SUPERSEDED`. Rzeczywisty PostgreSQL rollback potwierdza, że:

- poprzednia decyzja nadal jest `CURRENT`,
- jej status pozostaje `REJECTED`,
- PRODUCT status pozostaje `REJECTED`,
- nie powstaje orphan evidence,
- nie powstaje dodatkowy ProductHistory.

## 11. Brak analizy evidence

E2E nie analizuje treści PDF/JPG/MSG, nie używa OCR/AI, nie odczytuje osoby ani daty decyzji i nie ustala statusu automatycznie. Status jest wybierany ręcznie w UI, a evidence jest wyłącznie referencją źródłową.

## 12. Cleanup

Po teście usuwane są metadata decyzji i evidence, ProductHistory, SDS, PRODUCT i MANUFACTURER. Pliki evidence są tymczasowe. Test nie usuwa żadnych danych produkcyjnych i chroni fixture własnymi identyfikatorami.

## 13. Walidacja końcowa

- acceptance E2E TASK-025: `1 passed`,
- pełny pytest: `138 passed`,
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS,
- brak `SAWarning`,
- `alembic current`: `e0dd7d6468bf (head)`,
- `alembic check`: `No new upgrade operations detected.`,
- schema bez zmian, 12 tabel biznesowych,
- brak nowych zależności,
- diagnostyka testu: brak błędów.

## 14. Architektura

```text
Streamlit
  -> ShellComposition
  -> RegisterBhpDecision
  -> BhpEvidenceValidator / repository
  -> TransactionExecutor
  -> PostgreSQL
```

Streamlit nie wykonuje SQL, nie importuje ORM, nie wykonuje commit/rollback i nie analizuje evidence. Backend pozostaje źródłem reguł statusów, relacji PRODUCT/SDS, CURRENT/SUPERSEDED, historii i atomowości.

## 15. Git / bezpieczeństwo

`.env` jest ignorowany. Nie dodano trwałych evidence, sekretów, dumpów ani backupów. Nie wykonano commit ani push. `git diff --check` i `git diff --cached --check` nie wykazały błędów whitespace.

## 16. DoD SPRINT-004

| Punkt | Status |
|---|---|
| PRODUCT z CURRENT SDS można wskazać | PASS |
| Evidence można wybrać z BHP_EVIDENCE_ROOT_PATH | PASS |
| Evidence jest wymagane | PASS |
| APPROVED można zapisać | PASS |
| APPROVED ustawia PRODUCT ACTIVE | PASS |
| REJECTED można zapisać | PASS |
| REJECTED ustawia PRODUCT REJECTED | PASS |
| Decyzja wskazuje product_id i sds_id | PASS |
| Jedna decyzja ma jeden evidence | PASS |
| Maksymalnie jedna CURRENT na SDS | PASS |
| Korekta tworzy nową decyzję | PASS |
| Poprzednia decyzja przechodzi na SUPERSEDED | PASS |
| Poprzedni evidence pozostaje | PASS |
| Notes działa | PASS |
| registered_at jest zapisane | PASS |
| Brak decided_by / decision_date | PASS |
| Operacja jest atomowa | PASS |
| Rollback działa | PASS |
| ProductHistory rejestruje zmiany | PASS |
| Evidence nie jest modyfikowane | PASS |
| Brak automatycznej decyzji BHP | PASS |
| E2E Sprintu 4 przechodzi | PASS |

## 17. Odstępstwa i ryzyka

Nie wykonano manualnego smoke poza automatycznym AppTest, ponieważ pełny test E2E używa prawdziwego Streamlit view, prawdziwego PostgreSQL i tymczasowego filesystemu. Nie wprowadzono korekt production code. Formalna decyzja o zamknięciu Sprintu pozostaje poza zakresem Codex.

Rekomendacja: `READY FOR SPRINT-004 CLOSURE`.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO ETAPU ROADMAPY.
