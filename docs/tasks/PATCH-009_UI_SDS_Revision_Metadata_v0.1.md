# PATCH-009 — Doprecyzowanie metadanych rewizji SDS w UI

**Projekt:** MSDS Manager  
**Typ:** PATCH  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-09-30  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
PATCH
```

---

## GOAL

Doprecyzować sposób prezentacji daty i numeru rewizji SDS w istniejącym UI bez zmiany Core, schema ani lifecycle SDS.

Przyjęta semantyka użytkowa:

```text
issue_date
→ "Data wydania / rewizji SDS"

revision
→ "Rewizja SDS"
→ pole opcjonalne
```

Producent SDS może:

```text
A. podać datę + numer rewizji
albo
B. podać tylko datę wydania / rewizji
```

Brak numeru rewizji nie jest błędem i nie blokuje rejestracji SDS.

---

## AUTHORITATIVE CONTEXT

Obowiązują:

1. `CORE-001_MSDS_Manager_v1.2-approved`
2. `SPRINT-006_UI_MVP_v1.0-approved`
3. `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED`
4. `BACKLOG-001_MSDS_Manager_Post_CHECKPOINT-006`
   - `UI-12 — Data wystawienia SDS`
   - `UI-13 — Rewizja CURRENT SDS w tabeli Produkty`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
6. root `AGENTS.md`

Nie wykonuj szerszego przeglądu repo bez potrzeby.

---

## KNOWN STARTING POINTS

Minimalnie zlokalizuj istniejące miejsca odpowiedzialne za:

```text
Streamlit:
- formularz pierwszego SDS
- formularz nowej rewizji SDS
- tabela Produkty
- szczegóły wybranego produktu

Application/read model:
- dane CURRENT SDS prezentowane w tabeli Produkty
```

Jeżeli `revision` CURRENT SDS nie jest obecnie dostępne w read modelu tabeli Produktów, rozszerz read model minimalnie tylko o tę informację.

---

## EXPECTED CHANGE SURFACE

Oczekiwane obszary zmian:

```text
app/presentation/streamlit/
app/application/            # tylko jeśli read model wymaga revision
tests/
```

Nie oczekuje się zmian w:

```text
app/domain/
app/infrastructure/db/schema
migrations/
parserze SDS
```

---

## DO

### 1. Zmiana etykiety daty SDS

W miejscach UI, w których użytkownik wprowadza lub ogląda `issue_date` SDS, użyj etykiety:

```text
Data wydania / rewizji SDS
```

Nie zmieniaj nazwy pola technicznego:

```text
issue_date
```

Nie zmieniaj semantyki danych.

---

### 2. Zachowanie `revision` jako osobnego pola

Pole:

```text
revision
```

pozostaje osobnym polem opcjonalnym.

Użytkownik może zapisać:

```text
issue_date = wartość
revision = NULL
```

bez błędu.

Nie wprowadzaj obowiązku podawania numeru rewizji.

---

### 3. Główna tabela `Produkty`

Dla CURRENT SDS dodaj w głównej tabeli Produktów kolumnę:

```text
Rewizja SDS
```

Wartość pochodzi z:

```text
CURRENT SDS.revision
```

Jeżeli `revision` jest puste / NULL, prezentuj neutralnie:

```text
—
```

lub równoważny pusty stan zgodny z istniejącym UI.

Nie pokazuj technicznego UUID SDS.

---

### 4. CURRENT SDS only

Kolumna `Rewizja SDS` w tabeli `Produkty` ma pokazywać wyłącznie rewizję:

```text
CURRENT SDS
```

Nie agreguj rewizji historycznych i nie pokazuj listy ARCHIVED SDS w tej tabeli.

---

### 5. Brak automatycznej interpretacji

Nie implementuj logiki typu:

```text
brak revision
→ utwórz revision z daty
```

Nie generuj numeru rewizji automatycznie.

Nie porównuj numerów rewizji w celu ustalania CURRENT.

Lifecycle SDS pozostaje bez zmian.

---

## DO NOT

Nie:

- zmieniaj schema,
- twórz migracji Alembic,
- zmieniaj Core,
- zmieniaj lifecycle SDS,
- zmieniaj reguły CURRENT / ARCHIVED,
- zmieniaj parsera SDS,
- dodawaj obowiązkowego numeru rewizji,
- twórz automatycznego numerowania rewizji,
- twórz dedykowanego modułu historii SDS,
- implementuj DOC-01,
- implementuj UI-11,
- refaktoruj niezwiązanych obszarów.

---

## VALIDATION

**LEVEL 1 — PATCH**

Minimum:

```text
1. Formularz pierwszego SDS pokazuje:
   "Data wydania / rewizji SDS"

2. Formularz nowej rewizji SDS pokazuje:
   "Data wydania / rewizji SDS"

3. revision pozostaje opcjonalne

4. zapis SDS z:
   issue_date != NULL
   revision = NULL
   → PASS

5. tabela Produkty pokazuje kolumnę:
   "Rewizja SDS"

6. tabela Produkty pokazuje revision CURRENT SDS

7. brak revision:
   → neutralny pusty stan / "—"

8. ARCHIVED SDS nie wpływa na wartość kolumny CURRENT

9. UUID SDS nie pojawia się w normalnym widoku
```

Uruchom focused tests dla zmienionego UI/read modelu.

Nie uruchamiaj pełnej regresji tylko z powodu tego PATCH-a.

---

## ACCEPTANCE CONDITIONS

PATCH = DONE, jeżeli:

```text
UI label:
Data wydania / rewizji SDS

revision:
osobne
opcjonalne
bez automatycznego generowania

Produkty:
pokazuje revision CURRENT SDS

schema:
NO CHANGE

migration:
NONE

Core:
NO CHANGE

SDS lifecycle:
NO CHANGE
```

---

## STOP CONDITIONS

Zatrzymaj PATCH jako `BLOCKED`, jeżeli:

1. pokazanie `revision` CURRENT SDS wymaga zmiany schema,
2. istniejący read model nie pozwala jednoznacznie ustalić CURRENT SDS bez zmiany lifecycle,
3. implementacja wymaga zmiany Core,
4. poprawna realizacja wymaga szerszego refaktoru poza UI/read model.

Nie wykonuj opportunistic work.

---

## REPORT

**SHORT REPORT**

Raport ma zawierać:

```text
STATUS: DONE / BLOCKED

CHANGED:
- UI
- read model, jeśli potrzebny
- tests

VALIDATION:
- focused tests
- UI/AppTest result

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- parser change: NO
- lifecycle change: NO

DEVIATIONS:
- NONE albo lista

NEXT:
- READY / BLOCKED
```

---

## AUTHORIZATION

```text
PATCH-009
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Wykonanie wymaga jawnego polecenia Architekta Operacyjnego:

```text
Wykonaj PATCH-009
```
