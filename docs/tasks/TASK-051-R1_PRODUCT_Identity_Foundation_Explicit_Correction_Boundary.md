# TASK-051-R1 — PRODUCT Identity Foundation + Explicit Identity Correction Boundary

**Projekt:** MSDS Manager  
**Task ID:** TASK-051-R1  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** SHORT / STANDARD INTEGRATION  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI  

---

## 1. GOAL

Wdrożyć techniczny fundament zatwierdzonego modelu tożsamości PRODUCT wynikającego z:

```text
BDR-009 v1.0-approved
CORE-001 v1.6-approved
TDR-013 v1.0-approved
```

Zakres TASK-051:

```text
manufacturer_product_code
NOT NULL → NULLABLE

+
PRODUCT_IDENTITY_CHANGE
dla:
- CODE_COMPLETION
- CORRECTION

+
spójne Domain / ORM / Application foundation
+
kontrolowana migracja Alembic
+
testy integralności
```

TASK-051-R1 NIE implementuje jeszcze:

```text
Evidence JSON mapper
JSON validator
CREATE / LINK resolver
DRY RUN
ALUCYNK JSON flow
pełnego JSON → DB commit
```

Te elementy należą do kolejnych Tasków TDR-013.

---

## 2. AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie niezbędny kontekst:

1. `CORE-001_MSDS_Manager_v1.6-approved_BDR009.md`
2. `BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved.md`
3. `TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved.md`
4. `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved`
5. `TDR-001`
6. `TDR-003`
7. `GOV-001_Zasady_wspolpracy_v1.0-approved`
8. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
9. root `AGENTS.md`
10. `TASK-050_IMPACT_ANALYSIS_REPORT.md` — wyłącznie jako diagnostyczny kontekst stanu repo
11. `TASK-051_REPORT.md` — BLOCKED report; źródło ujawnionego konfliktu UX/API

Nie wykonuj repo-wide discovery bez potrzeby.

W razie konfliktu między stanem repo a zatwierdzonym BDR/Core/TDR:

```text
STOP / BLOCKED
```

Nie zgaduj.

---

## 3. KNOWN STARTING POINTS

Rozpocznij od bezpośrednich miejsc wskazanych przez TASK-050:

### Domain / DTO

```text
app/domain/models/catalog.py

app/application/dto/products.py
app/application/dto/sds.py
app/application/dto/supervisory.py
app/application/dto/bhp_decisions.py
```

Sprawdź wyłącznie rzeczywiście powiązane DTO zawierające:

```text
manufacturer_product_code
```

### Application

```text
UpdateProductIdentity
```

oraz bezpośrednio powiązany repository / port odpowiedzialny za zmianę identity.

Nie rozszerzaj jeszcze `AcceptSds` o JSON / resolver.

### Infrastructure

```text
app/infrastructure/db/models/catalog.py
```

oraz:

```text
Product repository
identity update persistence
migrations/versions/
```

### Tests

Znane punkty startowe z TASK-050:

```text
tests/unit/test_orm_metadata.py
tests/unit/test_update_product_identity.py
tests/integration/test_patch007_product_identity.py
```

Jeżeli nazwy plików różnią się od aktualnego repo, znajdź bezpośrednie odpowiedniki i nie rozszerzaj eksploracji poza wymagany zakres.

---

## 4. EXPECTED CHANGE SURFACE

Oczekiwane obszary zmian:

```text
app/domain/
app/application/
app/infrastructure/db/
migrations/versions/
tests/unit/
tests/integration/
```

UI:

```text
YES — minimalny zakres wymagany do usunięcia BLOCKED z TASK-051
```

Dozwolone wyłącznie:

```text
- zastąpienie ogólnej etykiety „Edytuj dane produktu”
  jawną ścieżką „Korekta danych identyfikacyjnych”
- dodanie osobnej ścieżki „Uzupełnij kod producenta”
- jawne potwierdzenie korekty przed zapisem
```

Nie wykonuj redesignu ekranu ani innych zmian UX.

Evidence JSON / SDS extraction:

```text
NO
```

---

# 5. DO

## 5.1. PRODUCT — nullable manufacturer_product_code

Zmień model tak, aby:

```text
manufacturer_product_code: str | None
```

było poprawnym stanem PRODUCT.

Semantyka:

```text
None
= brak zatwierdzonej wartości kodu

None
≠ ""
None
≠ wildcard
None
≠ placeholder
```

Nie normalizuj pustego stringa do sztucznej wartości.

Jeżeli istniejący kontrakt wejściowy dopuszcza `""`, walidacja powinna:

```text
"" / whitespace-only
→ traktować jako brak wartości / None
```

tylko jeżeli jest to zgodne z istniejącymi wzorcami walidacji projektu.

Jeżeli wymagałoby to nowej decyzji semantycznej:

```text
STOP / BLOCKED
```

Nie twórz placeholderów.

---

## 5.2. ORM / PostgreSQL

Zmień:

```text
products.manufacturer_product_code
NOT NULL
→ NULLABLE
```

Bez:

```text
backfill
placeholder
default sztuczny
```

Istniejące niepuste wartości muszą pozostać bez zmian.

Nie dodawaj automatycznie:

```text
UNIQUE
INDEX
```

dla trójki identity ani samego kodu, ponieważ TDR-013 nie zatwierdza takiego constraintu.

---

## 5.3. PRODUCT_IDENTITY_CHANGE — Domain

Dodaj minimalny model domenowy odpowiadający zatwierdzonemu TDR-013:

```text
PRODUCT_IDENTITY_CHANGE
├── change_id
├── product_id
├── change_kind
├── old_product_name
├── new_product_name
├── old_manufacturer_product_code
├── new_manufacturer_product_code
├── old_manufacturer_id
├── new_manufacturer_id
└── changed_at
```

Dozwolone `change_kind`:

```text
CODE_COMPLETION
CORRECTION
```

Nie dodawaj:

```text
changed_by
reason
notes
source
generic audit metadata
```

bez osobnej decyzji.

---

## 5.4. PRODUCT_IDENTITY_CHANGE — ORM / schema

Dodaj osobną tabelę:

```text
product_identity_changes
```

Nazwa może zostać technicznie dostosowana wyłącznie wtedy, gdy istniejąca konwencja repo jednoznacznie wymaga innego pluralization/naming.

Minimalna struktura zgodna z TDR-013:

```text
change_id
product_id
change_kind
old_product_name
new_product_name
old_manufacturer_product_code
new_manufacturer_product_code
old_manufacturer_id
new_manufacturer_id
changed_at
```

Wymagania:

```text
PK dla change_id
FK product_id → PRODUCT
CHECK change_kind IN ('CODE_COMPLETION', 'CORRECTION')
old/new manufacturer_product_code → NULL allowed
changed_at → NOT NULL
```

Typy:

```text
product_id
manufacturer_id
change_id
```

muszą być zgodne z rzeczywistymi fizycznymi typami istniejącego modelu.

Nie migruj istniejących ID do nowych typów.

---

## 5.5. CODE_COMPLETION

Zaimplementuj kontrolowaną operację:

```text
manufacturer_product_code:
NULL → known value
```

dla tego samego:

```text
product_id
```

Wymagane zachowanie:

```text
PRODUCT update
+
PRODUCT_IDENTITY_CHANGE(change_kind=CODE_COMPLETION)
→ jedna transakcja
```

Warunki:

```text
old code = NULL
new code = non-empty
product_id unchanged
manufacturer unchanged
product_name unchanged
```

Jeżeli produkt posiada już kod:

```text
CODE_COMPLETION
→ reject
```

Nie traktuj:

```text
known A → known B
```

jako CODE_COMPLETION.

---

## 5.6. Jawna granica Application po TDR-013 v1.1

Zgodnie z zatwierdzonym `TDR-013 v1.1-approved` implementacja ma rozdzielić dwa przypadki użycia:

```text
CompleteManufacturerProductCode
CorrectProductIdentity
```

Nie pozostawiaj ogólnej publicznej semantyki:

```text
UpdateProductIdentity
= dowolna edycja identity
```

### 5.6.1. CompleteManufacturerProductCode

Operacja:

```text
manufacturer_product_code:
NULL → known value
```

Wymagania:

```text
ten sam product_id
product_name bez zmiany
manufacturer_id bez zmiany
change_kind = CODE_COMPLETION
```

Jeżeli kod jest już znany:

```text
REJECT
```

### 5.6.2. CorrectProductIdentity

Operacja służy wyłącznie do jawnej korekty błędnie zarejestrowanych danych:

```text
product_name
manufacturer_product_code
manufacturer_id
```

Wymagania:

```text
ten sam product_id
change_kind = CORRECTION
pełny old/new identity snapshot
```

Use case nie może reprezentować zwykłej zmiany produktu.

### 5.6.3. Istniejący UpdateProductIdentity

Preferowane rozwiązanie:

```text
zastąpić publiczne użycie
→ CompleteManufacturerProductCode
→ CorrectProductIdentity
```

Jeżeli zachowanie starej klasy jako wewnętrznego wrappera jest konieczne dla minimalnej kompatybilności testów, może ona pozostać tylko wtedy, gdy:

```text
nie jest publiczną ogólną ścieżką edycji
nie omija jawnej semantyki CODE_COMPLETION / CORRECTION
```

Nie klasyfikuj automatycznie wszystkich zmian jako `CORRECTION`.

---

## 5.7. Audytowalność

Dla każdej udanej:

```text
CODE_COMPLETION
lub
CORRECTION
```

musi istnieć dokładnie jeden wpis identity history.

Historia musi zapisać pełny snapshot:

```text
old identity
new identity
change_kind
changed_at
```

Nie zapisuj wyłącznie diffu jednego pola.

Błąd zapisu historii:

```text
ROLLBACK PRODUCT update
```

Błąd PRODUCT update:

```text
brak history entry
```

---

## 5.8. Existing PRODUCT_HISTORY

Nie rozszerzaj istniejącej:

```text
PRODUCT_HISTORY
```

o identity fields w TASK-051.

TDR-013 zatwierdza osobny mechanizm:

```text
PRODUCT_IDENTITY_CHANGE
```

Nie twórz duplikatu tej samej zmiany w obu historiach, chyba że istniejący workflow PRODUCT_HISTORY jest obowiązkowo wywoływany przez ten sam use case zgodnie z zatwierdzonym Core.

Jeżeli wystąpi konflikt:

```text
STOP / BLOCKED
```

i opisz go.

---

## 5.9. Read models / DTO

Dostosuj tylko te DTO/read models, które muszą poprawnie reprezentować:

```text
manufacturer_product_code = None
```

W szczególności typy nie mogą wymuszać `str`, jeśli odczyt z DB może zwrócić `NULL`.

Prezentacji UI nie implementuj w tym Tasku.

Jeżeli sortowanie Python porównuje:

```text
None <-> str
```

i dotyczy bezpośrednio zmienianego DTO/repository, popraw minimalnie tak, aby foundation nie wprowadzał runtime error.

Nie przebudowuj widoku nadzorczego.

---

# 6. ALEMBIC

Utwórz jedną kontrolowaną migrację realizującą wyłącznie zatwierdzony foundation scope:

```text
1. manufacturer_product_code → nullable
2. product_identity_changes
```

Nie łącz z innymi zmianami schema.

Wymagany standard migracji:

```text
review migration
→ upgrade
→ validate
→ downgrade
→ re-upgrade
→ alembic current
→ alembic check
```

Po re-upgrade:

```text
current = single head
schema drift = NONE
```

Jeżeli istnieją multiple heads przed wykonaniem Tasku:

```text
STOP / BLOCKED
```

Nie twórz merge migration bez decyzji.

---

# 7. DATA MIGRATION

Istniejące PRODUCT:

```text
manufacturer_product_code != NULL
```

pozostają niezmienione.

Nie wykonuj:

```text
NULL backfill
placeholder generation
deduplication
manufacturer merge
identity correction istniejących rekordów
```

Nowa tabela historii:

```text
startuje pusta
```

Nie rekonstruuj historii wstecz.

---

# 8. DO NOT

Nie implementuj w TASK-051:

```text
SDS-JSON validator
Evidence JSON mapper
JSON parser
DRY RUN
Manufacturer Resolver
Product Resolver
CREATE / LINK candidate logic
Golden Decisions runtime
ALUCYNK flow
Import plan
Approved Import Plan
AcceptSds JSON integration
AddSdsRevision JSON integration
PDF import changes
CURRENT / ARCHIVED changes
SAFETY_PROFILE changes
SDS_COMPONENT changes
SDS-ALIAS changes
SDS-JSON changes
fuzzy matching
MANUFACTURER merge
new dependencies
generic audit log
users / changed_by
```

Nie zapisuj danych BATCH-001 do operator DB.

---

# 9. VALIDATION — LEVEL 2

## 9.1. Focused Domain / Application

Potwierdź co najmniej:

```text
PRODUCT code None accepted
existing non-null code preserved
CODE_COMPLETION NULL → code PASS
CODE_COMPLETION code → other code REJECT
CORRECTION writes identity history
identity update + history = atomic
history failure → rollback
```

## 9.2. ORM / schema

Potwierdź:

```text
manufacturer_product_code nullable = TRUE

product_identity_changes:
- PK
- FK
- CHECK change_kind
- nullable old/new code
- required changed_at
```

## 9.3. PostgreSQL integration

Na izolowanej bazie:

```text
CREATE PRODUCT with NULL code
→ PASS

NULL → code completion
→ same product_id
→ 1 identity change
→ PASS

controlled correction
→ same product_id
→ CORRECTION history
→ PASS

transaction rollback
→ PASS
```

## 9.4. Migration

Wykonaj:

```text
upgrade
downgrade
re-upgrade
alembic current
alembic check
```

Wymagane:

```text
single head
No new upgrade operations detected
```

## 9.5. Related regression

Uruchom tylko bezpośrednio powiązane testy:

```text
PRODUCT identity
PATCH-007
SDS acceptance foundation
ORM metadata
history transaction
```

Nie uruchamiaj pełnego repo pytest w TASK-051.

---

# 10. DATA SAFETY

Testy DB:

```text
isolated PostgreSQL / istniejący test harness
```

Operator DB:

```text
schema migration allowed only after standard checks
existing PRODUCT codes preserved
no data cleanup
no test fixture writes
```

Jeżeli migracja na operator DB ujawnia niespodziewany konflikt:

```text
STOP
→ bez automatycznego cleanup
```

---

# 11. STOP CONDITIONS

Po minimalnej diagnostyce wykonaj:

```text
STOP / BLOCKED
```

jeżeli:

1. `CORE-001 v1.6-approved`, BDR-009 i TDR-013 są wzajemnie niespójne,
2. rzeczywisty schema nie odpowiada stanowi z TASK-050 w sposób wymagający dodatkowej decyzji,
3. istnieją multiple Alembic heads,
4. nullable code wymaga placeholdera / backfillu,
5. implementacja wymaga UNIQUE/index niewynikającego z TDR-013,
6. typy `product_id` / `manufacturer_id` wymagałyby migracji,
7. istniejącego publicznego `UpdateProductIdentity` nie da się bezpiecznie zastąpić / ograniczyć zgodnie z TDR-013 v1.1 bez rozszerzenia poza zatwierdzony minimalny zakres,
8. poprawna audytowalność wymaga `changed_by` / users / nowego workflow uprawnień,
9. poprawna transakcyjność wymaga przebudowy całego repository/UoW,
10. TASK zaczyna wymagać JSON resolvera / DRY RUN,
11. potrzebna jest nowa dependency,
12. wymagany jest repo-wide refactor,
13. trzeba zgadywać znaczenie istniejącego PATCH-007 lub historii PRODUCT.

Nie wykonuj opportunistic fix.

---

# 12. REPORT

Utwórz:

```text
docs/task_reports/TASK-051-R1_REPORT.md
```

Format:

```text
# TASK-051-R1 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- Domain
- Application
- ORM
- Repository
- Migration
- Tests

IMPLEMENTED:
- manufacturer_product_code nullable
- PRODUCT_IDENTITY_CHANGE
- CODE_COMPLETION
- CORRECTION audit
- atomic identity update + history

SCHEMA:
- previous Alembic head:
- new Alembic head:
- nullable change:
- new table:
- constraints:

VALIDATION:
- focused tests:
- PostgreSQL integration:
- upgrade:
- downgrade:
- re-upgrade:
- alembic current:
- alembic check:
- related regression:
- SAWarning:

DATA SAFETY:
- existing product codes preserved:
- operator data preserved:
- synthetic backfill:
- test residue:

SCOPE:
- JSON mapper: NO
- resolver: NO
- DRY RUN: NO
- PDF workflow change: NO
- CURRENT/ARCHIVED change: NO
- new dependencies:

RISKS / DEVIATIONS:
- NONE albo lista

NEXT:
- READY FOR CERBERUS REVIEW
- albo BLOCKED
```

---

# 13. ACCEPTANCE CRITERIA

TASK-051-R1 jest DONE tylko jeżeli:

1. PRODUCT może posiadać `manufacturer_product_code = NULL`.
2. Istniejące kody nie są zmienione.
3. Brak kodu nie wymaga placeholdera.
4. `NULL → known code` zachowuje ten sam `product_id`.
5. `CODE_COMPLETION` zapisuje historię.
6. Kontrolowana korekta identity zapisuje `CORRECTION`.
7. UPDATE + identity history są atomowe.
8. Nie powstał generyczny audit log.
9. Nie wdrożono JSON resolvera / DRY RUN.
10. Migracja upgrade/downgrade/re-upgrade przechodzi.
11. Alembic ma jeden head.
12. Operator data pozostają zachowane.
13. Powiązana regresja przechodzi.
14. `CompleteManufacturerProductCode` obsługuje wyłącznie `NULL → code`.
15. `CorrectProductIdentity` jest jawną kontrolowaną korektą, nie zwykłą edycją.
16. UI rozdziela „Uzupełnij kod producenta” od „Korekta danych identyfikacyjnych”.
17. Rzeczywista zmiana identity nie może przejść przez ścieżkę korekty bez świadomego potwierdzenia semantyki korekty.

---

# 14. AUTHORIZATION

```text
TASK-051-R1
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Start dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-051-R1.
```

Po wykonaniu:

```text
STOP
→ TASK-051-R1_REPORT
→ CERBERUS REVIEW
→ ARCHITEKT DECISION
```

Nie rozpoczynaj kolejnego Tasku TDR-013 automatycznie.
