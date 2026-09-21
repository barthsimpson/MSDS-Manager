# PATCH-003 — SDS acceptance: language detection must not block manual acceptance

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Usunąć błędny twardy warunek akceptacji:

```text
Accepted SDS must be a valid PL document.
```

Rozpoznanie języka SDS ma być funkcją pomocniczą, a nie bramką blokującą zapis.

Po PATCH-003 użytkownik ma móc zaakceptować SDS po ręcznej weryfikacji i korekcie danych również wtedy, gdy automatyczna heurystyka nie potwierdzi języka PL.

PATCH dotyczy wyłącznie acceptance gate języka.

---

## BUSINESS RULE

Obowiązująca zasada projektu:

```text
parser = pomocnik
użytkownik = ostateczny walidator
```

Automatyzacja ma ograniczać ręczne przepisywanie danych, ale nie może odrzucać poprawnego SDS tylko dlatego, że parser/heurystyka:

- nie rozpoznała języka,
- nie rozpoznała layoutu,
- nie odczytała części pól.

Brak pewności językowej ma prowadzić do:

```text
WARNING + możliwość ręcznej akceptacji
```

a nie do:

```text
BLOCK / ValidationError
```

---

## CONFIRMED REAL-WORLD CASE

Rzeczywisty polski SDS został odrzucony przez aplikację jako nie-PL:

```text
WYCOFANE!!! Cyna-Pbfree-SnCu-SnCuAg-SnAgCu-SnAg rew 2.2.PL(1).pdf
```

Dokument zawiera jednoznaczne sygnały PL, m.in.:

```text
KARTA CHARAKTERYSTYKI
Data wydania
Data aktualizacji
wersja: 2.2/PL
Sekcja 1: Identyfikacja substancji/mieszaniny...
ZASTOSOWANIA ZIDENTYFIKOWANE
ZASTOSOWANIA ODRADZANE
```

Mimo to zapis kończy się błędem:

```text
Accepted SDS must be a valid PL document.
```

To jest fałszywe odrzucenie i blokuje manual fallback.

Drugi reprezentatywny przypadek PL:

```text
CX80 TIRE PROTECTOR rew. 1.2 02.10.2018.pdf
```

zawiera m.in.:

```text
Wersja 1.2/PL
SEKCJA 1: IDENTYFIKACJA...
Zastosowania zidentyfikowane
producent: CX80 Polska
```

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany kod acceptance / language validation dla SDS,
- bezpośrednio powiązane focused tests.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów ani raportów historycznych, jeśli nie pojawi się konkretna sprzeczność.

Nie wykonuj repo-wide discovery.

---

## DO

### 1. Zlokalizuj twardą walidację języka

Znajdź minimalny punkt, który prowadzi do błędu:

```text
Accepted SDS must be a valid PL document.
```

Ustal, czy walidacja znajduje się w:

- use case acceptance,
- validatorze,
- DTO/domain guard,
- presentation layer,

i zmień wyłącznie niezbędny zakres.

### 2. Usuń blokadę acceptance opartą wyłącznie na language detection

Jeżeli dokument został poprawnie otwarty i użytkownik uzupełnił wymagane pola acceptance, brak pozytywnego wyniku heurystyki PL **nie może blokować zapisu**.

Wymagane zachowanie:

```text
language check = PL
→ normalny acceptance

language check = UNKNOWN / NOT_CONFIRMED
→ acceptance nadal dozwolony
→ opcjonalny warning dla UI, jeśli istniejąca architektura umożliwia to bez rozszerzania zakresu
```

Nie implementuj nowego mechanizmu detekcji języka.

### 3. Zachowaj istniejące prawdziwe blokery

Nie usuwaj walidacji wymaganych pól acceptance.

Nadal mają blokować m.in. przypadki:

```text
brak wymaganej nazwy produktu
brak wymaganego producenta
brak innych pól zdefiniowanych jako REQUIRED w obecnym kontrakcie
```

Nie zmieniaj istniejącej polityki mandatory fields poza language gate.

### 4. Zachowaj twarde błędy techniczne

PATCH nie ma umożliwiać zapisu dokumentu, którego nie da się technicznie obsłużyć.

Nadal poprawne są blokady dla przypadków typu:

```text
plik nie istnieje
plik nie jest możliwy do otwarcia
PDF jest uszkodzony
brak możliwej do odczytu treści, jeżeli obecny pipeline wymaga jej do utworzenia formularza
```

Nie rozwiązuj w tym PATCH-u encrypted/copy-protected PDF.

---

## EXPECTED CHANGE SURFACE

Preferowany zakres:

```text
1 mały fragment kodu acceptance/language validation
+
focused tests
+
PATCH-003_REPORT.md
```

Dozwolone są wyłącznie bezpośrednio powiązane pliki.

Nie zmieniaj:

```text
schema
migrations
database model
Core lifecycle PRODUCT/SDS
BHP workflow
usage locations
supervisory read model
dependencies
PDF extraction implementation
component parser
alias dictionary
UI layout
```

---

## DO NOT

Nie:

- przebudowuj parsera,
- dodawaj słownika aliasów,
- poprawiaj parsera składników,
- dodawaj OCR,
- dodawaj drugiej biblioteki PDF,
- poprawiaj encrypted PDF handling,
- refaktoryzuj SDS workflow,
- zmieniaj reguł PRODUCT / CURRENT / ARCHIVED,
- zmieniaj UI poza ewentualnym istniejącym warningiem,
- uruchamiaj repo-wide review,
- analizuj historii Git,
- rozpoczynaj kolejnego tasku.

Jeżeli usunięcie language gate wymaga większej zmiany architektonicznej:

```text
STOP / BLOCKED
```

---

## VALIDATION — LEVEL 1

Wykonaj focused validation.

### A. Regression existing acceptance

Potwierdź, że istniejące poprawne SDS nadal mogą być zaakceptowane.

### B. New regression test: language false negative

Dodaj focused test reprezentujący:

```text
language detection != confirmed PL
+
wymagane pola acceptance kompletne
→ acceptance PASS
```

Test nie musi używać pełnego realnego PDF, jeśli obecna architektura pozwala bezpiecznie przetestować warunek na poziomie use case/validatora.

### C. Required fields stay required

Potwierdź co najmniej jednym istniejącym lub focused testem:

```text
brak required field
→ nadal FAIL
```

Przykład:

```text
manufacturer_name missing
→ nadal blokada
```

### D. No broad validation

Nie uruchamiaj automatycznie:

- pełnego pytest,
- integration suite PostgreSQL,
- Alembic current/check,
- migracji,
- tymczasowych klastrów.

Uruchom wyłącznie focused tests konieczne do PATCH-003.

---

## ACCEPTANCE CRITERIA

PATCH-003 = DONE, gdy:

1. brak potwierdzenia PL nie blokuje acceptance,
2. wymagane pola nadal blokują zapis, gdy są puste,
3. poprawne istniejące scenariusze acceptance nadal przechodzą,
4. nie zmieniono parsera PDF,
5. nie zmieniono parsera składników,
6. nie zmieniono schema/migracji/dependencies,
7. focused tests PASS.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. language gate jest sprzężony z inną krytyczną regułą i nie można go usunąć lokalnie,
2. poprawka wymaga zmiany Core lifecycle,
3. poprawka wymaga zmiany schema,
4. poprawka wymaga przebudowy parsera,
5. focused regression ujawni niezależny błąd poza zakresem PATCH-a.

Nie naprawiaj problemów pobocznych.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-003_REPORT.md
```

Format:

```text
# PATCH-003 REPORT

STATUS:
DONE / BLOCKED

CAUSE:
- ...

CHANGED:
- ...

BEHAVIOR:
- language not confirmed: ACCEPTANCE ALLOWED / BLOCKED
- required fields validation: PRESERVED / BROKEN

VALIDATION:
- focused tests: ...
- existing acceptance regression: PASS / FAIL
- language false-negative regression: PASS / FAIL
- missing required field regression: PASS / FAIL

CHANGES OUTSIDE SCOPE:
- parser PDF: NONE
- component parser: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-003.
```
