# CHECKPOINT-004 — Zamknięcie SPRINT-004 / R5

**Projekt:** MSDS Manager  
**Checkpoint:** CHECKPOINT-004  
**Data:** 2026-09-14  
**Status:** ACCEPTED / CLOSED  
**Zakres:** SPRINT-004 — Decyzja BHP i dowód decyzji / Roadmap R5  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  

---

## 1. Decyzja checkpointu

SPRINT-004 oraz etap Roadmapy R5 zostają uznane za zakończone.

```text
TASK-022  ACCEPTED / CLOSED
TASK-023  ACCEPTED / CLOSED
TASK-024  ACCEPTED / CLOSED
TASK-025  ACCEPTED / CLOSED

SPRINT-004  ACCEPTED / CLOSED
R5          CLOSED
```

Podstawą zamknięcia jest raport TASK-025 z pełnym E2E i wynikiem wszystkich 22 punktów DoD Sprintu 4 = PASS.

---

## 2. Stan funkcjonalny po R5

System obsługuje obecnie pionowy proces:

```text
Dodaj SDS
   ↓
minimalny automatyczny odczyt danych
   ↓
formularz + ręczna korekta / manual fallback
   ↓
Zapis
   ↓
PRODUCT + CURRENT SDS
PRODUCT = PENDING_APPROVAL
   ↓
Decyzja BHP
   ↓
wskazanie dowodu .msg/.pdf/.jpg/.jpeg/.png
   ↓
ręczne APPROVED / REJECTED
   ↓
APPROVED → PRODUCT ACTIVE
REJECTED → PRODUCT REJECTED
```

Dowód decyzji BHP jest zwykłym plikiem źródłowym, np. zapisem maila, PDF albo obrazem decyzji Specjalisty BHP.

Aplikacja przechowuje referencję do dowodu; nie interpretuje jego treści.

---

## 3. Historia decyzji BHP

Dla jednego SDS może istnieć wiele decyzji historycznych, ale maksymalnie jedna CURRENT.

```text
Decision #1 CURRENT
        ↓ korekta
Decision #1 SUPERSEDED
Decision #2 CURRENT
```

Poprzednie decyzje oraz ich evidence pozostają zachowane.

Nowy CURRENT SDS nie dziedziczy decyzji starego SDS i ustawia PRODUCT na PENDING_APPROVAL.

---

## 4. Stan techniczny

Stan potwierdzony przez TASK-025:

```text
pytest                         138 passed
SAWarning                      none
Alembic head                   e0dd7d6468bf
alembic check                  clean
business tables                12
schema drift                   none
new dependencies in TASK-025   none
```

TASK-025 nie zmienił production code, Domain, ORM ani schema.

---

## 5. Potwierdzone własności integralności

Potwierdzono na rzeczywistym PostgreSQL:

- atomową rejestrację decyzji,
- powiązanie decyzji z PRODUCT i konkretnym CURRENT SDS,
- obowiązkowy evidence,
- jeden evidence na decyzję,
- maksymalnie jedną decyzję CURRENT na SDS,
- CURRENT → SUPERSEDED przy korekcie,
- zachowanie poprzednich evidence,
- APPROVED → PRODUCT ACTIVE,
- REJECTED → PRODUCT REJECTED,
- zapis ProductHistory,
- rollback bez orphan evidence,
- rollback korekty przywracający poprzednią decyzję CURRENT.

---

## 6. Granice rozwiązania zachowane

Po R5 nadal nie istnieją i nie są wymagane:

- workflow engine,
- OCR/AI dla decyzji BHP,
- automatyczna decyzja BHP,
- kartoteka osób BHP,
- e-signature,
- wielostopniowe zatwierdzanie,
- upload/storage service,
- generic audit framework,
- event sourcing.

System pozostaje prostym narzędziem operacyjnym i audytowalnym.

---

## 7. Stan Roadmapy

```text
R0  Fundament projektu                 CLOSED
R1  Model domenowy Core                CLOSED
R2  Fundament techniczny/PostgreSQL    CLOSED
R3  Produkty i miejsca stosowania      CLOSED
R4  SDS i wersjonowanie                CLOSED
R5  Decyzje BHP                        CLOSED
R6  Migracja danych początkowych       NEXT — NOT STARTED
R7  Widok nadzorczy                    NOT STARTED
R8  Przeglądy                          NOT STARTED
R9  MVP 1.0                            NOT STARTED
```

Zgodnie z Roadmapą kolejnym etapem jest R6 — Migracja danych początkowych.

R6 obejmuje analizę i kontrolowane przeniesienie danych z `MSDS_baza.xlsx`, w tym produkty, miejsca stosowania, istniejące SDS i istniejące decyzje BHP, bez zgadywania przy brakach i konfliktach.

---

## 8. Bramka przed R6

Checkpoint nie autoryzuje rozpoczęcia R6.

Przed pierwszym Taskiem migracyjnym należy:

1. przeanalizować rzeczywistą strukturę `MSDS_baza.xlsx`,
2. zmapować kolumny źródłowe na aktualny Core,
3. sklasyfikować braki, konflikty i dane wymagające decyzji człowieka,
4. ustalić minimalną strategię migracji,
5. dopiero potem przygotować Sprint R6 i Tasks.

Nie należy rozpoczynać od pisania importera.

---

## 9. Zasada migracji

Nadrzędna zasada R6:

```text
SOURCE DATA
   ↓
MAP
   ↓
VALIDATE
   ↓
CONFLICT / MISSING?
   ├── YES → raport / decyzja człowieka
   └── NO  → import
```

Importer nie może automatycznie „naprawiać” niejednoznacznych danych.

---

## 10. Stan bezpieczeństwa checkpointu

Na checkpoint:

- pełna regresja jest zielona,
- schema jest stabilne,
- Alembic jest bez driftu,
- Sprint 4 nie pozostawia otwartych defektów blokujących,
- kolejny etap Roadmapy nie został rozpoczęty.

---

## 11. Decyzja końcowa

```text
CHECKPOINT-004
STATUS: ACCEPTED / CLOSED

SPRINT-004: CLOSED
R5: CLOSED

NEXT:
R6 — Migracja danych początkowych

R6 AUTHORIZATION:
NOT GRANTED BY THIS CHECKPOINT
```

Pierwszą czynnością R6 powinna być analiza źródłowego `MSDS_baza.xlsx`, a nie implementacja importera.
