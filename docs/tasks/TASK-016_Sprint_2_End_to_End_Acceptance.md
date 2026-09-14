# TASK-016 — Sprint 2 End-to-End Acceptance

**Projekt:** MSDS Manager
**Task ID:** TASK-016
**Sprint:** SPRINT-002 v1.2-approved
**Status:** READY
**Typ:** Acceptance / E2E / Sprint Closure Candidate
**Nadzór:** Cerberus — Agent Architekt
**Wykonawca:** Codex OpenAI

## 1. Cel

Przeprowadzić końcową walidację Sprintu 2 jako jednego działającego przyrostu:

`Streamlit → Application → Infrastructure → PostgreSQL`

TASK-016 jest przede wszystkim Taskiem walidacyjnym. Nie rozwija nowych funkcji. Ma potwierdzić współdziałanie TASK-008..015 zgodnie z `SPRINT-002 v1.2-approved`.

Pozytywny wynik jest podstawą do decyzji Cerberusa / Architekta Operacyjnego o zamknięciu Sprintu 2.

## 2. Źródła

Przed wykonaniem przeczytaj:
- `SPRINT-002 v1.2-approved` — nadrzędne kryteria Sprintu,
- `CORE-001 v1.2-approved`,
- `BDR-002 v1.2-approved`,
- `TDR-004 v1.0-approved`,
- root `AGENTS.md`,
- raporty zaakceptowanych TASK-008..015.

W razie konfliktu lub potrzeby nowej decyzji: **STOP. Nie zgaduj.**

## 3. Zasada TASK-016

Preferowany wynik:

`0 zmian produkcyjnych + test/scenariusz E2E + raport acceptance`

Drobny jednoznaczny defekt można naprawić tylko, gdy korekta nie zmienia Core, semantyki, schema ani zakresu Sprintu. Każdą korektę opisz w raporcie.

Nowa funkcja / decyzja / schema / migracja → `BLOCKED / STOP`.

## 4. Baseline

Przed E2E:
1. `git status --short`
2. `alembic current`
3. `alembic check`
4. potwierdź schema PostgreSQL,
5. pełny pytest z `SAWarning` jako error,
6. potwierdź brak pozostawionych danych testowych.

Uwzględnij znane wymaganie sesji Windows:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
```

Oczekiwany stan po TASK-015:
- head `e0dd7d6468bf`,
- 12 tabel (9 Core + 3 history),
- brak driftu,
- baseline regresji: 99 testów.

Rozbieżności wyjaśnij, nie maskuj.

## 5. Fixture E2E

Sprint 2 nie posiada publicznego `CreateProduct` ani `CreateManufacturer`.

Kontrolowany MANUFACTURER i PRODUCT utwórz wyłącznie w setupie/fixture testu. Nie może to stać się:
- funkcją użytkownika,
- use case'em CreateProduct,
- przyciskiem UI,
- trwałym seedem,
- obejściem przyszłego workflow SDS.

Po scenariuszu dane testowe mają zostać usunięte/rollbackowane.

## 6. Główny scenariusz E2E

### A. Setup
Utwórz kontrolowany MANUFACTURER i PRODUCT technicznie w fixture. Nie wyprowadzaj z fixture nowej reguły biznesowej.

### B. Start
Potwierdź start Streamlit z rzeczywistą konfiguracją i PostgreSQL. Streamlit AppTest lub równoważny test automatyczny jest dopuszczalny, jeśli wiarygodnie realizuje przepływ.

### C. Rejestr produktu
Potwierdź:
- produkt na liście,
- wybór po `product_id`,
- szczegóły,
- producent,
- status,
- widoczna i chroniona tożsamość.

### D. Administracja PRODUCT
Przez istniejący workflow zmień:
- `use_description`,
- `use_restriction`,
- `waste_type`,
- `waste_code`.

Potwierdź:
- odczyt nowych wartości,
- trwałość PostgreSQL,
- brak zmiany identity,
- brak niezatwierdzonej zmiany `usage_status`,
- właściwy snapshot `PRODUCT_HISTORY`.

### E. UsageLocation
Utwórz co najmniej 2 lokalizacje istniejącym workflow. Potwierdź ACTIVE i różne `location_id`.

### F. Assignments i quantities
Przypisz PRODUCT do obu ACTIVE locations.

Scenariusz łącznie ma objąć:
- peak > 0,
- peak = 0,
- monthly = NULL,
- monthly = 0.

Potwierdź current state, prezentację w szczegółach oraz initial snapshots `PRODUCT_USAGE_LOCATION_HISTORY`. Bez konwersji jednostek.

### G. Quantity update
Zmień quantities jednego przypisania. Potwierdź:
- nowy current state,
- zachowany poprzedni snapshot,
- nowy snapshot,
- kolejność `changed_at`, `history_id`,
- Decimal,
- NULL != 0,
- brak konwersji.

### H. Deactivate
Jedną przypisaną lokalizację zmień `ACTIVE → INACTIVE`.

Potwierdź:
- ten sam `location_id`,
- current INACTIVE,
- snapshot historii,
- brak dostępności do nowego przypisania,
- brak fizycznego DELETE,
- brak usunięcia istniejącej relacji.

### I. Reactivate
Wykonaj `INACTIVE → ACTIVE`.

Potwierdź ten sam `location_id`, current ACTIVE, kolejny snapshot i ponowną dostępność zgodnie z istniejącymi regułami.

### J. Odczyt końcowy
Ponownie odczytaj PRODUCT przez istniejące Application/UI i potwierdź admin data, manufacturer, status, obie lokalizacje, quantities, 0/NULL i jednostki.

## 7. Acceptance historii

Na rzeczywistym PostgreSQL potwierdź:
- `PRODUCT_HISTORY`: snapshot po admin update,
- `USAGE_LOCATION_HISTORY`: INACTIVE i ACTIVE dla tego samego location_id,
- `PRODUCT_USAGE_LOCATION_HISTORY`: initial snapshot i kolejny po quantity update,
- wcześniejsze snapshoty niezmienione,
- deterministyczne sortowanie.

TASK-016 nie dodaje pełnego UI historii.

## 8. PostgreSQL jako źródło prawdy

Nie kończ acceptance na UI. Potwierdź rzeczywisty stan PostgreSQL przez istniejące repozytoria/testy integracyjne lub kontrolowane zapytania testowe:

`UI/Application state = PostgreSQL current state = expected history`

Nie dodawaj SQL do Streamlit.

## 9. Transakcje

Wszystkie write operations mają przechodzić przez istniejący `TransactionExecutor`.

UI nie wykonuje SQL, commit ani rollback.

Pełna regresja musi nadal obejmować testy atomicity z TASK-015.

## 10. Cleanup

Po E2E usuń/rollbackuj wyłącznie fixture techniczne. Nie twórz publicznych delete use case'ów.

Jawnie potwierdź finalny brak fixture TASK-016 w bazie.

## 11. DoD Sprintu 2

W raporcie oznacz każdy punkt `PASS / FAIL / NOT VERIFIED`:

1. lista istniejących produktów,
2. szczegóły produktu,
3. producent,
4. ochrona tożsamości,
5. edycja danych administracyjnych,
6. waste_type / waste_code,
7. osobny słownik stanowisk,
8. dodawanie / dezaktywacja stanowiska,
9. przypisanie produktu do wielu stanowisk,
10. peak_quantity >= 0,
11. opcjonalne monthly_consumption >= 0,
12. semantyka 0 / NULL,
13. UI nie omija Application,
14. PostgreSQL jest źródłem operacyjnym,
15. historia istotnych zmian,
16. testy przechodzą,
17. E2E przechodzi na kontrolowanych danych,
18. brak publicznego CreateProduct,
19. nie rozpoczęto SDS/BHP/AI/REACH.

Codex nie zamyka Sprintu samodzielnie.

## 12. Regression

Po E2E:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane: wszystkie testy PASS i brak SAWarning. Nie osłabiaj wcześniejszych testów.

## 13. Alembic / schema

TASK-016 nie powinien wymagać migracji.

Potwierdź:
- `alembic current = e0dd7d6468bf (head)`,
- `alembic check = No new upgrade operations detected.`,
- 12 tabel,
- brak nowej rewizji,
- brak driftu.

Potrzeba schema/migracji → **STOP**.

## 14. Architektura

Potwierdź:
- presentation → application → domain,
- infrastructure implementuje application ports,
- Streamlit bez ORM/SQL/commit/rollback,
- Domain bez infrastructure/SQLAlchemy,
- Application bez infrastructure,
- repositories bez commit per method.

## 15. Git / bezpieczeństwo

Sprawdź:
- `git status --short`,
- `git diff --check`,
- `git diff --cached --check`,
- `.env` ignored/untracked,
- brak sekretów i pełnego DATABASE_URL,
- brak dumpów/backupów/PDF/MSG,
- brak nowych bibliotek,
- brak commit/push bez polecenia,
- brak trwałego seeda.

## 16. Poza zakresem

Nie implementuj:
- CreateProduct / CreateManufacturer,
- Dodaj nowy SDS / SDS workflow / PDF extraction / duplicate workflow,
- SAFETY_PROFILE / SDS_COMPONENT,
- BHP,
- PENDING_APPROVAL → ACTIVE/REJECTED,
- REACH / AI,
- import Excel,
- waste module / BDO,
- RemoveProductUsageLocation / DeleteUsageLocation,
- generic audit / nowy history framework,
- barcode / review workflow.

Nie przygotowuj fundamentu R4 „przy okazji”.

## 17. STOP CONDITIONS

`PARTIAL / BLOCKED`, jeśli:
- brakuje zatwierdzonej funkcji wymaganej przez DoD,
- potrzebna jest zmiana Core/BDR/TDR,
- potrzebny jest nowy publiczny use case,
- potrzebna jest schema/migracja,
- potrzebny jest nowy status/enum,
- PRODUCT trzeba tworzyć poza fixture,
- trzeba wejść w SDS/BHP,
- defektu nie da się naprawić bez rozszerzenia zakresu.

## 18. Definition of Done TASK-016

DONE tylko gdy:
1. baseline zielony,
2. PRODUCT/MANUFACTURER istnieją tylko w fixture,
3. aplikacja startuje,
4. list/details działają,
5. identity chronione,
6. admin edit działa,
7. 2 UsageLocations można utworzyć i przypisać,
8. quantities zgodne z Core,
9. 0/NULL zachowane,
10. deactivate/reactivate na tym samym location_id,
11. current potwierdzony w PostgreSQL,
12. PRODUCT_HISTORY potwierdzona,
13. USAGE_LOCATION_HISTORY potwierdzona,
14. PRODUCT_USAGE_LOCATION_HISTORY potwierdzona,
15. snapshoty nie są nadpisywane,
16. pełny pytest bez SAWarning,
17. architektura zgodna,
18. Alembic `e0dd7d6468bf (head)`,
19. alembic check bez driftu,
20. 12 tabel,
21. brak nowej migracji,
22. fixture usunięte,
23. brak nowych zależności,
24. brak publicznego CreateProduct/CreateManufacturer,
25. nie rozpoczęto R4/SDS,
26. wszystkie punkty DoD Sprintu 2 = PASS.

## 19. Raport

Utwórz `docs/task_reports/TASK-016_REPORT.md`.

Raport zawiera:
- DONE/PARTIAL/BLOCKED,
- baseline,
- zmienione pliki i ewentualne production-code changes,
- fixture,
- przebieg E2E,
- dowód Streamlit → Application → PostgreSQL,
- admin edit,
- 2 locations + assignments,
- peak/monthly z 0/NULL,
- deactivate/reactivate,
- current PostgreSQL,
- trzy obszary historii,
- cleanup,
- pełny pytest + SAWarning,
- architekturę,
- alembic current/check,
- liczbę rewizji/tabel,
- Git/bezpieczeństwo,
- tabelę 19 punktów DoD Sprintu,
- odstępstwa/ryzyka,
- rekomendację `READY FOR SPRINT-002 CLOSURE` albo `NOT READY FOR SPRINT-002 CLOSURE`.

Codex nie podejmuje formalnej decyzji o zamknięciu Sprintu.

## 20. Autoryzacja

Sama obecność pliku nie oznacza zgody na wykonanie.

Start dopiero po poleceniu:

`Wykonaj TASK-016.`

Po wykonaniu:

`OCZEKUJĘ NA JAWNE POLECENIE.`  
`NIE ROZPOCZYNAM R4 ANI WORKFLOW SDS.`
