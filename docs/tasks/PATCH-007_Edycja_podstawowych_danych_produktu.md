# PATCH-007 — Edycja podstawowych danych istniejącego produktu

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Dodać prostą i bezpieczną możliwość poprawienia podstawowych danych identyfikacyjnych istniejącego PRODUCT bez usuwania produktu i bez tworzenia nowego rekordu.

Cel biznesowy:

> Jeżeli użytkownik lub parser wprowadził błędną nazwę produktu, kod producenta albo producenta, użytkownik ma móc poprawić rekord istniejącego produktu.

Nie jest to funkcja merge ani deduplikacji.

---

## BUSINESS RULE

PRODUCT pozostaje tym samym obiektem:

```text
product_id = BEZ ZMIAN
```

Edycja nie może zmieniać:

```text
SDS history
CURRENT / ARCHIVED lifecycle
BHP decisions
usage locations
peak quantities
monthly consumption
product history mechanism
```

Zmiana dotyczy wyłącznie pól identyfikacyjnych wskazanych w tym PATCH-u.

---

## EDITABLE FIELDS

Dodaj możliwość edycji:

```text
product_name
manufacturer_product_code
manufacturer
```

Jeżeli producent jest osobnym rekordem `MANUFACTURER`, aktualizacja ma użyć istniejącego modelu danych i nie może prowadzić do przypadkowego duplikowania producentów.

Nie rozszerzaj zakresu na inne pola.

Dane administracyjne, które już są edytowalne, pozostają bez zmian:

```text
use_description
use_restriction
waste_type
waste_code
```

---

## UI

Na ekranie `Produkty`, w kontekście wybranego produktu, dodaj czytelną akcję:

```text
Edytuj dane produktu
```

Po uruchomieniu pokaż prosty formularz:

```text
Nazwa produktu
Kod produktu producenta
Producent

[ Zapisz zmiany ]
[ Anuluj ]
```

Nie przebudowuj całego ekranu `Produkty`.

Nie zmieniaj tabeli głównej ani layoutu poza minimalnym dodaniem tej funkcji.

---

## VALIDATION

Zachowaj istniejące zasady wymaganych pól dla identyfikacji produktu.

W szczególności nie zapisuj:

```text
pustej nazwy produktu
pustego producenta
pustego kodu, jeśli obecny kontrakt wymaga kodu
```

Nie dodawaj nowych reguł walidacyjnych.

---

## MANUFACTURER RULE

Jeżeli użytkownik zmienia producenta:

- preferuj reuse istniejącego `MANUFACTURER`, jeśli dokładnie taki producent już istnieje zgodnie z obecnym mechanizmem,
- jeżeli nie istnieje, utwórz nowego producenta zgodnie z obecną logiką,
- nie usuwaj automatycznie starego producenta tylko dlatego, że produkt został przepięty,
- nie wykonuj globalnego merge producentów.

Cleanup osieroconych producentów nie jest częścią PATCH-007.

---

## HISTORY

Jeżeli istniejący mechanizm historii PRODUCT zapisuje snapshot po istotnej zmianie, użyj go.

Nie twórz nowego mechanizmu historii.

Nie zmieniaj TDR-004.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany kod PRODUCT edit/update,
- model/repository MANUFACTURER,
- istniejący mechanizm product history,
- focused tests.

Nie wykonuj repo-wide discovery.

Nie czytaj ponownie całego CORE/BDR/TDR/Sprintów bez konkretnej potrzeby.

---

## DO

1. Dodaj use case / rozszerz istniejący use case aktualizacji PRODUCT.
2. Dodaj minimalne wsparcie repository, jeśli potrzebne.
3. Dodaj akcję UI `Edytuj dane produktu`.
4. Zachowaj `product_id`.
5. Zachowaj wszystkie powiązania produktu.
6. Użyj istniejącego mechanizmu historii, jeśli już obsługuje taki typ zmiany.
7. Dodaj focused tests.

---

## DO NOT

Nie:

- usuwaj produktu,
- twórz nowego produktu zamiast edycji,
- zmieniaj `product_id`,
- zmieniaj SDS lifecycle,
- zmieniaj CURRENT/ARCHIVED,
- resetuj BHP,
- modyfikuj miejsc stosowania,
- zmieniaj ilości,
- rozwijaj parsera,
- dodawaj merge/deduplication,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- przebudowuj całego UI,
- dodawaj PATCH-008 w tym samym zadaniu.

---

## EXPECTED CHANGE SURFACE

Preferowany zakres:

```text
application/use_case lub istniejący update product
repository/persistence tylko jeśli konieczne
presentation/streamlit — mała akcja/formularz
focused tests
PATCH-007_REPORT.md
```

Bez zmian:

```text
schema
migrations
dependencies
parser
PDF reader
BHP workflow
usage relations
supervisory read model
```

---

## VALIDATION — LEVEL 1

### A. Edit product name

```text
PRODUCT P1
product_name = A

edit → B

expected:
product_id unchanged
product_name = B
```

### B. Edit manufacturer code

```text
manufacturer_product_code = OLD
edit → NEW

expected:
product_id unchanged
code = NEW
```

### C. Edit manufacturer

```text
manufacturer = M1
edit → M2

expected:
product_id unchanged
manufacturer = M2
```

### D. Relations preserved

Po każdej edycji:

```text
SDS count/history unchanged
CURRENT SDS unchanged
BHP decisions unchanged
usage locations unchanged
peak/monthly quantities unchanged
```

### E. Required-field validation

Próba zapisania niepoprawnych pustych pól wymaganych:

```text
→ controlled validation error
```

### F. UI focused test

Akcja:

```text
Edytuj dane produktu
```

ma działać wyłącznie dla wybranego produktu i przekazywać jego istniejący `product_id`.

### G. Scope

Uruchom:

```text
focused unit tests
+
focused PostgreSQL integration tylko jeśli update repository tego wymaga
```

Nie uruchamiaj pełnego pytest bez konkretnego powodu.

---

## ACCEPTANCE CRITERIA

PATCH-007 = DONE, gdy:

1. użytkownik może poprawić nazwę produktu,
2. użytkownik może poprawić kod producenta,
3. użytkownik może zmienić producenta,
4. `product_id` pozostaje bez zmian,
5. SDS i ich historia pozostają bez zmian,
6. BHP pozostaje bez zmian,
7. miejsca i ilości pozostają bez zmian,
8. istniejące wymagane pola są nadal walidowane,
9. brak zmian schema/migrations/dependencies,
10. focused tests PASS.

---

## PHYSICAL RE-TEST

Po wykonaniu PATCH-007 użytkownik wykona prosty test:

```text
Produkty
→ wybierz XBRAKE CLEANER
→ Edytuj dane produktu
→ popraw wybrane błędne pole
→ Zapisz
→ sprawdź, że produkt pozostał tym samym rekordem
```

Nie wykonuj przy okazji cleanup ani delete.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. edycja wymaga zmiany schema,
2. aktualizacja producenta wymaga decyzji architektonicznej poza istniejącym modelem,
3. update produktu powoduje konieczność zmiany lifecycle SDS/BHP,
4. konieczna byłaby implementacja merge/deduplication.

Nie rozszerzaj zakresu.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-007_REPORT.md
```

Format:

```text
# PATCH-007 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

BEHAVIOR:
- product_name editable: YES / NO
- manufacturer_product_code editable: YES / NO
- manufacturer editable: YES / NO
- product_id unchanged: YES / NO
- SDS preserved: YES / NO
- BHP preserved: YES / NO
- usage relations preserved: YES / NO

VALIDATION:
- focused unit tests: ...
- focused PostgreSQL integration: ...
- UI focused test: ...

CHANGES OUTSIDE SCOPE:
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- delete/merge: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO PATCH-A.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-007.
```
