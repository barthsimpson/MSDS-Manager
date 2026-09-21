# PATCH-005 — Uproszczenie akceptacji SDS: chemia opcjonalna w MVP

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Przywrócić prosty cel MVP:

> MSDS Manager ma przede wszystkim zarządzać plikami SDS, ich rewizjami, produktem, miejscami stosowania, ilościami, decyzją BHP i dowodem decyzji.

Automatyczna ekstrakcja danych chemicznych jest dodatkiem pomocniczym.

Braki lub błędy w:

```text
SAFETY_PROFILE
SDS_COMPONENTS
```

nie mogą blokować rejestracji SDS.

---

## BUSINESS RULE

Obowiązująca zasada MVP:

```text
parser = pomocnik
dane chemiczne = opcjonalne
użytkownik = może je poprawić, pominąć lub zostawić puste
```

Akceptacja SDS ma zależeć wyłącznie od minimalnych danych wymaganych do identyfikacji produktu i dokumentu.

Parser nie może zmuszać użytkownika do ręcznego odtwarzania pełnej sekcji chemicznej tylko po to, aby zapisać SDS.

---

## MVP ACCEPTANCE — REQUIRED

Zachowaj jako wymagane tylko pola, które już istnieją w obecnym kontrakcie identyfikacyjnym produktu/SDS i są potrzebne do utworzenia rekordu.

Nie rozszerzaj ich.

W szczególności nie zmieniaj bez potrzeby istniejących reguł dla:

```text
product_name
manufacturer_name
manufacturer_product_code
revision / issue_date — zgodnie z aktualnym kontraktem
```

Jeżeli któreś z tych pól dziś jest opcjonalne, nie rób go wymaganym w tym PATCH-u.

---

## MVP ACCEPTANCE — OPTIONAL

Następujące obszary nie mogą blokować `Zapisz / Akceptuj`:

```text
SAFETY_PROFILE
SDS_COMPONENTS
```

Dotyczy to m.in.:

```text
brak składników
brak component_name
brak CAS
brak WE
brak REACH
brak stężenia
brak klasyfikacji składnika
brak zwrotów H
NO_DATA w Safety Profile
niepełny wynik parsera
błędnie utworzony przez parser niepełny komponent
```

Jeżeli parser utworzył niepełny komponent, aplikacja nie może wymagać jego ręcznego naprawienia przed zapisaniem SDS.

Preferowane zachowanie:

```text
niekompletny komponent z parsera
→ nie blokuje acceptance
→ nie zapisuj niepoprawnego rekordu komponentu
```

Jeżeli obecna architektura ma prostszy bezpieczny wariant:

```text
pomijaj niekompletne komponenty przy acceptance
```

jest to akceptowalne.

Nie zapisuj rekordów komponentów, które naruszają integralność danych.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany kod `AcceptSds`,
- bezpośrednio powiązane DTO/validation dla `SAFETY_PROFILE` i `SDS_COMPONENTS`,
- focused tests acceptance.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów bez konkretnej potrzeby.

Nie wykonuj repo-wide discovery.

---

## DO

### 1. Usuń blokowanie acceptance przez dane chemiczne

Znajdź walidacje powodujące błędy typu:

```text
Each accepted SDS component requires component_name.
```

i zmień je tak, aby brak/niekompletność danych chemicznych nie blokowała zapisu SDS.

### 2. Zachowaj integralność bazy

Nie zapisuj niepoprawnych rekordów `SDS_COMPONENTS`.

Jeżeli komponent jest niekompletny:

```text
→ pomiń go przy zapisie
```

albo zastosuj równoważne minimalne rozwiązanie zgodne z obecną architekturą.

Nie twórz rekordów z:

```text
component_name = NULL / pusty
```

jeżeli model na to nie pozwala.

### 3. Safety Profile

Jeżeli Safety Profile może istnieć jako pusty / NO_DATA zgodnie z aktualnym modelem, zachowaj obecny mechanizm.

Nie twórz nowych statusów i nie zmieniaj schema.

Brak pełnego Safety Profile nie może blokować SDS acceptance.

### 4. Manual fallback

Po PATCH-u użytkownik ma móc:

```text
otworzyć SDS
→ poprawić tylko podstawowe dane produktu/SDS
→ zignorować sekcję chemiczną
→ Zapisz / Akceptuj
→ PRODUCT + CURRENT SDS zapisane
```

---

## EXPECTED CHANGE SURFACE

Preferowany zakres:

```text
AcceptSds / bezpośrednia walidacja
+
focused tests
+
PATCH-005_REPORT.md
```

Bez zmian:

```text
schema
migrations
dependencies
PDF reader
language detection
parser aliases
component parser algorithm
Core lifecycle PRODUCT/SDS
BHP workflow
usage locations
supervisory view
```

---

## DO NOT

Nie:

- rozwijaj parsera,
- buduj słownika aliasów,
- naprawiaj segmentacji sekcji 3,
- dodawaj OCR,
- zmieniaj PDF readera,
- dodawaj nowych tabel,
- zmieniaj schema,
- usuwaj `SAFETY_PROFILE` ani `SDS_COMPONENTS` z modelu,
- przebudowuj UI,
- zmieniaj lifecycle rewizji,
- rozpoczynaj etapu 2 parsera,
- wykonuj repo-wide refactor.

Jeżeli uproszczenie acceptance wymaga zmiany schema:

```text
STOP / BLOCKED
```

---

## VALIDATION — LEVEL 1

Wykonaj focused tests.

### A. Minimal SDS acceptance

Scenariusz:

```text
wymagane dane produktu/SDS kompletne
SAFETY_PROFILE = pusty / NO_DATA
SDS_COMPONENTS = brak
→ PASS
```

### B. Incomplete parsed component

Scenariusz:

```text
component_name = brak
CAS / WE mogą być obecne
→ SDS acceptance PASS
→ niepoprawny komponent NIE zostaje zapisany
```

### C. Valid component

Scenariusz:

```text
kompletny komponent
→ nadal zapisuje się poprawnie
```

### D. Required product/SDS fields

Potwierdź, że istniejące wymagane dane identyfikacyjne nadal blokują zapis, jeśli ich brakuje.

### E. No broad validation

Nie uruchamiaj automatycznie:

```text
pełnego pytest
PostgreSQL integration suite
Alembic
migracji
```

Tylko focused tests związane z acceptance.

---

## ACCEPTANCE CRITERIA

PATCH-005 = DONE, gdy:

1. brak `SAFETY_PROFILE` nie blokuje SDS acceptance,
2. brak `SDS_COMPONENTS` nie blokuje SDS acceptance,
3. niepełny komponent parsera nie blokuje SDS acceptance,
4. niepełny komponent nie jest zapisywany jako błędny rekord,
5. kompletny komponent nadal może zostać zapisany,
6. wymagane podstawowe dane produktu/SDS nadal są walidowane,
7. schema/migrations/dependencies pozostają bez zmian,
8. focused tests PASS.

---

## PHYSICAL RE-TEST

Po PATCH-u użytkownik powtórzy test na:

```text
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
```

Oczekiwany przebieg:

```text
Odczytaj dane
→ parser może zwrócić niepełne dane chemiczne
→ użytkownik poprawia tylko podstawowe dane
→ Zapisz / Akceptuj
→ brak stopera z component_name
→ SDS zapisany
```

Następnie wracamy do właściwego testu rewizji:

```text
stary CURRENT → ARCHIVED
nowy SDS → CURRENT
ten sam PRODUCT
ten sam product_id
```

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-005_REPORT.md
```

Format:

```text
# PATCH-005 REPORT

STATUS:
DONE / BLOCKED

CAUSE:
- ...

CHANGED:
- ...

BEHAVIOR:
- empty Safety Profile: ALLOWED / BLOCKED
- no components: ALLOWED / BLOCKED
- incomplete component: SKIPPED / BLOCKED / SAVED
- valid component: SAVED / BROKEN
- required product/SDS fields: PRESERVED / BROKEN

VALIDATION:
- focused tests: ...

CHANGES OUTSIDE SCOPE:
- parser algorithm: NONE
- PDF reader: NONE
- schema/migrations: NONE
- dependencies: NONE
- UI: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-005.
```
