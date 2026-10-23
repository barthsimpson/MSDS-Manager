# TASK-054-R1 — Automatyczne powiązanie Evidence JSON ↔ źródłowy PDF

**Projekt:** MSDS Manager  
**Task:** TASK-054-R1  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1 + targeted integration  
**REPORT:** SHORT  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI

---

## 1. Problem i wynik

TASK-054 technicznie wymaga obecnie, aby operator ręcznie wskazał:

```text
Evidence JSON
+
PDF SDS
```

mimo że Evidence JSON powstał z konkretnego PDF i zawiera metadane źródła oraz SHA-256.

Dla BATCH-001_CX relacja JSON ↔ PDF została już ustalona podczas bootstrapu. Każdy poprawny JSON wskazuje źródłowy PDF, a manifest zachowuje SHA-256.

Ręczne ponowne wybieranie tego samego PDF jest zbędną pracą i nie może być standardową ścieżką dla przygotowanych batchy.

### Oczekiwany wynik

Standardowy przepływ dla Evidence JSON:

```text
wybór Evidence JSON
→ odczyt source filename + source SHA-256
→ automatyczne odnalezienie źródłowego PDF w kontrolowanym kontekście batcha
→ sprawdzenie SHA-256
→ status: PDF POWIĄZANY / ZWERYFIKOWANY
→ DRY RUN
```

Ręczne wskazanie PDF pozostaje wyłącznie fallbackiem, gdy automatyczne powiązanie nie jest możliwe.

Nie zmieniaj logiki T052/T053 ani zasad Controlled Commit.

---

## 2. Authoritative context

Minimalnie:

1. `TASK-054_Human_Review_Commit_UI_ALUCYNK.md`
2. `TASK-054_REPORT.md`
3. `TASK-052_REPORT.md`
4. `TASK-053_REPORT.md`
5. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_MANIFEST.json`
6. `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_REPORT.md`
7. `SDS-JSON-001 v1.0-approved`
8. `TDR-006_Kontrolowany_import_SDS_v1.0-approved`
9. `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved`
10. `UI-GUIDE-001_Standard_UI_Dashboard_Layout_v1.0-approved`
11. `GOV-001 v1.0-approved`
12. `GOV-002 v1.0-approved`
13. root `AGENTS.md`

BATCH-001 ma już zweryfikowaną relację source PDF ↔ JSON przez filename/SHA-256. Nie rekonstruuj jej heurystycznie.

---

## 3. Known starting points

Sprawdź przede wszystkim:

```text
app/presentation/streamlit/evidence_import.py
app/presentation/streamlit/add_sds.py
app/presentation/streamlit/composition.py

app/application/dto/approved_import.py
app/application/use_cases/controlled_evidence_import.py
app/application/use_cases/plan_evidence_json_import.py

istniejące filesystem ports/adapters używane przez SDS import

tests/unit/test_task054_evidence_ui.py
tests/integration/test_task054_operator_flow.py

docs/sds_bootstrap/BATCH-001_CX/
```

Nie wykonuj repo-wide discovery bez konkretnej potrzeby.

---

## 4. Do

### 4.1. Automatyczne source binding

Po wyborze Evidence JSON odczytaj z kontraktu istniejące dane źródłowe, w szczególności:

```text
source PDF filename
source PDF SHA-256
```

Jeżeli JSON należy do kontrolowanego batcha i jego source PDF jest dostępny w znanym kontekście źródłowym batcha:

```text
znajdź kandydat PDF
→ oblicz SHA-256
→ porównaj z JSON/manifest
```

Powiązanie automatyczne jest poprawne wyłącznie wtedy, gdy:

```text
exact expected SHA-256 match
```

Nazwa pliku jest pomocą lokalizacyjną, ale nie jest samodzielnym dowodem zgodności.

### 4.2. Bez zgadywania lokalizacji

Użyj wyłącznie istniejącego, kontrolowanego kontekstu źródłowego batcha / manifestu / obecnego mechanizmu filesystem, jeśli repo lub konfiguracja już go dostarcza.

Jeżeli obecny projekt NIE posiada deterministycznej informacji, skąd runtime ma odczytać źródłowy PDF batcha:

```text
STOP / BLOCKED
```

W raporcie wskaż dokładnie brakujący kontrakt lokalizacji.

NIE dodawaj samodzielnie:

```text
nowego root path w .env
nowego staging repository
nowego DMS
hardcoded C:\...\Paczka1 cx
```

bez osobnej decyzji Architekta.

### 4.3. UI — standard case

Gdy PDF zostanie znaleziony automatycznie, UI ma pokazać jeden zwarty blok, np. semantycznie:

```text
Evidence JSON
B001-P001_DOC-001.json

Źródłowy PDF
✓ ALUCYNK 23.01.2023 rew. 2.0.pdf
✓ SHA-256 zgodny
```

Operator NIE wybiera wtedy PDF drugi raz.

`Uruchom DRY RUN` dotyczy całego zestawu źródłowego i ma znajdować się wizualnie pod wspólnym blokiem, nie pod samą kolumną JSON.

### 4.4. UI — fallback

Jeżeli PDF:

```text
nie został odnaleziony
lub
nie jest dostępny w kontrolowanym kontekście
```

pokaż jawny fallback:

```text
Nie odnaleziono źródłowego PDF.
[ Wskaż źródłowy PDF ]
```

Po ręcznym wskazaniu:

```text
PDF signature validation
+
SHA-256 == expected SHA-256
```

Dopiero wtedy PDF może zostać zaakceptowany jako source binding.

Jeżeli hash nie pasuje:

```text
PDF_MISMATCH
→ brak DRY RUN / brak ApprovedImportPlan / brak COMMIT
```

### 4.5. Session safety

Zmiana:

```text
JSON
PDF fallback
source binding
```

musi unieważnić istniejący plan dokładnie tak, jak obecnie T054 unieważnia plan po zmianie źródeł.

Nie osłabiaj zabezpieczeń `SOURCE_CHANGED` / `PDF_CHANGED` z TASK-053.

---

## 5. Do not

Nie implementuj w R1:

- batch COMMIT,
- `Import all`,
- automatycznego importu wielu JSON,
- zmian `SDS-ALIAS-001`,
- mechanizmu CANDIDATE → ACTIVE,
- nowych reguł extractora,
- OCR,
- nowych pól Core,
- zmian Domain,
- ORM/schema/Alembic,
- nowych tabel,
- nowych zależności,
- realnego COMMIT ALUCYNK,
- realnego zapisu do operator DB,
- realnego zapisu do operator `SDS_ROOT_PATH`.

Nie zmieniaj toru `Dodanie ręczne PDF` poza konieczną regresją wspólnego kodu.

---

## 6. Expected change surface

Oczekiwane:

```text
app/presentation/streamlit/evidence_import.py
app/presentation/streamlit/composition.py

app/application/...          # tylko jeśli binding należy do Application
app/infrastructure/filesystem/... # tylko jeśli potrzebny istniejący adapter/resolver

tests/unit/test_task054_evidence_ui.py
tests/integration/test_task054_operator_flow.py
```

Opcjonalnie minimalny nowy port / DTO dla source binding, jeśli jest potrzebny do zachowania TDR-003.

Nie przenoś logiki filesystem do Streamlit.

---

## 7. Validation

### Focused unit / AppTest

Potwierdź co najmniej:

1. JSON + dostępny exact PDF → auto-bound.
2. Auto-bound PDF → brak obowiązkowego drugiego uploadu.
3. Filename zgodny, hash błędny → brak binding.
4. PDF nieznaleziony → fallback manualny widoczny.
5. Manual fallback + właściwy hash → binding PASS.
6. Manual fallback + zły hash → `PDF_MISMATCH` i brak dalszej ścieżki.
7. Zmiana JSON unieważnia source binding i ApprovedImportPlan.
8. Zmiana fallback PDF unieważnia ApprovedImportPlan.
9. `Uruchom DRY RUN` jest związany z kompletnym source binding.
10. Dotychczasowy manual `Dodanie ręczne` nie ma regresji.

### Targeted integration

Na izolowanym źródle testowym odtwórz:

```text
manifest
+ Evidence JSON
+ source PDF
```

i potwierdź automatyczne powiązanie przez SHA-256.

Bez operator DB write i bez operator `SDS_ROOT_PATH` write.

### Physical UX

Po implementacji wymagany ponowny screenshot:

```text
1920×1080
zoom 100%
Dodaj SDS → Import z Evidence JSON
```

Sprawdzić:

- brak dublowania wyboru PDF w standard case,
- czytelny status powiązania PDF,
- fallback tylko gdy potrzebny,
- pozycję `Uruchom DRY RUN`,
- brak zbędnego scrollowania.

---

## 8. Acceptance criteria

| ID | Kryterium | Dowód |
|---|---|---|
| A1 | Dla dostępnego source PDF operator wskazuje tylko Evidence JSON | AppTest + Physical UX |
| A2 | Powiązanie PDF wymaga exact SHA-256 | unit/integration |
| A3 | Filename nie wystarcza do akceptacji | test mismatch |
| A4 | Brak auto-resolve pokazuje manual fallback | AppTest |
| A5 | Zły fallback PDF blokuje dalszy workflow | AppTest |
| A6 | T052/T053 source-change protections pozostają aktywne | regression |
| A7 | Brak zmian Core/Domain/schema/Alembic | diff/report |
| A8 | Operator DB writes = 0 | report |
| A9 | Operator SDS_ROOT_PATH writes = 0 | report |
| A10 | Brak batch importu i realnego ALUCYNK COMMIT | report |
| A11 | Physical UX zgodny z UI-GUIDE-001 | screenshot review |

---

## 9. STOP conditions

STOP / BLOCKED, jeśli:

1. nie istnieje kontrolowany sposób ustalenia lokalizacji source PDF batcha,
2. poprawne rozwiązanie wymaga nowej konfiguracji root/staging bez zatwierdzonej decyzji,
3. trzeba skanować arbitralnie cały dysk,
4. trzeba zgadywać PDF tylko po nazwie,
5. wymagany jest Core/Domain/schema change,
6. wymagany jest nowy framework/dependency,
7. trzeba osłabić source fingerprint / stale-plan safety,
8. poprawka wymaga rozpoczęcia batch importu.

W stanie BLOCKED opisz dokładnie brak i zakończ R1 bez obejścia.

---

## 10. Report

Utwórz:

```text
docs/task_reports/TASK-054-R1_REPORT.md
```

Krótko:

```text
STATUS
CHANGED
SOURCE RESOLUTION
UI
VALIDATION
OPERATOR SAFETY
SCOPE
DEVIATIONS / BLOCKERS
NEXT
```

W szczególności raport ma odpowiedzieć:

```text
Skąd dokładnie runtime bierze source PDF?
Jak potwierdza SHA-256?
Kiedy pokazuje manual fallback?
Czy operator DB/SDS_ROOT_PATH pozostały nietknięte?
```

---

## 11. Authorization

```text
TASK-054-R1
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Start dopiero po jawnym:

```text
Wykonaj TASK-054-R1.
```

Po wykonaniu:

```text
STOP
→ TASK-054-R1_REPORT
→ CERBERUS REVIEW
→ PHYSICAL UX REVIEW
→ ARCHITEKT DECISION
```

Nie rozpoczynaj automatycznie Batch Readiness / SDS-ALIAS ani Batch Import.
