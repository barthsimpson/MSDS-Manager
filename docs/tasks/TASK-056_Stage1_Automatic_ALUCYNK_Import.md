# TASK-056 — Stage 1 automatic Evidence import + ALUCYNK one-item operator test

**Projekt:** MSDS Manager  
**Task:** TASK-056  
**Status:** READY / AUTHORIZED FOR EXECUTION  
**Tryb:** INTEGRATION  
**Walidacja:** LEVEL 2 + migration cycle + operator preflight  
**Cel:** jeden automatyczny, kontrolowany import ALUCYNK bez przechodzenia formularza ręcznych potwierdzeń.

---

## 1. Decyzja Architekta

Stage 1 służy wyłącznie do rejestracji:

```text
PRODUCT identity
+ MANUFACTURER resolution
+ SDS metadata
+ verified source PDF
```

Sekcje 2/3/11, `SAFETY_PROFILE` i `SDS_COMPONENT` są osobnym późniejszym sprintem.

Dla PRODUCT tworzonego w Stage 1:

```text
use_description = NULL allowed
use_restriction = NULL allowed
```

Znaczenie `NULL`:

```text
administrative data not yet provided
```

Nie wolno używać placeholderów typu:

```text
"Do uzupełnienia"
"Brak danych"
"N/A"
```

jako wartości biznesowych.

Ścieżka ręczna / pojedynczy SDS może nadal wymagać tych pól w formularzu.

Przed finalną decyzją BHP produkt musi mieć:

```text
complete Safety enrichment
+ non-NULL use_description
+ non-NULL use_restriction
```

Nie zmieniaj semantyki `CURRENT / ARCHIVED`.

---

## 2. Wynik Tasku

Po wykonaniu TASK-056 istnieje kontrolowany mechanizm:

```text
prepared Evidence JSON
+ batch manifest
+ verified source PDF
+ approved batch decision
        ↓
automatic Stage 1 plan
        ↓
revalidation
        ↓
one controlled commit
        ↓
PRODUCT + SDS + PDF in MSDS Manager
```

Pierwszy rzeczywisty przypadek:

```text
B001-P001_DOC-001.json
→ ALUCYNK
→ existing MANUFACTURER: CX80 Polska
→ manufacturer_product_code = NULL
→ issue_date = 2023-01-23
→ revision = 2.0
→ Safety enrichment pending
```

Bez ręcznego przechodzenia formularza `Dodaj SDS`.

---

## 3. Źródła obowiązujące

Minimalnie odczytaj:

- TASK-055 i TASK-055_REPORT,
- TASK-055-R1 i poprawiony TASK-055-R1_REPORT,
- TASK-052 / TASK-053 / TASK-054 / TASK-054-R1 reports,
- BATCH-001_CX manifest, Golden Decisions i JSON ALUCYNK,
- BDR-005 / Stage 1 revision,
- aktualny CORE-001 Stage 1 revision,
- TDR-013 Stage 1 revision,
- TDR-006,
- GOV-001 / GOV-002,
- root AGENTS.md.

Nie wykonuj repo-wide discovery bez potrzeby.

---

## 4. Zakres A — Stage 1 administrative NULL alignment

### 4.1 Domain / DTO / Application

Dopuść dla PRODUCT utworzonego przez Stage 1:

```text
use_description: str | None
use_restriction: str | None
```

Nie zmieniaj znaczenia tych pól dla istniejących produktów.

### 4.2 Persistence

Jeżeli kolumny są nadal `NOT NULL`:

- przygotuj jedną kontrolowaną migrację Alembic,
- zmień wyłącznie te dwie kolumny na nullable,
- bez backfill,
- bez placeholderów,
- istniejące wartości pozostają niezmienione.

Wykonaj:

```text
review migration
upgrade
focused PostgreSQL test
downgrade
re-upgrade
alembic check
```

### 4.3 Manual workflow regression

Dotychczasowe ręczne `Dodaj SDS` może nadal wymagać podania obu pól przed swoim commit path.

Nie upraszczaj istniejącego pojedynczego UX w tym Tasku.

### 4.4 BHP gate

Finalna decyzja BHP ma być zablokowana, jeżeli CURRENT SDS:

- nie ma kompletnego Safety enrichment, lub
- PRODUCT ma `use_description IS NULL`, lub
- PRODUCT ma `use_restriction IS NULL`.

Nie dodawaj nowego statusu PRODUCT/SDS.

---

## 5. Zakres B — automatic one-item Stage 1 runner

Dodaj minimalny kontrolowany runner / application entrypoint dla przygotowanego Evidence JSON.

Preferuj istniejący wzorzec CLI/scripts repo; nie twórz nowego frameworka.

Runner ma przyjąć jeden wskazany Evidence JSON i wykonać istniejące mechanizmy:

```text
validate Evidence JSON
→ resolve source PDF from controlled batch context
→ verify exact SHA-256
→ identity resolver
→ apply approved human/batch decision
→ create Approved Stage 1 Plan
→ revalidate DB + JSON + PDF
→ controlled commit via existing Application use cases
```

Zakazane:

```text
raw SQL
JSON → SQL shortcut
filesystem write from script outside Application/Infrastructure
filename-only PDF acceptance
fuzzy automatic manufacturer LINK
silent CREATE/LINK
```

---

## 6. Batch-local approved decision — not normalization library

Dla BATCH-001_CX utwórz lub wykorzystaj minimalny jawny artefakt decyzji wejściowej dla automatu.

Ma reprezentować zatwierdzoną decyzję Architekta:

```text
canonical manufacturer from Evidence: CX80 POLSKA
→ existing DB manufacturer: CX80 Polska
```

Decyzja batchowa:

- może wskazywać istniejący rekord przez exact DB name i po resolution zamrożony `manufacturer_id`,
- przed commit wymaga dokładnie jednego zgodnego rekordu,
- zmiana / brak / wieloznaczność → STOP,
- NIE jest biblioteką normalizacji,
- NIE tworzy `ACTIVE` aliasu,
- NIE ma wpływu na inne batch'e.

CX80 może występować w danych decyzji / fixture, ale nie jako hardcode w production resolver logic.

---

## 7. ALUCYNK — oczekiwany automatyczny plan

Dla:

```text
docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json
```

oczekiwane:

```text
JSON VALID
logical SDS DOC-001
source PDF ALUCYNK 23.01.2023 rew. 2.0.pdf
SHA-256 exact match
product_name ALUCYNK
manufacturer canonical CX80 POLSKA
manufacturer DB LINK CX80 Polska
manufacturer_product_code NULL
issue_date 2023-01-23
revision 2.0
PRODUCT action CREATE
use_description NULL
use_restriction NULL
Safety enrichment pending
```

Jeżeli istnieje już PRODUCT `ALUCYNK` dla wybranego producenta:

```text
STOP / STALE_RESOLUTION
```

Nie twórz duplikatu i nie zgaduj rewizji/linku.

---

## 8. Walidacja przed realnym operatorem

Najpierw wykonaj na izolowanym PostgreSQL + temporary SDS root:

1. Stage 1 CREATE z NULL obu pól administracyjnych.
2. PDF exact SHA.
3. Manufacturer LINK do istniejącego rekordu.
4. Product code NULL.
5. SDS CURRENT.
6. PDF dostępny przez kartę produktu/read path.
7. Brak SAFETY_PROFILE i SDS_COMPONENT.
8. BHP decision blocked.
9. Existing manual workflow still requires its manual fields.
10. rollback/compensation przy DB/FS failure.
11. stale DB decision blocks commit.

Focused + related regression zgodnie z GOV-002.

---

## 9. Realny operator ALUCYNK — granica wykonania

Po PASS walidacji Codex wykonuje **PRECHECK na operator DB i source PDF**, ale nie zapisuje automatycznie, jeśli wystąpi jakakolwiek rozbieżność.

Realny zapis jest dozwolony tylko gdy jednocześnie:

```text
exact JSON fingerprint matches
exact PDF SHA matches
manufacturer CX80 Polska resolves uniquely
ALUCYNK PRODUCT does not already exist for that manufacturer
migration is at head / alembic check clean
operator precheck reports exactly one intended CREATE PRODUCT + one SDS
```

Jeżeli wszystkie warunki są PASS, TASK-056 jest autoryzowany do wykonania **jednego** realnego Stage 1 COMMIT dla ALUCYNK.

Zakres realnego zapisu:

```text
max 0/1 MANUFACTURER write  # oczekiwane 0, bo LINK
exactly 1 PRODUCT create
exactly 1 SDS create
exactly 1 controlled PDF import
0 BHP decisions
0 Safety profiles
0 SDS components
```

Po tym natychmiast STOP.

Nie importuj żadnego kolejnego JSON z BATCH-001_CX.

---

## 10. Kryteria akceptacji

| ID | Kryterium |
|---|---|
| A1 | Stage 1 nie wymaga `use_description` / `use_restriction` i nie zapisuje placeholderów. |
| A2 | Manual single-SDS workflow zachowuje swoje obecne wymagania. |
| A3 | BHP jest blokowane przy brakującym Safety lub brakujących obu danych administracyjnych. |
| A4 | Runner działa dla jednego Evidence JSON przez Application, bez raw SQL. |
| A5 | PDF jest zaakceptowany wyłącznie po exact SHA-256. |
| A6 | Batch decision LINKuje `CX80 POLSKA` do dokładnie jednego `CX80 Polska`; brak hardcode w resolverze. |
| A7 | ALUCYNK plan = CREATE PRODUCT, code NULL, issue date 2023-01-23, revision 2.0. |
| A8 | Izolowany commit zapisuje PRODUCT + SDS + PDF i nic z Safety/BHP. |
| A9 | Operator precheck wykrywa duplikat/stale i wtedy nie zapisuje nic. |
| A10 | Realny operator commit, jeśli wykonany, dotyczy wyłącznie ALUCYNK i po nim Task STOP. |
| A11 | Existing operator data poza tym jednym rekordem pozostają niezmienione. |
| A12 | Migration cycle + Alembic check PASS, jeśli nullable schema change była potrzebna. |

---

## 11. Poza zakresem

NIE implementuj teraz:

- batch import całych 35/50 SDS,
- Safety extraction Sekcji 2/3/11,
- SDS_COMPONENT,
- biblioteki normalizacji producentów,
- `CANDIDATE → ACTIVE`,
- SDS-ALIAS governance,
- automatycznego uczenia,
- fuzzy merge producentów,
- OCR / LLM runtime,
- nowych statusów SDS/PRODUCT,
- importu kolejnych pozycji po ALUCYNK.

---

## 12. Biblioteka normalizacji — utrwalona decyzja przyszłego sprintu

Dla pojedynczo dodawanego nowego SDS docelowy mechanizm ma działać:

```text
new RAW manufacturer variant
→ proposed canonical/existing manufacturer
→ explicit human accept/reject
→ current SDS decision applied
→ normalization candidate recorded
→ human-approved governance + regression
→ ACTIVE rule for future SDS
```

TASK-056 nie implementuje tego mechanizmu. Nie zgub tej decyzji w raporcie / NEXT.

---

## 13. STOP conditions

STOP / BLOCKED, jeżeli:

- nullable `use_description/use_restriction` wymaga szerszej zmiany Core niż opisana,
- migration wpływa na inne dane/constraints,
- manual workflow nie da się zachować,
- BHP gate nie może odróżnić incomplete Stage 1,
- source PDF SHA nie zgadza się,
- manufacturer nie rozwiązuje się jednoznacznie,
- ALUCYNK już istnieje,
- operator DB ma drift / Alembic problem,
- commit wymaga raw SQL lub obejścia Application,
- konieczny jest batch import lub normalization library.

Nie obchodź blokady.

---

## 14. Raport

Utwórz:

```text
docs/task_reports/TASK-056_REPORT.md
```

Raport ma zawierać:

- changed files,
- schema/migration impact,
- NULL semantics,
- BHP gate,
- runner entrypoint,
- isolated validation results,
- operator precheck,
- exact ALUCYNK expected/actual mapping,
- operator DB writes count,
- operator SDS_ROOT_PATH writes count,
- jeśli commit wykonany: `product_id`, `sds_id`, manufacturer ID/name, PDF relative path i potwierdzenie CURRENT,
- deviations/risks,
- NEXT = Cerberus review; bez importu kolejnej pozycji.

