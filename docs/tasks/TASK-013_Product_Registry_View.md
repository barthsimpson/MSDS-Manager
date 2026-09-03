# TASK-013 — Product Registry View

**Projekt:** MSDS Manager  
**Task ID:** TASK-013  
**Sprint:** SPRINT-002 v1.2-approved — Rejestr produktów i miejsc stosowania  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Zamienić placeholder `Produkty` z TASK-012 w pierwszy rzeczywiście użytkowy, **tylko do odczytu** widok rejestru produktów.

Użytkownik ma móc:

```text
Produkty
   ↓
lista istniejących PRODUCT
   ↓
wybór produktu
   ↓
szczegóły PRODUCT
   ↓
producent + dane administracyjne + miejsca stosowania + quantity
```

TASK-013 korzysta wyłącznie z istniejących kontraktów Application i istniejącego persistence.

Nie tworzy PRODUCT i nie implementuje edycji.

---

## 2. Stan wejściowy

Po zaakceptowanym TASK-012:

```text
CORE                    v1.2-approved
Tests                   95 passed
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Schema drift            none
Business records        0
Streamlit shell         working
```

Dostępne są między innymi:

```text
ListProducts
GetProductDetails
```

oraz działający composition root Streamlit.

---

## 3. Źródła nadrzędne

Obowiązują:

1. `CORE-001 v1.2-approved`,
2. `SPRINT-002 v1.2-approved`,
3. zatwierdzone BDR-001..005,
4. TDR-001..003,
5. zaakceptowane TASK-008..012 oraz TASK-009-ALIGN,
6. root `AGENTS.md`.

Jeżeli do zbudowania widoku potrzebna byłaby nowa semantyka biznesowa:

```text
STOP
```

Codex nie rozszerza Core w warstwie UI.

---

# CZĘŚĆ A — GRANICA FUNKCJONALNA

## 4. TASK-013 implementuje

Wyłącznie read-only Product Registry:

- listę istniejących produktów,
- poprawny pusty stan,
- wybór produktu,
- szczegóły wybranego produktu,
- producenta,
- status produktu,
- dane administracyjne,
- dane odpadowe będące bridgeheadem Core,
- przypisane miejsca stosowania,
- peak quantity,
- monthly consumption,
- status lokalizacji.

---

## 5. TASK-013 NIE implementuje

Nie implementuj:

- `CreateProduct`,
- `CreateManufacturer`,
- `Dodaj produkt`,
- `Dodaj SDS`,
- edycji produktu,
- zmiany `usage_status`,
- formularza lokalizacji,
- create/deactivate/reactivate lokalizacji w UI,
- przypisywania produktu do lokalizacji,
- edycji quantity,
- usuwania relacji,
- SDS,
- BHP,
- SafetyProfile,
- historii,
- dashboardu,
- REACH,
- BDO,
- importu Excel.

To nie jest jeszcze TASK-014.

---

# CZĘŚĆ B — LISTA PRODUKTÓW

## 6. Źródło danych

Lista musi korzystać z:

```text
ListProducts
```

UI nie może:

- wykonywać SQL,
- korzystać bezpośrednio z repository jako źródła biznesowego,
- importować ORM,
- rekonstruować produktu z tabel persistence.

---

## 7. Minimalna lista

Lista ma umożliwiać użytkownikowi jednoznaczne rozpoznanie produktu.

Wyświetl co najmniej informacje dostępne w istniejącym `ProductListItem`, zgodnie z aktualnym kontraktem Application.

Nie rozszerzaj DTO tylko dla wygody UI, jeżeli potrzebne informacje nie należą do zatwierdzonego kontraktu TASK-009.

Nie twórz w TASK-013 dodatkowych pól biznesowych.

---

## 8. Wybór produktu

Użytkownik musi móc wybrać jeden istniejący produkt z listy.

Wewnętrzna identyfikacja wyboru musi opierać się na:

```text
product_id
```

Nie używaj nazwy produktu jako technicznego klucza.

Nazwy produktów nie muszą być unikalne.

---

## 9. Brak sztucznego sortowania biznesowego

Jeżeli `ListProducts` ma już stabilną kolejność — zachowaj ją.

Jeżeli nie ma zatwierdzonej reguły kolejności, dopuszczalne jest neutralne sortowanie prezentacyjne dla czytelności, np. po nazwie produktu.

Nie nadawaj sortowaniu znaczenia biznesowego.

Udokumentuj wybraną opcję w raporcie.

---

# CZĘŚĆ C — PUSTY STAN

## 10. Pusta baza

Aktualna baza może legalnie zawierać:

```text
0 PRODUCT
```

W takim przypadku ekran `Produkty`:

- nie zgłasza błędu,
- nie tworzy danych testowych,
- nie pokazuje pustego/zepsutego selectboxa,
- wyświetla neutralny komunikat, np.:

```text
Brak produktów w rejestrze.
```

Nie dodawaj przycisku `Dodaj produkt`.

---

# CZĘŚĆ D — SZCZEGÓŁY PRODUCT

## 11. Źródło danych

Po wyborze produktu UI wywołuje:

```text
GetProductDetails(product_id)
```

Nie pobieraj szczegółów bezpośrednio przez repository.

---

## 12. Tożsamość produktu

Widok szczegółów powinien prezentować dostępne w DTO pola tożsamości:

```text
product_name
manufacturer_product_code
manufacturer
```

`manufacturer_id` może pozostać technicznym identyfikatorem i nie musi być eksponowany użytkownikowi, jeśli istniejący DTO dostarcza nazwę producenta.

Nie umożliwiaj edycji tych pól.

---

## 13. Status produktu

Wyświetl:

```text
usage_status
```

jako informację read-only.

Nie twórz:

```text
SetProductStatus
```

Nie implementuj przycisków ACTIVE/INACTIVE/REJECTED/PENDING_APPROVAL.

---

## 14. Dane administracyjne

Wyświetl read-only, jeżeli są dostępne:

```text
use_description
use_restriction
waste_type
waste_code
```

Dla `None` użyj czytelnej neutralnej reprezentacji prezentacyjnej.

Nie zapisuj zastępczego tekstu do bazy.

---

# CZĘŚĆ E — MIEJSCA STOSOWANIA

## 15. Lista przypisanych lokalizacji

W szczegółach PRODUCT pokaż wszystkie relacje zwrócone przez:

```text
GetProductDetails
```

Każdy wpis powinien prezentować dane dostępne w `ProductUsageLocationDetails`, w szczególności:

- lokalizację,
- status lokalizacji,
- peak quantity,
- monthly consumption.

Nie wykonuj dodatkowego zapytania SQL z UI.

---

## 16. ACTIVE / INACTIVE

Jeżeli do produktu historycznie/praktycznie przypisana jest lokalizacja `INACTIVE`, szczegóły produktu nie mogą jej automatycznie usuwać z read-only widoku, jeśli `GetProductDetails` ją zwraca.

TASK-013 jest widokiem szczegółów produktu, nie „current analytics”.

Status lokalizacji ma być widoczny, aby użytkownik rozumiał jej aktualny stan.

Nie zmieniaj semantyki `ListUsageLocations`.

---

## 17. Peak quantity

Wyświetl:

```text
peak_quantity_value
peak_quantity_unit
```

bez konwersji.

`Decimal("0")` musi być prezentowane jako rzeczywiste zero, nie jako brak danych.

Nie agreguj automatycznie factory peak w TASK-013, jeśli nie istnieje zatwierdzony Application use case do takiej prezentacji.

---

## 18. Monthly consumption

Wyświetl:

```text
monthly_consumption_value
monthly_consumption_unit
```

z zachowaniem semantyki:

```text
None = brak danych
0    = świadome zero
```

Nie przeliczaj jednostek.

Nie zastępuj `None` wartością `0`.

---

## 19. Brak przypisanych lokalizacji

Jeżeli produkt nie ma relacji PRODUCT_USAGE_LOCATION:

- widok szczegółów nadal działa,
- pokaż neutralny komunikat, np.:

```text
Brak przypisanych miejsc stosowania.
```

Nie twórz relacji automatycznie.

---

# CZĘŚĆ F — PRESENTATION

## 20. Odpowiedzialność UI

Warstwa Streamlit może:

- formatować dane,
- wybierać produkt,
- wyświetlać sekcje,
- przedstawiać `None` w czytelny sposób.

Nie może:

- implementować reguł Domain,
- wykonywać SQL,
- wykonywać commit/rollback,
- importować ORM do widoku,
- zmieniać statusów,
- wykonywać zapisów.

---

## 21. Minimalizm UI

Preferuj prosty, czytelny widok operacyjny.

Nie buduj:

- rozbudowanego CSS,
- własnego design systemu,
- kart/dashboardów tylko dla wyglądu,
- wykresów,
- KPI,
- filtrów bez zatwierdzonej potrzeby.

To jest rejestr operacyjny, nie dashboard zarządczy.

---

# CZĘŚĆ G — COMPOSITION ROOT

## 22. Rozszerzenie composition root

Rozszerz istniejący composition root tylko o elementy konieczne do:

```text
ListProducts
GetProductDetails
```

Preferuj współdzielenie tej samej infrastruktury w ramach pojedynczego renderowania/operacji, zgodnie z aktualnym prostym modelem TASK-012.

Nie wprowadzaj frameworka Dependency Injection.

Nie optymalizuj jeszcze globalnego cache Engine bez wykazanej potrzeby.

---

## 23. Obsługa błędów

Zachowaj kontrolowany mechanizm TASK-012.

W przypadku błędu konfiguracji/persistence:

- UI pokazuje krótki komunikat,
- nie pokazuje sekretów,
- nie pokazuje pełnego DATABASE_URL,
- nie pokazuje ORM tracebacku jako komunikatu biznesowego.

Nie twórz w TASK-013 szczegółowej semantyki konfliktów DB.

---

# CZĘŚĆ H — TESTY

## 24. Test pustego rejestru

Potwierdź przez Streamlit AppTest lub równoważny istniejący mechanizm:

```text
ListProducts → []
```

Rezultat:

- widoczny neutralny empty state,
- brak błędu,
- brak przycisku `Dodaj produkt`,
- brak zapisu danych.

---

## 25. Test jednego produktu

Przy kontrolowanym fixture PRODUCT potwierdź:

- produkt pojawia się w rejestrze,
- można go wybrać,
- szczegóły pochodzą z `GetProductDetails`,
- producent jest poprawny,
- status jest widoczny,
- pola administracyjne są widoczne,
- brak lokalizacji jest poprawnie obsłużony.

Fixture nie może stać się produkcyjnym CreateProduct.

---

## 26. Test wielu produktów

Potwierdź:

- więcej niż jeden produkt jest dostępny do wyboru,
- wybór używa `product_id`,
- przełączenie produktu zmienia prezentowane szczegóły,
- identyczne lub podobne nazwy nie mogą powodować błędnej identyfikacji rekordu.

---

## 27. Test produktu z lokalizacjami

Przy fixture:

```text
PRODUCT
├── LOCATION A — ACTIVE
└── LOCATION B — INACTIVE
```

potwierdź prezentację obu relacji, jeśli obie zwraca `GetProductDetails`.

Potwierdź:

- status każdej lokalizacji,
- peak value/unit,
- monthly value/unit,
- `0` ≠ brak danych,
- `None` ≠ zero,
- brak konwersji jednostek.

---

## 28. Test read-only

Potwierdź, że ekran `Produkty` nie zawiera elementów zapisujących:

- Add/Create Product,
- Save,
- Delete,
- Set status,
- Assign location,
- Edit quantities.

Nie wymagaj testowania każdego tekstu świata; kontroluj konkretne elementy UI utworzone przez aplikację.

---

## 29. Test architektury

Utrzymaj:

```text
presentation → application
application !→ presentation
application !→ infrastructure
domain !→ presentation
```

Kod widoku nie może importować:

- SQLAlchemy,
- psycopg,
- ORM models.

Composition root może korzystać z infrastructure zgodnie z TASK-012.

---

# CZĘŚĆ I — MANUAL SMOKE

## 30. Manualny test UI

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/app.py
```

Potwierdź:

1. aplikacja startuje,
2. `Produkty` działa przy pustej bazie,
3. `Stanowiska` nadal działa jako shell,
4. nie ma `Dodaj produkt`,
5. nie ma `Dodaj nowy SDS`,
6. nie ma operacji zapisujących,
7. start/nawigacja nie zmienia DB.

Jeżeli manualny smoke wykonujesz na pustej bazie, nie dodawaj trwałych danych tylko po to, aby ręcznie zobaczyć szczegóły. Scenariusze z produktami pokryj fixture/testami.

---

# CZĘŚĆ J — POSTGRESQL / SCHEMA

## 31. Brak zmian schema

TASK-013 nie wymaga:

- zmian Domain,
- nowych Application contracts,
- zmian ORM,
- nowych tabel,
- nowych constraintów,
- migracji.

Oczekiwany stan:

```text
Alembic revisions       4
PostgreSQL current      d2b4f6a8c190 (head)
Application tables      9
Schema drift            none
Business records        0 po testach
```

Jeżeli widok wymaga zmiany schema lub DTO/Application contract:

```text
STOP
```

Nie obchodź tego bezpośrednim repository/SQL w UI.

---

## 32. Alembic

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
d2b4f6a8c190 (head)
No new upgrade operations detected.
```

---

# CZĘŚĆ K — REGRESJA

## 33. Pełny pytest

Stan bazowy:

```text
95 passed
```

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie testy muszą przejść bez `SAWarning`.

---

# CZĘŚĆ L — GIT / BEZPIECZEŃSTWO

## 34. Kontrole

Uruchom:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:

- `.env` ignored i nietrackowany,
- brak sekretów,
- brak pełnego DATABASE_URL w UI/raporcie,
- brak dumpów/backupów,
- brak PDF/MSG,
- brak pozostawionych fixture w PostgreSQL,
- brak nowych bibliotek,
- brak commit/push bez jawnego polecenia.

---

# CZĘŚĆ M — STOP CONDITIONS

## 35. STOP

Raportuj `PARTIAL/BLOCKED`, jeżeli:

- istniejący `ProductListItem` lub `ProductDetails` nie wystarcza do wymaganego widoku,
- potrzebna jest zmiana kontraktu Application,
- potrzebna jest zmiana Domain,
- potrzebna jest zmiana ORM/schema/migracja,
- potrzebny jest nowy status,
- potrzebna jest nowa reguła filtrowania ACTIVE/INACTIVE,
- potrzebny jest CreateProduct/CreateManufacturer,
- potrzebny jest zapis z UI,
- potrzebna jest nowa biblioteka,
- zakres zaczyna realizować TASK-014,
- zakres wchodzi w SDS/BHP/history.

Nie zgaduj brakującej semantyki.

---

# CZĘŚĆ N — KRYTERIA AKCEPTACJI

## 36. TASK-013 = DONE, jeżeli

1. placeholder `Produkty` został zastąpiony read-only Product Registry,
2. lista korzysta z `ListProducts`,
3. pusta baza daje poprawny empty state,
4. nie powstają dane testowe przy normalnym uruchomieniu,
5. użytkownik może wybrać istniejący PRODUCT,
6. wybór technicznie opiera się na `product_id`,
7. szczegóły korzystają z `GetProductDetails`,
8. widoczna jest tożsamość produktu,
9. widoczny jest producent,
10. widoczny jest `usage_status`,
11. widoczne są dostępne dane administracyjne,
12. `waste_type/waste_code` są read-only,
13. brak lokalizacji jest poprawnym stanem,
14. przypisane lokalizacje są prezentowane,
15. status lokalizacji jest prezentowany,
16. peak value/unit są prezentowane bez konwersji,
17. peak zero pozostaje zerem,
18. monthly NULL pozostaje brakiem danych,
19. monthly zero pozostaje zerem,
20. ACTIVE i INACTIVE mogą być widoczne w szczegółach produktu zgodnie z wynikiem use case'u,
21. UI nie wykonuje SQL,
22. UI nie importuje ORM,
23. UI nie wykonuje commit/rollback,
24. nie ma `Dodaj produkt`,
25. nie ma `Dodaj nowy SDS`,
26. nie ma edycji produktu,
27. nie ma zapisu lokalizacji/quantity,
28. sekcja `Stanowiska` z TASK-012 nadal działa,
29. błędy inicjalizacji pozostają kontrolowane,
30. testy presentation przechodzą,
31. testy architektury przechodzą,
32. pełna regresja przechodzi bez SAWarning,
33. brak zmian Domain,
34. brak zmian Application contracts,
35. brak zmian ORM/schema,
36. brak migracji #5,
37. PostgreSQL nadal ma 9 tabel,
38. `alembic current = d2b4f6a8c190 (head)`,
39. `alembic check` bez driftu,
40. po testach 0 rekordów biznesowych,
41. brak nowych bibliotek,
42. utworzono TASK-013_REPORT,
43. TASK-014 nie został rozpoczęty.

---

# CZĘŚĆ O — RAPORT

## 37. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-013_REPORT.md
```

Raport musi zawierać:

1. Status.
2. Stan wejściowy.
3. Zmienione pliki.
4. Implementację Product Registry.
5. Źródło danych listy.
6. Mechanizm wyboru po `product_id`.
7. Empty state.
8. Product Details.
9. Manufacturer.
10. Product usage status.
11. Dane administracyjne.
12. Waste bridgehead.
13. Usage locations.
14. ACTIVE/INACTIVE presentation.
15. Peak quantity.
16. Monthly consumption.
17. Reprezentację NULL i zero.
18. Brak konwersji jednostek.
19. Read-only boundary.
20. Composition root.
21. Obsługę błędów.
22. Testy presentation.
23. Testy architektury.
24. Manual Streamlit smoke.
25. Pełny pytest / SAWarning.
26. Potwierdzenie braku zmian Domain/Application contracts/ORM/schema.
27. `alembic current`.
28. `alembic check`.
29. Finalny stan PostgreSQL.
30. Git/bezpieczeństwo.
31. Odstępstwa.
32. Problemy/ryzyka.
33. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-014.
```

---

# CZĘŚĆ P — AUTORYZACJA

## 38. Autoryzacja wykonania

Obecność pliku:

```text
docs/tasks/TASK-013_Product_Registry_View.md
```

w repozytorium **nie stanowi zgody na wykonanie Tasku**.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wykonaj TASK-013.
```

Po zakończeniu:

- tworzy raport,
- zatrzymuje się,
- nie rozpoczyna TASK-014.

---

## 39. Oczekiwany stan końcowy

```text
TASK-012 ACCEPTED
        ↓
Streamlit shell
        ↓
TASK-013
        ↓
read-only Product Registry
        ↓
ListProducts
        ↓
GetProductDetails
        ↓
Product + Manufacturer + Usage Locations
        ↓
schema unchanged
        ↓
READY FOR TASK-014
```
