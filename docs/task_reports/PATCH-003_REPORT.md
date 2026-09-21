# PATCH-003 REPORT

STATUS:
DONE

CAUSE:
- Acceptance use case treated automatic PL language detection as a mandatory validation gate.

CHANGED:
- Removed the language-detection blocker from `AcceptSds` validation.
- Added focused regressions for unconfirmed language and a missing required manufacturer name.

BEHAVIOR:
- language not confirmed: ACCEPTANCE ALLOWED
- required fields validation: PRESERVED

VALIDATION:
- focused tests: `tests/unit/test_accept_sds.py` — 7 passed
- existing acceptance regression: PASS
- language false-negative regression: PASS
- missing required field regression: PASS

CHANGES OUTSIDE SCOPE:
- parser PDF: NONE
- component parser: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
