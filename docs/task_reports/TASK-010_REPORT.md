# TASK-010 — raport wykonania

## 1. Status

**DONE** — adaptery SQLAlchemy oraz minimalna granica transakcji zostały
zaimplementowane zgodnie z kontraktami TASK-009.

## 2. Stan wejściowy

- CORE: v1.2-approved.
- Application ports i use case'y TASK-009: dostępne.
- Testy bazowe: 81 passed.
- Alembic revisions: 4.
- PostgreSQL current: `d2b4f6a8c190 (head)`.
- Tabele aplikacyjne: 9.
- Drift: brak.
- Rekordy biznesowe: 0.

## 3. Repository adapters

Utworzono:

- `SqlAlchemyProductRepository`,
- `SqlAlchemyUsageLocationRepository`,
- `SqlAlchemyProductUsageLocationRepository`.

Zachowano istniejący `SqlAlchemyManufacturerRepository`. Każdy adapter
implementuje odpowiadający mu aktualny port application i korzysta z
zewnętrznie przekazanej `Session`. Nie dodano generic/base/CRUD repository.

## 4. Mapping ORM ↔ Domain/DTO

Mapping jest jawny:

- wiersze PRODUCT + MANUFACTURER są składane do `ProductListItem`,
- PRODUCT + MANUFACTURER + PRODUCT_USAGE_LOCATION + USAGE_LOCATION są składane
  do `ProductDetails` i `ProductUsageLocationDetails`,
- `UsageLocationModel` jest mapowany do domenowego `UsageLocation`,
- domenowe `UsageLocation` i `ProductUsageLocation` są jawnie mapowane na
  odpowiednie modele ORM przy zapisie.

Modele ORM nie opuszczają infrastructure. `Numeric` pozostaje `Decimal`, a
statusy są przekazywane jako `ProductUsageStatus` i `UsageLocationStatus`.

## 5. Product repository

- `list_all()` wykonuje jawny join PRODUCT–MANUFACTURER i zwraca DTO listy.
- `get_details()` pobiera wyłącznie PRODUCT, MANUFACTURER,
  PRODUCT_USAGE_LOCATION i USAGE_LOCATION; nie pobiera SDS/BHP/SafetyProfile.
- Brak produktu jest zwracany jako `None`, które use case tłumaczy na
  `EntityNotFoundError`.
- `update_administrative_data()` używa celowanego SQL `UPDATE` tylko dla
  `use_description`, `use_restriction`, `waste_type` i `waste_code`.
- Nie użyto `merge`; pola tożsamości i `usage_status` nie są częścią UPDATE.

## 6. UsageLocation repository

- `list_all()` zwraca administracyjnie zarówno `ACTIVE`, jak i `INACTIVE`.
- `get_by_id()` zwraca model Domain albo `None`.
- `add()` zapisuje ID, nazwę i status otrzymane z Domain; brak DB defaultu.
- `update_status()` aktualizuje wyłącznie kolumnę `status` dla zachowanego ID.
- Repozytorium nie decyduje o przejściu statusu i nie udostępnia delete.

## 7. ProductUsageLocation repository

- `add()` zapisuje oba identyfikatory i cztery pola quantity.
- `update_quantities()` aktualizuje wyłącznie cztery pola quantity, używając
  `(product_id, location_id)` wyłącznie jako warunku wyszukiwania.
- Nie duplikuje walidacji Domain i nie konwertuje jednostek ani `Decimal`.
- Nie zawiera delete/remove ani mechanizmu omijającego blokadę lokalizacji
  `INACTIVE` z use case'u TASK-009.

## 8. Manufacturer adapter

`SqlAlchemyManufacturerRepository` pozostał bez zmian. Istniejący pionowy test
TASK-007 przechodzi w pełnej regresji.

## 9. Granica transakcji

Dodano mały `TransactionExecutor`. Dla jednej przekazanej operacji:

```text
utworzenie Session
→ wykonanie use case'u i repository calls
→ jeden commit
albo
→ rollback całej transakcji
```

Nie utworzono frameworka Unit of Work ani transaction managera w application.

## 10. Miejsce commit/rollback

`commit()` i `rollback()` występują wyłącznie w `TransactionExecutor`, powyżej
pojedynczych wywołań repozytorium. Repozytoria nie wykonują commit-per-method.
Kontrola AST potwierdza brak `commit()` w katalogu repository.

## 11. Translacja błędów infrastruktury

- Oczekiwany brak encji pozostaje kontraktem `None`/`False` portu i jest
  tłumaczony przez use case na `EntityNotFoundError`.
- `SQLAlchemyError`, w tym `IntegrityError`, jest przechwytywany przez granicę
  transakcji po rollback i tłumaczony na kontrolowany `PersistenceError`.
- Oryginalny błąd jest zachowany jako przyczyna diagnostyczna, lecz nie jest
  bezpośrednim wyjątkiem granicy wywołania.
- Nie wymyślono biznesowej semantyki konfliktów ani retry.

## 12. Testy repository

Dodano 6 testów integracyjnych na rzeczywistym PostgreSQL. Potwierdzono:

- listę PRODUCT z nazwą producenta,
- szczegóły produktu z lokalizacją i quantity,
- mapowanie enumów i zachowanie `Decimal`,
- celowaną aktualizację administracyjną bez zmiany tożsamości/statusu,
- zapis, odczyt i listę UsageLocation,
- zapis i aktualizację ProductUsageLocation bez zmiany PK,
- peak `0`, monthly `NULL/NULL`, monthly `0 + unit` i różne jednostki,
- odrzucenie niepoprawnej quantity przez istniejący CHECK PostgreSQL.

Wynik pliku persistence: **6 passed**.

## 13. Testy transaction commit/rollback

Commit potwierdzono przez odczyt zmian w nowej sesji po każdej poprawnej
operacji zapisującej:

- `UpdateProductAdministrativeData`,
- `CreateUsageLocation`,
- `DeactivateUsageLocation`,
- `ReactivateUsageLocation`,
- `AssignProductUsageLocation`,
- `UpdateProductUsageLocation`.

Rollback przetestowano transakcją zawierającą poprawny UPDATE produktu, a potem
celowy konflikt PK. Po błędzie ani UPDATE, ani próba dodania lokalizacji nie
pozostały w PostgreSQL. Osobny test potwierdził rollback lokalizacji i
przypisania odrzuconego przez quantity CHECK.

## 14. Pionowe testy application → PostgreSQL

Potwierdzono działanie pełnych ścieżek:

- `CreateUsageLocation` → `SqlAlchemyUsageLocationRepository` → PostgreSQL,
- `UpdateProductAdministrativeData` → `SqlAlchemyProductRepository` →
  PostgreSQL,
- `AssignProductUsageLocation` → oba wymagane repository adapters →
  PostgreSQL,
- dodatkowo deactivate, reactivate i update quantities przez use case'y.

Przypisanie do `INACTIVE` jest odrzucane przed zapisem repository.

## 15. Pełny pytest i `SAWarning`

Uruchomiono:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **88 passed**, kod wyjścia 0, brak `SAWarning`.

## 16. Granice architektury

Testy AST potwierdzają:

- application nie importuje infrastructure, SQLAlchemy, psycopg ani Alembic,
- domain nie importuje application, infrastructure ani bibliotek persistence,
- Session pozostaje w infrastructure,
- repository adapters mogą importować application ports/DTO i Domain,
- repozytoria nie zawierają commit ani metod delete/remove.

Wynik kontroli architektury: **3 passed**.

## 17. Brak zmian schema

TASK-010 nie zmienił modeli ORM, constraints, konfiguracji Alembic ani schema.
Nie utworzono piątej migracji. Zmiany ORM widoczne w roboczym Git pochodzą z
wcześniejszego zaakceptowanego TASK-009-ALIGN i zostały zachowane bez ingerencji.

## 18. `alembic current`

```text
d2b4f6a8c190 (head)
```

Liczba rewizji: 4.

## 19. `alembic check`

```text
No new upgrade operations detected.
```

Rzeczywisty drift: brak.

## 20. Finalny stan PostgreSQL

- Current/head: `d2b4f6a8c190`.
- Tabele aplikacyjne: 9.
- Rekordy w każdej z 9 tabel aplikacyjnych: 0.
- Dane testowe pozostawione: nie.
- Constraints TASK-006, TASK-008 i TASK-009-ALIGN: bez zmian.

## 21. Git/bezpieczeństwo

- `git diff --check`: bez błędów; występują tylko ostrzeżenia LF/CRLF,
- `git diff --cached --check`: bez błędów,
- `.env`: ignorowany i nietrackowany,
- sekretów nie dodano ani nie ujawniono,
- dumpów, backupów, PDF i MSG: brak,
- `pyproject.toml` i zależności: bez zmian,
- commit/push: nie wykonano,
- wcześniejsze zmiany użytkownika i zaakceptowanych Tasków zachowano.

## 22. Odstępstwa

Brak.

## 23. Problemy/ryzyka

Brak blockerów. `PersistenceError` celowo nie nadaje biznesowego znaczenia
konfliktom integralności; szczegółowe komunikaty konfliktów wymagają przyszłej
zatwierdzonej decyzji. Granica transakcji jest minimalna i przeznaczona do
wywoływania z przyszłego composition root, bez wprowadzania UoW frameworka.

## 24. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-011.
