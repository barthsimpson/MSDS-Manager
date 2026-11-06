# TASK-058-AUDIT — Read-only integrity check after interrupted execution

**Projekt:** MSDS Manager  
**Powiązanie:** TASK-058 — BATCH-001_CX Review Identity  
**MODE:** READ-ONLY AUDIT  
**STATUS:** READY / AUTHORIZED  
**CEL:** potwierdzić, że uśpienie laptopa / utrata sieci w trakcie TASK-058 nie pozostawiły częściowego commitu, orphan PDF ani niespójności DB ↔ SDS_ROOT_PATH.

## Zasada nadrzędna

To zadanie jest wyłącznie diagnostyczne.

```text
READ ONLY
NO FIX
NO COMMIT
NO DELETE
NO RETRY TASK-058
NO BUSINESS DATA WRITE
```

Jeżeli wykryjesz jakąkolwiek rozbieżność: **STOP / REPORT ONLY**.

## Źródła

1. `docs/tasks/TASK-058_BATCH-001_CX_Resolve_Review_Identity.md`
2. `docs/task_reports/TASK-058_REPORT.md`
3. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md`
4. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_REVIEW_DECISIONS.json`
5. operator PostgreSQL
6. operator `SDS_ROOT_PATH`
7. źródłowy batch PDF przekazany przez runtime `--source-root` — tylko do porównania SHA, bez kopiowania.

## Oczekiwany stan z raportu TASK-058

Po TASK-058 raport deklaruje:

```text
MANUFACTURER                  5
PRODUCT                      35
SDS                          37
PRODUCT_HISTORY              41

TASK-058 writes:
+8 PRODUCT
+8 SDS
+8 PRODUCT_HISTORY
+1 UPDATE existing PRODUCT (P023)
+1 PRODUCT_IDENTITY_CHANGE (P023, CORRECTION)
+8 PDF in SDS_ROOT_PATH
+0 MANUFACTURER
+0 SAFETY_PROFILE
+0 SDS_COMPONENT
+0 BHP_DECISION
```

Pozostałe REVIEW:

```text
P012 — CLEANER PROF — no write
P037 — XBRAKE CLEANER — no write
```

## Kontrole

### A. Stan DB

Read-only potwierdź:

1. liczby tabel zgodne z raportem: 5 MANUFACTURER, 35 PRODUCT, 37 SDS, 41 PRODUCT_HISTORY;
2. dokładnie jeden `PRODUCT_IDENTITY_CHANGE` utworzony przez TASK-058 dla P023:
   - `change_kind = CORRECTION`,
   - old manufacturer = legacy `CX80`,
   - new manufacturer = `CX80 Polska`,
   - nazwa i kod produktu bez zmiany;
3. P023:
   - ten sam `product_id` co przed korektą,
   - manufacturer = `CX80 Polska`,
   - kod `0300-F0DT-500F-GJ25`,
   - istniejący SDS pozostaje CURRENT;
4. P012: brak nowego PRODUCT/SDS oraz brak identity correction wynikającej z TASK-058;
5. P037: brak nowego SDS i brak identity correction wynikającej z TASK-058;
6. P028 istnieje jako odrębny PRODUCT `XBRAKE CLEANER liquid`, code `NULL`, manufacturer `CX80 Polska`;
7. osiem CREATE z TASK-058 ma po jednym PRODUCT, jednym SDS CURRENT i jednym PRODUCT_HISTORY;
8. dla każdego PRODUCT istnieje maksymalnie jeden SDS `CURRENT`;
9. brak nowych SAFETY_PROFILE / SDS_COMPONENT / BHP_DECISION dla rekordów TASK-058.

### B. DB ↔ filesystem

Dla 8 SDS utworzonych przez TASK-058:

1. odczytaj `relative_path` z DB;
2. potwierdź, że plik istnieje pod `SDS_ROOT_PATH`;
3. potwierdź PDF signature;
4. przelicz SHA-256 pliku docelowego;
5. porównaj z expected SHA w manifest/JSON;
6. każdy z 8 plików ma być powiązany z dokładnie jednym rekordem SDS.

### C. Orphan / partial-write scan

Read-only przeskanuj `SDS_ROOT_PATH` i porównaj z `SDS.relative_path`.

Raportuj osobno:

```text
FILES_WITHOUT_DB_REFERENCE
DB_REFERENCES_WITHOUT_FILE
DUPLICATE_DB_RELATIVE_PATH
```

Nie usuwaj niczego.

Jeżeli istnieją wcześniejsze orphan files niezwiązane z TASK-058, oznacz je jako `PRE-EXISTING / PROVENANCE UNKNOWN`, a nie jako awarię TASK-058.

Dodatkowo dla 11 źródeł TASK-058 sprawdź, czy nie istnieje w `SDS_ROOT_PATH` dodatkowy niezarejestrowany plik o tym samym SHA poza oczekiwanymi 8 zapisami / wcześniej istniejącymi kontrolowanymi SDS.

### D. Lifecycle / transakcje

Potwierdź:

1. brak PRODUCT z więcej niż jednym CURRENT SDS;
2. brak SDS z `product_id` nieistniejącego PRODUCT;
3. brak PRODUCT_HISTORY wskazującego nieistniejący PRODUCT;
4. P023 correction audit i stan bieżący są spójne;
5. P012/P037 zachowały stan sprzed TASK-058;
6. brak częściowego correction bez odpowiadającego audytu.

### E. Stan migracji

Read-only:

```text
alembic current
alembic heads
alembic check
```

Oczekiwane:

```text
current = b7d4a1f03962 (head)
single head
alembic check = PASS
```

Nie wykonuj upgrade/downgrade.

## Kryteria wyniku

### PASS

Tylko jeśli:

- DB odpowiada raportowi,
- wszystkie 8 PDF istnieją i mają exact SHA,
- brak orphan/partial write przypisywalnego TASK-058,
- P012/P037 są nietknięte,
- P023 correction jest kompletna i audytowalna,
- lifecycle CURRENT jest spójny,
- Alembic jest czysty.

### REVIEW REQUIRED

Jeżeli wykryto rozbieżność, ale nie można jednoznacznie przypisać jej TASK-058.

### FAIL / STOP

Jeżeli wykryto m.in.:

- PDF bez rekordu DB powstały w TASK-058,
- rekord SDS bez PDF,
- częściowy correction bez audytu,
- więcej niż jeden CURRENT dla produktu,
- dodatkowy PRODUCT/SDS dla P012 lub P037,
- hash docelowego PDF różny od źródła.

## Raport

Zapisz:

```text
docs/task_reports/TASK-058_AUDIT_REPORT.md
```

Raport ma zawierać:

1. `STATUS: PASS / REVIEW REQUIRED / FAIL`,
2. tabelę kontroli A–E,
3. liczniki DB,
4. tabelę 8 PDF: SDS ID / relative_path / expected SHA / actual SHA / result,
5. wynik orphan scan,
6. stan P023 / P012 / P037,
7. Alembic current/heads/check,
8. jednoznaczne potwierdzenie `NO WRITES PERFORMED`.

Po raporcie:

```text
STOP.
Nie wznawiaj TASK-058.
Nie naprawiaj wykrytych rozbieżności.
Nie uruchamiaj Paczki2.
```
