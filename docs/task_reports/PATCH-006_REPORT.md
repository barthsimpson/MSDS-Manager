# PATCH-006 REPORT

STATUS:
DONE

REUSED EXISTING LOGIC:
- Existing `SdsFileValidator` and `TransactionExecutor`.
- Existing SDS persistence lifecycle for CURRENT/ARCHIVED, product history, safety profile, and optional components.

CHANGED:
- Added `AddSdsRevision` and `AddSdsRevisionInput` for an explicitly selected existing `product_id`.
- Added repository/composition support that never resolves or creates a product from parser identity fields.
- Added a `Dodaj nową rewizję SDS` action in the selected product context with PDF, revision, and issue-date inputs.
- Added focused unit and PostgreSQL lifecycle coverage.

LIFECYCLE RESULT:
- product_id unchanged: YES
- old SDS archived: YES
- new SDS current: YES
- product pending approval: YES
- usage relations preserved: YES
- previous BHP preserved as history: YES
- previous BHP inherited by new SDS: NO

VALIDATION:
- focused unit tests: 15 passed
- focused PostgreSQL integration: 1 passed
- UI focused test: PASS

CHANGES OUTSIDE SCOPE:
- schema/migrations: NONE
- dependencies: NONE
- parser algorithm: NONE
- product edit/delete: NONE

RISKS / DEVIATIONS:
- Physical retest with a real two-revision product remains to be performed by the user.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO PATCH-A.
