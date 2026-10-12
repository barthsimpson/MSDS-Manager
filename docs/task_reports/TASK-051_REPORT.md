# TASK-051 REPORT

STATUS:
BLOCKED

CHANGED:
- Domain: NO
- Application: NO
- ORM: NO
- Repository: NO
- Migration: NO
- Tests: NO
- Report: this file only

IMPLEMENTED:
- manufacturer_product_code nullable: NO
- PRODUCT_IDENTITY_CHANGE: NO
- CODE_COMPLETION: NO
- CORRECTION audit: NO
- atomic identity update + history: NO

SCHEMA:
- previous Alembic head: `9f62c4e8b7a1` (single head)
- current Alembic revision: `9f62c4e8b7a1` (head)
- new Alembic head: NONE
- nullable change: NOT PERFORMED
- new table: NONE
- constraints: NOT CHANGED

VALIDATION:
- focused tests: NOT RUN; STOP occurred during prerequisite diagnosis
- PostgreSQL integration: NOT RUN
- upgrade: NOT RUN
- downgrade: NOT RUN
- re-upgrade: NOT RUN
- alembic current: `9f62c4e8b7a1 (head)`
- alembic check: NOT RUN
- related regression: NOT RUN
- SAWarning: NOT ASSESSED

DATA SAFETY:
- existing product codes preserved: YES; no data changes
- operator data preserved: YES; no writes or migration
- synthetic backfill: NO
- test residue: NONE

SCOPE:
- JSON mapper: NO
- resolver: NO
- DRY RUN: NO
- PDF workflow change: NO
- CURRENT/ARCHIVED change: NO
- new dependencies: NO

RISKS / DEVIATIONS:
- TASK-051 §5.6 and STOP condition 7 require the invoked Application use case to mean an explicit `CONTROLLED CORRECTION`, and require STOP if the current `UpdateProductIdentity` is publicly used as ordinary editing that cannot be unambiguously narrowed without a UX/API decision.
- `app/presentation/streamlit/product_registry.py` exposes the operation as **„Edytuj dane produktu”**, **„Edycja danych produktu”**, and **„Zapisz zmiany”**. The form directly calls `composition.update_product_identity(...)` with editable name, code, and manufacturer; it does not identify the operation as correction of an erroneous registration. `app/application/use_cases/update_product_identity.py` also describes it as editing identity fields and accepts any nonempty replacement code. Thus a real known-code A → B change can currently take the same path as error correction.
- BDR-009 §20 interprets PATCH-007 as `CONTROLLED CORRECTION`; PATCH-007's business goal concerns fixing erroneous entries. Neither document resolves how this public, general edit form must express or constrain that intent. TASK-051 §4 prohibits UI changes except minimal technical fixes. Automatically recording every call as `CORRECTION` would silently decide that distinction and could retain the same `product_id` for a real identity change, contrary to BDR-009.
- Required decision before implementation: approve a concrete UX/API boundary that makes the correction intent explicit for this public path (or otherwise directs how it is restricted). Then authorize the corresponding UI/API work or revise TASK-051 scope. No Core, BDR, TDR, schema, or application change was made.

NEXT:
- BLOCKED; STOP pending the UX/API decision above and a newly authorized implementation instruction. No subsequent TDR-013 task started.
