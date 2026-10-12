# BDR-009 — Opcjonalny kod produktu producenta i kontrolowana tożsamość PRODUCT

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-009  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-10-12  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny po autoryzacji:** Codex OpenAI  

---

## 1. Cel decyzji

Celem BDR-009 jest doprecyzowanie biznesowej tożsamości `PRODUCT` w sytuacji, gdy kod produktu producenta:

```text
manufacturer_product_code
```

nie występuje w SDS, nie został jeszcze ustalony albo zostanie uzupełniony dopiero po pierwszej rejestracji produktu.

Decyzja usuwa wymaganie:

```text
manufacturer_product_code = MUST HAVE
```

i zastępuje je zasadą:

```text
manufacturer_product_code = OPTIONAL / NULL ALLOWED
```

bez osłabienia kontroli tożsamości produktu i bez automatycznego łączenia niejednoznacznych rekordów.

---

## 2. Kontekst i ujawniony problem

Dotychczasowy Core definiuje tożsamość PRODUCT przez:

```text
product_name
manufacturer_product_code
manufacturer_id
```

oraz przyjmuje regułę:

```text
nowa nazwa
lub nowy kod
lub inny producent
→ nowy PRODUCT
```

Jednocześnie starsza decyzja BDR-001 określa `manufacturer_product_code` jako kod/numer producenta lub dostawcy:

```text
jeśli występuje
```

Praktyczny bootstrap rzeczywistych SDS wykazał, że w wielu poprawnych kartach kod produktu nie występuje albo nie może zostać jednoznacznie wykryty.

BATCH-001_CX wykazał:

```text
manufacturer_product_code = NOT_FOUND
```

dla wszystkich logicznych SDS w paczce.

Brak kodu nie może zatem blokować:

```text
rozpoznania produktu
→ przygotowania CREATE/LINK
→ rejestracji PRODUCT
→ rejestracji SDS
```

jeżeli pozostałe wymagania procesu zostały spełnione.

---

## 3. Zasada nadrzędna

`manufacturer_product_code` pozostaje ważnym atrybutem identyfikacyjnym PRODUCT, jeżeli jest znany.

Nie jest jednak warunkiem istnienia PRODUCT.

Obowiązuje:

```text
kod znany
→ przechowuj wartość

kod nieznany / niewystępujący
→ NULL

NULL
≠ pusty napis
≠ wildcard
≠ wartość zastępcza
≠ informacja, że producent na pewno nie posiada kodu
```

`NULL` oznacza wyłącznie:

> **w chwili rejestracji nie ma zatwierdzonej wartości manufacturer_product_code.**

---

## 4. Niedozwolone wartości zastępcze

Brak kodu producenta nie może być uzupełniany automatycznie przez:

```text
product_name
UFI
CAS
numer SDS
nazwę pliku
wewnętrzny UUID
kolejny numer techniczny
dowolny inny identyfikator
```

System nie może tworzyć sztucznej wartości wyłącznie w celu spełnienia technicznego `NOT NULL`.

---

## 5. Utworzenie PRODUCT bez kodu

Nowy PRODUCT może zostać utworzony przy:

```text
manufacturer_product_code = NULL
```

jeżeli:

1. `product_name` jest zatwierdzona,
2. producent został jednoznacznie wskazany albo zatwierdzony przez człowieka,
3. nie występuje nierozstrzygnięty konflikt tożsamości,
4. wymagania właściwego workflow rejestracji SDS zostały spełnione.

Brak kodu sam w sobie:

```text
NIE → BLOCKED
NIE → validation error
NIE → sztuczna wartość
```

---

## 6. Późniejsze uzupełnienie kodu

Jeżeli istniejący PRODUCT posiada:

```text
manufacturer_product_code = NULL
```

i użytkownik później ustali poprawny kod, przejście:

```text
NULL → znany kod
```

jest:

```text
uzupełnieniem brakującej informacji
```

a nie zmianą tożsamości produktu.

Obowiązuje:

```text
product_id pozostaje bez zmian
istniejące SDS pozostają powiązane
istniejące decyzje BHP pozostają powiązane
istniejące miejsca stosowania pozostają powiązane
```

Operacja wymaga świadomego zatwierdzenia przez użytkownika.

---

## 7. Zmiana kodu już znanego

Jeżeli istniejący PRODUCT posiada zatwierdzony kod:

```text
manufacturer_product_code = A
```

a źródło wskazuje rzeczywiście inny kod:

```text
manufacturer_product_code = B
```

domyślna reguła pozostaje:

```text
A → B
→ nowy PRODUCT
```

Wyjątek stanowi wyłącznie kontrolowana korekta błędnie wcześniej zarejestrowanej wartości.

Korekta błędu:

```text
NIE jest zwykłą edycją administracyjną
NIE może być wykonana automatycznie przez parser/importer
musi być świadomą operacją korekty
musi pozostać audytowalna
```

Techniczny sposób audytu korekt zostanie określony w TDR / Tasku implementacyjnym.

---

## 8. Nazwa produktu i producent

BDR-009 nie znosi istniejącej reguły dotyczącej rzeczywistej zmiany nazwy produktu lub producenta.

Domyślnie:

```text
rzeczywiście nowa product_name
→ nowy PRODUCT

rzeczywiście inny manufacturer_id
→ nowy PRODUCT
```

Wyjątkiem pozostaje kontrolowana korekta błędnie zarejestrowanej wartości lub zatwierdzona normalizacja danych referencyjnych.

System nie może sam uznać, że różniące się nazwy oznaczają ten sam produkt lub tego samego producenta.

---

## 9. CREATE / LINK przy znanym kodzie

Po zatwierdzeniu danych wejściowych i producenta:

```text
product_name
manufacturer_id
manufacturer_product_code
```

mogą służyć do wyznaczenia kandydatów.

Dla znanego kodu:

```text
dokładnie 1 zgodny PRODUCT
→ LINK CANDIDATE

0 zgodnych PRODUCT
→ CREATE CANDIDATE

więcej niż 1 zgodny PRODUCT
→ HUMAN REVIEW
```

System nie może wybierać pierwszego rekordu z wielu dopasowań.

---

## 10. CREATE / LINK przy braku kodu

Jeżeli:

```text
manufacturer_product_code = NULL
```

resolver może korzystać z:

```text
zatwierdzonej product_name
+
jednoznacznie wskazanego manufacturer_id
```

Reguła:

```text
dokładnie 1 kandydat PRODUCT
→ LINK CANDIDATE
→ wymaga potwierdzenia człowieka

0 kandydatów
→ CREATE CANDIDATE

więcej niż 1 kandydat
→ HUMAN REVIEW
```

Brak kodu nie daje zgody na automatyczne połączenie produktu.

`NULL` nie może działać jako wildcard.

Podobieństwo nazw, fuzzy matching albo różnica wyłącznie w wielkości liter nie jest samodzielną podstawą automatycznego LINK.

---

## 11. Tożsamość MANUFACTURER

Rozwiązanie producenta poprzedza finalne rozstrzygnięcie tożsamości PRODUCT.

Obowiązuje:

```text
jednoznaczny manufacturer_id
→ można przejść do PRODUCT resolution

brak producenta
→ MANUFACTURER CREATE CANDIDATE

kilka możliwych rekordów
→ HUMAN REVIEW
```

Zatwierdzone Golden Decisions mogą przekształcić identyczny, wcześniej rozstrzygnięty zapis źródłowy w zatwierdzoną nazwę kanoniczną.

Nie oznacza to jednak automatycznego wyboru istniejącego `manufacturer_id`, jeżeli baza zawiera kilka możliwych rekordów.

Przykład:

```text
RAW:
CX80 POLSKA, CX80 GmbH

HUMAN-APPROVED CANONICAL:
CX80 POLSKA
```

Jeżeli baza zawiera:

```text
CX80
Cx80
```

system nadal nie może samodzielnie scalić lub wybrać tych rekordów.

---

## 12. Relacja z Evidence JSON

BDR-009 nie zmienia kontraktu `SDS-JSON-001`.

Dozwolone pozostaje:

```text
manufacturer_product_code.state = NOT_FOUND
manufacturer_product_code.value = null
```

Evidence JSON może więc przejść etap:

```text
walidacja
→ DATA MAPPING
→ CREATE / LINK / HUMAN REVIEW
```

bez sztucznego uzupełniania kodu.

Jeżeli użytkownik zna kod, może uzupełnić go ręcznie przed CREATE.

Jeżeli nie zna kodu, może kontynuować z `NULL`.

---

## 13. Relacja z pełną rejestracją SDS

BDR-009 nie zmienia zasad:

```text
SDS_ROOT_PATH
kontrolowany import PDF
CURRENT / ARCHIVED
PENDING_APPROVAL
decyzja BHP
human approval
```

Rozdziela się:

```text
Evidence JSON
→ mapowanie i identity resolution
```

od:

```text
pełna rejestracja SDS
→ PDF + Application + PostgreSQL
```

Brak kodu producenta nie blokuje żadnego z tych etapów wyłącznie z powodu braku kodu.

---

## 14. `use_description` i `use_restriction`

BDR-009 nie zmienia statusu pól:

```text
use_description
use_restriction
```

Nie są one częścią tożsamości PRODUCT.

Decyzja, czy mają być wymagane przed finalnym CREATE, należy do osobnego zakresu i nie wynika automatycznie z opcjonalności `manufacturer_product_code`.

---

## 15. SAFETY_PROFILE i dane bezpieczeństwa

BDR-009 nie zmienia zasad ekstrakcji ani zatwierdzania:

```text
SAFETY_PROFILE
SDS_COMPONENT
NO_DATA
NO
```

Brak danych bezpieczeństwa w częściowym Evidence JSON nie może zostać automatycznie zamieniony na domenowe `NO_DATA` tylko dlatego, że sekcje nie były jeszcze ekstraktowane.

To zagadnienie pozostaje osobnym elementem importera JSON → Core.

---

## 16. Audytowalność uzupełnienia i korekty tożsamości

Operacje:

```text
NULL → known manufacturer_product_code
```

oraz:

```text
kontrolowana korekta błędnej nazwy / kodu / producenta
```

muszą pozostać możliwe do odtworzenia.

BDR-009 nie narzuca konkretnej tabeli historii.

TDR / Task implementacyjny ma określić minimalny mechanizm pozwalający ustalić co najmniej:

```text
jaki atrybut zmieniono
wartość poprzednią
wartość nową
czas zmiany
```

Nie wolno wprowadzić cichego nadpisania danych tożsamości bez śladu.

---

## 17. Wpływ na bazę danych

Implementacja BDR-009 wymaga technicznego dopuszczenia:

```text
PRODUCT.manufacturer_product_code = NULL
```

Bieżący schemat PostgreSQL posiada `NOT NULL`.

Wymagana będzie osobna, kontrolowana migracja Alembic po zatwierdzeniu odpowiedniego TDR / Tasku implementacyjnego.

BDR-009 nie rozstrzyga technicznego mechanizmu:

```text
UNIQUE constraint
index
concurrency control
transaction locking
```

Mechanizm ten musi jednak zapewnić, że resolver nie dokonuje cichego wyboru pierwszego z kilku kandydatów.

---

## 18. Relacja z BDR-001

BDR-009 potwierdza zapis BDR-001, zgodnie z którym kod produktu jest danym identyfikacyjnym:

```text
jeśli występuje
```

BDR-009 doprecyzowuje i częściowo zastępuje regułę BDR-001 dotyczącą nowego kodu.

Od tej decyzji:

```text
NULL → pierwszy zatwierdzony kod
```

nie oznacza nowego PRODUCT.

Natomiast:

```text
znany kod A → rzeczywiście nowy kod B
```

nadal oznacza nowy PRODUCT, z wyjątkiem jawnej korekty błędu.

---

## 19. Relacja z CORE-001

Po zatwierdzeniu BDR-009 wymagana jest aktualizacja `CORE-001`.

Core powinien otrzymać co najmniej reguły:

```text
manufacturer_product_code jest opcjonalny

NULL oznacza brak zatwierdzonej wartości kodu

NULL → known code
= uzupełnienie tego samego PRODUCT

known code A → real known code B
= new PRODUCT

wyjątek:
controlled correction of erroneous identity data
```

Do czasu zatwierdzenia odpowiedniej rewizji Core BDR-009 nie stanowi zgody na implementację.

---

## 20. Relacja z PATCH-007

Istniejące zachowanie umożliwiające korektę pól tożsamości tego samego `product_id` należy interpretować jako:

```text
CONTROLLED CORRECTION
```

a nie ogólną zgodę na dowolną zmianę tożsamości PRODUCT.

Docelowa implementacja ma odróżniać:

```text
korektę błędnych danych
```

od:

```text
rzeczywistej zmiany produktu / kodu / producenta
```

Rzeczywista zmiana tożsamości prowadzi do nowego PRODUCT.

---

## 21. Przypadek referencyjny — ALUCYNK

Evidence JSON:

```text
product_name = ALUCYNK
manufacturer_product_code = NULL
manufacturer = CX80 POLSKA
```

Stan bazy:

```text
PRODUCT ALUCYNK = brak
MANUFACTURER exact CX80 POLSKA = brak
istnieją: CX80 / Cx80
```

Oczekiwany DRY RUN:

```text
PRODUCT
→ CREATE CANDIDATE

MANUFACTURER
→ HUMAN REVIEW / CREATE CANDIDATE

manufacturer_product_code
→ NULL
→ NIE BLOKUJE
```

Po zatwierdzeniu producenta i całego workflow produkt może zostać utworzony bez kodu.

Kod może zostać uzupełniony później bez zmiany `product_id`.

---

## 22. Poza zakresem

BDR-009 nie zatwierdza:

- implementacji mappera JSON → Application,
- implementacji resolvera,
- migracji PostgreSQL,
- automatycznego scalania MANUFACTURER,
- fuzzy matching,
- zmian `SDS-JSON-001`,
- zmian `SDS-ALIAS-001`,
- automatycznego importu do Core,
- automatycznej decyzji BHP,
- zmian CURRENT / ARCHIVED,
- zmiany wymagalności `use_description`,
- zmiany wymagalności `use_restriction`,
- rozwiązania częściowego `SAFETY_PROFILE`,
- nowego mechanizmu historii bez TDR.

---

## 23. Konsekwencje decyzji

### Pozytywne

- rzeczywiste SDS bez kodu producenta mogą być rejestrowane,
- brak danych opcjonalnych nie blokuje procesu,
- system nie generuje sztucznych identyfikatorów,
- późniejsze ustalenie kodu nie rozrywa historii istniejącego PRODUCT,
- CREATE/LINK staje się jawne i kontrolowane,
- niejednoznaczne dopasowanie pozostaje decyzją człowieka,
- możliwe jest wykorzystanie istniejącego `AcceptSds` zamiast budowania równoległego workflow.

### Ograniczenia

- przy `NULL` automatyczna identyfikacja PRODUCT jest słabsza,
- możliwe są przypadki wymagające HUMAN REVIEW,
- konieczna będzie migracja schema,
- konieczne jest techniczne zaprojektowanie audytu korekt tożsamości,
- istniejące duplikaty MANUFACTURER nie są automatycznie rozwiązywane.

---

## 24. Wymagane dalsze kroki

Po zatwierdzeniu BDR-009:

```text
1. CORE-001 v1.6
   → aktualizacja reguł PRODUCT identity

2. TDR-013
   → Evidence JSON
   → DRY RUN
   → CREATE / LINK / HUMAN REVIEW
   → Application
   → PostgreSQL

3. Task implementacyjny
   → nullable manufacturer_product_code
   → Alembic migration
   → DTO / Application / Repository / UI
   → resolver + mapper
   → audyt uzupełnienia / korekty
   → testy

4. Kontrolowany test ALUCYNK
```

Każdy etap wymaga osobnej autoryzacji zgodnie z GOV-001.

---

## 25. Status decyzji

Architekt Operacyjny zatwierdził niniejszą decyzję.

```text
BDR-009
VERSION: 1.0-approved
STATUS: APPROVED
IMPLEMENTATION: NOT AUTHORIZED
```

Zatwierdzenie BDR-009 oznacza, że kolejnym wymaganym krokiem projektowym jest przygotowanie rewizji:

```text
CORE-001 v1.6
```

BDR-009 nie stanowi samodzielnej zgody na implementację, migrację schema ani zapis danych do PostgreSQL.

---

## 26. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-12 | Draft | Opcjonalny manufacturer_product_code, NULL→kod w tym samym PRODUCT, CREATE/LINK przy braku kodu, kontrolowana korekta tożsamości i wymaganie aktualizacji Core |
| 1.0-approved | 2026-10-12 | Approved | Zatwierdzono opcjonalny kod producenta, NULL→kod w tym samym PRODUCT, kontrolowane CREATE/LINK/HUMAN REVIEW oraz wymaganie aktualizacji CORE-001 |
