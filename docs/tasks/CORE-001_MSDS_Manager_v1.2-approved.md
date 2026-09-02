# CORE-001 — Model Core projektu MSDS Manager

**Projekt:** MSDS Manager  
**Id dokumentu:** CORE-001  
**Wersja:** 1.2-approved  
**Status:** Approved  
**Data rewizji:** 2026-09-02  
**Dokument bazowy:** CORE-001 v1.1-approved  
**Właściciel:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

## 1. Cel dokumentu

CORE-001 opisuje chroniony model domenowy MSDS Manager i agreguje zatwierdzone zasady dotyczące PRODUCT, MANUFACTURER, USAGE_LOCATION, PRODUCT_USAGE_LOCATION, SDS, SAFETY_PROFILE, SDS_COMPONENT, BHP_DECISION, DECISION_EVIDENCE oraz zasad audytowalności.

Rewizja v1.2 włącza do Core decyzję `BDR-002 v1.2-approved` dotyczącą statusu i cyklu życia `USAGE_LOCATION`.

CORE-001 nie zastępuje ADR, BDR ani TDR. Jest skonsolidowanym obrazem obowiązującego Core.

## 2. Zasada nadrzędna

Centralnym obiektem systemu jest **PRODUCT — produkt chemiczny**.

Nie plik PDF ani stanowisko.

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

Równolegle:

```text
PRODUCT
   ↓
PRODUCT_USAGE_LOCATION
   ↓
USAGE_LOCATION
```

`USAGE_LOCATION` jest osobną encją relacyjnej bazy, ale biznesowo opisuje PRODUCT: gdzie produkt jest używany.

## 3. PRODUCT

### 3.1. Identyfikator

Każdy produkt posiada niezmienny `product_id`.

### 3.2. Tożsamość biznesowa

Tożsamość produktu tworzą:

- `product_name`,
- `manufacturer_product_code`,
- `manufacturer_id`.

**Nowa nazwa, nowy kod/numer produktu lub inny producent = nowy rekord PRODUCT.**

Pola te nie są zwykłymi polami administracyjnie edytowalnymi.

### 3.3. Dane administracyjnie edytowalne

- `use_description`,
- `use_restriction`,
- `usage_status`,
- `waste_type`,
- `waste_code`.

`waste_type` i `waste_code` pozostają opcjonalnymi polami informacyjnymi PRODUCT i nie tworzą osobnego modułu gospodarki odpadami.

### 3.4. Status stosowania PRODUCT

Dozwolone statusy MVP:

- `PENDING_APPROVAL`,
- `ACTIVE`,
- `REJECTED`,
- `INACTIVE`.

Znaczenie statusów pozostaje zgodne z zatwierdzonymi BDR dotyczącymi produktu, SDS i decyzji BHP.

## 4. MANUFACTURER

```text
MANUFACTURER
├── manufacturer_id
└── manufacturer_name
```

Relacja:

```text
MANUFACTURER 1:N PRODUCT
```

Dostawca handlowy pozostaje poza Core.

## 5. USAGE_LOCATION

Miejsca stosowania są osobną tabelą/słownikiem stanowisk.

```text
USAGE_LOCATION
├── location_id
├── location_name
└── status
```

Relacja:

```text
PRODUCT N:M USAGE_LOCATION
```

Biznesową perspektywą aplikacji pozostaje PRODUCT.

### 5.1. Status USAGE_LOCATION

Dozwolone statusy:

```text
ACTIVE
INACTIVE
```

Status `USAGE_LOCATION` jest osobnym pojęciem domenowym. Nie wolno używać `ProductUsageStatus` jako statusu lokalizacji, nawet jeśli oba słowniki zawierają wartości `ACTIVE` i `INACTIVE`.

Znaczenie:

- `ACTIVE` — lokalizacja aktualnie funkcjonuje, może być używana w nowych przypisaniach PRODUCT–USAGE_LOCATION i uczestniczy w bieżącej analityce;
- `INACTIVE` — lokalizacja wycofana z bieżącego użytkowania; pozostaje w bazie i historii, nie może być używana do nowych przypisań i nie uczestniczy w bieżącej analityce aktualnych miejsc stosowania.

### 5.2. Status początkowy

Nowo utworzona `USAGE_LOCATION` otrzymuje:

```text
ACTIVE
```

### 5.3. Cykl życia

Dozwolone przejścia:

```text
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

```text
CreateUsageLocation
        ↓
      ACTIVE
        │
        │ deactivate
        ↓
     INACTIVE
        │
        │ reactivate
        ↓
      ACTIVE
```

Bez osobnej decyzji nie wprowadza się dodatkowych statusów typu `DELETED`, `ARCHIVED`, `SUSPENDED`, `CLOSED`.

### 5.4. Dezaktywacja

`ACTIVE → INACTIVE` oznacza wycofanie lokalizacji z bieżącego użytkowania.

Dezaktywacja:

- nie usuwa fizycznie rekordu,
- nie zmienia `location_id`,
- zachowuje znaczenie historyczne.

Lokalizacja posiadająca znaczenie historyczne nie może zostać fizycznie usunięta tylko dlatego, że została zlikwidowana w zakładzie.

### 5.5. Reaktywacja

`INACTIVE → ACTIVE` jest dopuszczalne.

Reaktywacja:

- wykorzystuje istniejący rekord,
- zachowuje `location_id`,
- nie tworzy nowej lokalizacji wyłącznie z powodu wcześniejszej dezaktywacji.

### 5.6. Nowe przypisania

Nowe przypisanie PRODUCT może zostać utworzone wyłącznie dla:

```text
USAGE_LOCATION.status = ACTIVE
```

`INACTIVE` nie jest dostępne do nowych bieżących przypisań.

### 5.7. Bieżąca analityka

Bieżące widoki i analizy aktualnych miejsc stosowania uwzględniają wyłącznie lokalizacje `ACTIVE`.

`INACTIVE` pozostaje dostępne dla historii, ale nie wpływa na bieżącą analitykę.

Szczegółowy techniczny mechanizm historii zmian pozostaje nierozstrzygnięty.

## 6. PRODUCT_USAGE_LOCATION

```text
PRODUCT_USAGE_LOCATION
├── product_id
├── location_id
├── peak_quantity_value
├── peak_quantity_unit
├── monthly_consumption_value
└── monthly_consumption_unit
```

Istnienie relacji oznacza przypisanie stanowiska do produktu.

### 6.1. Ilość szczytowa

`peak_quantity_value`:

- obowiązkowe,
- `Decimal`,
- `>= 0`.

`peak_quantity_unit` jest obowiązkowe.

`0` jest prawidłową wartością biznesową.

### 6.2. Miesięczne zużycie

`monthly_consumption_value`:

- opcjonalne,
- `Decimal`,
- jeśli podane: `>= 0`.

Jeśli wartość jest podana, `monthly_consumption_unit` jest obowiązkowe.

```text
NULL → brak zadeklarowanej informacji
0    → świadomie zadeklarowane zerowe zużycie
> 0  → zadeklarowane dodatnie zużycie
```

## 7. Jednostki i peak_factory_quantity

System nie wykonuje automatycznej konwersji jednostek.

```text
peak_factory_quantity(product)
=
Σ peak_quantity_value
```

dla `USAGE_LOCATION.status = ACTIVE` i wyłącznie dla zgodnych jednostek.

Lokalizacje `INACTIVE` nie wchodzą do bieżącej wartości `peak_factory_quantity`.

`monthly_consumption_value` nie wchodzi do tej sumy.

## 8. SDS

Każdy zarejestrowany SDS:

- posiada PRODUCT,
- posiada fizyczny PDF,
- otrzymuje `sds_id`.

```text
brak PRODUCT → brak rekordu SDS
brak PDF     → brak rekordu SDS
```

Dla obecnego wdrożenia przyjmowany jest wyłącznie SDS w wymaganym języku polskim.

## 9. Metadane i status SDS

Minimalnie:

- `sds_id`,
- `product_id`,
- `original_filename`,
- `relative_path`,
- `issue_date`,
- `revision`,
- `status`,
- `registered_at`.

Statusy:

- `CURRENT`,
- `ARCHIVED`.

Jeden PRODUCT może posiadać maksymalnie jeden zatwierdzony SDS `CURRENT`.

## 10. SAFETY_PROFILE

`SAFETY_PROFILE` należy do konkretnego `sds_id`.

Zakres MVP obejmuje zatwierdzone dane z Sekcji 2 i 11, zgodnie z BDR-005.

Dla właściwych pól:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

`NO_DATA` nie oznacza `NO`.

## 11. SDS_COMPONENT

Składniki Sekcji 3 są przechowywane jako relacja 1:N do konkretnego SDS.

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

## 12. Ekstrakcja i akceptacja SDS

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

Odrzucony draft nie jest zapisywany w Core.

Po akceptacji zapisuje się `approved_at`, automatyczne przetwarzanie danego SDS kończy się, a późniejsza ręczna edycja aktualizuje `last_manual_edit_at`.

## 13. BHP_DECISION

Decyzja BHP dotyczy konkretnego PRODUCT i konkretnego zatwierdzonego SDS.

Wynik:

- `APPROVED`,
- `REJECTED`.

Status rekordu:

- `CURRENT`,
- `SUPERSEDED`.

Nowy zatwierdzony SDS wymaga nowej decyzji BHP.

## 14. DECISION_EVIDENCE

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Dopuszczalne formaty:

- `.msg`,
- `.pdf`,
- `.jpg`,
- `.jpeg`,
- `.png`.

## 15. Repozytoria plików

```text
SDS_ROOT_PATH
BHP_EVIDENCE_ROOT_PATH
```

Aplikacja referencjonuje pliki źródłowe i ich nie modyfikuje.

## 16. Historia i audytowalność

Core musi zachowywać historię co najmniej:

- produktów,
- statusu stosowania,
- wersji SDS,
- statusów SDS `CURRENT / ARCHIVED`,
- decyzji BHP,
- dowodów decyzji,
- powiązań PRODUCT z USAGE_LOCATION,
- zmian statusu USAGE_LOCATION,
- `peak_quantity`,
- `monthly_consumption`,
- przeglądów.

W obszarze PRODUCT–USAGE_LOCATION perspektywą nadrzędną historii jest PRODUCT.

Zmiana `USAGE_LOCATION.status` pomiędzy `ACTIVE` i `INACTIVE` nie może niszczyć informacji o historycznym wykorzystaniu lokalizacji.

Szczegółowy techniczny mechanizm historyzacji pozostaje otwartą decyzją.

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
│      ├── CURRENT / ARCHIVED
│      ├── SAFETY_PROFILE 1:1
│      └── SDS_COMPONENT 1:N
│
├── N:M USAGE_LOCATION
│      ├── location_id
│      ├── location_name
│      ├── status: ACTIVE / INACTIVE
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

## 19. Reguły integralności Core

1. `PRODUCT` zawsze posiada `product_id`.
2. Nowa nazwa, kod/numer lub producent = nowy PRODUCT.
3. Pola tożsamości PRODUCT nie są zwykłymi polami administracyjnie edytowalnymi.
4. MANUFACTURER jest osobną encją 1:N względem PRODUCT.
5. USAGE_LOCATION jest osobną encją; PRODUCT i USAGE_LOCATION pozostają w relacji N:M.
6. `USAGE_LOCATION.status` posiada wyłącznie `ACTIVE` albo `INACTIVE`.
7. Nowa USAGE_LOCATION otrzymuje `ACTIVE`.
8. Dozwolone przejścia to `ACTIVE → INACTIVE` oraz `INACTIVE → ACTIVE`.
9. `ProductUsageStatus` i status USAGE_LOCATION są odrębnymi pojęciami domenowymi.
10. `INACTIVE` nie może być używane do nowych przypisań PRODUCT.
11. `INACTIVE` nie uczestniczy w bieżącej analityce.
12. Dezaktywacja nie usuwa rekordu.
13. Reaktywacja zachowuje `location_id`.
14. Historycznie używana lokalizacja nie może zostać fizycznie usunięta tylko wskutek jej likwidacji.
15. Istnienie PRODUCT_USAGE_LOCATION oznacza przypisanie stanowiska do produktu.
16. `peak_quantity_value >= 0` i jest obowiązkowe.
17. `peak_quantity_unit` jest obowiązkowe.
18. `monthly_consumption_value` jest opcjonalne i jeśli podane `>= 0`.
19. `monthly_consumption_unit` jest obowiązkowe, gdy podano wartość.
20. `0` nie oznacza braku danych.
21. `monthly_consumption_value = NULL` oznacza brak zadeklarowanej informacji.
22. `peak_factory_quantity` jest liczone wyłącznie dla aktywnych lokalizacji.
23. System nie sumuje różnych jednostek bez zatwierdzonej reguły.
24. `waste_type` i `waste_code` nie tworzą osobnego modułu odpadów.
25. SDS nie istnieje bez PRODUCT i zaakceptowanego PDF.
26. Jeden PRODUCT ma maksymalnie jeden SDS `CURRENT`.
27. Zatwierdzenie nowego SDS archiwizuje poprzedni `CURRENT`.
28. SAFETY_PROFILE i SDS_COMPONENT należą do konkretnego `sds_id`.
29. `NO_DATA` nie oznacza `NO`.
30. Odrzucony draft ekstrakcji nie jest zapisywany w Core.
31. Po akceptacji SDS nie jest automatycznie reinterpretowany.
32. BHP_DECISION dotyczy konkretnego PRODUCT i `sds_id`.
33. Jeden aktualny rekord BHP_DECISION posiada jeden dowód.
34. Korekta decyzji tworzy nowy rekord, a poprzedni staje się `SUPERSEDED`.
35. SDS i dowody BHP są przechowywane w osobnych repozytoriach.
36. Wynik automatycznej analizy nie jest decyzją BHP.
37. Dane znaczące historycznie nie mogą być fizycznie usuwane bez zatwierdzonej reguły.

## 20. Otwarte elementy Core

Otwarte pozostają:

- techniczny mechanizm historii zmian PRODUCT–USAGE_LOCATION i USAGE_LOCATION,
- polityka fizycznego usuwania lokalizacji, które nigdy nie zostały wykorzystane i nie mają znaczenia historycznego,
- przyszłe rozwinięcie `waste_type` i `waste_code` do modelu gospodarki odpadami.

Zasada dla lokalizacji posiadających znaczenie historyczne jest rozstrzygnięta: nie mogą być fizycznie usuwane wskutek likwidacji lub dezaktywacji.

## 21. Ochrona Core

Codex nie może bez zatwierdzonej decyzji:

- zmieniać relacji Core,
- zmieniać tożsamości PRODUCT,
- dodawać nowych statusów lub zmieniać znaczenia istniejących,
- używać `ProductUsageStatus` jako statusu USAGE_LOCATION,
- dodawać statusów USAGE_LOCATION innych niż `ACTIVE` i `INACTIVE`,
- tworzyć nowych przypisań produktu do `INACTIVE`,
- uwzględniać `INACTIVE` w bieżącej analityce,
- fizycznie usuwać lokalizacji posiadających znaczenie historyczne,
- automatycznie przeliczać jednostek,
- zmieniać reguł SDS i BHP,
- tworzyć mechanizmu historii bez osobnej decyzji.

Zmiana Core wymaga zatwierdzonego ADR lub BDR.

## 22. Konsekwencje implementacyjne rewizji v1.2

BDR-002 v1.2-approved wymaga kontrolowanego wyrównania:

```text
Domain
→ osobny UsageLocationStatus

ORM
→ status ograniczony do ACTIVE / INACTIVE

PostgreSQL
→ constraint dla zatwierdzonych wartości

Alembic
→ wersjonowana migracja

Application
→ Create / Deactivate / Reactivate zgodnie z Core

Tests
→ Domain + PostgreSQL + application
```

Zmiana schematu nie może zostać wprowadzona „przy okazji” Tasku, który jej zabrania.

Ponieważ TASK-009 zatrzymał się poprawnie na braku decyzji, przed pełnym wznowieniem TASK-009 wymagany jest kontrolowany alignment Domain/ORM/PostgreSQL.

## 23. Status dokumentu

Niniejszy dokument jest rewizją `CORE-001 v1.1-approved` przygotowaną na podstawie `BDR-002 v1.2-approved`.

**Wersja:** 1.2-approved  
**Status:** Draft — do zatwierdzenia przez Architekta Operacyjnego

`CORE-001 v1.2-approved` jest obowiązującym dokumentem Core projektu i zastępuje `CORE-001 v1.1-approved` jako aktualny skonsolidowany model Core.

## 24. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-08-25 | Draft | Pierwszy zbiorczy model Core MSDS Manager |
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono model Core jako obowiązujące źródło wymagań dla implementacji |
| 1.1-approved | 2026-08-28 | Approved | Producent w tożsamości PRODUCT, waste_type/waste_code, nowy model PRODUCT_USAGE_LOCATION, monthly consumption, semantyka 0/NULL i perspektywa historii od strony PRODUCT |
| 1.2-approved | 2026-09-02 | Approved | Osobny status USAGE_LOCATION `ACTIVE/INACTIVE`, status początkowy ACTIVE, dezaktywacja i reaktywacja, zachowanie location_id, zakaz usuwania lokalizacji historycznych, wyłączenie INACTIVE z nowych przypisań i bieżącej analityki oraz konsekwencje alignment Domain/ORM/PostgreSQL |
