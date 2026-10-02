# PATCH-013 — ANALYTICS Compact Filter Bar + Export Placement

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 / ANALYTICS-02  
**Patch:** PATCH-013  
**Wersja:** 0.1  
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

Po wdrożeniu PATCH-012 Physical UX Review potwierdził, że lokalna nawigacja, Dashboard i ogólna gęstość UI idą w dobrym kierunku.

Pozostałym głównym problemem jest sposób prezentacji filtrów:

```text
duży panel "Filtry"
→ zajmuje zbyt dużo wysokości
→ opóźnia wejście w dane
→ przy zoom 100% nadal nadmiernie rozciąga Dashboard
```

Zatwierdzony kierunek UX:

```text
filtry jako pozioma belka sterująca
→ jedna linia
→ dane bezpośrednio poniżej
```

Model inspirowany rozwiązaniami znanymi z FlowVision oraz lekkiego toolbaru SaaS.

---

## GOAL

Zastąpić dużą kartę filtrów kompaktową poziomą belką oraz usunąć eksport z Dashboardu.

Docelowy układ:

```text
Dashboard

[ Okres SDS ] [ Producent ] [ SDS ] [ BHP ] [ Lokalizacja ]

[ KPI ][ KPI ][ KPI ][ KPI ][ KPI ]

[ wykresy ... ]
```

oraz:

```text
Zestawienie zbiorcze

[ Okres SDS ] [ Producent ] [ SDS ] [ BHP ] [ Lokalizacja ]

[ tabela PRODUCT × USAGE_LOCATION ]

                                      [ przyszły eksport ]
```

PATCH-013 nie implementuje jeszcze aktywnego eksportu.

---

## AUTHORITATIVE CONTEXT

Przeczytaj wyłącznie:

1. `PATCH-012_REPORT.md`
2. `PATCH-011_REPORT.md`
3. `TASK-042_REPORT.md`
4. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved.md`
5. `BDR-009_ANALYTICS_Zestawienie_zbiorcze_KPI_i_agregacje_v1.0-approved.md`
6. `TDR-009_ANALYTICS_Dynamic_Read_Model_Dashboard_v1.0-approved.md`
7. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
8. root `AGENTS.md`

Nie wykonuj repo-wide rediscovery.

---

## KNOWN STARTING POINTS

Minimalnie:

```text
app/presentation/streamlit/analytics.py
tests/unit/test_task042_streamlit_analytics.py
```

Opcjonalnie:

```text
app/presentation/streamlit/main.py
```

wyłącznie jeśli lokalny styling lub state tego wymaga.

---

## DO

### 1. Usuń kartę `Filtry`

Nie renderuj osobnego dużego kontenera:

```text
Filtry
```

Filtry mają być prezentowane bezpośrednio jako kompaktowy toolbar.

---

### 2. Jedna pozioma linia filtrów

Docelowo:

```text
[ Okres SDS ] [ Producent ] [ SDS ] [ BHP ] [ Lokalizacja ]
```

Preferowana implementacja:

```text
st.columns(...)
```

z proporcjami dopasowanymi do treści.

Dokładne proporcje mogą zostać dostosowane po renderze.

---

### 3. Date range jako jedna kontrolka

Zastąp dwa osobne pola:

```text
Od
Do
```

jedną kontrolką:

```text
Okres SDS
```

która zwraca:

```text
(date_from, date_to)
```

Preferuj natywny komponent Streamlit obsługujący zakres dat.

Nie dodawaj nowej dependency.

Nie zmieniaj semantyki:

```text
Okres SDS
→ dotyczy trendu SDS
→ nie zmienia current-state KPI
```

Jeżeli natywna kontrolka wymaga innej reprezentacji inputu, mapowanie pozostaje wyłącznie presentation-level.

---

### 4. Skróć etykiety

W toolbarze użyj:

```text
Okres SDS
Producent
SDS
BHP
Lokalizacja
```

Nie używaj:

```text
Status SDS
Status BHP
Okres trendu SDS
```

Semantyka pozostaje bez zmian.

---

### 5. Dashboard — usuń `Eksport`

Dashboard nie ma pokazywać:

```text
Eksport
```

ani:

```text
disabled placeholder
```

Dashboard służy do:

```text
orientacji
analizy
oceny stanu
```

a nie do generowania pliku.

---

### 6. Zestawienie zbiorcze — eksport tylko docelowo

Eksport będzie związany docelowo z:

```text
Zestawieniem zbiorczym
```

po tym, jak użytkownik:

```text
ustawi filtry
→ obejrzy wynik
→ potwierdzi poprawność zestawienia
→ uruchomi eksport
```

Docelowa pozycja przyszłej akcji:

```text
prawy dolny narożnik pod tabelą
```

W PATCH-013:

```text
NIE RENDERUJ przycisku eksportu
```

dopóki funkcja nie jest zaimplementowana.

Nie implementuj CSV / XLSX / PDF.

---

### 7. Spójność Dashboard / Zestawienie zbiorcze

Oba widoki mają używać tego samego wizualnego wzorca toolbaru filtrów.

Nie twórz dwóch niezależnych stylów.

---

### 8. Responsive behavior

Toolbar ma pozostać czytelny przy typowej szerokości desktopowej.

Jeżeli viewport jest zbyt wąski, dopuszczalne jest naturalne zachowanie Streamlit.

Nie implementuj custom responsive JS.

---

### 9. Zachowanie filtrów

Nie zmieniaj:

```text
manufacturer_id
sds_status
bhp_status
usage_location_id
include_no_active_location
trend_date_from
trend_date_to
```

Nie zmieniaj mapowania wartości biznesowych.

---

## DO NOT

PATCH-013 nie obejmuje:

```text
aktywnego eksportu
CSV
XLSX
PDF export
zmian KPI
zmian wykresów
zmian alertów
zmian read model
zmian TASK-041
zmian BDR/TDR
nowych query
schema change
migration
Core change
Domain change
Application business logic change
Infrastructure change
ANALYTICS-03
React
custom JS
new dependencies
globalnego redesignu aplikacji
```

---

## EXPECTED CHANGE SURFACE

Preferowany:

```text
app/presentation/streamlit/analytics.py
tests/unit/test_task042_streamlit_analytics.py
docs/task_reports/PATCH-013_REPORT.md
```

Nie oczekuje się zmian poza Presentation + tests.

---

## VALIDATION

```text
LEVEL 1 — PATCH
REPORT: SHORT
```

Potwierdź co najmniej:

1. Dashboard nie renderuje kontenera `Filtry`,
2. Dashboard ma jedną linię filtrów,
3. `Od` + `Do` zostały zastąpione przez jeden `Okres SDS`,
4. toolbar zawiera:
   - Okres SDS,
   - Producent,
   - SDS,
   - BHP,
   - Lokalizacja,
5. Dashboard nie pokazuje `Eksport`,
6. wszystkie filtry nadal mapują się do istniejących AnalyticsFilters,
7. okres SDS nadal wpływa wyłącznie na trend,
8. KPI current-state nie zmieniają się po zmianie samego okresu,
9. Zestawienie zbiorcze używa tego samego wzorca toolbaru,
10. tabela PRODUCT × USAGE_LOCATION działa bez zmian,
11. brak aktywnej funkcji eksportu,
12. focused TASK-042 / PATCH-011 / PATCH-012 UI tests pozostają PASS po aktualizacji presentation expectations.

Testy automatyczne nie zastępują Physical UX Review.

---

## STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. date range wymaga nowej dependency,
2. poprawna implementacja wymaga Application change,
3. poprawna implementacja wymaga Infrastructure change,
4. trzeba zmienić read model TASK-041,
5. trzeba zmienić BDR-009 / TDR-009,
6. wymagany byłby custom JS,
7. toolbar powoduje regresję innych ekranów,
8. realizacja zaczyna wymagać globalnego redesignu Streamlit.

---

## REPORT

Utwórz:

```text
docs/task_reports/PATCH-013_REPORT.md
```

Minimalny format:

```text
# PATCH-013 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

IMPLEMENTED:
- compact filter bar:
- date range:
- short labels:
- dashboard export removal:
- aggregate view toolbar:
- export policy:

VALIDATION:
- focused AppTest:
- filter mapping:
- trend/current-state separation:
- regression:
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

PATCH-013 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj PATCH-013.
```

Po wykonaniu:

```text
Codex report
→ Cerberus review
→ Physical UX Review
→ closure ANALYTICS-01 / ANALYTICS-02
   albo ostatni kosmetyczny PATCH
```
