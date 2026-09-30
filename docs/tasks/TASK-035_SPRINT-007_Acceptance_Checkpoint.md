# TASK-035 — SPRINT-007 Acceptance / Checkpoint

**Projekt:** MSDS Manager  
**Task ID:** TASK-035  
**Sprint:** SPRINT-007 — DATA-01 — Słownik jednostek miary  
**MODE:** ACCEPTANCE  
**VALIDATION LEVEL:** LEVEL 3  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  
**Status:** AUTHORIZED FOR EXECUTION  

---

## 1. GOAL

Udowodnić pełną spójność `DATA-01 — UNIT_OF_MEASURE` oraz brak regresji istniejącego MVP po wykonaniu:

```text
TASK-033 — DONE / ACCEPTED
TASK-034 — DONE / ACCEPTED
```

TASK-035 jest końcowym checkpointem SPRINT-007.

Nie jest Taskiem implementacyjnym.

Jego celem jest:

```text
zweryfikować
→ wykazać integralność
→ wykazać brak regresji
→ przygotować pełny raport acceptance
```

---

## 2. AUTHORITATIVE CONTEXT

Obowiązują wyłącznie aktualne zatwierdzone źródła:

1. `SPRINT-007_DATA-01_Slownik_jednostek_v1.0-approved.md`
2. `TDR-005_UNIT_OF_MEASURE_v1.0-approved.md`
3. `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved.md`
4. `CORE-001_MSDS_Manager_v1.2-approved_BDR006.md`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
6. `GOV-001 — Zasady współpracy — Człowiek / Cerberus / Codex`
7. `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED.md`
8. `TASK-034_REPORT.md`
9. root `AGENTS.md`

Nie wykonuj repo-wide rediscovery tylko po to, aby odtworzyć stan już znany z powyższych źródeł.

Rozszerzaj analizę wyłącznie wtedy, gdy realny wynik walidacji tego wymaga.

---

## 3. BASELINE

Stan wejściowy:

```text
TASK-033 — DONE / ACCEPTED
TASK-034 — DONE / ACCEPTED
```

Alembic head po TASK-033:

```text
a97e2cb7f31d
```

TASK-034 potwierdził:

- wybór `ACTIVE UNIT_OF_MEASURE`,
- walidację Application,
- integrację `AssignProductUsageLocation`,
- integrację `UpdateProductUsageLocation`,
- Product details,
- supervisory display,
- formularze Streamlit add/edit,
- zachowanie `unit_id` w historii,
- semantykę `0 != NULL`,
- brak free-text dla jednostek,
- brak UUID jednostki w normalnym UI,
- brak zmiany schema w TASK-034,
- brak conversion engine,
- brak legacy mapping.

---

## 4. EXPECTED CHANGE SURFACE

Domyślnie:

```text
production code changes: NONE
schema changes: NONE
migrations: NONE
Core changes: NONE
```

Dopuszczalne:

- testy acceptance,
- lokalne artefakty testowe,
- raport `TASK-035_REPORT.md`.

Jeżeli acceptance ujawni realny production defect:

```text
STOP
→ opisz defect
→ wskaż dowód
→ nie naprawiaj automatycznie
```

---

## 5. DO

### 5.1. Full regression

Uruchom pełny `pytest` całego projektu.

Raport musi jawnie podać:

```text
passed
failed
errors
skipped
```

Każdy `FAIL` lub `ERROR` musi zostać sklasyfikowany.

Nie wykonuj opportunistic fix problemów spoza zakresu.

---

### 5.2. SAWarning

Uruchom kontrolę SQLAlchemy z `SAWarning` traktowanym jako błąd.

Oczekiwane:

```text
SAWarning: NONE
```

---

### 5.3. Alembic current

Potwierdź:

```text
current = head
expected head = a97e2cb7f31d
```

---

### 5.4. Alembic check

Uruchom:

```text
alembic check
```

Oczekiwane:

```text
no new upgrade operations
schema drift = NONE
```

---

### 5.5. Upgrade / downgrade / re-upgrade

Na izolowanym środowisku testowym potwierdź poprawność ścieżki:

```text
upgrade
→ downgrade
→ re-upgrade
```

Nie używaj operator DB do destrukcyjnej walidacji.

---

### 5.6. Schema / integrity — UNIT_OF_MEASURE

Potwierdź:

```text
unit_of_measure
├── unit_id
├── code
├── name
├── category
└── status
```

Sprawdź co najmniej:

- tabela istnieje,
- `unit_id` jest stabilną referencją,
- `code` jest UNIQUE,
- `category` ograniczone do:
  - `VOLUME`,
  - `MASS`,
  - `COUNT`,
- `status` ograniczony do:
  - `ACTIVE`,
  - `INACTIVE`.

Seed musi zawierać:

```text
l
ml
kg
g
szt
```

Wszystkie rekordy seed:

```text
status = ACTIVE
```

---

### 5.7. PRODUCT_USAGE_LOCATION

Potwierdź model:

```text
peak_quantity_value
+
peak_quantity_unit_id FK → UNIT_OF_MEASURE

monthly_consumption_value
+
monthly_consumption_unit_id FK → UNIT_OF_MEASURE
```

Reguły:

#### MAX

```text
value wymagane
unit wymagane
```

#### Monthly

```text
NULL value → NULL unit
0 jest wartością biznesową
0 wymaga jednostki
value != NULL → unit wymagane
```

---

### 5.8. ACTIVE / INACTIVE

Potwierdź:

#### ACTIVE

- może być użyte w nowym przypisaniu,
- może być użyte przy edycji.

#### INACTIVE

- nie może być nowym wyborem,
- nie może zostać użyte jako nowa/zmieniona wartość,
- istniejące i historyczne referencje pozostają czytelne,
- jednostka nie jest fizycznie usuwana.

---

### 5.9. History

Potwierdź mechanizm TDR-004:

```text
current state change
+
history snapshot
=
ONE TRANSACTION
```

Dla `PRODUCT_USAGE_LOCATION_HISTORY` snapshot musi zachowywać co najmniej:

- `peak_quantity_value`,
- `peak_quantity_unit_id`,
- `monthly_consumption_value`,
- `monthly_consumption_unit_id`,
- `changed_at`.

Potwierdź szczególnie:

```text
zmiana samej jednostki
→ tworzy nowy snapshot historii
```

Potwierdź rollback:

```text
history write failure
→ current state MUST NOT commit
```

---

### 5.10. Application validation

Potwierdź, że reguła jednostek nie istnieje wyłącznie w Streamlit.

`AssignProductUsageLocation` oraz `UpdateProductUsageLocation` muszą kontrolowanie odrzucać:

- brak wymaganej jednostki MAX,
- unknown `unit_id`,
- `INACTIVE unit_id`,
- monthly value bez jednostki.

---

### 5.11. Streamlit UI

Potwierdź:

- brak free-text dla jednostki MAX,
- brak free-text dla jednostki monthly,
- wybór pochodzi z `ACTIVE UNIT_OF_MEASURE`,
- użytkownik widzi `code`,
- UUID `unit_id` nie jest elementem użytkowym normalnego workflow,
- formularz add działa,
- formularz edit działa,
- monthly może pozostać puste,
- monthly `= 0` działa z wybraną jednostką.

---

### 5.12. Product details

Potwierdź prezentację kodów jednostek.

Techniczne `unit_id` może być dostępne dla logiki edycji, ale nie może być prezentowane operatorowi jako normalna informacja użytkowa.

---

### 5.13. Supervisory display

Potwierdź:

- widoczne są kody jednostek,
- UUID jednostek nie są wyświetlane,
- istniejąca semantyka widoku nadzorczego nie została zmieniona.

---

### 5.14. Operator data safety

Sprawdź stan danych operatora przed i po acceptance.

Nie usuwaj automatycznie danych operatora.

Jeżeli walidacja wymaga danych testowych:

```text
izolowane środowisko
lub
transakcja rollback
```

Raport ma jawnie potwierdzić:

```text
operator data preserved = YES / NO
```

Jeżeli `NO`:

```text
STOP / BLOCKED
```

---

### 5.15. No legacy import

Potwierdź, że nie powstało:

- mapowanie starego Excela,
- heurystyczne mapowanie tekstowych jednostek,
- automatyczna normalizacja legacy.

---

### 5.16. No conversion engine

Potwierdź brak:

- `conversion_factor`,
- `base_unit`,
- `base_unit_id`,
- tabeli konwersji,
- `kg ↔ g`,
- `l ↔ ml`,
- density conversion,
- automatycznej normalizacji do jednostki bazowej.

---

### 5.17. Dependencies

Potwierdź, czy TASK-033/TASK-034 wprowadziły nowe dependencies poza zatwierdzonym zakresem.

Oczekiwane:

```text
new dependencies = NONE
```

---

### 5.18. Cleanup

Po testach:

- usuń wyłącznie artefakty testowe utworzone przez acceptance,
- nie usuwaj danych operatora,
- potwierdź brak orphan/test records wynikających z TASK-035.

---

## 6. DEFINITION OF DONE

SPRINT-007 może zostać zamknięty tylko wtedy, gdy wszystkie poniższe kryteria są `PASS`:

| # | Kryterium | Oczekiwany wynik |
|---|---|---|
| 1 | `unit_of_measure` istnieje | PASS |
| 2 | seed `l/ml/kg/g/szt` istnieje | PASS |
| 3 | `code` jest unikalny | PASS |
| 4 | category ograniczone do VOLUME/MASS/COUNT | PASS |
| 5 | status ograniczony do ACTIVE/INACTIVE | PASS |
| 6 | MAX wskazuje jednostkę przez kontrolowaną referencję | PASS |
| 7 | monthly wskazuje jednostkę przez kontrolowaną referencję | PASS |
| 8 | monthly NULL → unit NULL | PASS |
| 9 | `0 != NULL` | PASS |
| 10 | INACTIVE nie może być nowym wyborem | PASS |
| 11 | INACTIVE pozostaje czytelne historycznie | PASS |
| 12 | zmiana jednostki tworzy snapshot historii | PASS |
| 13 | current + history są atomowe | PASS |
| 14 | UI nie ma free-text dla jednostki | PASS |
| 15 | UI pokazuje kod jednostki | PASS |
| 16 | UUID jednostki nie jest użytkowym elementem UI | PASS |
| 17 | brak automatycznej konwersji | PASS |
| 18 | brak importu legacy | PASS |
| 19 | pełna regresja przechodzi | PASS |
| 20 | Alembic check bez driftu | PASS |

---

## 7. DO NOT

Nie:

- zmieniaj Core,
- zmieniaj BDR/TDR,
- dodawaj nowej migracji bez ujawnionego realnego defektu,
- rozwijaj schema,
- implementuj conversion engine,
- twórz legacy mappera,
- implementuj `Analizy`,
- implementuj `PATCH-009`,
- zmieniaj parsera SDS,
- refaktoruj niezwiązanych modułów,
- wykonuj DOC cleanup,
- naprawiaj problemów spoza zakresu bez osobnej decyzji.

---

## 8. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

- pełna regresja ujawni realny production defect,
- schema różni się od zatwierdzonego modelu,
- Alembic nie jest na oczekiwanym head,
- `alembic check` wykazuje drift,
- current/history nie są atomowe,
- dane operatora byłyby zagrożone,
- potrzebna byłaby zmiana Core,
- potrzebna byłaby nowa decyzja biznesowa,
- konieczna byłaby nowa migracja naprawcza,
- test wymaga zgadywania zamiast kontrolowanej interpretacji.

Nie stosuj opportunistic fix.

---

## 9. VALIDATION

**LEVEL 3 — ACCEPTANCE / CHECKPOINT**

Wymagane minimum:

```text
full pytest
E2E
SAWarning
Alembic current
Alembic check
schema/integrity
upgrade/downgrade/re-upgrade
history
UI unit selection
supervisory display
operator data safety
cleanup
```

---

## 10. REPORT

**FULL REPORT**

Przygotuj:

```text
TASK-035_REPORT.md
```

Raport musi zawierać:

### STATUS

```text
PASS / BLOCKED / FAILED
```

### BASELINE

- TASK-033,
- TASK-034,
- Alembic head.

### FULL REGRESSION

- passed,
- failed,
- errors,
- skipped.

### VALIDATION

- E2E,
- SAWarning,
- Alembic current,
- Alembic check,
- schema drift,
- upgrade/downgrade/re-upgrade,
- history,
- UI,
- supervisory,
- operator data safety,
- cleanup.

### DEFINITION OF DONE

Tabela punktów `1–20`:

```text
PASS / FAIL + krótki dowód
```

### SCOPE

Potwierdź jawnie:

```text
Core changed?
schema changed?
migration added?
dependencies added?
conversion engine?
legacy mapping?
```

### RISKS / DEVIATIONS

Wymień wszystkie odstępstwa, pominięte testy, problemy środowiskowe i ograniczenia dowodowe.

### FINAL CONCLUSION

```text
READY / NOT READY TO CLOSE SPRINT-007
```

### NEXT

```text
OCZEKUJĘ NA JAWNE POLECENIE.
```

---

## 11. AUTHORIZATION

```text
WYKONAJ TASK-035.
```

Task został jawnie autoryzowany przez Architekta Operacyjnego.
