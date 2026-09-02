# TASK-011 — raport wykonania

## 1. Status

**DONE** — reguły biznesowe istniejącego PRODUCT zostały domknięte i
zweryfikowane pionowo na rzeczywistym PostgreSQL.

## 2. Stan wejściowy

- CORE: v1.2-approved.
- Repozytoria i `TransactionExecutor` TASK-010: dostępne.
- Testy bazowe: 88 passed.
- Alembic revisions: 4.
- PostgreSQL: `d2b4f6a8c190 (head)`.
- Tabele aplikacyjne: 9.
- Drift: brak.
- Rekordy biznesowe: 0.

## 3. Zakres zmian kodu

TASK-011 nie wymagał zmiany kodu produkcyjnego. Rozszerzono wyłącznie
`tests/integration/test_product_usage_repositories.py` o trzy scenariusze oraz
dodatkowe asercje wymagane przez Task. Utworzono niniejszy raport.

## 4. Product read tests

Potwierdzono:

- pusty `ListProducts` zwraca `[]`,
- istniejący PRODUCT pojawia się na liście,
- poprawne powiązanie i nazwa MANUFACTURER,
- `usage_status` mapuje się do `ProductUsageStatus.ACTIVE`,
- `waste_type` i `waste_code` zachowują `None`,
- `GetProductDetails` zwraca producenta, lokalizacje i quantity,
- wartości `Numeric` wracają jako `Decimal`, bez ORM poza infrastructure.

## 5. Ochrona tożsamości PRODUCT

Test zapisuje przed aktualizacją zestaw:

```text
product_name
manufacturer_product_code
manufacturer_id
usage_status
```

i porównuje go z ponownym odczytem w nowej sesji po commit. Wszystkie wartości
pozostają niezmienione.

## 6. Aktualizacja danych administracyjnych

Pionowy test potwierdza commit zmian wyłącznie dla:

- `use_description`,
- `use_restriction`,
- `waste_type`,
- `waste_code`.

Nie istnieje `SetProductStatus` ani publiczna zmiana pól tożsamości.

## 7. UsageLocation create/deactivate/reactivate

Na pełnej ścieżce use case → repository → `TransactionExecutor` → PostgreSQL
potwierdzono:

- create daje `ACTIVE`,
- deactivate daje `INACTIVE`,
- reactivate przywraca `ACTIVE`,
- `location_id` pozostaje ten sam,
- istnieje nadal jeden rekord, bez delete i bez rekordu zastępczego,
- lista administracyjna jednocześnie zawiera `ACTIVE` i `INACTIVE`.

## 8. Jedna i wiele lokalizacji produktu

Istniejący test jednego przypisania potwierdza relację po commit i jej obecność
w `GetProductDetails`. Dodany scenariusz zapisuje dwa równoczesne przypisania
tego samego produktu do dwóch różnych aktywnych lokalizacji. Oba są zwracane w
szczegółach produktu z własnymi quantity i jednostkami.

## 9. Blokada `INACTIVE`

Przypisanie do nieaktywnej lokalizacji kończy się
`InactiveUsageLocationError` przed zapisem repozytorium. Nowa sesja potwierdza
brak rekordu PRODUCT_USAGE_LOCATION i brak częściowego zapisu.

## 10. Peak quantity scenarios

Pełna regresja potwierdza:

- `Decimal("0")` jest poprawne i pozostaje zerem po odczycie PostgreSQL,
- wartości dodatnie są zapisywane i odczytywane jako `Decimal`,
- wartość ujemna jest odrzucana przez istniejącą walidację Domain,
- CHECK PostgreSQL pozostaje drugą linią ochrony.

## 11. Monthly consumption scenarios

Potwierdzono:

- `None/None` jako brak informacji,
- `Decimal("0") + unit` jako świadome zero różne od NULL,
- zapis i odczyt wartości dodatniej,
- odrzucenie wartości ujemnej,
- odrzucenie value bez unit,
- odrzucenie unit bez value.

Scenariusze negatywne korzystają z istniejących testów Domain/Application i nie
duplikują reguł w persistence.

## 12. Jednostki i brak konwersji

Test wielu lokalizacji zapisuje niezależne wartości i jednostki, w tym peak w
`l` oraz monthly w `kg`. Odczyt zwraca je bez zamiany i bez konwersji. Istniejące
testy agregacji potwierdzają sumowanie zgodnych jednostek, błąd dla różnych
jednostek i brak wpływu monthly na peak factory quantity.

## 13. `UpdateProductUsageLocation`

Pionowy test potwierdza aktualizację czterech pól quantity, commit i odczyt w
nowej sesji. Złożony PK `(product_id, location_id)` pozostaje niezmieniony.

## 14. `EntityNotFoundError`

Kontrolowany wyjątek application potwierdzono dla:

- brakującego PRODUCT w `GetProductDetails`,
- brakującej USAGE_LOCATION w deactivate,
- brakującej USAGE_LOCATION w reactivate,
- brakującego PRODUCT_USAGE_LOCATION w update quantities.

W tych scenariuszach wyjątki ORM/PostgreSQL nie wyciekają.

## 15. `PersistenceError`

Celowy konflikt integralności przechodzący przez `TransactionExecutor`:

- wywołuje rollback,
- jest tłumaczony na `PersistenceError`,
- zachowuje instancję `SQLAlchemyError` jako `__cause__`,
- ma neutralny komunikat `Database operation failed.`, bez niezatwierdzonej
  interpretacji biznesowej.

## 16. Commit tests

Widoczność w nowej sesji po commit potwierdzono dla:

- `UpdateProductAdministrativeData`,
- `CreateUsageLocation`,
- `DeactivateUsageLocation`,
- `ReactivateUsageLocation`,
- `AssignProductUsageLocation`,
- `UpdateProductUsageLocation`.

## 17. Rollback tests

Zachowano dwa scenariusze TASK-010. Jeden wykonuje poprawny UPDATE produktu, a
następnie powoduje konflikt PK. Po rollback nowa sesja widzi pierwotne dane i
brak częściowo dodanej lokalizacji. Drugi potwierdza brak lokalizacji oraz
przypisania po odrzuceniu quantity przez CHECK PostgreSQL.

## 18. Testy PostgreSQL

Testy integracyjne korzystają z konfiguracji `msds_manager` i sterownika
PostgreSQL, nie z SQLite. Rozszerzony plik persistence ma wynik:

```text
9 passed
```

Każdy scenariusz usuwa swoje techniczne dane wejściowe w `finally`.

## 19. Pełny pytest / `SAWarning`

Uruchomiono:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **91 passed**, kod wyjścia 0, brak `SAWarning`.

## 20. Granice architektury

Testy AST pozostały nieosłabione i przechodzą: application nie importuje
infrastructure/SQLAlchemy/psycopg, Domain nie importuje warstw zewnętrznych ani
persistence, a infrastructure implementuje porty application. Wynik: 3 passed.

## 21. Brak zmian ORM/schema

TASK-011 nie zmienił Domain, application, repository adapters, ORM, constraints
ani konfiguracji Alembic. Nie utworzono piątej migracji ani tabeli. Zmiany
widoczne w tych obszarach w roboczym Git pochodzą z wcześniejszych
zaakceptowanych Tasków i zostały zachowane.

## 22. `alembic current`

```text
d2b4f6a8c190 (head)
```

Liczba rewizji: 4.

## 23. `alembic check`

```text
No new upgrade operations detected.
```

Rzeczywisty drift: brak.

## 24. Finalny stan PostgreSQL

- Current/head: `d2b4f6a8c190`.
- Tabele aplikacyjne: 9.
- Rekordy w każdej z 9 tabel: 0.
- Dane testowe pozostawione: nie.
- Constraints: bez zmian.

## 25. Git/bezpieczeństwo

- `git diff --check`: bez błędów, tylko ostrzeżenia LF/CRLF,
- `git diff --cached --check`: bez błędów,
- `.env`: ignorowany i nietrackowany,
- sekrety: nie dodano ani nie ujawniono,
- dumpy, backupy, PDF i MSG: brak,
- nowe biblioteki i zmiany `pyproject.toml`: brak,
- commit/push: nie wykonano,
- wcześniejsze zmiany użytkownika zachowano.

## 26. Odstępstwa

Brak.

## 27. Problemy/ryzyka

Brak blockerów. Task pozostaje walidacyjny: nie dodano nowej semantyki
konfliktów, konwersji jednostek, delete ani historii. Repozytorium robocze jest
nieczyste z powodu skumulowanych, niecommitowanych wyników jawnie wykonanych
Tasków.

## 28. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-012.
