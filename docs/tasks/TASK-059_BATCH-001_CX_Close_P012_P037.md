# TASK-059 — BATCH-001_CX: domknięcie P012 i P037

**Projekt:** MSDS Manager  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**STATUS:** READY / AUTHORIZED  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus  

## 1. Cel

Domknąć dwie ostatnie pozycje `REVIEW` w `BATCH-001_CX` bez tworzenia duplikatów i bez naruszenia lifecycle SDS:

- `B001-P012` — `CLEANER PROF`,
- `B001-P037` — `XBRAKE CLEANER`.

Po wykonaniu Tasku `BATCH-001_CX` ma nie zawierać żadnej pozycji `REVIEW`.

## 2. Authoritative context

Minimalnie odczytaj przed wykonaniem:

- `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
- `BDR-003_MSDS_Manager` — lifecycle `CURRENT / ARCHIVED`, brak automatycznego rozstrzygania duplikatów
- `BDR-007_Kontrolowany_import_SDS_v1.0-approved.md`
- aktualny `CORE-001`
- `TASK-058_REPORT.md`
- `TASK-058_AUDIT_REPORT.md`
- `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md`
- manifest i Evidence JSON dla P012 oraz P037
- aktualny stan operator DB i `SDS_ROOT_PATH`

## 3. Stan wejściowy potwierdzony

### P012

Evidence JSON:

```text
B001-P012_DOC-001.json
product_name = CLEANER PROF
manufacturer => CX80 Polska
```

Istniejący PRODUCT:

```text
product_name = Cleaner prof
manufacturer = CX80 Polska
```

Audit TASK-058 potwierdził:

- P012 nie utworzył nowego PRODUCT/SDS,
- istniejący `Cleaner prof` ma jeden `CURRENT` SDS,
- fizyczny PDF P012 jest bajtowo tym samym PDF co istniejący SDS,
- różnica nazwy dotyczy wyłącznie wielkości liter.

### P037

Evidence JSON:

```text
B001-P037_DOC-001.json
product_name = XBRAKE CLEANER
issue_date = 2023-01-24
revision = 3.0
manufacturer => CX80 Polska
```

Istniejący PRODUCT:

```text
product_id = 833c0080c0a34bd1a40f5b2be18b82a6
product_name = XBRAKE CLEANER
manufacturer = Cx80
manufacturer_product_code = CX80 XBRAKE CLEANER
```

Audit TASK-058 potwierdził:

- PRODUCT ma 3 wcześniejsze SDS,
- dokładnie jeden SDS jest `CURRENT`,
- CURRENT ma datę `2026-09-01`,
- P037 ma inny PDF niż istniejące SDS,
- P037 nie został zapisany ani nie zmienił lifecycle.

## 4. Zatwierdzone decyzje Architekta

### D1 — P012

P012 i istniejący `Cleaner prof` są tym samym PRODUCT.

Różnica:

```text
CLEANER PROF
vs
Cleaner prof
```

nie tworzy nowego PRODUCT w tym konkretnym przypadku, ponieważ:

- producent jest ten sam,
- fizyczny PDF jest identyczny,
- SHA-256 źródła jest identyczny z istniejącym SDS.

Działanie:

```text
LINK existing PRODUCT
+ SKIP_EXACT_EXISTING SDS/PDF
```

Nie twórz nowego PRODUCT, SDS ani kopii PDF.

Zapisz tę decyzję w artefakcie decyzji batchowej jako jawne human-approved rozstrzygnięcie P012. Nie twórz globalnej reguły case-insensitive dla nazw PRODUCT.

### D2 — P037 — tożsamość PRODUCT

P037 należy do istniejącego PRODUCT:

```text
XBRAKE CLEANER
product_id = 833c0080c0a34bd1a40f5b2be18b82a6
```

Zachowaj:

```text
product_name = XBRAKE CLEANER
manufacturer_product_code = CX80 XBRAKE CLEANER
product_id = bez zmian
```

Skoryguj wyłącznie producenta:

```text
Cx80
→ CX80 Polska
```

przez istniejący kontrolowany mechanizm `CorrectProductIdentity` / równoważny zaakceptowany use case, z `PRODUCT_IDENTITY_CHANGE = CORRECTION` w tej samej transakcji.

### D3 — P037 — źródłowy PDF z 2023 r.

P037 jest historycznym źródłem SDS i NIE może zastąpić bieżącego `CURRENT` z `2026-09-01`.

Dla tego batcha zatwierdza się:

```text
SKIP_HISTORICAL_SOURCE
```

Znaczenie:

- nie twórz nowego SDS,
- nie kopiuj P037 do `SDS_ROOT_PATH/imported/`,
- nie zmieniaj żadnego SDS `CURRENT/ARCHIVED`,
- nie twórz nowej decyzji BHP,
- zachowaj źródłowy PDF w katalogu batcha i jego SHA w raporcie jako ślad źródłowy,
- odnotuj jawnie, że karta z 2023 r. została pominięta, ponieważ system posiada późniejszy CURRENT i celem Stage 1 batcha nie jest retrospektywne uzupełnianie pełnej historii SDS.

Nie implementuj w tym Tasku nowego mechanizmu `register historical SDS as ARCHIVED`.

## 5. Wymagane wykonanie

### 5.1. Read-only preflight

Przed jakimkolwiek zapisem ponownie potwierdź:

#### P012

- exact Evidence JSON,
- exact source PDF,
- SHA manifest = SHA JSON = SHA rzeczywistych bajtów,
- istniejący `Cleaner prof`,
- jego producent = `CX80 Polska`,
- istniejący SDS wskazuje dokładnie ten sam SHA/PDF,
- brak nowego P012 PRODUCT/SDS po TASK-058.

Jeżeli którykolwiek warunek nie jest spełniony:

```text
STOP / BLOCKED
```

#### P037

- exact Evidence JSON,
- exact source PDF i SHA,
- dokładnie wskazany istniejący PRODUCT `833c0080...`,
- nazwa = `XBRAKE CLEANER`,
- znany kod = `CX80 XBRAKE CLEANER`,
- producent przed korektą nadal = `Cx80`, chyba że został już poprawnie skorygowany przez wcześniejszą autoryzowaną operację,
- dokładnie jeden `CURRENT` SDS,
- CURRENT pozostaje datowany `2026-09-01`,
- P037 źródło ma `2023-01-24 / 3.0`,
- brak nowego SDS/PDF P037 po TASK-058.

Jeżeli stan różni się istotnie od powyższego:

```text
STOP / BLOCKED
```

### 5.2. P012

Po preflight:

- nie wykonuj zapisu biznesowego,
- oznacz wynik jako `SKIP_EXACT_EXISTING`,
- utrwal human-approved batch decision:
  `CLEANER PROF` → existing PRODUCT `Cleaner prof` tylko dla P012,
- nie dodawaj globalnej normalizacji nazwy PRODUCT.

### 5.3. P037

Po preflight:

1. wykonaj wyłącznie korektę producenta istniejącego PRODUCT `Cx80 → CX80 Polska`,
2. zachowaj nazwę i kod produktu,
3. utwórz dokładnie jeden audit `PRODUCT_IDENTITY_CHANGE = CORRECTION`,
4. nie twórz SDS/PDF z P037,
5. nie zmieniaj CURRENT/ARCHIVED,
6. oznacz P037 jako `SKIP_HISTORICAL_SOURCE` w decyzji i raporcie batcha.

Jeżeli producent został już poprawnie skorygowany przed wykonaniem Tasku, nie twórz drugiej korekty; potraktuj ją jako `ALREADY_CORRECT` i jedynie potwierdź audit/provenance.

## 6. Domknięcie raportu BATCH-001_CX

Zaktualizuj raport batcha tak, aby po TASK-059:

```text
Remaining REVIEW = 0
```

Końcowy bilans 35 logical SDS ma jednoznacznie rozliczać każdą pozycję jako:

- registered/imported,
- exact existing/skipped,
- duplicate source,
- historical source skipped,
- excluded non-SDS.

P012 i P037 nie mogą pozostać w kategorii `REVIEW`.

## 7. DO NOT

Nie wolno:

- tworzyć nowego PRODUCT dla P012,
- tworzyć nowego PRODUCT dla P037,
- zmieniać kodu `CX80 XBRAKE CLEANER`,
- ustawiać P037 PDF jako `CURRENT`,
- archiwizować obecnego CURRENT P037,
- tworzyć historycznego SDS P037 w tym Tasku,
- kopiować P037 PDF do `imported/`,
- tworzyć nowych MANUFACTURER,
- zmieniać Core,
- zmieniać schema lub Alembic,
- implementować globalnej biblioteki normalizacji,
- implementować case-insensitive PRODUCT resolver globally,
- uruchamiać Paczki2,
- rozpoczynać Stage 2.

## 8. Walidacja

### Focused / integration

Potwierdź co najmniej:

1. P012 exact PDF + ten sam manufacturer + zaakceptowany human link → `SKIP_EXACT_EXISTING`, 0 zapisów PRODUCT/SDS/PDF.
2. P012 podobna nazwa bez exact PDF → brak automatycznego LINK.
3. P037 correction-only zmienia wyłącznie `manufacturer_id` i zapisuje audit.
4. Błąd audytu P037 → rollback korekty.
5. P037 source nie tworzy SDS/PDF i nie zmienia CURRENT.
6. Po P037 dokładnie jeden SDS pozostaje `CURRENT` i jest to ten sam rekord co przed Taskiem.
7. Brak nowych SAFETY_PROFILE / SDS_COMPONENT / BHP_DECISION.
8. Brak nowych MANUFACTURER.
9. `alembic current` / `heads` / `check` bez zmian.
10. `git diff --check` dla zmian Tasku PASS.

### Operator verification

Po wykonaniu odczytowo potwierdź:

- P012: 0 nowych PRODUCT/SDS/PDF,
- P037: 0 nowych SDS/PDF,
- P037: producent = `CX80 Polska`, nazwa/kod bez zmian,
- dokładnie jeden nowy `PRODUCT_IDENTITY_CHANGE` dla P037, chyba że korekta była już wcześniej wykonana,
- CURRENT P037 nadal `2026-09-01`,
- `Remaining REVIEW = 0`,
- brak orphan PDF przypisywalnego TASK-059.

## 9. STOP CONDITIONS

STOP bez zapisu lub przed kolejnym zapisem, jeżeli:

- P012 PDF nie jest exact tym samym PDF co istniejący SDS,
- P012 existing PRODUCT nie jest jednoznaczny,
- P037 PRODUCT / kod / producent / lifecycle różni się od preflight,
- więcej niż jeden P037 SDS jest `CURRENT`,
- korekta producenta wymaga zmiany nazwy lub kodu,
- wymagany jest nowy schema/Core/lifecycle mechanism,
- implementacja wymaga ręcznego SQL poza istniejącymi repo/use case,
- nie można zagwarantować atomicity korekta + audit,
- pojawi się potrzeba importu P037 jako ARCHIVED — to wymaga osobnej decyzji/Tasku.

## 10. Raport

Zapisz:

```text
docs/task_reports/TASK-059_REPORT.md
```

Raport ma zawierać:

- preflight P012/P037,
- dokładną decyzję i wynik każdej pozycji,
- wszystkie operator writes,
- ID korekty/audytu P037,
- potwierdzenie braku zapisów P012 i braku SDS/PDF P037,
- lifecycle P037 przed/po,
- końcowy bilans `BATCH-001_CX`,
- wyniki testów,
- Alembic current/heads/check,
- orphan scan dla zakresu TASK-059,
- odstępstwa/ryzyka.

## 11. Authorization

Architekt Operacyjny jawnie polecił kontynuację i rozstrzygnięcie P012 oraz P037.

```text
TASK-059: AUTHORIZED
```

## 12. Zakończenie

Po wykonaniu:

```text
STOP
```

Nie uruchamiaj Paczki2, Stage 2 ani biblioteki normalizacji.
