# TASK-003 REPORT

## 1. Status

DONE

Zaimplementowano czysty model domenowy Core, zatwierdzone enumy oraz regułę
agregacji ilości bez zależności od infrastruktury, UI, ORM i filesystemu.

## 2. Zakres wykonania

- dodano osiem zatwierdzonych enumów bez dodatkowych wartości,
- dodano dziewięć modeli domenowych,
- zastosowano `Decimal` dla ilości oraz `date`/`datetime` dla dat i czasu,
- kolekcje H-statements reprezentowane są przez deterministyczne krotki,
- brakujące dane składnika SDS mogą być reprezentowane przez `None` i pustą krotkę,
- status `UsageLocation` ma prostą reprezentację tekstową; nie utworzono
  niezatwierdzonego enumu,
- dodano regułę sumowania ilości w tej samej jednostce,
- dodano domenowy wyjątek odmawiający sumowania różnych jednostek,
- nie zaimplementowano żadnej konwersji jednostek,
- dodano komplet testów jednostkowych i uruchomiono testy regresyjne.

## 3. Modele domenowe

- `Manufacturer`,
- `Product`,
- `UsageLocation`,
- `ProductUsageLocation`,
- `SdsDocument`,
- `BhpDecision`,
- `DecisionEvidence`,
- `SafetyProfile`,
- `SdsComponent`.

Modele są prostymi, niemutowalnymi dataclasses ze slotami. Nie wykonują dostępu
do bazy, `.env` ani filesystemu podczas konstrukcji.

## 4. Enumy

- `ProductUsageStatus`: `PENDING_APPROVAL`, `ACTIVE`, `REJECTED`, `INACTIVE`,
- `SdsDocumentStatus`: `CURRENT`, `ARCHIVED`,
- `FileAvailabilityStatus`: `AVAILABLE`, `MISSING`,
- `BhpDecisionStatus`: `APPROVED`, `REJECTED`,
- `DecisionRecordStatus`: `CURRENT`, `SUPERSEDED`,
- `SafetyInformationStatus`: `YES`, `NO`, `NO_DATA`, `NOT_APPLICABLE`,
- `EvidenceType`: `EMAIL`, `DOCUMENT`, `PHOTO_SCAN`,
- `EvidenceFileFormat`: `MSG`, `PDF`, `JPG`, `JPEG`, `PNG`.

`BhpDecisionStatus` nie zawiera `PENDING`, a `NO_DATA` pozostaje odrębne od `NO`.

## 5. Reguła ilości

`sum_product_quantity()` sumuje `Decimal` bez utraty precyzji, jeśli wszystkie
przekazane `ProductUsageLocation` mają dokładnie tę samą jednostkę. Różne
jednostki powodują `MixedQuantityUnitsError`. Nie jest wykonywana konwersja
`kg↔g`, `l↔ml` ani `kg↔l`.

## 6. Pełna lista zmienionych plików

Utworzone:

- `app/domain/enums/statuses.py`,
- `app/domain/models/catalog.py`,
- `app/domain/models/documents.py`,
- `app/domain/models/safety.py`,
- `app/domain/exceptions/quantity.py`,
- `app/domain/rules/quantities.py`,
- `tests/unit/test_domain_enums.py`,
- `tests/unit/test_domain_models.py`,
- `tests/unit/test_domain_quantity_rules.py`,
- `docs/task_reports/TASK-003_REPORT.md`.

Zmienione:

- `app/domain/enums/__init__.py`,
- `app/domain/models/__init__.py`,
- `app/domain/exceptions/__init__.py`,
- `app/domain/rules/__init__.py`.

## 7. Testy i wyniki

Polecenie:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Wynik: **28 passed**, kod wyjścia 0. Obejmuje 22 testy domenowe TASK-003 oraz
6 wcześniejszych testów regresyjnych.

Pokryto dokładne wartości enumów, tworzenie wszystkich modeli, opcjonalność daty
i rewizji SDS, rozróżnienie `NO_DATA`/`NO`, niezależne statusy endokrynne, brak
`PENDING`, statusy `CURRENT`/`SUPERSEDED`, sumowanie `Decimal`, odmowę mieszania
jednostek bez konwersji, brakujące dane składnika oraz domyślne `None` dla
`last_manual_edit_at`.

## 8. Kontrola architektury

- importy SQLAlchemy w `app/domain`: BRAK,
- importy psycopg/Alembic/Streamlit w `app/domain`: BRAK,
- importy `app.infrastructure` lub `.env` w `app/domain`: BRAK,
- markery ORM (`DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`): BRAK,
- `create_all()`: BRAK,
- dostęp modeli do filesystemu: BRAK,
- modele dostawcy, magazynu i encje H-statement: BRAK.

## 9. Alembic i PostgreSQL

- `.\.venv\Scripts\python.exe -m alembic history`: kod wyjścia 0, historia pusta,
- pliki rewizji domenowych: 0,
- `target_metadata`: nadal `None`,
- tabele poza schematami `pg_catalog` i `information_schema`: 0,
- nie utworzono ani nie zmodyfikowano danych w PostgreSQL.

## 10. Zależności

`pyproject.toml` nie został zmieniony. Nie dodano żadnej biblioteki.

## 11. Git i bezpieczeństwo

- `.env` istnieje lokalnie i jest ignorowany przez Git,
- `.env` nie jest śledzony,
- `.env` nie został odczytany, zmieniony ani ujawniony,
- rzeczywiste dokumenty SDS/BHP w repozytorium: BRAK,
- lokalne pliki baz danych w repozytorium: BRAK,
- sekrety dodane w TASK-003: BRAK,
- konfiguracja PostgreSQL i systemowy `PATH` nie zostały zmienione.

Repozytorium nadal pokazuje pliki projektu jako nieśledzone, zgodnie ze stanem
zastanym przed TASK-003. Task nie obejmował inicjalnego commita.

## 12. Decyzje techniczne w granicach Tasku

- identyfikatory reprezentowane są przez `str`, bez projektowania strategii
  kluczy PostgreSQL,
- `UsageLocation.status` jest tekstem, ponieważ nie zatwierdzono jego enumu,
- modele pogrupowano według odpowiedzialności w `catalog`, `documents` i `safety`,
- modele i enumy są eksportowane z odpowiednich pakietów domenowych,
- nie dodano walidacji biznesowych niewynikających jednoznacznie ze specyfikacji.

## 13. Odstępstwa

BRAK.

## 14. Problemy wymagające decyzji

BRAK.

## 15. Jak zweryfikować rezultat

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m alembic history
rg -n "sqlalchemy|streamlit|psycopg|alembic|app\.infrastructure" app\domain
git check-ignore .env
git status --short
```

Pierwsze polecenie powinno zakończyć się wynikiem 28 passed, historia Alembic
powinna pozostać pusta, a wyszukiwanie niedozwolonych importów nie powinno
zwrócić wyników.

## 16. Następny krok

OCZEKUJĘ NA REVIEW CERBERUSA I JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-004.
