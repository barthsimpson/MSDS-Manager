# TASK-009-ALIGN — raport wykonania

## 1. Status

**DONE** — implementacja Domain, ORM i PostgreSQL została wyrównana z
`CORE-001 v1.2-approved` w zakresie `USAGE_LOCATION.status`.

## 2. Stan wejściowy

- Alembic current: `c41d8e2f7a90`.
- Rewizje Alembic: 3.
- Tabele aplikacyjne PostgreSQL: 9.
- Testy: 59 przed zmianą.
- `UsageLocation.status` był tekstem bez zatwierdzonego constraintu.
- Repozytorium zawierało niezatwierdzone w Git zmiany i pliki z wcześniejszych
  TASK-008/TASK-009; zostały zachowane.

## 3. Zmiany Domain

- Dodano osobny `UsageLocationStatus` z dokładnie `ACTIVE` i `INACTIVE`.
- `UsageLocation.status` korzysta z `UsageLocationStatus`.
- Domyślny status nowej lokalizacji to `UsageLocationStatus.ACTIVE`.
- Dodano niezmienne przejścia `deactivate()` i `reactivate()`, zwracające nowy
  obiekt odpowiednio ze statusem `INACTIVE` i `ACTIVE`.
- Nie użyto `ProductUsageStatus` dla lokalizacji.
- Nie dodano historii ani innych statusów.

## 4. Zmiany ORM

`UsageLocationModel.status` odwzorowano przez istniejący helper
`enum_column_type` jako `VARCHAR + CHECK`, z typem domenowym
`UsageLocationStatus`. Nie dodano DB defaultu i nie zmieniono innych modeli w
ramach tego Tasku.

## 5. Rewizja Alembic

- Revision ID: `d2b4f6a8c190`.
- `down_revision`: `c41d8e2f7a90`.
- Końcowa liczba rewizji: 4.
- Jest to dokładnie jedna nowa rewizja TASK-009-ALIGN.

## 6. Review migracji

Migrację przeczytano przed pierwszym `upgrade head`. Upgrade tworzy wyłącznie
CHECK `usage_location_status_values` na `usage_locations`; downgrade usuwa
wyłącznie ten CHECK. Migracja nie zawiera zmian innych tabel, kolumn, enumów,
indeksów, FK ani wcześniejszych constraintów. Nie zastosowano false positives
dotyczących innych enumowych CHECK-ów.

## 7. Constraint `USAGE_LOCATION.status`

PostgreSQL zawiera:

```text
usage_location_status_values
status IN ('ACTIVE', 'INACTIVE')
```

Constraint jest zgodny z metadanymi ORM. Brak DB defaultu.

## 8. Ochrona wcześniejszych constraints

Po finalnym re-upgrade bezpośrednia inspekcja PostgreSQL potwierdziła:

- 18/18 wcześniejszych enumowych CHECK-ów,
- nowy, dziewiętnasty enumowy CHECK `usage_location_status_values`,
- wszystkie 3 quantity CHECK-i TASK-008,
- brak zmian constraints TASK-006.

## 9. Testy Domain

Potwierdzono testami:

- nowa `UsageLocation` ma `ACTIVE`,
- `ACTIVE -> INACTIVE`,
- `INACTIVE -> ACTIVE`,
- enum zawiera tylko dwa zatwierdzone statusy,
- `UsageLocationStatus is not ProductUsageStatus`.

Testy jednostkowe: **57 passed**.

## 10. Testy PostgreSQL

Na realnym PostgreSQL potwierdzono:

- akceptację `ACTIVE`,
- akceptację `INACTIVE`,
- odrzucenie `ARCHIVED` przez `usage_location_status_values`,
- brak regresji wcześniejszych testów integralności.

Test korzysta z transakcji wycofywanej i nie pozostawia danych.

## 11. Pełna regresja

Uruchomiono:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik końcowy: **63 passed**, bez `SAWarning`.

## 12. Upgrade / downgrade / re-upgrade

Zweryfikowana sekwencja:

```text
c41d8e2f7a90
  -> upgrade
d2b4f6a8c190
  -> downgrade -1
c41d8e2f7a90
  -> re-upgrade
d2b4f6a8c190
```

Po upgrade, downgrade i re-upgrade potwierdzono dokładnie 9 tabel
aplikacyjnych.

## 13. Alembic current/check

- Finalne `alembic current`: `d2b4f6a8c190 (head)`.
- `alembic check`: `No new upgrade operations detected.`
- Rzeczywisty drift ORM ↔ PostgreSQL: brak.

## 14. Finalny stan PostgreSQL

- Alembic revisions: 4.
- Current/head: `d2b4f6a8c190`.
- Tabele aplikacyjne: 9.
- Rekordy we wszystkich 9 tabelach aplikacyjnych: 0.
- `usage_locations.status`: `VARCHAR`, `NOT NULL`, CHECK wyłącznie
  `ACTIVE`/`INACTIVE`.

## 15. Git/bezpieczeństwo

- Nie wykonano commita ani operacji destrukcyjnych Git.
- Nie cofnięto ani nie nadpisano istniejących zmian użytkownika.
- Nie dodano bibliotek.
- Nie utworzono tabel, triggerów, historii, audytu ani danych testowych.
- Nie rozpoczęto TASK-010.

## 16. Odstępstwa

Brak.

## 17. Problemy/ryzyka

Brak otwartych blockerów. Repozytorium pozostaje roboczo nieczyste z powodu
zmian bieżącego Tasku oraz zachowanych zmian i plików wcześniejszych Tasków.

## 18. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE WZNAWIAM TASK-009.
NIE ROZPOCZYNAM TASK-010.
