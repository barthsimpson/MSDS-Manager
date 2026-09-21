# PATCH-007 REPORT

STATUS:
DONE

CHANGED:
- Added `UpdateProductIdentity` for editing product name, manufacturer code, and manufacturer by existing `product_id`.
- Reused an exact existing manufacturer or created one when necessary; the old manufacturer is not removed.
- Added the `Edytuj dane produktu` action and minimal form in the selected product context.
- Added focused unit and PostgreSQL integration coverage.

BEHAVIOR:
- product_name editable: YES
- manufacturer_product_code editable: YES
- manufacturer editable: YES
- product_id unchanged: YES
- SDS preserved: YES
- BHP preserved: YES
- usage relations preserved: YES

VALIDATION:
- focused unit tests: 8 passed
- focused PostgreSQL integration: 1 passed
- UI focused test: PASS

CHANGES OUTSIDE SCOPE:
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- delete/merge: NONE

RISKS / DEVIATIONS:
- Physical retest with `XBRAKE CLEANER` remains to be performed by the user.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO PATCH-A.
