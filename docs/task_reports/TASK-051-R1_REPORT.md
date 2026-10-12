# TASK-051-R1 REPORT

STATUS:
DONE

CHANGED:
- Domain: `Product.manufacturer_product_code: str | None`; domain-specific `ProductIdentityChange` with `CODE_COMPLETION` / `CORRECTION`.
- Application: separate `CompleteManufacturerProductCode` and `CorrectProductIdentity` inputs/use cases; removed public general `UpdateProductIdentity`; nullable code in relevant read DTOs and SDS acceptance foundation.
- ORM: nullable PRODUCT code and `ProductIdentityChangeModel`.
- Repository: locked PRODUCT identity updates, one full old/new history snapshot in the same transaction, cleanup of identity history on explicit PRODUCT deletion.
- Migration: one revision `c6a8f1d2940e`; no backfill or identity index/unique constraint.
- UI: separate „Uzupełnij kod producenta” and „Korekta danych identyfikacyjnych”; correction requires explicit confirmation of error correction.
- Tests: focused unit, PATCH-007 regression, isolated PostgreSQL integration, migration and operator-data verification.

IMPLEMENTED:
- manufacturer_product_code nullable: YES; `None` represents unknown code, and blank SDS/correction input is normalized to `None`.
- PRODUCT_IDENTITY_CHANGE: YES; separate full-snapshot model/table.
- CODE_COMPLETION: YES; only `NULL → nonempty code` in the same PRODUCT, preserving name and manufacturer; known code is rejected.
- CORRECTION audit: YES; explicit correction records one `CORRECTION` snapshot; `NULL → code` is rejected on this path.
- atomic identity update + history: YES; both writes use one SQLAlchemy transaction, and injected history-insert failures roll back completion and correction.

SCHEMA:
- previous Alembic head: `9f62c4e8b7a1` (single head).
- new Alembic head: `c6a8f1d2940e` (single head).
- nullable change: `products.manufacturer_product_code` from NOT NULL to NULLABLE.
- new table: `product_identity_changes`; empty after operator migration.
- constraints: `change_id` PK; `product_id` FK to `products`; `change_kind` CHECK for `CODE_COMPLETION` / `CORRECTION`; old/new codes nullable; `changed_at` NOT NULL. No new PRODUCT identity unique constraint or index.

VALIDATION:
- focused tests: 75 passed (identity, ORM metadata, AcceptSds foundation, registry UI, supervisory sorting).
- PostgreSQL integration: 4 passed in disposable `task051_*` database, including NULL PRODUCT, completion, correction, PATCH-007 relations, rejection and rollback. The database was removed.
- upgrade: PASS on isolated PostgreSQL and operator PostgreSQL.
- downgrade: PASS on isolated PostgreSQL at baseline with non-NULL codes.
- re-upgrade: PASS on isolated PostgreSQL.
- alembic current: `c6a8f1d2940e (head)` on isolated and operator databases.
- alembic check: `No new upgrade operations detected` on isolated and operator databases.
- related regression: PATCH-007, SDS acceptance foundation, history transaction, registry UI and supervisory read passed. `git diff --check` passed.
- SAWarning: none observed in focused test output.

DATA SAFETY:
- existing product codes preserved: YES; all 3 operator PRODUCT records were compared field by field before and after migration and were unchanged.
- operator data preserved: YES; only schema migration was applied; no operator test fixtures or BATCH-001 data were written.
- synthetic backfill: NO.
- test residue: NONE; disposable database and dedicated pytest temporary directory removed.

SCOPE:
- JSON mapper: NO
- resolver: NO
- DRY RUN: NO
- PDF workflow change: NO
- CURRENT/ARCHIVED change: NO
- new dependencies: NO

RISKS / DEVIATIONS:
- Downgrade back to NOT NULL requires every PRODUCT code to be non-NULL. The downgrade was validated before inserting NULL test products; after real NULL products exist, an operator must resolve them before downgrade. No placeholder or automatic cleanup was added.
- Existing non-JSON `AcceptSds` product lookup is unchanged, including its pre-existing ambiguity behavior. The TDR-013 resolver remains for a later, separately authorized Task.

NEXT:
- READY FOR CERBERUS REVIEW. STOP; no subsequent TDR-013 task started.
