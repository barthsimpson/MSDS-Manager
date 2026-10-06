# CORE-001 — Model Core projektu MSDS Manager

**Projekt:** MSDS Manager  
**Id dokumentu:** CORE-001  
**Wersja:** 1.5-approved  
**Status:** Approved  
**Data rewizji:** 2026-10-06  
**Dokument bazowy:** CORE-001 v1.4-approved  
**Właściciel:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel dokumentu

CORE-001 opisuje chroniony model domenowy MSDS Manager.

Dokument agreguje zatwierdzone zasady dotyczące:

- produktu chemicznego,
- producenta,
- miejsc stosowania,
- ilości szczytowych i miesięcznego zużycia,
- słownika jednostek miary,
- pomocniczych informacji odpadowych produktu,
- dokumentów SDS,
- profilu bezpieczeństwa i składników SDS,
- wersjonowania SDS,
- statusów produktu,
- decyzji BHP i dowodów,
- przeglądów fizycznego stanu `REVIEW / REVIEW_ITEM`,
- podstaw audytowalności.

CORE-001 nie zastępuje ADR, BDR ani TDR. Jego rolą jest pokazanie obowiązującego Core, którego Codex nie może zmieniać bez zatwierdzonej decyzji Architekta Operacyjnego.

---

## 2. Zasada nadrzędna

Centralnym obiektem systemu jest:

**PRODUCT — produkt chemiczny.**

Nie plik PDF ani stanowisko.

Główna relacja dokumentacyjna:

```text
PRODUCT
   ↓
SDS
   ├── SAFETY_PROFILE
   └── SDS_COMPONENT 1:N
   ↓
BHP_DECISION
   ↓
DECISION_EVIDENCE
```

Równolegle PRODUCT jest powiązany z miejscami stosowania:

```text
PRODUCT
   ↓
PRODUCT_USAGE_LOCATION
   ↓
USAGE_LOCATION
```

`USAGE_LOCATION` jest osobną encją relacyjnej bazy, ale biznesowo opisuje PRODUCT: gdzie produkt jest używany.

Jednostki danych ilościowych są wskazywane z kontrolowanego słownika:

```text
PRODUCT_USAGE_LOCATION
   ├── peak quantity ───────→ UNIT_OF_MEASURE
   └── monthly consumption ─→ UNIT_OF_MEASURE
```

`UNIT_OF_MEASURE` jest wspólnym słownikiem dla ilości szczytowej i miesięcznego zużycia.

Równolegle system może rejestrować punktowy przegląd fizycznego stanu:

```text
REVIEW
   └── REVIEW_ITEM
          ├── PRODUCT
          └── USAGE_LOCATION
```

`REVIEW / REVIEW_ITEM` tworzą historyczny snapshot obserwacji fizycznej. Nie zastępują bieżących danych `PRODUCT_USAGE_LOCATION` ani mechanizmu historii Core.

---

## 3. PRODUCT

### 3.1. Identyfikator

Każdy produkt posiada własny niezmienny:

`product_id`

### 3.2. Tożsamość biznesowa

Tożsamość produktu tworzą:

- `product_name`,
- `manufacturer_product_code`,
- `manufacturer_id`.

Obowiązuje:

> **Nowa nazwa, nowy kod/numer produktu lub inny producent = nowy rekord PRODUCT.**

Pola te po utworzeniu PRODUCT nie są zwykłymi polami administracyjnie edytowalnymi.

Poprzedni produkt pozostaje w bazie wraz z historią SDS, decyzji i powiązań.

### 3.3. Dane administracyjnie edytowalne

Po utworzeniu PRODUCT ręcznie edytowalne są:

- `use_description`,
- `use_restriction`,
- `usage_status`,
- `waste_type`,
- `waste_code`.

`waste_type` i `waste_code` są opcjonalnymi polami informacyjnymi w PRODUCT. Nie tworzą w MVP osobnej bazy ani modułu gospodarki odpadami.

### 3.4. Status stosowania

Dozwolone statusy MVP:

- `PENDING_APPROVAL`,
- `ACTIVE`,
- `REJECTED`,
- `INACTIVE`.

Znaczenie statusów pozostaje zgodne z zatwierdzonymi BDR dotyczącymi produktu, SDS i decyzji BHP.

---

## 4. MANUFACTURER

Producent jest osobną encją:

```text
MANUFACTURER
├── manufacturer_id
└── manufacturer_name
```

Relacja:

```text
MANUFACTURER 1:N PRODUCT
```

Producent może zostać utworzony podczas workflow tworzenia produktu, lecz zawsze jako osobny rekord MANUFACTURER.

Dostawca handlowy pozostaje poza Core.

---

## 5. USAGE_LOCATION

Miejsca stosowania są osobną tabelą/słownikiem stanowisk.

Minimalny model:

```text
USAGE_LOCATION
├── location_id
├── location_code
├── location_name
└── status
```

`location_id`:
- jest technicznym, niezmiennym identyfikatorem,
- pozostaje PK/FK,
- nie jest podstawowym identyfikatorem biznesowym prezentowanym w normalnym UI.

`location_code`:
- jest krótkim symbolem biznesowym nadawanym świadomie przez użytkownika,
- jest wymagany w docelowym modelu,
- jest unikalny,
- jest normalizowany do uppercase,
- pozostaje stabilny w normalnym workflow,
- nie zastępuje `location_id`.

Migracja danych legacy nie może zgadywać `location_code`.

Dozwolone statusy:

```text
ACTIVE
INACTIVE
```

Relacja:

```text
PRODUCT N:M USAGE_LOCATION
```

Jedno stanowisko może być powiązane z wieloma produktami, a produkt z wieloma stanowiskami.

Biznesową perspektywą aplikacji pozostaje PRODUCT. Stanowiska odpowiadają na pytanie: **gdzie dany produkt jest używany?**

`ACTIVE` oznacza lokalizację aktualnie funkcjonującą, dostępną dla nowych przypisań i bieżącej analityki.

`INACTIVE` oznacza lokalizację wycofaną z bieżącego użycia; rekord i jego `location_id` pozostają zachowane dla historii.

System umożliwia dodawanie stanowisk, dezaktywację i reaktywację. Dane posiadające znaczenie historyczne nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

Historia lokalizacji nadal opiera się na `location_id`; `location_code` nie jest osobno wersjonowany w obecnym Core.

---

## 6. PRODUCT_USAGE_LOCATION

Obiekt pośredni przechowuje powiązanie produktu ze stanowiskiem oraz dwa niezależne rodzaje danych ilościowych:

```text
PRODUCT_USAGE_LOCATION
├── product_id
├── location_id
├── peak_quantity_value
├── peak_quantity_unit → UNIT_OF_MEASURE
├── monthly_consumption_value
└── monthly_consumption_unit → UNIT_OF_MEASURE
```

Nazwy `peak_quantity_unit` i `monthly_consumption_unit` opisują biznesową rolę jednostki. Dokładna techniczna reprezentacja referencji do `UNIT_OF_MEASURE` należy do TDR i nie jest rozstrzygana przez Core.

Samo istnienie relacji oznacza, że stanowisko jest przypisane do produktu.

Brak relacji oznacza, że stanowisko nie jest przypisane do produktu.

### 6.1. Ilość szczytowa

`peak_quantity_value` oznacza zadeklarowaną maksymalną/szczytową ilość produktu na stanowisku z punktu widzenia bezpieczeństwa.

Reguły:

- obowiązkowa dla istniejącej relacji,
- typ `Decimal`,
- wartość `>= 0`,
- jednostka ilości szczytowej jest obowiązkowa,
- jednostka jest wybierana z kontrolowanego `UNIT_OF_MEASURE`, a nie wpisywana dowolnym tekstem.

`0` jest prawidłową wartością biznesową i nie oznacza braku danych.

Ilość szczytowa nie jest stanem magazynowym, zapasem, zakupem, przyjęciem, wydaniem ani ruchem materiałowym.

### 6.2. Miesięczne zużycie

`monthly_consumption_value` oznacza deklarowane/orientacyjne zużycie produktu na stanowisku w skali miesięcznej.

Reguły:

- opcjonalne,
- typ `Decimal`,
- jeżeli podane: `>= 0`,
- jeżeli wartość jest podana, jednostka miesięcznego zużycia jest obowiązkowa,
- jednostka jest wybierana z tego samego kontrolowanego `UNIT_OF_MEASURE`.

Semantyka:

```text
NULL → brak zadeklarowanej informacji
0    → świadomie zadeklarowane zerowe zużycie
> 0  → zadeklarowane dodatnie zużycie
```

Jeżeli miesięczne zużycie nie jest podane:

```text
monthly_consumption_value = NULL
monthly_consumption_unit  = NULL
```

Ilość szczytowa i miesięczne zużycie są różnymi informacjami biznesowymi i mogą wskazywać różne jednostki z tego samego słownika.
---

## 7. UNIT_OF_MEASURE i sumaryczna ilość szczytowa

W systemie obowiązuje jeden wspólny, kontrolowany słownik jednostek:

```text
UNIT_OF_MEASURE
├── unit_id
├── code
├── name
├── category
└── status
```

Minimalne znaczenie pól:

- `unit_id` — stabilny identyfikator jednostki,
- `code` — krótki kod prezentowany przy wartości, np. `l`, `kg`, `szt`,
- `name` — pełna nazwa użytkowa,
- `category` — rodzaj wielkości,
- `status` — `ACTIVE` albo `INACTIVE`.

Minimalnie przewidziane kategorie:

```text
VOLUME
MASS
COUNT
```

Przykładowe jednostki:

```text
l    → litr       → VOLUME
ml   → mililitr   → VOLUME
kg   → kilogram   → MASS
g    → gram       → MASS
szt  → sztuka     → COUNT
```

Lista jednostek nie jest zamknięta na poziomie Core. Dodanie jednostki do zatwierdzonej kategorii nie zmienia logiki Core, o ile nie wprowadza nowej semantyki biznesowej ani reguł przeliczania.

### 7.1. Status jednostki

`ACTIVE`:
- może być wybierana przy nowych lub edytowanych danych ilościowych.

`INACTIVE`:
- nie jest proponowana jako nowy wybór,
- może pozostać powiązana z istniejącymi i historycznymi danymi.

Wycofanie jednostki nie może niszczyć ani przepisywać danych historycznych.

Fizyczne usunięcie jednostki posiadającej referencje nie jest standardowym zachowaniem Core.

### 7.2. Brak automatycznej konwersji

System nie wykonuje automatycznych konwersji jednostek, w szczególności:

```text
kg ↔ g
l ↔ ml
```

Nie istnieje w Core:
- silnik konwersji,
- tabela współczynników przeliczeniowych,
- automatyczna normalizacja do jednostki bazowej,
- przeliczanie przez gęstość.

Kategoria jednostki służy uporządkowaniu danych i walidacji, a nie automatycznemu przeliczaniu wartości.

### 7.3. Zasada dla `Raportu przeglądu / Stan na dzień`

Dla `Raportu przeglądu / Stan na dzień` obowiązuje reguła biznesowa:

> wartość obserwowana dla PRODUCT × USAGE_LOCATION jest zapisywana w tej samej jednostce co MAX dla tej relacji.

Przykład:

```text
MAX = 40 kg
Stan na dzień = 45 kg
Różnica = +5 kg
```

Użytkownik nie wybiera alternatywnej jednostki dla obserwacji tej samej pozycji.

BDR-006 ustalił zasadę zgodności jednostki porównania. Model snapshotu przeglądu został następnie zatwierdzony w BDR-011.

### 7.4. Sumaryczna ilość szczytowa

Dla produktu:

```text
peak_factory_quantity(product)
=
Σ peak_quantity_value
```

dla aktywnych miejsc stosowania i wyłącznie dla pozycji posiadających tę samą jednostkę.

`peak_factory_quantity`:
- jest wartością wyliczaną,
- nie jest ręcznie edytowalnym polem,
- nie obejmuje `monthly_consumption_value`.

System nie sumuje różnych jednostek i nie przelicza ich automatycznie.
---

## 8. SDS

Każdy zarejestrowany SDS:

- musi posiadać powiązany PRODUCT,
- musi posiadać fizyczny plik PDF,
- otrzymuje własny systemowy `sds_id`.

```text
brak PRODUCT → brak rekordu SDS
brak PDF     → brak rekordu SDS
```

PDF pochodzi ze wskazanego `SDS_ROOT_PATH`. Aplikacja referencjonuje plik źródłowy i nie zarządza nim fizycznie.

Dla obecnego wdrożenia do Core przyjmowany jest wyłącznie SDS w wymaganym języku polskim. Odrzucony dokument obcojęzyczny nie tworzy SDS ani PRODUCT w Core.

---

## 9. Metadane i status SDS

Minimalne dane SDS obejmują m.in.:

- `sds_id`,
- `product_id`,
- `original_filename`,
- `relative_path`,
- `issue_date` — jeśli dostępna,
- `revision` — jeśli dostępna,
- `status`,
- `registered_at`.

Dozwolone statusy:

- `CURRENT`,
- `ARCHIVED`.

Jeden PRODUCT może posiadać maksymalnie jeden zatwierdzony SDS `CURRENT`.

Zatwierdzenie nowego SDS wykonuje spójną zmianę:

```text
poprzedni CURRENT → ARCHIVED
nowy SDS          → CURRENT
```

Rewizja, data i nazwa pliku nie ustalają automatycznie aktualności SDS.

---

## 10. SAFETY_PROFILE

`SAFETY_PROFILE` należy do konkretnego `sds_id`, nie bezpośrednio do trwałej tożsamości PRODUCT.

Zakres MVP obejmuje zatwierdzone dane bezpieczeństwa z Sekcji 2 i 11, w szczególności:

- definicję produktu,
- klasyfikację CLP,
- status klasyfikacji jako niebezpieczny,
- hasło ostrzegawcze,
- zwroty H i informacje uzupełniające,
- PBT,
- vPvB,
- rakotwórczość,
- mutagenność komórek rozrodczych,
- toksyczność reprodukcyjną,
- właściwości endokrynne z Sekcji 2 i Sekcji 11 jako osobne informacje,
- uczulenie skóry,
- uczulenie dróg oddechowych.

Dla właściwych pól obowiązują statusy:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

`NO_DATA` nie oznacza `NO`.

---

## 11. SDS_COMPONENT

Dane składników ujawnionych w Sekcji 3 są przechowywane jako relacja 1:N do konkretnego SDS.

Minimalny model:

```text
SDS_COMPONENT
├── component_id
├── sds_id
├── component_name
├── cas_number
├── ec_number
├── reach_registration_number
├── concentration_text
├── classification_text
└── hazard_statements
```

Zagrożenie składnika nie może być automatycznie utożsamiane z klasyfikacją całego produktu.

---

## 12. Ekstrakcja i akceptacja danych SDS

Automatyczna ekstrakcja przygotowuje draft, a nie obowiązujące dane:

```text
PDF SDS
  ↓
walidacja wejściowa
  ↓
automatyczna ekstrakcja
  ↓
DRAFT
  ↓
weryfikacja użytkownika
  ↓
AKCEPTUJ / NIE AKCEPTUJ
```

Draft obejmuje jako pakiet dane identyfikacyjne produktu, producenta, metadane SDS, SAFETY_PROFILE i SDS_COMPONENT.

Odrzucony draft nie jest zapisywany w Core.

Po akceptacji:

- zapisuje się `approved_at`,
- automatyczne przetwarzanie danego SDS kończy się,
- system nie reinterpretuje go samoczynnie po zmianie parsera.

Późniejsza ręczna edycja zatwierdzonej reprezentacji danych:

- nie zmienia PDF,
- nie tworzy automatycznie nowego SDS,
- aktualizuje `last_manual_edit_at`.

---

## 13. BHP_DECISION

Decyzja BHP jest osobnym obiektem dotyczącym:

- konkretnego PRODUCT,
- konkretnego zatwierdzonego SDS.

```text
BHP_DECISION
├── product_id
├── sds_id
├── decision_status
├── record_status
├── notes
└── registered_at
```

Wynik decyzji:

- `APPROVED`,
- `REJECTED`.

Status rekordu:

- `CURRENT`,
- `SUPERSEDED`.

Nowy zatwierdzony SDS wymaga nowej decyzji BHP. Poprzednia decyzja pozostaje przy poprzednim `sds_id`.

Korekta decyzji tworzy nowy rekord; poprzedni staje się `SUPERSEDED`.

Decyzja BHP nie jest wydawana osobno dla każdego miejsca stosowania.

---

## 14. DECISION_EVIDENCE

W MVP obowiązuje:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Jedna decyzja posiada jeden dowód.

Dopuszczalne formaty:

- `.msg`,
- `.pdf`,
- `.jpg`,
- `.jpeg`,
- `.png`.

Minimalne metadane pliku dowodowego obejmują:

```text
evidence_id
original_filename
relative_path
evidence_type
file_format
file_status
```

`original_filename` zachowuje nazwę pliku dostarczonego przez użytkownika / źródło i jest niezależne od technicznej nazwy storage.

`relative_path` wskazuje kontrolowaną lokalizację względem `BHP_EVIDENCE_ROOT_PATH`.

Techniczna nazwa pliku nie zastępuje `original_filename` ani `evidence_id`.

Dowód jest przechowywany w osobnym repozytorium `BHP_EVIDENCE_ROOT_PATH`; baza przechowuje jego metadane i ścieżkę względną.

---

## 15. Repozytoria plików

SDS i dowody BHP pozostają w dwóch niezależnych repozytoriach:

```text
SDS_ROOT_PATH
BHP_EVIDENCE_ROOT_PATH
```

Aplikacja referencjonuje pliki źródłowe i ich nie modyfikuje.

Brak pliku źródłowego po wcześniejszej rejestracji nie usuwa historii rekordu z bazy; interfejs powinien sygnalizować niedostępność źródła.

---

## 16. Historia i audytowalność

Core musi zachowywać historię co najmniej:

- produktów,
- statusu stosowania,
- wersji SDS,
- statusów SDS `CURRENT / ARCHIVED`,
- decyzji BHP,
- dowodów decyzji,
- powiązań PRODUCT z USAGE_LOCATION,
- `peak_quantity`,
- `monthly_consumption`,
- przeglądów.

W obszarze PRODUCT–USAGE_LOCATION perspektywą nadrzędną historii jest PRODUCT.

Docelowo musi być możliwe odtworzenie co najmniej zmian:

- `usage_status`,
- przypisanych miejsc stosowania,
- `peak_quantity_value` i przypisanej jednostki z `UNIT_OF_MEASURE`,
- `monthly_consumption_value` i przypisanej jednostki z `UNIT_OF_MEASURE`.

Zmiana przypisanej jednostki MAX lub miesięcznego zużycia jest zmianą biznesowej informacji ilościowej i musi pozostać możliwa do odtworzenia.

Szczegółowa techniczna reprezentacja referencji do jednostki w historii należy do TDR. Codex nie może jej samodzielnie zaprojektować.

Rekordy znaczące historycznie nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

---

## 16A. REVIEW / REVIEW_ITEM — Raport przeglądu / Stan na dzień

`REVIEW` i `REVIEW_ITEM` tworzą odrębny od historii Core mechanizm historycznego przeglądu fizycznego.

Jeden `REVIEW` reprezentuje jeden logiczny przegląd zakładu dla określonej daty.

Minimalny model biznesowy:

```text
REVIEW
├── review_id
├── review_date
├── status
├── created_at
└── finalized_at

REVIEW_ITEM
├── review_item_id
├── review_id
├── product_id
├── location_id
├── baseline_max_quantity
├── baseline_unit
└── observed_quantity
```

Dokładne nazwy techniczne, typy i FK należą do TDR.

### 16A.1. Lifecycle

Dozwolone statusy MVP:

```text
DRAFT
FINAL
```

W systemie może istnieć maksymalnie jeden aktywny `DRAFT`.

Finalizacja:

```text
DRAFT → FINAL
```

zapisuje `finalized_at`.

Nie istnieje standardowe przejście:

```text
FINAL → DRAFT
```

### 16A.2. Populacja snapshotu

Przy utworzeniu nowego `DRAFT` populacja obejmuje wszystkie istniejące:

```text
PRODUCT_USAGE_LOCATION
```

dla:

```text
USAGE_LOCATION.status = ACTIVE
```

Status produktu nie usuwa automatycznie istniejącego przypisania z populacji przeglądu.

Populacja jest zamrażana w chwili utworzenia `DRAFT`.

Późniejsze:
- utworzenie lokalizacji,
- dezaktywacja lub reaktywacja lokalizacji,
- nowe przypisanie PRODUCT × USAGE_LOCATION,
- zmiana istniejącego przypisania

nie dodają ani nie usuwają automatycznie pozycji z już istniejącego przeglądu.

### 16A.3. Baseline i jednostka

Każdy `REVIEW_ITEM` zachowuje wartość MAX obowiązującą dla relacji PRODUCT × USAGE_LOCATION w chwili utworzenia snapshotu:

```text
baseline_max_quantity
baseline_unit
```

Późniejsza zmiana `PRODUCT_USAGE_LOCATION.peak_quantity` lub jego jednostki nie zmienia historycznego `FINAL`.

Dla wartości obserwowanej obowiązuje:

```text
observed_unit = baseline_unit
```

Użytkownik nie wybiera alternatywnej jednostki i system nie wykonuje konwersji.

### 16A.4. observed_quantity — 0 i NULL

`observed_quantity`, jeżeli podane, musi być:

```text
>= 0
```

Semantyka:

```text
0
→ pozycję sprawdzono i fizycznie stwierdzono brak produktu / ilość równą zero

NULL
→ pozycja nie została sprawdzona albo nie uzyskano wiarygodnego wyniku obserwacji
```

`0` i `NULL` nie są zamienne.

`FINAL` może zawierać pozycje z `observed_quantity = NULL`.

### 16A.5. Różnica

Różnica ma znaczenie:

```text
difference
=
observed_quantity - baseline_max_quantity
```

Jeżeli:

```text
observed_quantity = NULL
```

różnica również nie posiada wartości.

`difference` jest informacją pochodną i pomocniczą. Nie powoduje automatycznie:
- zmiany MAX,
- zmiany statusu produktu,
- decyzji BHP,
- oceny zgodności.

Decyzja, czy `difference` jest zapisywana fizycznie czy wyliczana w read modelu, należy do TDR.

### 16A.6. Finalizacja i immutable snapshot

Finalizacji dokonuje użytkownik/operator poprzez świadomą akcję.

W MVP Core nie wymaga osobnego `approved_by`.

Po przejściu do `FINAL` nie wolno edytować:
- `review_date`,
- populacji,
- baseline MAX,
- jednostki,
- `observed_quantity`.

Korekta lub nowy stan fizyczny wymaga utworzenia nowego `REVIEW`.

### 16A.7. Relacja do ANALYTICS-02

Dla `PRODUCT × USAGE_LOCATION` ostatni właściwy przegląd oznacza:

```text
najpóźniejszy FINAL według review_date
```

Przy tej samej `review_date` rozstrzyga:

```text
finalized_at
```

Brak `FINAL` dla pozycji oznacza brak wyniku przeglądu i nie może być prezentowany jako `0`.

`Zestawienie zbiorcze` może prezentować informacyjnie:

```text
MAX
Stan na dzień
Różnica +/-
```

bez automatycznej zmiany danych Core.

### 16A.8. Rozdzielenie od historii Core

Historia Core odpowiada na pytanie:

```text
jaki zatwierdzony stan danych referencyjnych obowiązywał
```

`REVIEW / REVIEW_ITEM` odpowiadają na pytanie:

```text
jaki stan fizycznie stwierdzono podczas konkretnego przeglądu
```

`REVIEW / REVIEW_ITEM`:
- nie są rekordami `PRODUCT_USAGE_LOCATION_HISTORY`,
- nie nadpisują historii Core,
- nie zastępują historii Core.

---

## 17. Granice Core

Core nie obejmuje:

- zakupów,
- dostawców handlowych,
- gospodarki magazynowej,
- ciągłego prowadzenia stanów magazynowych; `Raport przeglądu / Stan na dzień` jest punktowym snapshotem kontrolnym, a nie ewidencją magazynową,
- wydań i przyjęć,
- numerów partii,
- osobnego modułu gospodarki odpadami,
- BDO,
- automatycznej interpretacji prawnej,
- automatycznego dopuszczenia BHP,
- pełnej kontroli REACH,
- ERP/MES,
- automatycznej konwersji jednostek.

Pola `waste_type` i `waste_code` nie zmieniają tej granicy.

---

## 18. Model Core — widok zbiorczy

```text
UNIT_OF_MEASURE
├── unit_id
├── code
├── name
├── category
└── ACTIVE / INACTIVE


MANUFACTURER
     │
     │ 1:N
     ▼
PRODUCT
├── product_id
├── product_name
├── manufacturer_product_code
├── manufacturer_id
├── usage_status
├── use_description
├── use_restriction
├── waste_type
├── waste_code
│
├── 1:N SDS
│      ├── sds_id
│      ├── issue_date
│      ├── revision
│      ├── relative_path
│      ├── CURRENT / ARCHIVED
│      ├── SAFETY_PROFILE 1:1
│      └── SDS_COMPONENT 1:N
│
├── N:M USAGE_LOCATION
│      ├── location_id
│      ├── location_code
│      ├── location_name
│      ├── ACTIVE / INACTIVE
│      └── PRODUCT_USAGE_LOCATION
│             ├── peak_quantity_value
│             ├── peak_quantity_unit ──────────────→ UNIT_OF_MEASURE
│             ├── monthly_consumption_value
│             └── monthly_consumption_unit ────────→ UNIT_OF_MEASURE
│
└── BHP_DECISION
       ├── sds_id
       ├── CURRENT / SUPERSEDED
       └── DECISION_EVIDENCE 1:1


REVIEW
├── review_id
├── review_date
├── DRAFT / FINAL
├── created_at
├── finalized_at
└── REVIEW_ITEM 1:N
       ├── product_id ─────────────────────────────→ PRODUCT
       ├── location_id ────────────────────────────→ USAGE_LOCATION
       ├── baseline_max_quantity
       ├── baseline_unit ──────────────────────────→ UNIT_OF_MEASURE
       └── observed_quantity
```

`peak_quantity_unit`, `monthly_consumption_unit` i `baseline_unit` oznaczają biznesową rolę referencji do wspólnego `UNIT_OF_MEASURE`; dokładny model FK / persistence zostanie określony w TDR.

---

## 19. Reguły integralności Core

1. `PRODUCT` zawsze posiada `product_id`.
2. Nowa nazwa, kod/numer lub producent = nowy PRODUCT.
3. `product_name`, `manufacturer_product_code` i `manufacturer_id` nie są zwykłymi polami administracyjnie edytowalnymi po utworzeniu PRODUCT.
4. MANUFACTURER jest osobną encją 1:N względem PRODUCT.
5. USAGE_LOCATION jest osobną encją; PRODUCT i USAGE_LOCATION pozostają w relacji N:M.
6. Istnienie PRODUCT_USAGE_LOCATION oznacza przypisanie stanowiska do produktu.
7. `peak_quantity_value` jest obowiązkowe dla relacji i musi być `>= 0`.
8. Jednostka `peak_quantity_value` jest obowiązkowa i musi wskazywać jednostkę z `UNIT_OF_MEASURE`.
9. `monthly_consumption_value` jest opcjonalne; jeśli podane, musi być `>= 0`.
10. Jeżeli podano `monthly_consumption_value`, jego jednostka jest obowiązkowa i musi wskazywać jednostkę z `UNIT_OF_MEASURE`.
11. Jednostki ilościowe nie są swobodnym tekstem użytkownika.
12. Tylko jednostka `ACTIVE` może być wybierana dla nowych lub edytowanych danych; `INACTIVE` może pozostać w danych istniejących i historycznych.
13. Jednostka posiadająca referencje nie może być standardowo fizycznie usunięta.
14. Zero jest wartością biznesową; nie może być utożsamiane z brakiem danych.
15. `monthly_consumption_value = NULL` oznacza brak zadeklarowanej informacji.
16. Sumaryczna ilość szczytowa fabryki jest obliczana z `peak_quantity_value`.
17. System nie sumuje różnych jednostek i nie wykonuje automatycznej konwersji jednostek.
18. W przyszłym `Stan na dzień` wartość obserwowana dla danej relacji PRODUCT × USAGE_LOCATION używa jednostki MAX; różnica jest liczona w tej samej jednostce.
19. `waste_type` i `waste_code` są opcjonalnymi polami PRODUCT i nie tworzą osobnego modułu odpadów.
20. SDS nie istnieje w Core bez PRODUCT ani zaakceptowanego fizycznego PDF w wymaganym języku.
21. Jeden PRODUCT ma maksymalnie jeden zatwierdzony SDS `CURRENT`.
22. Zatwierdzenie nowego SDS archiwizuje poprzedni `CURRENT`.
23. Rewizja i data nie ustalają automatycznie aktualności SDS.
24. SAFETY_PROFILE i SDS_COMPONENT należą do konkretnego `sds_id`.
25. `NO_DATA` nie oznacza `NO`.
26. Dane automatycznie odczytane z PDF wymagają jawnej weryfikacji i akceptacji użytkownika.
27. Odrzucony draft ekstrakcji nie jest zapisywany w Core.
28. Po akceptacji SDS nie jest automatycznie reinterpretowany w tle.
29. BHP_DECISION dotyczy konkretnego PRODUCT i konkretnego `sds_id`.
30. Jeden aktualny rekord decyzji BHP posiada jeden dowód w MVP.
31. Korekta decyzji nie nadpisuje historii; tworzy nowy rekord, a poprzedni staje się `SUPERSEDED`.
32. SDS i dowody BHP są przechowywane w osobnych repozytoriach.
33. Wynik automatycznej analizy nie jest decyzją BHP.
34. Dane znaczące historycznie nie mogą być fizycznie usuwane bez zatwierdzonej reguły.
35. Docelowa `USAGE_LOCATION` posiada niepusty `location_code`.
36. `location_code` jest unikalny.
37. `location_code` nie jest PK/FK i nie zastępuje `location_id`.
38. Standardowy UI nie eksponuje `location_id` jako biznesowego identyfikatora lokalizacji.
39. Migracja legacy nie może zgadywać `location_code`.
40. `REVIEW` posiada własne `review_id`, `review_date` oraz status `DRAFT / FINAL`.
41. W MVP może istnieć maksymalnie jeden aktywny `DRAFT`.
42. Populacja nowego `REVIEW` obejmuje wszystkie `PRODUCT_USAGE_LOCATION` dla lokalizacji `ACTIVE`.
43. Populacja `REVIEW` jest zamrażana przy jego utworzeniu i nie zmienia się automatycznie wskutek późniejszych zmian bieżących danych.
44. Każdy `REVIEW_ITEM` zachowuje `product_id`, `location_id`, baseline MAX, jednostkę MAX i `observed_quantity`.
45. Jednostka wartości obserwowanej jest zawsze jednostką baseline MAX; brak alternatywnej jednostki i brak automatycznej konwersji.
46. `observed_quantity = 0` oznacza sprawdzony fizyczny brak produktu / ilość zero.
47. `observed_quantity = NULL` oznacza pozycję niesprawdzoną albo brak wiarygodnego wyniku; `0` i `NULL` nie są zamienne.
48. `FINAL` może zawierać pozycje z `observed_quantity = NULL`.
49. `DRAFT → FINAL` zapisuje `finalized_at`; w MVP Core nie wymaga osobnego `approved_by`.
50. `FINAL` jest immutable; nie ma standardowego `FINAL → DRAFT`, a korekta wymaga nowego `REVIEW`.
51. Późniejsza zmiana MAX, jednostki, przypisania lub statusu lokalizacji nie zmienia istniejącego `FINAL`.
52. `difference = observed_quantity - baseline_max_quantity`; przy `observed_quantity = NULL` różnica nie posiada wartości.
53. Różnica ma charakter informacyjny i nie zmienia automatycznie MAX, statusu produktu, decyzji BHP ani oceny zgodności.
54. Ostatni właściwy przegląd dla ANALYTICS-02 to najpóźniejszy `FINAL` wg `review_date`, a przy remisie wg `finalized_at`.
55. Brak `FINAL` dla pozycji oznacza brak wyniku przeglądu i nie może być podstawiany jako `0`.
56. `REVIEW / REVIEW_ITEM` są odrębnym mechanizmem od `PRODUCT_USAGE_LOCATION_HISTORY` i nie nadpisują historii Core.
---

## 20. Otwarte elementy Core

Po BDR-011 biznesowy model `REVIEW / REVIEW_ITEM` jest ustalony, ale przed implementacją wymagają decyzji technicznej:

- dokładne tabele / modele persistence dla `REVIEW` i `REVIEW_ITEM`,
- techniczna reprezentacja `baseline_unit` oraz FK do `UNIT_OF_MEASURE`,
- constraints wymuszające maksymalnie jeden aktywny `DRAFT`,
- sposób utworzenia i transakcyjnego zamrożenia populacji snapshotu,
- sposób zapewnienia immutability `FINAL`,
- sposób wyznaczania ostatniego `FINAL` w read modelu ANALYTICS-02,
- migracja Alembic i walidacja schema,
- finalny workflow Application i UI `Raportu przeglądu`.

Poza tym nadal otwarte pozostają:
- szczegółowa polityka fizycznego usuwania / dezaktywacji stanowisk posiadających historię,
- przyszłe rozwinięcie pól `waste_type` i `waste_code` do modelu gospodarki odpadami — poza obecnym zakresem.

Punkty te nie upoważniają Codexa do samodzielnego projektowania rozwiązania bez właściwego TDR / Tasku.

---

## 21. Ochrona Core

Codex nie może bez zatwierdzonej decyzji:

- zmieniać relacji między obiektami Core,
- zmieniać definicji tożsamości PRODUCT,
- pozwalać na zwykłą edycję nazwy, kodu lub producenta istniejącego PRODUCT,
- dodawać nowych statusów lub zmieniać znaczenia istniejących,
- zastępować MANUFACTURER lub USAGE_LOCATION swobodnym tekstem,
- zastępować `UNIT_OF_MEASURE` swobodnym tekstem,
- pozwalać na wybór jednostki `INACTIVE` dla nowych lub edytowanych danych,
- fizycznie usuwać jednostki posiadającej referencje bez zatwierdzonej reguły,
- interpretować wartości `0` jako braku danych,
- automatycznie przeliczać jednostek,
- zmieniać reguły SDS `CURRENT / ARCHIVED`,
- zmieniać zasad przechowywania dokumentów,
- dodawać funkcji magazynowych,
- tworzyć osobnego modułu odpadów na podstawie `waste_type` i `waste_code`,
- zmieniać relacji decyzja–dowód,
- automatycznie podejmować decyzji BHP,
- upraszczać `NO_DATA` do `NO`,
- projektować mechanizmu historii PRODUCT–USAGE_LOCATION bez osobnej decyzji.
- zmieniać lifecycle `REVIEW DRAFT / FINAL` bez nowej zatwierdzonej decyzji,
- edytować lub otwierać ponownie `FINAL`,
- utożsamiać `observed_quantity = NULL` z wartością `0`,
- automatycznie aktualizować MAX na podstawie wyniku przeglądu,
- traktować `REVIEW / REVIEW_ITEM` jako zamiennik historii Core.

Zmiana Core wymaga zatwierdzonego ADR lub BDR.

---

## 22. Status dokumentu

Niniejszy dokument jest zatwierdzoną, skonsolidowaną rewizją:

```text
CORE-001 v1.5-approved
```

Bazą jest:

```text
CORE-001 v1.4-approved
```

Rewizja 1.5:
- konsoliduje do pełnego dokumentu zatwierdzoną zmianę `USAGE_LOCATION.location_code` z v1.4,
- dodaje model `REVIEW / REVIEW_ITEM` wynikający z BDR-011 v1.0-approved,
- nie zmienia zatwierdzonych zasad PRODUCT, SDS, BHP_DECISION, DECISION_EVIDENCE ani UNIT_OF_MEASURE poza koniecznymi powiązaniami z przeglądem.

`CORE-001 v1.5-approved` staje się aktualnym obowiązującym dokumentem Core i zastępuje `CORE-001 v1.4-approved` jako current Core.

---

## 23. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-08-25 | Draft | Pierwszy zbiorczy model Core MSDS Manager |
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono model Core jako obowiązujące źródło wymagań dla implementacji |
| 1.1-approved | 2026-08-28 | Approved | Zatwierdzona rewizja po BDR-002 v1.1-approved: producent w tożsamości PRODUCT, waste_type/waste_code, nowy model PRODUCT_USAGE_LOCATION, monthly consumption, semantyka 0/NULL i perspektywa historii od strony PRODUCT; uaktualniono także agregację o zatwierdzone BDR-004 i BDR-005 |
| 1.2-draft | 2026-09-29 | Draft | Rewizja wynikająca z BDR-006 v1.0-approved: centralny UNIT_OF_MEASURE, kontrolowane jednostki dla MAX i monthly consumption, ACTIVE/INACTIVE, brak automatycznej konwersji oraz zasada tej samej jednostki MAX dla przyszłego `Stan na dzień` |
| 1.2-approved | 2026-09-29 | Approved | Architekt Operacyjny zatwierdził rewizję Core wynikającą z BDR-006 bez zmian merytorycznych |
| 1.3-draft | 2026-10-01 | Draft | Dodano `DECISION_EVIDENCE.original_filename` jako wymaganą metadaną źródłową, bez zmiany relacji 1:1 ani lifecycle BHP; zmiana wynika z BDR-008 i BLOCKED TASK-037 |


| 1.3-approved | 2026-10-01 | Approved | Architekt Operacyjny zatwierdził dodanie `original_filename` do DECISION_EVIDENCE jako metadanej źródłowej, bez zmiany relacji 1:1 ani lifecycle BHP. |

| 1.4-approved | 2026-10-05 | Approved | Dodano biznesowy `USAGE_LOCATION.location_code`: wymagany docelowo, unikalny, nadawany przez użytkownika, niewykorzystywany jako PK/FK; zachowano `location_id` jako techniczną tożsamość i zabroniono zgadywania kodu dla legacy. |
| 1.5-approved | 2026-10-06 | Approved | Architekt Operacyjny zatwierdził skonsolidowany Core po v1.4 oraz model `REVIEW / REVIEW_ITEM` dla ANALYTICS-03 zgodny z BDR-011 v1.0-approved: DRAFT/FINAL, zamrożona populacja, baseline MAX/unit, semantyka `0` vs `NULL`, niepełny FINAL, immutable snapshot i relacja do ANALYTICS-02. |
