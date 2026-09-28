# CHECKPOINT-006 — SPRINT-006 UI MVP CLOSED

**Projekt:** MSDS Manager  
**Checkpoint ID:** CHECKPOINT-006  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Status:** CLOSED  
**Data zamknięcia:** 2026-09-28  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

---

## 1. Decyzja

SPRINT-006 zostaje formalnie zamknięty.

Status końcowy:

```text
SPRINT-006
OPERACYJNY UI MVP
STATUS: CLOSED
```

Podstawa zamknięcia:

```text
TASK-029 — ACCEPTED / CLOSED
TASK-030 — ACCEPTED / CLOSED
TASK-031 — ACCEPTED / CLOSED
TASK-032 — ACCEPTANCE COMPLETED
TASK-032-R1 — ACCEPTED / CLOSED
```

Końcowy checkpoint LEVEL 3 zakończył się wynikiem:

```text
213 passed
0 failed
0 errors
0 skipped
SAWarning: NONE
Alembic current: head
Alembic check: No new upgrade operations detected.
schema drift: NONE
cleanup: PASS
operator data preserved: YES
```

Nie potwierdzono żadnego realnego production defect w pięciu porażkach ujawnionych przez pierwszy przebieg TASK-032.

---

## 2. Cel Sprintu — rezultat

Cel Sprintu:

> Przekształcić istniejący funkcjonalny interfejs Streamlit w prosty, zwarty i wygodny interfejs codziennej pracy, bez zmiany Core.

Cel został osiągnięty.

Aplikacja zachowuje istniejące workflow:

```text
PRODUCT
→ SDS
→ kolejna rewizja SDS
→ decyzja BHP
→ miejsca stosowania i ilości
→ widok nadzorczy
→ korekta / usunięcie błędnego wpisu
```

oraz prezentuje je w bardziej operacyjnym układzie.

---

## 3. Stan końcowy UI

### 3.1. Fundament

Potwierdzono:

```text
wide layout
table-first
business data first
UUID hidden in normal workflow
compact forms
user-facing status labels
```

Interfejs ma charakter:

```text
szeroki
zwarty
tabelaryczny
informacyjny
operacyjny
```

### 3.2. Rejestr produktów

Ekran `Produkty`:
- używa tabeli jako głównego punktu wejścia,
- pozwala wybrać produkt z wiersza,
- pokazuje uporządkowane szczegóły,
- nie eksponuje UUID jako informacji użytkowej,
- zachowuje akcje `Edytuj dane produktu`, `Dodaj nową rewizję SDS`, `Usuń produkt`,
- pokazuje przyjazne etykiety statusów,
- zachowuje bezpieczne potwierdzenie przy usuwaniu.

### 3.3. Dodaj SDS

Ekran `Dodaj SDS`:
- ma zwarty układ sekcji,
- wykorzystuje szerokość ekranu,
- oznacza istniejące pola wymagane,
- traktuje Safety Profile i Components jako dane opcjonalne,
- zachowuje manual fallback,
- nie blokuje workflow z powodu braku pełnej ekstrakcji,
- nie pokazuje UUID w komunikatach sukcesu,
- nie podstawia automatycznie bieżącej daty jako daty SDS.

Automatyczny parser pozostaje:

```text
secondary target
```

a nie warunkiem działania MVP.

### 3.4. Nowa rewizja SDS

Potwierdzono workflow:

```text
existing PRODUCT
→ new SDS revision
→ old CURRENT = ARCHIVED
→ new SDS = CURRENT
→ PRODUCT = PENDING_APPROVAL
```

Zachowane są:

```text
product_id
usage locations
quantities
history
```

Poprzednia decyzja BHP nie jest dziedziczona na nowy CURRENT SDS.

Nieznana data SDS pozostaje nieustalona.

### 3.5. Decyzja BHP

Ekran `Decyzja BHP`:
- pokazuje kontekst PRODUCT + CURRENT SDS,
- prezentuje evidence przez nazwę pliku,
- używa użytkowych etykiet `Dopuszczony` / `Niedopuszczony`,
- po zapisie wykonuje ponowny odczyt rzeczywistego stanu,
- nie pozostawia stale state.

Fizycznie potwierdzono:

```text
PENDING_APPROVAL
→ APPROVED
→ ACTIVE
```

bez ręcznego refreshu strony.

### 3.6. Miejsca stosowania

Sekcja `Miejsca stosowania`:
- pokazuje istniejące przypisania jako tabelę,
- oddziela dodawanie od edycji,
- pozwala wybrać istniejące przypisanie,
- pokazuje jeden formularz edycji dla wybranego wiersza,
- używa użytkowych etykiet:
  - `Maksymalna ilość na stanowisku`,
  - `Jednostka`,
  - `Zużycie miesięczne`,
  - `Jednostka`.

Semantyka pozostaje bez zmian:

```text
0 != None
```

Nie wprowadzono jeszcze słownika jednostek.

### 3.7. Widok nadzorczy

SPRINT-006 zmienił jednostkę prezentacji z:

```text
1 PRODUCT = 1 wiersz
```

na:

```text
1 PRODUCT × 1 aktywna USAGE_LOCATION = 1 wiersz
```

Potwierdzono:
- wiele aktywnych lokalizacji → wiele wierszy,
- produkt bez lokalizacji pozostaje widoczny,
- peak quantity widoczne per lokalizacja,
- monthly consumption widoczne per lokalizacja,
- `None` i `0` są rozróżniane,
- CURRENT SDS/BHP pozostają poprawnie propagowane,
- `requires_action` zachowuje istniejące reguły,
- read-side unika N+1,
- widok pozostaje read-only.

Filtry:

```text
Szukaj produktu
Status produktu
Lokalizacja
BHP
Wszystkie / Wymagają działania
```

---

## 4. Fizyczny Sprint Review

Architekt Operacyjny fizycznie potwierdził działanie:

```text
rejestru produktów
wyboru produktu
formularza Dodaj SDS
nowej rewizji SDS
decyzji BHP
automatycznego refreshu statusu
tabeli miejsc stosowania
dodawania lokalizacji
edycji przypisania
peak/monthly
widoku PRODUCT × LOCATION
filtrów widoku nadzorczego
```

Podczas review ujawniono chwilowo stary render `Widoku nadzorczego`.

Po pełnym restarcie Streamlit załadował aktualną implementację TASK-031 i fizyczny test przeszedł.

Nie stwierdzono konieczności PATCH produkcyjnego.

---

## 5. TASK-032 — pierwszy przebieg

Pierwszy checkpoint wykazał:

```text
5 failed
208 passed
```

Zgodnie z governance TASK-032 został poprawnie zatrzymany jako BLOCKED.

Nie wykonano opportunistic fixes.

Porażki dotyczyły:

```text
PATCH-006 revision
PATCH-008 delete
TASK-016 acceptance
TASK-021 SDS acceptance
TASK-025 BHP acceptance
```

---

## 6. TASK-032-R1 — wynik diagnostyki

Każdy FAIL został odtworzony osobno.

Klasyfikacja:

| Obszar | Przyczyna | Klasyfikacja |
|---|---|---|
| PATCH-006 | brak testowego PDF w izolowanym SDS root | TEST FIXTURE / ISOLATION |
| PATCH-008 | test oczekiwał pliku, którego sam nie utworzył | TEST FIXTURE / ISOLATION |
| TASK-016 | stary test wymagał UUID w użytkowej tabeli | OBSOLETE TEST CONTRACT |
| TASK-021 | test wybierał selectbox po indeksie po zmianie UI | OBSOLETE TEST CONTRACT |
| TASK-025 | test wymagał literalnego `ACTIVE` w komunikacie | OBSOLETE TEST CONTRACT |

Wynik:

```text
3 × obsolete test / contract alignment
2 × fixture / isolation defect
0 × real production defect
```

Production code w TASK-032-R1:

```text
NONE
```

---

## 7. Końcowa walidacja LEVEL 3

Po korekcie wyłącznie testów / fixture:

```text
pytest:
213 passed
0 failed
0 errors
0 skipped

SAWarning:
NONE

E2E:
PASS

Alembic current:
e0dd7d6468bf (head)

Alembic check:
No new upgrade operations detected.

schema drift:
NONE

cleanup:
PASS

operator data preserved:
YES
```

Pełny zestaw obejmuje:

```text
Sprint 2
Sprint 3
Sprint 4
SDS revision
safe delete
supervisory read model
Streamlit UI
```

---

## 8. Integralność architektury

SPRINT-006 nie zmienił założeń Core ani modelu persistence.

Nadal obowiązuje:

```text
presentation
→ application
→ domain
→ infrastructure
```

Potwierdzono:

```text
Streamlit SQL/ORM: NONE
lifecycle SDS/BHP in UI: NONE
Core change: NONE
schema change: NONE
new migrations: NONE
new dependencies: NONE
```

Zmiany w supervisory read model są zmianą read-side / prezentacji, nie zmianą Core.

---

## 9. Bezpieczeństwo i dane operatora

Checkpoint używał izolowanych klastrów PostgreSQL i kontrolowanych fixture.

Potwierdzono:

```text
operator data preserved: YES
.env ignored
new secrets: NONE
new dumps/backups: NONE
new PDF/MSG fixtures in repo: NONE
commit/push: NONE
```

Zastane lokalne usunięcia PDF w `.pytest_tmp` nie są częścią SPRINT-006 i nie blokują closure.

---

## 10. Definition of Done SPRINT-006

| # | Kryterium | Status |
|---|---|---|
| 1 | wide / compact layout | PASS |
| 2 | Products table-first | PASS |
| 3 | UUID hidden | PASS |
| 4 | Add SDS compact sections | PASS |
| 5 | required fields visible | PASS |
| 6 | unknown SDS date not defaulted to today | PASS |
| 7 | BHP state refresh after save | PASS |
| 8 | usage assignments table + separate add/edit | PASS |
| 9 | supervisory PRODUCT × LOCATION | PASS |
| 10 | peak/monthly visible per location | PASS |
| 11 | product without location preserved | PASS |
| 12 | supervisory filters work | PASS |
| 13 | no Core/schema changes | PASS |
| 14 | full LEVEL 3 validation | PASS |
| 15 | physical Sprint Review | PASS |

---

## 11. Backlog po SPRINT-006

Poniższe punkty są świadomie odłożone i **nie blokują zamknięcia MVP UI**.

### UI / dokumenty

```text
UI-11 — otwieranie / pobieranie CURRENT SDS z tabeli
UI-12 — nazwa "Data wystawienia SDS"
UI-13 — rewizja SDS w głównej tabeli Produkty
UI-14 / DOC-02 — podgląd dowodu decyzji BHP
DOC-01 — dodawanie SDS z komputera / upload do kontrolowanego repozytorium
```

### Dane

```text
DATA-01 — słownik jednostek miary
```

### Automatyzacja / kolejne etapy

```text
Stage 2 — parser / automatyczna analiza SDS
R8 — przeglądy okresowe
REACH
```

---

## 12. Stan danych po fizycznych testach

Fizyczny walkthrough zawierał świadome operacje testowe na lokalnej bazie operatora.

W szczególności stan XBRAKE CLEANER był modyfikowany podczas testu rewizji SDS.

Checkpoint automatyczny:

```text
nie naprawiał
nie usuwał
nie nadpisywał
```

danych operatora.

Ewentualne uporządkowanie ręcznych danych testowych należy traktować jako osobne działanie operacyjne, a nie warunek closure SPRINT-006.

---

## 13. Kryterium biznesowe

Po SPRINT-006 użytkownik może wykonywać codzienną obsługę podstawowego procesu:

```text
SDS
→ PRODUCT
→ rewizje
→ BHP
→ lokalizacje
→ ilości
→ nadzór
```

bez potrzeby pracy bezpośrednio na danych technicznych lub UUID.

Automatyczne odczytywanie treści PDF pozostaje pomocą, a nie warunkiem poprawnego działania głównego procesu.

---

## 14. Formalne zamknięcie

Decyzja końcowa:

```text
CHECKPOINT-006
SPRINT-006 UI MVP
STATUS: CLOSED

TASK-029: CLOSED
TASK-030: CLOSED
TASK-031: CLOSED
TASK-032: ACCEPTED
TASK-032-R1: CLOSED

FULL REGRESSION: PASS
PHYSICAL REVIEW: PASS
CORE CHANGE: NONE
SCHEMA CHANGE: NONE
```

SPRINT-006 stanowi nowy zaakceptowany baseline interfejsu operacyjnego MSDS Manager.

Dalsze prace wymagają nowej jawnej decyzji / Sprintu / Tasku zgodnie z governance projektu.

---

## 15. Authorization boundary

Ten checkpoint:

```text
zamyka SPRINT-006
```

ale:

```text
nie autoryzuje rozpoczęcia kolejnego Sprintu
nie autoryzuje backlogu UI/DOC/DATA
nie autoryzuje Stage 2 parsera
nie autoryzuje R8
nie autoryzuje REACH
```

Kolejne prace rozpoczynają się wyłącznie po jawnej decyzji Architekta Operacyjnego.
