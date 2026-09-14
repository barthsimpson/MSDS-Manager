# TASK-025 — Sprint 4 End-to-End Acceptance

**Projekt:** MSDS Manager  
**Task ID:** TASK-025  
**Sprint:** SPRINT-004 — Decyzja BHP i dowód decyzji  
**Status:** READY  
**Typ:** Acceptance / End-to-End / Sprint Closure Candidate  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Przeprowadzić końcową walidację całego Sprintu 4 jako jednego działającego procesu:

```text
PRODUCT = PENDING_APPROVAL
        ↓
CURRENT SDS
        ↓
Streamlit „Decyzja BHP”
        ↓
evidence z BHP_EVIDENCE_ROOT_PATH
        ↓
APPROVED / REJECTED
        ↓
RegisterBhpDecision
        ↓
TransactionExecutor
        ↓
PostgreSQL
        ↓
PRODUCT ACTIVE / REJECTED
        ↓
PRODUCT_HISTORY
```

TASK-025 jest Taskiem acceptance.

Nie ma dodawać nowych funkcji.

---

## 2. Źródła obowiązujące

Przed wykonaniem przeczytaj co najmniej:

- root `AGENTS.md`,
- aktualny `CORE-001`,
- `BDR-004`,
- `BDR-003`,
- `TDR-001`,
- `TDR-002`,
- `TDR-003`,
- `TDR-004`,
- `SPRINT-004`,
- `TASK-022` + REPORT,
- `TASK-023` + REPORT,
- `TASK-024` + REPORT,
- `TASK-021_REPORT` jako stan wejściowy po Sprint 3.

Jeżeli E2E ujawni potrzebę nowej decyzji biznesowej lub zmiany Core:

```text
STOP
```

Nie zgaduj.

---

## 3. Zasada TASK-025

Preferowany wynik:

```text
0 nowych funkcji
+
pełny scenariusz APPROVED
+
pełny scenariusz korekty decyzji
+
scenariusz REJECTED
+
pełna regresja
+
raport acceptance
```

Drobny jednoznaczny defekt techniczny można poprawić tylko, jeśli:
- nie zmienia Core,
- nie zmienia schema,
- nie dodaje nowej funkcji,
- nie wymaga nowego statusu,
- nie rozszerza Sprintu.

Każdą korektę opisz w raporcie.

Jeżeli potrzebna byłaby nowa funkcja lub decyzja:

```text
PARTIAL / BLOCKED
```

---

## 4. Baseline

Przed E2E uruchom:

```powershell
git status --short
git diff --check
git diff --cached --check

$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"

.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwany stan po TASK-024:

```text
pytest        137 passed
Alembic       e0dd7d6468bf (head)
schema        bez zmian
drift         none
```

Rozbieżności wyjaśnij, nie maskuj.

---

## 5. Dane wejściowe E2E

TASK-025 nie tworzy nowego publicznego workflow PRODUCT/SDS.

Przygotuj kontrolowany fixture techniczny reprezentujący stan po Sprint 3:

```text
MANUFACTURER
PRODUCT
CURRENT SDS
PRODUCT.usage_status = PENDING_APPROVAL
```

Fixture może zostać utworzony przez setup testu / bezpośredni mechanizm techniczny zgodny z istniejącą praktyką testową.

Nie twórz nowego UI ani publicznego use case tylko na potrzeby setupu.

Po teście fixture ma zostać usunięty / rollbackowany.

---

## 6. Testowy BHP_EVIDENCE_ROOT_PATH

Utwórz tymczasowy katalog:

```text
BHP_EVIDENCE_ROOT_PATH
```

i kontrolowane pliki dowodowe, np.:

```text
approved.pdf
rejected.jpg
correction.msg
```

Zawartość plików nie jest analizowana.

Liczy się:
- istnienie,
- rozszerzenie,
- relative_path,
- powiązanie z decyzją.

Po teście pliki mają zostać usunięte.

---

## 7. Scenariusz A — APPROVED

### A1. Start UI

Uruchom istniejący widok `Decyzja BHP` z prawdziwym `ShellComposition`, PostgreSQL i kontrolowanym `BHP_EVIDENCE_ROOT_PATH`.

### A2. Produkt

Potwierdź, że fixture PRODUCT jest widoczny i pokazuje:

```text
usage_status = PENDING_APPROVAL
```

### A3. CURRENT SDS

Potwierdź, że widoczny jest właściwy CURRENT SDS.

### A4. Evidence

Wybierz:

```text
approved.pdf
```

lub równoważny kontrolowany plik.

### A5. Decyzja

Wybierz:

```text
APPROVED
```

Dodaj opcjonalne `notes`, np.:

```text
Dopuszczony pod warunkiem stosowania zgodnie z instrukcją BHP.
```

### A6. Zapis

Kliknij:

```text
Zapisz decyzję
```

### A7. PostgreSQL

Potwierdź:

```text
BHP_DECISION exists
decision_status = APPROVED
record_status = CURRENT
DECISION_EVIDENCE exists
evidence_relative_path = expected
PRODUCT.usage_status = ACTIVE
PRODUCT_HISTORY contains ACTIVE snapshot
```

### A8. UI po sukcesie

Potwierdź:
- komunikat sukcesu,
- PRODUCT status = ACTIVE,
- bieżąca decyzja CURRENT jest widoczna,
- registered_at jest widoczne,
- notes są widoczne,
- evidence path jest widoczna.

---

## 8. Scenariusz B — korekta decyzji dla tego samego SDS

Celem jest potwierdzenie historii decyzji.

### B1. Stan wejściowy

Po scenariuszu A istnieje:

```text
Decision #1 CURRENT = APPROVED
PRODUCT = ACTIVE
```

### B2. Nowa decyzja

W tym samym UI wybierz nowy evidence:

```text
correction.msg
```

i decyzję:

```text
REJECTED
```

Dodaj notes, np.:

```text
Korekta wcześniejszej decyzji.
```

### B3. Zapis

Zapisz nową decyzję.

### B4. PostgreSQL

Potwierdź:

```text
Decision #1 = SUPERSEDED
Decision #2 = CURRENT
Decision #2.status = REJECTED
Decision #1 evidence nadal istnieje
Decision #2 evidence istnieje
CURRENT count for sds_id = 1
PRODUCT.usage_status = REJECTED
PRODUCT_HISTORY contains new REJECTED snapshot
```

Stara decyzja nie może zostać fizycznie usunięta ani nadpisana.

---

## 9. Scenariusz C — ponowna decyzja APPROVED

Opcjonalnie, jeżeli test pozostaje prosty i czytelny, wykonaj trzecią decyzję:

```text
APPROVED
```

dla tego samego SDS, aby potwierdzić:

```text
Decision #2 → SUPERSEDED
Decision #3 → CURRENT
PRODUCT → ACTIVE
```

Nie jest to obowiązkowe, jeśli scenariusze A+B wystarczają do pokrycia obu statusów i historii.

---

## 10. Scenariusz D — brak evidence

Spróbuj zapisać decyzję bez wybranego dowodu.

Potwierdź:

```text
controlled error
no RegisterBhpDecision success
no DB changes
no false success message
```

---

## 11. Scenariusz E — ARCHIVED SDS

W warstwie Application/Infrastructure acceptance potwierdź, że próba rejestracji decyzji dla ARCHIVED SDS kończy się:

```text
controlled error
zero changes
```

Nie musisz budować osobnego UI do wyboru ARCHIVED SDS, jeśli UI słusznie pokazuje tylko CURRENT.

---

## 12. Scenariusz F — rollback korekty

Wykorzystaj istniejący mechanizm/test z TASK-023 lub rozszerz acceptance w kontrolowany sposób.

Potwierdź:

```text
old CURRENT → SUPERSEDED
then failure
→ ROLLBACK
→ old decision remains CURRENT
→ Product status unchanged
→ no orphan evidence
→ no extra ProductHistory
```

Nie wystarczy mock.

Potwierdzenie ma dotyczyć rzeczywistego PostgreSQL.

---

## 13. PostgreSQL jako źródło prawdy

Po każdym scenariuszu zapisującym dane potwierdź stan w PostgreSQL.

Sprawdź zgodność:

```text
UI
=
Application
=
PostgreSQL
=
ProductHistory
```

Nie dodawaj SQL do Streamlit.

---

## 14. Historia decyzji

Acceptance ma jednoznacznie wykazać:

```text
dla jednego sds_id:
Decision #1 SUPERSEDED
Decision #2 CURRENT
```

oraz zachowanie obu evidence.

Jeżeli wykonasz scenariusz C:

```text
Decision #1 SUPERSEDED
Decision #2 SUPERSEDED
Decision #3 CURRENT
```

Maksymalnie jedna CURRENT.

---

## 15. Historia PRODUCT

Potwierdź snapshoty odpowiadające zmianom statusu:

```text
PENDING_APPROVAL
→ ACTIVE
→ REJECTED
```

Jeżeli wykonasz ponowne APPROVED:

```text
→ ACTIVE
```

Nie twórz nowego mechanizmu historii.

---

## 16. Brak treściowego przetwarzania evidence

Potwierdź, że w całym E2E aplikacja:

- nie analizuje treści MSG/PDF/JPG,
- nie wykonuje OCR,
- nie odczytuje osoby decydującej,
- nie odczytuje daty decyzji,
- nie ustala decyzji automatycznie.

Użytkownik ręcznie wybiera:

```text
APPROVED / REJECTED
```

Evidence jest wyłącznie dowodem źródłowym.

---

## 17. Cleanup

Po E2E:

- usuń/rollbackuj fixture PRODUCT/SDS,
- usuń decyzje testowe i evidence metadata zgodnie z technicznym cleanupem testowym,
- usuń tymczasowe pliki evidence,
- nie twórz publicznych delete use case'ów,
- nie usuwaj danych produkcyjnych.

Po cleanup baza powinna wrócić do stanu sprzed testu.

---

## 18. Kontrola DoD SPRINT-004

W raporcie oznacz:

```text
PASS
FAIL
NOT VERIFIED
```

dla co najmniej:

1. można wskazać PRODUCT z CURRENT SDS,
2. można wybrać evidence z BHP_EVIDENCE_ROOT_PATH,
3. evidence jest wymagane,
4. można zapisać APPROVED,
5. APPROVED ustawia PRODUCT = ACTIVE,
6. można zapisać REJECTED,
7. REJECTED ustawia PRODUCT = REJECTED,
8. decyzja wskazuje product_id i sds_id,
9. jedna decyzja ma dokładnie jeden evidence,
10. maksymalnie jedna decyzja CURRENT na sds_id,
11. korekta tworzy nową decyzję,
12. poprzednia decyzja przechodzi na SUPERSEDED,
13. poprzedni evidence pozostaje,
14. notes działa,
15. registered_at jest zapisane,
16. brak decided_by / decision_date,
17. operacja jest atomowa,
18. rollback działa,
19. ProductHistory zachowuje zmianę statusu,
20. evidence file nie jest modyfikowany,
21. brak automatycznej decyzji BHP,
22. E2E Sprintu 4 przechodzi.

Codex nie zamyka Sprintu samodzielnie.

---

## 19. Regression

Po acceptance:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- wszystkie testy PASS,
- brak `SAWarning`.

Nie osłabiaj istniejących testów.

---

## 20. Alembic / schema

TASK-025 nie powinien wymagać migracji.

Potwierdź:

```text
alembic current = e0dd7d6468bf (head)
alembic check = No new upgrade operations detected.
schema bez zmian
```

Jeżeli acceptance wymaga schema change:

```text
STOP
```

---

## 21. Architektura

Potwierdź nadal:

```text
Streamlit
   ↓
ShellComposition
   ↓
RegisterBhpDecision
   ↓
Application
   ↓
Infrastructure
   ↓
TransactionExecutor
   ↓
PostgreSQL
```

Streamlit:
- bez SQL,
- bez ORM,
- bez commit/rollback,
- bez analizy evidence.

---

## 22. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored,
- brak sekretów,
- brak trwałych fixture evidence,
- brak dumpów/backupów,
- brak commit/push bez polecenia.

---

## 23. Poza zakresem

TASK-025 NIE implementuje:

```text
R6
REACH
AI/OCR
analizy dowodu
upload service
storage service
kartoteki osób BHP
e-signature
notifications
periodic review
new schema
new dependencies
new business statuses
```

Nie rozpoczynaj kolejnego etapu Roadmapy.

---

## 24. STOP CONDITIONS

Zatrzymaj jako `PARTIAL / BLOCKED`, jeśli:
- potrzebna jest nowa funkcja,
- potrzebna jest zmiana Core,
- potrzebna jest migracja/schema change,
- potrzebny jest nowy status,
- potrzebna jest nowa zależność,
- problemu nie da się naprawić bez rozszerzenia Sprintu.

---

## 25. Definition of Done TASK-025

TASK-025 = DONE tylko gdy:

1. baseline jest zielony,
2. PRODUCT PENDING_APPROVAL jest dostępny w UI,
3. CURRENT SDS jest poprawnie powiązany,
4. evidence można wybrać,
5. APPROVED przechodzi E2E,
6. PRODUCT staje się ACTIVE,
7. REJECTED przechodzi E2E,
8. PRODUCT staje się REJECTED,
9. CURRENT/SUPERSEDED działa,
10. poprzedni evidence pozostaje,
11. jedna CURRENT decision na SDS,
12. notes i registered_at działają,
13. ProductHistory rejestruje zmiany,
14. brak evidence blokuje zapis,
15. ARCHIVED SDS nie przyjmuje decyzji,
16. rollback korekty działa w PostgreSQL,
17. evidence nie jest modyfikowane,
18. cleanup działa,
19. pełny pytest PASS,
20. brak SAWarning,
21. Alembic bez driftu,
22. schema bez zmian,
23. brak nowych zależności,
24. wszystkie punkty DoD SPRINT-004 = PASS,
25. następny etap Roadmapy nie został rozpoczęty.

---

## 26. Raport

Utwórz:

```text
docs/task_reports/TASK-025_REPORT.md
```

Raport ma zawierać:

1. status `DONE / PARTIAL / BLOCKED`,
2. baseline,
3. zmienione pliki,
4. informację, czy zmieniono production code,
5. setup PRODUCT/CURRENT SDS,
6. setup BHP_EVIDENCE_ROOT_PATH,
7. scenariusz APPROVED,
8. stan PostgreSQL po APPROVED,
9. scenariusz korekty REJECTED,
10. CURRENT/SUPERSEDED,
11. evidence history,
12. ProductHistory,
13. brak evidence,
14. ARCHIVED SDS,
15. rollback korekty,
16. brak analizy evidence,
17. cleanup,
18. pełny pytest,
19. SAWarning,
20. Alembic current/check,
21. schema,
22. architekturę,
23. Git/bezpieczeństwo,
24. tabelę DoD SPRINT-004 PASS/FAIL/NOT VERIFIED,
25. odstępstwa i ryzyka,
26. rekomendację:
   - `READY FOR SPRINT-004 CLOSURE`
   albo
   - `NOT READY FOR SPRINT-004 CLOSURE`.

Codex nie podejmuje formalnej decyzji o zamknięciu Sprintu.

---

## 27. Autoryzacja

Sama obecność TASK-025 nie stanowi zgody na wykonanie.

Start dopiero po poleceniu:

```text
Wykonaj TASK-025.
```

Po wykonaniu:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO ETAPU ROADMAPY.
```
