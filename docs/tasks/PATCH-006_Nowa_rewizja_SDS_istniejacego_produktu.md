# PATCH-006 — Nowa rewizja SDS istniejącego produktu

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** INTEGRATION  
**VALIDATION:** FOCUSED + INTEGRATION  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Dodać jawną funkcję użytkową:

```text
Dodaj nową rewizję SDS
```

dla **już istniejącego PRODUCT**.

Nowa rewizja ma być przypisywana do produktu wskazanego przez użytkownika, a nie rozpoznawanego automatycznie przez parser.

Główna zasada:

```text
PRODUCT = trwały obiekt biznesowy
SDS = kolejne rewizje dokumentu przypisanego do PRODUCT
```

---

## BUSINESS WORKFLOW

Docelowy przebieg:

```text
Produkty
→ wybierz istniejący PRODUCT
→ Dodaj nową rewizję SDS
→ wybierz PDF
→ opcjonalny odczyt danych
→ użytkownik potwierdza rewizję / datę
→ Zapisz nową rewizję
```

Efekt:

```text
PRODUCT
product_id = BEZ ZMIAN

poprzedni SDS CURRENT
→ ARCHIVED

nowy SDS
→ CURRENT

PRODUCT
→ PENDING_APPROVAL

miejsca stosowania
→ BEZ ZMIAN

peak quantity / monthly consumption
→ BEZ ZMIAN

poprzednia decyzja BHP
→ pozostaje historią dla poprzedniego SDS
→ NIE może zatwierdzać nowego CURRENT SDS
```

Nowy CURRENT SDS wymaga nowej decyzji BHP zgodnie z istniejącym lifecycle.

---

## CRITICAL RULE

W tym workflow **nie wolno tworzyć nowego PRODUCT na podstawie danych parsera**.

To użytkownik jawnie wskazuje istniejący produkt.

Przykład:

```text
PRODUCT: XBRAKE CLEANER
product_id: istniejące ID

nowy PDF:
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf

→ nowy SDS dla tego samego PRODUCT
→ NIE nowy PRODUCT
```

Parser może pomóc odczytać dane dokumentu, ale nie decyduje o tożsamości produktu.

---

## MVP SCOPE

Dla nowej rewizji wymagane jest minimum potrzebne do zapisania SDS zgodnie z istniejącym kontraktem.

Preferowany UX:

```text
Wybrany produkt:
- nazwa
- producent
- kod produktu

Nowa rewizja SDS:
- plik PDF
- rewizja
- data SDS / data wydania, jeśli wymagana
- opcjonalnie dane odczytane przez istniejący parser
```

Nie wymagaj ponownego ręcznego wpisywania:

```text
product_name
manufacturer_name
manufacturer_product_code
```

jeżeli produkt został już jawnie wybrany.

Tożsamość produktu bierze się z `product_id`.

---

## CHEMISTRY DATA

Zgodnie z PATCH-005:

```text
SAFETY_PROFILE
SDS_COMPONENTS
```

są opcjonalne w MVP i nie mogą blokować dodania nowej rewizji.

Jeżeli parser odczyta dane poprawnie:

```text
→ można je zapisać
```

Jeżeli parser zwróci dane niepełne:

```text
→ pomiń niepełne komponenty
→ nie blokuj rewizji
```

Nie rozwijaj parsera w PATCH-006.

---

## FILE RULES

Zachowaj istniejące zasady:

```text
aplikacja referencjonuje plik w SDS_ROOT_PATH
nie kopiuje
nie przenosi
nie nadpisuje
nie usuwa pliku PDF
```

Nowy SDS ma wskazywać właściwy plik źródłowy.

Poprzedni plik pozostaje dostępny jako historyczny SDS.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany kod:
  - PRODUCT details / Streamlit,
  - SDS acceptance,
  - SDS repository / persistence,
  - lifecycle CURRENT / ARCHIVED,
  - product status transition,
  - BHP lookup dla CURRENT SDS,
- bezpośrednio powiązane focused/integration tests.

Jeżeli istnieje już use case umożliwiający dodanie SDS do istniejącego produktu, **reuse first**.

Nie twórz równoległej logiki, jeżeli istniejąca może zostać użyta po małym rozszerzeniu.

Nie czytaj ponownie całego CORE/BDR/TDR/Sprintów bez konkretnej potrzeby.

---

## KNOWN STARTING POINT

Obecny ekran `Produkty` pozwala wybrać istniejący produkt i pokazuje jego szczegóły.

Brakuje jawnej akcji:

```text
Dodaj nową rewizję SDS
```

Obecny `Dodaj SDS` jest używany głównie do utworzenia nowego produktu na podstawie pierwszego SDS.

PATCH-006 ma rozdzielić te dwa intencjonalnie różne workflow:

```text
Dodaj SDS
→ nowy PRODUCT + pierwszy CURRENT SDS

Dodaj nową rewizję SDS
→ istniejący PRODUCT + nowy CURRENT SDS
```

---

## DO

### 1. Dodaj akcję w kontekście istniejącego produktu

Na ekranie `Produkty`, dla wybranego produktu, dodaj czytelną akcję:

```text
Dodaj nową rewizję SDS
```

Może być przyciskiem lub rozwijanym panelem zgodnym z aktualnym prostym UI.

Nie przebudowuj całego ekranu `Produkty`.

### 2. Wybór pliku

Po uruchomieniu funkcji użytkownik wybiera PDF z istniejącego `SDS_ROOT_PATH`.

Zachowaj istniejący mechanizm listowania plików.

### 3. Odczyt pomocniczy

Można użyć istniejącego PDF readera/parsera do podpowiedzi:

```text
revision
issue_date
opcjonalne dane chemiczne
```

Nie pozwól parserowi zmienić tożsamości produktu.

Jeżeli parser zwróci:

```text
product_name
manufacturer_name
manufacturer_product_code
```

nie używaj tych pól do tworzenia nowego produktu ani automatycznego przełączania produktu.

### 4. Zapis rewizji

Zapis musi być atomowy zgodnie z istniejącym podejściem transakcyjnym.

Po sukcesie:

```text
old CURRENT → ARCHIVED
new SDS → CURRENT
PRODUCT.id → unchanged
PRODUCT.status → PENDING_APPROVAL
```

### 5. Zachowaj dane operacyjne produktu

Po nowej rewizji mają pozostać bez zmian:

```text
PRODUCT_USAGE_LOCATION
peak_quantity
peak_unit
monthly_consumption
monthly_unit
administrative product data
```

Nie kopiuj ich do nowego SDS — one nadal należą do PRODUCT.

### 6. BHP lifecycle

Nowy CURRENT SDS nie dziedziczy zatwierdzenia poprzedniej rewizji.

Po zapisie:

```text
PRODUCT = PENDING_APPROVAL
```

Poprzednia decyzja i dowód pozostają historią poprzedniego SDS.

Nie usuwaj poprzednich decyzji ani evidence.

Nie twórz automatycznie nowej decyzji BHP.

### 7. Historia

Jeżeli istniejący lifecycle/history mechanism zapisuje snapshot przy tej zmianie, użyj go.

Nie twórz nowego mechanizmu historii.

---

## DO NOT

Nie:

- twórz nowego PRODUCT dla nowej rewizji,
- auto-matchuj produktu na podstawie nazwy/kodu parsera,
- zmieniaj `product_id`,
- kopiuj miejsc stosowania do SDS,
- usuwaj starego SDS,
- usuwaj starego pliku,
- dziedzicz decyzji BHP,
- rozwijaj parsera,
- buduj alias dictionary,
- dodawaj OCR,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- przebudowuj całego UI,
- dodawaj funkcji edycji produktu,
- dodawaj funkcji delete produktu/SDS,
- rozpoczynaj kolejnego PATCH-a.

Edycja produktu i bezpieczne usuwanie są osobnymi późniejszymi zmianami.

---

## EXPECTED CHANGE SURFACE

Przewidywany zakres:

```text
presentation/streamlit — mała akcja/formularz rewizji
application/use_case — reuse lub małe rozszerzenie
repository/persistence — tylko jeśli istniejący port nie obsługuje wskazanego product_id
focused tests
integration test lifecycle
PATCH-006_REPORT.md
```

Preferuj minimalną zmianę.

---

## VALIDATION

### A. Existing PRODUCT + new revision

Przygotuj scenariusz:

```text
PRODUCT P1
SDS S1 = CURRENT
```

Dodaj S2 jako nową rewizję do P1.

Oczekiwane:

```text
P1.id == bez zmian
S1.status == ARCHIVED
S2.status == CURRENT
P1.status == PENDING_APPROVAL
```

### B. No duplicate PRODUCT

Po dodaniu rewizji:

```text
PRODUCT count dla P1
→ nadal 1
```

Nie może powstać nowy manufacturer tylko dlatego, że parser inaczej odczytał producenta.

### C. Usage preservation

Przed rewizją:

```text
P1 → Location A → peak 25 l
P1 → Location B → peak 300 l
```

Po rewizji relacje i ilości muszą być identyczne.

### D. BHP reset

Jeżeli S1 miał zatwierdzoną decyzję:

```text
S1 → APPROVED
P1 → ACTIVE
```

po dodaniu S2:

```text
P1 → PENDING_APPROVAL
S2 → brak decyzji BHP
stara decyzja/evidence → zachowane
```

### E. Optional chemistry

Nowa rewizja musi zostać zapisana również gdy:

```text
Safety Profile = pusty / NO_DATA
components = brak / niepełne
```

zgodnie z PATCH-005.

### F. UI focused test

Potwierdź, że akcja:

```text
Dodaj nową rewizję SDS
```

jest dostępna wyłącznie w kontekście wybranego istniejącego produktu i przekazuje jego `product_id`.

### G. Validation scope

Ponieważ PATCH dotyka kilku warstw i trwałych danych:

```text
focused unit tests
+
focused PostgreSQL integration test
```

Nie uruchamiaj pełnego repo-wide pytest, chyba że pojawi się konkretny powód.

Nie uruchamiaj migracji, jeśli schema się nie zmienia.

---

## ACCEPTANCE CRITERIA

PATCH-006 = DONE, gdy:

1. użytkownik może jawnie dodać nową rewizję do wybranego PRODUCT,
2. `product_id` pozostaje bez zmian,
3. nie powstaje duplikat PRODUCT,
4. poprzedni CURRENT SDS staje się ARCHIVED,
5. nowy SDS staje się CURRENT,
6. PRODUCT przechodzi do PENDING_APPROVAL,
7. miejsca i ilości pozostają bez zmian,
8. poprzednia decyzja BHP nie zatwierdza nowego SDS,
9. dane chemiczne pozostają opcjonalne,
10. brak zmian schema/migrations/dependencies,
11. focused + integration tests PASS.

---

## PHYSICAL RE-TEST

Po wykonaniu PATCH-006 użytkownik wykona test na rzeczywistym produkcie z co najmniej dwiema rewizjami SDS.

Sprawdzimy fizycznie:

```text
1. PRODUCT istnieje przed zmianą
2. Dodaj nową rewizję SDS
3. wskaż nowy PDF
4. Zapisz
5. sprawdź ten sam PRODUCT w Produkty
6. sprawdź CURRENT SDS
7. sprawdź status PENDING_APPROVAL
8. sprawdź miejsca i ilości
9. sprawdź Decyzja BHP
```

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. istniejący model nie pozwala dodać SDS do istniejącego PRODUCT bez zmiany schema,
2. lifecycle CURRENT/ARCHIVED jest sprzeczny z wymaganiem i wymaga decyzji architektonicznej,
3. BHP decision lifecycle wymaga nowej decyzji biznesowej,
4. implementacja wymaga automatycznego matchowania produktu,
5. konieczna byłaby przebudowa parsera lub UI poza opisanym zakresem.

Nie zgaduj i nie rozszerzaj scope.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-006_REPORT.md
```

Format:

```text
# PATCH-006 REPORT

STATUS:
DONE / BLOCKED

REUSED EXISTING LOGIC:
- ...

CHANGED:
- ...

LIFECYCLE RESULT:
- product_id unchanged: YES / NO
- old SDS archived: YES / NO
- new SDS current: YES / NO
- product pending approval: YES / NO
- usage relations preserved: YES / NO
- previous BHP preserved as history: YES / NO
- previous BHP inherited by new SDS: NO / YES

VALIDATION:
- focused unit tests: ...
- focused PostgreSQL integration: ...
- UI focused test: ...

CHANGES OUTSIDE SCOPE:
- schema/migrations: NONE
- dependencies: NONE
- parser algorithm: NONE
- product edit/delete: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO PATCH-A.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-006.
```
