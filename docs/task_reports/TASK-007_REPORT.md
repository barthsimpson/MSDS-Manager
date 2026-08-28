# TASK-007 REPORT

## 1. Status

DONE

Minimalny pionowy przebieg aplikacji działa przez rzeczywistą konfigurację,
fabryki SQLAlchemy, port aplikacyjny, adapter persistence i PostgreSQL, a wynik
wraca jako modele domenowe. Test i ręczny skrypt nie pozostawiają danych ani nie
zmieniają schematu.

## 2. Cel osiągnięty

Potwierdzony przepływ:

```text
Settings
→ Engine / sessionmaker
→ Session
→ SqlAlchemyManufacturerRepository
→ ManufacturerRepositoryPort
→ ListManufacturers
→ SELECT manufacturers w PostgreSQL
→ list[Manufacturer]
```

Composition root znajduje się wyłącznie w teście integracyjnym i ręcznym
skrypcie. Warstwa application nie zna infrastruktury ani SQLAlchemy.

## 3. Utworzone/zmienione pliki

Utworzone:

- `app/application/ports/manufacturer_repository.py`,
- `app/application/use_cases/list_manufacturers.py`,
- `app/infrastructure/db/repositories/manufacturer.py`,
- `scripts/smoke_application.py`,
- `tests/integration/test_application_smoke.py`,
- `tests/unit/test_architecture_boundaries.py`,
- `docs/task_reports/TASK-007_REPORT.md`.

Zmienione:

- `app/application/ports/__init__.py`,
- `app/application/use_cases/__init__.py`,
- `app/infrastructure/db/repositories/__init__.py`.

Nie zmieniono domeny, modeli ORM, migracji, schema, presentation ani zależności.

## 4. Port

`ManufacturerRepositoryPort` jest minimalnym `Protocol` należącym do application:

```python
def list_all(self) -> list[Manufacturer]: ...
```

Port opisuje tylko potrzebę use case. Nie dodano generic repository, CRUD,
paginacji, filtrów, sortowania ani frameworka persistence.

## 5. Use case

`ListManufacturers`:

- otrzymuje `ManufacturerRepositoryPort` w konstruktorze,
- `execute()` deleguje pojedyncze wywołanie `list_all()`,
- zwraca `list[Manufacturer]`,
- nie importuje SQLAlchemy, PostgreSQL, konfiguracji ani infrastructure,
- nie tworzy sesji i nie zawiera dodatkowej logiki biznesowej.

## 6. Adapter SQLAlchemy

`SqlAlchemyManufacturerRepository`:

- implementuje `ManufacturerRepositoryPort`,
- otrzymuje zewnętrznie zarządzaną `Session`,
- wykonuje `select(ManufacturerModel)` w stylu SQLAlchemy 2.x,
- nie dodaje sortowania ani filtrów biznesowych,
- jawnie mapuje każdy `ManufacturerModel` na domenowy `Manufacturer`,
- nie zwraca modeli ORM poza infrastructure,
- nie tworzy Engine/sessionmaker,
- nie ładuje `.env`,
- nie wykonuje commit.

## 7. Dependency direction

Dodano deterministyczne testy AST dla importów wszystkich modułów application i
domain.

Potwierdzono:

- `application → domain`: TAK,
- `application → infrastructure`: NIE,
- `application → SQLAlchemy/psycopg/Alembic`: NIE,
- `domain → application/infrastructure`: NIE,
- `domain → SQLAlchemy/psycopg/Alembic/Streamlit`: NIE,
- `infrastructure → application ports/domain`: TAK, dozwolone,
- composition root łączy warstwy poza application/domain: TAK.

Nie dodano kontenera DI, Unit of Work, Service Locator, generic repository,
command/event bus, CQRS ani mediatora.

## 8. Integration smoke test

Plik: `tests/integration/test_application_smoke.py`.

### Setup

- załadowanie rzeczywistych `Settings`,
- potwierdzenie bazy `msds_manager`,
- utworzenie Engine przez istniejącą fabrykę,
- utworzenie sessionmaker przez istniejącą fabrykę,
- rozpoczęcie kontrolowanej transakcji PostgreSQL,
- techniczne dodanie dwóch producentów ORM i `flush`, bez commit.

### Przebieg

- wykonanie `SELECT 1`,
- utworzenie `Session` powiązanej z transakcją testu,
- utworzenie `SqlAlchemyManufacturerRepository`,
- przekazanie adaptera do `ListManufacturers`,
- wykonanie `execute()`.

### Rezultat

- zwrócono dokładnie dwóch oczekiwanych producentów,
- każdy wynik jest domenowym `Manufacturer`,
- żaden wynik nie jest `ManufacturerModel`,
- użyto prawdziwego PostgreSQL, bez mocka i bez SQLite.

### Rollback

- transakcja została wycofana w `finally`,
- osobne połączenie potwierdziło brak obu identyfikatorów testowych,
- kontrola po pełnym pytest potwierdziła 0 rekordów biznesowych we wszystkich
  tabelach.

Wynik testu pionowego: PASSED.

## 9. Manual smoke script

Plik: `scripts/smoke_application.py`.

Polecenie:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe scripts\smoke_application.py
```

Rzeczywisty wynik:

```text
Application smoke test: OK
Manufacturers returned: 0
```

Kod wyjścia: 0.

Skrypt:

- ładuje konfigurację,
- korzysta z istniejących fabryk Engine/sessionmaker,
- wykonuje ten sam use case,
- zamyka Session i Engine,
- wykonuje wyłącznie odczyt,
- nie uruchamia Alembic, `create_all`, DDL, INSERT, UPDATE, DELETE ani commit,
- zwraca bezpieczny komunikat błędu bez ujawniania URL/sekretu, jeśli baza lub
  schema są niedostępne.

Po skrypcie nadal: 9 tabel, rewizja `bae33dc76391`, 0 rekordów biznesowych.

## 10. Testy regresji

Polecenie:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **47 passed**, kod wyjścia 0, brak `SAWarning`.

Zestaw obejmuje:

- 4 testy integracyjne PostgreSQL,
- 43 testy jednostkowe/architektoniczne,
- wszystkie wcześniejsze testy TASK-001..006.

Nowe testy TASK-007: 3/3 passed.

## 11. PostgreSQL final state

- database: `msds_manager`,
- current revision: `bae33dc76391 (head)`,
- liczba tabel aplikacyjnych: 9,
- liczba producentów: 0,
- łączna liczba rekordów biznesowych: 0,
- schema zmieniony przez TASK-007: NIE,
- dane seed/testowe pozostawione: NIE.

Constraints TASK-006 pozostają aktywne; TASK-007 ich nie obchodzi ani nie
modyfikuje.

## 12. Alembic / drift

- liczba rewizji: dokładnie 2,
- trzecia rewizja utworzona: NIE,
- `alembic current`: `bae33dc76391 (head)`,
- `alembic history`: dwie oczekiwane rewizje,
- `alembic check`: `No new upgrade operations detected.`, kod wyjścia 0,
- rzeczywisty drift ORM ↔ PostgreSQL: BRAK.

Filtr enumowych type-bound CHECK-ów z TASK-006 nie został zmieniony.

## 13. Git / bezpieczeństwo

- commit wykonany: NIE,
- `git diff --check`: kod 0,
- `git diff --cached --check`: kod 0,
- `.env` ignored: TAK,
- `.env` tracked: NIE,
- `.env` zmieniony lub ujawniony: NIE,
- sekrety dodane: NIE,
- dumpy/backupy/lokalne pliki DB: BRAK,
- dokumenty SDS/BHP w repozytorium: BRAK,
- dane testowe w repozytorium: BRAK,
- nowe biblioteki: NIE,
- `pyproject.toml` zmieniony: NIE,
- systemowy `PATH` zmieniony: NIE.

Istniejące staged migracje TASK-005/006 pozostawiono bez zmian. Nowych plików
TASK-007 nie commitowano ani nie stage'owano automatycznie.

## 14. Odstępstwa

BRAK.

## 15. Problemy / ryzyka

- test pionowy wymaga działającego lokalnego PostgreSQL, poprawnego `.env`,
  schematu na head i katalogu PostgreSQL `bin` widocznego dla procesu,
- `ListManufacturers` celowo nie definiuje kolejności wyniku; przyszłe wymaganie
  sortowania wymaga świadomego kontraktu aplikacyjnego,
- smoke potwierdza szkielet odczytowy, ale celowo nie stanowi jeszcze workflow
  SDS/BHP ani pełnego API aplikacji.

Brak blokerów zamknięcia Sprintu 1.

## 16. Ocena gotowości Sprintu 1

```text
SPRINT-001 FOUNDATION / CORE SKELETON:
READY FOR CERBERUS CLOSURE
```

Konfiguracja, domena, persistence, migracje, constraints, testy integralności i
pierwszy pionowy przebieg application → PostgreSQL działają łącznie.

## 17. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO SPRINTU ANI TASKU.
