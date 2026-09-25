# SPRINT-006 — Operacyjny UI MVP

**Projekt:** MSDS Manager  
**Sprint ID:** SPRINT-006  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Etap Roadmapy:** R9 — domknięcie operacyjnego MVP 1.0  
**R8 — Przeglądy okresowe:** DEFERRED  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca Tasków:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  
**Data zatwierdzenia:** 2026-09-25  

---

## 1. Cel Sprintu

Przekształcić istniejący, funkcjonalny interfejs Streamlit w prosty i wygodny interfejs codziennej pracy.

Sprint nie buduje nowych funkcji domenowych.

Ma uporządkować sposób korzystania z funkcji, które już działają:

```text
PRODUCT
→ SDS
→ kolejne rewizje SDS
→ decyzja BHP
→ miejsca stosowania i ilości
→ widok nadzorczy
→ korekta / usunięcie błędnego wpisu
```

Cel użytkowy:

> Operator ma pracować głównie na czytelnych tabelach i szczegółach wybranego rekordu, a nie na długich formularzach, technicznych identyfikatorach i wielu niepowiązanych kontrolkach.

---

## 2. Stan wejściowy

Po fizycznym walkthrough MVP potwierdzono działanie głównych procesów:

```text
pierwszy SDS → nowy PRODUCT
nowa rewizja SDS → ten sam PRODUCT
CURRENT → ARCHIVED
nowy CURRENT → PENDING_APPROVAL
decyzja BHP → ACTIVE / REJECTED
PRODUCT ↔ wiele miejsc stosowania
peak quantity / monthly consumption
edycja danych produktu
bezpieczne usunięcie omyłkowego PRODUCT
```

Seria PATCH-003…PATCH-008 została fizycznie zweryfikowana.

Parser PDF pozostaje funkcją pomocniczą.

Jeżeli parser działa:

```text
→ podpowiada dane
```

Jeżeli parser nie działa lub odczytuje dane niepoprawnie:

```text
→ użytkownik uzupełnia dane ręcznie
→ główny workflow nadal działa
```

Automatyczny odczyt PDF jest **secondary target**, nie warunkiem użyteczności MVP.

---

## 3. Kierunek wizualny

UI ma przypominać desktopową aplikację operacyjną, a nie dashboard marketingowy.

Przyjmujemy styl:

```text
szeroki
zwarty
tabelaryczny
informacyjny
stabilny
nastawiony na szybkie wykonanie pracy
```

Inspiracja dostarczonymi ekranami referencyjnymi:

- duża szerokość robocza,
- mało pustej przestrzeni,
- czytelne sekcje,
- cienkie separatory,
- zwarte tabele,
- filtry blisko danych,
- akcje w kontekście rekordu,
- statusy łatwe do odczytania,
- szczegóły podporządkowane rejestrowi.

Nie kopiujemy:

- złożoności referencyjnego systemu,
- rozbudowanych paneli,
- wielopoziomowego menu,
- nadmiaru ikon,
- logiki CRM/task managera.

---

## 4. Zasady UI Sprintu

### UI-1 — Wide layout

Aplikacja używa dostępnej szerokości ekranu.

Preferowane:

```text
Streamlit layout = wide
```

Nie budować głównych formularzy jako bardzo wąskiej kolumny na środku szerokiego monitora.

### UI-2 — Table first

Dla rejestrów obowiązuje:

```text
tabela
→ wybór rekordu
→ szczegóły / akcje
```

Nie:

```text
tabela
+ osobny dropdown z tymi samymi rekordami
+ długa lista danych
```

jeżeli technicznie można uzyskać stabilny wybór rekordu z tabeli.

### UI-3 — Business data first

W głównym UI pokazujemy dane biznesowe.

Techniczne UUID:

```text
product_id
sds_id
decision_id
...
```

nie są normalnym identyfikatorem dla użytkownika.

UUID pozostaje w systemie, ale ma być ukryty w codziennym widoku.

Jeżeli jest potrzebny do diagnostyki, może być dostępny w:

```text
Dane techniczne
```

lub równoważnym rozwijanym obszarze.

### UI-4 — Compact forms

Formularze dzielimy logicznie na sekcje i wykorzystujemy szerokość ekranu.

Preferowane:

```text
2 kolumny
krótkie grupy pól
opcjonalne dane w expanderach
```

Nie tworzyć jednej długiej pionowej kolumny, jeżeli pola naturalnie mogą być zestawione obok siebie.

### UI-5 — Required fields are visible

Pole wymagane powinno być dla użytkownika rozpoznawalne przed próbą zapisu.

Preferowane:

```text
Nazwa produktu *
Producent *
Opis zastosowania *
```

Nie czekać wyłącznie na komunikat błędu po kliknięciu `Zapisz / Akceptuj`.

Nie zmieniać przy tym istniejącego kontraktu walidacji.

### UI-6 — Actions belong to selected record

Akcje typu:

```text
Edytuj produkt
Dodaj nową rewizję SDS
Usuń produkt
```

mają być czytelnie związane z aktualnie wybranym produktem.

Akcje destrukcyjne pozostają wizualnie oddzielone i zabezpieczone potwierdzeniem.

### UI-7 — No stale state

Po operacji zmieniającej stan aplikacja ma od razu pokazać aktualny rezultat.

Przykład:

```text
BHP APPROVED
→ PRODUCT = ACTIVE
```

Po zapisie UI nie może nadal pokazywać starego `PENDING_APPROVAL`.

### UI-8 — Source paths are secondary

Pełne ścieżki filesystemu nie są podstawową informacją użytkową.

W normalnym widoku pokazujemy:

```text
nazwa pliku
status dostępności
```

Ścieżkę techniczną można udostępnić jako detal.

---

## 5. Ekran „Produkty”

### 5.1. Rejestr

Głównym elementem jest tabela produktów.

Minimalne kolumny:

| Kolumna | Znaczenie |
|---|---|
| Produkt | nazwa |
| Kod producenta | kod produktu |
| Producent | producent |
| Status | status użytkowania |
| SDS | podstawowy stan CURRENT SDS |
| BHP | bieżący stan decyzji |

Nie pokazujemy UUID w głównej tabeli.

### 5.2. Wybór produktu

Docelowo:

```text
kliknięcie / wybór wiersza
→ Szczegóły produktu
```

Jeżeli używana wersja Streamlit nie daje stabilnego row-selection bez nieuzasadnionych zmian technicznych, dopuszczalny jest prosty fallback selekcji, ale nie należy dublować rejestru bez potrzeby.

### 5.3. Szczegóły produktu

Po wyborze produktu pokazujemy sekcje:

```text
Tożsamość
SDS
BHP
Miejsca stosowania
Dane administracyjne
Akcje
```

Nie wszystkie formularze muszą być stale rozwinięte.

### 5.4. Akcje

Dostępne funkcje istniejące:

```text
Edytuj dane produktu
Dodaj nową rewizję SDS
Usuń produkt
```

Nie zmieniać reguł PATCH-006, PATCH-007 i PATCH-008.

---

## 6. Ekran „Dodaj SDS”

### 6.1. Cel

Skrócić i uporządkować formularz pierwszego SDS.

### 6.2. Sekcje

Preferowany układ:

```text
[ Dokument SDS ]
plik | data | rewizja

[ Produkt ]
nazwa | kod producenta
producent
opis zastosowania | ograniczenia

[ Dane bezpieczeństwa — opcjonalne ]
Safety Profile
Składniki
```

Chemia pozostaje opcjonalna w MVP.

### 6.3. Parser

Parser:

```text
Odczytaj dane
```

pozostaje pomocą.

UI powinien jasno pozwalać użytkownikowi poprawić wszystkie odczytane dane przed zapisem.

Nie rozwijać parsera w tym Sprincie.

### 6.4. Komunikat sukcesu

Po zapisie preferowany komunikat:

```text
SDS został zapisany.
Produkt oczekuje na decyzję BHP.
```

Nie pokazujemy technicznego UUID w podstawowym komunikacie sukcesu.

---

## 7. Nowa rewizja SDS

Workflow pozostaje:

```text
istniejący PRODUCT
→ Dodaj nową rewizję SDS
→ nowy CURRENT
→ poprzedni CURRENT = ARCHIVED
→ PRODUCT = PENDING_APPROVAL
```

UI ma:

- jednoznacznie pokazać wybrany produkt,
- pokazać wybrany plik,
- pozwolić podać rewizję,
- pozwolić podać datę dokumentu.

### Ważna korekta UX

Jeżeli data SDS nie została odczytana:

```text
NIE podstawiaj automatycznie dzisiejszej daty
```

Pole powinno pozostać puste / nieustalone zgodnie z istniejącym kontraktem.

Data rejestracji w systemie nie jest datą wydania SDS.

---

## 8. Ekran „Miejsca stosowania”

### 8.1. Istniejące przypisania

Najpierw pokaż tabelę:

| Lokalizacja | Maks. ilość | Jednostka | Zużycie miesięczne | Jednostka |
|---|---:|---|---:|---|
| Regeneracja | 25 | l | 100 | l |
| MZT_Mag.Techniczny | 300 | l | 10 | l |

### 8.2. Dodawanie

Pod tabelą / po akcji:

```text
+ Dodaj miejsce stosowania
```

otwiera osobny formularz.

### 8.3. Edycja

Wybór istniejącego przypisania:

```text
→ Edytuj przypisanie
```

Nie mieszamy w jednym formularzu:

```text
istniejących przypisań
+
nowego przypisania
+
edycji innego przypisania
```

### 8.4. Etykiety

Używać języka użytkowego:

```text
Maksymalna ilość na stanowisku
Zużycie miesięczne
Jednostka
```

zamiast technicznych etykiet typu:

```text
Peak quantity nowego przypisania
```

---

## 9. Widok nadzorczy — zmiana prezentacji

### 9.1. Nowa jednostka wiersza

SPRINT-006 świadomie zmienia prezentacyjne założenie SPRINT-005.

Było:

```text
1 PRODUCT = 1 wiersz
lokalizacje agregowane
```

Po fizycznym walkthrough przyjmujemy:

```text
1 PRODUCT × 1 USAGE_LOCATION = 1 wiersz nadzorczy
```

Powód:

- czytelniejsze filtrowanie po lokalizacji,
- widoczna maksymalna ilość dla konkretnego miejsca,
- widoczne zużycie miesięczne dla konkretnego miejsca,
- brak nieczytelnej listy lokalizacji w jednej komórce.

To jest zmiana read modelu / prezentacji.

Nie zmienia Core ani relacji PRODUCT ↔ USAGE_LOCATION.

### 9.2. Produkt bez miejsca stosowania

Produkt bez aktywnego miejsca nadal musi być widoczny:

```text
Produkt | Lokalizacja = Brak
```

i zachowuje istniejące `requires_action`.

### 9.3. Minimalne kolumny

| Kolumna | Znaczenie |
|---|---|
| Produkt | nazwa |
| Producent | producent |
| Kod | kod producenta |
| Lokalizacja | konkretne miejsce |
| Maks. ilość | peak_quantity |
| Jedn. | peak_unit |
| Zużycie mies. | monthly_consumption |
| Jedn. | monthly_unit |
| SDS | status |
| Data SDS | issue_date |
| Rewizja | revision |
| Produkt | usage_status |
| BHP | bieżąca decyzja |
| Warunki | notes |
| Wymaga działania | action reasons |

### 9.4. Filtry

Minimalnie:

```text
Szukaj produktu
Status produktu
Lokalizacja
BHP
Wszystkie / Wymagają działania
```

Filtry mają być blisko tabeli.

Nie budować query buildera.

---

## 10. Ekran „Decyzja BHP”

### 10.1. Kontekst

Na górze jasno pokazujemy:

```text
Produkt
CURRENT SDS
rewizję / datę
```

### 10.2. Dowód

W MVP pozostaje obecny model plików w `BHP_EVIDENCE_ROOT_PATH`.

Sprint nie implementuje nowego upload/storage service.

UI ma natomiast jasno pokazywać:

```text
Wybrany dowód
nazwa pliku
status dostępności
```

i unikać eksponowania pełnej ścieżki jako podstawowej informacji.

### 10.3. Po zapisie

Po decyzji:

```text
APPROVED → ACTIVE
REJECTED → REJECTED
```

ekran ma natychmiast odświeżyć aktualny stan produktu.

Nie może pozostać stary status w kontrolce wyboru lub nagłówku.

---

## 11. Nawigacja

Nawigacja ma być:

```text
stała
krótka
przewidywalna
```

Podstawowe obszary:

```text
Widok nadzorczy
Produkty
Dodaj SDS
Decyzja BHP
Stanowiska
```

Nie tworzyć wielopoziomowego menu.

Nie dodawać modułów R8/R10/R11.

---

## 12. Statusy

Statusy biznesowe mogą otrzymać czytelne etykiety / badge, np.:

```text
ACTIVE             → Aktywny
PENDING_APPROVAL   → Oczekuje na BHP
REJECTED           → Odrzucony
INACTIVE           → Nieaktywny

APPROVED           → Dopuszczony
REJECTED           → Niedopuszczony
NO_DECISION        → Brak decyzji
```

Wewnętrzne wartości domenowe pozostają bez zmian.

Kolor jest pomocą prezentacyjną, nie niesie nowej logiki biznesowej.

---

## 13. Czego Sprint NIE robi

Nie implementujemy:

- nowej logiki Core,
- zmiany schema,
- migracji Alembic,
- nowych tabel,
- React,
- FastAPI,
- nowego systemu CSS/frameworka UI,
- upload/storage service,
- automatycznego kopiowania plików,
- OCR,
- ulepszeń parsera,
- alias dictionary,
- nowych danych Safety Profile,
- REACH,
- R8 przeglądów okresowych,
- dashboardów KPI,
- wykresów,
- powiadomień,
- systemu ról/uprawnień,
- merge/deduplication,
- nowego systemu identyfikatorów biznesowych w bazie.

Techniczne UUID mają być ukryte prezentacyjnie; nie tworzymy przez to nowej kolumny/schema.

---

## 14. Architektura

Sprint pozostaje zgodny z zasadą:

```text
presentation
→ application
→ domain
→ infrastructure
```

UI:

- nie wykonuje bezpośredniego SQL,
- nie definiuje reguł lifecycle,
- nie interpretuje Core na nowo,
- może wykonywać wyłącznie logikę prezentacyjną.

Jeżeli nowy widok wymaga read modelu:

```text
repository/query
→ application read model
→ Streamlit
```

---

## 15. Plan Tasków

### TASK-029 — UI Foundation + Rejestr produktów

**MODE:** INTEGRATION

Zakres:

- wide layout,
- podstawowe zasady wspólnego wyglądu,
- zwarta nawigacja,
- tabela `Produkty`,
- ukrycie UUID w normalnym widoku,
- wybór produktu z tabeli lub minimalny techniczny fallback,
- uporządkowane sekcje szczegółów,
- akcje produktu w kontekście rekordu,
- komunikaty sukcesu bez UUID.

Nie zmieniać funkcjonalności produktu.

---

### TASK-030 — Formularze SDS i BHP

**MODE:** INTEGRATION

Zakres:

- uporządkowanie `Dodaj SDS`,
- required-field visibility,
- wykorzystanie szerokości ekranu,
- chemia w sekcji opcjonalnej,
- uporządkowanie `Nowa rewizja SDS`,
- brak automatycznej dzisiejszej daty SDS,
- uporządkowanie kontekstu decyzji BHP,
- czytelna nazwa dowodu,
- natychmiastowy refresh statusu po decyzji.

Bez zmian parsera i lifecycle.

---

### TASK-031 — Miejsca stosowania + Widok nadzorczy

**MODE:** INTEGRATION

Zakres:

- tabela istniejących przypisań,
- oddzielny formularz dodania/edycji,
- przyjazne etykiety ilości,
- read model `PRODUCT × USAGE_LOCATION`,
- peak quantity,
- monthly consumption,
- produkt bez lokalizacji nadal widoczny,
- filtry nadzorcze,
- kompaktowa tabela operacyjna.

Bez zmian schema/Core.

---

### TASK-032 — UI MVP Acceptance / Checkpoint

**MODE:** ACCEPTANCE

Zakres:

- pełny walkthrough UI,
- sprawdzenie wszystkich głównych workflow,
- pełna regresja,
- E2E,
- SAWarning,
- Alembic current/check,
- schema/integrity,
- kontrola braku zmian Core/schema,
- kontrola pustej bazy / stanów NO_DATA,
- Sprint Review.

TASK-032 nie dodaje nowych funkcji.

Jeżeli acceptance ujawni defekt:

```text
STOP
→ raport
→ decyzja Architekta Operacyjnego
```

Nie wykonywać opportunistic fixes w checkpoint.

---

## 16. Kolejność wykonania

```text
TASK-029
   ↓
TASK-030
   ↓
TASK-031
   ↓
TASK-032 ACCEPTANCE
```

Taski wykonywane są wyłącznie po osobnej jawnej autoryzacji.

---

## 17. Walidacja Sprintu

### Functional

Należy potwierdzić co najmniej:

```text
PRODUCT register
PRODUCT details
first SDS
new SDS revision
BHP decision
product status refresh
usage locations
peak/monthly quantities
supervisory view
product correction
safe product deletion
```

### UI

Należy potwierdzić:

```text
brak UUID w normalnym workflow
brak niepotrzebnych pełnych ścieżek
czytelne pola wymagane
brak stale state
czytelny PRODUCT × LOCATION
brak pomieszania add/edit usage
formularze wykorzystują szerokość ekranu
```

### Regression

Na końcu Sprintu:

```text
full pytest
E2E
PostgreSQL integration
Alembic current/check
schema integrity
SAWarning review
```

zgodnie z `GOV-002` LEVEL 3.

---

## 18. Definition of Done

SPRINT-006 jest zakończony, gdy:

1. aplikacja używa szerokiego, zwartego layoutu,
2. `Produkty` działa jako rejestr tabelaryczny z czytelnymi szczegółami,
3. techniczne UUID nie dominują w UI,
4. `Dodaj SDS` jest krótszy i logicznie podzielony,
5. pola wymagane są rozpoznawalne przed zapisem,
6. nowa rewizja SDS nie podpowiada fałszywie bieżącej daty dokumentu,
7. ekran BHP pokazuje aktualny stan po zapisie,
8. miejsca stosowania mają osobną tabelę i formularz,
9. widok nadzorczy pokazuje `PRODUCT × LOCATION`,
10. peak/monthly są widoczne w widoku nadzorczym,
11. produkt bez lokalizacji nie znika z nadzoru,
12. filtry działają na nowym read modelu,
13. nie zmieniono Core/schema,
14. pełna walidacja checkpointu przechodzi,
15. fizyczny Sprint Review zostaje zaakceptowany przez Architekta Operacyjnego.

---

## 19. STOP CONDITIONS

Codex zatrzymuje wykonanie Tasku, jeżeli:

1. wymagana jest zmiana Core,
2. wymagana jest zmiana schema/migracja,
3. wymaganie UI wymaga nowej reguły biznesowej,
4. row-selection wymaga niezatwierdzonej zmiany frameworka/dependency,
5. zmiana wymaga nowego storage/upload service,
6. implementacja zaczyna wymagać repo-wide refactor,
7. konieczne staje się rozwijanie parsera.

Nie rozszerzać zakresu.

---

## 20. Decyzje świadomie odroczone

Poza tym Sprintem pozostają:

```text
R8 — przeglądy okresowe
Stage 2 — parser / automatyczna analiza SDS
REACH
nowy frontend
upload/storage service
zaawansowane uprawnienia
```

---

## 21. Kryterium sukcesu

Po Sprint Review użytkownik powinien móc powiedzieć:

> Funkcjonalnie system robi to samo co przed Sprintem, ale codzienna praca jest wyraźnie szybsza, czytelniejsza i mniej techniczna.

Nie mierzymy sukcesu liczbą nowych funkcji.

Mierzymy go redukcją tarcia w istniejącym procesie.

---

## 22. Authorization

SPRINT-006 został zatwierdzony przez Architekta Operacyjnego.

Sprint nie uruchamia automatycznie żadnego Tasku.

Kolejny krok:

```text
przygotować TASK-029 — UI Foundation + Rejestr produktów
```

Start implementacji TASK-029 dopiero po jawnym poleceniu:

```text
Wykonaj TASK-029.
```

---

## 23. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-25 | Draft | Pierwsza wersja Sprintu UI MVP |
| 1.0-approved | 2026-09-25 | Approved | Zatwierdzenie przez Architekta Operacyjnego bez zmian zakresu |

