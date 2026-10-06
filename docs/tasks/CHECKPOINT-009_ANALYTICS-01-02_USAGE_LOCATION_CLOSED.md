# CHECKPOINT-009 — ANALYTICS-01 / ANALYTICS-02 + USAGE_LOCATION Stabilization CLOSED

**Projekt:** MSDS Manager  
**Checkpoint:** CHECKPOINT-009  
**Data:** 2026-10-06  
**Status:** ACCEPTED / CLOSED  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

## 1. Decyzja checkpointu

Zamknięty zostaje bieżący etap obejmujący:

```text
ANALYTICS-01 — Dashboard / read model
ANALYTICS-02 — Zestawienie zbiorcze
USAGE_LOCATION — biznesowy symbol lokalizacji + stabilizacja UI
```

Zakres został technicznie zweryfikowany i fizycznie zaakceptowany przez Architekta Operacyjnego.

## 2. ANALYTICS-01 / ANALYTICS-02 — stan końcowy

Zrealizowano:

```text
dynamic read model
Dashboard
KPI
wykresy
Wymaga uwagi
Podsumowanie producentów
Zestawienie zbiorcze PRODUCT × USAGE_LOCATION
lokalna nawigacja Analizy
kompaktowy toolbar filtrów
```

Obowiązująca nawigacja:

```text
Dashboard
Zestawienie zbiorcze
Raport przeglądu
```

`Raport przeglądu` pozostaje placeholderem przyszłego ANALYTICS-03.

Dashboard i Zestawienie zbiorcze otrzymały:

```text
TECHNICAL REVIEW: PASS
PHYSICAL UX REVIEW: PASS
```

Eksport nie jest obecnie implementowany.

## 3. USAGE_LOCATION — symbol biznesowy

Model został rozszerzony o:

```text
location_code
```

Docelowy stan:

```text
location_id   = techniczny UUID
location_code = biznesowy symbol użytkownika
location_name = nazwa lokalizacji
status        = ACTIVE / INACTIVE
```

Normalny UI nie prezentuje UUID jako identyfikatora biznesowego.

Ekran `Stanowiska` prezentuje:

```text
Symbol | Lokalizacja | Status | Akcja
```

Akcje lifecycle są przypisane do konkretnego wiersza:

```text
ACTIVE   → Dezaktywuj
INACTIVE → Reaktywuj
```

## 4. Migracja i hardening location_code

Sekwencja:

```text
TASK-043 — foundation/schema
TASK-044 — operator DB migration
TASK-045 — legacy backfill workflow + Stanowiska UX
TASK-046 — NOT NULL hardening
```

Końcowy stan operator DB:

```text
location_code VARCHAR(32) NOT NULL
CHECK preserved
UNIQUE preserved
Alembic head = d8f3a21c6046
```

TASK-046 potwierdził:

```text
NULL = 0
blank = 0
duplicates = 0
format violations = 0
business data preserved
```

## 5. Zasada GOV-002 po TASK-046

Dla kolejnych Tasków utrzymujemy:

```text
minimal context
minimal exploration
proportional validation
no opportunistic work
short reports
```

Przy lokalnym hardeningu schema:

```text
mocna walidacja migracji
+ minimalny końcowy smoke
```

Nie powtarzamy szerokich testów Application/UI, jeżeli te warstwy nie były zmieniane i właściwości zostały już udowodnione.

Pełny LEVEL 3 pozostaje dla acceptance/checkpoint/high-risk closure.

## 6. Elementy świadomie otwarte

Poza CHECKPOINT-009:

```text
ANALYTICS-03 — Raport przeglądu / Stan na dzień
eksport Zestawienia zbiorczego
Settings / UNIT_OF_MEASURE admin
parser Stage 2
REACH
```

## 7. Następny krok

Następny projektowany obszar:

```text
ANALYTICS-03
— Raport przeglądu / Stan na dzień
```

Backlog wskazuje przed implementacją:

```text
BDR
+ data model
+ decyzja schema
```

Kolejny artefakt:

```text
BDR-011
— ANALYTICS-03 / Raport przeglądu / Stan na dzień
```

BDR-011 powinien rozstrzygnąć co najmniej:

```text
review / snapshot identity
DRAFT / FINAL lifecycle
kto i kiedy zatwierdza
approved_at
immutability po zatwierdzeniu
semantyka "nie sprawdzono"
population PRODUCT × LOCATION
baseline MAX snapshot
unit snapshot
observed quantity
difference
obsługa lokalizacji nowych / wycofanych
relacja do historii Core
```

## 8. Status końcowy

```text
CHECKPOINT-009
STATUS: ACCEPTED / CLOSED

ANALYTICS-01: CLOSED
ANALYTICS-02: CLOSED
USAGE_LOCATION location_code stabilization: CLOSED

NEXT:
BDR-011 — ANALYTICS-03 / Raport przeglądu / Stan na dzień
```
