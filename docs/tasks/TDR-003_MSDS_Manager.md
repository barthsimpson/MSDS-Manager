# TDR-003 — Struktura repozytorium i granice warstw

**Projekt:** MSDS Manager  
**Id dokumentu:** TDR-003  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Powiązane IR:** IR-001-35  

---

## 1. Cel decyzji

Celem TDR-003 jest zatwierdzenie docelowej struktury repozytorium MVP MSDS Manager oraz jednoznacznych granic pomiędzy:

- domeną,
- przypadkami użycia,
- infrastrukturą,
- warstwą prezentacji,
- migracjami,
- testami,
- konfiguracją i dokumentacją techniczną.

Struktura ma umożliwiać rozpoczęcie implementacji bez zgadywania architektury przez Codexa.

---

## 2. Zasada nadrzędna

Repozytorium ma odzwierciedlać rozdzielenie odpowiedzialności:

```text
presentation
     |
     v
application
     |
     v
domain

infrastructure
     |
     +--> implementuje techniczne mechanizmy wymagane przez application/domain
```

Najważniejsza reguła:

> **Core domenowy nie może zależeć od Streamlit, SQLAlchemy, psycopg, PostgreSQL ani lokalnego systemu plików.**

Technologia ma implementować zatwierdzony model biznesowy, a nie definiować jego znaczenie.

---

## 3. Zatwierdzona struktura repozytorium

Dla MVP przyjmuje się strukturę:

```text
msds-manager/
|
+-- app/
|   +-- domain/
|   |   +-- models/
|   |   +-- enums/
|   |   +-- rules/
|   |   +-- exceptions/
|   |
|   +-- application/
|   |   +-- use_cases/
|   |   +-- ports/
|   |   +-- dto/
|   |
|   +-- infrastructure/
|   |   +-- db/
|   |   |   +-- models/
|   |   |   +-- repositories/
|   |   |   +-- session.py
|   |   |
|   |   +-- filesystem/
|   |   +-- config/
|   |
|   +-- presentation/
|       +-- streamlit/
|
+-- migrations/
|   +-- versions/
|
+-- tests/
|   +-- unit/
|   +-- integration/
|
+-- docs/
|   +-- technical/
|
+-- scripts/
|
+-- .env.example
+-- .gitignore
+-- alembic.ini
+-- pyproject.toml
+-- README.md
```

Dopuszczalne jest dodawanie plików `__init__.py` wymaganych przez strukturę pakietów Python.

Dodanie nowego katalogu technicznego jest dopuszczalne, jeśli nie zmienia granic architektury ani Core.

---

## 4. `app/domain` — Core domenowy

`app/domain` zawiera znaczenie biznesowe systemu.

Tutaj należą m.in.:

- encje i obiekty domenowe,
- statusy i enumy domenowe,
- reguły integralności,
- walidacje biznesowe,
- wyjątki domenowe.

Przykładowe pojęcia:

```text
PRODUCT
MANUFACTURER
USAGE_LOCATION
PRODUCT_USAGE
SDS
BHP_DECISION
DECISION_EVIDENCE
```

oraz statusy wynikające z zatwierdzonych BDR.

### Zakaz zależności

`domain` nie importuje:

- Streamlit,
- SQLAlchemy,
- psycopg,
- Alembic,
- konkretnego kodu PostgreSQL,
- adapterów systemu plików.

`domain` nie zna `.env`, `DATABASE_URL`, `SDS_ROOT_PATH` ani `BHP_EVIDENCE_ROOT_PATH`.

---

## 5. `app/domain/models`

Katalog zawiera modele domenowe opisujące pojęcia zatwierdzone w CORE i BDR.

Model domenowy nie jest modelem ORM.

Przykład zasady:

```text
domain.models.SDS
```

opisuje znaczenie SDS w systemie,

natomiast:

```text
infrastructure.db.models.SDSModel
```

jest technicznym odwzorowaniem rekordu PostgreSQL.

Nie wolno łączyć tych dwóch odpowiedzialności tylko dla skrócenia kodu.

---

## 6. `app/domain/enums`

Katalog przechowuje zatwierdzone słowniki/statusy domenowe, np.:

- status stosowania produktu,
- `CURRENT / ARCHIVED` dla SDS,
- `AVAILABLE / MISSING`,
- `APPROVED / REJECTED`,
- `CURRENT / SUPERSEDED` dla rekordu decyzji.

Codex nie może rozszerzać enumów o nowe stany bez zatwierdzonego BDR.

---

## 7. `app/domain/rules`

Katalog przechowuje reguły biznesowe niezależne od UI i bazy.

Przykłady:

- reguły dopuszczalnych zmian statusów,
- konsekwencje zatwierdzenia nowego SDS,
- konsekwencje decyzji BHP,
- walidacja relacji PRODUCT–SDS–BHP_DECISION.

Reguła biznesowa nie może istnieć wyłącznie jako warunek w Streamlit ani wyłącznie jako efekt uboczny ORM.

---

## 8. `app/application` — przypadki użycia

Warstwa `application` organizuje operacje wykonywane przez system.

Przykładowe przyszłe przypadki użycia:

```text
register_product
register_sds
approve_sds_as_current
register_bhp_decision
replace_bhp_decision
assign_usage_location
```

Application:

- uruchamia reguły domenowe,
- koordynuje repozytoria,
- wyznacza granice transakcji,
- zwraca wynik do UI,
- nie implementuje szczegółów PostgreSQL ani Streamlit.

---

## 9. `app/application/ports`

`ports` definiuje interfejsy potrzebne przypadkom użycia.

Przykładowo:

- `ProductRepository`,
- `SDSRepository`,
- `BHPDecisionRepository`,
- `DocumentRepository` / interfejs dostępu do plików.

Warstwa application może powiedzieć:

> „potrzebuję repozytorium SDS”

ale nie powinna wiedzieć:

> „wykonaj zapytanie SQLAlchemy do PostgreSQL pod localhost”.

Konkretna implementacja znajduje się w `infrastructure`.

---

## 10. `app/application/dto`

DTO służą do przekazywania danych przez granice przypadków użycia, jeżeli jest to potrzebne.

Nie są encjami domenowymi ani modelami SQLAlchemy.

Nie należy tworzyć DTO „na zapas”. Powstają wtedy, gdy rzeczywiście upraszczają granicę między warstwami.

---

## 11. `app/infrastructure` — szczegóły techniczne

`infrastructure` zawiera implementacje zależne od technologii.

Tutaj znajdują się:

- SQLAlchemy,
- połączenie z PostgreSQL,
- implementacje repozytoriów,
- konfiguracja techniczna,
- adaptery systemu plików.

Infrastructure może zależeć od domain/application.

Domain nie może zależeć od infrastructure.

---

## 12. `app/infrastructure/db/models`

Tutaj znajdują się modele ORM SQLAlchemy odpowiadające tabelom PostgreSQL.

Ich zadaniem jest odwzorowanie zatwierdzonego modelu danych na technologię.

Modele ORM nie są miejscem do definiowania nowych reguł biznesowych.

Ograniczenia bazy danych, klucze obce, unikalności i indeksy powinny wzmacniać reguły Core tam, gdzie jest to technicznie właściwe.

---

## 13. `app/infrastructure/db/repositories`

Katalog zawiera implementacje repozytoriów korzystające z SQLAlchemy.

Przykład:

```text
application.port:
SDSRepository

        ↓ implementacja

infrastructure:
SqlAlchemySDSRepository
```

Zapytania bazodanowe nie powinny być rozproszone po Streamlit ani po modelach domenowych.

---

## 14. `app/infrastructure/db/session.py`

Moduł odpowiada za techniczne tworzenie połączenia, sesji SQLAlchemy i obsługę konfiguracji `DATABASE_URL`.

Nie zawiera reguł biznesowych.

Granice transakcji są koordynowane zgodnie z przypadkiem użycia, a nie przypadkowo przez UI.

---

## 15. `app/infrastructure/filesystem`

Katalog zawiera adaptery pracy z:

- `SDS_ROOT_PATH`,
- `BHP_EVIDENCE_ROOT_PATH`.

Odpowiada m.in. za:

- bezpieczne wyznaczanie pełnej ścieżki z root + `relative_path`,
- sprawdzanie istnienia pliku,
- sprawdzanie dostępności repozytorium,
- odczyt pliku, gdy dany przypadek użycia tego wymaga.

Nie może samodzielnie:

- usuwać dokumentów,
- przenosić dokumentów,
- zmieniać nazw,
- nadpisywać źródłowych SDS lub dowodów BHP.

---

## 16. `app/infrastructure/config`

Katalog odpowiada za odczyt i walidację konfiguracji środowiska.

Minimalnie:

```text
DATABASE_URL
SDS_ROOT_PATH
BHP_EVIDENCE_ROOT_PATH
```

Kod domenowy nie może czytać `.env` bezpośrednio.

---

## 17. `app/presentation/streamlit`

Jest to jedyne miejsce przeznaczone dla interfejsu Streamlit MVP.

Warstwa prezentacji:

- wyświetla dane,
- zbiera dane użytkownika,
- wywołuje przypadki użycia,
- prezentuje wynik i błędy.

Nie może:

- definiować reguł Core,
- wykonywać bezpośrednio zapytań SQL jako standardowego mechanizmu,
- samodzielnie zmieniać kilku rekordów bazy w celu realizacji procesu,
- samodzielnie interpretować statusów biznesowych.

---

## 18. `migrations`

Katalog zawiera konfigurację i wersjonowane migracje Alembic.

```text
migrations/
└── versions/
```

Migracje są częścią kodu projektu i podlegają Git.

Każda zmiana schematu po migracji początkowej wymaga nowej migracji.

Nie wolno traktować ręcznej zmiany PostgreSQL jako równoważnej zmianie repozytorium.

---

## 19. `tests`

Przyjmuje się dwa podstawowe poziomy:

```text
tests/
├── unit/
└── integration/
```

### `unit`

Testuje przede wszystkim:

- Core,
- reguły domenowe,
- przypadki użycia możliwe do sprawdzenia bez realnej infrastruktury.

### `integration`

Testuje m.in.:

- SQLAlchemy + PostgreSQL,
- repozytoria,
- migracje,
- relacje i constraints bazy,
- adaptery systemu plików, gdy jest to uzasadnione.

Nie tworzymy osobnej rozbudowanej hierarchii testów, dopóki projekt jej realnie nie potrzebuje.

---

## 20. Testowa baza danych

Testy integracyjne nie mogą pracować na właściwej bazie operacyjnej użytkownika.

Powinny używać osobnej bazy testowej PostgreSQL.

Szczegółowy sposób jej tworzenia i czyszczenia może zostać określony w Tasku implementacyjnym, pod warunkiem zachowania tej granicy bezpieczeństwa.

Nie używamy SQLite jako zamiennika PostgreSQL w testach integracyjnych Core persistence.

---

## 21. `docs`

Repozytorium może przechowywać dokumentację techniczną potrzebną wykonawcy, np.:

```text
docs/technical/
```

Natomiast zatwierdzone źródła projektowe w ChatGPT pozostają nadrzędnym źródłem decyzji Architekta.

Skopiowanie dokumentu do repozytorium nie daje Codexowi prawa do samodzielnej zmiany jego znaczenia.

Zakres dokumentów przekazywanych do repozytorium będzie wynikał z Tasków.

---

## 22. `scripts`

`scripts/` jest miejscem na pomocnicze, jawne operacje administracyjne, np. inicjalizację lub kontrolę środowiska, jeżeli zostaną zatwierdzone w Tasku.

Skrypt nie może być „boczną drogą” omijającą Core, historię lub migracje.

---

## 23. Pliki w katalogu głównym

### `.env.example`

Szablon konfiguracji bez sekretów.

### `.gitignore`

Wyklucza co najmniej:

```text
.env
.venv/
__pycache__/
.pytest_cache/
```

oraz lokalne artefakty, które nie powinny trafiać do repozytorium.

### `alembic.ini`

Konfiguracja Alembic.

Rzeczywisty sekret połączenia nie może być utrwalony w repozytorium.

### `pyproject.toml`

Centralna deklaracja projektu Python i jego zależności.

Dla MVP przyjmuje się `pyproject.toml` jako podstawowy plik deklaracji zależności zamiast utrzymywania kilku konkurencyjnych źródeł zależności.

### `README.md`

Instrukcja techniczna projektu, obejmująca z czasem co najmniej:

- wymagania środowiska,
- utworzenie `.venv`,
- konfigurację `.env`,
- migracje,
- uruchomienie aplikacji,
- uruchomienie testów.

README nie jest źródłem decyzji biznesowych.

---

## 24. Kierunek zależności

Dopuszczalny kierunek:

```text
presentation ---> application ---> domain
                       ^
                       |
                infrastructure
```

Dokładniej:

- `presentation` może używać `application`,
- `application` może używać `domain`,
- `application` może definiować porty/interfejsy,
- `infrastructure` implementuje porty i może używać `domain`,
- `domain` nie zależy od pozostałych warstw.

Nie dopuszcza się cyklicznych zależności pomiędzy warstwami.

---

## 25. Granica między Domain a bazą danych

Reguła:

> **Model domenowy i model ORM są rozdzielone.**

Pozwala to:

- testować Core bez PostgreSQL,
- nie uzależniać znaczenia biznesowego od SQLAlchemy,
- zmieniać szczegóły persistence bez zmiany reguł biznesowych,
- kontrolować, czy Codex nie „przemyca” decyzji domenowych do modeli ORM.

W MVP oznacza to pewną dodatkową ilość kodu mapującego, ale jest ona świadomie zaakceptowana jako koszt czytelnej architektury.

---

## 26. Granica między Application a Infrastructure

Application definiuje **co system ma wykonać**.

Infrastructure definiuje **jak technicznie zapisać/odczytać dane lub plik**.

Przykład:

```text
APPLICATION:
"zatwierdź nowy SDS jako CURRENT"

DOMAIN:
"tylko jeden CURRENT; produkt wraca do PENDING_APPROVAL"

INFRASTRUCTURE:
"wykonaj odpowiednie operacje SQLAlchemy w PostgreSQL"

PRESENTATION:
"użytkownik nacisnął Zatwierdź i zobaczył wynik"
```

---

## 27. Granica między UI a Core

Streamlit nie może stać się miejscem implementacji procesu.

Niepoprawny kierunek:

```text
button()
  -> bezpośredni UPDATE tabel
  -> ręczna zmiana statusów
```

Poprawny kierunek:

```text
button()
  -> application use case
  -> domain rules
  -> repository
  -> PostgreSQL
```

Dzięki temu przyszła zmiana UI nie zmienia logiki systemu.

---

## 28. Granica plików źródłowych

Fizyczne katalogi SDS i dowodów BHP nie należą do repozytorium Git aplikacji.

Nie tworzymy w repozytorium katalogów zawierających produkcyjne:

- SDS,
- maile BHP,
- skany,
- zdjęcia dowodów.

Repozytorium zawiera kod i konfigurację wzorcową, a ścieżki do dokumentów wynikają z `.env`.

---

## 29. Zakaz projektowania „na przyszłość”

Repozytorium nie powinno zawierać pustych warstw i modułów przeznaczonych wyłącznie dla hipotetycznych funkcji.

W szczególności nie tworzymy teraz osobnych modułów dla:

- AI,
- REACH,
- API,
- wieloużytkownikowości,
- kolejek zadań,
- mikroserwisów.

Powstaną dopiero po zatwierdzeniu odpowiednich decyzji i wejściu w dany etap Roadmapy.

---

## 30. Zasady tworzenia nowych modułów

Codex może tworzyć pliki i moduły w ramach zatwierdzonej struktury, jeżeli są potrzebne do realizacji Tasku.

Jeżeli wykonanie Tasku wymaga:

- nowej warstwy,
- odwrócenia kierunku zależności,
- połączenia Domain z ORM,
- przeniesienia logiki do UI,
- nowego frameworka infrastrukturalnego,

Codex zatrzymuje implementację i zgłasza potrzebę decyzji.

---

## 31. Kryteria architektoniczne dla pierwszego repo

Pierwszy szkielet repozytorium jest poprawny, jeżeli:

1. istnieją cztery główne warstwy: `domain`, `application`, `infrastructure`, `presentation`,
2. `domain` nie importuje technologii infrastrukturalnych,
3. SQLAlchemy znajduje się w `infrastructure`,
4. Streamlit znajduje się w `presentation`,
5. Alembic posiada wydzielony katalog migracji,
6. testy są oddzielone od kodu aplikacji,
7. `.env` jest ignorowany przez Git,
8. `.env.example` jest wersjonowany,
9. produkcyjne dokumenty SDS/BHP nie znajdują się w repozytorium,
10. istnieje instrukcja uruchomienia,
11. struktura nie zawiera niezatwierdzonych technologii ani modułów „na przyszłość”.

---

## 32. Rozstrzygnięcie IR-001-35

**Zagadnienie:** Jaka jest docelowa struktura repozytorium i granice warstw?

**Status:** Resolved

**Decyzja:**

Repozytorium MVP jest podzielone na:

- `domain`,
- `application`,
- `infrastructure`,
- `presentation`,
- `migrations`,
- `tests`,
- pomocnicze `docs` i `scripts`.

Core domenowy jest niezależny od Streamlit, SQLAlchemy, PostgreSQL i systemu plików.

Dostęp do PostgreSQL i plików jest implementowany w `infrastructure`.

Streamlit komunikuje się z systemem poprzez przypadki użycia warstwy `application`.

---

## 33. Konsekwencje decyzji

### Pozytywne

- jasne granice dla Codexa,
- Core możliwy do testowania bez UI i PostgreSQL,
- łatwiejszy audyt architektury przez Cerberusa,
- mniejsze ryzyko przenikania logiki do Streamlit,
- możliwość późniejszej zmiany UI lub infrastruktury bez przebudowy domeny,
- czytelne miejsce dla migracji i testów.

### Koszt

- więcej plików niż w bardzo prostej aplikacji Streamlit,
- konieczność mapowania pomiędzy modelem domenowym i ORM,
- większa dyscyplina implementacyjna.

Koszt jest świadomie zaakceptowany, ponieważ projekt ma być wzorcem kontrolowanej współpracy Architekt–Cerberus–Codex i fundamentem do późniejszych projektów.

---

## 34. Elementy pozostające poza TDR-003

TDR-003 nie rozstrzyga:

- szczegółowego schematu tabel PostgreSQL,
- nazw wszystkich klas i metod,
- technologii ekstrakcji PDF,
- AI/REACH,
- polityki backupu IR-001-37,
- migracji `MSDS_baza.xlsx`,
- szczegółowego UI,
- przyszłej architektury wieloużytkownikowej.

Elementy te wymagają odpowiednich Tasków lub późniejszych BDR/TDR.

---

## 35. Ograniczenia dla Codexa

Codex nie może bez zatwierdzonej decyzji:

- zmieniać kierunku zależności warstw,
- łączyć modelu domenowego z ORM,
- umieszczać Core w Streamlit,
- wykonywać standardowej logiki persistence bezpośrednio w UI,
- dodawać niezatwierdzonych frameworków,
- dodawać modułów AI/REACH „na przyszłość”,
- umieszczać produkcyjnych SDS lub dowodów BHP w Git,
- omijać Alembic przy zmianach schematu,
- używać bazy operacyjnej do testów integracyjnych.

---

## 36. Powiązane dokumenty

TDR-003 należy czytać łącznie z:

- CORE-001,
- BDR-001,
- BDR-002,
- BDR-003,
- BDR-004,
- TDR-001,
- TDR-002,
- ADR-001,
- ADR-002,
- ADR-003,
- PDP-001,
- ROADMAP-001,
- Konstytucją projektu.

---

## 37. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono strukturę repozytorium, granice Domain/Application/Infrastructure/Presentation, rozdzielenie modelu domenowego od ORM oraz zasady migracji i testów |
