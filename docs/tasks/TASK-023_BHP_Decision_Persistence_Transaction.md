# TASK-023 — BHP Decision Persistence & Transaction

**Projekt:** MSDS Manager  
**Task ID:** TASK-023  
**Sprint:** SPRINT-004 — Decyzja BHP i dowód decyzji  
**Status:** READY  
**Typ:** Infrastructure / Persistence / Transaction / PostgreSQL Integration  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Zaimplementować rzeczywistą persystencję decyzji BHP i dowodu decyzji w PostgreSQL, zgodnie z kontraktami TASK-022 i zatwierdzonym Core.

Operacja ma działać jako jedna atomowa transakcja:

```text
RegisterBhpDecisionInput
        ↓
walidacja PRODUCT / SDS
        ↓
walidacja dowodu
        ↓
old BHP_DECISION CURRENT → SUPERSEDED
        ↓
DECISION_EVIDENCE
        ↓
new BHP_DECISION CURRENT
        ↓
PRODUCT usage_status
        ↓
PRODUCT_HISTORY snapshot
        ↓
COMMIT
```

Każdy błąd:

```text
ROLLBACK całości
```

---

## 2. Źródła obowiązujące

Przed implementacją przeczytaj co najmniej:

- root `AGENTS.md`,
- aktualny zatwierdzony `CORE-001`,
- `BDR-004`,
- `BDR-003`,
- `TDR-001`,
- `TDR-002`,
- `TDR-003`,
- `TDR-004`,
- `SPRINT-004`,
- `TASK-022` i `TASK-022_REPORT`,
- `TASK-021_REPORT` jako stan wejściowy po Sprint 3.

Jeżeli implementacja wymaga nowej decyzji biznesowej lub zmiany Core:

```text
STOP
```

Nie zgaduj.

---

## 3. Stan wejściowy

Po TASK-022 istnieją:

```text
RegisterBhpDecisionInput
RegisterBhpDecisionResult
BhpEvidenceValidatorPort
BhpDecisionRepositoryPort
RegisterBhpDecision
BhpDecisionValidationError
```

Stan techniczny po TASK-022:

```text
pytest        126 passed
Alembic       e0dd7d6468bf (head)
schema        12 tables
drift         none
```

TASK-023 może zmienić ORM/schema tylko wtedy, gdy zatwierdzone encje:

```text
BHP_DECISION
DECISION_EVIDENCE
```

nie mają jeszcze pełnego odwzorowania w obecnym schema.

Jeżeli już istnieją, nie twórz zbędnej migracji.

---

## 4. Zakres

TASK-023 obejmuje:

1. adapter walidacji dowodu,
2. implementację `BhpDecisionRepositoryPort`,
3. persystencję `DECISION_EVIDENCE`,
4. persystencję `BHP_DECISION`,
5. CURRENT / SUPERSEDED,
6. zmianę PRODUCT na ACTIVE / REJECTED,
7. PRODUCT_HISTORY snapshot,
8. transaction boundary,
9. PostgreSQL integration tests,
10. migrację Alembic wyłącznie jeśli rzeczywiście potrzebna.

Nie implementuj UI.

---

## 5. Walidacja dowodu

Zaimplementuj adapter infrastrukturalny do:

```text
BhpEvidenceValidatorPort
```

Walidator ma sprawdzać:

- ścieżka jest względna,
- plik istnieje pod `BHP_EVIDENCE_ROOT_PATH`,
- plik nie wychodzi poza root,
- rozszerzenie należy do:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Walidator:
- nie kopiuje pliku,
- nie przenosi,
- nie usuwa,
- nie zmienia nazwy,
- nie analizuje treści.

Zwraca znormalizowaną ścieżkę względną.

---

## 6. Walidacja PRODUCT / SDS

Przed utworzeniem decyzji repository musi potwierdzić:

```text
PRODUCT istnieje
SDS istnieje
SDS.product_id == product_id
SDS.document_status == CURRENT
```

Jeżeli którykolwiek warunek nie jest spełniony:

```text
controlled error
+
ROLLBACK
```

Nie można zarejestrować decyzji dla:
- obcego produktu,
- nieistniejącego SDS,
- ARCHIVED SDS.

---

## 7. DECISION_EVIDENCE

Każda decyzja posiada dokładnie jeden dowód.

Minimalny zapis ma odpowiadać zatwierdzonemu modelowi i istniejącemu schema, np.:

```text
evidence_id
relative_path
file_format / evidence_type — tylko jeśli istnieje w zatwierdzonym modelu
registered_at / created_at — zgodnie z aktualnym schema
```

Nie dodawaj nowych pól „na przyszłość”.

Powiązanie:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Decyzja bez dowodu nie może zostać zatwierdzona.

---

## 8. BHP_DECISION

Minimalne dane:

```text
decision_id
product_id
sds_id
decision_status
notes
registered_at
record_status
evidence_id
```

Dozwolone:

```text
decision_status:
APPROVED
REJECTED

record_status:
CURRENT
SUPERSEDED
```

Nie dodawaj:

```text
PENDING
decided_by
decision_date
signature
approver_id
```

---

## 9. Pierwsza decyzja dla SDS

Jeżeli dla `sds_id` nie istnieje CURRENT decision:

```text
insert evidence
insert BHP_DECISION CURRENT
update PRODUCT usage_status
insert PRODUCT_HISTORY snapshot
```

Wynik:

```text
APPROVED → PRODUCT = ACTIVE
REJECTED → PRODUCT = REJECTED
```

---

## 10. Kolejna decyzja dla tego samego SDS

Jeżeli istnieje CURRENT decision:

```text
old CURRENT → SUPERSEDED
new evidence
new BHP_DECISION CURRENT
PRODUCT status update
PRODUCT_HISTORY snapshot
```

Poprzednia decyzja i jej dowód pozostają w historii.

Nie edytuj poprzedniego `decision_status`, `notes` ani evidence.

---

## 11. CURRENT / SUPERSEDED

Twarda reguła:

```text
dla jednego sds_id
→ maksymalnie jedna BHP_DECISION CURRENT
```

Regułę zabezpiecz co najmniej logiką repository/Application i testami.

Jeżeli istniejący schema posiada już indeks/constraint dla tej reguły — użyj go.

Jeżeli jego dodanie wymaga prostej migracji zgodnej z zatwierdzonym modelem, jest to dozwolone.

Nie buduj dodatkowego systemu concurrency.

---

## 12. Status PRODUCT

Po nowej CURRENT decision:

```text
APPROVED → PRODUCT.usage_status = ACTIVE
REJECTED → PRODUCT.usage_status = REJECTED
```

Nie ustawiaj:

```text
INACTIVE
PENDING_APPROVAL
```

jako wyniku decyzji BHP.

`PENDING_APPROVAL` oznacza brak aktualnej decyzji dla CURRENT SDS.

---

## 13. PRODUCT_HISTORY

Zmiana statusu PRODUCT musi utworzyć snapshot historii zgodnie z TDR-004.

Snapshot powinien zawierać aktualny zatwierdzony stan historyzowanych pól PRODUCT, w tym:

```text
usage_status
use_description
use_restriction
waste_type
waste_code
changed_at
```

Obowiązuje:

```text
PRODUCT update
+
PRODUCT_HISTORY snapshot
=
ONE TRANSACTION
```

Nie twórz nowego history framework.

---

## 14. Atomowość

Cała operacja rejestracji decyzji jest jedną transakcją:

```text
validate product/sds
validate evidence
archive old decision if needed
insert evidence
insert new decision
update product
insert product history
COMMIT
```

Repository nie może commitować per metoda.

Użyj istniejącego `TransactionExecutor`.

Jeżeli dowolny etap zawiedzie:

```text
ROLLBACK
```

Po rollbacku nie może zostać:
- samotny evidence,
- decision bez evidence,
- SUPERSEDED bez nowej CURRENT,
- zmieniony Product bez historii,
- historia bez odpowiadającego current state.

---

## 15. ORM / Alembic

Najpierw sprawdź istniejący ORM/schema.

Jeżeli `BHP_DECISION` i `DECISION_EVIDENCE` już istnieją i są zgodne z Core:

```text
NIE twórz migracji
```

Jeżeli brakuje wymaganych zatwierdzonych tabel/kolumn/constraintów:

- dodaj minimalne modele ORM,
- przygotuj jedną spójną migrację Alembic,
- bez rozszerzania modelu.

Nie używaj `Base.metadata.create_all()`.

---

## 16. Constraints i FK

Minimalnie sprawdź / zapewnij:

```text
BHP_DECISION.product_id → PRODUCT
BHP_DECISION.sds_id → SDS
BHP_DECISION.evidence_id → DECISION_EVIDENCE
```

oraz zatwierdzone wartości statusów.

Nie stosuj `ON DELETE CASCADE`, jeśli mogłoby usunąć historię decyzji.

Jeżeli aktualny schema posiada inną zatwierdzoną semantykę usuwania, zachowaj ją.

---

## 17. Wynik portu

`BhpDecisionRepositoryPort.register()` ma zwrócić:

```text
RegisterBhpDecisionResult
```

z rzeczywistymi wartościami zapisanymi w systemie:

```text
decision_id
product_id
sds_id
decision_status
product_usage_status
registered_at
evidence_relative_path
```

Nie twórz osobnego read model tylko dla TASK-023.

---

## 18. Testy Application / Infrastructure

Dodaj focused testy dla:

### APPROVED

```text
PENDING_APPROVAL
→ APPROVED
→ PRODUCT ACTIVE
→ decision CURRENT
→ evidence exists
→ ProductHistory ACTIVE
```

### REJECTED

```text
PENDING_APPROVAL
→ REJECTED
→ PRODUCT REJECTED
```

### Korekta

```text
decision #1 CURRENT
→ decision #1 SUPERSEDED
→ decision #2 CURRENT
```

i odpowiednia zmiana Product.

### Archived SDS

Próba rejestracji decyzji dla ARCHIVED SDS:

```text
controlled error
zero zmian
```

### SDS innego Product

```text
controlled error
zero zmian
```

### Brak evidence

```text
controlled error
zero zmian
```

---

## 19. PostgreSQL rollback tests

Obowiązkowo na rzeczywistym PostgreSQL potwierdź:

### A. Success

```text
evidence + decision + product + history
→ COMMIT
```

### B. Failure po evidence

Wymuś kontrolowany błąd po utworzeniu evidence, ale przed zakończeniem całej operacji:

```text
ROLLBACK
→ evidence count bez zmian
→ decision count bez zmian
→ product status bez zmian
→ history bez nowego snapshotu
```

### C. Failure przy korekcie

Jeżeli stara decyzja została już oznaczona SUPERSEDED, a nowa operacja zawiedzie:

```text
ROLLBACK
→ stara decyzja nadal CURRENT
```

To jest krytyczny test.

---

## 20. Test pliku dowodu

Do testów użyj kontrolowanego fixture w tymczasowym `BHP_EVIDENCE_ROOT_PATH`.

Nie dodawaj trwałego realnego MSG/PDF/JPG do repo, jeśli nie jest to już zatwierdzony fixture.

Dopuszczalny jest prosty testowy plik np. `.pdf` lub `.jpg` utworzony technicznie na czas testu, jeśli walidator sprawdza tylko istnienie/rozszerzenie.

Nie analizuj zawartości pliku.

---

## 21. Brak UI

TASK-023 nie implementuje Streamlit.

Nie twórz:
- formularza decyzji,
- wyboru evidence w UI,
- widoku historii decyzji.

To należy do TASK-024.

---

## 22. Poza zakresem

Nie implementuj:

```text
AI/OCR
analizy treści evidence
decided_by
decision_date
e-signature
approval workflow
notifications
REACH
BHP multi-user
upload service
storage service
generic audit
event sourcing
database triggers
Streamlit
```

---

## 23. STOP CONDITIONS

Zatrzymaj jako `PARTIAL / BLOCKED`, jeśli:

- wymagane jest rozszerzenie Core,
- potrzebny jest nowy status biznesowy,
- obecny model BHP_DECISION/DECISION_EVIDENCE jest sprzeczny z BDR-004,
- potrzebna jest nowa biblioteka,
- potrzebna jest nowa istotna decyzja techniczna,
- nie da się bezpiecznie zapewnić atomowości istniejącym TransactionExecutor,
- konieczne byłoby rozpoczęcie TASK-024.

Minimalna migracja odwzorowująca już zatwierdzony model nie jest blockerem.

---

## 24. Regression

Po implementacji:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- focused tests PASS,
- pełna regresja PASS,
- brak `SAWarning`.

---

## 25. Alembic

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Jeżeli migracja nie jest potrzebna:

```text
head = e0dd7d6468bf
```

Jeżeli migracja powstanie:
- podaj `revision`,
- `down_revision`,
- nową liczbę tabel,
- `alembic check` musi zakończyć się bez driftu.

---

## 26. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored,
- brak sekretów,
- brak trwałych testowych evidence,
- brak dumpów/backupów,
- brak commit/push bez polecenia.

---

## 27. Definition of Done

TASK-023 = DONE, gdy:

1. istnieje adapter `BhpEvidenceValidatorPort`,
2. działa walidacja root/path/extension,
3. działa persystencja DECISION_EVIDENCE,
4. działa persystencja BHP_DECISION,
5. decyzja zawsze wskazuje PRODUCT i SDS,
6. SDS musi należeć do PRODUCT,
7. SDS musi być CURRENT,
8. APPROVED → Product ACTIVE,
9. REJECTED → Product REJECTED,
10. decyzja ma record_status CURRENT,
11. poprzednia CURRENT przy korekcie przechodzi na SUPERSEDED,
12. maksymalnie jedna CURRENT na sds_id,
13. poprzednie decyzje/evidence pozostają,
14. ProductHistory rejestruje zmianę statusu,
15. całość jest atomowa,
16. rollback po częściowym zapisie działa,
17. rollback korekty przywraca poprzednią CURRENT,
18. brak edycji zatwierdzonej starej decyzji,
19. brak BHP UI,
20. brak zmian Core poza zatwierdzonym modelem,
21. focused tests PASS,
22. pełny pytest PASS,
23. brak SAWarning,
24. Alembic bez driftu,
25. TASK-024 nie został rozpoczęty.

---

## 28. Raport

Utwórz:

```text
docs/task_reports/TASK-023_REPORT.md
```

Raport ma zawierać:

1. status,
2. zmienione pliki,
3. evidence validator,
4. walidację PRODUCT/SDS,
5. DECISION_EVIDENCE persistence,
6. BHP_DECISION persistence,
7. CURRENT/SUPERSEDED,
8. Product status transition,
9. ProductHistory,
10. transaction boundary,
11. rollback tests,
12. ORM/schema,
13. migrację, jeśli powstała,
14. focused tests,
15. PostgreSQL integration tests,
16. pełny pytest,
17. SAWarning,
18. Alembic current/check,
19. Git/bezpieczeństwo,
20. odstępstwa/ryzyka.

Na końcu:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-024.
```

---

## 29. Autoryzacja

Sama obecność pliku Tasku nie stanowi zgody na wykonanie.

Start dopiero po poleceniu:

```text
Wykonaj TASK-023.
```
