# TASK-022 — BHP Decision Application Contracts

## 1. Status

`DONE`

Zaimplementowano minimalną granicę Application dla przyszłej rejestracji decyzji BHP. Nie rozpoczęto TASK-023.

## 2. Zmienione pliki

- `app/application/dto/bhp_decisions.py`
- `app/application/dto/__init__.py`
- `app/application/ports/bhp_decision.py`
- `app/application/ports/__init__.py`
- `app/application/exceptions.py`
- `app/application/use_cases/register_bhp_decision.py`
- `app/application/use_cases/__init__.py`
- `tests/unit/test_register_bhp_decision.py`
- `docs/task_reports/TASK-022_REPORT.md`

## 3. DTO

Dodano `RegisterBhpDecisionInput` z polami:

- `product_id`,
- `sds_id`,
- `decision_status`,
- `evidence_relative_path`,
- opcjonalne `notes`.

Dodano `RegisterBhpDecisionResult` z minimalnymi danymi dla przyszłego UI:

- `decision_id`,
- `product_id`,
- `sds_id`,
- `decision_status`,
- `product_usage_status`,
- `registered_at`,
- `evidence_relative_path`.

Wykorzystano istniejące enumy Domain `BhpDecisionStatus` oraz `ProductUsageStatus`; nie utworzono duplikatów ani statusu `PENDING` decyzji.

## 4. Porty

`BhpEvidenceValidatorPort.validate()` przyjmuje ścieżkę względną dowodu i zwraca zwalidowaną/znormalizowaną ścieżkę względną. Szczegóły root path, istnienia pliku i rozszerzeń pozostają poza Application.

`BhpDecisionRepositoryPort.register()` przyjmuje cały `RegisterBhpDecisionInput` i zwraca `RegisterBhpDecisionResult`. Jest to jedna granica dla przyszłej atomowej implementacji TASK-023 obejmującej PRODUCT/SDS, evidence, decyzję i historię.

## 5. RegisterBhpDecision

Use case:

1. waliduje wymagane `product_id`, `sds_id` i `evidence_relative_path`,
2. wymaga statusu `APPROVED` albo `REJECTED` przez istniejący enum,
3. wywołuje validator dowodu przed repozytorium,
4. normalizuje białe `notes` do `None`,
5. deleguje cały zapis do portu rejestracji,
6. zwraca wynik bez wykonywania własnej persystencji.

Nie rozstrzyga istnienia PRODUCT/SDS, relacji PRODUCT-SDS, CURRENT/SUPERSEDED, statusu produktu, historii ani rollbacku. Te reguły pozostają TASK-023.

## 6. Kontrolowane błędy

Dodano `BhpDecisionValidationError` dla niepoprawnych danych Application. Błąd walidatora dowodu oraz błąd persystencji są propagowane bez fałszywego sukcesu; repozytorium nie jest wywoływane, gdy wejście lub dowód nie przejdzie wcześniejszej walidacji.

## 7. Testy

Focused testy TASK-022: `6 passed`.

Pokryto:

- poprawny `APPROVED`,
- poprawny `REJECTED`,
- wywołanie validatora i repozytorium dokładnie raz,
- przekazanie znormalizowanej ścieżki i notatek,
- błędny status bez delegacji,
- brak ścieżki dowodu bez delegacji,
- błąd validatora bez wywołania repozytorium,
- propagację błędu persystencji.

## 8. Regresja i walidacja

- pełny pytest: `126 passed`,
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS,
- brak `SAWarning`,
- `alembic current`: `e0dd7d6468bf (head)`,
- `alembic check`: `No new upgrade operations detected.`,
- diagnostyka zmienionych plików: brak błędów.

## 9. Architektura i schema

Application nie importuje Streamlit, SQLAlchemy, psycopg, Alembic, pypdf ani adaptera filesystem. Nie wykonuje SQL, nie otwiera sesji, nie czyta `.env`, nie wykonuje commit/rollback i nie operuje bezpośrednio na filesystem.

Nie zmieniono Domain, ORM, PostgreSQL schema, Alembic ani historii Core. Nie dodano migracji ani nowych zależności.

## 10. Odstępstwa i ryzyka

Kontrakt zwraca ścieżkę dowodu z wyniku validatora, dzięki czemu przyszła infrastruktura może ją znormalizować bez logiki filesystem w Application. Walidacja relacji PRODUCT/SDS i wszystkie operacje atomowe są celowo odłożone do TASK-023.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-023.
