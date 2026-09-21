# PATCH-004 R1 REPORT

STATUS:
DONE

ROOT CAUSE:
- `pypdf` requires `cryptography` to decrypt AES-encrypted PDF objects, but the project did not declare that dependency.

DEPENDENCY CHANGE:
- file: `pyproject.toml`
- dependency: `cryptography`
- version rule: `>=3.1`

VALIDATION:
- focused tests: `tests/unit/test_pdf_sds_extractor.py` — 6 passed
- plain PDF: PASS
- AES encrypted PDF: PASS
- password-required PDF: CONTROLLED FAIL
- textless PDF: PASS

CHANGES OUTSIDE SCOPE:
- parser fields: NONE
- component parser: NONE
- language acceptance: NONE
- schema/migrations: NONE
- UI: NONE

RISKS / DEVIATIONS:
- Physical retest with `Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf` remains to be performed by the user.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
