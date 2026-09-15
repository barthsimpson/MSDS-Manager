# SPRINT-005 — Widok nadzorczy

**Projekt:** MSDS Manager  
**Sprint ID:** SPRINT-005  
**Wersja:** 0.1-draft  
**Status:** Draft — do zatwierdzenia  
**Etap Roadmapy:** R7 — Widok nadzorczy  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca Tasków:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  

---

## 1. Cel Sprintu

Zbudować jeden prosty widok codziennego nadzoru nad aktualnym stanem produktów chemicznych.

Widok ma pozwolić użytkownikowi szybko odpowiedzieć:

> Które produkty wymagają mojego działania i dlaczego?

Docelowy przebieg:

```text
[ Widok nadzorczy ]
        ↓
lista PRODUCT
        ↓
bieżący stan:
- producent
- miejsca stosowania
- CURRENT SDS
- data / rewizja SDS
- status PRODUCT
- CURRENT decyzja BHP
- notes / warunki
- problemy wymagające działania
        ↓
filtr / identyfikacja problemu
        ↓
użytkownik wie, czym ma się zająć
```

Sprint nie tworzy przeglądów okresowych ani dashboardu analitycznego.

---

## 2. Decyzja poprzedzająca Sprint

R6 — Migracja danych początkowych — zostaje pominięty (`SKIPPED`).

Powód:

- dane ze starego `MSDS_baza.xlsx` nie są wystarczająco wiarygodnym źródłem Core,
- istniejące dane nie będą automatycznie migrowane,
- produkty i ich SDS będą wprowadzane ponownie przez zatwierdzony workflow aplikacji,
- dane operacyjne będą uzupełniane w nowym systemie.

Nie implementować:
- importera Excel,
- stagingu migracyjnego,
- mapowania starej bazy,
- mechanizmu automatycznej korekty danych legacy.

---

## 3. Zasada MVP

R7 ma być przede wszystkim **jedną użyteczną listą**, a nie systemem BI.

Nie budujemy:
- dashboardów,
- wykresów,
- KPI historycznych,
- snapshotów przeglądów,
- harmonogramów,
- powiadomień,
- workflow problemów,
- osobnej tabeli `ISSUE`,
- task managera,
- scoringu ryzyka,
- AI/LLM,
- nowych struktur audytowych.

Widok ma odczytywać i interpretować istniejący Core.

---

## 4. Obowiązujące źródła

Sprint realizuje aktualny zatwierdzony model projektu, w szczególności:

- aktualny `CORE-001`,
- BDR-003 — SDS i wersjonowanie,
- BDR-004 — decyzja BHP,
- BDR-005 — Safety Profile,
- BDR-002 — miejsca stosowania,
- TDR-001,
- TDR-002,
- TDR-003,
- TDR-004,
- zamknięty SPRINT-003,
- zamknięty SPRINT-004,
- CHECKPOINT-004,
- root `AGENTS.md`.

Jeżeli implementacja wymaga zmiany Core lub ujawnia brak decyzji biznesowej:

```text
STOP
```

Codex nie zgaduje.

---

## 5. Stan wejściowy

Po R5 system posiada działający pionowy workflow:

```text
PDF SDS
   ↓
PRODUCT + CURRENT SDS
   ↓
PRODUCT = PENDING_APPROVAL
   ↓
BHP_DECISION + EVIDENCE
   ↓
ACTIVE / REJECTED
```

Dodatkowo istnieją:

- MANUFACTURER,
- USAGE_LOCATION,
- PRODUCT_USAGE_LOCATION,
- SAFETY_PROFILE,
- SDS_COMPONENT,
- historia PRODUCT i danych operacyjnych.

Stan techniczny checkpointu R5:

```text
pytest baseline    138 passed
Alembic head       e0dd7d6468bf
business tables    12
schema drift       none
```

---

## 6. Główny read model widoku

Widok jest zorientowany na `PRODUCT`.

Jeden PRODUCT powinien być reprezentowany jako jeden główny wiersz nadzorczy.

Minimalny zestaw informacji:

```text
PRODUCT
├── product_name
├── manufacturer
├── manufacturer_product_code
├── usage_status
├── use_description
├── use_restriction
├── usage locations
├── CURRENT SDS
│   ├── issue_date
│   ├── revision
│   └── source availability
└── CURRENT BHP_DECISION
    ├── decision_status
    ├── registered_at
    ├── notes
    └── evidence availability
```

Jeżeli PRODUCT posiada wiele miejsc stosowania, widok nie powinien przez to sztucznie powielać produktu na wiele głównych wierszy.

Miejsca mogą być prezentowane jako lista / tekst zagregowany w komórce.

---

## 7. Status SDS w widoku

Widok ma pokazywać aktualny stan dokumentu wynikający z Core.

Minimalnie:

```text
CURRENT
MISSING_FILE
NO_CURRENT_SDS
```

Znaczenie:

### CURRENT

PRODUCT posiada CURRENT SDS i wskazany plik źródłowy jest dostępny.

### MISSING_FILE

Rekord CURRENT SDS istnieje, ale źródłowy PDF nie jest dostępny pod oczekiwaną ścieżką.

Nie usuwa to SDS i nie zmienia historii.

### NO_CURRENT_SDS

Brak CURRENT SDS dla produktu.

Jeżeli obecny Core / workflow uniemożliwia taki stan dla normalnie utworzonego produktu, reguła nadal może być bezpiecznie obsłużona jako kontrola integralności odczytu.

Nie tworzymy nowego statusu w bazie danych tylko na potrzeby UI.

---

## 8. Status BHP w widoku

Status BHP wynika z CURRENT decyzji dotyczącej CURRENT SDS.

Minimalna prezentacja:

```text
APPROVED
REJECTED
NO_DECISION
```

Reguła:

```text
CURRENT SDS
   ↓
CURRENT BHP_DECISION dla tego sds_id
```

Jeżeli brak takiej decyzji:

```text
NO_DECISION
```

Nie należy dziedziczyć decyzji poprzedniego SDS.

---

## 9. Warunki dopuszczenia

Nie tworzymy osobnego strukturalnego modelu warunków.

Widok korzysta z istniejącego:

```text
BHP_DECISION.notes
```

Może pokazywać skróconą treść lub pełny tekst w szczegółach.

Nie analizować automatycznie treści notes.

---

## 10. Problemy wymagające działania

R7 nie tworzy encji `ISSUE`.

Pole / lista:

```text
requires_action
action_reasons
```

jest wartością wyliczaną z aktualnego Core.

Minimalne reguły:

### A. Oczekiwanie na decyzję BHP

```text
PRODUCT.usage_status = PENDING_APPROVAL
```

→ `WYMAGA DZIAŁANIA: BRAK DECYZJI BHP`

### B. Produkt odrzucony

```text
PRODUCT.usage_status = REJECTED
```

→ `WYMAGA UWAGI: PRODUKT ODRZUCONY`

### C. Brak CURRENT SDS

```text
CURRENT SDS = none
```

→ `WYMAGA DZIAŁANIA: BRAK CURRENT SDS`

### D. Brak pliku CURRENT SDS

```text
CURRENT SDS exists
AND source file missing
```

→ `WYMAGA DZIAŁANIA: BRAK PLIKU SDS`

### E. Brak miejsca stosowania

```text
no active PRODUCT_USAGE_LOCATION
```

→ `WYMAGA UZUPEŁNIENIA: BRAK MIEJSCA STOSOWANIA`

### F. Brak dowodu bieżącej decyzji

```text
CURRENT BHP_DECISION exists
AND evidence file missing
```

→ `WYMAGA DZIAŁANIA: BRAK PLIKU DOWODU BHP`

Brak pliku dowodu nie zmienia decyzji BHP ani statusu PRODUCT.

---

## 11. Czego R7 nie uznaje automatycznie za problem

Nie tworzymy problemu wyłącznie dlatego, że:

- PRODUCT jest `INACTIVE`,
- monthly consumption jest `NULL`,
- wartość zużycia wynosi `0`,
- notes jest puste,
- brak osobnego `decided_by`,
- brak osobnego `decision_date`,
- SDS posiada historyczne wersje ARCHIVED,
- BHP posiada decyzje SUPERSEDED.

`INACTIVE` ma być widoczny i możliwy do filtrowania, ale sam status nie oznacza błędu.

---

## 12. Lokalizacja reguł

Warunek Roadmapy R7:

> informacje mają wynikać z Core i zatwierdzonych reguł, a nie z logiki zaszytej w UI.

Dlatego:

```text
PostgreSQL / repositories
        ↓
Application read model / query service
        ↓
wyliczone statusy nadzorcze
        ↓
Streamlit
```

Streamlit:
- wyświetla dane,
- filtruje wynik,
- nie definiuje znaczenia `requires_action`,
- nie wykonuje SQL,
- nie importuje ORM,
- nie interpretuje samodzielnie relacji Core.

---

## 13. Minimalny UI

Nowa pozycja nawigacji:

```text
Widok nadzorczy
```

Minimalna tabela:

| Kolumna | Znaczenie |
|---|---|
| Produkt | PRODUCT.product_name |
| Producent | MANUFACTURER |
| Kod producenta | manufacturer_product_code |
| Miejsca stosowania | aktywne lokalizacje |
| SDS | status CURRENT / missing |
| Data SDS | issue_date |
| Rewizja SDS | revision |
| Status produktu | PENDING_APPROVAL / ACTIVE / INACTIVE / REJECTED |
| BHP | APPROVED / REJECTED / NO_DECISION |
| Warunki / notes | BHP_DECISION.notes |
| Wymaga działania | wynik reguł R7 |

Dopuszczalne jest dostosowanie kolejności/etykiet dla czytelności bez zmiany znaczenia danych.

---

## 14. Filtrowanie

Minimalne filtry:

```text
[ Wszystkie / Wymagają działania ]
[ Status produktu ]
[ Miejsce stosowania ]
```

Opcjonalnie, jeżeli implementacja jest trywialna w istniejącym Streamlit:

```text
wyszukiwanie po nazwie produktu
```

Nie budować zaawansowanego query buildera.

Domyślnie widok powinien umożliwiać szybkie przejście do pozycji wymagających działania.

---

## 15. Zachowanie dla pustej bazy

Widok musi działać także wtedy, gdy baza nie zawiera jeszcze produktów.

Oczekiwany rezultat:

```text
Brak produktów do wyświetlenia.
```

Nie jest to błąd.

Jest to szczególnie istotne, ponieważ dane produkcyjne będą wprowadzane od nowa przez workflow aplikacji.

---

## 16. Dostęp do dokumentów

R7 może wykorzystać istniejące mechanizmy wskazywania dostępności SDS i evidence.

Jeżeli bez zmiany architektury możliwe jest pokazanie ścieżki / informacji umożliwiającej użytkownikowi dotarcie do dokumentu, można ją wyświetlić.

Nie budować w tym Sprincie:
- document viewer,
- upload service,
- download service,
- preview PDF/MSG,
- konwertera dokumentów.

---

## 17. Brak zmian Core jako założenie

SPRINT-005 powinien zostać wykonany jako read-side nad istniejącym modelem.

Założenie:

```text
NO CORE CHANGE
NO SCHEMA CHANGE
NO ALEMBIC MIGRATION
```

Jeżeli Codex stwierdzi, że warunek Sprintu wymaga zmiany Core/schema:

```text
STOP
```

i raportuje konkretny brak.

Nie rozszerza modelu samodzielnie.

---

## 18. Poza zakresem Sprintu

Nie implementujemy:

- R6/importu danych legacy,
- przeglądów okresowych R8,
- snapshotów przeglądów,
- dashboardów,
- wykresów,
- KPI historycznych,
- alertów e-mail,
- powiadomień,
- schedulerów,
- REACH,
- AI/LLM,
- OCR,
- workflow problemów,
- osobnej encji ISSUE,
- scoringu ryzyka,
- nowych tabel historii,
- zmian zasad BHP,
- zmian zasad SDS,
- zmian tożsamości PRODUCT,
- zmian modelu USAGE_LOCATION.

---

## 19. Proponowany backlog

### TASK-026 — Supervisory Read Model & Rules

Zakres:
- DTO/read model jednego wiersza PRODUCT,
- query/application service,
- odczyt MANUFACTURER,
- aktywne USAGE_LOCATION,
- CURRENT SDS,
- CURRENT BHP_DECISION dla CURRENT SDS,
- dostępność pliku SDS,
- dostępność evidence,
- wyliczenie `requires_action` i `action_reasons`,
- testy reguł,
- bez UI,
- bez zmian schema.

Cel:

> Jedno miejsce poza Streamlit potrafi odpowiedzieć, jaki jest aktualny stan nadzorczy każdego produktu.

---

### TASK-027 — Supervisory PostgreSQL Query Integration

Zakres:
- implementacja read-side na istniejących repositories / SQLAlchemy,
- brak N+1 w oczywistym zakresie,
- poprawna agregacja wielu miejsc stosowania bez duplikowania głównego wiersza PRODUCT,
- testy integracyjne PostgreSQL,
- przypadki CURRENT/ARCHIVED,
- CURRENT/SUPERSEDED,
- brak SDS,
- brak decyzji,
- brak plików źródłowych,
- brak aktywnych miejsc stosowania,
- bez zmian schema.

Cel:

> Read model jest poprawnie składany z rzeczywistego Core w PostgreSQL.

Jeżeli istniejąca architektura pozwala bezpiecznie połączyć TASK-026 i TASK-027 bez utraty czytelności, Codex nadal wykonuje je jako dwa osobno autoryzowane Taski; nie łączy ich samodzielnie.

---

### TASK-028 — Streamlit „Widok nadzorczy”

Zakres:
- pozycja nawigacji,
- jedna tabela produktów,
- kolumny Sprintu,
- oznaczenie `Wymaga działania`,
- filtry:
  - wszystkie / wymagają działania,
  - status produktu,
  - miejsce stosowania,
- obsługa pustej bazy,
- thin UI,
- testy Streamlit/AppTest,
- bez SQL/ORM/reguł biznesowych w UI.

Cel:

> Użytkownik otwiera jedną stronę i od razu widzi, które produkty wymagają działania.

---

### TASK-029 — Sprint 5 / R7 End-to-End Acceptance

Kontrolowane scenariusze co najmniej:

1. ACTIVE + CURRENT SDS + APPROVED + evidence + location → bez problemu,
2. PENDING_APPROVAL + CURRENT SDS + brak decyzji → brak decyzji BHP,
3. REJECTED → produkt odrzucony,
4. CURRENT SDS z brakującym PDF → brak pliku SDS,
5. CURRENT decyzja z brakującym evidence → brak pliku dowodu BHP,
6. produkt bez aktywnego miejsca stosowania → brak miejsca stosowania,
7. wiele miejsc stosowania → jeden główny wiersz PRODUCT,
8. historyczny ARCHIVED SDS nie zastępuje CURRENT,
9. historyczna SUPERSEDED decyzja nie zastępuje CURRENT,
10. filtry działają,
11. pusta baza działa,
12. pełna regresja,
13. Alembic bez driftu,
14. cleanup fixture.

Cel:

> Potwierdzić na rzeczywistym PostgreSQL i rzeczywistym UI, że jedna lista poprawnie pokazuje bieżący stan i produkty wymagające działania.

---

## 20. Definition of Done Sprintu 5

Sprint jest gotowy do closure, gdy:

1. istnieje widok `Widok nadzorczy`,
2. widok jest zorientowany na PRODUCT,
3. jeden PRODUCT nie jest powielany przez wiele miejsc stosowania,
4. widoczna jest nazwa produktu,
5. widoczny jest producent,
6. widoczny jest kod producenta,
7. widoczne są aktywne miejsca stosowania,
8. widoczny jest status PRODUCT,
9. widoczny jest CURRENT SDS,
10. widoczna jest data SDS, jeśli istnieje,
11. widoczna jest rewizja SDS, jeśli istnieje,
12. sygnalizowany jest brak pliku CURRENT SDS,
13. widoczny jest status bieżącej decyzji BHP dla CURRENT SDS,
14. brak decyzji jest jawnie widoczny,
15. notes bieżącej decyzji może być odczytane,
16. sygnalizowany jest brak pliku evidence,
17. PENDING_APPROVAL jest oznaczone jako wymagające działania,
18. REJECTED jest oznaczone jako wymagające uwagi,
19. brak aktywnego miejsca stosowania jest jawnie widoczny,
20. `requires_action` i `action_reasons` nie są definiowane w Streamlit,
21. można filtrować po `Wymagają działania`,
22. można filtrować po statusie PRODUCT,
23. można filtrować po miejscu stosowania,
24. pusta baza jest obsłużona,
25. UI nie wykonuje SQL i nie importuje ORM,
26. nie utworzono encji ISSUE ani workflow problemów,
27. nie utworzono dashboardów/przeglądów R8,
28. nie zmieniono Core,
29. nie zmieniono schema/Alembic,
30. testy TASK-029 E2E przechodzą,
31. pełna regresja przechodzi,
32. Alembic pozostaje bez driftu.

---

## 21. Kryterium sukcesu biznesowego

Sprint 5 ma zakończyć się sytuacją:

> **Użytkownik otwiera MSDS Manager i na jednej liście widzi bieżący stan produktów oraz od razu rozpoznaje, które pozycje wymagają działania i z jakiego powodu.**

Nie musi wykonywać ręcznej kontroli kolejnych ekranów produktu, SDS i BHP tylko po to, aby wykryć podstawowe braki.

---

## 22. Stan końcowy oczekiwany

```text
                  WIDOK NADZORCZY

PRODUCT A   ACTIVE             OK
PRODUCT B   PENDING_APPROVAL   BRAK DECYZJI BHP
PRODUCT C   ACTIVE             BRAK MIEJSCA STOSOWANIA
PRODUCT D   REJECTED           PRODUKT ODRZUCONY
PRODUCT E   ACTIVE             BRAK PLIKU SDS
PRODUCT F   ACTIVE             BRAK PLIKU DOWODU BHP
```

Widok jest projekcją bieżącego Core.

Nie tworzy własnego równoległego stanu biznesowego.

---

## 23. Bramka STOP

Codex zatrzymuje Task i raportuje `BLOCKED`, jeżeli:

- potrzebna okazuje się zmiana Core,
- potrzebna okazuje się migracja schema,
- nie można jednoznacznie wyznaczyć CURRENT SDS,
- nie można jednoznacznie powiązać CURRENT BHP_DECISION z CURRENT SDS,
- wymaganie wymusza nową decyzję biznesową,
- implementacja wymaga stworzenia nowego trwałego statusu/problem entity.

Nie obchodzi blokera przez lokalną logikę w Streamlit.

---

## 24. Autoryzacja

Dokument Sprintu nie stanowi automatycznej zgody na wykonanie Tasków.

Po zatwierdzeniu każdy Task wymaga osobnego polecenia Architekta Operacyjnego:

```text
Wykonaj TASK-026
```

Obecność pliku Task w repo nie oznacza autoryzacji wykonania.

Po zatwierdzeniu Sprint może otrzymać status:

```text
SPRINT-005 v1.0-approved
```

---

## 25. Uwagi do Roadmapy

Oryginalny ROADMAP-001 opisywał R7 szerzej, używając m.in. pojęć `producent/dostawca`, `status dokumentacji` i `warunki dopuszczenia`.

SPRINT-005 interpretuje te wymagania przez aktualny zatwierdzony Core:

```text
producent/dostawca
→ MANUFACTURER
→ bez SUPPLIER

status dokumentacji
→ stan CURRENT SDS + dostępność źródłowego PDF

status BHP
→ CURRENT BHP_DECISION dla CURRENT SDS

warunki dopuszczenia
→ BHP_DECISION.notes

nierozstrzygnięte problemy
→ wyliczone action_reasons
→ bez osobnej encji ISSUE
```

Jest to świadome zawężenie do rzeczywiście zatwierdzonego i zaimplementowanego Core.
