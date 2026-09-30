# TASK-034 — Application + UI Integration dla UNIT_OF_MEASURE

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-007 — DATA-01 — Słownik jednostek miary  
**Task:** TASK-034  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-09-30  
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

Zintegrować wdrożony w TASK-033 `UNIT_OF_MEASURE` z warstwą Application, read modelami i istniejącym UI Streamlit tak, aby użytkownik:

```text
nie wpisywał jednostek jako free-text
→ wybierał wyłącznie jednostki ACTIVE
→ widział kody jednostek w danych bieżących
→ nie widział technicznych unit_id w normalnym workflow
```

Zakres obejmuje oba pola ilościowe relacji:

```text
PRODUCT × USAGE_LOCATION
├── peak_quantity
└── monthly_consumption
```

TASK-034 nie zmienia schema i nie tworzy nowej migracji Alembic.

---

## AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie kontekst potrzebny do tego Tasku:

1. `SPRINT-007_DATA-01_Slownik_jednostek_v1.0-approved`
2. `TDR-005_UNIT_OF_MEASURE_v1.0-approved`
3. `CORE-001_MSDS_Manager_v1.2-approved`
4. `TASK-033_REPORT.md` — końcowy raport `STATUS: DONE`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
6. root `AGENTS.md`

Nie wykonuj repo-wide rediscovery bez konkretnej potrzeby.

Jeżeli implementacja wymaga zmiany decyzji biznesowej, Core lub schema:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

TASK-033 pozostawił gotowy fundament:

```text
unit_of_measure
UnitOfMeasure
UnitOfMeasureRepository
get_by_id()
list_active()

product_usage_locations:
peak_quantity_unit_id
monthly_consumption_unit_id

product_usage_location_history:
peak_quantity_unit_id
monthly_consumption_unit_id
```

Aktualny Alembic head po TASK-033:

```text
a97e2cb7f31d
```

Minimalnie zlokalizuj bezpośrednie implementacje / odpowiedniki symboli:

```text
AssignProductUsageLocation
UpdateProductUsageLocation
GetProductDetails
ListSupervisoryProducts

ProductUsageLocation repository / mapping
ProductUsageLocation history snapshot

Streamlit:
Produkty → Miejsca stosowania
formularz dodawania przypisania
formularz edycji przypisania
Widok nadzorczy
```

Jeżeli nazwy plików różnią się od nazw symboli, znajdź ich bezpośrednie odpowiedniki. Nie rozszerzaj eksploracji poza potrzebny zakres.

---

## EXPECTED CHANGE SURFACE

Oczekiwane obszary zmian:

```text
app/application/
app/domain/                 # tylko jeśli konieczne do kontraktów Application
app/infrastructure/         # read/write mapping, bez schema change
app/presentation/streamlit/
tests/
```

Nie oczekuje się zmian w:

```text
migrations/
Alembic schema
CORE
BDR
TDR
parserze SDS
```

Jeżeli zmiana schema okaże się konieczna:

```text
STOP
```

---

## DO

### 1. Application — kontrolowana jednostka zamiast free-text

Dostosuj:

```text
AssignProductUsageLocation
UpdateProductUsageLocation
```

tak, aby zapis operował na:

```text
peak_quantity_unit_id
monthly_consumption_unit_id
```

a nie na dowolnym tekście jednostki.

Application ma być właścicielem reguły:

```text
nowy / edytowany zapis ilościowy
→ jednostka musi istnieć
→ jednostka musi mieć status ACTIVE
```

Nie wolno przenosić tej reguły wyłącznie do Streamlit.

---

### 2. Walidacja jednostki MAX

Dla MAX obowiązuje:

```text
peak_quantity_value
→ wymagane
→ Decimal
→ >= 0

peak_quantity_unit_id
→ wymagane
→ istniejące UNIT_OF_MEASURE
→ status ACTIVE przy nowym / edytowanym zapisie
```

Brak prawidłowej jednostki ma powodować kontrolowany błąd Application, a nie błąd FK z bazy.

---

### 3. Walidacja monthly consumption

Zachowaj semantykę Core:

```text
monthly_consumption_value = NULL
→ monthly_consumption_unit_id = NULL

monthly_consumption_value = 0
→ prawidłowa wartość biznesowa
→ monthly_consumption_unit_id wymagane

monthly_consumption_value > 0
→ monthly_consumption_unit_id wymagane
```

Jeżeli monthly value istnieje:

```text
jednostka musi istnieć
i być ACTIVE
```

Nie utożsamiaj `0` z brakiem wartości.

---

### 4. Historia

Istniejący mechanizm TDR-004 pozostaje bez zmian.

Przy zmianie danych PRODUCT × USAGE_LOCATION:

```text
current state
+
history snapshot
=
ONE TRANSACTION
```

Snapshot musi zachować:

```text
peak_quantity_unit_id
monthly_consumption_unit_id
```

Zmiana samej jednostki jest istotną zmianą biznesową i musi być odtwarzalna w historii.

Nie przebudowuj mechanizmu historii.

---

### 5. UnitOfMeasure repository / port

Wykorzystaj fundament TASK-033.

Minimalne operacje:

```text
list_active()
get_by_id(unit_id)
```

Nie twórz pełnego CRUD.

Nie implementuj:

```text
create/edit/delete UNIT_OF_MEASURE
```

w UI.

Jeżeli TASK-033 już dostarczył potrzebny port/repository, nie duplikuj go — tylko użyj.

---

### 6. Read models / DTO

Dostosuj read-side tak, aby dane użytkowe mogły prezentować co najmniej:

```text
unit_id      # techniczne, jeśli potrzebne Application/UI do wyboru
unit_code    # użytkowe
```

Dopuszczalne jest użycie istniejącego DTO `UnitOfMeasure` / równoważnego kontraktu, jeżeli nie wymaga tworzenia zbędnej warstwy.

W normalnej prezentacji użytkowej pokazuj:

```text
l
ml
kg
g
szt
```

Nie pokazuj UUID jako informacji operacyjnej.

---

### 7. Product details — Miejsca stosowania

W istniejącej sekcji:

```text
Produkty
→ wybrany PRODUCT
→ Miejsca stosowania
```

dostosuj tabelę przypisań do nowego modelu.

Użytkownik ma widzieć:

```text
Lokalizacja
Maksymalna ilość na stanowisku
Jednostka [code]
Zużycie miesięczne
Jednostka [code]
```

Dane istniejące z jednostką `INACTIVE` muszą pozostawać odczytywalne.

Nie ukrywaj historycznie/prawidłowo zapisanej wartości tylko dlatego, że jednostka została później dezaktywowana.

---

### 8. Formularz dodania przypisania

Zastąp pola free-text jednostek kontrolowanym wyborem z:

```text
list_active()
```

Dla MAX:

```text
Jednostka
→ wybór wymagany
```

Dla monthly:

```text
monthly value NULL
→ unit może pozostać NULL

monthly value podane, w tym 0
→ unit wymagane
```

W selectboxie / kontrolce pokazuj użytkownikowi `code` jednostki, nie UUID.

---

### 9. Formularz edycji przypisania

Edycja korzysta z tych samych reguł:

```text
nowy zapis po edycji
→ wyłącznie ACTIVE
```

Jeżeli istniejący rekord wskazuje jednostkę `INACTIVE`:

- rekord pozostaje poprawnie odczytywalny,
- UI nie proponuje `INACTIVE` jako nowego wyboru,
- zapis edycji danych ilościowych wymaga wyboru jednostki `ACTIVE` zgodnie z TDR-005.

Nie twórz automatycznej zamiany jednostki.

---

### 10. Widok nadzorczy

Zachowaj istniejący kontrakt:

```text
1 PRODUCT × 1 aktywna USAGE_LOCATION
= 1 wiersz nadzorczy
```

Nie zmieniaj istniejących filtrów ani `requires_action`, jeśli nie jest to bezpośrednio konieczne.

Dostosuj kolumny ilościowe tak, aby prezentowały:

```text
peak quantity + unit code
monthly consumption + unit code
```

lub zachowały istniejące oddzielne kolumny wartości/jednostki, jeżeli taki układ jest obecnie używany.

Nie pokazuj `unit_id`.

---

### 11. Brak konwersji

TASK-034 nie może wprowadzić:

```text
kg ↔ g
l ↔ ml
```

Nie dodawaj:

- conversion factor,
- base unit,
- normalizacji wartości,
- przeliczeń po kategorii,
- przeliczeń przez gęstość.

UI wybiera jednostkę; Application waliduje referencję.

---

## DO NOT

Nie:

- twórz nowej migracji Alembic,
- zmieniaj schema z TASK-033,
- implementuj CRUD słownika jednostek,
- implementuj ekran administracyjny `UNIT_OF_MEASURE`,
- implementuj `Analizy`,
- implementuj `Stan na dzień`,
- implementuj DOC-01 / UI-11 / UI-14,
- rozwijaj parsera SDS,
- implementuj PARSER-02 / PARSER-03,
- implementuj REACH,
- importuj starego Excela,
- heurystycznie mapuj legacy units,
- automatycznie modyfikuj danych operatora,
- wykonuj konwersji jednostek,
- zmieniaj semantyki `0 / NULL`,
- zmieniaj TDR-004,
- refaktoruj niezwiązanych modułów,
- dodawaj nowych dependencies bez konieczności i decyzji.

---

## VALIDATION

**LEVEL 2 — INTEGRATION**

Wykonaj focused + integration validation dla zmienionego zakresu.

Minimum:

### Application / Domain

```text
1. Assign: ACTIVE unit → PASS
2. Assign: INACTIVE unit → controlled rejection
3. Assign: unknown unit_id → controlled rejection
4. Update: ACTIVE unit → PASS
5. Update: INACTIVE unit → controlled rejection
6. MAX bez unit → rejection
7. monthly NULL + unit NULL → PASS
8. monthly 0 + ACTIVE unit → PASS
9. monthly value + unit NULL → rejection
10. monthly value + INACTIVE unit → rejection
```

### History / persistence

```text
11. zmiana peak unit → snapshot zawiera poprzedni stan i unit_id
12. zmiana monthly unit → snapshot zachowuje unit_id
13. current + history pozostają w jednej transakcji
14. istniejąca referencja do INACTIVE pozostaje odczytywalna
```

### Read models

```text
15. Product details zwraca code jednostki
16. Supervisory read model zwraca code jednostki
17. brak regresji PRODUCT bez lokalizacji
18. brak regresji 0 != NULL
```

### Streamlit focused tests / AppTest

```text
19. add usage: jednostka MAX = kontrolowany wybór
20. add usage: lista zawiera ACTIVE
21. add usage: UI nie przyjmuje free-text jednostki
22. edit usage: lista wyboru zawiera ACTIVE
23. monthly empty zachowuje NULL/NULL
24. monthly = 0 wymaga jednostki
25. Product details pokazuje unit code
26. Widok nadzorczy pokazuje unit code
27. UUID jednostki nie jest eksponowany użytkownikowi
```

### Safety / regression

Uruchom regresję powiązanego obszaru:

```text
PRODUCT × LOCATION
history
supervisory read model
Streamlit usage workflow
```

Nie uruchamiaj pełnej regresji całego projektu wyłącznie z powodu TASK-034.

Pełny pytest / E2E / LEVEL 3 należy do TASK-035.

Nie wykonuj upgrade/downgrade migracji ponownie — TASK-033 już to udowodnił i TASK-034 nie zmienia schema.

Jeżeli ORM/schema zostaną nieoczekiwanie zmienione:

```text
STOP
```

---

## ACCEPTANCE CONDITIONS

TASK-034 = DONE tylko jeśli:

```text
free-text unit input usunięty z add/edit usage UI

lista wyboru jednostek pochodzi z ACTIVE UNIT_OF_MEASURE

Application odrzuca:
- unknown unit_id
- INACTIVE dla nowego/edytowanego zapisu

MAX:
- unit wymagane

monthly:
- NULL → unit NULL
- 0 → unit wymagane
- >0 → unit wymagane

Product details:
- pokazuje unit code

Widok nadzorczy:
- pokazuje unit code
- nie pokazuje unit UUID

history:
- unit_id zachowane w snapshotach
- zmiana jednostki jest odtwarzalna

schema:
- bez zmian względem TASK-033

migration:
- NONE

conversion engine:
- NONE
```

---

## STOP CONDITIONS

Zatrzymaj Task jako `BLOCKED`, jeżeli:

1. implementacja wymaga nowej migracji lub zmiany schema,
2. model TASK-033 nie wystarcza do bezpiecznej integracji bez zmiany TDR-005,
3. istniejące use case'y nie mają jednoznacznej granicy Application dla walidacji ACTIVE,
4. poprawne zachowanie wymaga automatycznej konwersji jednostek,
5. poprawne zachowanie wymaga heurystycznego mapowania danych legacy,
6. historia jednostek wymaga zmiany mechanizmu TDR-004,
7. UI wymaga nowego frameworka/dependency,
8. realizacja zaczyna wymagać repo-wide refactor,
9. pojawia się konflikt pomiędzy CORE-001 v1.2, TDR-005 i stanem po TASK-033.

Po minimalnej uzasadnionej diagnostyce:

```text
STOP / BLOCKED
→ krótki raport
→ bez opportunistic fix
```

---

## REPORT

**SHORT REPORT**

Raport ma zawierać:

```text
STATUS: DONE / BLOCKED

CHANGED:
- Application
- Repositories/read models
- Streamlit
- Tests

IMPLEMENTED:
- ACTIVE unit selection
- MAX validation
- monthly NULL/0 validation
- Product details display
- supervisory display
- history unit preservation

VALIDATION:
- focused tests
- PostgreSQL integration
- Streamlit/AppTest
- related regression
- SAWarning dla uruchamianego zestawu, jeśli dotyczy

SCOPE:
- schema change: NO
- migration: NONE
- conversion engine: NONE
- legacy mapping: NONE
- new dependencies: NONE albo jawnie opisana konieczność

RISKS / DEVIATIONS:
- NONE albo lista

NEXT:
- READY FOR TASK-035 / BLOCKED
```

Nie twórz repo-wide raportu bez potrzeby.

---

## AUTHORIZATION

```text
TASK-034
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Task może zostać wykonany dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-034
```
