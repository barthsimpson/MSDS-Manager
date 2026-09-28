# TASK-031 — Miejsca stosowania + Widok nadzorczy PRODUCT × LOCATION

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Task ID:** TASK-031  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** SHORT  
**Status:** READY  
**Wykonawca:** Codex OpenAI

---

## GOAL

Uporządkować obsługę miejsc stosowania produktu oraz przebudować istniejący widok nadzorczy z agregacji:

```text
1 PRODUCT = 1 wiersz
```

na zatwierdzony w SPRINT-006 model prezentacyjny:

```text
1 PRODUCT × 1 aktywna USAGE_LOCATION = 1 wiersz
```

tak, aby użytkownik widział dla konkretnego miejsca stosowania:

```text
Maksymalną ilość
Jednostkę
Zużycie miesięczne
Jednostkę
```

Task zmienia **read model i prezentację**, ale nie zmienia Core ani schema.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `SPRINT-006_UI_MVP_v1.0-approved.md`,
- ten TASK,
- `TASK-030_REPORT.md`,
- istniejący kod obsługi miejsc stosowania,
- istniejący supervisory read model z TASK-026,
- istniejący Streamlit `Widok nadzorczy`,
- bezpośrednio powiązane focused/integration/AppTests.

Nie czytaj ponownie całego CORE/BDR/TDR/history bez konkretnej potrzeby.

Jeżeli realizacja wymaga zmiany Core, schema, migracji lub nowej reguły biznesowej:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

Zweryfikuj lokalnie przede wszystkim:

```text
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/supervisory.py
app/presentation/streamlit/composition.py
```

Supervisory read-side:

```text
app/application/dto/supervisory.py
app/application/ports/supervisory_query.py
app/application/use_cases/list_supervisory_products.py
app/infrastructure/db/repositories/supervisory_query.py
```

Istniejące testy:

```text
tests/unit/test_task026_supervisory.py
tests/integration/test_task026_supervisory_read_model_postgresql.py
tests/unit/test_streamlit_supervisory.py
testy product_registry / usage assignments
```

Użyj istniejących use case'ów przypisania i aktualizacji miejsc stosowania.

Nie twórz równoległego workflow.

---

# CZĘŚĆ A — Miejsca stosowania w szczegółach produktu

## 1. Istniejące przypisania jako tabela

W szczegółach wybranego produktu sekcja:

```text
Miejsca stosowania
```

ma najpierw pokazywać istniejące przypisania w zwartej tabeli.

Minimalne kolumny:

| Lokalizacja | Maksymalna ilość | Jednostka | Zużycie miesięczne | Jednostka |
|---|---:|---|---:|---|
| Regeneracja | 25 | l | 100 | l |
| MZT_Mag.Techniczny | 300 | l | 10 | l |

Nie pokazuj technicznych UUID.

---

## 2. Oddziel dodawanie od istniejących przypisań

Pod tabelą / po akcji pokaż:

```text
+ Dodaj miejsce stosowania
```

Dopiero ta akcja otwiera formularz nowego przypisania.

Nie pokazuj stale pustego formularza nowego przypisania obok istniejących danych.

---

## 3. Oddziel edycję od dodawania

Użytkownik powinien móc wybrać istniejące przypisanie i przejść do:

```text
Edytuj przypisanie
```

Preferowany UX:

```text
wybór wiersza istniejącej tabeli
→ Edytuj przypisanie
```

Jeżeli row-selection nie jest stabilny w używanej wersji Streamlit, zastosuj minimalny fallback.

Nie aktualizuj dependencies.

Nie mieszaj w jednym formularzu:

```text
nowego przypisania
+
edycji istniejącego przypisania
```

---

## 4. Przyjazne etykiety

Zastąp techniczne etykiety:

```text
Peak quantity nowego przypisania
Jednostka peak nowego przypisania
```

użytkowymi:

```text
Maksymalna ilość na stanowisku
Jednostka
Zużycie miesięczne
Jednostka
```

W edycji i dodawaniu używaj tych samych nazw.

Nie zmieniaj nazw pól Domain/DTO/DB.

---

## 5. Semantyka ilości pozostaje bez zmian

Zachowaj istniejące reguły:

```text
peak >= 0
monthly = None lub >= 0
monthly value + unit tworzą spójną parę
0 != None
```

Nie dodawaj konwersji jednostek.

Nie zmieniaj walidacji Domain/Application.

---

## 6. Jednostki pozostają tekstowe w tym Sprincie

**DATA-01 — słownik jednostek miary jest świadomie poza TASK-031.**

Nie implementuj:

```text
UNIT_OF_MEASURE
dropdownu z nowej tabeli
migracji jednostek
normalizacji l/L/litr
```

W tym Tasku poprawiamy wyłącznie prezentację etykiet.

---

# CZĘŚĆ B — Supervisory read model

## 7. Zmiana jednostki wiersza

Istniejący read model agreguje aktywne lokalizacje do jednego PRODUCT.

TASK-031 świadomie zmienia tę prezentację.

Nowa reguła:

```text
PRODUCT z 2 aktywnymi lokalizacjami
→ 2 wiersze nadzorcze
```

Przykład:

```text
IDROLIN | Regeneracja          | 25  | l | 100 | l
IDROLIN | MZT_Mag.Techniczny   | 300 | l | 10  | l
```

To **nie jest duplikacja PRODUCT w Core**.

To jest read model:

```text
PRODUCT × PRODUCT_USAGE_LOCATION × active USAGE_LOCATION
```

---

## 8. Produkt bez aktywnej lokalizacji

Produkt bez aktywnego miejsca stosowania **nie może zniknąć** z widoku.

Ma powstać dokładnie jeden wiersz:

```text
Produkt | Lokalizacja = Brak
```

Pola ilości:

```text
Maksymalna ilość = —
Jednostka = —
Zużycie miesięczne = —
Jednostka = —
```

Istniejący reason:

```text
BRAK MIEJSCA STOSOWANIA
```

pozostaje.

---

## 9. Aktywne lokalizacje

Read model nadzorczy pokazuje wyłącznie aktywne `USAGE_LOCATION`, zgodnie z dotychczasowym zachowaniem.

`INACTIVE` location nie tworzy wiersza nadzorczego.

Nie zmieniaj historycznych relacji ani danych.

---

## 10. Ilości w read modelu

Dla każdego aktywnego przypisania zwróć:

```text
usage_location_name
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Zachowaj różnicę:

```text
monthly = None → brak danych
monthly = 0    → jawne zero
```

Nie wykonuj konwersji jednostek ani sumowania między lokalizacjami.

---

## 11. CURRENT SDS i BHP pozostają produktowe

Każdy wiersz lokalizacji tego samego produktu pokazuje ten sam bieżący stan:

```text
CURRENT SDS
issue_date
revision
PRODUCT usage_status
CURRENT BHP decision
current BHP notes
action reasons
```

Nie zmieniaj reguł TASK-026 dotyczących:

```text
CURRENT / ARCHIVED
CURRENT / SUPERSEDED
file availability
requires_action
action_reasons
```

Nie duplikuj tych reguł w Infrastructure ani Streamlit.

---

## 12. `requires_action`

Reguły pozostają na poziomie aktualnego stanu produktu.

Jeżeli produkt ma dwie aktywne lokalizacje i wymaga działania z powodu BHP:

```text
oba wiersze pokazują ten sam powód BHP
```

Jeżeli produkt ma co najmniej jedną aktywną lokalizację:

```text
BRAK MIEJSCA STOSOWANIA
```

nie występuje.

Jeżeli nie ma żadnej aktywnej lokalizacji:

```text
powstaje jeden wiersz "Brak"
+
BRAK MIEJSCA STOSOWANIA
```

---

## 13. Wydajność read-side

Preferuj zachowanie obecnego wzorca bez N+1.

Istniejący adapter TASK-026 wykonuje:

```text
1 SELECT — PRODUCT + MANUFACTURER + CURRENT SDS + CURRENT BHP
1 SELECT — usage locations
```

Można rozszerzyć drugi SELECT o ilości i rozwinąć wiersze w pamięci.

Nie twórz zapytania osobno dla każdego produktu.

Nie wprowadzaj cache.

---

# CZĘŚĆ C — Widok nadzorczy UI

## 14. Minimalne kolumny

Tabela ma pokazywać:

| Kolumna | Znaczenie |
|---|---|
| Produkt | product_name |
| Producent | manufacturer |
| Kod | manufacturer_product_code |
| Lokalizacja | konkretna aktywna lokalizacja / Brak |
| Maks. ilość | peak_quantity |
| Jedn. | peak unit |
| Zużycie mies. | monthly consumption |
| Jedn. zużycia | monthly unit |
| SDS | status CURRENT / brak / missing |
| Data SDS | issue_date |
| Rewizja | revision |
| Status produktu | usage_status |
| BHP | APPROVED / REJECTED / brak |
| Warunki | current_bhp_notes |
| Wymaga działania | action reasons / OK |

Dopuszczalne są krótsze nagłówki dla czytelności.

---

## 15. Formatowanie wartości pustych

W UI:

```text
None → —
```

Dotyczy to m.in.:

```text
data SDS
rewizja
monthly consumption
monthly unit
notes
```

Jawne `0` musi być pokazane jako:

```text
0
```

a nie `—`.

---

## 16. Filtry

Nad tabelą dodaj / zachowaj:

```text
Szukaj produktu
Status produktu
Lokalizacja
BHP
Wszystkie / Wymagają działania
```

### Szukaj produktu

Proste wyszukiwanie case-insensitive po nazwie produktu.

Nie buduj full-text search.

### Status produktu

Filtr po istniejącym `usage_status`.

### Lokalizacja

Filtr po pojedynczej lokalizacji read modelu.

Preferowane opcje:

```text
Wszystkie
<aktywne lokalizacje>
Brak miejsca
```

### BHP

Filtr:

```text
Wszystkie
Dopuszczony
Niedopuszczony
Brak decyzji
```

przy zachowaniu wewnętrznych enumów.

### Wymaga działania

Zachowaj:

```text
Wszystkie
Wymagają działania
```

Nie dodawaj severity/scoring.

---

## 17. Read-only

`Widok nadzorczy` pozostaje read-only.

Nie dodawaj w tabeli:

```text
edycji
delete
zmiany BHP
przypisania lokalizacji
masowych operacji
```

Akcje nadal należą do odpowiednich ekranów operacyjnych.

---

# CZĘŚĆ D — Granice znanych backlogów

## 18. Nie implementuj przy okazji

Podczas walkthrough zapisano przyszłe wymagania:

```text
UI-11 — otwieranie/pobieranie CURRENT SDS z tabeli
DATA-01 — słownik jednostek
UI-12 — nazwa "Data wystawienia SDS"
UI-13 — rewizja SDS w głównej tabeli Produkty
DOC-01 — dodawanie SDS z komputera
UI-14 / DOC-02 — podgląd dowodu BHP
```

Nie implementuj ich w TASK-031.

Wyjątek:

```text
Rewizja SDS w Widoku nadzorczym
```

jest już zatwierdzonym wymaganiem SPRINT-006 i należy do tego Tasku.

---

# ARCHITECTURE

## 19. Granice warstw

Zachowaj:

```text
PostgreSQL / repositories
        ↓
Application supervisory read model
        ↓
Streamlit
```

Streamlit nie:

- wykonuje SQL,
- importuje ORM,
- wyznacza CURRENT,
- interpretuje BHP,
- wylicza `requires_action`,
- sumuje ilości,
- tworzy dane lokalizacji.

Logika prezentacyjna filtrów może pozostać w UI.

---

# DO NOT

Nie:

- zmieniaj Core,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- zmieniaj modelu `PRODUCT_USAGE_LOCATION`,
- zmieniaj walidacji ilości,
- dodawaj słownika jednostek,
- wykonuj konwersji jednostek,
- zmieniaj lifecycle SDS/BHP,
- rozwijaj parsera,
- dodawaj upload/download/viewer,
- implementuj R8/R10/R11,
- dodawaj dashboardów/KPI/wykresów,
- dodawaj ISSUE/workflow/scoring,
- refaktoryzuj niezwiązanych modułów,
- rozpoczynaj TASK-032.

---

# EXPECTED CHANGE SURFACE

Przewidywany zakres:

```text
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/supervisory.py

app/application/dto/supervisory.py
app/application/ports/supervisory_query.py          # tylko jeśli kontrakt wymaga korekty
app/application/use_cases/list_supervisory_products.py

app/infrastructure/db/repositories/supervisory_query.py

app/presentation/streamlit/composition.py           # tylko jeśli kontrakt wywołania się zmienia

tests/unit/test_task026_supervisory.py
tests/integration/test_task026_supervisory_read_model_postgresql.py
tests/unit/test_streamlit_supervisory.py
testy product_registry / usage assignments

docs/task_reports/TASK-031_REPORT.md
```

Nie zmieniaj nazw istniejących plików bez potrzeby.

### DO NOT TOUCH

Jeżeli nie ma bezpośredniej konieczności:

```text
Domain
ORM models
Alembic
SDS persistence
BHP persistence
PDF parser
filesystem validators
```

---

# VALIDATION — LEVEL 2

## A. Miejsca stosowania UI

Focused tests:

1. brak przypisań → czytelny pusty stan,
2. jedno przypisanie → jeden wiersz tabeli,
3. dwa przypisania → dwa wiersze,
4. peak `0` pokazuje `0`,
5. monthly `None` pokazuje `—`,
6. monthly `0` pokazuje `0`,
7. formularz dodania jest oddzielony od tabeli,
8. formularz edycji jest oddzielony od dodania,
9. etykiety są użytkowe,
10. istniejące use case'y add/update nadal są wywoływane bez zmiany kontraktów.

Nie testuj ponownie pełnej walidacji Domain ilości.

---

## B. Supervisory Application / read model

Focused unit tests:

1. PRODUCT + 1 aktywna location → 1 wiersz,
2. PRODUCT + 2 aktywne locations → 2 wiersze,
3. PRODUCT bez aktywnej location → 1 wiersz z location `None`,
4. inactive location nie tworzy wiersza,
5. peak/monthly są przypisane do właściwej lokalizacji,
6. monthly `None` i `0` pozostają rozróżnione,
7. `requires_action` produktu jest poprawnie propagowane na jego wiersze,
8. brak aktywnej lokalizacji nadal daje `BRAK MIEJSCA STOSOWANIA`,
9. reguły CURRENT SDS/BHP nie ulegają zmianie.

---

## C. PostgreSQL integration

Wymagane, ponieważ zmienia się read model i adapter danych.

Potwierdź na rzeczywistym PostgreSQL:

```text
PRODUCT A
├── Location 1: peak 25 l, monthly 100 l
└── Location 2: peak 300 l, monthly 10 l
```

wynik:

```text
2 wiersze
z poprawnymi ilościami
```

oraz:

```text
PRODUCT B bez aktywnych locations
→ 1 wiersz "Brak"
```

Potwierdź brak N+1 w oczywistym zakresie.

Preferuj zachowanie maksymalnie stałej liczby SELECT zgodnej z istniejącym wzorcem TASK-026.

---

## D. Streamlit supervisory AppTests

Potwierdź:

1. nowe kolumny są widoczne,
2. PRODUCT z dwiema lokalizacjami daje dwa wiersze,
3. produkt bez lokalizacji pozostaje widoczny,
4. `None → —`,
5. `0 → 0`,
6. filtr produktu działa,
7. filtr statusu działa,
8. filtr lokalizacji działa,
9. filtr BHP działa,
10. filtr `Wymagają działania` działa,
11. filtry łączą się poprawnie,
12. pusta baza nadal działa,
13. kontrolowany read error nadal działa.

---

## E. Related regression

Uruchom focused regression powiązanego obszaru:

```text
usage locations
supervisory read model
supervisory UI
product registry
```

Nie uruchamiaj pełnego repo-wide pytest bez konkretnej przyczyny.

Pełna regresja, SAWarning, Alembic i E2E są obowiązkowe w:

```text
TASK-032 — UI MVP Acceptance / Checkpoint
```

---

# ACCEPTANCE CRITERIA

TASK-031 = DONE, gdy:

1. istniejące miejsca stosowania są pokazane w osobnej tabeli,
2. dodawanie lokalizacji jest osobnym formularzem,
3. edycja istniejącego przypisania jest oddzielona od dodawania,
4. etykiety `peak` są zastąpione językiem użytkowym,
5. nie dodano słownika jednostek ani zmiany schema,
6. supervisory read model zwraca jeden wiersz na PRODUCT × aktywna LOCATION,
7. produkt bez lokalizacji nadal ma jeden wiersz,
8. peak i monthly są widoczne dla konkretnej lokalizacji,
9. `None` i `0` są poprawnie rozróżniane,
10. CURRENT SDS/BHP i `requires_action` działają jak wcześniej,
11. widok nadzorczy ma wymagane kolumny,
12. działa 5 zatwierdzonych grup filtrów,
13. widok pozostaje read-only,
14. brak Core/schema/migration/dependency changes,
15. focused tests PASS,
16. PostgreSQL integration PASS,
17. nie rozpoczęto TASK-032.

---

# PHYSICAL REVIEW

Po wykonaniu Tasku Architekt Operacyjny wykona dwa testy.

## 1. Miejsca stosowania

Na produkcie z co najmniej dwoma lokalizacjami:

```text
Produkty
→ wybierz PRODUCT
→ Miejsca stosowania
```

Sprawdzi:

```text
tabelę istniejących przypisań
peak
monthly
osobne Dodaj
osobne Edytuj
przyjazne etykiety
```

---

## 2. Widok nadzorczy

Dla produktu z dwiema lokalizacjami oczekiwane:

```text
2 osobne wiersze
```

Dla produktu bez lokalizacji:

```text
1 wiersz
Lokalizacja = Brak
```

Sprawdzi również filtry:

```text
produkt
status
lokalizacja
BHP
wymaga działania
```

---

# STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. PRODUCT × LOCATION wymaga zmiany schema,
2. pobranie peak/monthly wymaga zmiany Core,
3. istniejący port/read model nie może zostać bezpiecznie rozszerzony bez nowej decyzji architektonicznej,
4. poprawna implementacja wymaga N+1 query jako jedynego rozwiązania,
5. oddzielenie add/edit wymaga zmiany kontraktów biznesowych zamiast UI,
6. konieczna jest nowa dependency,
7. implementacja zaczyna wymagać słownika jednostek,
8. Task zaczyna realizować backlog dokumentów/upload/download,
9. potrzebna jest zmiana lifecycle SDS/BHP.

Nie obchodź blokera logiką w Streamlit.

---

# REPORT — SHORT

Utwórz:

```text
docs/task_reports/TASK-031_REPORT.md
```

Format:

```text
# TASK-031 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

USAGE LOCATIONS UI:
- existing assignments table: YES / NO
- add form separated: YES / NO
- edit form separated: YES / NO
- user-friendly quantity labels: YES / NO
- unit dictionary added: NO / YES
- existing use cases preserved: YES / NO

SUPERVISORY READ MODEL:
- row unit = PRODUCT x LOCATION: YES / NO
- multiple locations -> multiple rows: YES / NO
- product without location preserved: YES / NO
- peak quantity included: YES / NO
- monthly consumption included: YES / NO
- None vs 0 preserved: YES / NO
- CURRENT SDS/BHP rules unchanged: YES / NO
- requires_action rules unchanged: YES / NO
- N+1 avoided: YES / NO

SUPERVISORY UI:
- required columns: YES / NO
- product search: YES / NO
- status filter: YES / NO
- location filter: YES / NO
- BHP filter: YES / NO
- requires-action filter: YES / NO
- read-only: YES / NO

VALIDATION:
- focused usage UI tests: ...
- focused supervisory unit tests: ...
- PostgreSQL integration: ...
- supervisory AppTests: ...
- related regression: ...

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- unit dictionary: NONE
- SDS/BHP lifecycle: NONE

RISKS / DEVIATIONS:
- NONE / ...

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-032.
```

---

# AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-031.
```
