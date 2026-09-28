# TASK-032 — UI MVP Acceptance / Checkpoint

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Task ID:** TASK-032  
**MODE:** ACCEPTANCE  
**VALIDATION:** LEVEL 3  
**REPORT:** FULL  
**Status:** READY  
**Wykonawca:** Codex OpenAI

---

## GOAL

Wykonać końcowy checkpoint SPRINT-006 i odpowiedzieć jednoznacznie:

> Czy operacyjny UI MVP działa spójnie end-to-end, nie narusza Core/schema i jest gotowy do formalnego zamknięcia Sprintu?

TASK-032 jest Taskiem walidacyjnym.

Nie dodaje nowych funkcji.

Nie poprawia znalezionych defektów.

Jeżeli acceptance ujawni defekt:

```text
STOP
→ raport
→ decyzja Architekta Operacyjnego
```

Bez opportunistic fixes.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `SPRINT-006_UI_MVP_v1.0-approved.md`,
- ten TASK,
- raporty:
  - `TASK-029_REPORT.md`,
  - `TASK-030_REPORT.md`,
  - `TASK-031_REPORT.md`,
- istniejące testy acceptance/integration dla:
  - PRODUCT + usage,
  - SDS,
  - BHP,
  - supervisory read model,
  - Streamlit shell/UI.

Nie czytaj ponownie całego CORE/BDR/TDR/history bez konkretnej potrzeby.

Jeżeli test ujawni możliwą sprzeczność domenową, dopiero wtedy rozszerz kontekst o bezpośrednio właściwy zatwierdzony BDR/TDR.

---

## KNOWN STARTING POINTS

### UI / composition

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/add_sds.py
app/presentation/streamlit/bhp_decision.py
app/presentation/streamlit/supervisory.py
app/presentation/streamlit/composition.py
```

### Supervisory read-side

```text
app/application/dto/supervisory.py
app/application/use_cases/list_supervisory_products.py
app/infrastructure/db/repositories/supervisory_query.py
```

### Existing acceptance/integration

W pierwszej kolejności wykorzystaj istniejące:

```text
tests/integration/test_task016_acceptance.py
tests/integration/test_task021_sprint3_acceptance.py
testy acceptance BHP / Sprint 4
tests/integration/test_task026_supervisory_read_model_postgresql.py
testy Streamlit TASK-029/030/031
scripts/verify_task026.py
```

Nazwy mogą różnić się w repo dla BHP / Streamlit — użyj istniejących plików.

Nie twórz drugiego frameworka acceptance.

---

# 1. ZASADA CHECKPOINTU

TASK-032 ma przede wszystkim:

```text
uruchomić
zweryfikować
udokumentować
```

a nie rozwijać.

Dopuszczalne zmiany w repo:

```text
docs/task_reports/TASK-032_REPORT.md
```

oraz **wyłącznie jeśli naprawdę potrzebne do pokrycia brakującego scenariusza acceptance**:

```text
tests/integration/test_task032_ui_mvp_acceptance.py
```

Preferuj reuse istniejących testów.

Nie zmieniaj production code w TASK-032.

---

# 2. OCHRONA DANYCH OPERATORA

Lokalna baza może zawierać rzeczywiste / ręcznie wprowadzone dane operatora.

Acceptance:

- nie usuwa danych operatora,
- nie resetuje bazy roboczej,
- nie "czyści" istniejących produktów,
- nie nadpisuje rzeczywistych SDS/BHP,
- nie wykorzystuje nazw istniejących produktów jako fixture,
- nie zakłada pustej bazy roboczej.

Jeżeli test wymaga pustej / kontrolowanej bazy:

```text
użyj istniejącego mechanizmu izolacji
tymczasowego PostgreSQL
transakcji + rollback
lub sprawdzonego fixture acceptance
```

zgodnie z wcześniejszymi checkpointami.

**Nie obchodź testu przez usuwanie danych użytkownika.**

---

# 3. ZNANY STAN TESTOWY OPERATORA

Podczas fizycznego walkthrough użytkownik świadomie zmieniał dane XBRAKE CLEANER, m.in. przypinał testowy SDS jako CURRENT.

TASK-032:

```text
NIE naprawia tego stanu automatycznie
NIE usuwa go
NIE nadpisuje
NIE używa jako fixture acceptance
```

Acceptance automatyczny musi być niezależny od tego stanu.

W raporcie można odnotować:

```text
operator DB contains manual walkthrough data — preserved
```

Jeżeli przed formalnym Sprint Review Architekt Operacyjny będzie chciał przywrócić dane produkcyjne, jest to osobne jawne działanie operacyjne.

---

# 4. ACCEPTANCE — GŁÓWNE WORKFLOW

Zweryfikuj co najmniej poniższe ścieżki.

## A. Product register

Potwierdź:

```text
Produkty
→ tabela first
→ brak UUID w normalnym widoku
→ wybór wiersza
→ szczegóły produktu
```

Akcje istnieją:

```text
Edytuj dane produktu
Dodaj nową rewizję SDS
Usuń produkt
```

Nie wykonuj destrukcyjnych operacji na danych operatora.

---

## B. First SDS

Scenariusz kontrolowany:

```text
PDF SDS
→ Odczytaj dane lub manual fallback
→ formularz
→ ręczna korekta
→ Zapisz / Akceptuj
```

Potwierdź:

```text
PRODUCT powstaje
CURRENT SDS powstaje
PRODUCT = PENDING_APPROVAL
brak częściowego zapisu przy błędzie
PDF nie jest modyfikowany
```

Chemia:

```text
Safety Profile / Components
→ opcjonalne
→ nie blokują głównego workflow
```

Parser nie jest celem jakościowym checkpointu poza potwierdzeniem, że nie blokuje manual fallback.

---

## C. New SDS revision

Dla kontrolowanego PRODUCT:

```text
CURRENT S1
→ Dodaj nową rewizję S2
```

Potwierdź:

```text
product_id unchanged
S1 → ARCHIVED
S2 → CURRENT
PRODUCT → PENDING_APPROVAL
usage locations preserved
previous BHP not inherited
```

oraz:

```text
nieznana issue_date pozostaje None
nie jest zastępowana datą systemową
```

---

## D. BHP decision

Dla:

```text
PRODUCT = PENDING_APPROVAL
CURRENT SDS
```

potwierdź:

```text
evidence required
APPROVED → PRODUCT ACTIVE
REJECTED → PRODUCT REJECTED
CURRENT/SUPERSEDED działa
evidence pozostaje referencją źródłową
```

UI po zapisie musi odczytać rzeczywisty nowy stan bez ręcznego refreshu.

---

## E. Product identity correction

Potwierdź na fixture:

```text
edit product_name
edit manufacturer_product_code
edit manufacturer
```

Oczekiwane:

```text
product_id unchanged
SDS preserved
BHP preserved
usage preserved
```

---

## F. Safe delete

Na **disposable fixture**:

```text
Usuń produkt
→ warning
→ explicit confirmation
→ DB delete
```

Potwierdź:

```text
dependent DB records removed
shared dictionaries preserved
SDS source file remains
BHP evidence file remains
no single historical SDS delete
```

Nie testuj na danych operatora.

---

## G. Usage locations

Potwierdź:

```text
existing assignments table
+ Dodaj miejsce stosowania
select existing row
→ Edytuj przypisanie
```

Ilości:

```text
peak >= 0
monthly None != 0
```

UI:

```text
Maksymalna ilość na stanowisku
Jednostka
Zużycie miesięczne
Jednostka
```

Nie testuj DATA-01 — słownik jednostek jest poza Sprintem.

---

## H. Supervisory view

Potwierdź read model:

```text
1 PRODUCT × 1 active LOCATION = 1 row
```

Dla produktu z 2 lokalizacjami:

```text
2 rows
```

Dla produktu bez aktywnej lokalizacji:

```text
1 row
Lokalizacja = Brak
```

Wiersz pokazuje:

```text
peak
monthly
CURRENT SDS
Data SDS
Rewizja
PRODUCT status
BHP
notes
action reasons
```

Potwierdź:

```text
None → —
0 → 0
```

Filtry:

```text
Szukaj produktu
Status produktu
Lokalizacja
BHP
Wszystkie / Wymagają działania
```

Widok pozostaje read-only.

---

# 5. UI ACCEPTANCE

Potwierdź zasady całego Sprintu:

```text
wide layout
table-first
business data first
UUID hidden in normal workflow
compact forms
required fields visible
actions tied to selected record
no stale state
technical filesystem paths not dominant
```

Sprawdź co najmniej:

```text
Produkty
Dodaj SDS
Decyzja BHP
Widok nadzorczy
```

---

# 6. EMPTY / NO_DATA STATES

Potwierdź kontrolowane zachowanie dla:

```text
brak produktów
brak CURRENT SDS
brak BHP decision
brak usage location
brak issue_date
brak revision
brak monthly consumption
brak evidence file
brak SDS source file
```

Nie każda sytuacja musi być tworzona w jednym E2E, jeśli jest już pokryta przez istniejące integration/AppTests.

Checkpoint ma jednak wykazać, że pełny zestaw testów obejmuje te stany.

---

# 7. FULL REGRESSION — LEVEL 3

Uruchom pełny pytest.

Preferowane środowisko Windows projektu:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:

```text
0 failed
0 errors
SAWarning = NONE
```

### Skips

Skip jest dopuszczalny tylko wtedy, gdy:

- jest jawnie istniejącym, kontrolowanym warunkiem testu,
- nie ukrywa awarii,
- jego przyczyna jest opisana w raporcie.

Jeżeli test jest skipowany wyłącznie dlatego, że baza operatora nie jest pusta:

```text
uruchom właściwy istniejący wariant izolowany
```

Nie uznawaj lokalnie zabrudzonej bazy za powód do pominięcia wymaganej walidacji acceptance.

---

# 8. E2E

Uruchom istniejące E2E dla:

```text
Sprint 2 — product/usage
Sprint 3 — SDS
Sprint 4 — BHP
R7 — supervisory
```

Jeżeli pełny pytest już uruchamia je poprawnie, nie duplikuj bez potrzeby.

Jeżeli potrzebny jest jeden dodatkowy scenariusz SPRINT-006:

```text
PRODUCT
→ SDS
→ BHP
→ usage locations
→ supervisory PRODUCT × LOCATION
```

można dodać jeden minimalny acceptance test.

Nie twórz dużego nowego frameworka E2E.

---

# 9. POSTGRESQL / SCHEMA INTEGRITY

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
current = head
No new upgrade operations detected.
```

Nie hardkoduj historycznego revision id jako warunku, jeżeli repo posiada nowszy prawidłowy head.

Sprawdź:

```text
ORM ↔ schema drift = NONE
```

oraz istniejące krytyczne constraints, co najmniej:

```text
one CURRENT SDS per product
one CURRENT BHP decision per SDS
PRODUCT/SDS relation integrity
BHP PRODUCT/SDS relation integrity
usage quantity constraints
history integrity
```

Nie zmieniaj schema.

---

# 10. TRANSACTION / CLEANUP

Acceptance fixtures muszą być:

```text
unikalne
kontrolowane
usunięte / rollback
```

Po E2E:

```text
brak orphan fixture
brak orphan evidence metadata
brak orphan SDS/component/profile
brak testowych PRODUCT/locations/manufacturers
```

Nie usuwaj fizycznych plików operatora.

Tymczasowe pliki stworzone przez test można usunąć w cleanup.

---

# 11. ARCHITECTURE CHECK

Potwierdź, że po Sprint 006 nadal obowiązuje:

```text
presentation
→ application
→ domain
→ infrastructure adapters
```

UI nie:

- wykonuje SQL,
- importuje ORM,
- wykonuje commit/rollback,
- definiuje lifecycle SDS/BHP,
- wylicza `requires_action`,
- analizuje evidence,
- implementuje parser.

Nie rozszerzaj architektury podczas checkpointu.

---

# 12. GIT / SECURITY CHECK

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:

```text
.env ignored / untracked
brak sekretów
brak dumpów / backupów
brak niezamierzonych PDF/MSG
brak nowych dependencies
brak commit/push bez polecenia
```

Zastane zmiany użytkownika / wcześniejszych Tasków zachowaj.

Nie resetuj working tree.

---

# 13. SPRINT-006 DEFINITION OF DONE

Raport ma jawnie ocenić każdy punkt:

1. wide/compact layout,
2. Products table-first,
3. UUID hidden,
4. Add SDS compact sections,
5. required fields visible,
6. unknown SDS date not defaulted to today,
7. BHP state refresh after save,
8. usage assignments table + separate add/edit,
9. supervisory PRODUCT × LOCATION,
10. peak/monthly visible per location,
11. product without location preserved,
12. filters work,
13. no Core/schema changes,
14. full validation PASS,
15. physical Sprint Review remains for Architekt Operacyjny.

---

# 14. KNOWN BACKLOG — NOT A FAILURE OF SPRINT-006

Nie uznawaj za defekt checkpointu braku funkcji świadomie odłożonych:

```text
UI-11 — otwieranie/pobieranie CURRENT SDS z tabeli
DATA-01 — słownik jednostek miary
UI-12 — nazwa "Data wystawienia SDS"
UI-13 — rewizja SDS w głównej tabeli Produkty
DOC-01 — dodawanie SDS z komputera
UI-14 / DOC-02 — podgląd dowodu BHP
Stage 2 — parser / automatyczna analiza SDS
R8 — przeglądy okresowe
REACH
```

Można je wymienić w raporcie jako backlog po MVP.

Nie implementuj ich.

---

# 15. EXPECTED CHANGE SURFACE

Preferowany:

```text
docs/task_reports/TASK-032_REPORT.md
```

Opcjonalnie, tylko jeśli istniejące testy nie pokrywają jednego koniecznego scenariusza:

```text
tests/integration/test_task032_ui_mvp_acceptance.py
```

### DO NOT TOUCH

```text
app/**
migrations/**
pyproject.toml
Core docs
BDR/TDR
```

Jeżeli acceptance nie może zostać wykonany bez zmiany production code:

```text
STOP / BLOCKED
```

---

# 16. ACCEPTANCE RESULT

Dozwolone końcowe statusy:

```text
DONE — READY FOR SPRINT-006 CLOSURE
```

albo:

```text
BLOCKED — SPRINT-006 NOT READY FOR CLOSURE
```

Nie używaj:

```text
DONE WITH FIXES
```

bo checkpoint nie naprawia.

---

# 17. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. jakikolwiek krytyczny workflow E2E FAIL,
2. full pytest FAIL,
3. pojawia się `SAWarning`,
4. Alembic nie jest na head,
5. `alembic check` wykrywa drift,
6. schema/integrity jest niespójna,
7. fixture cleanup pozostawia dane,
8. acceptance wymaga zmiany production code,
9. Core/schema zmieniły się poza zatwierdzonym zakresem,
10. trzeba zgadywać decyzję biznesową,
11. test można przeprowadzić tylko przez usunięcie danych operatora.

Nie poprawiaj defektu.

Zgłoś go.

---

# 18. REPORT — FULL

Utwórz:

```text
docs/task_reports/TASK-032_REPORT.md
```

Minimalna struktura:

```text
# TASK-032 REPORT

STATUS:
DONE — READY FOR SPRINT-006 CLOSURE
lub
BLOCKED — SPRINT-006 NOT READY FOR CLOSURE

BASELINE:
- git status:
- operator data preserved:
- test isolation:

SPRINT-006 WORKFLOW ACCEPTANCE:
- product register:
- product details:
- first SDS:
- manual fallback:
- new SDS revision:
- BHP decision:
- product status refresh:
- product correction:
- safe delete:
- usage locations:
- peak/monthly:
- supervisory PRODUCT x LOCATION:
- filters:

UI ACCEPTANCE:
- wide layout:
- table-first:
- UUID hidden:
- compact forms:
- required fields visible:
- no stale state:
- technical paths secondary:

NO_DATA / ERROR STATES:
- ...

FULL VALIDATION:
- pytest:
- SAWarning:
- E2E:
- PostgreSQL integration:
- Alembic current:
- Alembic check:
- schema drift:
- constraints/integrity:
- cleanup:

ARCHITECTURE:
- Streamlit SQL/ORM: NONE
- lifecycle in UI: NONE
- Core change: NONE
- schema change: NONE
- dependencies: NONE

GIT / SECURITY:
- git diff check:
- .env:
- secrets:
- unintended PDF/MSG/dumps:
- commit/push:

SPRINT-006 DoD:
1. ...
...
15. ...

KNOWN BACKLOG — NOT BLOCKING:
- UI-11
- DATA-01
- UI-12
- UI-13
- DOC-01
- UI-14 / DOC-02
- Stage 2 parser
- R8
- REACH

RISKS / DEVIATIONS:
- ...

CLOSURE RECOMMENDATION:
READY FOR CERBERUS + ARCHITEKT OPERACYJNY REVIEW
lub
NOT READY — <reason>

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO SPRINTU.
```

---

# AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-032.
```
