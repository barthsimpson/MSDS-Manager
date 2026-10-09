# TDR-012 — Autonomiczny moduł ekstrakcji i walidacji SDS

**Projekt:** MSDS Manager  
**Dokument:** TDR-012  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-09  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — projektowanie i kontrola, poza runtime aplikacji  
**Wykonawca techniczny po autoryzacji:** Codex OpenAI  

**Podstawa biznesowa i projektowa:**
- BDR-005 — automatyczna ekstrakcja SDS jako DRAFT + weryfikacja użytkownika,
- CORE-001 v1.5-approved,
- TDR-003 — granice warstw aplikacji,
- TDR-006 — kontrolowany import SDS,
- SDS-SCHEMA-001 v1.0-approved,
- SDS-ALIAS-001 v1.0-approved,
- SDS-JSON-001 v1.0-approved,
- GOV-001 i GOV-002.

---

## 1. Cel decyzji technicznej

TDR-012 definiuje minimalny techniczny model autonomicznego modułu, który:

```text
PDF SDS
→ odczyt techniczny
→ rozpoznanie logicznych kart SDS
→ rozpoznanie sekcji / podsekcji
→ mapowanie przez zatwierdzoną bibliotekę aliasów
→ ekstrakcja wartości wraz z dowodem źródłowym
→ walidacja
→ Evidence JSON DRAFT
```

Moduł przygotowuje dane do późniejszej weryfikacji człowieka i kontrolowanego importu do MSDS Manager.

TDR-012 NIE autoryzuje zapisu odczytanych danych bezpośrednio do PostgreSQL.

---

## 2. Zasada nadrzędna

Runtime ma być autonomiczny:

```text
BEZ LLM
BEZ ChatGPT Work
BEZ Cerberusa
BEZ zewnętrznej usługi AI
```

Cerberus i Codex mogą uczestniczyć w projektowaniu, implementacji, testach i rozwoju biblioteki poza runtime.

Działający moduł ekstrakcji opiera się wyłącznie na:

```text
kodzie aplikacji
+ SDS-SCHEMA
+ SDS-ALIAS
+ zatwierdzonych regułach ekstrakcji
+ walidatorach
```

---

## 3. Decyzja: moduł, nie mikroserwis

Na obecnym etapie NIE tworzy się osobnego mikroserwisu sieciowego.

Pierwsza implementacja jest wydzielonym modułem w repozytorium MSDS Manager, uruchamianym lokalnie i możliwym do wywołania przez:

```text
Application use case
lub
kontrolowane CLI
```

Powód:

- brak potrzeby osobnego API,
- brak potrzeby kolejek i niezależnego deploymentu,
- łatwiejsze testy na rzeczywistych SDS,
- mniejszy narzut operacyjny,
- zachowanie autonomii lokalnej,
- możliwość późniejszego wydzielenia bez zmiany kontraktu `SDS-JSON-001`.

Granica modułu ma być jednak jawna, aby przyszłe wydzielenie było możliwe.

---

## 4. Granice odpowiedzialności

### 4.1. Moduł ekstrakcji odpowiada za

- walidację wejściowego PDF,
- odczyt warstwy tekstowej,
- ocenę czytelności,
- wykrycie jednej lub wielu logicznych kart SDS w jednym PDF,
- wykrycie sekcji i podsekcji,
- dopasowanie aktywnych aliasów,
- odczyt wybranych pól,
- zapis dowodu źródłowego dla każdego `FOUND`,
- wykrycie `NOT_FOUND`, `AMBIGUOUS`, `UNREADABLE`,
- utworzenie `Evidence JSON DRAFT`,
- raport walidacji ekstrakcji.

### 4.2. Moduł ekstrakcji NIE odpowiada za

- decyzję BHP,
- automatyczne utworzenie PRODUCT,
- automatyczne uznanie SDS za CURRENT,
- zmianę poprzedniego SDS na ARCHIVED,
- zapis do PostgreSQL,
- bezpośrednią modyfikację Core,
- automatyczne rozszerzanie biblioteki aliasów,
- automatyczne poprawianie braków poprzez zgadywanie.

---

## 5. Pipeline techniczny

### ETAP A — INPUT VALIDATION

Wejście:

```text
PDF
```

Sprawdzenia co najmniej:

- plik istnieje,
- rozszerzenie / typ wejścia jest PDF,
- plik nie jest pusty,
- możliwy jest odczyt liczby stron,
- obliczany jest `sha256`,
- identyfikowana jest możliwość odczytu tekstu.

Rezultat:

```text
READABLE
PARTIALLY_READABLE
UNREADABLE
```

### ETAP B — TEXT EXTRACTION

Odczytywana jest istniejąca warstwa tekstowa PDF.

Pierwsza implementacja NIE wymaga OCR.

Jeżeli istotna część dokumentu jest wyłącznie skanem:

```text
UNREADABLE / PARTIALLY_READABLE
→ brak zgadywania
→ HUMAN REVIEW
```

OCR może zostać dodany później jako osobna, kontrolowana decyzja techniczna.

### ETAP C — LOGICAL SDS SEGMENTATION

Moduł wykrywa:

```text
1 source PDF
→ 1..N logical SDS documents
```

Każdy logiczny SDS otrzymuje:

```text
document_key
page_range
```

Przypadek referencyjny:

```text
3M DP-490
→ SDS zestawu
→ SDS Part B
→ SDS Part A
```

Nie wolno przyjmować automatycznie:

```text
1 PDF = 1 SDS
```

### ETAP D — SECTION DETECTION

Dla każdego logicznego SDS wykrywane są sekcje i podsekcje zgodnie z:

```text
SDS-SCHEMA-001
```

Parser rozpoznaje strukturę kanoniczną, nie tylko pozycję tekstu na stronie.

### ETAP E — ALIAS MATCHING

Dozwolone są wyłącznie aliasy:

```text
status = ACTIVE
```

zgodnie z `SDS-ALIAS-001`.

Nierozpoznany wariant:

```text
→ CANDIDATE observation
→ nie staje się automatycznie ACTIVE
```

### ETAP F — FIELD EXTRACTION

Ekstraktor odczytuje tylko pola objęte zatwierdzonym zakresem.

Każde pole otrzymuje:

```text
value
state
evidence[]
```

Reguła:

```text
state = FOUND
→ evidence musi istnieć
```

Jeżeli brak dowodu:

```text
FOUND jest niedozwolone
```

### ETAP G — VALIDATION

Walidacja jest oddzielona od samej ekstrakcji.

Obejmuje trzy poziomy:

#### G1 — structural validation

Sprawdza m.in.:

- zgodność JSON z `SDS-JSON-001`,
- dozwolone statusy,
- wymagane pola techniczne,
- zakres stron,
- spójność `document_key`,
- relację `FOUND → evidence`.

#### G2 — source/evidence validation

Sprawdza m.in.:

- czy wskazana strona mieści się w logicznym SDS,
- czy sekcja/podsekcja jest zgodna z rodzajem pola,
- czy `source_text` faktycznie wspiera wartość,
- czy nazwa pliku nie została użyta jako jedyny dowód wartości domenowej.

#### G3 — semantic validation

Sprawdza zatwierdzone reguły znaczeniowe, np.:

```text
manufacturer ≠ supplier ≠ EU representative
```

oraz:

```text
hazard statement składnika z sekcji 3
≠
automatycznie hazard statement całego produktu z sekcji 2
```

Walidator nie podejmuje decyzji BHP.

---

## 6. Zasady błędów i niepewności

Dozwolone stany ekstrakcji:

```text
FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE
```

Twarda reguła:

```text
NOT_FOUND / AMBIGUOUS / UNREADABLE
≠
NO
```

oraz:

```text
NO SOURCE EVIDENCE
→ NO IMPORTABLE VALUE
```

Parser ma preferować:

```text
brak wartości + jawny status
```

zamiast:

```text
wartość prawdopodobna / zgadywana
```

---

## 7. Artefakt wyjściowy

Jedynym podstawowym artefaktem wyjściowym modułu jest:

```text
Evidence JSON DRAFT
```

zgodny z:

```text
SDS-JSON-001 v1.0-approved
```

JSON pozostaje:

```text
DRAFT
```

i nie jest obowiązującą reprezentacją Core.

---

## 8. Granica z MSDS Manager Application

Po stronie MSDS Manager obowiązuje późniejszy przepływ:

```text
Evidence JSON DRAFT
→ walidacja wejścia
→ DRY RUN przeciw stanowi aplikacji
→ HUMAN REVIEW
→ Application use case
→ Repository / SQLAlchemy
→ PostgreSQL
```

Bezpośredni zapis:

```text
JSON → SQL INSERT/UPDATE
```

jest niedozwolony jako standardowy mechanizm.

Szczegółowy importer i jego workflow mogą zostać zdefiniowane osobnym Taskiem / rozszerzeniem TDR po udowodnieniu jakości extractora.

---

## 9. Proponowane granice kodu

TDR-012 nie narzuca nazw każdego pliku, ale implementacja ma zachować istniejące granice TDR-003.

Minimalny podział odpowiedzialności:

```text
application
├── orchestration ekstrakcji
├── kontrakty wejścia/wyjścia
└── walidacja procesu

infrastructure
└── sds_extraction
    ├── pdf reader
    ├── section detector
    ├── alias matcher
    ├── field extractor
    └── JSON serializer

domain
└── bez zależności od biblioteki PDF / filesystem / CLI
```

CLI, jeżeli powstanie, jest tylko adapterem uruchamiającym Application.

---

## 10. Biblioteka aliasów w runtime

Biblioteka `SDS-ALIAS` jest wersjonowanym artefaktem danych.

Runtime:

```text
READ ACTIVE aliases
```

Runtime NIE może:

```text
CANDIDATE → ACTIVE
```

Zmiana biblioteki wymaga:

```text
obserwacja
→ ocena człowieka
→ APPROVED
→ test regresyjny
→ ACTIVE
```

---

## 11. Golden Set

Przed uznaniem extractora za użyteczny operacyjnie powstaje kontrolowany zestaw referencyjny:

```text
GOLDEN SDS SET
```

Początkowo powinien zawierać co najmniej:

- prosty, czytelny SDS,
- OPEX jako przypadek jednoznaczny,
- 3M DP-490 jako PDF wielokartowy,
- SDS o innym układzie producenta,
- SDS z brakującym polem,
- SDS z nierozpoznanym aliasem,
- dokument częściowo nieczytelny / skanowany, jeśli jest dostępny.

Dla każdego przypadku przechowujemy oczekiwany wynik ekstrakcji.

---

## 12. Kryteria jakości pierwszego PoC

Pierwszy PoC NIE musi odczytywać wszystkich pól SDS.

Zakres początkowy:

```text
product name
manufacturer product code
party roles z sekcji 1.3
SDS issue/update date
SDS revision/version
logical SDS segmentation
source evidence
```

PoC uznaje się za poprawny, jeżeli:

1. OPEX daje oczekiwane pola identyfikacyjne i rozróżnia role podmiotów.
2. 3M jest wykrywany jako wiele logicznych SDS w jednym PDF.
3. data zastępowanej wersji nie zostaje użyta jako bieżąca data SDS.
4. nazwa pliku nie jest jedynym źródłem daty, rewizji ani nazwy produktu.
5. każde `FOUND` posiada dowód.
6. nierozpoznane / nieczytelne pola nie są zgadywane.
7. wynik jest zgodny z `SDS-JSON-001`.
8. testy regresyjne Golden Set przechodzą.

---

## 13. Rozwój po PoC

Po stabilizacji danych identyfikacyjnych zakres może być rozszerzany etapami:

```text
Sekcja 2
→ SAFETY_PROFILE

Sekcja 3
→ SDS_COMPONENT

Sekcja 11
→ wybrane dane toksykologiczne
```

Każde rozszerzenie wymaga:

```text
jawnego zakresu
+ aliasów / reguł
+ golden cases
+ testów
```

Nie rozszerzamy parsera „przy okazji” implementacji.

---

## 14. STOP conditions dla Codexa

Codex ma zatrzymać implementację i zgłosić problem, jeżeli:

- wymagane pole nie ma jednoznacznej reguły źródłowej,
- kontrakt `SDS-JSON-001` okazuje się niewystarczający,
- potrzebna byłaby zmiana Core,
- potrzebna byłaby automatyczna decyzja BHP,
- PDF wymaga OCR, którego zakres nie został zatwierdzony,
- konieczne byłoby automatyczne aktywowanie nowych aliasów,
- potrzebny byłby bezpośredni zapis SQL z pominięciem Application,
- istnieje konflikt pomiędzy dokumentami zatwierdzonymi.

---

## 15. Wpływ na Core i bazę

TDR-012:

```text
Core change: NO
DB schema change: NO
Alembic migration: NO
BHP decision model change: NO
SDS lifecycle change: NO
```

Artefakty ekstrakcji są warstwą roboczą przed Core.

---

## 16. Authorization boundary

Po zatwierdzeniu TDR-012:

```text
wolno przygotować Sprint / Task implementacyjny dla PoC extractora
```

Sam TDR NIE stanowi zgody na wykonanie zmian w repozytorium.

Wykonanie wymaga nadal:

```text
jawnego Tasku
+ jawnej autoryzacji Architekta
```

---

## 17. Status

```text
TDR-012
VERSION: 1.0-approved
STATUS: APPROVED
IMPLEMENTATION: NOT AUTHORIZED
```
