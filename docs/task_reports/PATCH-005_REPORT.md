# PATCH-005 REPORT

STATUS:
DONE

CAUSE:
- Acceptance rejected parsed SDS drafts when a chemical component had no `component_name`, even though chemical data is optional in the MVP.

CHANGED:
- Removed the component-name acceptance blocker.
- Filtered incomplete components before repository persistence so invalid `SDS_COMPONENTS` rows are not created.
- Added focused coverage for empty chemical data, incomplete components, complete components, and required product/SDS fields.

BEHAVIOR:
- empty Safety Profile: ALLOWED
- no components: ALLOWED
- incomplete component: SKIPPED
- valid component: SAVED
- required product/SDS fields: PRESERVED

VALIDATION:
- focused tests: `tests/unit/test_accept_sds.py` — 9 passed

CHANGES OUTSIDE SCOPE:
- parser algorithm: NONE
- PDF reader: NONE
- schema/migrations: NONE
- dependencies: NONE
- UI: NONE

RISKS / DEVIATIONS:
- NONE

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
