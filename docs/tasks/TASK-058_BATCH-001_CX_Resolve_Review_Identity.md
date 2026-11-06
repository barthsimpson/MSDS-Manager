# TASK-058 — BATCH-001_CX: Resolve 11 REVIEW_IDENTITY + Controlled Completion

**Projekt:** MSDS Manager  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** STANDARD INTEGRATION  
**STATUS:** READY / AUTHORIZED  
**Autoryzacja Architekta:** „zatwierdzam” — dla decyzji producenta i PRODUCT opisanych poniżej.

## GOAL

Domknąć wyłącznie 11 pozycji `REVIEW_IDENTITY` pozostawionych przez TASK-057 w `BATCH-001_CX`, wykorzystując jawnie zatwierdzone decyzje Architekta, bez ponownego importowania 22 pozycji już committed i bez uruchamiania Paczki2.

Docelowy przebieg:

```text
11 REVIEW_IDENTITY
→ zatwierdzone decyzje producenta / produktu
→ pełny read-only re-preflight tych 11 pozycji
→ ApprovedImportPlan / identity correction plan
→ controlled per-item commit
→ aktualizacja raportu BATCH-001
→ STOP
```

TASK-058 nie tworzy jeszcze produkcyjnej globalnej biblioteki normalizacji. Ma jednak utrwalić zatwierdzone warianty i decyzje w kontrolowanym artefakcie batcha tak, aby późniejszy mechanizm biblioteki mógł je przejąć bez ponownego odtwarzania decyzji człowieka.

---

## AUTHORITATIVE CONTEXT

Minimalny kontekst:

1. `TASK-057` + `TASK-057_REPORT.md`.
2. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md`.
3. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_BATCH_DECISION.json`.
4. `TASK-056` + raport — udowodniony controlled Stage 1 commit.
5. `TASK-055-R1` — human-confirmed manufacturer link.
6. `TASK-051-R1` — controlled `CorrectProductIdentity` / audit `CORRECTION`.
7. aktualny `TDR-013` Stage 1 / ApprovedImportPlan / controlled commit.
8. `TDR-006` — controlled PDF import / write-once.
9. `BDR-003` — SDS lifecycle `CURRENT / ARCHIVED`, brak automatycznego rozstrzygania duplikatów.
10. `GOV-001`, `GOV-002`, root `AGENTS.md`.

Nie wykonuj szerokiej eksploracji repo bez konkretnej potrzeby.

---

## INPUT / SOURCE ROOT

Evidence JSON i manifest pozostają w:

```text
docs/sds_bootstrap/BATCH-001_CX/
```

Realne PDF:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\data\sds\Paczki\Paczka1 cx
```

Ścieżkę przekazuj wyłącznie jako runtime `--source-root`.
Nie hardkoduj jej w production code ani w globalnej konfiguracji.

Exact SHA-256 realnych bajtów pozostaje obowiązkowe.

---

# 1. ZATWIERDZONE DECYZJE PRODUCENTA

Wszystkie poniższe warianty oznaczają dla `BATCH-001_CX` tego samego istniejącego producenta:

```text
manufacturer_id = a11c4d78f64b41f89de6ec0196a9254b
manufacturer_name = CX80 Polska
```

### M1 — starsza forma prawna

RAW / canonical observed:

```text
CX 80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA JAWNA
```

zatwierdzone jako:

```text
CX80 Polska
```

Dotyczy minimum:

```text
B001-P005
B001-P014
B001-P025
```

### M2 — wariant zapisu/case

RAW / canonical observed:

```text
CX80 Polska
```

zatwierdzone jako istniejący:

```text
CX80 Polska
```

Dotyczy minimum:

```text
B001-P008
B001-P026
```

### M3 — długa historyczna nazwa / warianty literalne

RAW / canonical observed:

```text
CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA
(CX 80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA JAWNA,
 CX-80 POLSKA AGATA NADERA, DARIUSZ NADERA SPÓŁKA KOMANDYTOWA)
```

zatwierdzone jako:

```text
CX80 Polska
```

Dotyczy minimum:

```text
B001-P011
B001-P012
B001-P031
```

### Reguła zakresu

Te decyzje są human-approved dla danych BATCH-001_CX.

TASK-058 ma je zapisać w kontrolowanym artefakcie decyzji batcha, np.:

```text
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_REVIEW_DECISIONS.json
```

Artefakt musi zachować co najmniej:

```text
observed_value
canonical_target_name
canonical_target_id
source_batch
source_manifest_ids
human_approved = true
status = APPROVED_BATCH_DECISION
```

Nie twórz jeszcze automatycznej globalnej reguły runtime ani tabeli DB biblioteki normalizacji.
Nie hardkoduj tych nazw w production resolverze.

---

# 2. ZATWIERDZONE DECYZJE PRODUCT

## P023 — CX80 PŁYN KONSERWUJĄCO NAPRAWCZY

Incoming:

```text
manifest_id: B001-P023
product_name: CX80 PŁYN KONSERWUJĄCO NAPRAWCZY
manufacturer_product_code: NULL
manufacturer: CX80 Polska
issue_date: 2023-01-02
revision: 1.0
```

Istniejący kandydat:

```text
product_id: e8d4fa16679240adb1bf094578367f05
product_name: CX80 Płyn Konserwująco Naprawczy
manufacturer_product_code: 0300-F0DT-500F-GJ25
manufacturer legacy: CX80
```

### Decyzja Architekta

To jest ten sam PRODUCT.

Działanie:

1. zachowaj istniejący `product_id`, nazwę display i znany kod producenta,
2. skoryguj `manufacturer_id` z legacy `CX80` do istniejącego `CX80 Polska` wyłącznie przez kontrolowany `CorrectProductIdentity` / `CORRECTION` audit,
3. nie zmieniaj znanego kodu na NULL,
4. po revalidation istniejących SDS:
   - exact ten sam source PDF / SHA → `SKIP_EXACT_EXISTING`,
   - rzeczywiście nowy dokument dla tego samego PRODUCT → `READY_ADD_REVISION`,
   - ten sam issue_date + revision, lecz inny SHA / konflikt dokumentu → STOP dla tej pozycji jako `REVIEW_SOURCE_CONFLICT`; bez korekty PRODUCT i bez zapisu SDS.

Korekta tożsamości i ewentualny zapis nowego SDS mają być poprzedzone pełnym read-only planem. Nie wykonuj korekty PRODUCT, jeśli dokument nie ma jednoznacznego planu końcowego.

## P037 — XBRAKE CLEANER

Incoming:

```text
manifest_id: B001-P037
product_name: XBRAKE CLEANER
manufacturer_product_code: NULL
manufacturer: CX80 Polska
issue_date: 2023-01-24
revision: 3.0
```

Istniejący kandydat:

```text
product_id: 833c0080c0a34bd1a40f5b2be18b82a6
product_name: XBRAKE CLEANER
manufacturer_product_code: CX80 XBRAKE CLEANER
manufacturer legacy: Cx80
```

### Decyzja Architekta

To jest ten sam PRODUCT.

Działanie analogiczne do P023:

1. zachowaj istniejący `product_id`, nazwę i znany kod,
2. controlled `CorrectProductIdentity`: manufacturer legacy `Cx80` → `CX80 Polska`, z audytem `CORRECTION`,
3. następnie:
   - exact source → SKIP,
   - nowy jednoznaczny SDS → ADD_REVISION,
   - konflikt tej samej rewizji/daty z innym PDF → STOP itemu bez write.

## P028 — XBRAKE CLEANER liquid

Incoming:

```text
manifest_id: B001-P028
product_name: XBRAKE CLEANER liquid
manufacturer_product_code: NULL
manufacturer: CX80 Polska
issue_date: 2025-01-15
revision: 3.0
```

### Decyzja Architekta

To jest NOWY PRODUCT, odrębny od istniejącego `XBRAKE CLEANER`.

Działanie:

```text
CREATE PRODUCT
name = XBRAKE CLEANER liquid
manufacturer = existing CX80 Polska
manufacturer_product_code = NULL
use_description = NULL
use_restriction = NULL
→ controlled Stage 1 SDS import
```

Nie linkuj P028 do istniejącego XBRAKE CLEANER.

---

# 3. POZOSTAŁE 8 POZYCJI PO ZATWIERDZENIU PRODUCENTA

Po zastosowaniu M1/M2/M3 wykonaj ponownie pełny resolver PRODUCT dla:

```text
P005 P008 P011 P012 P014 P025 P026 P031
```

Oczekiwany kierunek zatwierdzony przez Architekta:

```text
manufacturer → existing CX80 Polska
brak dotychczas zatwierdzonego LINK do innego PRODUCT
→ Stage 1 CREATE, o ile revalidation operator DB nie pokaże już dokładnego istniejącego PRODUCT/SDS
```

Reguła bezpieczeństwa:

- jeżeli po zatwierdzeniu producenta pojawi się dokładny istniejący PRODUCT + exact SDS/PDF → SKIP, nie twórz duplikatu,
- jeżeli pojawi się dokładny istniejący PRODUCT, ale nowy jednoznaczny SDS → ADD_REVISION,
- jeżeli pojawi się niezatwierdzony konflikt PRODUCT wymagający nowej decyzji biznesowej → nie zgaduj; `REVIEW_IDENTITY` dla tej pozycji i kontynuuj pozostałe, chyba że konflikt ujawnia błąd systemowy lub source/data blocker.

Nie stosuj fuzzy merge ani case-insensitive PRODUCT merge jako nowej ogólnej reguły.

---

# 4. PREFLIGHT — ZERO WRITES

Przed pierwszym zapisem wykonaj pełny read-only preflight tylko 11 pozycji.

Dla każdej pokaż minimum:

```text
manifest_id
JSON
PDF
expected_sha
actual_sha
approved manufacturer decision
approved product decision, jeśli dotyczy
existing product candidates
existing SDS + CURRENT/ARCHIVED
planned identity correction, jeśli dotyczy
final classification
planned action
```

Dozwolone final classification:

```text
READY_CREATE
READY_ADD_REVISION
READY_IDENTITY_CORRECTION_AND_ADD_REVISION
READY_IDENTITY_CORRECTION_ONLY
SKIP_EXACT_EXISTING
REVIEW_IDENTITY
REVIEW_SOURCE_CONFLICT
BLOCKED_SOURCE
BLOCKED_DATA
```

Jeżeli wystąpi `BLOCKED_SOURCE` lub `BLOCKED_DATA` → STOP przed wszystkimi writes.

`REVIEW_IDENTITY` / `REVIEW_SOURCE_CONFLICT` jest wyjątkiem itemu, nie globalnym blockerem, o ile nie ujawnia problemu kontraktu wspólnego dla batcha.

---

# 5. COMMIT RULES

### Każdy item osobno

Każda z 11 pozycji ma osobny kontrolowany commit / transakcję zgodnie z TASK-057/TASK-056.

### Corrections P023/P037

Dla correction + revision preferuj jeden logicznie kontrolowany workflow Application z jednoznaczną kolejnością i rollbackiem. Jeżeli obecna architektura nie pozwala bezpiecznie połączyć korekty PRODUCT identity i SDS revision bez częściowego zapisu:

```text
STOP / BLOCKED
```

i zgłoś potrzebę decyzji technicznej zamiast ręcznie sklejać transakcje lub używać raw SQL.

### Filesystem

- exact SHA source przed write,
- PDF write-once,
- brak overwrite,
- DB fail po nowym PDF → compensation tylko pliku niezarejestrowanego,
- successful commit → PDF pozostaje registered source.

### Existing SDS lifecycle

`READY_ADD_REVISION`:

```text
previous CURRENT → ARCHIVED
new SDS → CURRENT
PRODUCT → PENDING_APPROVAL
```

Nie przenoś starej decyzji BHP.

---

# 6. DO NOT

Nie:

- importuj ponownie 22 pozycji z TASK-057,
- ruszaj ALUCYNK ani duplicate P015,
- ruszaj RC72,
- uruchamiaj Paczki2,
- implementuj Sekcji 2/3/11,
- twórz SAFETY_PROFILE / SDS_COMPONENT / BHP_DECISION,
- dodawaj schema/Alembic/dependencies,
- twórz globalnej tabeli biblioteki normalizacji,
- aktywuj automatycznie normalization/alias rules w runtime,
- hardkoduj wariantów CX80 w resolverze production,
- wykonuj fuzzy merge PRODUCT,
- zastępuj znanego product code wartością NULL,
- wykonuj raw SQL dla danych biznesowych,
- modyfikuj istniejących PRODUCT poza P023/P037 i wyłącznie przez zatwierdzony correction workflow.

---

# 7. EXPECTED CHANGE SURFACE

Preferuj minimalne rozszerzenie istniejącej orkiestracji TASK-057.

Dopuszczalne:

```text
scripts/task058_resolve_review_identity.py
lub minimalne rozszerzenie scripts/task057_stage1_batch_import.py

docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_REVIEW_DECISIONS.json
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md
app/application/                        # tylko jeśli konieczne dla bezpiecznej orkiestracji correction+revision
tests/integration/test_task058_review_identity.py
docs/task_reports/TASK-058_REPORT.md
```

Chronione bez osobnej decyzji:

```text
app/domain/
migrations/
Core docs
SDS parser / extractor
SDS-ALIAS production activation
```

---

# 8. VALIDATION — LEVEL 2

Przed operator writes:

1. focused tests decyzji batchowych M1/M2/M3 bez hardcode w resolverze,
2. isolated PostgreSQL + temporary SDS root:
   - manufacturer variant → existing manufacturer,
   - ordinary REVIEW item → CREATE,
   - P028-like explicit new PRODUCT despite similar existing product,
   - P023/P037-like existing PRODUCT with known code + manufacturer correction,
   - exact existing source → correction-only lub SKIP zgodnie z planem,
   - new SDS revision → CURRENT/ARCHIVED,
   - same revision/date + different hash → no write / review conflict,
   - injected failure → rollback + filesystem compensation,
3. related regression TASK-051-R1, TASK-053/056/057,
4. `git diff --check`,
5. operator `alembic current = b7d4a1f03962 (head)`,
6. operator `alembic check` PASS.

Nie wykonuj nowej migracji.

---

# 9. ACCEPTANCE CRITERIA

| ID | Kryterium |
|---|---|
| A1 | Wszystkie 11 wcześniejszych `REVIEW_IDENTITY` są ponownie sklasyfikowane na podstawie jawnych decyzji Architekta. |
| A2 | M1/M2/M3 wskazują wyłącznie istniejący `CX80 Polska` i nie tworzą nowego MANUFACTURER. |
| A3 | Zatwierdzone warianty są utrwalone w batch decision artifact jako human-approved, ale nie są globalnie ACTIVE w runtime library. |
| A4 | P023 wykorzystuje istniejący PRODUCT, zachowuje nazwę/kod, a manufacturer correction jest audytowany jako CORRECTION. |
| A5 | P037 wykorzystuje istniejący PRODUCT, zachowuje kod `CX80 XBRAKE CLEANER`, a manufacturer correction jest audytowany jako CORRECTION. |
| A6 | P028 tworzy odrębny PRODUCT `XBRAKE CLEANER liquid` z code=NULL pod `CX80 Polska`. |
| A7 | Znany kod istniejącego P023/P037 nigdy nie jest nadpisany NULL z JSON. |
| A8 | Exact istniejący SDS/PDF jest pomijany; nowa jednoznaczna rewizja używa lifecycle CURRENT→ARCHIVED. |
| A9 | Konflikt tego samego issue_date/revision z innym SHA nie jest automatycznie rozstrzygany. |
| A10 | Pozostałe 8 pozycji po manufacturer approval nie tworzą duplikatu, jeśli revalidation wykryje dokładnie istniejący PRODUCT/SDS. |
| A11 | Wszystkie nowe Stage 1 PRODUCT zachowują admin fields NULL i brak Safety/Components/BHP. |
| A12 | Brak nowych MANUFACTURER poza istniejącym `CX80 Polska`; brak zmian Core/schema/Alembic/dependencies. |
| A13 | Raport końcowy pokazuje dla każdego z 11: decyzję, action, product_id, sds_id oraz ewentualny powód pozostawienia REVIEW. |
| A14 | Nie uruchomiono Paczki2 ani żadnego kolejnego sprintu/tasku. |

---

# 10. REPORT / FINAL STATE

Raport:

```text
docs/task_reports/TASK-058_REPORT.md
```

Musi zawierać:

1. tabelę 11 pozycji: previous status → approved decision → final action → result,
2. listę nowych PRODUCT/SDS,
3. listę PRODUCT identity corrections wraz z `PRODUCT_IDENTITY_CHANGE` / `CORRECTION` evidence,
4. liczbę nowych PDF i weryfikację SHA,
5. finalne liczniki BATCH-001_CX po TASK-058:
   - imported/registered,
   - exact/skipped,
   - duplicate source,
   - excluded non-SDS,
   - remaining REVIEW,
6. potwierdzenie 0 Safety / 0 Components / 0 BHP dla nowych Stage 1 records,
7. potwierdzenie, że zatwierdzone warianty producenta zapisano jako batch decisions, a nie hardcoded production normalization.

Po wykonaniu:

```text
STOP po BATCH-001_CX.
Nie uruchamiaj Paczki2.
Nie rozpoczynaj biblioteki normalizacji ani Stage 2 bez osobnego Tasku.
```
