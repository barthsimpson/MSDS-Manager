# TDR-009 — ANALYTICS — Dynamiczny read model i dashboard `Zestawienie zbiorcze`

**Projekt:** MSDS Manager  
**Dokument:** TDR-009  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Podstawa biznesowa:** `BDR-009 v1.0-approved`  
**Podstawa UX:** `ANALYTICS-01 UX Contract v1.0-approved`  
**Model MVP:** `MODEL A — DYNAMIC READ MODEL`

---

## 1. Cel decyzji technicznej

TDR-009 definiuje minimalny techniczny model realizacji:

```text
Analizy
→ Zestawienie zbiorcze
→ dashboard current-state
```

zgodnie z zatwierdzonym modelem:

```text
Streamlit
→ Application analytics query
→ analytics read port
→ PostgreSQL read adapter
→ istniejące dane operacyjne
```

Dokument rozstrzyga:

- granice warstw,
- kontrakty read model,
- filtrowanie,
- agregacje,
- dostęp do stanu plików SDS / evidence,
- kompozycję dashboardu,
- technologię wykresów,
- sposób uniknięcia N+1,
- granice wydajności,
- NO_DATA / ERROR,
- zakres testów,
- brak zmian schema / Core.

TDR-009 nie implementuje kodu.

---

## 2. Kontekst obowiązujący

TDR-009 należy czytać łącznie z:

1. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved`,
2. `BDR-009_ANALYTICS_Zestawienie_zbiorcze_KPI_i_agregacje_v1.0-approved`,
3. `CORE-001_MSDS_Manager_v1.3-approved_DECISION_EVIDENCE`,
4. `BDR-002 v1.2-approved`,
5. `BDR-004`,
6. `BDR-006`,
7. `TDR-003 — struktura warstw aplikacji`,
8. `TDR-005 — UNIT_OF_MEASURE`,
9. `TDR-006 — kontrolowany import SDS`,
10. `TDR-007 v1.1-approved — DECISION_EVIDENCE`,
11. `TDR-008 — kontrolowany dostęp do CURRENT SDS`,
12. `GOV-001 v1.0-approved`,
13. `GOV-002 v1.0-approved`.

W razie konfliktu:

```text
STOP
```

Codex nie projektuje samodzielnie nowej semantyki biznesowej.

---

## 3. Decyzja główna — Model A

Dla MVP obowiązuje:

```text
MODEL A — DYNAMIC READ MODEL
```

czyli:

```text
PostgreSQL operational data
        ↓
read-only analytics queries
        ↓
Application DTO / aggregation
        ↓
Streamlit dashboard
```

Nie tworzymy:

```text
analytics schema
materialized views
data warehouse
ETL
osobnej bazy raportowej
nowych tabel analytics
```

TDR-009 nie wymaga:

```text
schema change
Alembic migration
Core change
```

---

## 4. Zasada architektoniczna

Obowiązuje kierunek zależności z TDR-003:

```text
Presentation / Streamlit
        ↓
Application
        ↓
Port read-side
        ↓
Infrastructure / PostgreSQL
```

### Streamlit nie wykonuje bezpośrednio:

- SQL,
- SQLAlchemy query,
- joinów,
- interpretacji lifecycle,
- reguł `CURRENT`,
- reguł BHP,
- liczenia KPI z ORM,
- dostępu do lokalnych ścieżek przez `Path(...)`.

### Application:

- przyjmuje filtry,
- uruchamia read porty,
- składa DTO dashboardu,
- wykonuje proste agregacje po zwróconym read model,
- łączy wynik PostgreSQL z kontrolowanym sprawdzeniem dostępności plików.

### Infrastructure:

- wykonuje zapytania PostgreSQL,
- mapuje wynik do read DTO / read records,
- realizuje kontrolowane sprawdzenie dostępności plików przez istniejące porty/adapters.

### Domain:

Nie otrzymuje nowej encji `Analytics`.

Dashboard jest:

```text
READ MODEL
```

a nie nowym obiektem Core.

---

## 5. Główny use case

Preferowany pojedynczy punkt wejścia Application:

```text
GetAnalyticsDashboard
```

Wejście:

```text
AnalyticsFilters
```

Wyjście:

```text
AnalyticsDashboardDto
```

Przykładowy kontrakt logiczny:

```text
GetAnalyticsDashboard.execute(filters)
→ AnalyticsDashboardDto
```

Nie wymaga się dokładnie takiej nazwy klasy, jeśli repo ma już spójny wzorzec query/read services.

Nie tworzyć frameworka CQRS.

---

## 6. AnalyticsFilters

Minimalny kontrakt:

```text
AnalyticsFilters
├── manufacturer_id: UUID | None
├── sds_status: CURRENT_PRESENT | CURRENT_MISSING | None
├── bhp_status: APPROVED | REJECTED | NO_DECISION | None
├── usage_location_id: UUID | None
├── include_no_active_location: bool = False
├── trend_date_from: date
└── trend_date_to: date
```

UI pokazuje nazwy biznesowe.

Application / Infrastructure operują na stabilnych identyfikatorach:

```text
manufacturer_id
usage_location_id
```

Nie filtrujemy po nazwie tekstowej, jeśli istnieje ID.

---

## 7. Zakres działania filtrów

### 7.1. Filtry current-state

Na bieżący zestaw PRODUCT wpływają:

```text
manufacturer
status SDS
status BHP
lokalizacja
```

Ten przefiltrowany zbiór jest bazą dla:

- KPI produktowych,
- statusu BHP,
- `Wymaga uwagi`,
- `Podsumowania producentów`,
- szczegółowego `PRODUCT × USAGE_LOCATION`.

### 7.2. Okres trendu SDS

Zakres dat:

```text
trend_date_from
trend_date_to
```

wpływa wyłącznie na:

```text
Nowe / zaktualizowane SDS
```

Nie zmienia znaczenia KPI current-state.

UI powinno używać etykiety:

```text
Okres trendu SDS
```

### 7.3. Trend a pozostałe filtry

Trend SDS może być ograniczony do PRODUCT należących do bieżącego zestawu wynikającego z filtrów wymiarowych.

Interpretacja:

```text
najpierw wybierz PRODUCT wg bieżących filtrów
→ następnie pokaż zdarzenia SDS tych PRODUCT w wybranym okresie
```

Nie oznacza to historycznego `as-of` dla producenta / lokalizacji.

---

## 8. Bazowy read model — ProductAnalyticsFact

Preferowany jest jeden spójny read model:

```text
ProductAnalyticsFact
```

Jeden rekord:

```text
1 PRODUCT = 1 ProductAnalyticsFact
```

Minimalny zakres:

```text
product_id
product_name
usage_status

manufacturer_id
manufacturer_name

has_current_sds
current_sds_id | None
current_sds_original_filename | None
current_sds_relative_path | None
current_sds_registered_at | None

bhp_category
current_bhp_decision_id | None
current_evidence_id | None
current_evidence_original_filename | None
current_evidence_relative_path | None

active_location_count
has_active_location

latest_sds_registered_at | None
```

`bhp_category` jest wartością read-side:

```text
APPROVED
REJECTED
NO_DECISION
NOT_APPLICABLE_NO_CURRENT_SDS
```

`NOT_APPLICABLE_NO_CURRENT_SDS` jest wyłącznie technicznym stanem read modelu.

Nie jest nowym statusem domenowym BHP.

---

## 9. Budowa ProductAnalyticsFact

Zapytanie ma zwracać jeden wiersz na PRODUCT.

Wymagane jest uniknięcie zwielokrotnienia przez:

```text
PRODUCT × SDS
PRODUCT × BHP_DECISION
PRODUCT × PRODUCT_USAGE_LOCATION
```

Dozwolone techniki:

- `EXISTS`,
- agregujące subquery,
- CTE,
- `LEFT JOIN` do podzapytania gwarantującego 1:1,
- `GROUP BY product_id`,
- `DISTINCT` tam, gdzie semantycznie uzasadnione.

Nie wolno:

```text
pobrać wszystkich ORM entities
→ wykonywać dodatkowy query per PRODUCT
```

czyli:

```text
N+1 = ZABRONIONE
```

---

## 10. Analytics read port

Application otrzymuje dedykowany read port, np.:

```text
AnalyticsReadPort
```

Minimalne operacje logiczne:

```text
list_product_facts(filters_current_state)
get_active_location_count(filters_current_state)
get_sds_trend(product_ids_or_filters, date_from, date_to)
list_product_location_rows(filters_current_state)
```

Dopuszczalne jest połączenie części zapytań, jeżeli uprości implementację.

Nie należy tworzyć osobnego repozytorium per widget.

Zasada:

```text
read model odpowiada potrzebie biznesowej
nie strukturze layoutu HTML
```

---

## 11. KPI assembly

Preferowany model:

```text
ProductAnalyticsFact[]
        ↓
Application
        ↓
KPI DTO
```

Z bazowych faktów Application wylicza:

```text
products_total
current_sds_count
bhp_approved_count
attention_products_count
```

Wyjątek:

```text
active_locations_count
```

może pochodzić z osobnego `COUNT(DISTINCT location_id)` w PostgreSQL.

Nie wolno liczyć stanowisk jako sumy `active_location_count` z PRODUCT, ponieważ jedna lokalizacja może być współdzielona przez wiele produktów.

---

## 12. File availability overlay

BDR-009 wymaga wykrycia:

```text
CURRENT SDS file = MISSING
CURRENT evidence file = MISSING
```

Sam PostgreSQL nie wystarcza do potwierdzenia fizycznej dostępności pliku.

Obowiązuje:

```text
ProductAnalyticsFact
→ kandydaci z current SDS / evidence
→ existing controlled availability port
→ availability overlay
→ attention flags
```

### Zasady:

- nie czytać zawartości pliku,
- nie otwierać PDF / MSG / obrazu,
- sprawdzać wyłącznie bezpieczną dostępność ścieżki,
- zachować istniejące path safety,
- `MISSING` nie usuwa rekordu,
- brak pliku nie zmienia lifecycle.

Jeżeli istniejący adapter udostępnia metodę typu:

```text
exists / availability / safe_resolve
```

należy go użyć.

Jeżeli jej brakuje, dopuszczalny jest mały read-only port Application + adapter Infrastructure.

Nie duplikować logiki bezpieczeństwa ścieżek w Analytics.

---

## 13. Cache

W MVP:

```text
BRAK PERSISTENT CACHE
BRAK MATERIALIZED CACHE
```

Powód:

- mały spodziewany wolumen,
- current-state powinien być aktualny po rerun,
- brak ryzyka prezentacji starego statusu BHP / SDS.

Dopuszczalny jest standardowy cykl rerun Streamlit.

Nie dodawać `st.cache_data` do danych biznesowych w pierwszym przyroście bez pomiaru realnego problemu wydajności.

---

## 14. SDS trend query

Trend jest osobnym read query.

Źródło czasu:

```text
SDS.registered_at
```

Minimalny wynik:

```text
SdsTrendPoint
├── period_start
├── new_sds_count
└── updated_sds_count
```

### Klasyfikacja

```text
NEW
= pierwszy SDS dla PRODUCT

UPDATED
= każdy kolejny SDS dla PRODUCT
```

Technicznie klasyfikacja może używać:

- `ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY registered_at, sds_id)`,
- równoważnego podzapytania.

Remis czasu musi być deterministyczny.

Nie używać:

```text
issue_date
revision
filename
```

do określania kolejności zdarzeń w systemie.

---

## 15. Granularność trendu

Dla zakresu do około jednego roku:

```text
MONTH
```

jest domyślną granularnością MVP.

TDR-009 nie wprowadza dynamicznej zmiany:

```text
DAY / WEEK / MONTH / QUARTER
```

Jeżeli zakres przekroczy rok, nadal można agregować miesięcznie.

Nie tworzyć mechanizmu automatycznej zmiany granularności w pierwszym przyroście.

---

## 16. Status BHP DTO

Wizualizacja korzysta z:

```text
BhpStatusDistributionDto
├── approved
├── rejected
└── no_decision
```

Mianownik:

```text
PRODUCT z CURRENT SDS
```

Produkty bez CURRENT SDS nie trafiają do donut chart.

Nie tworzyć:

```text
W TRAKCIE
PENDING BHP
```

---

## 17. Manufacturer summary DTO

Minimalny wynik:

```text
ManufacturerSummaryRow
├── manufacturer_id
├── manufacturer_name
├── products_count
├── current_sds_count
├── bhp_approved_count
├── attention_products_count
└── latest_sds_registered_at
```

UI label dla ostatniej kolumny:

```text
Ostatni SDS
```

lub:

```text
Ostatnia rejestracja SDS
```

Preferowane:

```text
Ostatni SDS
```

ze względu na kompaktowy dashboard.

---

## 18. Szczegółowe PRODUCT × USAGE_LOCATION

Drugi poziom raportu ma read model:

```text
ProductLocationAnalyticsRow
```

Minimalnie:

```text
product_id
product_name
manufacturer_name

location_id
location_name

peak_quantity_value
peak_quantity_unit_code

monthly_consumption_value | None
monthly_consumption_unit_code | None

product_usage_status
current_sds_revision | None
current_sds_issue_date | None
bhp_category
```

Główne znaczenie ilościowe raportu:

```text
MAX = peak_quantity
```

Monthly consumption może być pokazane pomocniczo, ale nie może zastępować MAX.

### PRODUCT bez lokalizacji

Nie wolno go zgubić wskutek `INNER JOIN`.

Jeżeli filtr lokalizacji nie jest aktywny, PRODUCT bez aktywnej lokalizacji może być prezentowany jako:

```text
Lokalizacja = BRAK
```

zgodnie z obecnym wzorcem widoku nadzorczego.

---

## 19. Prezentacja — struktura strony

Zatwierdzony layout implementujemy jako jeden ekran:

```text
Analizy

[ filtry ]

[ KPI ][ KPI ][ KPI ][ KPI ][ KPI ]

[ Produkty wg producenta ]
[ Status BHP ]
[ Nowe / zaktualizowane SDS ]

[ Wymaga uwagi ]

[ Podsumowanie producentów ]

[ Zestawienie zbiorcze — PRODUCT × USAGE_LOCATION ]
```

Szczegółowe zestawienie może być:

```text
st.expander
```

lub sekcją poniżej dashboardu.

Preferowane MVP:

```text
expander domyślnie zamknięty
```

aby nie przeciążać pierwszego widoku.

---

## 20. `Wymaga uwagi`

Minimalne karty:

```text
Brak CURRENT SDS
Brak decyzji BHP
Brak aktywnego miejsca stosowania
Niedostępny dokument
```

Techniczny DTO może zawierać:

```text
AttentionSummaryDto
├── no_current_sds_count
├── no_bhp_decision_count
├── no_active_location_count
├── missing_source_file_count
└── affected_product_ids_by_reason
```

Lista `product_id` jest opcjonalna w pierwszym przyroście, jeżeli nie implementujemy jeszcze drill-down.

Nie implementować routingu do innych ekranów bez jawnego zakresu Tasku.

---

## 21. Technologia wykresów

Dla MVP preferowane:

```text
Streamlit st.vega_lite_chart
```

dla:

```text
bar chart
donut / arc chart
line / area chart
```

Powody:

- brak potrzeby nowego frameworka frontendowego,
- brak potrzeby React,
- brak potrzeby dodatkowej biblioteki wykresowej,
- wystarczająca kontrola wyglądu dla UX target.

Nie dodawać:

```text
Plotly
ECharts
custom JS component
```

jeżeli nie są już wymagane przez repozytorium.

Jeżeli aktualna wersja Streamlit nie obsługuje potrzebnego Vega-Lite:

```text
STOP
```

i zgłosić potrzebę decyzji o zależności / uproszczeniu wykresu.

---

## 22. KPI cards i styl

Dopuszczalne:

```text
st.container
st.columns
st.markdown
statyczny scoped CSS
```

dla odwzorowania targetu SaaS.

Zasady:

- nie wprowadzać custom JavaScript,
- nie wprowadzać zewnętrznych CDN,
- nie ładować zdalnych fontów,
- unikać globalnych hacków do losowych klas DOM Streamlit,
- nie renderować nieescaped user data w `unsafe_allow_html`.

Jeżeli KPI są renderowane jako HTML:

```text
wartości dynamiczne muszą być liczbami / jawnie escapowanym tekstem
```

---

## 23. Eksport

`Eksport` nie jest implementowany funkcjonalnie w TDR-009.

Pierwszy przyrost może:

```text
A. pominąć przycisk
lub
B. pokazać disabled "Eksport"
```

Preferowane:

```text
disabled "Eksport"
```

jeżeli pozwala zachować zatwierdzony UX target bez sugerowania działającej funkcji.

Aktywny eksport wymaga osobnego kontraktu:

```text
format
zakres danych
filtry
nazwa pliku
uprawnienia
```

---

## 24. Stany UI

### LOADING

Streamlit korzysta z:

```text
st.spinner
```

dla całości odczytu dashboardu.

Nie renderować częściowo sprzecznych KPI podczas trwania odczytu.

### NO_DATA

Jeżeli brak PRODUCT w zakresie filtrów:

```text
0 produktów dla wybranych filtrów
```

KPI = 0.

Wykresy:

```text
czytelny empty state
```

Nie tworzyć fikcyjnych zerowych serii.

### ERROR

Błąd query / filesystem availability:

```text
kontrolowany komunikat
brak stack trace dla operatora
```

Błąd availability pojedynczego pliku nie powinien blokować całego dashboardu, jeśli można bezpiecznie oznaczyć ten dokument jako:

```text
availability = UNKNOWN / CHECK_FAILED
```

Taki stan techniczny nie może być automatycznie liczony jako `MISSING`, jeżeli brak pewności.

---

## 25. Integralność i read-only

Cały obszar ANALYTICS-01 / 02 jest:

```text
READ ONLY
```

Nie dopuszcza się:

- INSERT,
- UPDATE,
- DELETE,
- zmian lifecycle,
- automatycznych korekt danych.

Po otwarciu dashboardu:

```text
database business state = unchanged
filesystem state = unchanged
```

---

## 26. Wydajność

W MVP priorytet:

```text
czytelność i poprawność
> mikrooptymalizacja
```

Jednocześnie obowiązuje:

```text
NO N+1
```

Liczba zapytań SQL na pełny render dashboardu ma być:

```text
stała względem liczby PRODUCT
```

Dopuszczalne jest kilka jawnych query read-side.

Preferowany układ:

```text
Q1 — ProductAnalyticsFact
Q2 — distinct active locations
Q3 — SDS trend
Q4 — PRODUCT × USAGE_LOCATION detail
```

Dodatkowe pojedyncze query są dopuszczalne, jeżeli upraszczają logikę i nie tworzą N+1.

Nie wymaga się materialized view dla optymalizacji MVP.

---

## 27. Ograniczenie szczegółowej tabeli

Szczegółowe:

```text
PRODUCT × USAGE_LOCATION
```

może rosnąć szybciej niż liczba PRODUCT.

MVP powinien:

- renderować tabelę dopiero po rozwinięciu sekcji lub na żądanie,
- nie wykonywać osobnego query na każdy wiersz,
- użyć jednego read query,
- respektować filtry.

Jeżeli `st.dataframe` obsługuje wymagany wolumen lokalnie, nie dodawać własnej paginacji.

Paginację projektować dopiero po realnym problemie wydajności.

---

## 28. Testy — Application

Wymagane testy semantyki co najmniej:

1. `Produkty ogółem` liczy DISTINCT PRODUCT,
2. `SDS CURRENT` liczy PRODUCT, nie rekordy SDS,
3. brak CURRENT SDS nie staje się ARCHIVED,
4. APPROVED dotyczy decyzji CURRENT dla CURRENT SDS,
5. REJECTED rozróżnione od NO_DECISION,
6. brak CURRENT SDS nie jest liczony jako NO_DECISION w donut,
7. `Braki` deduplikuje produkt spełniający kilka warunków,
8. INACTIVE / REJECTED nie dostaje alertu lokalizacji wg BDR-009,
9. aktywne stanowiska liczone DISTINCT,
10. filtry nie powodują zwielokrotnienia PRODUCT,
11. okres trendu nie zmienia KPI current-state,
12. `0` pozostaje wartością, nie NO_DATA.

---

## 29. Testy — PostgreSQL integration

Na izolowanym PostgreSQL wymagane scenariusze:

- PRODUCT bez SDS,
- PRODUCT z jednym CURRENT SDS,
- PRODUCT z CURRENT + ARCHIVED SDS,
- CURRENT SDS bez BHP_DECISION,
- CURRENT SDS + APPROVED,
- CURRENT SDS + REJECTED,
- wiele decyzji z jedną CURRENT,
- wiele lokalizacji jednego PRODUCT,
- jedna lokalizacja współdzielona przez wiele PRODUCT,
- PRODUCT bez lokalizacji,
- lokalizacja INACTIVE,
- dwóch producentów,
- pierwszy i kolejny SDS dla trendu,
- identyczne / bliskie timestamps — deterministyczne rozstrzygnięcie kolejności.

Operator DB nie jest środowiskiem testów integracyjnych.

---

## 30. Testy — filesystem availability

W izolowanych katalogach `tmp_path`:

- CURRENT SDS istnieje → AVAILABLE,
- CURRENT SDS brak → MISSING,
- evidence istnieje → AVAILABLE,
- evidence brak → MISSING,
- traversal / outside root → blocked / check failed,
- brak root → kontrolowany error,
- żaden test nie modyfikuje zarejestrowanego pliku.

---

## 31. Testy — Streamlit / UX smoke

Minimalnie:

- zakładka `Analizy` pojawia się w sidebar,
- brak danych → empty state,
- KPI renderują się,
- filtr producenta działa,
- filtr SDS działa,
- filtr BHP działa,
- filtr lokalizacji działa,
- okres trendu wpływa na trend,
- chart sections renderują się bez wyjątku,
- `Wymaga uwagi` renderuje poprawne liczby,
- `Podsumowanie producentów` renderuje tabelę,
- expander szczegółowego zestawienia działa,
- UUID nie jest podstawową informacją użytkową,
- brak działającego eksportu nie udaje sukcesu.

---

## 32. Expected change surface

Preferowany zakres implementacyjny:

```text
app/application/
  dto/
  ports/
  use_cases/

app/infrastructure/db/
  repositories/ lub read_models/

app/infrastructure/filesystem/
  tylko jeśli brak istniejącego availability contract

app/presentation/streamlit/

tests/
```

Nie oczekuje się zmian:

```text
migrations/
Core docs
Domain entities
existing lifecycle rules
pyproject.toml
```

Jeżeli implementacja wymaga schema change albo nowej dependency:

```text
STOP
```

---

## 33. Poza zakresem TDR-009

Nie obejmuje:

- ANALYTICS-03 `Stan na dzień`,
- snapshotów,
- historycznego `as-of`,
- aktywnego eksportu,
- osobnego BI,
- materialized views,
- AI,
- REACH,
- R8,
- parsera SDS,
- konfiguracji Ustawień,
- uprawnień użytkowników,
- React,
- custom JS frontend.

---

## 34. STOP conditions dla implementacji

Codex ma wykonać:

```text
STOP / BLOCKED
```

jeżeli:

1. KPI nie da się uzyskać bez zmiany zatwierdzonej semantyki BDR-009,
2. potrzebna jest zmiana Core,
3. potrzebna jest zmiana schema,
4. potrzebna jest migracja,
5. wymagany jest nowy status biznesowy,
6. wymagane jest założenie historycznego `as-of`,
7. brak bezpiecznego sposobu sprawdzenia dostępności pliku,
8. nie da się zachować rozdziału Streamlit → Application → Infrastructure,
9. wymagany jest nowy frontend framework,
10. potrzebna jest nowa dependency,
11. test wymaga użycia / modyfikacji danych operatora.

---

## 35. Proponowany podział wykonawczy

Po zatwierdzeniu TDR-009 preferowane są dwa małe Taski:

```text
TASK-A
Analytics read model + Application + PostgreSQL integration

TASK-B
Streamlit dashboard + charts + physical UX review
```

Pozwala to oddzielić:

```text
poprawność danych
od
warstwy prezentacji
```

Numeracja Tasków zostanie nadana dopiero przy przygotowaniu pakietu wykonawczego.

---

## 36. Zatwierdzone decyzje Architekta

Architekt Operacyjny zatwierdził:

```text
T1. Jeden read-side use case GetAnalyticsDashboard.

T2. ProductAnalyticsFact = 1 rekord na PRODUCT
    jako wspólna baza KPI / statusów / alertów.

T3. Bounded SQL queries / NO N+1.

T4. MISSING jako runtime availability overlay
    z użyciem istniejących bezpiecznych portów filesystem.

T5. Wykresy przez st.vega_lite_chart
    bez nowej biblioteki frontendowej.

T6. Szczegółowe PRODUCT × USAGE_LOCATION
    jako expander / sekcja ładowana na żądanie.

T7. Brak cache biznesowego w pierwszym MVP.

T8. Brak aktywnego eksportu w TDR-009;
    disabled placeholder jest dopuszczalny.

T9. Dwa Taski implementacyjne:
    read model/data correctness → dashboard/UX.
```

---

## 37. Status

```text
TDR-009 v1.0-approved
APPROVED
```

Następny krok:

```text
Task 1
→ analytics read model
→ Application
→ PostgreSQL integration
→ testy semantyki / integracyjne

Task 2
→ Streamlit dashboard
→ wykresy
→ UX target
→ physical review
```

Każdy Task wymaga osobnej, jawnej autoryzacji Architekta Operacyjnego.

