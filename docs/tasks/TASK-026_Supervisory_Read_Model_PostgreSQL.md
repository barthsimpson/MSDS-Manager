# TASK-026 — Supervisory Read Model + PostgreSQL

**Projekt:** MSDS Manager  
**Task ID:** TASK-026  
**Sprint:** SPRINT-005 — R7 Widok nadzorczy  
**Status:** READY  
**Typ:** Application Read Model / PostgreSQL Query / Integration Tests  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

## 1. Cel

Przygotować prosty read model dla R7 i jego odczyt z PostgreSQL.

Task ma odpowiedzieć dla każdego PRODUCT:

```text
jaki jest aktualny stan
+
czy wymaga działania
+
dlaczego
```

TASK-026 łączy wcześniejszy plan read model + PostgreSQL integration, żeby nie komplikować rozwiązania.

Nie implementujemy jeszcze Streamlit UI.

## 2. Zasada MVP

```text
Core / PostgreSQL
      ↓
prosty read model
      ↓
kilka reguł
      ↓
wynik gotowy dla UI
```

Nie tworzyć:
- tabeli ISSUE,
- workflow problemów,
- scoringu,
- osobnego silnika reguł,
- cache,
- CQRS framework,
- dashboard backend.

## 3. Źródła

Przed implementacją przeczytaj:
- root `AGENTS.md`,
- aktualny `CORE-001`,
- `BDR-002`, `BDR-003`, `BDR-004`, `BDR-005`,
- `TDR-003`, `TDR-004`,
- `SPRINT-005`,
- `CHECKPOINT-004`,
- raporty TASK-021 i TASK-025.

Zmiana Core/schema → **STOP**.

## 4. Stan wejściowy

Po R5:

```text
pytest baseline    138 passed
Alembic head       e0dd7d6468bf
business tables    12
schema drift       none
```

TASK-026 wyłącznie odczytuje istniejące dane.

## 5. Read model

Dodaj jeden prosty DTO, np. `SupervisoryProductRow`:

```text
product_id
product_name
manufacturer_name
manufacturer_product_code
usage_status
use_description
use_restriction

usage_locations[]

current_sds_id
current_sds_filename
current_sds_issue_date
current_sds_revision
current_sds_file_available

current_bhp_decision_id
current_bhp_decision_status
current_bhp_registered_at
current_bhp_notes
current_bhp_evidence_relative_path
current_bhp_evidence_available

requires_action
action_reasons[]
```

Bez pól „na przyszłość”.

## 6. Jeden PRODUCT = jeden rekord

Wiele aktywnych miejsc stosowania ma być zagregowane do `usage_locations[]`.

Nie duplikuj PRODUCT przez relację do wielu lokalizacji.

## 7. CURRENT SDS

Wybieraj wyłącznie SDS z:

```text
document_status = CURRENT
```

Nie wybieraj „najnowszego” po dacie ani rewizji.

Brak CURRENT:

```text
current_sds_id = None
```

## 8. CURRENT decyzja BHP

Dla CURRENT SDS wybieraj wyłącznie:

```text
BHP_DECISION.record_status = CURRENT
```

Nie korzystaj z:
- SUPERSEDED,
- decyzji starego ARCHIVED SDS.

Brak decyzji → pola bieżącej decyzji `None`.

## 9. Dostępność plików

Dla CURRENT SDS sprawdź dostępność źródłowego PDF w `SDS_ROOT_PATH`.

Dla CURRENT BHP_DECISION sprawdź evidence w `BHP_EVIDENCE_ROOT_PATH`.

Wynik:

```text
current_sds_file_available = True/False
current_bhp_evidence_available = True/False
```

To tylko read-side. Brak pliku nie zmienia Core.

## 10. Reguły `requires_action`

Reguły mają być wyliczane poza Streamlit.

### PENDING_APPROVAL
Dodaj:
```text
BRAK DECYZJI BHP
```

### REJECTED
Dodaj:
```text
PRODUKT ODRZUCONY
```

### brak CURRENT SDS
Dodaj:
```text
BRAK CURRENT SDS
```

### brak pliku CURRENT SDS
Dodaj:
```text
BRAK PLIKU SDS
```

### brak aktywnego miejsca stosowania
Dodaj:
```text
BRAK MIEJSCA STOSOWANIA
```

### CURRENT decyzja istnieje, evidence brak
Dodaj:
```text
BRAK PLIKU DOWODU BHP
```

Na końcu:

```text
requires_action = len(action_reasons) > 0
```

## 11. Czego NIE oznaczamy jako problem

Nie dodawaj powodu tylko dlatego, że:
- PRODUCT = INACTIVE,
- monthly_consumption = NULL,
- monthly_consumption = 0,
- notes = NULL,
- brak decided_by,
- brak decision_date,
- istnieją SDS ARCHIVED,
- istnieją decyzje SUPERSEDED.

## 12. Application service

Dodaj jeden prosty use case/query service, np.:

```text
ListSupervisoryProducts
```

Odpowiedzialność:
1. pobiera dane przez port,
2. składa read model,
3. wylicza `requires_action`,
4. zwraca listę.

Bez rozbudowanej warstwy query.

## 13. Port

Dodaj jeden minimalny port, np.:

```text
SupervisoryQueryPort
```

z operacją w stylu:

```text
list_products()
```

Nie twórz osobnego portu dla każdej tabeli.

## 14. PostgreSQL adapter

Zaimplementuj jeden adapter SQLAlchemy odczytujący potrzebne dane z:

```text
PRODUCT
MANUFACTURER
PRODUCT_USAGE_LOCATION
USAGE_LOCATION
SDS
BHP_DECISION
DECISION_EVIDENCE
```

Nie pobieraj SAFETY_PROFILE/SDS_COMPONENT, bo nie są potrzebne do R7.

Uniknij oczywistego N+1, ale nie mikrooptymalizuj.

## 15. Testy reguł

Pokryj co najmniej:

1. kompletny ACTIVE → brak problemów,
2. PENDING_APPROVAL → `BRAK DECYZJI BHP`,
3. REJECTED → `PRODUKT ODRZUCONY`,
4. brak CURRENT SDS → `BRAK CURRENT SDS`,
5. brak pliku SDS → `BRAK PLIKU SDS`,
6. brak aktywnej lokalizacji → `BRAK MIEJSCA STOSOWANIA`,
7. brak evidence → `BRAK PLIKU DOWODU BHP`,
8. wiele problemów jednocześnie.

## 16. Testy PostgreSQL

Potwierdź na rzeczywistym PostgreSQL:

1. jeden PRODUCT = jeden read-model row,
2. wiele aktywnych lokalizacji nie duplikuje PRODUCT,
3. INACTIVE location nie jest liczona jako aktywna,
4. CURRENT SDS wygrywa nad ARCHIVED,
5. CURRENT decision wygrywa nad SUPERSEDED,
6. decyzja starego SDS nie jest używana dla nowego CURRENT SDS,
7. brak CURRENT SDS działa,
8. pusta baza → pusta lista,
9. dostępność SDS/evidence jest poprawnie wyliczana.

## 17. Kolejność

Zwróć stabilną kolejność, np.:

```text
product_name
manufacturer_product_code
product_id
```

Bez scoringu/rankingu ryzyka.

## 18. Brak zmian schema

TASK-026 nie zmienia:
- Domain,
- ORM models,
- PostgreSQL schema,
- Alembic.

Oczekiwane:

```text
Alembic head = e0dd7d6468bf
schema drift = none
```

Jeśli potrzeba schema change → STOP.

## 19. Brak nowych zależności

Nie dodawaj bibliotek.

## 20. Poza zakresem

Nie implementuj:
- Streamlit Widok nadzorczy,
- dashboardów/wykresów/KPI,
- alertów,
- przeglądów okresowych,
- ISSUE entity/workflow,
- scoringu,
- migracji R6,
- REACH,
- AI/LLM/OCR,
- nowych tabel/history.

## 21. STOP CONDITIONS

STOP/PARTIAL/BLOCKED, jeśli:
- potrzebna zmiana Core/schema,
- nie da się jednoznacznie wskazać CURRENT SDS,
- nie da się jednoznacznie wskazać CURRENT BHP decision dla CURRENT SDS,
- potrzebna nowa zależność,
- wymaganie zmusza do trwałego zapisu `requires_action`,
- trzeba wejść w UI.

## 22. Regression

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Wymagane:
- focused tests PASS,
- integration tests PASS,
- pełny pytest PASS,
- brak SAWarning,
- Alembic bez driftu.

## 23. Definition of Done

DONE gdy:
1. istnieje jeden prosty supervisory read model,
2. istnieje jeden query/application service,
3. istnieje minimalny query port,
4. PostgreSQL adapter składa dane z istniejącego Core,
5. jeden PRODUCT daje jeden rekord,
6. aktywne lokalizacje są zagregowane,
7. CURRENT SDS jest poprawnie wybrany,
8. CURRENT BHP decision dotyczy CURRENT SDS,
9. dostępność SDS file jest wyliczana,
10. dostępność evidence jest wyliczana,
11. `requires_action` nie jest zapisywany do DB,
12. `action_reasons` są poza Streamlit,
13. wszystkie 6 reguł działa,
14. INACTIVE samo nie tworzy problemu,
15. wiele problemów może współistnieć,
16. pusta baza działa,
17. brak zmian Domain/schema/Alembic,
18. brak nowych zależności,
19. focused tests PASS,
20. PostgreSQL integration tests PASS,
21. pełna regresja PASS,
22. brak SAWarning,
23. Alembic bez driftu,
24. TASK-027 nie został rozpoczęty.

## 24. Raport

Utwórz:

```text
docs/task_reports/TASK-026_REPORT.md
```

Raport: status, zmienione pliki, read model, service, port, PostgreSQL adapter, agregacja lokalizacji, CURRENT SDS/BHP, dostępność plików, reguły, focused tests, integration tests, pełny pytest, SAWarning, Alembic current/check, brak schema changes, Git/bezpieczeństwo, odstępstwa/ryzyka.

Zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-027.
```

## 25. Autoryzacja

Start dopiero po poleceniu:

```text
Wykonaj TASK-026.
```
