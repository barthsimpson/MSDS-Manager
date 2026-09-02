# TASK-009-ALIGN — UsageLocation Core v1.2 Alignment

**Projekt:** MSDS Manager  
**Task ID:** TASK-009-ALIGN  
**Powiązanie:** corrective/alignment task dla zablokowanego TASK-009  
**Sprint:** SPRINT-002 v1.2-approved  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

## 1. Cel

Wyrównać implementację z `CORE-001 v1.2-approved` oraz `BDR-002 v1.2-approved` wyłącznie w obszarze `USAGE_LOCATION`, aby usunąć blocker TASK-009.

Sekwencja:

```text
Domain
→ ORM
→ Alembic
→ PostgreSQL
→ tests
```

Po akceptacji tego Tasku należy **wznowić ten sam TASK-009**. Nie rozpoczynać TASK-010.

## 2. Stan wejściowy

Po TASK-008:

```text
Alembic revisions: 3
PostgreSQL head: c41d8e2f7a90
Application tables: 9
Tests: 59 passed
Schema drift: none
```

TASK-009 został prawidłowo zatrzymany na braku zatwierdzonej semantyki `USAGE_LOCATION.status`.

## 3. Źródła nadrzędne

1. `CORE-001 v1.2-approved`
2. `BDR-002 v1.2-approved`
3. `SPRINT-002 v1.2-approved`
4. `TDR-001`, `TDR-003`
5. zaakceptowany TASK-008
6. raport BLOCKED z TASK-009
7. root `AGENTS.md`

Potrzeba decyzji poza tym zakresem = STOP.

## 4. Zakres Domain

Utwórz osobny enum domenowy:

```text
UsageLocationStatus
├── ACTIVE
└── INACTIVE
```

Nie używaj `ProductUsageStatus`.

Zaktualizuj `UsageLocation.status`, aby korzystał z `UsageLocationStatus`.

Reguły:

```text
nowa lokalizacja → ACTIVE
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Nie dodawaj innych statusów.

Nie implementuj historii.

## 5. Zakres ORM

Zaktualizuj ORM `UsageLocation`:

- status odwzorowuje `UsageLocationStatus`,
- wartości przechowywane jako zatwierdzony model `VARCHAR + CHECK`, zgodnie z istniejącym stylem enumów projektu,
- wartości wyłącznie `ACTIVE`, `INACTIVE`.

Nie zmieniaj innych modeli ORM.

## 6. PostgreSQL

Dodaj constraint zapewniający:

```text
usage_locations.status IN ('ACTIVE', 'INACTIVE')
```

Nowa lokalizacja powinna otrzymywać `ACTIVE` przez zatwierdzoną logikę Domain/Application; nie dodawaj niezatwierdzonego mechanizmu DB default, jeśli nie jest potrzebny do zgodności z aktualną architekturą.

Nie twórz nowych tabel.

## 7. Migracja Alembic

Utwórz dokładnie jedną nową rewizję po:

```text
c41d8e2f7a90
```

Stan końcowy:

```text
Alembic revisions: 4
Application tables: 9
Current: new TASK-009-ALIGN revision (head)
```

Migracja może zmienić wyłącznie `usage_locations.status` i związany z nim constraint.

Nie może zmieniać:

- PRODUCT,
- PRODUCT_USAGE_LOCATION,
- SDS,
- BHP,
- SafetyProfile,
- SdsComponent,
- constraints TASK-006,
- quantity constraints TASK-008,
- innych enumów.

## 8. Review migracji

Przed `upgrade head` przeczytaj wygenerowaną migrację.

Nieoczekiwane zmiany = STOP.

Znane false positives innych enumowych CHECK-ów nie mogą zostać zastosowane.

## 9. Testy Domain

Potwierdź:

1. nowa `UsageLocation` ma `ACTIVE`,
2. `ACTIVE → INACTIVE` działa,
3. `INACTIVE → ACTIVE` działa,
4. nie istnieje trzeci status,
5. `UsageLocationStatus` jest osobnym enumem od `ProductUsageStatus`.

Nie projektuj historii zmian statusu.

## 10. Testy PostgreSQL

Na realnym PostgreSQL potwierdź:

1. `ACTIVE` jest akceptowane,
2. `INACTIVE` jest akceptowane,
3. inna wartość statusu jest odrzucana,
4. brak regresji istniejących constraintów.

Testy nie pozostawiają danych.

## 11. Ochrona bieżącej analityki

TASK-009-ALIGN **nie implementuje jeszcze query filtering ani application use cases**.

Nie dodawaj w tym Tasku:

- filtrów listy tylko ACTIVE,
- CreateUsageLocation use case,
- DeactivateUsageLocation,
- ReactivateUsageLocation,
- assignment rules.

Te kontrakty należą do wznowionego TASK-009.

TASK-009-ALIGN jedynie przygotowuje poprawny Domain/ORM/PostgreSQL.

## 12. Ochrona historii

Nie twórz:

- history tables,
- audit tables,
- event log,
- temporal tables,
- triggerów historycznych,
- snapshotów,
- created_by/updated_by.

Historia pozostaje poza zakresem do osobnej decyzji przed TASK-015.

## 13. Pełna regresja

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie istniejące testy i nowe testy muszą przejść.

## 14. Upgrade / downgrade / re-upgrade

Przetestuj:

```text
c41d8e2f7a90
    ↓ upgrade
TASK-009-ALIGN head
    ↓ downgrade -1
c41d8e2f7a90
    ↓ re-upgrade
TASK-009-ALIGN head
```

Po każdej operacji potwierdź 9 tabel.

## 15. Drift

Po finalnym re-upgrade:

```powershell
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwany brak rzeczywistego driftu.

## 16. Poza zakresem

Nie implementuj:

- TASK-009 application contracts,
- repozytoriów TASK-010,
- UI,
- CreateProduct,
- CreateManufacturer,
- SDS workflow,
- BHP,
- historii,
- modułu odpadów,
- nowych bibliotek.

## 17. STOP

Zatrzymaj Task jako `PARTIAL/BLOCKED`, jeśli:

- zmiana wymaga czegoś poza `USAGE_LOCATION.status`,
- autogenerate proponuje inne zmiany schema,
- potrzebna jest nowa decyzja statusowa,
- potrzebny jest mechanizm historii,
- potrzebna jest nowa biblioteka,
- trzeba zmienić inny Core.

## 18. Kryteria akceptacji

TASK-009-ALIGN = DONE, jeśli:

1. istnieje osobny `UsageLocationStatus`,
2. zawiera tylko `ACTIVE`, `INACTIVE`,
3. nie korzysta z `ProductUsageStatus`,
4. `UsageLocation.status` używa nowego enuma,
5. nowa lokalizacja ma semantykę `ACTIVE`,
6. Domain wspiera `ACTIVE ↔ INACTIVE`,
7. ORM jest zgodny,
8. PostgreSQL wymusza wyłącznie `ACTIVE/INACTIVE`,
9. istnieje dokładnie jedna nowa migracja,
10. `down_revision = c41d8e2f7a90`,
11. nadal jest 9 tabel,
12. constraints TASK-006/TASK-008 są zachowane,
13. wszystkie inne enumowe CHECK-i są zachowane,
14. upgrade działa,
15. downgrade -1 działa,
16. re-upgrade działa,
17. brak rzeczywistego driftu,
18. pełna regresja przechodzi bez `SAWarning`,
19. brak danych testowych,
20. brak historii,
21. brak application contracts TASK-009,
22. TASK-010 nie został rozpoczęty.

## 19. Raport

Utwórz:

```text
docs/task_reports/TASK-009-ALIGN_REPORT.md
```

Raport zawiera:

1. Status.
2. Stan wejściowy.
3. Zmiany Domain.
4. Zmiany ORM.
5. Revision id i `down_revision`.
6. Review migracji.
7. Constraint `USAGE_LOCATION.status`.
8. Ochronę wcześniejszych constraints.
9. Testy Domain.
10. Testy PostgreSQL.
11. Pełną regresję.
12. Upgrade/downgrade/re-upgrade.
13. Alembic current/check.
14. Finalny stan PostgreSQL.
15. Git/bezpieczeństwo.
16. Odstępstwa.
17. Problemy/ryzyka.
18. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE WZNAWIAM TASK-009.
NIE ROZPOCZYNAM TASK-010.
```

## 20. Autoryzacja

Obecność pliku w `docs/tasks/` nie stanowi zgody na wykonanie.

Rozpocznij dopiero po jawnym poleceniu:

```text
Wykonaj TASK-009-ALIGN.
```
