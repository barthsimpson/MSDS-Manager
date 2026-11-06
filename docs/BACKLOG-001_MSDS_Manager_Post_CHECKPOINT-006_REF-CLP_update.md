# BACKLOG-001 — MSDS Manager — Post CHECKPOINT-006

**Projekt:** MSDS Manager  
**Dokument:** BACKLOG-001  
**Status:** OPEN / CONSOLIDATED  
**Punkt odniesienia:** `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED.md`  
**Data utworzenia:** 2026-09-28  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

---

## 1. Cel dokumentu

Dokument konsoliduje otwarte wątki ujawnione podczas i po SPRINT-006.

Nie jest Sprintem. Nie jest Taskiem. Nie autoryzuje implementacji i nie przesądza kolejności realizacji.

Jego rolą jest:

```text
zachować otwarte potrzeby
→ oddzielić ustalenia od pytań otwartych
→ uniknąć utraty kontekstu
→ przygotować bazę do wyboru kolejnego obszaru prac
```

Każdy punkt wymaga później osobnej decyzji:

```text
wybór priorytetu
→ ewentualny BDR/TDR
→ Sprint
→ Task
→ jawna autoryzacja
```

---

## 2. Baseline po CHECKPOINT-006

SPRINT-006 został zamknięty jako zaakceptowany baseline UI MVP.

Stan referencyjny:

```text
PRODUCT
→ SDS
→ rewizje SDS
→ BHP
→ miejsca stosowania
→ ilości
→ widok nadzorczy
```

Końcowa walidacja:

```text
213 passed
0 failed
0 errors
0 skipped
SAWarning: NONE
Alembic current: head
Alembic check: no drift
cleanup: PASS
operator data preserved: YES
```

Nie stwierdzono realnego production defect w pięciu porażkach pierwszego przebiegu TASK-032.

---

# 3. Rejestr backlogu

## ANALYTICS-01 — Zakładka `Analizy`

**Status:** DECISION NEEDED / BUSINESS DIRECTION APPROVED  
**Typ:** nowy obszar funkcjonalny  
**Wpływ:** UI + read model + prawdopodobnie schema dla przeglądów historycznych

### Potrzeba

W aplikacji brakuje zakładki umożliwiającej zbiorczy nadzór nad substancjami w formie zbliżonej do dotychczasowego arkusza Excel.

Istotną cechą starego rozwiązania jest:

```text
produkt / środek
×
miejsce stosowania
```

w jednej szerokiej macierzy.

### Ustalone

Zakładka `Analizy` ma docelowo zawierać dwa różne raporty:

```text
1. Zestawienie zbiorcze
2. Stan na dzień
```

Raporty mają podobną macierzową formę, ale różne znaczenie biznesowe.

### Nieustalone

- finalny układ zakładki,
- zakres filtrów,
- eksport,
- dokładne nazwy nagłówków,
- finalny model danych dla snapshotów,
- uprawnienia / autor zatwierdzenia,
- reguły edycji draftu przeglądu.

Nie projektować tych elementów bez nowej decyzji.

---

## ANALYTICS-02 — Zestawienie zbiorcze

**Status:** BUSINESS LOGIC APPROVED / DESIGN NOT STARTED  
**Typ:** raport dynamiczny  
**Wpływ:** UI + read model

### Znaczenie

Raport pokazuje **aktualny stan referencyjny wynikający z danych zatwierdzonych w `Produkty`**.

Jednostka prezentacji:

```text
PRODUCT × USAGE_LOCATION
```

### Ustalone

Komórka raportu pokazuje:

```text
maksymalną ilość produktu
dla danego miejsca stosowania
```

Źródło:

```text
PRODUCT_USAGE_LOCATION.peak_quantity
```

Raport:

```text
nie służy do wpisywania miesięcznego zużycia
nie zmienia danych produktu
nie tworzy snapshotu sam z siebie
```

### Powiązanie ze `Stan na dzień`

Po zatwierdzeniu `Stanu na dzień` Zestawienie zbiorcze ma otrzymać automatyczną informację pomocniczą:

```text
+ / - różnica
```

porównującą wartość MAX z ilością stwierdzoną w zatwierdzonym przeglądzie.

Przykład prezentacyjny:

```text
MAX: 40 l
Stan na dzień: 45 l
Różnica: +5 l
```

lub skrótowo:

```text
40 l   (+5)
```

### Zasada graniczna

Różnica jest **podpowiedzią informacyjną**.

Nie powoduje:

```text
automatycznej aktualizacji MAX
automatycznej decyzji
automatycznej oceny zgodności
```

Użytkownik sam analizuje różnicę i ewentualnie ręcznie zmienia dane w `Produkty`.

### Nieustalone

- czy prezentować wartość ostatniego przeglądu zawsze, czy tylko różnicę,
- sposób wizualnego wyróżnienia,
- zachowanie przy zmianie jednostki,
- sposób obsługi produktów bez ostatniego zatwierdzonego przeglądu.

---

## ANALYTICS-03 — `Stan na dzień`

**Status:** BUSINESS LOGIC APPROVED / REQUIRES BDR + DATA MODEL  
**Typ:** historyczny przegląd / snapshot  
**Wpływ:** Core-adjacent business data + schema + UI

### Znaczenie

`Stan na dzień` jest ręcznie wykonywanym przeglądem fizycznego stanu substancji w zakładzie.

Jest odpowiednikiem szybkiego przeglądu wykonywanego dotąd w Excelu.

### Ustalone

Użytkownik wpisuje ręcznie:

```text
ilość stwierdzoną
dla PRODUCT × LOCATION
```

`Stan na dzień`:

```text
nie obejmuje miesięcznego zużycia
nie aktualizuje automatycznie maksymalnej ilości
```

Po zatwierdzeniu przegląd staje się historycznym snapshotem.

### Snapshot po zatwierdzeniu

Dla każdej pozycji logicznie wymagane są co najmniej:

```text
PRODUCT
LOCATION
data przeglądu
wartość bazowa MAX
jednostka
ilość stwierdzona
```

Różnica:

```text
observed_quantity - baseline_max_quantity
```

może być wyliczana.

### Zasada historyczna

Po zatwierdzeniu przeglądu późniejsza zmiana MAX w `Produkty` nie może zmieniać historycznego obrazu przeglądu.

Przykład:

```text
28.09.2026
MAX w chwili przeglądu: 40 l
stan stwierdzony:       45 l
różnica:                +5 l
```

Jeżeli później MAX zostanie ręcznie zmienione do 50 l, historyczny przegląd nadal pokazuje bazę 40 l.

### Nieustalone

- statusy robocze i finalne,
- kto zatwierdza,
- czy zapisujemy `approved_at`,
- czy dopuszczamy cofnięcie zatwierdzenia,
- czy zatwierdzony snapshot jest absolutnie immutable,
- sposób obsługi pustej komórki / „nie sprawdzono”,
- sposób obsługi nowych/usuniętych lokalizacji,
- migracja i constraints.

Te elementy wymagają osobnej decyzji biznesowej / BDR.

---

# 4. Dokumenty SDS

## UI-11 — Otwieranie / pobieranie CURRENT SDS

**Status:** OPEN  
**Typ:** ergonomia dokumentowa  
**Wpływ:** UI + filesystem

### Potrzeba

Użytkownik powinien móc z poziomu produktu / tabeli otworzyć CURRENT SDS bez ręcznego wyszukiwania pliku w katalogu.

### Ustalone

Funkcja ma pracować na CURRENT SDS.

### Nieustalone

- `Otwórz` vs `Pobierz`,
- zachowanie dla brakującego pliku,
- obsługa wieloużytkownikowa,
- sposób ekspozycji pliku w Streamlit.

---

## DOC-01 — Dodawanie SDS z komputera użytkownika

**Status:** OPEN / ARCHITECTURAL DECISION NEEDED  
**Typ:** obsługa dokumentów  
**Wpływ:** storage model + UI + bezpieczeństwo

### Potrzeba

Docelowy użytkownik nie powinien znać ani ręcznie obsługiwać:

```text
SDS_ROOT_PATH
```

Nowy SDS powinien być możliwy do wskazania z komputera użytkownika.

### Ustalone

Obecny model lokalnej referencji do pliku był wystarczający dla MVP.

### Nieustalone

- upload vs kontrolowane kopiowanie,
- własność pliku,
- nazewnictwo,
- struktura katalogów,
- kolizje nazw,
- multi-user,
- backup,
- retention,
- bezpieczeństwo.

Wymaga osobnej decyzji technicznej.

---

# 5. Dowody decyzji BHP

## UI-14 / DOC-02 — Podgląd / otwieranie evidence

**Status:** OPEN  
**Typ:** ergonomia dokumentowa  
**Wpływ:** UI + filesystem

### Potrzeba

Użytkownik powinien mieć możliwość szybkiego odczytu dowodu decyzji BHP.

### Kierunek roboczy

Rozważane formaty:

```text
JPG / PNG → podgląd inline
PDF       → otwarcie / pobranie / ewentualny preview
MSG       → otwarcie / pobranie
```

### Nieustalone

- dokładny UX,
- bezpieczeństwo otwierania plików,
- zachowanie dla MISSING,
- relacja do przyszłego DOC-01.

---

# 6. Dane referencyjne

## DATA-01 — Słownik jednostek miary

**Status:** OPEN / SCHEMA DECISION NEEDED  
**Typ:** dane referencyjne  
**Wpływ:** schema + migracja + UI + raporty

### Problem

Jednostki są obecnie wpisywane tekstowo, co pozwala na warianty:

```text
l
L
litr
litry
szt
szt.
```

### Potrzeba

Docelowo wspólny słownik jednostek dla:

```text
peak quantity
monthly consumption
```

### Kierunek roboczy

Rozważana struktura:

```text
UNIT_OF_MEASURE
- unit_id
- code
- name
- category
- is_active
```

### Nieustalone

- finalny model,
- migracja istniejących wartości,
- reguły kategorii,
- konwersje jednostek,
- wpływ na Analizy.

Nie implementować bez osobnej decyzji schema.

---

# 7. Drobne korekty UI / semantyki

## UI-12 — `Data wystawienia SDS`

**Status:** OPEN  
**Typ:** nazewnictwo UI

### Potrzeba

Pole daty SDS powinno jednoznacznie oznaczać:

```text
datę wystawienia dokumentu przez producenta
```

a nie datę wprowadzenia do systemu.

Systemowa data rejestracji pozostaje odrębną informacją techniczną.

---

## UI-13 — Rewizja CURRENT SDS w tabeli `Produkty`

**Status:** OPEN  
**Typ:** ergonomia rejestru

### Potrzeba

W głównej tabeli produktów powinna być łatwo widoczna aktualna rewizja CURRENT SDS.

Nie zmienia to lifecycle SDS.

---

# 8. Dane robocze / porządkowanie

## OPS-01 — Uporządkowanie danych XBRAKE po walkthrough

**Status:** OPEN / OPERATIONAL  
**Typ:** lokalne dane operatora  
**Wpływ:** dane, nie production code

### Kontekst

Podczas fizycznego walkthrough wykorzystano XBRAKE CLEANER do testów:

```text
nowej rewizji SDS
decyzji BHP
miejsca stosowania
```

W efekcie lokalne dane mogą zawierać świadomie wprowadzone wartości testowe, w tym testowy CURRENT SDS.

### Zasada

Nie wykonywać automatycznego cleanup przez checkpoint / testy.

Przywrócenie rzeczywistego stanu danych ma być osobnym, kontrolowanym działaniem użytkownika.

---

# 9. Automatyczny odczyt SDS

## PARSER-02 — Stage 2 parsera SDS

**Status:** DEFERRED  
**Typ:** automatyzacja pomocnicza

### Zasada obowiązująca

Parser pozostaje:

```text
secondary target
```

Jeżeli działa:

```text
podpowiada dane
```

Jeżeli nie działa:

```text
manual fallback pozostaje pełnoprawnym workflow
```

### Poza zakresem bieżącego backlog refinement

Nie ustalamy teraz:

- nowych aliasów,
- segmentation framework,
- OCR platform,
- AI/LLM extraction,
- confidence score,
- mechanizmu uczenia.

---

# 10. Przeglądy okresowe

## R8 — Przeglądy okresowe

**Status:** DEFERRED  
**Typ:** przyszły etap biznesowy

Nie łączyć automatycznie z `Stan na dzień`.

`Stan na dzień` jest obecnie rozumiany jako:

```text
snapshot fizycznego stanu substancji
```

R8 pozostaje osobnym przyszłym zakresem dopóki Architekt Operacyjny nie podejmie decyzji o ich relacji.

---

# 11. REACH

## REACH — przyszły moduł compliance

**Status:** DEFERRED  
**Typ:** przyszły etap

Nie projektować ani nie implementować w ramach prac post CHECKPOINT-006 bez osobnej decyzji.

---

## REF-CLP — Nadzorowany katalog referencyjny klasyfikacji i oznakowania

**Status:** APPROVED REQUIREMENT / NOT IMPLEMENTED  
**Typ:** wymaganie przyszłego modułu referencyjnego  
**Decyzja Architekta Operacyjnego:** 2026-11-05  
**Powiązanie:** ekstrakcja i walidacja SDS (TDR-012); przyszły zakres CLP/REACH  
**Priorytet realizacji:** do ustalenia; obowiązkowa zależność przed uruchomieniem walidacji regulacyjnej opartej na słowniku.

### Zatwierdzona potrzeba

MSDS Manager ma posiadać nadzorowany, wersjonowany katalog referencyjny klasyfikacji i oznakowania substancji chemicznych oparty na właściwych źródłach prawa UE, w szczególności CLP i REACH oraz oficjalnych publikacjach EUR-Lex/ECHA.

Zakres wymagania obejmuje odniesienia do klas i kategorii zagrożeń, kodów i treści H/EUH/P, piktogramów GHS, haseł ostrzegawczych oraz identyfikację źródła prawnego, wersji, dat stosowania i historii zmian. Zakres szczegółowy wymaga osobnego BDR.

### Granice zatwierdzenia

- Katalog służy do rozpoznawania kodów i kontroli referencyjnej danych wyekstrahowanych z SDS.
- Poprawność kodu lub treści nie oznacza automatycznego potwierdzenia prawidłowości klasyfikacji chemicznej produktu.
- Automatyczna ocena zgodności substancji/mieszaniny z prawem nie jest zatwierdzona niniejszym wpisem.
- Australijski plakat GHS jest materiałem pomocniczym, **nie** źródłem obowiązujących reguł UE.
- Wpis nie autoryzuje zmiany CORE, schematu PostgreSQL, migracji, implementacji ani nowego Tasku.

### Następne działanie, kiedy obszar zostanie wybrany do realizacji

Przygotować BDR określający źródła, odpowiedzialność za aktualizację, wersjonowanie, ważność czasową i minimalny zakres słownika; następnie TDR i zamknięty Task po jawnej autoryzacji.

---

# 12. Macierz backlogu

| ID | Obszar | Stan ustaleń | Wymaga decyzji przed implementacją |
|---|---|---|---|
| ANALYTICS-01 | Zakładka Analizy | kierunek zatwierdzony | TAK |
| ANALYTICS-02 | Zestawienie zbiorcze | logika biznesowa zatwierdzona | TAK — UX/read model |
| ANALYTICS-03 | Stan na dzień | logika biznesowa zatwierdzona | TAK — BDR/schema |
| UI-11 | Otwieranie CURRENT SDS | potrzeba potwierdzona | TAK |
| DOC-01 | Dodawanie SDS z komputera | potrzeba potwierdzona | TAK — architektura storage |
| UI-14 / DOC-02 | Dowód BHP | potrzeba potwierdzona | TAK |
| DATA-01 | Jednostki miary | potrzeba potwierdzona | TAK — schema |
| UI-12 | Data wystawienia SDS | potrzeba potwierdzona | mała decyzja UI |
| UI-13 | Rewizja SDS w Produkty | potrzeba potwierdzona | mała decyzja UI |
| OPS-01 | Cleanup XBRAKE | otwarte operacyjnie | działanie ręczne |
| PARSER-02 | Parser Stage 2 | odłożony | TAK |
| R8 | Przeglądy okresowe | odłożony | TAK |
| REACH | Compliance | odłożony | TAK |
| REF-CLP | Nadzorowany katalog CLP/REACH | zatwierdzone wymaganie, niewdrożone | TAK — BDR/TDR przed implementacją |

---

# 13. Celowo nieustalona kolejność

Na moment utworzenia BACKLOG-001:

```text
nie wybieramy kolejnego Sprintu
nie ustalamy priorytetu wykonawczego
nie tworzymy nowych Tasków
nie zmieniamy Core
nie zmieniamy schema
```

Najbliższa decyzja Architekta Operacyjnego powinna dotyczyć wyłącznie:

> Który obszar backlogu ma zostać następnie przygotowany do formalnego projektowania?

Dopiero po tej decyzji przygotowywany jest właściwy BDR/TDR/Sprint.

---

## 14. Authorization boundary

BACKLOG-001 jest dokumentem ewidencyjnym.

Nie stanowi zgody na:

```text
implementację
migrację
zmianę Core
zmianę schema
nowy Sprint
nowy Task
```

Każda dalsza praca wymaga jawnego polecenia Architekta Operacyjnego.
