# TASK-017 — Minimal SDS Application Contracts

## 1. Status

`DONE`

TASK-017 został wykonany po uzupełnieniu roboczych źródeł Sprintu 3. Zgodnie z decyzją użytkownika dokumenty BDR/TDR bez sufiksu `approved` zostały przyjęte jako obowiązujące źródła robocze.

Sprint 3 pozostaje dokumentem `v0.1-draft`, ale zakres TASK-017 jest jednoznacznie określony i nie wymagał nowej decyzji biznesowej ani architektonicznej.

## 2. Zakres sprawdzenia

Wykonano ponowną kontrolę katalogu `docs/tasks` oraz wyszukiwanie po nazwach i treści wymaganych dokumentów.

### Dostępne źródła

- `BDR-001_MSDS_Manager_v1.1.md`
- `BDR-002_MSDS_Manager_v1.2-approved.md`
- `BDR-003_MSDS_Manager.md`
- `BDR-005_MSDS_Manager_v1.0-approved.md`
- `CORE-001_MSDS_Manager_v1.2-approved.md`
- `TDR-001_MSDS_Manager.md`
- `TDR-002_MSDS_Manager.md`
- `TDR-003_MSDS_Manager.md`
- `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved.md`
- `SPRINT-003_Dodaj_SDS_v0.1-draft.md`

`SPRINT-003_Dodaj_SDS_v0.1-draft.md` został zaakceptowany jako źródło robocze na podstawie jawnej decyzji użytkownika.

## 3. Wykonane działania

- Odczytano treść TASK-017.
- Sprawdzono root `AGENTS.md`.
- Zweryfikowano dostępność wymaganych dokumentów w `docs/tasks`.
- Przyjęto dostępny draft Sprintu 3 jako źródło robocze.
- Dodano DTO SDS, porty `SdsExtractorPort` i `SdsFileValidatorPort` oraz use case `PrepareSdsDraft`.
- Dodano testy jednostkowe kontraktów Application.

## 4. Zmiany w repozytorium

Dodano lub zmieniono wyłącznie Application, testy kontraktów i raport:

- `app/application/dto/sds.py`
- `app/application/dto/__init__.py`
- `app/application/ports/sds_extractor.py`
- `app/application/ports/__init__.py`
- `app/application/use_cases/prepare_sds_draft.py`
- `app/application/use_cases/__init__.py`
- `app/application/exceptions.py`
- `tests/unit/test_sds_application_contracts.py`
- `docs/task_reports/TASK-017_REPORT.md`

Nie zmieniono Domain, ORM, migracji, PostgreSQL schema ani zależności.

## 5. Zrealizowane kontrakty

`ExtractedSdsData` obejmuje dane identyfikacyjne, metadane, język, `SdsSafetyProfileDraft` i `SdsComponentDraft`.

`SdsSafetyProfileDraft` obejmuje zatwierdzony minimalny zakres BDR-005, w tym statusy `SafetyInformationStatus` z Sekcji 2 i 11.

`SdsComponentDraft` obejmuje nazwę, CAS, EC, numer REACH, koncentrację, klasyfikację i zwroty H.

`SdsDraft` jest mutowalnym DTO formularza, a `AcceptSdsInput` stanowi minimalny kontrakt wejściowy dla przyszłego TASK-019.

`PrepareSdsDraft` deleguje walidację ścieżki i ekstrakcję, a następnie zwraca draft. Nie zapisuje do Core i nie tworzy PRODUCT, MANUFACTURER ani SDS.

Brakujące dane są reprezentowane przez `None`, lista składników może być pusta, a manual fallback jest możliwy przez mutowalne DTO. Nie dodano confidence score ani parser framework.

## 6. Stan wcześniejszego Sprintu

Według wcześniejszego checkpointu po SPRINT-002:

- testy przed implementacją: `100 passed`,
- testy TASK-017: `4 passed in 0.15s`,
- pełny pytest po implementacji: `104 passed in 4.22s`,
- Alembic head: `e0dd7d6468bf`,
- schema: `12 tables`,
- schema drift: brak,
- dane biznesowe i fixture TASK-016: brak.

Brak `SAWarning` przy `-W error::sqlalchemy.exc.SAWarning`.

## 7. Alembic, architektura i bezpieczeństwo

- `alembic current` — `e0dd7d6468bf (head)`.
- `alembic check` — `No new upgrade operations detected.`
- brak nowej rewizji, zmian ORM i zmian schema.
- Application nie importuje Streamlit, SQLAlchemy, psycopg ani biblioteki PDF.
- Nie dodano parsera PDF, OCR, AI/LLM, confidence scoring, trwałych draftów ani workflow engine.
- Nie zmieniono zależności i nie dodano sekretów, PDF, MSG, dumpów ani backupów.
- Nie wykonano commit ani push.

## 8. Zakres poza wykonaniem

Nie rozpoczęto TASK-018 ani TASK-019, parsera PDF, OCR, AI/LLM, Streamlit Add SDS UI, persystencji SDS ani workflow BHP/REACH.

Odstępstwa:

- Sprint 3 jest dostępny jako `v0.1-draft`, a nie formalnie `v1.0-approved`; użytkownik jawnie zaakceptował go jako źródło robocze.
- BDR-001, BDR-003 i TDR-001..003 nie mają sufiksu `approved`; użytkownik jawnie zaakceptował te źródła.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-018.
