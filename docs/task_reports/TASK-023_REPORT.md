# TASK-023 — BHP Decision Persistence & Transaction

## 1. Status

`DONE`

Zaimplementowano persystencję decyzji BHP i dowodów w istniejącym ORM/schema. Nie rozpoczęto TASK-024.

## 2. Zmienione pliki

- `app/infrastructure/filesystem/bhp_evidence_validator.py`
- `app/infrastructure/db/repositories/bhp_decision.py`
- `app/infrastructure/db/repositories/__init__.py`
- `app/application/exceptions.py`
- `tests/unit/test_bhp_evidence_validator.py`
- `tests/integration/test_task023_bhp_decision.py`
- `docs/task_reports/TASK-023_REPORT.md`

## 3. Evidence validator

`BhpEvidenceValidator` implementuje `BhpEvidenceValidatorPort` i waliduje:

- ścieżkę względną,
- pozostawanie pod `BHP_EVIDENCE_ROOT_PATH`,
- istnienie pliku,
- rozszerzenie `.msg`, `.pdf`, `.jpg`, `.jpeg` lub `.png`.

Zwracana jest znormalizowana ścieżka względna. Adapter nie analizuje, kopiuje, przenosi, usuwa ani nie zmienia nazwy pliku.

## 4. Walidacja PRODUCT/SDS

`SqlAlchemyBhpDecisionRepository` przed zmianami potwierdza:

- istnienie PRODUCT,
- istnienie SDS,
- zgodność `SDS.product_id == product_id`,
- `SDS.document_status == CURRENT`.

Nie można zarejestrować decyzji dla SDS archiwalnego, nieistniejącego ani należącego do innego produktu.

## 5. DECISION_EVIDENCE i BHP_DECISION

Każda decyzja tworzy jeden `DecisionEvidenceModel` oraz jeden `BhpDecisionModel`. Format i typ evidence wynikają wyłącznie z rozszerzenia i istniejących enumów. Decyzja ma `record_status = CURRENT`, wskazuje produkt, SDS i evidence oraz zachowuje opcjonalne notes.

Poprzednia decyzja CURRENT dla tego samego SDS jest ustawiana na `SUPERSEDED`; jej rekord i evidence pozostają w bazie. Istniejący częściowo unikalny indeks `uq_bhp_decisions_one_current_per_sds` zabezpiecza maksymalnie jedną decyzję CURRENT.

## 6. Product status i ProductHistory

Po decyzji:

- `APPROVED` ustawia PRODUCT na `ACTIVE`,
- `REJECTED` ustawia PRODUCT na `REJECTED`.

Dla każdej zmiany tworzony jest snapshot `ProductHistory` z aktualnym usage status, opisem użycia, ograniczeniem, waste fields i timestampem. Nie ustawiano `PENDING_APPROVAL` ani `INACTIVE` jako wyniku decyzji.

## 7. Transaction boundary

Repozytorium nie wykonuje commit. Cały przebieg działa w sesji przekazanej przez istniejący `TransactionExecutor`, który wykonuje jeden commit po sukcesie i rollback dla wyjątku.

Kolejność obejmuje walidację relacji, supersedowanie poprzedniej decyzji, evidence, nową decyzję, zmianę PRODUCT, ProductHistory i flush. Nie powstają osobne transakcje per rekord.

## 8. Testy rollback i PostgreSQL

Rzeczywiste testy PostgreSQL potwierdzają:

- APPROVED: PRODUCT `PENDING_APPROVAL -> ACTIVE`, decyzja CURRENT, evidence i historia,
- REJECTED: PRODUCT `PENDING_APPROVAL -> REJECTED`,
- druga decyzja: poprzednia CURRENT -> SUPERSEDED, nowa CURRENT, poprzedni evidence pozostaje,
- archiwalny SDS: kontrolowany błąd i zero zmian,
- SDS obcego produktu: kontrolowany błąd i zero zmian,
- błąd po utworzeniu evidence: rollback evidence, decyzji, produktu i historii,
- błąd korekty po supersedowaniu: rollback przywraca poprzednią decyzję CURRENT, evidence i status ACTIVE.

Focused testy TASK-023: `7 passed`.

## 9. ORM / schema / migracja

Istniejące modele `DecisionEvidenceModel` i `BhpDecisionModel` oraz zatwierdzone tabele były kompletne. Nie zmieniono Domain, ORM, PostgreSQL schema ani Alembic. Nie utworzono migracji i nie dodano nowych zależności.

## 10. Walidacja końcowa

- pełny pytest: `133 passed`,
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS,
- brak `SAWarning`,
- `alembic current`: `e0dd7d6468bf (head)`,
- `alembic check`: `No new upgrade operations detected.`,
- diagnostyka zmienionych plików: brak błędów,
- `git diff --check` i `git diff --cached --check`: bez błędów whitespace.

## 11. Git / bezpieczeństwo

`.env` jest ignorowany. Testowe evidence są tworzone wyłącznie w katalogach tymczasowych i nie są dodawane do repozytorium. Nie dodano sekretów, dumpów ani backupów. Nie wykonano commit ani push.

## 12. Odstępstwa i ryzyka

Mapowanie typu evidence opiera się na zatwierdzonych rozszerzeniach i istniejących enumach; analiza treści dowodu pozostaje poza zakresem. Brak concurrency framework zgodnie z TASK-023; reguła jednej decyzji CURRENT jest zabezpieczona istniejącym indeksem i logiką transakcyjną.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-024.
