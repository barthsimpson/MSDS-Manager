# BDR-002 — Decyzja uzupełniająca: cykl życia USAGE_LOCATION

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-002  
**Wersja:** 1.2-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-31  
**Dokument bazowy:** BDR-002 v1.1-approved  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  

---

## 1. Cel rewizji

Celem rewizji jest jednoznaczne określenie statusów i cyklu życia `USAGE_LOCATION`.

Decyzja usuwa blocker ujawniony podczas TASK-009, wynikający z tego, że zatwierdzony model zawierał pole:

```text
USAGE_LOCATION.status
```

oraz zasadę wycofywania stanowisk z bieżącego użycia, ale nie określał dozwolonych wartości statusu ani przejść między nimi.

---

## 2. Dozwolone statusy USAGE_LOCATION

Dla `USAGE_LOCATION` zatwierdza się dwa statusy:

```text
ACTIVE
INACTIVE
```

Statusy te dotyczą wyłącznie `USAGE_LOCATION`.

Nie należy wykorzystywać do tego celu `ProductUsageStatus`, mimo występowania w nim nazw `ACTIVE` i `INACTIVE`.

---

## 3. Znaczenie statusu ACTIVE

```text
USAGE_LOCATION.status = ACTIVE
```

oznacza, że lokalizacja / stanowisko:

- fizycznie funkcjonuje,
- jest dostępne do bieżącego użytkowania,
- może być wybierane przy nowych przypisaniach PRODUCT–USAGE_LOCATION,
- uczestniczy w bieżących widokach i analizach dotyczących aktualnych miejsc stosowania.

Nowo utworzona `USAGE_LOCATION` otrzymuje status:

```text
ACTIVE
```

---

## 4. Znaczenie statusu INACTIVE

```text
USAGE_LOCATION.status = INACTIVE
```

oznacza, że lokalizacja / stanowisko zostało wycofane z bieżącego użytkowania.

Lokalizacja `INACTIVE`:

- pozostaje w bazie danych,
- zachowuje swoją tożsamość `location_id`,
- zachowuje znaczenie dla historii,
- nie może być wybierana do nowych bieżących przypisań produktu,
- nie uczestniczy w bieżącej analityce aktualnych miejsc stosowania.

Status `INACTIVE` nie oznacza usunięcia rekordu.

---

## 5. Dezaktywacja

Dopuszczalne przejście:

```text
ACTIVE → INACTIVE
```

Operacja odpowiada fizycznemu wycofaniu / likwidacji stanowiska lub lokalizacji z bieżącego użytkowania.

Dezaktywacja nie powoduje fizycznego usunięcia `USAGE_LOCATION`.

---

## 6. Reaktywacja

Ponowne uruchomienie wcześniej wycofanej lokalizacji jest dopuszczalne.

Dopuszczalne przejście:

```text
INACTIVE → ACTIVE
```

Reaktywacja wykorzystuje istniejący rekord `USAGE_LOCATION` i jego `location_id`.

Nie tworzy nowej lokalizacji wyłącznie z powodu jej wcześniejszej dezaktywacji.

---

## 7. Cykl życia

Minimalny cykl życia:

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

Nie wprowadza się dodatkowych statusów takich jak:

```text
DELETED
ARCHIVED
SUSPENDED
CLOSED
```

bez osobnej zatwierdzonej decyzji.

---

## 8. Zakaz fizycznego usuwania

Lokalizacja, która została wykorzystana w systemie i posiada znaczenie historyczne, nie może zostać fizycznie usunięta z powodu jej likwidacji w zakładzie.

Podstawową operacją biznesową jest:

```text
deactivate
```

a nie:

```text
delete
```

Pozwala to zachować możliwość odtworzenia informacji, gdzie produkt był wcześniej stosowany.

Szczegółowa techniczna implementacja historii pozostaje poza zakresem tej decyzji.

---

## 9. Bieżąca analityka

Bieżące analizy dotyczące aktualnego wykorzystania produktów uwzględniają wyłącznie:

```text
USAGE_LOCATION.status = ACTIVE
```

Lokalizacje `INACTIVE` pozostają dostępne dla historii, lecz nie mogą wpływać na bieżące wyniki dotyczące aktualnych miejsc stosowania.

W szczególności zasada sumowania aktualnej ilości szczytowej produktu pozostaje:

```text
peak_factory_quantity(product)
=
Σ peak_quantity_value
```

dla **aktywnych miejsc stosowania** i zgodnych jednostek.

---

## 10. Nowe przypisania produktu

Nowe przypisanie:

```text
PRODUCT → USAGE_LOCATION
```

może zostać utworzone wyłącznie dla:

```text
USAGE_LOCATION.status = ACTIVE
```

Lokalizacja `INACTIVE` nie jest dostępna do nowych bieżących przypisań.

Reaktywacja lokalizacji przywraca możliwość jej wykorzystania w nowych przypisaniach.

---

## 11. Granica historii

Niniejsza decyzja określa:

- bieżący status lokalizacji,
- dozwolone przejścia statusów,
- zachowanie rekordu po fizycznym wycofaniu lokalizacji,
- wpływ statusu na bieżące wykorzystanie i analitykę.

Nie określa technicznego mechanizmu historii zmian.

Nie tworzy:

- tabel historii,
- event logu,
- snapshotów,
- triggerów,
- wersjonowania temporalnego.

Mechanizm historii pozostaje przedmiotem osobnej decyzji przed TASK-015.

---

## 12. Rozstrzygnięcie blockera TASK-009

Po zatwierdzeniu decyzji TASK-009 może przyjąć:

```text
CreateUsageLocation
→ status = ACTIVE

DeactivateUsageLocation
→ ACTIVE → INACTIVE

ReactivateUsageLocation
→ INACTIVE → ACTIVE
```

`ListUsageLocations` może prezentować oba statusy.

Kontrakty przeznaczone do wyboru lokalizacji dla nowego przypisania PRODUCT powinny udostępniać wyłącznie lokalizacje `ACTIVE`.

TASK-009 może zostać wznowiony jako ten sam Task.

---

## 13. Zmiana wymagana w CORE-001

Sekcję `5. USAGE_LOCATION` w `CORE-001 v1.1-approved` należy rozszerzyć o następującą treść:

### 5.x. Status i cykl życia USAGE_LOCATION

Dozwolone statusy:

```text
ACTIVE
INACTIVE
```

Nowa lokalizacja otrzymuje `ACTIVE`.

Znaczenie:

- `ACTIVE` — lokalizacja aktualnie funkcjonuje, może być używana w nowych przypisaniach produktu i uczestniczy w bieżącej analityce;
- `INACTIVE` — lokalizacja wycofana z bieżącego użytkowania; pozostaje w bazie i historii, nie może być używana do nowych przypisań i nie uczestniczy w bieżącej analityce.

Dozwolone przejścia:

```text
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Dezaktywacja nie usuwa fizycznie rekordu.

Ponowne uruchomienie lokalizacji powoduje reaktywację istniejącego rekordu, a nie utworzenie nowego wyłącznie z powodu wcześniejszej dezaktywacji.

Lokalizacje mające znaczenie historyczne nie mogą być fizycznie usuwane wskutek ich likwidacji w zakładzie.

Szczegółowy mechanizm historii pozostaje nierozstrzygnięty i wymaga osobnej decyzji.

---

## 14. Ochrona Core

Codex nie może bez nowej zatwierdzonej decyzji:

- dodawać innych statusów `USAGE_LOCATION`,
- wykorzystywać `ProductUsageStatus` jako enuma lokalizacji,
- fizycznie usuwać historycznie używanych lokalizacji,
- pozwalać na nowe przypisania produktu do lokalizacji `INACTIVE`,
- uwzględniać lokalizacji `INACTIVE` w bieżącej analityce aktualnych miejsc stosowania,
- tworzyć mechanizmu historii w ramach tej decyzji.

---

## 15. Wpływ na implementację

Decyzja wymaga odzwierciedlenia w:

- Domain — osobny status/enumeracja dla `USAGE_LOCATION`,
- ORM — zatwierdzone wartości statusu,
- PostgreSQL — constraint / migracja zgodna z przyjętym modelem,
- application contracts TASK-009,
- testach domenowych i integracyjnych.

Zmiana schema powinna zostać wykonana przez Alembic zgodnie z TDR-001.

Ponieważ TASK-009 został zaprojektowany jako Task bez zmian schema, implementacja wymaganej zmiany Domain/ORM/PostgreSQL powinna zostać wykonana w kontrolowanym kroku alignment przed lub podczas formalnie zatwierdzonego wznowienia TASK-009 — bez samodzielnego rozszerzania zakresu przez Codex.

---

## 16. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Producent, miejsca stosowania, ilość na stanowisku i sumaryczna ilość szczytowa fabryki |
| 1.1-approved | 2026-08-28 | Approved | Tożsamość PRODUCT, nowe ilości, pola odpadowe i kierunek historii |
| 1.2-approved | 2026-08-31 | Approved | Statusy `ACTIVE/INACTIVE` dla USAGE_LOCATION, dezaktywacja i reaktywacja, zakaz usuwania historycznych lokalizacji oraz wyłączenie INACTIVE z bieżącej analityki |
