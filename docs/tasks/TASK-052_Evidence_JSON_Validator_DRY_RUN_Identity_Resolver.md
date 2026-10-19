# TASK-052 — Evidence JSON Validator + DRY RUN Identity Resolver

**Projekt:** MSDS Manager  
**Task ID:** TASK-052  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** STANDARD INTEGRATION  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI  

---

## 1. GOAL

Zaimplementować pierwszy kontrolowany etap konsumpcji `Evidence JSON DRAFT` przez MSDS Manager:

Evidence JSON
→ walidacja SDS-JSON-001
→ mapowanie danych
→ Manufacturer Resolver
→ Product Resolver
→ DRY RUN
→ CREATE / LINK / HUMAN REVIEW

TASK-052 kończy się na planie DRY RUN.

W tym Tasku:

DB WRITE: NO
FILESYSTEM WRITE: NO
PDF IMPORT: NO
SDS REGISTRATION: NO
CURRENT / ARCHIVED CHANGE: NO
CORE COMMIT: NO
UI: NO

Przypadek referencyjny:

BATCH-001_CX
B001-P001_DOC-001.json
ALUCYNK

---

## 2. AUTHORITATIVE CONTEXT

Czytaj minimalnie:

1. `CORE-001_MSDS_Manager_v1.6-approved_BDR009.md`
2. `BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved.md`
3. `TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved.md`
4. `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md`
5. `SDS-JSON-001_Kontrakt_Evidence_JSON_DRAFT_v1.0-approved.md`
6. `BATCH-001_GOLDEN_DECISIONS.md`
7. `TASK-050_IMPACT_ANALYSIS_REPORT.md`
8. `TASK-051-R1_REPORT.md`
9. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
10. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
11. root `AGENTS.md`

`UI-GUIDE-001` nie jest wymagany — TASK-052 nie obejmuje UI.

Konflikt authoritative context ze stanem repo:

STOP / BLOCKED

Nie zgaduj.

---

## 3. ARCHITECTURE BOUNDARY

Docelowy przepływ:

Evidence JSON
→ ValidateEvidenceJson
→ MapEvidenceJson
→ ResolveManufacturer
→ ResolveProduct
→ BuildSdsImportPlan
→ DRY RUN RESULT

TASK-052 NIE wywołuje w trybie zapisu:

AcceptSds
AddSdsRevision
ImportSds

Nie zapisuje planu do PostgreSQL.

---

## 4. SDS-JSON VALIDATION

Waliduj co najmniej:

schema_version
source
documents[]
document_key
page_range
identification
document_metadata
parties
validation
review_status

Dozwolone stany ekstrakcji:

FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE

Reguły:

FOUND
→ value != null
→ evidence present

NOT_FOUND
→ value = null

AMBIGUOUS
→ brak importowalnej wartości bez HUMAN REVIEW

UNREADABLE
→ brak importowalnej wartości

Zabronione:

NOT_FOUND / AMBIGUOUS / UNREADABLE
→ NO / NO_DATA / NOT_APPLICABLE

Wynik:

VALID / INVALID
errors[]
warnings[]

INVALID
→ brak identity resolution dla danego logical SDS.

---

## 5. LOGICAL SDS

Zachować:

1 PDF
→ 1..N logical SDS

Każdy `document_key` otrzymuje osobny DRY RUN.

---

## 6. DATA MAPPING

Mapuj minimalnie:

JSON product_name
→ PRODUCT candidate.product_name

JSON manufacturer_product_code
→ PRODUCT candidate.manufacturer_product_code

JSON MANUFACTURER party
→ Manufacturer Resolver input

JSON issue_date
→ candidate SDS.issue_date

JSON revision
→ candidate SDS.revision

JSON original_filename
→ candidate SDS.original_filename

Dane:

file_sha256
document_key
page_range
source_text
evidence
validation

pozostają danymi procesu.

Nie dodawaj dla nich pól Core / DB.

---

## 7. GOLDEN DECISIONS

`BATCH-001_GOLDEN_DECISIONS.md` może być używany tylko dla identycznych zatwierdzonych przypadków.

Przykłady:

"CX80 POLSKA, CX80 GmbH"
→ "CX80 POLSKA"

"CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA"
→ "CX80 POLSKA"

Nowy albo tylko podobny RAW value:

→ HUMAN REVIEW

Nie aktualizuj `SDS-ALIAS-001`.

Nie twórz runtime normalization library.

---

## 8. MANUFACTURER RESOLVER

Wejście:

canonical manufacturer name

Exact resolution:

0 exact
→ CREATE_CANDIDATE

1 exact
→ LINK_CANDIDATE

>1 exact
→ HUMAN_REVIEW

Podobne rekordy można zwrócić jako:

warnings[]
similar_records[]

ale NIE mogą powodować automatycznego LINK.

Zakazane:

fuzzy auto-link
case-insensitive auto-merge
first()
cichy wybór pierwszego rekordu

---

## 9. PRODUCT RESOLVER — KOD ZNANY

Jeżeli:

manufacturer_product_code != NULL

kandydaci:

product_name
+ manufacturer_id
+ manufacturer_product_code

Wynik:

0 → CREATE_CANDIDATE
1 → LINK_CANDIDATE
>1 → HUMAN_REVIEW

Jeżeli manufacturer nie ma jeszcze jednoznacznego `manufacturer_id`:

→ PENDING_MANUFACTURER / HUMAN_REVIEW

Nie zgaduj manufacturer_id.

---

## 10. PRODUCT RESOLVER — KOD NULL

Jeżeli:

manufacturer_product_code = NULL

brak kodu:

NIE BLOKUJE

Po jednoznacznym manufacturer_id kandydaci:

product_name
+ manufacturer_id

Wynik:

0
→ CREATE_CANDIDATE

1
→ LINK_CANDIDATE
→ HUMAN CONFIRMATION REQUIRED

>1
→ HUMAN_REVIEW

Jeżeli:

JSON code = NULL
DB code = known

wynik może być:

LINK_CANDIDATE
+ HUMAN CONFIRMATION REQUIRED

Nigdy automatyczny LINK.

`NULL` nie jest wildcardem.

---

## 11. RESOLUTION STATUSES

Minimalnie:

CREATE_CANDIDATE
LINK_CANDIDATE
HUMAN_REVIEW
INVALID

Dozwolony wewnętrzny:

PENDING_MANUFACTURER

Statusy nie trafiają do Core.

---

## 12. DRY RUN READ MODEL

Dodaj minimalny Application DTO, np.:

SdsJsonImportPlan

Pola co najmniej:

document_key
source_filename
validation_status

mapped_product_name
mapped_manufacturer_product_code
mapped_issue_date
mapped_revision

manufacturer_resolution:
- status
- canonical_name
- candidate_ids[]
- similar_records[]

product_resolution:
- status
- candidate_ids[]

required_manual_inputs[]
warnings[]
blockers[]

commit_readiness

Dozwolone:

NOT_READY
READY_FOR_CONTROLLED_COMMIT

TASK-052 nie wykonuje COMMIT.

---

## 13. MANUAL INPUTS

Obecny AcceptSds wymaga:

use_description
use_restriction

Jeżeli nie ma ich w Evidence JSON:

required_manual_inputs:
- use_description
- use_restriction

Nie blokuje to DRY RUN.

Powoduje:

commit_readiness = NOT_READY

Nie zmieniaj ich wymagalności.

---

## 14. SAFETY DATA GATE

Reguła:

brak ekstrakcji
≠ NO_DATA

Zabronione:

safety_profile = {}
→ domenowe NO_DATA

Niekompletne dane bezpieczeństwa:

INCOMPLETE_SAFETY_DATA
commit_readiness = NOT_READY

Identity resolution nadal musi zostać wykonany.

---

## 15. PDF BOUNDARY

TASK-052 = ETAP A:

JSON DATA MAPPING / DRY RUN

PDF:

NIE jest wymagany do DRY RUN.

Nie wykonuj:

PDF copy
storage validation
SDS_ROOT_PATH write
SDS registration
CURRENT / ARCHIVED changes

---

## 16. READ-ONLY DATA ACCESS

PostgreSQL może być używany tylko do:

Manufacturer resolution
Product resolution
read-only diagnostics

Zakazane:

INSERT
UPDATE
DELETE
COMMIT zmian
schema change
Alembic migration

---

## 17. REFERENCYJNY TEST — ALUCYNK

Użyj:

B001-P001_DOC-001.json

Oczekiwane dane:

product_name = ALUCYNK
manufacturer_product_code = NULL
manufacturer canonical = CX80 POLSKA
issue_date = 2023-01-23
revision = 2.0

Znany stan precheck:

PRODUCT exact ALUCYNK = 0
MANUFACTURER exact CX80 POLSKA = 0

similar:
CX80
Cx80

Oczekiwany DRY RUN:

JSON
→ VALID

manufacturer_product_code
→ NULL
→ ACCEPTABLE

MANUFACTURER
→ CREATE_CANDIDATE
→ similar_records: CX80 / Cx80
→ HUMAN CONFIRMATION REQUIRED

PRODUCT
→ CREATE_CANDIDATE
  po rozstrzygnięciu / planowanym utworzeniu manufacturer

use_description
→ REQUIRED_MANUAL_INPUT

use_restriction
→ REQUIRED_MANUAL_INPUT

safety
→ INCOMPLETE_SAFETY_DATA

commit_readiness
→ NOT_READY

Kluczowa reguła:

ALUCYNK
≠ NOT RECOGNIZED

ALUCYNK
= recognized from JSON
+ new PRODUCT candidate

---

## 18. TESTY RESOLVERA

Manufacturer:

0 exact → CREATE_CANDIDATE
1 exact → LINK_CANDIDATE
>1 exact → HUMAN_REVIEW

Product z kodem:

0 / 1 / >1

Product bez kodu:

0 / 1 / >1

Known DB code vs JSON NULL:

→ LINK_CANDIDATE
→ HUMAN CONFIRMATION REQUIRED

AMBIGUOUS:

→ brak importowalnej wartości
→ HUMAN_REVIEW

UNREADABLE:

→ brak importowalnej wartości
→ NOT equivalent to NO

---

## 19. NO UI

Nie implementuj nowego ekranu Streamlit.

Wynik przez:

Application DTO
tests
controlled diagnostic entry point

Dopuszczalny dev-only runner w `scripts/`:

READ ONLY
NO COMMIT
NO production dependency

---

## 20. AUTONOMY

Runtime TASK-052:

BEZ LLM
BEZ ChatGPT
BEZ Cerberusa
BEZ Codexa
BEZ Work
BEZ external AI

Deterministycznie:

JSON
+ approved Golden Decisions
+ repository reads
+ approved rules

---

## 21. DO NOT

Nie implementuj:

Approved Import Plan for COMMIT
AcceptSds commit integration
AddSdsRevision integration
ImportSds integration
PDF storage
filesystem write
PostgreSQL write
schema migration
CURRENT / ARCHIVED changes
PENDING_APPROVAL
BHP decision
UI import screen
fuzzy matching
manufacturer merge
SDS-ALIAS changes
SDS-JSON changes
OCR
new extraction logic
runtime LLM

Nie zmieniaj:

CORE
BDR
TDR

---

## 22. EXPECTED CHANGE SURFACE

Przewidywane:

app/application/
app/infrastructure/db/
tests/unit/
tests/integration/
scripts/  # opcjonalnie

Infrastructure wyłącznie read-only query/repository additions.

Nie przewiduje się:

migrations/
presentation/streamlit/

Jeżeli Domain change jest konieczny:

STOP / BLOCKED

i opisz powód.

---

## 23. VALIDATION — LEVEL 2

Focused Unit/Application:

SDS-JSON validation
mapping
Golden Decision exact reuse
Manufacturer Resolver
Product Resolver
DRY RUN plan
manual inputs
safety gate

PostgreSQL integration na izolowanym DB:

read-only manufacturer resolution
read-only product resolution
0 / 1 / >1 candidates
NULL code cases

Po testach:

new records = 0
changed records = 0

Jeżeli ALUCYNK używa operator DB:

READ ONLY
writes = 0

Related regression:

AcceptSds foundation
Product identity read models
Manufacturer/Product repositories

Bez pełnego pytest.

---

## 24. STOP CONDITIONS

STOP / BLOCKED, jeśli:

1. SDS-JSON-001 nie wystarcza do walidacji.
2. Potrzebna jest zmiana SDS-JSON-001.
3. Golden Decisions wymagają runtime normalization library.
4. Resolver wymaga fuzzy matching.
5. Repository nie zwraca wszystkich kandydatów bez cichego first().
6. DRY RUN wymaga DB write.
7. Trzeba modyfikować AcceptSds / AddSdsRevision.
8. Brak kodu producenta ponownie staje się blockerem.
9. Partial safety wymaga sztucznego NO_DATA.
10. PDF jest wymagany do DRY RUN.
11. Potrzebny jest schema change / Alembic.
12. Potrzebna jest nowa dependency.
13. Potrzebny jest operator-facing UI.
14. Trzeba zgadywać semantykę identity.

---

## 25. REPORT

Utwórz:

docs/task_reports/TASK-052_REPORT.md

Raport:

STATUS
CHANGED
IMPLEMENTED

ALUCYNK:
- JSON validation
- manufacturer
- similar records
- product
- manufacturer_product_code
- manual inputs
- safety gate
- commit readiness

READ-ONLY SAFETY:
- PostgreSQL writes
- filesystem writes
- PDF operations
- schema changes
- migrations

VALIDATION:
- unit/application
- PostgreSQL integration
- related regression
- git diff --check

SCOPE:
- UI: NO
- AcceptSds commit integration: NO
- PDF import: NO
- CURRENT/ARCHIVED change: NO
- new dependencies

RISKS / DEVIATIONS

NEXT

---

## 26. ACCEPTANCE CRITERIA

TASK-052 jest DONE tylko jeśli:

1. Evidence JSON jest walidowany wg SDS-JSON-001.
2. FOUND / NOT_FOUND / AMBIGUOUS / UNREADABLE zachowują semantykę.
3. Brak kodu producenta nie blokuje DRY RUN.
4. Golden Decision działa tylko dla identycznych zatwierdzonych przypadków.
5. Manufacturer Resolver obsługuje 0 / 1 / >1.
6. Product Resolver obsługuje 0 / 1 / >1.
7. Brak fuzzy auto-link.
8. NULL nie działa jak wildcard.
9. Powstaje jawny DRY RUN plan.
10. use_description / use_restriction są manual inputs.
11. Partial safety nie tworzy NO_DATA.
12. ALUCYNK daje oczekiwany CREATE candidate flow.
13. PostgreSQL writes = 0.
14. Filesystem writes = 0.
15. PDF nie jest wymagany.
16. Brak schema / Alembic.
17. Brak operator-facing UI.
18. Focused validation PASS.

---

## 27. AUTHORIZATION

TASK-052
STATUS: READY
EXECUTION: NOT AUTHORIZED

Start dopiero po:

Wykonaj TASK-052.

Po wykonaniu:

STOP
→ TASK-052_REPORT
→ CERBERUS REVIEW
→ ARCHITEKT DECISION

Nie rozpoczynaj automatycznie Controlled Commit Task.