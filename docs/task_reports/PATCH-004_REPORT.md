# PATCH-004 REPORT

STATUS:
DONE

CAUSE:
- The PDF adapter accessed encrypted document pages without first attempting the supported empty-password decryption.

CHANGED:
- Added `decrypt("")` handling for encrypted PDFs before text extraction.
- Preserved the controlled read error when empty-password decryption fails.
- Added focused tests for plain, empty-password encrypted, password-required, and textless PDFs.

BEHAVIOR:
- plain PDF read: PASS
- encrypted PDF with empty-password decrypt: PASS
- password-required PDF: CONTROLLED FAIL

VALIDATION:
- focused tests: `tests/unit/test_pdf_sds_extractor.py` — 5 passed

CHANGES OUTSIDE SCOPE:
- parser fields: NONE
- language acceptance: NONE
- schema/migrations: NONE
- dependencies: NONE
- UI: NONE

RISKS / DEVIATIONS:
- The default `.pytest_tmp` was locked by the operating system, so focused tests were run with an isolated temporary base directory; test behavior was unchanged.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
