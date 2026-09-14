# TASK-022 — BHP Decision Application Contracts

**Projekt:** MSDS Manager  
**Task ID:** TASK-022  
**Sprint:** SPRINT-004 — Decyzja BHP i dowód decyzji  
**Status:** READY  
**Typ:** Application contracts / use-case boundary  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Przygotować minimalny kontrakt warstwy Application dla rejestracji decyzji BHP dotyczącej konkretnego PRODUCT i konkretnego SDS.

TASK-022 ma zdefiniować granicę dla kolejnych Tasków:

```text
Streamlit
   ↓
RegisterBhpDecision
   ↓
Application ports
   ↓
Infrastructure / PostgreSQL   [TASK-023]
```

W tym Tasku nie implementujemy persystencji ani UI.

---

## 2. Źródła obowiązujące

Przed rozpoczęciem przeczytaj co najmniej:

- root `AGENTS.md`,
- aktualny `CORE-001`,
- `BDR-004` — decyzja BHP,
- `TDR-001`,
- `TDR-003`,
- `TDR-004`,
- `SPRINT-004`,
- raport TASK-021 jako stan wejściowy po Sprint 3.

Jeżeli źródła nie rozstrzygają wymaganej reguły biznesowej:

```text
STOP
```

Nie uzupełniaj jej własnym założeniem.

---

## 3. Zakres

Zaimplementuj wyłącznie minimalne Application contracts potrzebne do przyszłego workflow:

```text
PRODUCT + CURRENT SDS
        ↓
dowód decyzji
        ↓
APPROVED / REJECTED
        ↓
notes
        ↓
RegisterBhpDecision
```

TASK-022 obejmuje:

1. DTO wejściowe decyzji,
2. DTO wyniku,
3. Application enum / typ statusu decyzji, jeśli istniejąca architektura wymaga takiego kontraktu,
4. port do walidacji pliku dowodu,
5. port do atomowej rejestracji decyzji,
6. use case `RegisterBhpDecision`,
7. kontrolowane wyjątki Application,
8. testy jednostkowe.

---

## 4. Kontrakt wejściowy

Przygotuj minimalny DTO, np.:

```text
RegisterBhpDecisionInput
```

z polami odpowiadającymi zatwierdzonemu modelowi:

```text
product_id
sds_id
decision_status
evidence_relative_path
notes
```

`notes` jest opcjonalne.

Nie dodawaj:

```text
decided_by
decision_date
approver_id
workflow_step
signature
confidence
```

---

## 5. Status decyzji

Dozwolone wartości biznesowe:

```text
APPROVED
REJECTED
```

Nie twórz statusu:

```text
PENDING
```

Brak decyzji jest reprezentowany przez stan PRODUCT:

```text
PENDING_APPROVAL
```

Jeżeli w istniejącym Domain/Core istnieje już właściwy enum, wykorzystaj go zgodnie z architekturą zamiast tworzyć duplikat.

Nie zmieniaj Domain w TASK-022.

---

## 6. Dowód decyzji

Każda rejestrowana decyzja musi wskazywać:

```text
evidence_relative_path
```

Ścieżka:
- nie może być pusta,
- ma być względna względem `BHP_EVIDENCE_ROOT_PATH`,
- zostanie zwalidowana przez port Application,
- nie oznacza uploadu ani kopiowania pliku.

TASK-022 nie implementuje filesystem adaptera.

Zdefiniuj port, np.:

```text
BhpEvidenceValidatorPort
```

który umożliwi TASK-023 walidację:
- istnienia pliku,
- pozostawania pod `BHP_EVIDENCE_ROOT_PATH`,
- dopuszczalnego rozszerzenia.

Dopuszczalne formaty zgodnie ze Sprintem:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Szczegóły filesystem pozostają poza Application.

---

## 7. Port rejestracji

Zdefiniuj minimalny port persystencji/transakcji, np.:

```text
BhpDecisionRepositoryPort
```

lub nazwę zgodną z aktualnym stylem projektu.

Port ma umożliwiać przyszłemu TASK-023 wykonanie jednej operacji biznesowej obejmującej:

```text
validate PRODUCT/SDS relationship
old CURRENT decision → SUPERSEDED
new evidence
new decision CURRENT
PRODUCT usage_status
PRODUCT_HISTORY
```

Nie implementuj tych operacji w TASK-022.

Nie rozbijaj kontraktu na wiele repozytoriów, jeżeli nie jest to potrzebne.

Preferuj jedną wyraźną granicę operacji Application → Infrastructure.

---

## 8. Use case

Zaimplementuj:

```text
RegisterBhpDecision
```

Use case ma:

1. przyjąć `RegisterBhpDecisionInput`,
2. wykonać prostą walidację wejścia należącą do Application,
3. wywołać validator dowodu,
4. delegować zapis do portu rejestracji,
5. zwrócić minimalny wynik.

Use case nie może:
- wykonywać SQL,
- importować SQLAlchemy,
- otwierać sesji PostgreSQL,
- wykonywać commit/rollback,
- czytać `.env`,
- operować bezpośrednio na filesystem,
- ustawiać statusów przez Streamlit.

---

## 9. Minimalny wynik

Zwróć DTO wystarczające przyszłemu UI do pokazania sukcesu, np.:

```text
RegisterBhpDecisionResult
```

Minimalnie:

```text
decision_id
product_id
sds_id
decision_status
product_usage_status
registered_at
evidence_relative_path
```

Nie rozbudowuj wyniku o dane, których UI nie potrzebuje.

Jeżeli zgodnie z aktualną architekturą część tych danych należy zwracać inaczej, zachowaj istniejący styl projektu i opisz to w raporcie.

---

## 10. Walidacja Application

Waliduj co najmniej:

```text
product_id        wymagane
sds_id            wymagane
decision_status   APPROVED lub REJECTED
evidence path     wymagane
```

`notes`:
- opcjonalne,
- pusta wartość może zostać znormalizowana do `None`, jeśli jest to zgodne z istniejącym stylem.

Nie wprowadzaj arbitralnych limitów długości bez istniejącej decyzji/schema.

---

## 11. Reguły pozostawione TASK-023

TASK-022 nie rozstrzyga technicznie:

- czy PRODUCT istnieje,
- czy SDS istnieje,
- czy SDS należy do PRODUCT,
- czy SDS jest CURRENT,
- czy istnieje poprzednia decyzja CURRENT,
- jak wykonywane jest CURRENT → SUPERSEDED,
- jak tworzony jest evidence record,
- jak PRODUCT przechodzi na ACTIVE/REJECTED,
- jak tworzony jest PRODUCT_HISTORY snapshot,
- jak realizowany jest rollback.

Kontrakty mają umożliwić wykonanie tych reguł w TASK-023.

---

## 12. Kontrolowane błędy

Użyj istniejącego mechanizmu wyjątków Application.

Potrzebne błędy powinny być możliwe do czytelnego obsłużenia przez przyszły Streamlit, np.:

```text
invalid input
invalid decision status
missing/invalid evidence
product not found
sds not found
SDS does not belong to product
SDS is not CURRENT
persistence failure
```

Nie twórz rozbudowanej hierarchii wyjątków, jeśli istniejący mechanizm wystarcza.

TASK-022 ma jedynie zapewnić kontrakt pozwalający Infrastructure zgłosić kontrolowany błąd.

---

## 13. Architektura

Wymagana zależność:

```text
presentation
     ↓
application
     ↓
domain

infrastructure → implements application ports
```

Application nie może importować:

```text
Streamlit
SQLAlchemy
psycopg
Alembic
pypdf
filesystem adapter
```

Nie zmieniaj kierunku zależności.

---

## 14. Bez zmian Core i schema

TASK-022 nie może zmieniać:

- Domain models,
- Domain enums,
- ORM,
- PostgreSQL schema,
- Alembic,
- historii Core,
- istniejących tabel.

Oczekiwany Alembic head:

```text
e0dd7d6468bf
```

Jeżeli kontrakt wymaga zmiany Core:

```text
STOP
```

---

## 15. Bez nowych zależności

Nie dodawaj bibliotek.

Jeżeli wykonanie Tasku wymaga nowej zależności:

```text
STOP
```

---

## 16. Testy jednostkowe

Dodaj testy co najmniej dla:

### poprawnej decyzji APPROVED

```text
valid input
→ evidence validator called
→ registration port called once
→ result returned
```

### poprawnej decyzji REJECTED

Analogicznie.

### błędnego statusu

```text
invalid decision_status
→ controlled Application error
→ validator/repository not called
```

### brakującego evidence path

```text
empty evidence_relative_path
→ controlled Application error
→ repository not called
```

### błędu validatora

```text
validator raises controlled error
→ registration port not called
```

### propagacji kontrolowanego błędu persistence

Use case nie może zamienić błędu na fałszywy sukces.

---

## 17. Regression

Po implementacji uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- wszystkie wcześniejsze testy PASS,
- nowe testy PASS,
- brak `SAWarning`.

Baseline po TASK-021:

```text
120 passed
```

---

## 18. Alembic / schema

Potwierdź:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
e0dd7d6468bf (head)
No new upgrade operations detected.
```

Schema pozostaje bez zmian.

---

## 19. Poza zakresem

Nie implementuj:

```text
BHP_DECISION ORM
DECISION_EVIDENCE ORM
migration
PostgreSQL persistence
filesystem adapter
Streamlit UI
ACTIVE/REJECTED transition implementation
CURRENT/SUPERSEDED implementation
ProductHistory write
BHP evidence viewer
file upload
file copy
AI/OCR
REACH
notifications
```

To należy do kolejnych Tasków.

---

## 20. Definition of Done

TASK-022 = DONE, gdy:

1. istnieje DTO wejściowe decyzji,
2. istnieje minimalny DTO wyniku,
3. obsługiwane są tylko APPROVED/REJECTED,
4. evidence path jest wymagany,
5. istnieje port validatora dowodu,
6. istnieje port rejestracji decyzji,
7. istnieje `RegisterBhpDecision`,
8. use case waliduje podstawowe wejście,
9. use case wywołuje validator przed persystencją,
10. use case deleguje zapis do portu,
11. kontrolowane błędy są propagowane,
12. brak SQL/filesystem w Application,
13. brak zmian Domain,
14. brak zmian ORM/schema/Alembic,
15. brak nowych zależności,
16. nowe testy PASS,
17. pełna regresja PASS,
18. brak `SAWarning`,
19. Alembic bez driftu,
20. TASK-023 nie został rozpoczęty.

---

## 21. Raport

Utwórz:

```text
docs/task_reports/TASK-022_REPORT.md
```

Raport ma zawierać:

1. status `DONE / PARTIAL / BLOCKED`,
2. zmienione pliki,
3. utworzone DTO,
4. port validatora,
5. port rejestracji,
6. działanie `RegisterBhpDecision`,
7. walidacje,
8. kontrolowane błędy,
9. testy focused,
10. pełny pytest,
11. SAWarning,
12. Alembic current/check,
13. potwierdzenie braku zmian schema,
14. potwierdzenie braku nowych zależności,
15. odstępstwa/ryzyka.

Na końcu:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-023.
```

---

## 22. Autoryzacja

Sama obecność pliku Tasku nie stanowi zgody na wykonanie.

Start dopiero po poleceniu:

```text
Wykonaj TASK-022.
```
