# PATCH-008 — Bezpieczne usuwanie omyłkowych / zdublowanych wpisów

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** INTEGRATION  
**VALIDATION:** FOCUSED + INTEGRATION  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Dodać użytkownikowi bezpieczną możliwość usunięcia omyłkowo utworzonego lub zdublowanego wpisu PRODUCT/SDS.

Funkcja ma służyć wyłącznie do korekty błędów użytkownika i danych testowych.

Nie może zastępować mechanizmu historii rewizji SDS.

---

## BUSINESS RULE

Rozróżniamy dwa przypadki:

```text
A. błędny / zdublowany rekord
→ może zostać usunięty

B. poprawna historyczna rewizja SDS
→ NIE usuwać
→ pozostaje ARCHIVED
```

Usuwanie ma być:

```text
jawne
świadome
potwierdzane
bez automatycznego kasowania plików z dysku
```

---

## MVP SCOPE

Dodaj możliwość usunięcia:

```text
PRODUCT
wraz z jego rekordami zależnymi w bazie
```

tylko wtedy, gdy użytkownik jawnie potwierdzi operację.

Usunięcie PRODUCT może objąć zależności należące wyłącznie do tego produktu, m.in.:

```text
SDS documents
Safety Profile
SDS Components
Product Usage Locations
Product History
BHP Decisions
Decision Evidence records
```

Dokładny zakres zależności ustal na podstawie istniejącego modelu.

Nie usuwaj plików źródłowych SDS ani plików dowodów BHP z filesystemu.

---

## SAFETY RULES

### 1. Confirmation

Na ekranie `Produkty`, w kontekście wybranego produktu, dodaj akcję:

```text
Usuń produkt
```

Po jej wybraniu pokaż jednoznaczne ostrzeżenie zawierające minimum:

```text
nazwa produktu
producent
kod producenta
liczba SDS
liczba miejsc stosowania
liczba decyzji BHP
```

Użytkownik musi wykonać jawne potwierdzenie.

Preferowany prosty wzorzec:

```text
[ ] Potwierdzam usunięcie tego produktu
[ Usuń produkt ]
```

lub równoważne rozwiązanie zgodne z obecnym Streamlit UI.

### 2. No filesystem delete

Operacja usuwa tylko rekordy bazy.

Nie:

```text
delete PDF SDS
delete MSG/PDF/JPG/PNG evidence
move files
rename files
```

### 3. Historical revision protection

Nie dodawaj funkcji:

```text
Usuń pojedynczą rewizję SDS
```

w PATCH-008.

Poprawne stare rewizje pozostają `ARCHIVED`.

### 4. No automatic duplicate detection

Nie wykrywaj automatycznie duplikatów.

Nie implementuj merge.

Użytkownik sam wybiera rekord do usunięcia.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany kod:
  - PRODUCT details UI,
  - repository / persistence dla PRODUCT,
  - zależności PRODUCT,
  - transaction handling,
  - existing history tables,
- focused/integration tests.

Nie wykonuj repo-wide discovery.

Nie czytaj ponownie całego CORE/BDR/TDR/Sprintów bez konkretnej potrzeby.

---

## DO

### 1. Dodaj use case

Dodaj use case typu:

```text
DeleteProduct
```

lub wykorzystaj istniejący mechanizm, jeśli już istnieje.

Wejście:

```text
product_id
```

### 2. Usuń zależności bezpiecznie

Usuń zależne rekordy w poprawnej kolejności child → parent albo użyj istniejących mechanizmów repozytorium/relacji, jeśli są jawnie zdefiniowane.

Operacja ma być atomowa w jednej transakcji.

### 3. Zachowaj filesystem

Po usunięciu PRODUCT:

```text
DB record absent
source SDS files still present
BHP evidence files still present
```

### 4. Dodaj UI

Na ekranie `Produkty`, dla wybranego produktu:

```text
Usuń produkt
```

z wyraźnym potwierdzeniem.

Nie umieszczaj akcji w sposób łatwy do przypadkowego kliknięcia.

### 5. Obsłuż brak rekordu

Jeżeli `product_id` nie istnieje:

```text
controlled error / not found
```

Bez częściowego delete.

---

## DO NOT

Nie:

- usuwaj pojedynczych rewizji SDS,
- usuwaj plików z filesystemu,
- dodawaj automatycznego wykrywania duplikatów,
- dodawaj merge PRODUCT,
- zmieniaj lifecycle CURRENT/ARCHIVED,
- rozwijaj parsera,
- zmieniaj BHP workflow,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- przebudowuj całego UI,
- dodawaj soft-delete, jeśli obecny model go nie posiada,
- twórz nowego systemu trash/archive,
- rozpoczynaj kolejnego PATCH-a.

Jeżeli bezpieczne usunięcie wymaga zmiany schema:

```text
STOP / BLOCKED
```

---

## EXPECTED CHANGE SURFACE

Przewidywany zakres:

```text
application/use_case DeleteProduct
repository/persistence
presentation/streamlit — akcja + confirmation
focused unit tests
focused PostgreSQL integration
PATCH-008_REPORT.md
```

Bez zmian:

```text
schema
migrations
dependencies
parser
PDF reader
BHP lifecycle
SDS lifecycle
supervisory read model
```

---

## VALIDATION

### A. Delete simple product

Przygotuj:

```text
PRODUCT P1
+ CURRENT SDS
```

Usuń P1.

Oczekiwane:

```text
PRODUCT absent
SDS DB records absent
source PDF still exists
```

### B. Delete product with usage relations

Przygotuj:

```text
PRODUCT
+ 2 usage locations
+ peak/monthly values
```

Po delete:

```text
product usage relations absent
usage location dictionary records preserved
```

Nie usuwaj `USAGE_LOCATION`, jeżeli może być używana przez inne produkty.

### C. Delete product with BHP decision

Przygotuj:

```text
PRODUCT
+ SDS
+ BHP decision
+ evidence DB record
```

Po delete:

```text
product-specific DB relations absent
evidence source file still exists
```

### D. Shared manufacturer

Jeżeli manufacturer jest używany przez inne produkty:

```text
manufacturer MUST remain
```

Nie usuwaj producenta automatycznie.

### E. Non-existing product

```text
unknown product_id
→ controlled fail
→ zero changes
```

### F. Transaction integrity

W przypadku błędu pośredniego:

```text
ROLLBACK
```

Brak częściowego usunięcia.

### G. UI focused test

Potwierdź:

```text
delete action only for selected product
explicit confirmation required
no delete without confirmation
```

---

## ACCEPTANCE CRITERIA

PATCH-008 = DONE, gdy:

1. użytkownik może usunąć jawnie wybrany omyłkowy PRODUCT,
2. operacja wymaga potwierdzenia,
3. zależne rekordy produktu są usuwane poprawnie,
4. wspólne słowniki/USAGE_LOCATION nie są przypadkowo usuwane,
5. manufacturer współdzielony przez inne produkty zostaje zachowany,
6. pliki SDS i evidence pozostają na dysku,
7. brak możliwości usuwania pojedynczej historycznej rewizji SDS,
8. delete jest atomowy,
9. brak zmian schema/migrations/dependencies,
10. focused + PostgreSQL integration tests PASS.

---

## PHYSICAL RE-TEST

Po wykonaniu PATCH-008 użytkownik utworzy lub wybierze jawnie omyłkowy rekord testowy i sprawdzi:

```text
Produkty
→ wybierz błędny produkt
→ Usuń produkt
→ potwierdzenie
→ produkt znika z rejestru
→ pozostałe właściwe produkty pozostają
→ plik PDF nadal istnieje w katalogu
```

Nie testuj funkcji na referencyjnym IDROLIN ani na właściwym produkcie produkcyjnym.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. usunięcie PRODUCT wymaga zmiany schema,
2. zależności nie pozwalają na bezpieczne atomowe usunięcie,
3. istnieje ryzyko usunięcia wspólnych danych innych produktów,
4. implementacja wymaga zmiany lifecycle historii SDS,
5. konieczne byłoby usuwanie plików z filesystemu.

Nie rozszerzaj scope.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-008_REPORT.md
```

Format:

```text
# PATCH-008 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

DELETE BEHAVIOR:
- explicit confirmation: YES / NO
- product deleted: YES / NO
- dependent DB records deleted: YES / NO
- shared usage locations preserved: YES / NO
- shared manufacturer preserved: YES / NO
- SDS source files preserved: YES / NO
- BHP evidence files preserved: YES / NO
- single historical SDS delete added: NO / YES
- transaction rollback verified: YES / NO

VALIDATION:
- focused unit tests: ...
- focused PostgreSQL integration: ...
- UI focused test: ...

CHANGES OUTSIDE SCOPE:
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- filesystem delete: NONE
- merge/deduplication: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO PATCH-A.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-008.
```
