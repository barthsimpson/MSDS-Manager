# TASK-007 — Application Smoke Test / pierwszy pionowy przebieg

**Projekt:** MSDS Manager  
**Task ID:** TASK-007  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Zamknąć Sprint 1 poprzez wykonanie minimalnego, kontrolowanego przebiegu przez przygotowane warstwy aplikacji:

```text
configuration
    ↓
application
    ↓
persistence / SQLAlchemy
    ↓
PostgreSQL
    ↓
application result
```

TASK-007 ma udowodnić, że fundament projektu działa jako całość, a nie wyłącznie jako zestaw osobno przetestowanych elementów.

To jest **smoke test szkieletu aplikacji**, a nie rozpoczęcie właściwego workflow SDS.

---

## 2. Warunek wejścia

TASK-006 jest zakończony `DONE` i zaakceptowany.

Stan wejściowy:

- modele domenowe: gotowe,
- modele ORM: gotowe,
- PostgreSQL schema: gotowe,
- constraints Core: aktywne,
- Alembic revisions: 2,
- current revision: `bae33dc76391 (head)`,
- tabele aplikacyjne: 9,
- testy: 44/44 passed,
- baza nie zawiera danych biznesowych/testowych,
- `.env` pozostaje lokalny i ignorowany.

---

## 3. Źródła obowiązujące

Implementacja musi być zgodna z:

- CORE-001 v1.0-approved,
- BDR-001..005,
- TDR-001..003,
- zaakceptowanymi TASK-003..006,
- AGENTS.md.

TASK-007 nie może zmieniać zatwierdzonego Core ani modelu persistence tylko po to, aby uprościć smoke test.

---

# CZĘŚĆ A — GRANICA SCOPE

## 4. Co dokładnie testujemy

Minimalny pionowy przebieg powinien potwierdzić:

1. konfiguracja projektu jest ładowana,
2. aplikacja może uzyskać sesję SQLAlchemy,
3. sesja łączy się z PostgreSQL,
4. warstwa application wywołuje persistence przez jawny port,
5. infrastruktura wykonuje minimalną operację,
6. wynik wraca do application,
7. transakcja działa poprawnie,
8. test nie pozostawia trwałych danych.

---

## 5. Czego jeszcze NIE budujemy

Nie implementuj:

- importu SDS,
- importu PDF,
- ekstrakcji sekcji 2/3/11,
- AI/LLM,
- workflow akceptacji SDS,
- workflow BHP,
- automatycznej archiwizacji,
- REACH,
- importu Excela,
- pełnego CRUD,
- generic repository framework,
- service layer framework,
- REST API,
- FastAPI,
- React,
- ekranów biznesowych Streamlit,
- użytkowników/uprawnień,
- logowania,
- audytu zmian,
- seedowania bazy.

TASK-007 ma pozostać mały.

---

# CZĘŚĆ B — PIERWSZY USE CASE

## 6. Minimalny use case

Zaimplementuj jeden minimalny use case aplikacyjny służący wyłącznie potwierdzeniu pionowego przebiegu.

Preferowany przypadek:

```text
ListManufacturers
```

lub równoważna, równie prosta operacja odczytowa.

Semantyka:

```text
Application
    ↓
ManufacturerRepositoryPort
    ↓
SQLAlchemy implementation
    ↓
SELECT manufacturers
    ↓
wynik wraca do Application
```

Nie rozszerzaj use case o filtrowanie, wyszukiwanie, paginację, sortowanie biznesowe ani CRUD.

---

## 7. Dlaczego odczyt zamiast pełnego CRUD

TASK-007 ma zweryfikować architekturę, nie projektować jeszcze API aplikacji.

Minimalny odczyt wystarcza do potwierdzenia:

- dependency direction,
- portu,
- adaptera SQLAlchemy,
- sesji,
- połączenia,
- mapowania ORM → domain/application result.

Jeżeli do testu potrzebne są dane, mają istnieć wyłącznie w transakcji testowej i zostać wycofane.

---

# CZĘŚĆ C — PORT

## 8. ManufacturerRepositoryPort

W:

```text
app/application/ports/
```

utwórz minimalny port potrzebny use case.

Port powinien opisywać potrzebę aplikacji, np.:

```python
class ManufacturerRepositoryPort(Protocol):
    def list_all(self) -> list[Manufacturer]:
        ...
```

Dopuszczalne jest użycie `Protocol`, ABC lub istniejącej konwencji projektu.

Preferuj najmniejszą liczbę abstrakcji.

Nie twórz generic repository typu:

```text
Repository[T]
BaseRepository
CRUDRepository
```

---

# CZĘŚĆ D — USE CASE

## 9. ListManufacturers

W:

```text
app/application/use_cases/
```

utwórz minimalny use case.

Use case:

- otrzymuje port w konstruktorze,
- nie zna SQLAlchemy,
- nie zna PostgreSQL,
- nie ładuje `.env`,
- nie tworzy sesji DB,
- zwraca rezultat zgodny z warstwą application/domain.

Przepływ:

```text
ListManufacturers.execute()
        ↓
ManufacturerRepositoryPort.list_all()
        ↓
list[Manufacturer]
```

Nie dodawaj logiki biznesowej, której nie ma w Core.

---

# CZĘŚĆ E — ADAPTER SQLALCHEMY

## 10. Implementacja repository

W:

```text
app/infrastructure/db/repositories/
```

utwórz minimalną implementację portu, np.:

```text
SqlAlchemyManufacturerRepository
```

Adapter:

- otrzymuje istniejącą `Session`,
- wykonuje SELECT przez SQLAlchemy 2.x,
- mapuje ORM → model domenowy,
- nie wykonuje commit wewnątrz prostego odczytu,
- nie tworzy Engine,
- nie czyta `.env`,
- nie zawiera logiki UI.

---

## 11. Mapping ORM → Domain

Mapping ma być jawny i minimalny.

Nie dodawaj obecnie:

- frameworka mapperów,
- automatycznego reflection,
- biblioteki mapującej,
- globalnego AutoMappera.

Dla jednego modelu wystarczy prosty kod adaptera.

Jeżeli pola `Manufacturer` z TASK-003 różnią się nazwami od ORM, odwzoruj je zgodnie z rzeczywistym zatwierdzonym modelem.

Nie zmieniaj Domain tylko dla wygody repository.

---

# CZĘŚĆ F — TRANSAKCJA I SESJA

## 12. Session ownership

Wykorzystaj istniejące fabryki Engine/sessionmaker z TASK-002.

Nie twórz drugiego mechanizmu połączenia.

Dla smoke testu odpowiedzialność powinna być czytelna:

```text
composition/test boundary
    ↓
Session
    ↓
Repository
    ↓
Use Case
```

Repository nie powinno samodzielnie tworzyć globalnej sesji.

---

## 13. Dane smoke testu

Test może utworzyć minimalne dane:

```text
Manufacturer A
Manufacturer B
```

wyłącznie w kontrolowanej transakcji testowej.

Po zakończeniu:

```text
ROLLBACK
```

i baza ma wrócić do stanu bez danych biznesowych.

Nie dodawaj seedów ani fixture danych do migracji.

---

# CZĘŚĆ G — TEST PIONOWY

## 14. Integration smoke test

Dodaj test, który rzeczywiście przechodzi przez:

```text
Settings
→ Engine/session factory
→ Session
→ SqlAlchemyManufacturerRepository
→ ListManufacturers
→ PostgreSQL
→ wynik
```

Nie mockuj PostgreSQL w tym teście.

Test ma wymagać aktywnej lokalnej bazy developerskiej `msds_manager` na `head`.

---

## 15. Scenariusz testowy

Minimalny scenariusz:

1. potwierdź połączenie z bazą,
2. rozpocznij kontrolowaną transakcję,
3. dodaj 2 producentów przez techniczny setup testu,
4. utwórz repository,
5. przekaż repository do `ListManufacturers`,
6. wykonaj use case,
7. potwierdź, że zwrócono dokładnie oczekiwanych producentów,
8. potwierdź, że wynik jest modelem domenowym / rezultatem application, a nie obiektem ORM,
9. wykonaj rollback,
10. potwierdź brak pozostawionych rekordów.

Setup danych testowych może korzystać bezpośrednio z ORM, ponieważ nie testujemy jeszcze use case zapisu.

---

## 16. Test dependency direction

Dodaj lub rozszerz kontrolę architektoniczną tak, aby potwierdzić:

```text
application
    NIE importuje infrastructure

domain
    NIE importuje application/infrastructure/SQLAlchemy

infrastructure
    MOŻE implementować application ports
```

Nie twórz rozbudowanego narzędzia dependency analysis.

Wystarczy prosta deterministyczna kontrola zgodna z istniejącymi testami.

---

# CZĘŚĆ H — MINIMALNY ENTRYPOINT SMOKE

## 17. Skrypt uruchomieniowy

Dodaj minimalny skrypt:

```text
scripts/smoke_application.py
```

Jego celem jest ręczne potwierdzenie, że aplikacja:

- ładuje konfigurację,
- tworzy Engine/session,
- wykonuje use case,
- kończy się bez błędu.

Skrypt nie może:

- tworzyć schema,
- uruchamiać migracji,
- dodawać danych biznesowych,
- zmieniać danych,
- uruchamiać Streamlit.

Na pustej bazie poprawny rezultat może być np.:

```text
Application smoke test: OK
Manufacturers returned: 0
```

Nie traktuj dokładnego tekstu jako kontraktu biznesowego.

---

## 18. Brak automatycznych migracji przy starcie

Smoke entrypoint nie może wykonywać:

```text
alembic upgrade
create_all
DDL
```

Jeżeli schema nie istnieje lub baza nie jest dostępna, skrypt ma zakończyć się czytelnym błędem.

Aplikacja nie ma samodzielnie „naprawiać” infrastruktury.

---

# CZĘŚĆ I — STREAMLIT

## 19. Streamlit w TASK-007

Streamlit jest zatwierdzoną technologią projektu, ale TASK-007 **nie ma jeszcze budować interfejsu biznesowego**.

Jeżeli istniejący bootstrap TASK-001 zawiera minimalny placeholder Streamlit, nie rozwijaj go.

Nie jest wymagane uruchamianie przeglądarki ani tworzenie ekranu producentów.

Pierwszy UI powinien powstać dopiero jako świadomy następny etap po zamknięciu fundamentu.

---

# CZĘŚĆ J — TESTY REGRESJI

## 20. Pełny pytest

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Oczekiwane:

- wszystkie wcześniejsze 44 testy przechodzą,
- nowe testy smoke/application przechodzą,
- brak `SAWarning`.

Nie obniżaj jakości wcześniejszych testów.

---

## 21. Test skryptu smoke

Uruchom:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_application.py
```

Na aktualnej pustej bazie oczekiwany jest sukces i 0 producentów.

Po uruchomieniu potwierdź, że:

- liczba tabel nadal wynosi 9,
- revision nadal `bae33dc76391`,
- liczba rekordów biznesowych nadal 0.

---

# CZĘŚĆ K — ALEMBIC / SCHEMA

## 22. Brak nowej migracji

TASK-007 nie powinien wymagać zmiany schema.

Oczekiwany stan:

```text
Alembic revisions: 2
Current: bae33dc76391 (head)
Application tables: 9
```

Nie generuj trzeciej rewizji.

Jeżeli implementacja smoke testu wymaga zmiany schema — STOP.

---

## 23. Drift

Uruchom kontrolę zgodności ORM ↔ DB zgodnie z mechanizmem ustalonym po TASK-006.

Oczekiwany wynik:

```text
No new upgrade operations detected.
```

Nie modyfikuj filtra enum CHECK bez potrzeby.

---

# CZĘŚĆ L — GRANICE ARCHITEKTURY

## 24. Oczekiwany przepływ zależności

Po TASK-007 architektura powinna wyglądać:

```text
presentation
     ↓
application
     ↓
domain

infrastructure
     ↓
application ports
     ↓
domain
```

Composition root / skrypt może łączyć konkretne implementacje.

Nie dopuszczaj:

```text
domain → infrastructure
application → infrastructure
domain → SQLAlchemy
application → SQLAlchemy
```

---

## 25. Nie twórz frameworka przed potrzebą

TASK-007 nie jest zgodą na budowę:

- Unit of Work framework,
- Dependency Injection container,
- Service Locator,
- generic repositories,
- command bus,
- event bus,
- CQRS,
- mediator,
- plugin architecture.

Jeżeli do wykonania jednego use case potrzebna jest duża infrastruktura, oznacza to overengineering.

---

# CZĘŚĆ M — GIT I BEZPIECZEŃSTWO

## 26. Kontrole

Wykonaj:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Nie wykonuj commita bez jawnego polecenia.

Potwierdź:

- `.env` ignored,
- `.env` untracked,
- brak sekretów,
- brak dumpów,
- brak dokumentów SDS/BHP,
- brak danych testowych w repo.

---

# CZĘŚĆ N — STOP

## 27. Zasada STOP

Zatrzymaj Task i raportuj `PARTIAL` albo `BLOCKED`, jeżeli:

- potrzebna jest zmiana Core,
- potrzebna jest zmiana schema,
- potrzebna jest nowa migracja,
- wymagany jest nowy framework/biblioteka,
- port nie może być zdefiniowany bez nowej decyzji architektonicznej,
- istniejące fabryki session/engine są sprzeczne z wymaganym dependency direction,
- smoke test wymaga obejścia constraints Core,
- zadanie zaczyna implementować rzeczywisty workflow SDS/BHP.

---

# CZĘŚĆ O — KRYTERIA AKCEPTACJI

## 28. TASK-007 = DONE, jeżeli

1. istnieje minimalny `ManufacturerRepositoryPort`,
2. istnieje minimalny `ListManufacturers`,
3. istnieje adapter SQLAlchemy implementujący port,
4. use case nie zna SQLAlchemy/PostgreSQL,
5. domain pozostaje niezależny,
6. integration smoke test przechodzi przez prawdziwy PostgreSQL,
7. wynik nie ujawnia modelu ORM do application,
8. dane testowe są rollbackowane,
9. istnieje `scripts/smoke_application.py`,
10. skrypt działa na aktualnej pustej bazie,
11. skrypt nie wykonuje DDL ani migracji,
12. wszystkie testy przechodzą,
13. brak `SAWarning`,
14. nadal istnieją dokładnie 2 rewizje,
15. nadal istnieje 9 tabel,
16. baza pozostaje na `bae33dc76391 (head)`,
17. brak rzeczywistego driftu,
18. brak danych biznesowych po testach,
19. nie dodano nowych bibliotek,
20. nie rozpoczęto kolejnego Sprintu/Tasku.

---

# CZĘŚĆ P — WYMAGANY RAPORT

## 29. Raport

Utwórz:

```text
docs/task_reports/TASK-007_REPORT.md
```

Raport musi zawierać:

### 1. Status
`DONE`, `PARTIAL` albo `BLOCKED`.

### 2. Cel osiągnięty
Krótko opisz pionowy przebieg.

### 3. Utworzone/zmienione pliki

### 4. Port
Opis `ManufacturerRepositoryPort`.

### 5. Use case
Opis `ListManufacturers`.

### 6. Adapter SQLAlchemy
Opis query i mappingu ORM → Domain.

### 7. Dependency direction
Potwierdzenie granic warstw.

### 8. Integration smoke test
- setup,
- przebieg,
- rezultat,
- rollback.

### 9. Manual smoke script
- polecenie,
- wynik.

### 10. Testy regresji
- polecenie,
- liczba testów,
- wynik.

### 11. PostgreSQL final state
- revision,
- liczba tabel,
- liczba rekordów biznesowych.

### 12. Alembic / drift
- liczba rewizji,
- wynik kontroli driftu.

### 13. Git / bezpieczeństwo

### 14. Odstępstwa

### 15. Problemy / ryzyka

### 16. Ocena gotowości Sprintu 1
Odpowiedz jednoznacznie:

```text
SPRINT-001 FOUNDATION / CORE SKELETON:
READY FOR CERBERUS CLOSURE
```

albo opisz blokery.

### 17. Następny krok

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO SPRINTU ANI TASKU.
```

---

## 30. Zakończenie

Po wykonaniu TASK-007:

- pozostaw bazę na `head`,
- nie zmieniaj schema,
- nie generuj migracji,
- nie pozostawiaj danych testowych,
- zapisz raport,
- przedstaw krótkie podsumowanie,
- zatrzymaj się.

TASK-007 jest bramką zamykającą **SPRINT-001 — Foundation / Core Skeleton**.
