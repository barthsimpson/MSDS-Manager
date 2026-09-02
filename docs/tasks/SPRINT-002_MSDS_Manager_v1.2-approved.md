# SPRINT-002 — Rejestr produktów i miejsc stosowania

**Projekt:** MSDS Manager  
**Sprint ID:** SPRINT-002  
**Wersja:** 1.2-approved  
**Status:** Approved  
**Data rewizji:** 2026-08-31  
**Dokument bazowy:** SPRINT-002 v1.1-approved  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca Tasków:** Codex OpenAI  

## 1. Powód rewizji

SPRINT-002 v1.1-approved zakładał możliwość samodzielnego tworzenia PRODUCT i MANUFACTURER w workflow rejestru produktów.

Po doprecyzowaniu procesu przyjmujemy:

> **Nowy PRODUCT nie jest tworzony przez osobny formularz „Dodaj produkt”. Powstaje jako część zatwierdzonego procesu „Dodaj nowy SDS”.**

Centralnym obiektem biznesowym nadal pozostaje PRODUCT, ale workflow rejestracji nowego środka chemicznego inicjuje SDS.

## 2. Docelowy przebieg rejestracji nowego środka

```text
[ Dodaj nowy SDS ]
        ↓
walidacja dokumentu
        ↓
odczyt danych wg CORE
        ↓
identyfikacja:
- PRODUCT
- MANUFACTURER
- SDS
- SAFETY_PROFILE
- SDS_COMPONENT
        ↓
kontrola potencjalnego duplikatu
        ↓
DRAFT
        ↓
weryfikacja użytkownika
        ↓
AKCEPTUJ / NIE AKCEPTUJ
```

Po `NIE AKCEPTUJ`:
```text
brak nowego PRODUCT w Core
brak nowego SDS w Core
draft nie jest zachowywany w Core
```

Po `AKCEPTUJ`:
```text
PRODUCT + SDS + zatwierdzone dane
        ↓
PRODUCT.usage_status = PENDING_APPROVAL
SDS.document_status  = CURRENT
        ↓
oczekiwanie na decyzję BHP
```

Po zarejestrowaniu decyzji BHP:
```text
APPROVED → PRODUCT.usage_status = ACTIVE
REJECTED → PRODUCT.usage_status = REJECTED
```

Nie wprowadza się nowego statusu `REGISTERED`.

## 3. Konsekwencja dla Sprintu 2

SPRINT-002 nadal realizuje etap R3: **Rejestr produktów i miejsc stosowania**.

Jednak Sprint 2:
- nie implementuje samodzielnego workflow tworzenia PRODUCT,
- nie implementuje publicznego `CreateProduct`,
- nie implementuje publicznego `CreateManufacturer`,
- nie wprowadza produktu do Core bez SDS.

SPRINT-002 implementuje funkcje pracy z **już istniejącym PRODUCT**:
- lista produktów,
- szczegóły produktu,
- edycja danych administracyjnych,
- producent jako powiązana encja,
- miejsca stosowania,
- ilości szczytowe,
- zużycie miesięczne,
- dane odpadowe,
- historię istotnych zmian w zatwierdzonym później zakresie.

Faktyczne utworzenie nowego PRODUCT będzie częścią etapu workflow SDS.

## 4. Cel biznesowy Sprintu

Po zakończeniu Sprintu 2 system ma być gotowy do operacyjnego zarządzania produktem utworzonym przez workflow SDS.

Dla istniejącego PRODUCT użytkownik ma móc odpowiedzieć:

> **Co to jest, kto jest producentem, gdzie i do czego jest stosowane, jaka jest zadeklarowana ilość szczytowa i jakie jest orientacyjne miesięczne zużycie?**

## 5. PRODUCT pozostaje nadrzędnym obiektem

Po utworzeniu PRODUCT użytkownik pracuje przede wszystkim od strony produktu:

```text
PRODUCT
├── producent
├── kod produktu
├── status
├── przeznaczenie
├── ograniczenia
├── waste_type
├── waste_code
└── miejsca stosowania
     ├── peak quantity
     └── monthly consumption
```

`USAGE_LOCATION` pozostaje osobną encją relacyjnej bazy.

## 6. Tożsamość PRODUCT

Tożsamość biznesową PRODUCT tworzą:
- `product_name`,
- `manufacturer_product_code`,
- `manufacturer_id`.

Nowa nazwa, nowy kod/numer produktu lub inny producent oznacza nowy PRODUCT.

Pola te nie są edytowane jako zwykłe dane administracyjne istniejącego produktu.

## 7. MANUFACTURER

MANUFACTURER pozostaje osobną encją 1:N względem PRODUCT.

SPRINT-002 umożliwia:
- odczyt listy producentów,
- użycie producenta w widokach PRODUCT,
- techniczne repozytorium/port potrzebny do odczytu producenta.

Samodzielne tworzenie producenta przez użytkownika nie jest wymaganiem Sprintu 2.

Nowy MANUFACTURER może zostać utworzony później w workflow akceptacji SDS, gdy zaakceptowany draft wskazuje producenta, którego nie ma w bazie.

## 8. USAGE_LOCATION

USAGE_LOCATION pozostaje osobnym słownikiem stanowisk.

SPRINT-002 może obejmować:
- listę stanowisk,
- dodawanie stanowiska,
- dezaktywację stanowiska,
- przypisywanie stanowiska do istniejącego PRODUCT.

Ta funkcja nie tworzy PRODUCT.

## 9. PRODUCT_USAGE_LOCATION

Relacja przechowuje:
```text
product_id
location_id
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Reguły Core pozostają bez zmian:
- `peak_quantity_value >= 0`,
- `peak_quantity_unit` wymagane,
- `monthly_consumption_value` opcjonalne i jeśli podane `>= 0`,
- `monthly_consumption_unit` wymagane, gdy istnieje wartość,
- `0` jest wartością biznesową,
- `NULL` oznacza brak zadeklarowanej informacji,
- brak automatycznej konwersji jednostek.

## 10. Dane administracyjnie edytowalne PRODUCT

Po utworzeniu PRODUCT przez workflow SDS użytkownik może edytować:
- `use_description`,
- `use_restriction`,
- `usage_status` wyłącznie zgodnie z zatwierdzonym procesem,
- `waste_type`,
- `waste_code`,
- przypisania do USAGE_LOCATION,
- peak quantity,
- monthly consumption.

SPRINT-002 nie może wprowadzać workflow statusów sprzecznego z SDS/BHP.

## 11. Granica statusu PRODUCT

SPRINT-002 nie tworzy własnego początkowego statusu produktu.

Produkt wprowadzony przez zatwierdzony workflow SDS otrzymuje:
```text
PENDING_APPROVAL
```

Po decyzji BHP:
```text
APPROVED → ACTIVE
REJECTED → REJECTED
```

`INACTIVE` pozostaje statusem wyłączenia produktu ze stosowania.

Sprint 2 nie implementuje jeszcze przejścia SDS/BHP.

## 12. Poza zakresem Sprintu 2

Poza zakresem pozostają:
- `Dodaj nowy SDS`,
- ekstrakcja PDF,
- tworzenie PRODUCT z draftu SDS,
- tworzenie MANUFACTURER z draftu SDS,
- rejestracja SDS,
- SAFETY_PROFILE,
- SDS_COMPONENT,
- kontrola duplikatu w workflow wejściowym,
- decyzja BHP,
- dowód decyzji BHP,
- przejście `PENDING_APPROVAL → ACTIVE/REJECTED`,
- REACH,
- import produkcyjny Excel,
- moduł gospodarki odpadami,
- BDO.

## 13. Stan po TASK-008

TASK-008 został zakończony i zaakceptowany.

```text
Domain                  Core v1.1 aligned
ORM                     Core v1.1 aligned
Alembic                 3 revisions
PostgreSQL              c41d8e2f7a90 (head)
Application tables      9
Tests                   59 passed
Schema drift            none
```

TASK-008 nie wymaga korekty.

## 14. Skorygowany backlog Sprintu 2

### TASK-009 — Product & Usage Application Contracts
Zdefiniować minimalne porty, DTO i use case'y do pracy z istniejącym PRODUCT.

Preferowany zakres:
```text
ListProducts
GetProductDetails
UpdateProductAdministrativeData

ListManufacturers

ListUsageLocations
CreateUsageLocation
DeactivateUsageLocation

AssignProductUsageLocation
UpdateProductUsageLocation
```

Nie implementować publicznego:
```text
CreateProduct
CreateManufacturer
```

Nie implementować workflow SDS.

### TASK-010 — SQLAlchemy Repositories + Transaction Boundary
Persistence dla use case'ów TASK-009:
- ProductRepository,
- Manufacturer read repository,
- UsageLocationRepository,
- ProductUsageLocation persistence,
- mapping ORM ↔ Domain/DTO,
- transakcje,
- rollback,
- testy PostgreSQL.

Bez tworzenia PRODUCT.

### TASK-011 — Product Business Rules & Integration Tests
Testować:
- odczyt istniejącego produktu,
- ochronę pól tożsamości,
- edycję danych administracyjnych,
- przypisanie jednej/wielu lokalizacji,
- `peak_quantity = 0`,
- monthly `NULL`,
- monthly `0`,
- odrzucenie wartości ujemnych,
- brak konwersji jednostek,
- rollback.

Nie testować publicznego `CreateProduct`.

### TASK-012 — Minimal Streamlit Shell
Pierwszy użytkowy shell Streamlit.

UI może posiadać sekcje:
```text
Produkty
Stanowiska
```

Nie posiada jeszcze:
```text
Dodaj nowy produkt
Dodaj nowy SDS
```

### TASK-013 — Product Registry View
Widok listy i szczegółów istniejących produktów:
- nazwa,
- kod,
- producent,
- status,
- przeznaczenie,
- ograniczenia,
- waste_type,
- waste_code,
- miejsca stosowania,
- peak quantity,
- monthly consumption.

Na pustej bazie poprawny stan:
```text
Brak zarejestrowanych produktów.
```

### TASK-014 — Product Administration & Usage Workflow
Dla istniejącego PRODUCT:
- edycja danych administracyjnych,
- zarządzanie miejscami stosowania,
- peak quantity,
- monthly consumption,
- pola waste.

Bez zmiany tożsamości i bez tworzenia nowego PRODUCT.

### TASK-015 — Product History Mechanism
Task warunkowy. Nie rozpoczynać bez zatwierdzonej decyzji technicznej dotyczącej historii.

### TASK-016 — Sprint 2 End-to-End Acceptance
Scenariusz korzysta z kontrolowanego testowego PRODUCT utworzonego wyłącznie przez setup testu.

1. uruchom aplikację,
2. baza posiada kontrolowany testowy PRODUCT,
3. otwórz listę produktów,
4. otwórz szczegóły,
5. edytuj dozwolone dane administracyjne,
6. przypisz co najmniej 2 miejsca stosowania,
7. zapisz peak quantities,
8. zapisz monthly consumption,
9. odczytaj zmienione dane,
10. potwierdź PostgreSQL,
11. potwierdź historię w zatwierdzonym zakresie,
12. rollback/usuń dane testowe.

Nie dodawać publicznego `CreateProduct`.

## 15. Kolejność

```text
TASK-008  Core alignment                    ACCEPTED
   ↓
TASK-009  Application contracts
   ↓
TASK-010  Repositories + transactions
   ↓
TASK-011  Business/integration rules
   ↓
TASK-012  Streamlit shell
   ↓
TASK-013  Product registry
   ↓
TASK-014  Product administration
   ↓
[DECYZJA HISTORII]
   ↓
TASK-015  History mechanism
   ↓
TASK-016  E2E + Sprint closure
```

## 16. Definition of Done — skorygowana

SPRINT-002 jest zakończony, gdy:
1. aplikacja wyświetla listę istniejących produktów,
2. wyświetla szczegóły produktu,
3. prezentuje producenta,
4. pola tożsamości są chronione,
5. można edytować dozwolone dane administracyjne,
6. działają `waste_type` i `waste_code`,
7. istnieje osobny słownik stanowisk,
8. można dodać/dezaktywować stanowisko,
9. istniejący produkt można przypisać do wielu stanowisk,
10. można zapisać `peak_quantity >= 0`,
11. można zapisać opcjonalne `monthly_consumption >= 0`,
12. `0` i `NULL` zachowują zatwierdzoną semantykę,
13. UI nie omija application,
14. PostgreSQL pozostaje źródłem danych operacyjnych,
15. historia istotnych zmian działa w zatwierdzonym zakresie,
16. testy przechodzą,
17. E2E przechodzi na kontrolowanych danych testowych,
18. nie istnieje publiczny workflow samodzielnego `CreateProduct`,
19. nie rozpoczęto implementacji SDS/BHP/AI/REACH.

SPRINT-002 nie wymaga możliwości utworzenia nowego produktu przez użytkownika.

Ta możliwość powstanie w workflow:
```text
Dodaj nowy SDS
→ ekstrakcja
→ DRAFT
→ akceptacja
→ PRODUCT + SDS
```

## 17. Wpływ na kolejne etapy

Korekta nie zmienia centralności PRODUCT. Zmienia wyłącznie inicjację jego cyklu życia.

```text
R3 / SPRINT-002
Rejestr i zarządzanie istniejącym PRODUCT
        ↓
R4
Dodaj nowy SDS
→ utworzenie / identyfikacja PRODUCT
→ wersjonowanie SDS
        ↓
R5
Decyzja BHP
→ ACTIVE / REJECTED
```

## 18. Ryzyka kontrolowane

- brak sztucznego `CreateProduct`,
- brak nowego statusu produktu bez SDS,
- testowe tworzenie PRODUCT nie staje się funkcją użytkownika,
- PRODUCT pozostaje centralnym obiektem mimo inicjacji workflow przez SDS.

## 19. Status rewizji

```text
SPRINT-002
VERSION: 1.2-approved
STATUS: APPROVED
REASON: PRODUCT lifecycle initiated by SDS workflow
```

## 20. Historia zmian

| Wersja | Status | Zmiana |
|---|---|---|
| 1.1-approved | Approved | Sprint 2 po CORE-001 v1.1; zakładał samodzielny CreateProduct |
| 1.2-approved | Approved | Usunięto publiczny CreateProduct/CreateManufacturer z R3; doprecyzowano, że nowy PRODUCT powstaje jako część workflow „Dodaj nowy SDS”; skorygowano TASK-009..016 i DoD; rewizja zatwierdzona przez Architekta Operacyjnego 2026-08-31. |
