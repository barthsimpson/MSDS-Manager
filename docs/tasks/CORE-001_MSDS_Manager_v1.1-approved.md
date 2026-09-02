# CORE-001 — Model Core projektu MSDS Manager

**Projekt:** MSDS Manager  
**Id dokumentu:** CORE-001  
**Wersja:** 1.1-draft  
**Status:** Approved  
**Data rewizji:** 2026-08-28  
**Dokument bazowy:** CORE-001 v1.0-approved  
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
- pomocniczych informacji odpadowych produktu,
- dokumentów SDS,
- profilu bezpieczeństwa i składników SDS,
- wersjonowania SDS,
- statusów produktu,
- decyzji BHP i dowodów,
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

- `location_id`,
- `location_name`,
- `status`.

Relacja:

```text
PRODUCT N:M USAGE_LOCATION
```

Jedno stanowisko może być powiązane z wieloma produktami, a produkt z wieloma stanowiskami.

Biznesową perspektywą aplikacji pozostaje PRODUCT. Stanowiska odpowiadają na pytanie: **gdzie dany produkt jest używany?**

System umożliwia dodawanie stanowisk i wycofywanie ich z bieżącego użycia. Dane posiadające znaczenie historyczne nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

---

## 6. PRODUCT_USAGE_LOCATION

Obiekt pośredni przechowuje powiązanie produktu ze stanowiskiem oraz dwa niezależne rodzaje danych ilościowych:

```text
PRODUCT_USAGE_LOCATION
├── product_id
├── location_id
├── peak_quantity_value
├── peak_quantity_unit
├── monthly_consumption_value
└── monthly_consumption_unit
```

Samo istnienie relacji oznacza, że stanowisko jest przypisane do produktu.

Brak relacji oznacza, że stanowisko nie jest przypisane do produktu.

### 6.1. Ilość szczytowa

`peak_quantity_value` oznacza zadeklarowaną maksymalną/szczytową ilość produktu na stanowisku z punktu widzenia bezpieczeństwa.

Reguły:

- obowiązkowa dla istniejącej relacji,
- typ `Decimal`,
- wartość `>= 0`,
- `peak_quantity_unit` obowiązkowe.

`0` jest prawidłową wartością biznesową i nie oznacza braku danych.

Ilość szczytowa nie jest stanem magazynowym, zapasem, zakupem, przyjęciem, wydaniem ani ruchem materiałowym.

### 6.2. Miesięczne zużycie

`monthly_consumption_value` oznacza deklarowane/orientacyjne zużycie produktu na stanowisku w skali miesięcznej.

Reguły:

- opcjonalne,
- typ `Decimal`,
- jeżeli podane: `>= 0`,
- jeżeli wartość jest podana, `monthly_consumption_unit` jest obowiązkowe.

Semantyka:

```text
NULL → brak zadeklarowanej informacji
0    → świadomie zadeklarowane zerowe zużycie
> 0  → zadeklarowane dodatnie zużycie
```

Ilość szczytowa i miesięczne zużycie są różnymi informacjami biznesowymi.

---

## 7. Jednostki i sumaryczna ilość szczytowa

Jednostki `peak_quantity` i `monthly_consumption` są przechowywane niezależnie.

System nie wykonuje automatycznych konwersji jednostek bez osobnej zatwierdzonej reguły.

Dla produktu:

```text
peak_factory_quantity(product)
=
Σ peak_quantity_value
```

dla aktywnych miejsc stosowania i wyłącznie dla zgodnych jednostek.

`peak_factory_quantity`:

- jest wartością wyliczaną,
- nie jest ręcznie edytowalnym polem,
- nie obejmuje `monthly_consumption_value`.

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
- `peak_quantity_value` i `peak_quantity_unit`,
- `monthly_consumption_value` i `monthly_consumption_unit`.

Szczegółowy techniczny mechanizm historyzacji tego obszaru pozostaje otwartą decyzją. Codex nie może go samodzielnie zaprojektować.

Rekordy znaczące historycznie nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

---

## 17. Granice Core

Core nie obejmuje:

- zakupów,
- dostawców handlowych,
- gospodarki magazynowej,
- stanów bieżących,
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
│      └── PRODUCT_USAGE_LOCATION
│             ├── peak_quantity_value
│             ├── peak_quantity_unit
│             ├── monthly_consumption_value
│             └── monthly_consumption_unit
│
└── BHP_DECISION
       ├── sds_id
       ├── CURRENT / SUPERSEDED
       └── DECISION_EVIDENCE 1:1
```

---

## 19. Reguły integralności Core

1. `PRODUCT` zawsze posiada `product_id`.
2. Nowa nazwa, kod/numer lub producent = nowy PRODUCT.
3. `product_name`, `manufacturer_product_code` i `manufacturer_id` nie są zwykłymi polami administracyjnie edytowalnymi po utworzeniu PRODUCT.
4. MANUFACTURER jest osobną encją 1:N względem PRODUCT.
5. USAGE_LOCATION jest osobną encją; PRODUCT i USAGE_LOCATION pozostają w relacji N:M.
6. Istnienie PRODUCT_USAGE_LOCATION oznacza przypisanie stanowiska do produktu.
7. `peak_quantity_value` jest obowiązkowe dla relacji i musi być `>= 0`.
8. `peak_quantity_unit` jest obowiązkowe.
9. `monthly_consumption_value` jest opcjonalne; jeśli podane, musi być `>= 0`.
10. `monthly_consumption_unit` jest obowiązkowe, gdy podano `monthly_consumption_value`.
11. Zero jest wartością biznesową; nie może być utożsamiane z brakiem danych.
12. `monthly_consumption_value = NULL` oznacza brak zadeklarowanej informacji.
13. Sumaryczna ilość szczytowa fabryki jest obliczana z `peak_quantity_value`.
14. System nie sumuje różnych jednostek bez zatwierdzonej reguły.
15. `waste_type` i `waste_code` są opcjonalnymi polami PRODUCT i nie tworzą osobnego modułu odpadów.
16. SDS nie istnieje w Core bez PRODUCT ani zaakceptowanego fizycznego PDF w wymaganym języku.
17. Jeden PRODUCT ma maksymalnie jeden zatwierdzony SDS `CURRENT`.
18. Zatwierdzenie nowego SDS archiwizuje poprzedni `CURRENT`.
19. Rewizja i data nie ustalają automatycznie aktualności SDS.
20. SAFETY_PROFILE i SDS_COMPONENT należą do konkretnego `sds_id`.
21. `NO_DATA` nie oznacza `NO`.
22. Dane automatycznie odczytane z PDF wymagają jawnej weryfikacji i akceptacji użytkownika.
23. Odrzucony draft ekstrakcji nie jest zapisywany w Core.
24. Po akceptacji SDS nie jest automatycznie reinterpretowany w tle.
25. BHP_DECISION dotyczy konkretnego PRODUCT i konkretnego `sds_id`.
26. Jeden aktualny rekord decyzji BHP posiada jeden dowód w MVP.
27. Korekta decyzji nie nadpisuje historii; tworzy nowy rekord, a poprzedni staje się `SUPERSEDED`.
28. SDS i dowody BHP są przechowywane w osobnych repozytoriach.
29. Wynik automatycznej analizy nie jest decyzją BHP.
30. Dane znaczące historycznie nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

---

## 20. Otwarte elementy Core

Otwarte pozostają wyłącznie zagadnienia, których zatwierdzone BDR nie rozstrzygają w sposób wystarczający do implementacji:

- szczegółowy techniczny mechanizm historii zmian PRODUCT–USAGE_LOCATION,
- szczegółowa polityka fizycznego usuwania / dezaktywacji stanowisk posiadających historię,
- przyszłe rozwinięcie pól `waste_type` i `waste_code` do modelu gospodarki odpadami — poza Sprintem 2 i poza obecnym MVP.

Punkty te nie upoważniają Codexa do samodzielnego projektowania rozwiązania.

---

## 21. Ochrona Core

Codex nie może bez zatwierdzonej decyzji:

- zmieniać relacji między obiektami Core,
- zmieniać definicji tożsamości PRODUCT,
- pozwalać na zwykłą edycję nazwy, kodu lub producenta istniejącego PRODUCT,
- dodawać nowych statusów lub zmieniać znaczenia istniejących,
- zastępować MANUFACTURER lub USAGE_LOCATION swobodnym tekstem,
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

Zmiana Core wymaga zatwierdzonego ADR lub BDR.

---

## 22. Status dokumentu

Niniejszy dokument jest **zatwierdzoną rewizją CORE-001 v1.0-approved przygotowaną na podstawie BDR-002 v1.1-approved**.

Wersja:

**1.1-approved**

Status:

**Approved**

CORE-001 v1.1-approved jest obowiązującym dokumentem Core projektu MSDS Manager i zastępuje CORE-001 v1.0-approved jako aktualne źródło modelu Core.

---

## 23. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-08-25 | Draft | Pierwszy zbiorczy model Core MSDS Manager |
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono model Core jako obowiązujące źródło wymagań dla implementacji |
| 1.1-approved | 2026-08-28 | Approved | Zatwierdzona rewizja po BDR-002 v1.1-approved: producent w tożsamości PRODUCT, waste_type/waste_code, nowy model PRODUCT_USAGE_LOCATION, monthly consumption, semantyka 0/NULL i perspektywa historii od strony PRODUCT; uaktualniono także agregację o zatwierdzone BDR-004 i BDR-005 |
