# TASK-045 — USAGE_LOCATION Legacy Code Backfill + Stanowiska UX

**Projekt:** MSDS Manager
**Task:** TASK-045
**Wersja:** 0.1
**Status:** READY / BLOCKED BY TASK-044 PRECONDITION
**Data:** 2026-10-05

## MODE

INTEGRATION

## PRECONDITION

TASK-045 wolno wykonać dopiero po zaakceptowanym TASK-044, który zastosuje na bazie operatora migrację:

b379f54c12a0 -> c7e5a82d9043

i potwierdzi:
- `usage_locations.location_code` istnieje,
- istniejące lokalizacje operatora zostały zachowane,
- legacy `location_code = NULL`,
- operator schema = head.

Jeżeli operator DB nie jest na `c7e5a82d9043` -> STOP / BLOCKED.

TASK-045 nie wykonuje migracji schema.

## GOAL

Domknąć workflow symbolu lokalizacji i poprawić ekran `Stanowiska`:

legacy NULL code -> kontrolowane nadanie symbolu przez użytkownika -> czytelna tabela -> row-specific lifecycle action

Docelowy widok:

Symbol | Lokalizacja | Status | Akcja
MZT | Magazyn Techniczny | ACTIVE | Dezaktywuj
UTR | Warsztat UTR | ACTIVE | Dezaktywuj
REG | Regeneracja | INACTIVE | Reaktywuj

UUID nie jest prezentowany jako informacja biznesowa.

## AUTHORITATIVE CONTEXT

1. BDR-010 v1.0-approved
2. CORE-001 v1.4-approved
3. TDR-010 v1.0-approved
4. TASK-043_REPORT.md
5. TASK-044_REPORT.md
6. BDR-002 v1.2-approved
7. TDR-004 v1.0-approved
8. GOV-002 v1.0-approved
9. root AGENTS.md

## DO

### 1. Controlled legacy code assignment

Dodaj osobny use case, preferowany:

`AssignLegacyUsageLocationCode`

Wejście:
- `location_id`
- `location_code`

Reguły:
- lokalizacja istnieje,
- current `location_code IS NULL`,
- input wymagany,
- trim,
- uppercase,
- format `^[A-Z0-9][A-Z0-9_-]{0,31}$`,
- unikalność.

Jeżeli rekord już posiada `location_code` -> REJECT.

To nie jest zwykła edycja symbolu, tylko kontrolowany backfill legacy.

### 2. Persistence

Aktualizacja tylko wskazanego rekordu:

UPDATE usage_locations
SET location_code = :normalized_code
WHERE location_id = :id
  AND location_code IS NULL

Bez zmian:
- location_id,
- location_name,
- status,
- historii,
- PRODUCT_USAGE_LOCATION.

Bez bulk auto-backfill.

### 3. Stanowiska — tabela biznesowa

Przebuduj widok do:

Symbol | Lokalizacja | Status | Akcja

Usuń z normalnego UI kolumnę UUID.

Dla legacy NULL pokaż `BRAK SYMBOLU`, nie UUID.

### 4. Legacy backfill UX

Dla `BRAK SYMBOLU` zapewnij jednoznaczny workflow per wiersz:

[ Symbol ] [ Uzupełnij ]

Użytkownik sam wpisuje symbol.

Nie prefilluj kodu na podstawie nazwy i nie zgaduj `MZT/UTR/REG`.

### 5. Lifecycle per row

ACTIVE -> [ Dezaktywuj ]
INACTIVE -> [ Reaktywuj ]

Akcja musi być w tym samym wierszu / jednoznacznie związana z rekordem.

Użyj istniejących use case'ów lifecycle.

### 6. New location form

Formularz:

Symbol lokalizacji
Nazwa lokalizacji
[ Dodaj lokalizację ]

Nowa lokalizacja bez symbolu -> REJECT.

### 7. Completion signal

Po uzupełnieniu wszystkich legacy kodów można pokazać:

`Brak symbolu: 0`

Nie wykonuj NOT NULL hardening w TASK-045.

## DO NOT

Nie implementuj:
- migracji schema,
- NOT NULL hardening,
- auto-generation kodu,
- kodu z nazwy,
- bulk heuristic backfill,
- zwykłej edycji nie-NULL `location_code`,
- historii `location_code`,
- nowych statusów,
- delete lokalizacji,
- hierarchii lokalizacji,
- zmian ANALYTICS.

## VALIDATION

LEVEL 2 — INTEGRATION

Potwierdź:
1. TASK-044 precondition PASS,
2. legacy NULL -> `BRAK SYMBOLU`,
3. UUID niewidoczne,
4. user może uzupełnić legacy code,
5. `mzt` -> `MZT`,
6. duplicate -> controlled error,
7. invalid format -> controlled error,
8. nie można zmienić istniejącego nie-NULL kodu,
9. ACTIVE -> Dezaktywuj,
10. INACTIVE -> Reaktywuj,
11. akcja dotyczy właściwego wiersza,
12. create wymaga kodu,
13. brak luźnych przycisków pod tabelą,
14. schema change = NO,
15. migration = NONE,
16. inne dane operatora zachowane.

## STOP CONDITIONS

STOP / BLOCKED jeżeli:
- operator schema != c7e5a82d9043,
- trzeba wykonywać migrację,
- trzeba zgadywać symbol,
- trzeba edytować istniejący nie-NULL symbol,
- potrzebna zmiana historii,
- potrzebna nowa dependency,
- wymagane zmiany Core/schema/ANALYTICS.

## REPORT

Utwórz `docs/task_reports/TASK-045_REPORT.md`.

Raport:
- STATUS,
- PRECONDITION,
- IMPLEMENTED,
- VALIDATION,
- OPERATOR DATA,
- SCOPE,
- DEVIATIONS,
- NEXT.

## AUTHORIZATION

Architekt Operacyjny wydał polecenie:

`Wykonaj TASK-045.`

Jednak wykonanie jest warunkowe.

Jeżeli TASK-044 nie został zakończony i zaakceptowany:

`TASK-045 = BLOCKED`

Najpierw należy wykonać i zaakceptować TASK-044.
