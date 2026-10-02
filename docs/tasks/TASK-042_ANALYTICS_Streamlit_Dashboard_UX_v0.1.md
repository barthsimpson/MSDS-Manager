# TASK-042 — ANALYTICS Streamlit Dashboard + UX Target

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 / ANALYTICS-02 — `Analizy` / `Zestawienie zbiorcze`  
**Task:** TASK-042  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
INTEGRATION
```

---

## GOAL

Wdrożyć finalną warstwę prezentacji MVP dla zakładki:

```text
Analizy
→ Zestawienie zbiorcze
```

na bazie zaakceptowanego `TASK-041`, bez zmiany semantyki danych.

Rezultat TASK-042:

```text
sidebar → Analizy
+ filtry
+ 5 KPI cards
+ 3 wykresy
+ sekcja "Wymaga uwagi"
+ "Podsumowanie producentów"
+ szczegółowe PRODUCT × USAGE_LOCATION
+ disabled placeholder "Eksport"
+ testy Streamlit/AppTest
```

Dashboard ma możliwie wiernie odwzorować zatwierdzony UX target:

```text
nowoczesny dashboard SaaS
lekki
szeroki
kafelkowy
czytelna hierarchia
pastelowe statusy
dużo przestrzeni
```

bez zmiany stosu technologicznego.

---

## AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie:

1. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved.md`
2. `BDR-009_ANALYTICS_Zestawienie_zbiorcze_KPI_i_agregacje_v1.0-approved.md`
3. `TDR-009_ANALYTICS_Dynamic_Read_Model_Dashboard_v1.0-approved.md`
4. `TASK-041_REPORT.md` — `STATUS: DONE`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
6. root `AGENTS.md`

Jeżeli do wiring potrzebny jest wzorzec istniejącego UI, sprawdź tylko bezpośrednio:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/composition.py
app/presentation/streamlit/supervisory.py
```

Nie wykonuj repo-wide rediscovery.

Jeżeli UI wymaga zmiany biznesowej, read modelu, schema lub Core:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

TASK-041 dostarczył:

```text
app/application/dto/analytics.py
app/application/ports/analytics_read.py

app/application/use_cases/get_analytics_dashboard.py
app/application/use_cases/list_analytics_product_locations.py

app/infrastructure/db/repositories/analytics_query.py
app/infrastructure/filesystem/analytics_availability.py
```

Raport TASK-041 potwierdził:

```text
ProductAnalyticsFact = 1 rekord / PRODUCT
KPI
BHP distribution
attention summary
manufacturer summary
SDS trend
PRODUCT × USAGE_LOCATION detail
runtime availability overlay

dashboard query count = 3 SELECT
detail query count = 1 SELECT
NO N+1
```

TASK-042 ma konsumować te kontrakty.

Nie duplikuj logiki biznesowej w Streamlit.

---

## EXPECTED CHANGE SURFACE

Oczekiwane zmiany:

```text
app/presentation/streamlit/
    analytics.py                  # preferowany nowy moduł
    main.py                       # nawigacja
    composition.py                # wiring use case'ów

tests/
    unit / presentation / AppTest

docs/task_reports/TASK-042_REPORT.md
```

Minimalne zmiany Application są dopuszczalne wyłącznie dla:

```text
presentation-safe helper / label mapping
```

jeśli istniejąca struktura repo tego wymaga.

Nie oczekuje się zmian w:

```text
app/domain/
app/infrastructure/db/
app/infrastructure/filesystem/
migrations/
pyproject.toml
CORE / BDR / TDR
```

Jeżeli takie zmiany okażą się konieczne:

```text
STOP / BLOCKED
```

---

# DO

## 1. Nawigacja

Dodaj do istniejącej nawigacji Streamlit:

```text
Analizy
```

Zakładka ma być równorzędnym ekranem aplikacji.

Nie usuwaj i nie przemieszczaj istniejących ekranów bez potrzeby.

---

## 2. Układ główny

Widok:

```text
Analizy

Zestawienie zbiorcze

[ FILTRY ]

[ KPI ][ KPI ][ KPI ][ KPI ][ KPI ]

[ Produkty wg producenta ]
[ Status BHP ]
[ Nowe / zaktualizowane SDS ]

[ Wymaga uwagi ]

[ Podsumowanie producentów ]

[ Zestawienie zbiorcze — PRODUCT × USAGE_LOCATION ]
```

Użyj szerokiego layoutu istniejącej aplikacji.

Dashboard nie może wyglądać jak zwykły ciąg formularzy Streamlit.

---

## 3. Filtry

Dodaj filtry w jednym zwartym panelu / wierszu.

### Okres trendu SDS

UI label:

```text
Okres trendu SDS
```

Pola:

```text
od
do
```

Nie używaj ogólnego:

```text
Zakres dat
```

bo mogłoby sugerować historyczny snapshot dashboardu.

### Producent

UI:

```text
Wszyscy producenci
+ nazwy producentów
```

Backend:

```text
manufacturer_id
```

### Status SDS

Opcje:

```text
Wszystkie
Ma CURRENT SDS
Brak CURRENT SDS
```

### Status BHP

Opcje:

```text
Wszystkie
Dopuszczony
Odrzucony
Brak decyzji
```

Mapowanie na read-side:

```text
APPROVED
REJECTED
NO_DECISION
```

Nie pokazuj:

```text
W trakcie
```

### Lokalizacja

Opcje:

```text
Wszystkie lokalizacje
+ ACTIVE USAGE_LOCATION
+ opcjonalnie "Brak aktywnej lokalizacji"
```

Backend operuje na ID.

---

## 4. Eksport

W zatwierdzonym UX target istnieje element `Eksport`, ale aktywna funkcja eksportu nie należy do TDR-009.

W TASK-042 pokaż:

```text
Eksport
```

jako kontrolkę:

```text
disabled
```

z krótkim helper/tooltip:

```text
Funkcja planowana
```

Nie implementuj CSV/XLSX/PDF.

---

## 5. KPI cards

Renderuj pięć kart:

```text
Produkty ogółem
SDS CURRENT
BHP zatwierdzone
Braki / do uzupełnienia
Stanowiska aktywne
```

Źródło:

```text
AnalyticsDashboardDto
```

Streamlit nie przelicza KPI z surowych rekordów.

### Wartości procentowe

Jeżeli DTO udostępnia wystarczające mianowniki, można pokazać pomocniczo procent dla:

```text
SDS CURRENT
BHP zatwierdzone
```

Nie pokazuj porównań:

```text
+12% vs poprzedni okres
```

bo nie zostały zatwierdzone w BDR-009.

### Styl

Karty powinny mieć:

```text
zaokrąglony kontener
delikatne obramowanie
czytelny label
dużą wartość
subtelny status / opis
spójne wysokości
```

Bez agresywnych kolorów.

---

## 6. Wykres — Produkty wg producenta

Typ:

```text
bar chart
```

Źródło:

```text
manufacturer summary
```

Minimalnie:

```text
manufacturer_name
products_count
```

Preferowany układ:

```text
horizontal bar
```

jeżeli lepiej obsługuje dłuższe nazwy producentów.

Nie pokazuj technicznych ID.

---

## 7. Wykres — Status BHP

Typ:

```text
donut / arc
```

Kategorie:

```text
Dopuszczony
Odrzucony
Brak decyzji
```

Źródło:

```text
BhpStatusDistributionDto
```

Produkty bez CURRENT SDS nie trafiają do wykresu.

Nie twórz kategorii:

```text
W trakcie
```

---

## 8. Wykres — Nowe / zaktualizowane SDS

Typ:

```text
line / area
```

Oś X:

```text
miesiąc
```

Serie:

```text
Nowe SDS
Zaktualizowane SDS
```

Źródło:

```text
SdsTrendPoint[]
```

Zakres zmienia wyłącznie wykres trendu.

Nie przeliczaj po:

```text
issue_date
revision
filename
```

---

## 9. Technologia wykresów

Użyj:

```text
st.vega_lite_chart
```

zgodnie z TDR-009.

Nie dodawaj:

```text
Plotly
ECharts
custom JS
React
zewnętrznych CDN
```

Jeżeli aktualna wersja Streamlit nie pozwala zrealizować któregoś wykresu bez nowej dependency:

```text
STOP / BLOCKED
```

Nie zmieniaj stosu samodzielnie.

---

## 10. Sekcja `Wymaga uwagi`

Renderuj cztery karty / pozycje:

```text
Brak CURRENT SDS
Brak decyzji BHP
Brak aktywnego miejsca stosowania
Niedostępny dokument
```

Źródło:

```text
AttentionSummaryDto
```

UI ma pokazać liczby problemów, a nie sam status kolorystyczny.

Nie implementuj jeszcze automatycznego routingu do ekranów operacyjnych, jeśli read model nie dostarcza jawnie wymaganych identyfikatorów.

Jeżeli `affected_product_ids_by_reason` jest dostępne, nie pokazuj surowych UUID.

Drill-down pozostaje poza TASK-042, chyba że da się zrobić lokalnie bez rozszerzenia zakresu i bez zmiany Application; domyślnie:

```text
NO DRILL-DOWN
```

---

## 11. Podsumowanie producentów

Tabela:

```text
Producent
Produkty
SDS CURRENT
BHP OK
Braki
Ostatni SDS
```

Źródło:

```text
ManufacturerSummaryRow[]
```

Nie używaj etykiety:

```text
Ostatnia aktualizacja
```

Użyj:

```text
Ostatni SDS
```

Datę prezentuj użytkowo:

```text
YYYY-MM-DD
```

lub zgodnie z istniejącą konwencją dat UI projektu.

Nie pokazuj manufacturer_id.

---

## 12. Zestawienie szczegółowe

Sekcja:

```text
Zestawienie zbiorcze
```

ma prezentować:

```text
PRODUCT × USAGE_LOCATION
```

Preferowany MVP:

```text
st.expander("Zestawienie zbiorcze", expanded=False)
```

Po rozwinięciu pobierz dane przez:

```text
ListAnalyticsProductLocations
```

jeżeli konstrukcja Streamlit pozwala rzeczywiście uniknąć zbędnego odczytu.

Jeżeli Streamlit wykonuje cały kod przy rerun i nie ma realnego lazy load przez sam expander:

```text
nie udawaj lazy load
```

W takim przypadku zastosuj jawny przycisk:

```text
Pokaż zestawienie szczegółowe
```

i dopiero po aktywacji wykonaj detail query.

### Kolumny minimalne

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

Ilości pokazuj z kodem jednostki:

```text
40 kg
2.5 l
```

`0` ma być pokazane jako:

```text
0 <jednostka>
```

a nie jako brak.

Produkt bez lokalizacji:

```text
Lokalizacja = Brak
```

---

## 13. Empty states

### Brak produktów

Pokaż:

```text
Brak produktów dla wybranych filtrów.
```

KPI mogą pokazywać:

```text
0
```

Wykresy nie renderują sztucznej serii zer.

### Brak trendu

Pokaż:

```text
Brak zarejestrowanych SDS w wybranym okresie.
```

### Brak producentów w tabeli

Pokaż:

```text
Brak danych do podsumowania.
```

---

## 14. Error states

Błędy Application mają być prezentowane jako kontrolowany komunikat.

Nie pokazuj operatorowi:

```text
stack trace
SQL
local filesystem paths
UUID
```

`CHECK_FAILED` dla availability nie może zostać wizualnie przedstawiony jako `MISSING`, jeśli Application zachował rozróżnienie.

---

## 15. Loading / rerun

Dla głównego odczytu:

```text
st.spinner
```

lub równoważny istniejący wzorzec.

Po zmianie filtra:

```text
dashboard rerun
→ nowy AnalyticsDashboardDto
```

Nie implementuj cache biznesowego.

Nie trzymaj starego DTO po zmianie filtra.

---

## 16. Styling

Dopuszczalne:

```text
st.columns
st.container
st.markdown
scoped CSS
```

CSS ma służyć wyłącznie prezentacji:

```text
karty
padding
border radius
subtelne tło
nagłówki
spacing
status badges
```

Nie używaj:

```text
custom JS
DOM manipulation
remote fonts
remote stylesheets
unsafe rendering of arbitrary user strings
```

Dynamiczne dane użytkowe mają być renderowane przez natywne komponenty lub escapowane.

---

## 17. UX hierarchy

Ekran ma od razu komunikować kolejność:

```text
1. filtrowanie
2. stan ogólny
3. struktura / trend
4. problemy
5. podsumowanie
6. szczegóły
```

Nie rozpoczynaj od dużej tabeli.

Nie przenoś technicznych szczegółów ponad KPI.

---

## 18. Existing UI coherence

Zachowaj istniejące zasady SPRINT-006:

```text
wide layout
compact controls
business data first
UUID hidden
table only where table adds value
```

Dashboard ma być wizualnie nowocześniejszy, ale nadal wyglądać jak część MSDS Manager.

Nie przebudowuj globalnie pozostałych ekranów, aby dopasować je do dashboardu.

---

# DO NOT

TASK-042 nie obejmuje:

```text
zmiany TASK-041 read model
nowych KPI
nowych statusów
nowych alert rules
drill-down workflow
aktywny eksport
ANALYTICS-03 Stan na dzień
snapshot history
history as-of
AI
REACH
R8
parser SDS
Ustawienia
permissions
React
new dependencies
schema change
migration
Core change
```

Nie implementuj:

```text
"W trakcie" BHP
trendów procentowych vs poprzedni okres
automatycznego scoringu
risk score
```

Nie wykonuj opportunistic refactor innych ekranów.

---

# VALIDATION

```text
LEVEL 2 — INTEGRATION
REPORT: SHORT / STANDARD INTEGRATION
```

## A. Streamlit/AppTest

Potwierdź co najmniej:

1. `Analizy` jest dostępne w nawigacji,
2. ekran renderuje się bez danych,
3. wszystkie pięć KPI istnieje,
4. filtr producenta jest mapowany na ID,
5. filtr SDS ma tylko zatwierdzone kategorie,
6. filtr BHP nie zawiera `W trakcie`,
7. filtr lokalizacji działa,
8. okres trendu jest opisany jako `Okres trendu SDS`,
9. zmiana okresu nie zmienia KPI current-state,
10. bar chart renderuje się,
11. donut BHP renderuje się,
12. trend SDS renderuje się,
13. `Wymaga uwagi` pokazuje cztery kategorie,
14. `Podsumowanie producentów` pokazuje `Ostatni SDS`,
15. Export jest disabled / nie wykonuje eksportu,
16. UUID nie są prezentowane użytkownikowi,
17. empty states są czytelne,
18. detail jest pobierany tylko po jawnej aktywacji, jeśli zastosowano button lazy-load,
19. szczegóły pokazują MAX i monthly z kodem jednostki,
20. zero ilości nie znika jako NO_DATA.

---

## B. Wiring / architecture

Potwierdź:

```text
Streamlit → GetAnalyticsDashboard
Streamlit → ListAnalyticsProductLocations
```

oraz brak:

```text
SQL / ORM w Streamlit
filesystem Path access w Streamlit
business aggregation w Streamlit
```

UI może wykonywać wyłącznie:

```text
formatting
label mapping
presentation composition
```

---

## C. Regression

Uruchom focused regressions dla:

```text
TASK-041 analytics
Streamlit shell/navigation
supervisory
```

Nie wykonuj pełnego repo-wide checkpointu na tym etapie, chyba że focused tests ujawnią powiązany problem.

---

## D. Scope

Raport musi potwierdzić:

```text
schema change: NO
migration: NONE
Core change: NO
Domain change: NO
Application business logic change: NO
Infrastructure change: NO
new dependencies: NO
operator data preserved: YES
```

---

## E. Physical review readiness

Po Tasku dashboard musi być gotowy do uruchomienia na danych operatora w celu:

```text
PHYSICAL UX REVIEW
```

Codex nie deklaruje:

```text
UX TARGET PASS
```

na podstawie samych testów.

Końcową ocenę wizualną wykonuje Architekt Operacyjny.

---

# STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. dashboard wymaga zmiany BDR-009,
2. dashboard wymaga zmiany TDR-009,
3. trzeba zmienić TASK-041 read model z powodów semantycznych,
4. potrzeba schema change lub migracji,
5. potrzeba Core change,
6. potrzeba nowej dependency,
7. `st.vega_lite_chart` nie wystarcza i wymagany byłby nowy framework,
8. UI musiałoby wykonywać SQL / ORM,
9. UI musiałoby samodzielnie ustalać lifecycle/current status,
10. zatwierdzone KPI nie mogą być pokazane z istniejącego DTO,
11. detail nie może zachować `PRODUCT × USAGE_LOCATION`,
12. testy wymagają trwałej zmiany danych operatora,
13. wdrożenie zaczyna wymagać globalnego refactoru Streamlit.

Po minimalnej diagnostyce:

```text
STOP
→ raport
→ bez opportunistic fix
```

---

# REPORT

Utwórz:

```text
docs/task_reports/TASK-042_REPORT.md
```

Format:

```text
# TASK-042 REPORT

STATUS:
DONE
lub
BLOCKED

CHANGED:
- Streamlit analytics:
- navigation:
- composition:
- tests:

IMPLEMENTED:
- filters:
- KPI:
- charts:
- attention:
- manufacturer summary:
- detail:
- export placeholder:
- empty/error states:
- styling:

VALIDATION:
- AppTest:
- focused analytics regression:
- shell/navigation regression:
- git diff --check:

ARCHITECTURE:
- direct SQL/ORM in Streamlit: NONE
- direct filesystem access in Streamlit: NONE
- business aggregation in Streamlit: NONE

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- Domain change: NO
- Application business logic change: NO
- Infrastructure change: NO
- new dependencies: NO

DATA SAFETY:
- operator data preserved: YES

DEVIATIONS:
- ...

NEXT:
- READY FOR CERBERUS REVIEW + PHYSICAL UX REVIEW
lub
- BLOCKED — <reason>
```

Nie raportuj `PHYSICAL REVIEW PASS` — należy to do Architekta Operacyjnego.

---

# AUTHORIZATION

TASK-042 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj TASK-042.
```

Po wykonaniu:

```text
Codex report
→ Cerberus review
→ Physical UX Review
→ ewentualny PATCH
→ closure ANALYTICS-01 / ANALYTICS-02
```
