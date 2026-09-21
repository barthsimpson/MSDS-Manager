# MAINT-001 REPORT

STATUS:
DONE

IDENTIFIED FILE ARTIFACTS:
- `data/sds/task019/` — 45 PDF artifacts, all scoped to TASK-019 test runs.

IDENTIFIED DB RECORDS:
- `06bc741059e542c4b149ab1abfee4153` — `CX 80 XBAKE CLEANER`; manufacturer `CX-80 Polska`; code `odradzane`; status `PENDING_APPROVAL`; current SDS `CX 80 XBAKE CLEANER rew. 01-08-2015.pdf`; usage locations `0`; BHP decisions `0`. One SDS/profile/component/history; no usage or BHP dependencies.
- `40e859006b5e433aba5eeaa5f0a40df2` — `IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO`; manufacturer `CX80 Polska`; code `30470`; status `PENDING_APPROVAL`; current SDS `30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf`; usage locations `0`; BHP decisions `0`. Duplicate/erroneous manufacturer record with one SDS/profile/component/history.

DELETED:
- `data/sds/task019/` and its 45 test PDFs.
- The two listed products and their SDS profiles, components, documents, and product histories in one transaction.
- Two now-orphaned manufacturers: `CX-80 Polska` and `CX80 Polska`.

PRESERVED:
- Reference `IDROLIN` product `7bd18a8ef2f84192b2d13263799d42a2` (`Sherwin-Williams`, code `30470`, 2 usage locations, 1 BHP decision).
- Reference `XBRAKE CLEANER` product `833c0080c0a34bd1a40f5b2be18b82a6`.
- All real SDS files listed by the MAINT task; each was verified present after cleanup.

FINAL STATE:
- task019 removed: YES
- ambiguous records remaining: NO
- real SDS files preserved: YES

CHANGES OUTSIDE SCOPE:
- code: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM PATCH-006.
