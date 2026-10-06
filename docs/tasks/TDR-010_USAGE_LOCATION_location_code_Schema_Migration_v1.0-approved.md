# TDR-010 — USAGE_LOCATION location_code — schema i migracja

**Projekt:** MSDS Manager  
**Dokument:** TDR-010  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-05  
**Podstawa biznesowa:** BDR-010 v1.0-approved  
**Podstawa Core:** CORE-001 v1.4-approved  

## 1. Cel

Wdrożyć technicznie `USAGE_LOCATION.location_code` bez utraty danych i bez zgadywania symboli legacy.

## 2. Docelowa schema

```text
usage_location.location_code VARCHAR(32)
```

Docelowo:

```text
NOT NULL
UNIQUE
```

## 3. Kanoniczna postać

Application zapisuje:

```text
trim(input).upper()
```

Format:

```text
^[A-Z0-9][A-Z0-9_-]{0,31}$
```

Baza zabezpiecza format przez CHECK.

## 4. Strategia migracji — dwa etapy

### ETAP A — foundation

Alembic:

```text
ADD COLUMN location_code VARCHAR(32) NULL
```

Następnie:

```text
CHECK:
location_code IS NULL
OR location_code spełnia format
```

Unikalność dla wartości uzupełnionych.

Nie wykonywać automatycznego backfill.

### ETAP B — hardening

Po ręcznym uzupełnieniu symboli:

```text
COUNT(NULL) = 0
duplicate count = 0
format violations = 0
```

Dopiero wtedy:

```text
ALTER location_code SET NOT NULL
```

Jeżeli preflight FAIL:

```text
STOP
```

## 5. Domain / ORM

W okresie przejściowym odczyt musi obsłużyć:

```text
location_code: str | None
```

ale `CreateUsageLocation` wymaga niepustego symbolu.

## 6. Application

Minimalnie:

```text
CreateUsageLocation
→ location_code required
→ trim
→ uppercase
→ format validation
→ controlled duplicate error
```

Read DTO zwraca:

```text
location_code
location_name
status
```

Legacy NULL nie może być zastępowany UUID.

## 7. Istniejące rekordy

Migracja A zachowuje wszystkie rekordy.

Nie wolno samodzielnie przypisywać symboli na podstawie nazwy.

Uzupełnienie symboli jest osobnym kontrolowanym krokiem użytkownika przed hardeningiem.

## 8. Historia

Nie dodajemy `location_code` do `USAGE_LOCATION_HISTORY`.

Uzasadnienie:

```text
location_id = stabilna tożsamość
location_code = stabilny symbol biznesowy
brak zwykłej edycji symbolu w MVP
```

## 9. Konsekwencja UI

Docelowy ekran:

```text
Symbol | Lokalizacja | Status | Akcja
```

Akcja:

```text
ACTIVE   → Dezaktywuj
INACTIVE → Reaktywuj
```

TDR-010 nie autoryzuje jeszcze finalnego patcha UI.

## 10. Walidacja

Wymagane:

```text
upgrade PASS
alembic current = head
alembic check = no drift
existing locations preserved
new location requires code
normalization uppercase
invalid format rejected
duplicate rejected
legacy NULL readable
no automatic backfill
lifecycle unchanged
```

## 11. STOP

STOP, jeżeli:
- potrzebna zmiana FK,
- trzeba zgadywać symbole,
- trzeba przebudować historię,
- potrzebna nowa dependency.

## 12. Status

```text
TDR-010
VERSION: 1.0-approved
STATUS: APPROVED

MIGRATION:
A — nullable foundation
B — user backfill
C — NOT NULL hardening
```
