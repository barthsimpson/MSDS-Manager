# TDR-005 — Techniczny model słownika jednostek miary

**Projekt:** MSDS Manager  
**Dokument:** TDR-005  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-09-29  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Podstawa biznesowa:** BDR-006 v1.0-approved  
**Podstawa Core:** CORE-001 v1.2-approved  

---

## 1. Cel decyzji

Celem TDR-005 jest zdefiniowanie minimalnego technicznego sposobu wdrożenia zatwierdzonego słownika:

```text
UNIT_OF_MEASURE
```

dla:

```text
PRODUCT_USAGE_LOCATION.peak_quantity
PRODUCT_USAGE_LOCATION.monthly_consumption
```

oraz dla istniejącej historii:

```text
PRODUCT_USAGE_LOCATION_HISTORY
```

TDR-005 nie implementuje `Analizy`, `Stan na dzień`, konwersji jednostek ani importu danych legacy.

---

## 2. Zasada nadrzędna

Implementacja ma być możliwie mała i jawna:

```text
kontrolowany słownik jednostek
→ referencje FK
→ istniejące use case'y ilościowe
→ istniejący mechanizm historii
```

Nie powstaje osobny framework jednostek, silnik konwersji ani warstwa normalizacji fizycznej.

---

## 3. Model tabeli UNIT_OF_MEASURE

Zatwierdza się jedną tabelę:

```text
unit_of_measure
```

Minimalny model techniczny:

```text
unit_of_measure
├── unit_id UUID PK
├── code VARCHAR NOT NULL UNIQUE
├── name VARCHAR NOT NULL
├── category VARCHAR NOT NULL
└── status VARCHAR NOT NULL
```

### 3.1. `unit_id`

- UUID,
- stabilny identyfikator techniczny,
- niezmienny po utworzeniu,
- używany przez FK z danych bieżących i historii.

### 3.2. `code`

Krótki kod użytkowy, np.:

```text
l
ml
kg
g
szt
```

Reguły:

- NOT NULL,
- UNIQUE,
- kod jest kanoniczny,
- nowy wpis nie może tworzyć drugiego kodu oznaczającego tę samą jednostkę tylko przez zmianę wielkości liter lub interpunkcji.

Normalizacja kodów jest obowiązkiem danych referencyjnych / Application, nie silnika konwersji.

### 3.3. `name`

Pełna nazwa prezentacyjna, np.:

```text
litr
mililitr
kilogram
gram
sztuka
```

Pole:

- NOT NULL,
- nie jest głównym identyfikatorem technicznym.

### 3.4. `category`

Dozwolone wartości początkowe:

```text
VOLUME
MASS
COUNT
```

Kategoria jest walidowaną wartością domenową.

Nie zawiera współczynnika konwersji i nie oznacza zgody na automatyczne przeliczenie.

### 3.5. `status`

Dozwolone wartości:

```text
ACTIVE
INACTIVE
```

Nowe i edytowane przypisania ilościowe mogą korzystać wyłącznie z `ACTIVE`.

`INACTIVE` może pozostać referencją istniejących i historycznych danych.

---

## 4. Dane początkowe słownika

Pierwsza migracja tworząca słownik seeduje minimalny zatwierdzony zestaw:

| code | name | category | status |
|---|---|---|---|
| `l` | litr | VOLUME | ACTIVE |
| `ml` | mililitr | VOLUME | ACTIVE |
| `kg` | kilogram | MASS | ACTIVE |
| `g` | gram | MASS | ACTIVE |
| `szt` | sztuka | COUNT | ACTIVE |

Seed:

- jest częścią wersjonowanej migracji,
- musi być deterministyczny,
- nie jest importem danych biznesowych,
- nie tworzy tabeli konwersji.

Rozbudowa słownika o kolejne jednostki tej samej semantyki może być wykonana później jako kontrolowana zmiana danych referencyjnych.

---

## 5. Referencje z PRODUCT_USAGE_LOCATION

Obecny model tekstowy:

```text
peak_quantity_unit
monthly_consumption_unit
```

zostaje technicznie zastąpiony referencjami:

```text
peak_quantity_unit_id
monthly_consumption_unit_id
```

Docelowy model:

```text
product_usage_locations
├── product_id
├── location_id
├── peak_quantity_value
├── peak_quantity_unit_id FK → unit_of_measure.unit_id
├── monthly_consumption_value
└── monthly_consumption_unit_id FK → unit_of_measure.unit_id
```

Reguły:

```text
peak_quantity_unit_id
→ NOT NULL

monthly_consumption_value IS NULL
→ monthly_consumption_unit_id IS NULL

monthly_consumption_value IS NOT NULL
→ monthly_consumption_unit_id IS NOT NULL
```

Istniejąca semantyka `0` i `NULL` pozostaje bez zmian.

---

## 6. Referencje w historii

TDR-004 pozostaje obowiązującym mechanizmem historii:

```text
current state change
+
history snapshot
=
ONE TRANSACTION
```

`PRODUCT_USAGE_LOCATION_HISTORY` musi przechowywać jednostkę jako część snapshotu.

Docelowo:

```text
product_usage_location_history
├── ...
├── peak_quantity_value
├── peak_quantity_unit_id FK → unit_of_measure.unit_id
├── monthly_consumption_value
├── monthly_consumption_unit_id FK → unit_of_measure.unit_id
└── changed_at
```

Zmiana jednostki jest istotną zmianą biznesową i tworzy nowy snapshot w tej samej transakcji co zmiana current state.

Nie zmieniamy modelu historii na delta, JSONB, trigger ani event sourcing.

---

## 7. Zachowanie historyczne jednostki INACTIVE

Jednostki historycznie użytej nie usuwa się fizycznie.

Model:

```text
ACTIVE
→ INACTIVE
```

nie powoduje:

```text
UPDATE history
UPDATE existing quantity references
DELETE unit
```

Dzięki temu snapshot historyczny nadal wskazuje tę samą jednostkę.

---

## 8. Brak automatycznej konwersji

TDR-005 nie wprowadza:

```text
kg ↔ g
l ↔ ml
```

Nie powstają:

- `conversion_factor`,
- `base_unit_id`,
- tabela konwersji,
- przeliczanie przez gęstość,
- normalizacja do jednostki bazowej.

Jeżeli przyszły raport wymaga porównania wartości, porównuje je wyłącznie wtedy, gdy dotyczą tej samej jednostki zgodnie z Core.

---

## 9. Application / Domain

Domain i Application nie powinny operować swobodnym tekstem jednostki przy zapisie ilości.

Minimalny kierunek:

```text
quantity value
+
unit_id
```

Application:

1. pobiera / otrzymuje wybraną jednostkę,
2. sprawdza jej istnienie,
3. sprawdza `status = ACTIVE` dla nowego lub edytowanego przypisania,
4. przekazuje prawidłową referencję do zapisu,
5. koordynuje current state + history zgodnie z TDR-004.

Nie wolno przenosić tej reguły wyłącznie do Streamlit.

---

## 10. Odczyt i prezentacja

Read models / DTO mogą zwracać użytkownikowi:

```text
unit_id
code
name
category
```

UI w normalnym workflow prezentuje przede wszystkim:

```text
code
```

np.:

```text
40 l
25 kg
3 szt
```

UUID jednostki jest techniczną referencją i nie powinien być eksponowany użytkownikowi jako informacja operacyjna.

---

## 11. UI wyboru jednostki

W formularzach przypisania miejsca stosowania:

```text
jednostka MAX
jednostka miesięcznego zużycia
```

są wybierane z listy aktywnych jednostek.

UI:

- nie zawiera pola free-text dla nowych jednostek,
- nie pozwala wybrać `INACTIVE`,
- zachowuje pustą jednostkę miesięcznego zużycia, jeżeli monthly value jest puste.

TDR-005 nie wymaga na tym etapie osobnego ekranu administracyjnego do zarządzania słownikiem.

---

## 12. Repozytorium / port jednostek

Dopuszcza się jeden minimalny port / repository dla danych referencyjnych, np.:

```text
UnitOfMeasureRepository
```

Minimalne potrzeby:

```text
list_active()
get_by_id(unit_id)
```

Jeżeli implementacja wymaga odczytu wszystkich jednostek dla administracji/testów, może mieć `list_all()`.

Nie tworzymy CRUD frameworka danych słownikowych.

Nie implementujemy delete jednostki.

---

## 13. Migracja Alembic

Alembic pozostaje jedynym mechanizmem zmiany schematu.

Migracja powinna wykonać logicznie:

```text
1. CREATE unit_of_measure
2. seed minimalnych jednostek
3. dodać nowe kolumny unit_id do current state
4. dodać nowe kolumny unit_id do history
5. dodać FK / constraints
6. usunąć stare tekstowe kolumny jednostek
```

Dokładna kolejność DDL może zostać dostosowana technicznie tak, aby upgrade/downgrade były poprawne i testowalne.

---

## 14. Brak migracji danych legacy

Nie wykonuje się:

- importu starego Excela,
- mapowania starych nazw `litr`, `L`, `litry` itd.,
- heurystycznej normalizacji,
- automatycznego odgadywania jednostek.

Dane produkcyjne zostaną wprowadzone ponownie ręcznie po przeglądzie.

---

## 15. Istniejące rekordy lokalnej bazy operatora

Na obecnym etapie lokalna baza operatora zawiera dane testowe, a nie produkcyjne.

TDR-005 nie wprowadza do migracji automatycznego mechanizmu przepisywania testowych wartości tekstowych.

Przed zastosowaniem docelowej migracji na lokalnej bazie operatora obowiązuje preflight:

```text
czy product_usage_locations ma rekordy?
czy product_usage_location_history ma rekordy?
```

Jeżeli tak:

```text
STOP
```

i dane testowe należy usunąć jako osobne, jawne działanie operacyjne przed migracją.

Migracja nie może samoczynnie usuwać danych ani zgadywać ich mapowania.

Dzięki temu kod migracji pozostaje bezpieczny i nie zawiera jednorazowej logiki zależnej od testowych rekordów konkretnej stacji.

---

## 16. Downgrade

Downgrade musi być technicznie możliwy w środowisku testowym.

Minimalny kierunek:

```text
unit_id FK
→ code jednostki
→ odtworzenie tekstowych kolumn
→ usunięcie FK
→ usunięcie unit_of_measure
```

Downgrade:

- nie wprowadza konwersji,
- wykorzystuje kanoniczny `code`,
- musi przejść test upgrade → downgrade → upgrade.

Nie jest to mechanizm biznesowego cofania danych produkcyjnych, tylko techniczna odwracalność migracji.

---

## 17. Constraints

Minimalne constraints:

### UNIT_OF_MEASURE

```text
PK(unit_id)
UNIQUE(code)
category IN (VOLUME, MASS, COUNT)
status IN (ACTIVE, INACTIVE)
```

### PRODUCT_USAGE_LOCATION

```text
peak_quantity_unit_id NOT NULL
FK peak_quantity_unit_id → unit_of_measure.unit_id
FK monthly_consumption_unit_id → unit_of_measure.unit_id
```

Istniejąca reguła spójności monthly value/unit musi zostać zachowana lub dostosowana do nowych kolumn FK.

Nie dodajemy constraints dotyczących konwersji.

---

## 18. Usuwanie / dezaktywacja jednostki

Na tym etapie:

```text
DELETE UNIT_OF_MEASURE
```

nie jest use case'em aplikacji.

Jeżeli jednostka przestaje być używana:

```text
status = INACTIVE
```

Fizyczny delete nie jest implementowany w standardowym workflow.

---

## 19. Warstwy architektury

Obowiązuje istniejący układ:

```text
presentation
→ application
→ domain
→ ports

infrastructure
→ implements ports
→ SQLAlchemy/PostgreSQL
```

Streamlit:

- wyświetla listę,
- przyjmuje wybór,
- nie wykonuje SQL,
- nie ustala samodzielnie reguł aktywności jednostki.

---

## 20. Wpływ na istniejące use case'y

Zmiana dotyczy co najmniej:

```text
AssignProductUsageLocation
UpdateProductUsageLocation
GetProductDetails / read model
ListSupervisoryProducts / read model
history snapshot write/read
```

Nie zmienia semantyki:

```text
peak quantity
monthly consumption
PRODUCT × LOCATION
```

Zmienia wyłącznie reprezentację jednostki z tekstowej na referencyjną.

---

## 21. Testy wymagane

Implementacja powinna udowodnić co najmniej:

1. seed jednostek istnieje po migracji,
2. `code` jest unikalny,
3. nieprawidłowa category/status jest odrzucana,
4. MAX wymaga aktywnej jednostki,
5. monthly z wartością wymaga aktywnej jednostki,
6. monthly bez wartości może nie mieć jednostki,
7. `0` nadal różni się od `NULL`,
8. `INACTIVE` nie może być użyta w nowym/edytowanym zapisie,
9. istniejąca referencja do `INACTIVE` pozostaje odczytywalna,
10. zmiana jednostki tworzy snapshot historii,
11. current + history pozostają atomowe,
12. supervisory/read models pokazują kod jednostki,
13. upgrade → downgrade → upgrade działa,
14. `alembic check` nie wykazuje driftu.

Pełny checkpoint Sprintu nadal wymaga walidacji zgodnej z governance projektu.

---

## 22. Ograniczenia dla Codexa

Codex nie może bez nowej decyzji:

- dodać silnika konwersji,
- dodać `base_unit` lub `conversion_factor`,
- zaimportować starego Excela,
- heurystycznie mapować stare tekstowe jednostki,
- usuwać automatycznie danych operatora w migracji,
- zmienić TDR-004 z snapshotów na inny model historii,
- użyć triggerów,
- stworzyć generycznego dictionary framework,
- dodać osobnego modułu administracji słownikami bez potrzeby,
- implementować `Stan na dzień` lub `Analizy` w tym zakresie,
- zmienić zasady `0` / `NULL`,
- obejść warstwę Application przez SQL w Streamlit.

---

## 23. Decyzje techniczne

TDR-005 proponuje zatwierdzić:

```text
1. jedna tabela unit_of_measure

2. UUID jako PK unit_id

3. code jako kanoniczny UNIQUE business/display code

4. category:
   VOLUME / MASS / COUNT

5. status:
   ACTIVE / INACTIVE

6. PRODUCT_USAGE_LOCATION:
   peak_quantity_unit_id FK
   monthly_consumption_unit_id FK

7. PRODUCT_USAGE_LOCATION_HISTORY:
   te same referencje unit_id jako część snapshotu

8. brak conversion engine

9. seed:
   l, ml, kg, g, szt

10. brak migracji legacy / heurystycznego mapowania

11. niepusta lokalna baza operatora:
    STOP przed migracją i jawny cleanup danych testowych

12. Alembic:
    jedyny mechanizm schema migration

13. zachowanie TDR-004:
    current + history w jednej transakcji
```

---

## 24. Relacja do przyszłych Analiz

TDR-005 nie implementuje `Analizy`.

Tworzy jednak techniczny fundament, dzięki któremu przyszłe:

```text
MAX = 40 kg
Stan na dzień = 45 kg
difference = +5 kg
```

nie wymaga konwersji jednostek.

`Stan na dzień` będzie używał jednostki MAX zgodnie z BDR-006 / CORE-001 v1.2-approved.

---

## 25. Powiązane dokumenty

TDR-005 należy czytać łącznie z:

- `BDR-006_Slownik_jednostek_miary_v1.0-approved`,
- `CORE-001_MSDS_Manager_v1.2-approved`,
- `TDR-001_MSDS_Manager`,
- `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved`,
- `BACKLOG-001_MSDS_Manager_Post_CHECKPOINT-006`,
- `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED`,
- Konstytucją projektu,
- GOV-002.

W razie konfliktu obowiązują nadrzędne zatwierdzone źródła projektu.

---

## 26. Authorization boundary

TDR-005 v1.0-approved jest obowiązującą decyzją techniczną dla DATA-01.

Dokument:

```text
autoryzuje przygotowanie Sprintu implementacyjnego
autoryzuje przygotowanie Tasków wynikających z TDR-005
```

Nie stanowi samodzielnego polecenia wykonania zmian w repozytorium.

Implementacja nadal wymaga:

```text
zatwierdzonego Sprintu
jawnego Tasku
jawnej autoryzacji wykonania dla Codexa
```

Cleanup lokalnych danych operatora pozostaje osobnym, jawnym działaniem operacyjnym.

---

## 27. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-29 | Draft | Pierwszy model techniczny UNIT_OF_MEASURE, FK w current/history, seed jednostek, brak konwersji i migracji legacy, bezpieczny preflight dla lokalnych danych testowych |
| 1.0-approved | 2026-09-29 | Approved | Architekt Operacyjny zatwierdził TDR-005 bez zmian merytorycznych |
