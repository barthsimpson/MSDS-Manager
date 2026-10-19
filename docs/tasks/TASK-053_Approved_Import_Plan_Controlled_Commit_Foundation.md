# TASK-053 — Approved Import Plan + Controlled Commit Foundation

**Projekt:** MSDS Manager
**Task ID:** TASK-053
**MODE:** INTEGRATION
**VALIDATION:** LEVEL 2
**REPORT:** STANDARD INTEGRATION
**Status:** READY / NOT AUTHORIZED FOR EXECUTION
**Wykonawca:** Codex OpenAI

---

## 1. Cel

Zaimplementować kontrolowane przejście:

Evidence JSON DRAFT
→ TASK-052 DRY RUN
→ HUMAN REVIEW
→ ApprovedImportPlan
→ revalidation
→ Controlled Commit
→ istniejące Application use cases
→ Repository / SQLAlchemy
→ PostgreSQL + SDS_ROOT_PATH

TASK-053 buduje i testuje rzeczywistą ścieżkę COMMIT.

W TASK-053:

operator DB writes = 0
operator SDS_ROOT_PATH writes = 0

Pełny COMMIT testujemy wyłącznie na:

isolated PostgreSQL
+
temporary SDS_ROOT_PATH

Realny import BATCH-001_CX do bazy operatora NIE należy do TASK-053.

---

## 2. Stan wejściowy

TASK-052 = ACCEPTED.

Dostępne są:

Evidence JSON validator
Evidence JSON mapper
Manufacturer Resolver
Product Resolver
DRY RUN plan
manual input detection
safety completeness gate

Reference case ALUCYNK z TASK-052:

JSON validation = VALID
manufacturer = CX80 POLSKA
manufacturer resolution = CREATE_CANDIDATE
product = ALUCYNK
product resolution = conditional CREATE_CANDIDATE
manufacturer_product_code = NULL
use_description = REQUIRED_MANUAL_INPUT
use_restriction = REQUIRED_MANUAL_INPUT
safety = INCOMPLETE_SAFETY_DATA
commit_readiness = NOT_READY

---

## 3. BATCH-001_CX — ważne ograniczenie

BATCH-001_CX jest celowo łatwiejszym, jednorodnym przypadkiem:

produkty
→ jeden producent
→ CX80 Polska

Jednorodność paczki upraszcza pierwszy test pełnego Controlled Commit.

Ale:

BATCH-001_CX homogeneity
≠ production architecture rule

Mechanizm TASK-053 musi być generyczny dla:

dowolnego producenta
dowolnego produktu
Manufacturer CREATE / LINK
Product CREATE / LINK
manufacturer_product_code known / NULL

ZAKAZ:

hardcoded manufacturer = CX80 POLSKA

CX80 Polska jest wyłącznie:

REFERENCE CASE / ACCEPTANCE CASE

---

## 4. Authoritative context

Czytaj minimalnie:

1. TASK-052_Evidence_JSON_Validator_DRY_RUN_Identity_Resolver.md
2. TASK-052_REPORT.md
3. TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved.md
4. TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md
5. TDR-006_Kontrolowany_import_SDS_v1.0-approved.md
6. BDR-007_Kontrolowany_import_SDS_v1.0-approved.md
7. BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved.md
8. CORE-001_MSDS_Manager_v1.6-approved_BDR009.md
9. GOV-001_Zasady_wspolpracy_v1.0-approved.md
10. GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md
11. root AGENTS.md

Jeżeli authoritative context jest sprzeczny ze stanem repo:

STOP / BLOCKED

Nie zgaduj.

---

## 5. Architecture boundary

Docelowo:

Evidence JSON
→ Validate / Map
→ DRY RUN
→ HUMAN REVIEW
→ ApprovedImportPlan
→ RevalidateApprovedImportPlan
→ ControlledCommit
    ├─ Manufacturer CREATE/LINK
    ├─ Product CREATE/LINK
    ├─ AcceptSds / AddSdsRevision
    └─ ImportSds
→ PostgreSQL + SDS_ROOT_PATH

Zakazane:

JSON
→ direct ORM INSERT
→ SQL INSERT/UPDATE

---

## 6. ApprovedImportPlan

Dodaj jawny Application DTO / process model, np.:

ApprovedImportPlan

Minimalnie zawiera:

source_json_fingerprint
document_key
source_filename

manufacturer_decision:
  action = CREATE / LINK
  canonical_name
  selected_manufacturer_id if LINK

product_decision:
  action = CREATE / LINK
  product_name
  manufacturer_product_code
  selected_product_id if LINK
  null_code_link_confirmed if required

SDS metadata:
  issue_date
  revision
  original_filename

manual_inputs:
  use_description
  use_restriction

approved safety payload

PDF:
  source identity
  fingerprint / equivalent binding

human_confirmation

Plan musi być związany z konkretnym:

Evidence JSON
+
logical SDS document_key
+
PDF
+
decyzjami człowieka

---

## 7. Human Review boundary

ApprovedImportPlan może powstać tylko po jawnych decyzjach człowieka.

Wymagają zatwierdzenia co najmniej:

Manufacturer CREATE / LINK
Product CREATE / LINK
NULL-code LINK, jeśli występuje
use_description
use_restriction
safety payload
PDF selection

Brak wymaganej decyzji:

NO ApprovedImportPlan
NO COMMIT

DRY RUN nie może sam zatwierdzić planu.

---

## 8. Source binding

ApprovedImportPlan musi przechowywać fingerprint Evidence JSON.

Przed COMMIT:

recompute fingerprint
→ compare with approved fingerprint

Jeżeli źródło zmieniło się:

SOURCE_CHANGED
→ STOP
→ new DRY RUN
→ HUMAN REVIEW

Nie wykonuj starego planu na zmienionym JSON.

---

## 9. Revalidation stanu DB

Bezpośrednio przed COMMIT ponownie zweryfikuj Manufacturer i Product.

Przykład:

DRY RUN:
CX80 POLSKA
→ CREATE_CANDIDATE

później ktoś tworzy:
CX80 POLSKA

COMMIT nie może:

utworzyć duplikatu

ani:

automatycznie zamienić CREATE → LINK

Wynik:

STALE_RESOLUTION
→ STOP
→ new DRY RUN
→ HUMAN REVIEW

Revalidation ma wykrywać co najmniej:

CREATE no longer valid
LINK target missing
LINK target identity changed
candidate count changed
approved resolution no longer matches DB state

---

## 10. Manufacturer commit

Dozwolone decyzje:

CREATE
LINK

### CREATE

Przed zapisem:

exact-match recheck

Jeżeli:

0 exact
→ CREATE przez Application / Repository

Jeżeli:

stan się zmienił
→ STALE_RESOLUTION

### LINK

Sprawdź, że zatwierdzony manufacturer_id:

exists
+
matches approved identity

Zakazane:

fuzzy linking
automatic merge
first candidate selection
case-insensitive silent merge

---

## 11. Product commit

Dozwolone:

CREATE
LINK

### CREATE

Nowy produkt może mieć:

manufacturer_product_code = NULL

Brak kodu NIE BLOKUJE.

Przed CREATE:

identity recheck

### LINK

Używaj wyłącznie zatwierdzonego product_id.

Dla:

JSON code = NULL
DB product code = known

LINK wymaga jawnego:

human confirmation

Nie zmieniaj istniejącego kodu produktu podczas importu.

TASK-053 nie wykorzystuje importu jako ukrytej:

CorrectProductIdentity
CompleteManufacturerProductCode

---

## 12. Existing Application use cases

Nie twórz równoległego persistence workflow.

Użyj istniejących:

AcceptSds
AddSdsRevision
ImportSds

zgodnie z ich istniejącą odpowiedzialnością.

Docelowo:

new Product / first SDS
→ AcceptSds

existing Product / next revision
→ AddSdsRevision

PDF storage
→ ImportSds

Jeżeli obecna implementacja uniemożliwia poprawne reuse bez równoległego zapisu:

STOP / BLOCKED

---

## 13. PDF boundary

W TASK-052 PDF nie był wymagany.

W Controlled Commit:

PDF IS REQUIRED

Przed COMMIT sprawdź:

PDF exists
PDF is readable
PDF passes existing ImportSds validation
PDF is explicitly selected for ApprovedImportPlan

Nie używaj nazwy PDF jako dowodu:

Product identity
Manufacturer identity
manufacturer_product_code

---

## 14. Filesystem

Obowiązuje:

WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION

Zachowaj:

SDS_ROOT_PATH
no-overwrite
path safety
controlled relative_path
original_filename
cleanup / compensation

Nie implementuj alternatywnego storage workflow, jeżeli ImportSds już zapewnia wymagane zachowanie.

---

## 15. Transaction / compensation

Filesystem i PostgreSQL nie są wspólną transakcją ACID.

Wymagane:

filesystem failure
→ NO DB COMMIT

DB failure after newly created file
→ DB ROLLBACK
→ remove only file created by unfinished operation

successful COMMIT
→ registered PDF must remain
→ compensation must not remove it

Nie kasuj żadnego wcześniej zarejestrowanego SDS.

---

## 16. Manual inputs

Controlled Commit wymaga co najmniej:

use_description
use_restriction

Brak:

PLAN_NOT_READY
→ NO COMMIT

Nie zmieniaj ich obecnej wymagalności.

---

## 17. Safety gate

TASK-052 wykazał dla ALUCYNK:

INCOMPLETE_SAFETY_DATA

Controlled Commit nie może tego ignorować.

Przed COMMIT wymagany jest:

approved safety payload

zgodny z obecnym Core / AcceptSds.

Zakazane:

missing extraction
→ synthetic NO_DATA

TASK-053 nie zmienia semantyki safety.

Jeżeli pełny commit nie może zostać wykonany bez nowej decyzji dotyczącej danych bezpieczeństwa:

STOP / BLOCKED

---

## 18. Reference acceptance case — ALUCYNK

Reference:

manufacturer = CX80 POLSKA
product = ALUCYNK
manufacturer_product_code = NULL
issue_date = 2023-01-23
revision = 2.0

Znany kontekst podobnych producentów:

CX80
CX80 Polska
Cx80

Nie są automatycznym exact match dla:

CX80 POLSKA

W isolated environment odtwórz scenariusz:

HUMAN APPROVES:

Manufacturer → CREATE
Product → CREATE
manufacturer_product_code → NULL
use_description → supplied
use_restriction → supplied
safety payload → valid / supplied
PDF → supplied

COMMIT:

CREATE Manufacturer
→ CREATE Product
→ import PDF
→ register SDS
→ correct CURRENT lifecycle
→ COMMIT

Po COMMIT potwierdź:

1 Manufacturer created
1 Product created
manufacturer_product_code IS NULL
1 SDS created
SDS status = CURRENT
original_filename preserved
controlled relative_path
PDF exists in temporary SDS_ROOT_PATH

---

## 19. Generic acceptance cases

Przetestuj minimum:

A. Manufacturer CREATE + Product CREATE
B. Manufacturer LINK + Product CREATE
C. Manufacturer LINK + Product LINK
D. Product LINK: JSON code=NULL + DB code=known + human confirmation
E. stale Manufacturer CREATE
F. stale Product CREATE
G. missing LINK target
H. changed Evidence JSON fingerprint
I. missing PDF
J. filesystem failure
K. DB failure after filesystem write + compensation
L. missing use_description
M. missing use_restriction
N. incomplete safety payload

Każdy scenariusz kończy się:

COMMIT

albo:

STOP without partial persisted state

---

## 20. Operator safety

TASK-053:

operator PostgreSQL writes = 0
operator SDS_ROOT_PATH writes = 0

Do integracji używaj wyłącznie:

isolated PostgreSQL
+
temporary SDS_ROOT_PATH

Nie importuj ALUCYNK do operator DB.

Nie twórz pliku ALUCYNK w operator SDS_ROOT_PATH.

Pierwszy realny import będzie osobnym Taskiem.

---

## 21. No UI

TASK-053 nie implementuje operator-facing Streamlit UI.

Dozwolone:

unit tests
integration tests
Application-level diagnostic runner

Runner nie może domyślnie wskazywać operator DB.

---

## 22. Runtime autonomy

Controlled Commit działa:

NO LLM
NO ChatGPT
NO Cerberus
NO Codex
NO Work
NO external AI

Runtime jest deterministyczny.

---

## 23. DO NOT

Nie implementuj:

real BATCH-001 operator import
operator-facing import UI
JSON → SQL
fuzzy manufacturer matching
manufacturer merge
automatic CREATE → LINK conversion
silent stale-plan repair
automatic identity correction
Core change
Domain semantic change
schema change
Alembic migration
OCR
new extraction logic
SDS-ALIAS update
runtime LLM
new dependency without approval

---

## 24. Expected change surface

Przewidywane:

app/application/dto/
app/application/use_cases/
app/application/ports/

app/infrastructure/db/repositories/
# tylko jeśli wymagane do revalidation / reuse

app/infrastructure/filesystem/
# tylko minimalna integracja z istniejącym TDR-006 workflow

tests/unit/
tests/integration/
scripts/ # optional

Nie przewiduje się:

app/domain/
migrations/
presentation/streamlit/

Jeżeli wymagany jest Domain albo schema change:

STOP / BLOCKED

---

## 25. Validation — LEVEL 2

Focused tests:

ApprovedImportPlan completeness
human confirmation
source fingerprint
DB state revalidation
STALE_RESOLUTION
Manufacturer CREATE/LINK
Product CREATE/LINK
NULL code
manual inputs
safety gate

Integration:

isolated PostgreSQL
+
temporary SDS_ROOT_PATH

Test:

full Manufacturer CREATE
→ Product CREATE
→ PDF
→ SDS
→ COMMIT

oraz:

LINK paths
CURRENT lifecycle
rollback
filesystem compensation
no-overwrite
path safety

Related regression:

TASK-052 planner/resolver
AcceptSds
AddSdsRevision
ImportSds
Product identity
SDS lifecycle
filesystem import

Nie uruchamiaj pełnego pytest.

Po testach potwierdź:

operator DB unchanged
operator SDS_ROOT_PATH unchanged
isolated DB cleaned
temporary files cleaned
no orphan test files

---

## 26. STOP conditions

STOP / BLOCKED, jeśli:

1. ApprovedImportPlan wymaga nowej tabeli/schema.
2. Potrzebny jest Core change.
3. Potrzebny jest Domain semantic change.
4. Existing use cases nie mogą zostać użyte bez równoległego workflow zapisu.
5. Nie da się wykryć stale CREATE/LINK.
6. Poprawny commit wymaga fuzzy matching.
7. Nie da się zachować DB transaction integrity.
8. Nie da się zachować TDR-006 compensation.
9. Validation wymaga write do operator DB.
10. Validation wymaga write do operator SDS_ROOT_PATH.
11. Missing safety musiałoby zostać zamienione na NO_DATA.
12. PDF identity trzeba zgadywać z filename.
13. Potrzebna jest nowa dependency.
14. Potrzebne jest operator-facing UI.
15. CX80 Polska musiałby zostać zaszyty jako reguła systemu.

---

## 27. REPORT

Utwórz:

docs/task_reports/TASK-053_REPORT.md

Raport:

STATUS
CHANGED
IMPLEMENTED

APPROVED IMPORT PLAN:
- binding
- human decisions
- readiness

REVALIDATION:
- source fingerprint
- manufacturer state
- product state
- stale resolution behavior

CONTROLLED COMMIT:
- Manufacturer
- Product
- SDS
- PDF
- transaction

ALUCYNK ISOLATED ACCEPTANCE:
- manufacturer result
- product result
- manufacturer_product_code
- manual inputs
- safety
- PDF
- SDS lifecycle
- DB rows
- filesystem artifact
- commit result

ROLLBACK / COMPENSATION

OPERATOR SAFETY:
- DB writes
- SDS_ROOT_PATH writes

VALIDATION

SCOPE

RISKS / DEVIATIONS

NEXT

---

## 28. Acceptance criteria

TASK-053 jest DONE tylko jeśli:

1. ApprovedImportPlan jest jawny.
2. Plan jest związany z konkretnym JSON + document_key.
3. Human confirmations są wymagane.
4. Source fingerprint jest rewalidowany.
5. DB identity state jest rewalidowany.
6. Zmiana stanu daje STALE_RESOLUTION.
7. Nie istnieje silent CREATE→LINK.
8. Manufacturer CREATE/LINK działa.
9. Product CREATE/LINK działa.
10. Product code=NULL może zostać utworzony.
11. Manual inputs są wymagane.
12. Safety gate nie tworzy synthetic NO_DATA.
13. PDF jest wymagany do COMMIT.
14. Existing Application use cases są użyte.
15. Nie istnieje JSON→SQL.
16. TDR-006 write-once/no-overwrite/path safety pozostaje zachowany.
17. Compensation działa.
18. Full ALUCYNK flow PASS w izolowanym środowisku.
19. Operator DB writes = 0.
20. Operator SDS_ROOT_PATH writes = 0.
21. Brak schema/migration/Core/Domain changes.
22. Brak UI.
23. Brak nowych dependencies.
24. Focused/integration tests PASS.

---

## 29. Authorization

TASK-053
STATUS: READY
EXECUTION: NOT AUTHORIZED

Start wyłącznie po jawnym poleceniu:

Wykonaj TASK-053.

Po wykonaniu:

STOP
→ TASK-053_REPORT
→ CERBERUS REVIEW
→ ARCHITEKT DECISION

Nie rozpoczynaj automatycznie realnego importu BATCH-001_CX.