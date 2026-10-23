# TASK-057 — BATCH-001_CX Stage 1 Batch Commit

**Projekt:** MSDS Manager  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** STANDARD INTEGRATION  
**STATUS:** READY / AUTHORIZED  
**Autoryzacja Architekta:** „robimy commit całej paczki”  

## GOAL

Wykonać kontrolowany Stage 1 import całej paczki `BATCH-001_CX` do operator DB, wykorzystując udowodniony pion z TASK-056:

```text
Evidence JSON
→ manifest
→ source PDF
→ exact SHA-256
→ Stage 1 validation / identity resolution
→ controlled per-item commit
→ PRODUCT + SDS CURRENT + PDF + PRODUCT_HISTORY
```

Zakres batcha:

```text
37 PDF w manifeście
35 logical SDS / 35 Evidence JSON
2 pozycje FAILED = karty techniczne RC72, nie SDS → EXCLUDED_NON_SDS
```

ALUCYNK został już poprawnie zaimportowany w TASK-056 i ma zostać wykryty jako istniejący, zweryfikowany rekord oraz pominięty bez tworzenia duplikatu.

---

## AUTHORITATIVE CONTEXT

Minimalny kontekst:

1. `TASK-056` + `TASK-056_REPORT.md` — udowodniony realny Stage 1 commit ALUCYNK, `--source-root`, nullable admin fields, BHP gate.
2. `TASK-055` / `TASK-055-R1` — Stage 1 identity registration i human-confirmed manufacturer resolution.
3. `TASK-052` / `TASK-053` — Evidence JSON validator, resolver, ApprovedImportPlan, ControlledEvidenceImport.
4. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_MANIFEST.json`.
5. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_REPORT.md` + Golden Decisions dla BATCH-001_CX.
6. `TDR-006` — controlled SDS PDF import / write-once.
7. aktualny `TDR-013` Stage 1 / controlled Evidence JSON import.
8. `GOV-001`, `GOV-002`, root `AGENTS.md`.

Nie wykonuj szerokiej eksploracji repo bez konkretnej potrzeby.

---

## KNOWN INPUTS

### Evidence JSON

```text
docs/sds_bootstrap/BATCH-001_CX/json/
```

### Manifest

```text
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_MANIFEST.json
```

### Real source root — tylko runtime input

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\data\sds\Paczki\Paczka1 cx
```

Ta ścieżka NIE może być hardkodowana w production code ani commitowana jako globalna konfiguracja. Ma być przekazana jako runtime `--source-root`.

### Batch-wide manufacturer decision

Dla `BATCH-001_CX` obowiązuje zaakceptowana decyzja:

```text
canonical manufacturer from batch: CX80 POLSKA
→ existing operator MANUFACTURER: CX80 Polska
```

Batch-wide approval dotyczy wyłącznie tej relacji producenta dla tej paczki.

Nie oznacza zgody na automatyczne scalanie rekordów `CX80`, `Cx80` ani innych wariantów producenta poza tym batch decision.

---

## BUSINESS / PROCESS RULES

### 1. Stage 1 only

Import obejmuje:

- PRODUCT identity,
- manufacturer link,
- manufacturer_product_code, jeśli istnieje; brak → `NULL`,
- SDS issue_date,
- SDS revision,
- source PDF,
- lifecycle SDS,
- PRODUCT_HISTORY,
- `use_description=NULL`,
- `use_restriction=NULL` dla nowych PRODUCT, jeśli nie są jeszcze podane.

Nie importuj:

- SAFETY_PROFILE,
- SDS_COMPONENT,
- BHP_DECISION,
- danych Sekcji 2/3/11.

### 2. Stare COMPLETE / NEEDS_REVIEW

Status bootstrapowy `COMPLETE` / `NEEDS_REVIEW` nie jest samodzielnym kryterium importu Stage 1.

Każdy JSON musi zostać oceniony ponownie według aktualnych wymagań Stage 1:

```text
source integrity
+ required header fields
+ approved Golden decisions
+ manufacturer resolution
+ product identity resolution
+ DB state
```

Jeżeli dane wymagane dla Stage 1 są jednoznaczne i mają evidence, pozycja może być READY nawet jeśli historycznie miała `NEEDS_REVIEW` z powodu elementu poza Stage 1.

Jeżeli nierozstrzygnięcie dotyczy danych używanych przez Stage 1 → REVIEW/BLOCKED.

### 3. No guessing

Nie wolno:

- dopasowywać produktu fuzzy,
- linkować produktu po podobieństwie nazwy,
- traktować `NULL` product code jako wildcard,
- używać filename jako dowodu wartości domenowej,
- linkować producenta do `CX80` / `Cx80` na podstawie podobieństwa,
- tworzyć placeholderów,
- zamieniać braków na `NO_DATA`,
- omijać ApprovedImportPlan / Application / repository.

---

## PHASE A — FULL BATCH PREFLIGHT / ZERO WRITES

Najpierw wykonaj pełny read-only preflight wszystkich 35 Evidence JSON i odpowiadających im PDF.

Dla każdego logicznego SDS utwórz w pamięci / raporcie jeden rekord readiness zawierający co najmniej:

```text
manifest_id
json_file
source_pdf
source_sha_expected
source_sha_actual
product_name
manufacturer_canonical
manufacturer_selected_id/name
manufacturer_product_code
issue_date
revision
existing_product_candidates
existing_current_sds
classification
reason
```

### Dozwolone classification

```text
READY_CREATE
READY_ADD_REVISION
SKIP_EXACT_EXISTING
SKIP_DUPLICATE_SOURCE
REVIEW_IDENTITY
BLOCKED_SOURCE
BLOCKED_DATA
EXCLUDED_NON_SDS
```

### Source validation

Dla każdego z 35 SDS:

- JSON musi być obecny i parseable,
- manifest musi wskazywać ten JSON i source PDF,
- source PDF musi istnieć w `--source-root`,
- przelicz SHA-256 realnych bajtów,
- SHA musi być exact zgodny z manifestem / Evidence JSON,
- jeden logical SDS musi odpowiadać kontraktowi JSON.

Inna zawartość pod poprawną nazwą = `BLOCKED_SOURCE`.

### Dwa RC72

Pozycje bez logical SDS / JSON oznaczone w manifeście jako FAILED technical cards:

```text
KT CX RC72-1 (1).pdf
KT CX RC72-1 (2).pdf
```

muszą otrzymać:

```text
EXCLUDED_NON_SDS
```

i nie są błędem batch importu.

---

## PRODUCT / SDS RESOLUTION

### A. Nowy jednoznaczny PRODUCT

Jeżeli pod zatwierdzonym manufacturer `CX80 Polska` brak istniejącego produktu odpowiadającego dokładnej zatwierdzonej tożsamości:

```text
READY_CREATE
```

### B. Dokładnie istniejący PRODUCT

Automatyczny LINK produktu jest dopuszczalny wyłącznie wtedy, gdy obecny kontrakt TDR/TASK-053 pozwala to zrobić bez zgadywania i tożsamość jest jednoznaczna.

Jeżeli batch JSON ma `manufacturer_product_code=NULL`, a istniejący PRODUCT ma znany kod i brak osobnej zatwierdzonej decyzji linku:

```text
REVIEW_IDENTITY
```

Nie traktuj NULL jako wildcard.

### C. Ten sam PRODUCT, nowa jednoznaczna rewizja SDS

Jeżeli PRODUCT jest jednoznacznie istniejący pod tym samym zatwierdzonym manufacturer i nowy dokument jest kolejną rewizją zgodnie z istniejącym lifecycle:

```text
READY_ADD_REVISION
```

Commit ma użyć istniejącego mechanizmu `AddSdsRevision` / lifecycle `CURRENT → ARCHIVED`, zgodnie z obowiązującym kontraktem.

### D. Ten sam dokument już zarejestrowany

Jeżeli istniejący SDS odpowiada temu samemu PRODUCT i ma zgodne:

- issue_date,
- revision,
- source PDF po odczycie z SDS_ROOT_PATH i exact SHA-256,

oznacz:

```text
SKIP_EXACT_EXISTING
```

Nie twórz drugiego SDS ani drugiego PDF.

ALUCYNK z TASK-056 powinien przejść tą ścieżką.

### E. Istniejące podobne produkty pod innymi wariantami producenta

Jeżeli nazwa produktu wskazuje możliwy istniejący produkt pod `CX80` lub `Cx80`, ale batch jest zatwierdzony dla `CX80 Polska`:

```text
REVIEW_IDENTITY
```

Nie twórz automatycznie duplikatu i nie zmieniaj istniejącego manufacturer_id.

Przypadki takie jak obecne `XBRAKE CLEANER` lub `CX80 Płyn Konserwująco Naprawczy` mają zostać jawnie wykryte przez preflight, jeśli odpowiadają pozycji batcha.

---

## DUPLICATE SOURCE INSIDE BATCH

Jeżeli dwa wpisy batcha mają identyczny SHA-256:

1. porównaj Stage 1 identity + issue_date + revision,
2. jeżeli są zgodne — tylko pierwszy deterministyczny manifest entry może być importowany; następny:

```text
SKIP_DUPLICATE_SOURCE
```

3. jeżeli ten sam hash prowadzi do sprzecznych danych Stage 1:

```text
BLOCKED_DATA
```

Nie importuj obu jako niezależnych SDS bez rozstrzygnięcia.

---

## PHASE B — BATCH COMMIT

### Warunek startu zapisów

Jeżeli preflight wykryje którekolwiek:

```text
BLOCKED_SOURCE
BLOCKED_DATA
```

STOP przed pierwszym zapisem i zwróć pełną matrix preflight.

`REVIEW_IDENTITY` jest wyjątkiem pozycji, nie globalnym blockerem batcha.

### Pozycje do automatycznego commitu

Commituj wyłącznie:

```text
READY_CREATE
READY_ADD_REVISION
```

Pomijaj bez zapisu:

```text
SKIP_EXACT_EXISTING
SKIP_DUPLICATE_SOURCE
EXCLUDED_NON_SDS
REVIEW_IDENTITY
```

### Transaction boundary

Każdy SDS = osobny controlled commit z istniejącym mechanizmem TASK-056/TASK-053.

Nie twórz jednej globalnej transakcji dla całej paczki.

Dla każdego itemu:

```text
revalidation
→ PDF write-once
→ DB transaction
→ PRODUCT / SDS / HISTORY
→ commit
```

Jeżeli pojedynczy item zawiedzie podczas COMMIT:

```text
rollback itemu + compensation jego nowego PDF
→ STOP dalszego batch commit
→ nie rollbackuj wcześniej poprawnie zakończonych itemów
→ raportuj dokładnie committed / failed / not attempted
```

---

## REQUIRED BATCH OUTPUT

Utwórz raport / artefakt wynikowy Stage 1 batch, np.:

```text
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md
```

Ma zawierać tabelę wszystkich 37 manifest entries oraz minimum:

```text
manifest_id
PDF
JSON
preflight classification
product name
action
product_id / sds_id po sukcesie
reason / exception
```

Podsumowanie musi pokazać liczby:

```text
manifest PDFs
logical SDS
READY_CREATE
READY_ADD_REVISION
SKIP_EXACT_EXISTING
SKIP_DUPLICATE_SOURCE
REVIEW_IDENTITY
BLOCKED_SOURCE
BLOCKED_DATA
EXCLUDED_NON_SDS
COMMITTED
FAILED_DURING_COMMIT
NOT_ATTEMPTED
```

---

## EXPECTED CHANGE SURFACE

Preferuj reuse TASK-056.

Dopuszczalne:

```text
app/application/use_cases/automatic_stage1_import.py
app/infrastructure/filesystem/evidence_source_pdf.py
scripts/task057_stage1_batch_import.py
lub minimalne rozszerzenie istniejącego task056 runnera
tests/integration/test_task057_stage1_batch.py
docs/sds_bootstrap/BATCH-001_CX/
docs/task_reports/TASK-057_REPORT.md
```

Zmiana Streamlit nie jest wymagana.

---

## DO NOT

Bez osobnej decyzji NIE:

- zmieniaj Core,
- zmieniaj schema / Alembic,
- dodawaj nowe zależności,
- implementuj Safety / Sections 2, 3, 11,
- implementuj trwałą bibliotekę normalizacji RAW → canonical/existing,
- aktywuj SDS-ALIAS candidates,
- scalaj / zmieniaj istniejących MANUFACTURER,
- zmieniaj istniejące PRODUCT identity,
- importuj 2 technical cards RC72 jako SDS,
- twórz placeholdery dla admin fields,
- wykonuj fuzzy product merge,
- używaj raw SQL do importu,
- zmieniaj operator data poza wynikami kontrolowanego Stage 1 batch commit.

---

## VALIDATION — LEVEL 2

Przed operator batch commit:

1. focused unit/application tests nowego batch orchestration,
2. isolated PostgreSQL + temporary SDS root z co najmniej:
   - 2 nowe produkty,
   - 1 SKIP_EXACT_EXISTING,
   - 1 READY_ADD_REVISION,
   - 1 REVIEW_IDENTITY,
   - 1 duplicate source,
   - 1 hash mismatch → global STOP przed writes,
   - failure podczas jednego commit → item rollback + stop dalszych,
3. related regression TASK-053/055/056 controlled import,
4. `git diff --check`,
5. operator `alembic current` = `b7d4a1f03962`,
6. operator `alembic check` clean.

Nie wykonuj nowej migracji.

---

## ACCEPTANCE CRITERIA

| ID | Kryterium |
|---|---|
| A1 | Wszystkie 37 manifest entries są sklasyfikowane w preflight matrix. |
| A2 | 35 logical SDS mają sprawdzony JSON ↔ manifest ↔ real PDF ↔ exact SHA. |
| A3 | Dwa RC72 są `EXCLUDED_NON_SDS`. |
| A4 | Batch-wide manufacturer decision linkuje tylko canonical `CX80 POLSKA` do istniejącego `CX80 Polska`. |
| A5 | ALUCYNK jest wykryty jako już zaimportowany i nie jest duplikowany. |
| A6 | Potencjalne istniejące produkty pod `CX80` / `Cx80` nie są automatycznie duplikowane ani scalane; trafiają do REVIEW, jeśli tożsamość nie jest jednoznacznie zatwierdzona. |
| A7 | Duplicate source hash w batchu nie tworzy podwójnego SDS. |
| A8 | `BLOCKED_SOURCE/BLOCKED_DATA` zatrzymuje batch przed pierwszym zapisem. |
| A9 | Pozycje `READY_CREATE/READY_ADD_REVISION` są commitowane osobno i kontrolowanie. |
| A10 | Każdy nowy PRODUCT Stage 1 może zachować admin fields jako NULL; brak Safety/Components/BHP. |
| A11 | Żaden commit nie używa raw SQL ani nie omija Application/ApprovedImportPlan/revalidation. |
| A12 | Po błędzie pojedynczego itemu nie ma częściowego DB/PDF dla tego itemu; dalszy batch zostaje zatrzymany. |
| A13 | Powstaje pełny BATCH-001_STAGE1_IMPORT_REPORT z wynikami per item. |
| A14 | Brak zmian Core/schema/Alembic/dependencies. |

---

## STOP CONDITIONS

STOP przed jakimikolwiek operator writes, jeśli:

- operator Alembic head/check nie jest zgodny,
- batch source root jest niedostępny,
- manifest / JSON contract nie pozwala deterministycznie związać plików,
- jakikolwiek source PDF wymagany dla SDS jest missing albo ma SHA mismatch,
- batch manufacturer decision nie daje dokładnie jednego istniejącego `CX80 Polska`,
- preflight wykryje `BLOCKED_SOURCE` lub `BLOCKED_DATA`,
- poprawne wykonanie wymaga Core/schema/dependency change,
- trzeba zgadywać product identity.

Po rozpoczęciu commitów STOP dalsze itemy przy pierwszym runtime commit failure.

`REVIEW_IDENTITY` nie jest globalnym STOP i ma pozostać niezaimportowanym wyjątkiem.

---

## REPORT

Raport:

```text
docs/task_reports/TASK-057_REPORT.md
```

Musi zawierać:

1. wynik preflight i pełne liczniki,
2. listę committed IDs + `product_id` + `sds_id`,
3. listę skipped/excluded,
4. listę REVIEW/BLOCKED wraz z konkretnym powodem,
5. dokładną liczbę operator DB writes i nowych PDF w SDS_ROOT_PATH,
6. potwierdzenie braku duplikatu ALUCYNK,
7. zachowanie istniejących MANUFACTURER i istniejących PRODUCT,
8. testy i wyniki,
9. odchylenia / ryzyka,
10. jednoznaczny STOP po BATCH-001_CX — nie uruchamiaj Paczki2 ani kolejnego sprintu.

---

## AUTHORIZATION

Task jest jawnie autoryzowany przez Architekta Operacyjnego poleceniem:

```text
robimy commit całej paczki
```

Codex może wykonać TASK-057 bez ponownego pytania o zgodę, ale musi respektować wszystkie STOP conditions.
