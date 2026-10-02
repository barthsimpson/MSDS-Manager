# PATCH-011 — ANALYTICS Local Navigation po Physical UX Review

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 / ANALYTICS-02  
**Patch:** PATCH-011  
**Wersja:** 0.2  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
PATCH
```

---

## CONTEXT

Po wykonaniu TASK-042 przeprowadzono Physical UX Review zakładki:

```text
Analizy
```

Kierunek dashboardu został oceniony jako prawidłowy, ale zatwierdzono korektę organizacji modułu.

Decyzja UX:

```text
Analizy
├── Dashboard
├── Zestawienie zbiorcze
└── Raport przeglądu
```

Nawigacja modułu ma być poziomą listwą pod nagłówkiem `Analizy`.

---

## GOAL

Dodać lokalną nawigację modułu `Analizy` i rozdzielić istniejący dashboard od szczegółowego zestawienia tabelarycznego.

Docelowy układ:

```text
MSDS Manager

Analizy

[ Dashboard ] [ Zestawienie zbiorcze ] [ Raport przeglądu ]

<aktywny widok>
```

---

## AUTHORITATIVE CONTEXT

Przeczytaj wyłącznie:

1. `TASK-042_REPORT.md`
2. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved.md`
3. `BDR-009_ANALYTICS_Zestawienie_zbiorcze_KPI_i_agregacje_v1.0-approved.md`
4. `TDR-009_ANALYTICS_Dynamic_Read_Model_Dashboard_v1.0-approved.md`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
6. root `AGENTS.md`

Nie wykonuj repo-wide rediscovery.

Jeżeli UI wymaga zmiany biznesowej, read modelu, schema lub Core:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

Minimalnie:

```text
app/presentation/streamlit/analytics.py
app/presentation/streamlit/main.py
app/presentation/streamlit/composition.py
tests/unit/test_task042_streamlit_analytics.py
```

TASK-042 dostarczył już:

```text
Dashboard
KPI
wykresy
Wymaga uwagi
Podsumowanie producentów
PRODUCT × USAGE_LOCATION detail
```

PATCH-011 reorganizuje wyłącznie prezentację.

---

## DO

### 1. Lokalna nawigacja

W module `Analizy` dodaj poziomą listwę trzech przycisków:

```text
Dashboard
Zestawienie zbiorcze
Raport przeglądu
```

Pierwszy widok po wejściu do `Analizy`:

```text
Dashboard
```

Aktywny przycisk powinien być wizualnie odróżniony.

Preferuj prosty mechanizm Streamlit bez nowej zależności.

---

### 2. Dashboard

Dashboard pozostaje obecnym ekranem TASK-042:

```text
filtry
5 KPI
3 wykresy
Wymaga uwagi
Podsumowanie producentów
```

Usuń z dołu Dashboardu istniejący rozwijany / przyciskowy blok:

```text
Zestawienie zbiorcze
```

Dashboard nie ma dublować widoku szczegółowego.

Nie zmieniaj semantyki KPI, filtrów ani wykresów.

---

### 3. Zestawienie zbiorcze

Po wyborze:

```text
Zestawienie zbiorcze
```

pokaż istniejący read model:

```text
PRODUCT × USAGE_LOCATION
```

jako osobny widok tabelaryczny.

Minimalne kolumny pozostają zgodne z TASK-042:

```text
Produkt
Producent
Lokalizacja
MAX
Miesięczne zużycie
Status produktu
SDS / rewizja
Status BHP
```

W tym widoku można wykorzystać pełną szerokość strony.

Dane nadal pochodzą z:

```text
ListAnalyticsProductLocations
```

Nie duplikuj query ani logiki biznesowej.

---

### 4. Raport przeglądu

Po wyborze:

```text
Raport przeglądu
```

pokaż wyłącznie kontrolowany placeholder:

```text
Raport przeglądu

Funkcja zostanie uruchomiona w kolejnym etapie.
```

Można dodatkowo użyć małego opisu:

```text
Obszar przyszłego ANALYTICS-03 — Stan na dzień.
```

Nie implementuj żadnej logiki ANALYTICS-03.

---

### 5. Hierarchia nagłówków

Uporządkuj początek ekranu do:

```text
MSDS Manager
Analizy
[ local navigation ]

<tytuł aktywnego widoku>
```

Dla Dashboardu:

```text
Dashboard
Bieżący stan produktów, SDS, decyzji BHP i miejsc stosowania.
```

Nie powielaj:

```text
Analizy
Zestawienie zbiorcze
```

nad dashboardem.

---

### 6. Stan lokalnej nawigacji

Przełączanie pomiędzy trzema widokami ma działać w obrębie jednej sekcji `Analizy`.

Dozwolone:

```text
st.session_state
```

dla przechowania aktywnego podwidoku.

Nie twórz nowej globalnej nawigacji aplikacji.

Nie zmieniaj sidebaru poza istniejącą pozycją `Analizy`.

---

## DO NOT

PATCH-011 nie obejmuje:

```text
zmian TASK-041 read model
zmian KPI
zmian wykresów
zmian filtrów biznesowych
nowych query
schema change
migration
Core change
Domain change
Application business logic change
Infrastructure change
ANALYTICS-03 implementation
snapshotów
Stan na dzień
aktywnego eksportu
React
custom JS
new dependencies
globalnego redesignu innych ekranów
```

---

## EXPECTED CHANGE SURFACE

Preferowany:

```text
app/presentation/streamlit/analytics.py
tests/unit/test_task042_streamlit_analytics.py
docs/task_reports/PATCH-011_REPORT.md
```

Opcjonalnie:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/composition.py
```

wyłącznie jeśli obecny wiring tego wymaga.

Nie oczekuje się zmian poza Presentation + tests.

---

## VALIDATION

```text
LEVEL 1 — PATCH
REPORT: SHORT
```

Potwierdź co najmniej:

1. wejście do `Analizy` otwiera `Dashboard`,
2. widoczne są trzy przyciski lokalnej nawigacji,
3. Dashboard nadal renderuje KPI / wykresy / attention / manufacturer summary,
4. Dashboard nie zawiera już szczegółowego `Zestawienia zbiorczego`,
5. `Zestawienie zbiorcze` pokazuje PRODUCT × USAGE_LOCATION,
6. detail query nie jest wykonywany na Dashboardzie,
7. `Raport przeglądu` pokazuje wyłącznie placeholder,
8. brak implementacji ANALYTICS-03,
9. powrót do Dashboardu działa,
10. istniejące testy TASK-042 pozostają PASS po dostosowaniu oczekiwań UI.

Focused only.

Nie wykonuj pełnego repo-wide checkpointu.

---

## STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. lokalna nawigacja wymaga nowej dependency,
2. zmiana wymaga modyfikacji Application / Infrastructure,
3. trzeba zmienić read model TASK-041,
4. trzeba zmienić BDR-009 / TDR-009,
5. implementacja placeholdera zaczyna wprowadzać ANALYTICS-03,
6. poprawka wymaga globalnego redesignu Streamlit.

---

## REPORT

Utwórz:

```text
docs/task_reports/PATCH-011_REPORT.md
```

Minimalny format:

```text
# PATCH-011 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

IMPLEMENTED:
- local navigation:
- dashboard separation:
- aggregate table view:
- review placeholder:

VALIDATION:
- focused AppTest:
- detail lazy/query behavior:
- git diff --check:

SCOPE:
- Application change: NO
- Infrastructure change: NO
- schema change: NO
- migration: NONE
- Core change: NO
- new dependencies: NO

DEVIATIONS:
- ...

NEXT:
- READY FOR CERBERUS REVIEW + PHYSICAL UX REVIEW
```

---

## AUTHORIZATION

PATCH-011 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj PATCH-011.
```

Po wykonaniu:

```text
Codex report
→ Cerberus review
→ Physical UX Review
→ ANALYTICS-01 / ANALYTICS-02 closure albo kolejny mały PATCH
```
