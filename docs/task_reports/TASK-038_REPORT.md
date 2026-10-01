# TASK-038 REPORT

STATUS:
DONE

CHANGED:
- Domain: `DecisionEvidence.original_filename`.
- ORM: osobna kolumna `DecisionEvidenceModel.original_filename`.
- Migration: `b379f54c12a0_task_038_evidence_original_filename.py`.
- Repository/mapping: jawny round-trip Domain ↔ ORM oraz zapis nazwy źródłowej w rejestracji BHP.
- Application contract: `RegisterBhpDecisionInput.original_filename` i walidacja dla nowych rejestracji.
- Tests: testy metadanych, mapowania, kontraktu i istniejącej integracji BHP; skrypt izolowanej walidacji PostgreSQL.

IMPLEMENTED:
- `original_filename` jest metadaną źródłową niezależną od `relative_path` i `evidence_id`.
- Migracja dodaje wyłącznie kolumnę `decision_evidence.original_filename`; downgrade usuwa wyłącznie tę kolumnę.
- Kolumna jest nullable, ponieważ w bazie operatora istnieją 3 historyczne rekordy bez możliwej do potwierdzenia nazwy źródłowej. Nowe rejestracje wymagają niepustej wartości w Application i repozytorium. Historyczne rekordy pozostają czytelne z `NULL`.
- Pełny round-trip nowego rekordu zachowuje nazwę źródłową bez wyliczania jej z technicznej ścieżki.

VALIDATION:
- Focused unit tests: 35 PASS.
- Streamlit/AppTest dotyczący obecnego widoku BHP: 5 PASS.
- Izolowany PostgreSQL: migracja ze starym rekordem, odczyt `NULL`, zapis i odczyt nowego rekordu, downgrade, ponowny upgrade oraz powiązane testy integracyjne BHP: PASS.
- `alembic current` = `b379f54c12a0` i `alembic check`: PASS w izolowanym klastrze.
- `git diff --check` dla zmienionych śledzonych plików: PASS.
- Baza operatora po walidacji: nadal 3 rekordy evidence; wersja schema nadal `a97e2cb7f31d`. Nie wykonywano migracji na bazie operatora.

DATA SAFETY:
- operator data preserved: YES
- existing evidence rows found: YES (3)
- backfill performed: NO
- orphan test files after validation: NONE

SCOPE:
- UI change: NO
- filesystem change: NO
- BHP lifecycle change: NO
- SDS lifecycle change: NO
- PRODUCT change: NO
- new dependencies: NO

DEVIATIONS:
- Przejściowe ograniczenie: istniejący widok BHP nie przekazuje jeszcze `original_filename`; dopóki TASK-037 nie doda jawnego wyboru/uploadu i tej metadanej, próba nowej rejestracji kończy się kontrolowanym błędem walidacji bez zapisu. TASK-038 zabrania zmiany UI.

NEXT:
- READY TO RESUME TASK-037 po akceptacji TASK-038 i wdrożeniu migracji we właściwym środowisku.
