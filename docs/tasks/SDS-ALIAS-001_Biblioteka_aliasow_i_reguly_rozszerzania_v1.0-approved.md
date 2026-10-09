# SDS-ALIAS-001 — Biblioteka aliasów i reguły rozszerzania

**Projekt:** MSDS Manager  
**Dokument:** SDS-ALIAS-001  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-09  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — projektowanie i kontrola, poza runtime aplikacji  
**Podstawa:** SDS-SCHEMA-001 — kanoniczna mapa sekcji i podsekcji SDS  

---

## 1. Cel

Dokument definiuje kontrolowaną bibliotekę aliasów używaną przez autonomiczny moduł odczytu SDS.

Biblioteka ma umożliwiać rozpoznawanie rzeczywistych wariantów nazw sekcji, etykiet pól i ról występujących w kartach SDS różnych producentów bez uzależniania działania aplikacji od LLM, Work ani Cerberusa.

Docelowy przepływ:

```text
PDF SDS
→ parser strukturalny
→ SDS-SCHEMA
→ SDS-ALIAS
→ ekstrakcja z dowodem źródłowym
→ walidacja
→ JSON DRAFT
→ HUMAN REVIEW
→ Application
→ PostgreSQL
```

Runtime MSDS Manager pozostaje autonomiczny.

---

## 2. Zasada nadrzędna

Biblioteka aliasów nie zmienia znaczenia danych domenowych.

Jej zadaniem jest wyłącznie:

```text
tekst / etykieta z SDS
→ rozpoznanie kanonicznego miejsca lub roli
```

Biblioteka NIE może:

- zgadywać brakujących danych,
- zastępować walidacji źródła,
- utożsamiać różnych ról podmiotów,
- uznawać `NOT_FOUND`, `UNREADABLE` lub `AMBIGUOUS` za `NO`,
- podejmować decyzji BHP,
- samoczynnie dopisywać nowych aliasów do zbioru ACTIVE.

---

## 3. Dwa poziomy aliasów

### 3.1. SECTION_ALIAS

Służy do rozpoznania sekcji lub podsekcji SDS.

Przykład:

```text
canonical_id: SDS_01_03_SUPPLIER_DETAILS
canonical_section: 1.3
```

Alias może wskazywać wariant tytułu, ale nie określa jeszcze konkretnej roli podmiotu.

### 3.2. FIELD_ROLE_ALIAS

Służy do rozpoznania konkretnego pola lub roli wewnątrz sekcji.

Przykład:

```text
section: 1.3
role: MANUFACTURER_EXPORTER
alias: "Mfg. in U.S.A and exported by"
```

oraz osobno:

```text
section: 1.3
role: EU_REPRESENTATIVE
alias: "EU Only Representative"
```

Reguła:

```text
MANUFACTURER ≠ SUPPLIER ≠ IMPORTER ≠ DISTRIBUTOR ≠ EU_REPRESENTATIVE
```

Jeżeli karta wskazuje kilka podmiotów, parser zachowuje każdą rolę osobno.

---

## 4. Statusy cyklu życia aliasu

Każdy nowy alias przechodzi kontrolowany cykl:

```text
CANDIDATE
→ APPROVED
→ ACTIVE
```

lub:

```text
CANDIDATE
→ REJECTED
```

Znaczenie statusów:

### CANDIDATE

Wariant zaobserwowany w rzeczywistym SDS, ale jeszcze niezatwierdzony do automatycznego użycia.

### APPROVED

Znaczenie aliasu zostało świadomie potwierdzone przez człowieka.

### ACTIVE

Alias może być używany przez parser po przejściu testów regresyjnych.

### REJECTED

Wariant został oceniony jako błędne, zbyt szerokie lub niebezpieczne dopasowanie.

Parser produkcyjny korzysta wyłącznie z aliasów `ACTIVE`.

---

## 5. Minimalny rekord aliasu

Minimalna struktura rekordu:

```text
alias_id
alias_type
canonical_id
canonical_section
role
alias_text
language
status
source_document
source_page
source_location
manufacturer_family
first_seen_at
approved_at
notes
```

### Pola wymagane

```text
alias_id
alias_type
canonical_id
alias_text
status
source_document
```

### Pola warunkowe

- `role` — wymagane dla `FIELD_ROLE_ALIAS`,
- `source_page` — jeśli możliwe do jednoznacznego ustalenia,
- `source_location` — sekcja, wiersz, stopka, nagłówek lub inny punkt dowodowy,
- `manufacturer_family` — opcjonalna informacja pomocnicza do analizy layoutu; nie może ograniczać aliasu do producenta bez osobnej reguły.

---

## 6. Reguła rozszerzania biblioteki

Nowy SDS może ujawnić wariant nieznany parserowi.

Przepływ:

```text
NOWY SDS
→ parser nie znajduje ACTIVE aliasu
→ zapisuje obserwację jako ALIAS_CANDIDATE
→ człowiek ocenia znaczenie
→ APPROVED lub REJECTED
→ test regresyjny
→ ACTIVE albo pozostaje poza runtime
```

Runtime nie dodaje automatycznie nowych aliasów.

Cerberus może pomagać projektowo w analizie przypadków, ale nie uczestniczy w wykonaniu aplikacji i nie jest źródłem decyzji runtime.

---

## 7. Reguły akceptacji aliasu

Alias może zostać zatwierdzony tylko wtedy, gdy:

1. występuje w rzeczywistym SDS,
2. jego lokalizacja jest znana,
3. jego znaczenie jest jednoznaczne w danym kontekście,
4. mapowanie do `canonical_id` nie zmienia znaczenia pola,
5. dla aliasu roli podmiotowej rozpoznana jest właściwa rola,
6. alias nie jest nadmiernie ogólny,
7. istnieje możliwość dodania testu pozytywnego,
8. istnieje możliwość sprawdzenia, że alias nie powoduje fałszywych dopasowań w dotychczasowym zestawie SDS.

Jeżeli warunki nie są spełnione:

```text
CANDIDATE → REJECTED
```

lub pozostaje:

```text
CANDIDATE / HUMAN REVIEW
```

---

## 8. Normalizacja techniczna przed dopasowaniem

Parser może wykonywać wyłącznie bezpieczną normalizację techniczną, np.:

- trim białych znaków,
- redukcję wielokrotnych spacji,
- ujednolicenie znaków końca linii,
- porównanie bez rozróżniania wielkości liter, jeśli reguła aliasu na to pozwala,
- zachowanie oryginalnego tekstu jako `source_text`.

Parser nie może podczas normalizacji:

- usuwać słów zmieniających rolę,
- tłumaczyć znaczenia pola,
- upraszczać kilku etykiet do jednego znaczenia bez zatwierdzonego aliasu,
- zamieniać danych źródłowych na własną interpretację.

---

## 9. Initial seed — obserwacje z OPEX

Źródło: `T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf`.

Poniższe wpisy są zatwierdzonym seedem obserwacji biblioteki. Ich użycie w runtime nadal wymaga przejścia cyklu APPROVED → test regresyjny → ACTIVE.

### A-001 — nazwa produktu

```yaml
alias_id: A-001
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_01_01_PRODUCT_IDENTIFIER
canonical_section: "1.1"
role: PRODUCT_NAME
alias_text: "Nazwa produktu"
language: pl
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: 1
source_location: "Sekcja 1.1"
manufacturer_family: "Sherwin-Williams / OPEX"
```

### A-002 — kod produktu

```yaml
alias_id: A-002
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_01_01_PRODUCT_IDENTIFIER
canonical_section: "1.1"
role: PRODUCT_CODE
alias_text: "Kod produktu"
language: pl
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: 1
source_location: "Sekcja 1.1"
manufacturer_family: "Sherwin-Williams / OPEX"
```

### A-003 — producent i eksporter

```yaml
alias_id: A-003
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_01_03_SUPPLIER_DETAILS
canonical_section: "1.3"
role: MANUFACTURER_EXPORTER
alias_text: "Mfg. in U.S.A and exported by"
language: en
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: 1
source_location: "Sekcja 1.3"
manufacturer_family: "Sherwin-Williams / OPEX"
```

### A-004 — przedstawiciel w UE

```yaml
alias_id: A-004
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_01_03_SUPPLIER_DETAILS
canonical_section: "1.3"
role: EU_REPRESENTATIVE
alias_text: "EU Only Representative"
language: en
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: 1
source_location: "Sekcja 1.3"
manufacturer_family: "Sherwin-Williams / OPEX"
```

### A-005 — data wydania / aktualizacji

```yaml
alias_id: A-005
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_DOCUMENT_METADATA
canonical_section: null
role: SDS_ISSUE_OR_UPDATE_DATE
alias_text: "Data wydania/Data aktualizacji"
language: pl
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: "1, 25"
source_location: "Stopka"
manufacturer_family: "Sherwin-Williams / OPEX"
```

### A-006 — wersja dokumentu

```yaml
alias_id: A-006
alias_type: FIELD_ROLE_ALIAS
canonical_id: SDS_DOCUMENT_METADATA
canonical_section: null
role: SDS_REVISION
alias_text: "Wersja"
language: pl
status: CANDIDATE
source_document: "T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf"
source_page: "1, 25"
source_location: "Stopka"
manufacturer_family: "Sherwin-Williams / OPEX"
```

---

## 10. Initial seed — obserwacje z 3M DP-490

Źródło: `3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf`.

Na obecnym materiale potwierdzono przede wszystkim zachowanie strukturalne:

```text
jeden PDF
→ trzy osobno oznaczone karty SDS
```

oraz:

```text
sekcja 1.1 → nazwa konkretnej karty / produktu
sekcja 1.3 → dane dostawcy
nagłówek karty → data aktualizacji + numer wersji
```

Nie tworzy się jeszcze dodatkowych `FIELD_ROLE_ALIAS` dla 3M, jeżeli raport nie zachował dokładnej etykiety źródłowej pola.

Reguła:

```text
brak dokładnego observed_alias
→ nie tworzymy aliasu z pamięci / interpretacji
```

Przypadek 3M zostaje natomiast zapisany jako wymagany wzorzec testowy dla:

```text
MULTI_SDS_IN_SINGLE_PDF
```

Parser musi rozpoznać granice co najmniej trzech kart i nie może przenieść daty, wersji ani produktu pomiędzy nimi.

---

## 11. Biblioteka layoutów — rozdzielenie odpowiedzialności

Alias tekstowy nie powinien przejmować odpowiedzialności za układ dokumentu.

Dlatego przewiduje się osobny artefakt / warstwę:

```text
SDS-LAYOUT-001
```

który będzie opisywał wzorce takie jak:

- pole w tej samej linii co etykieta,
- wartość w kolejnej linii,
- tabela w sekcji 3,
- wartość w stopce,
- powtarzalny nagłówek na każdej stronie,
- kilka kart SDS w jednym PDF.

`SDS-ALIAS` odpowiada za znaczenie etykiety.

`SDS-LAYOUT` odpowiada za sposób technicznego znalezienia wartości wokół etykiety.

---

## 12. Regresja po aktywacji aliasu

Każdy alias przed uzyskaniem statusu `ACTIVE` musi przejść test regresyjny na zestawie wzorcowych SDS.

Minimalne sprawdzenia:

```text
1. alias znajduje właściwe pole w dokumencie źródłowym,
2. alias nie znajduje pola w miejscach, gdzie nie powinien,
3. rola podmiotu nie zostaje pomylona,
4. wartość pozostaje przypisana do właściwej karty w PDF wielokartowym,
5. brak wyniku pozostaje brakiem / HUMAN REVIEW,
6. nie pojawia się nowe false positive w dotychczasowym golden set.
```

Priorytet jakości:

```text
FALSE POSITIVE
> większe ryzyko niż
MISSING / HUMAN REVIEW
```

---

## 13. Golden set

Biblioteka aliasów i parser powinny być rozwijane na kontrolowanym zestawie reprezentatywnych kart SDS.

Początkowy zestaw obejmuje co najmniej:

```text
OPEX
→ prosty, jednoznaczny przypadek identyfikacyjny

3M DP-490
→ wiele kart SDS w jednym PDF
```

Docelowo należy dodać:

- inny producent i layout,
- SDS z tabelą składników o innym układzie,
- SDS skanowany / częściowo nieczytelny,
- SDS z brakami danych,
- SDS z niejednoznacznymi rolami podmiotów,
- SDS z innym formatem daty / rewizji.

Każdy przypadek golden set powinien posiadać ręcznie zatwierdzony wynik referencyjny.

---

## 14. Autonomia aplikacji

Obowiązuje:

```text
runtime MSDS Manager
→ bez LLM
→ bez Cerberusa
→ bez Work
→ bez zewnętrznej usługi AI
```

Cerberus może uczestniczyć wyłącznie w procesie projektowym:

- analizie nowego typu SDS,
- przygotowaniu propozycji reguły,
- ocenie spójności artefaktów,
- przeglądzie raportów z implementacji.

Decyzję o dopuszczeniu aliasu do `ACTIVE` podejmuje człowiek zgodnie z kontrolowanym procesem projektu.

---

## 15. Proponowana fizyczna postać biblioteki

Na obecnym etapie preferowany jest wersjonowany plik danych w repozytorium, np.:

```text
config/sds_aliases.yaml
```

lub równoważna lokalizacja wynikająca z istniejącej struktury repo.

Nie tworzymy na tym etapie:

- osobnej tabeli PostgreSQL dla aliasów,
- panelu administracyjnego,
- mechanizmu online learning,
- API mikroserwisu,
- zależności od LLM.

Format danych zostanie ostatecznie ustalony w TDR przed implementacją.

---

## 16. Następne artefakty

Po zatwierdzeniu SDS-ALIAS-001 należy przygotować kolejno:

```text
1. SDS-JSON-001
   kontrakt evidence JSON DRAFT

2. SDS-LAYOUT-001
   minimalne wzorce technicznego położenia danych

3. GOLDEN-SET-001
   zestaw przypadków i oczekiwanych wyników

4. TDR
   techniczny model extractora + validatora + importera

5. TASK dla Codexa
```

Nie rozpoczynamy implementacji przed zatwierdzeniem wymaganych decyzji.

---

## 17. Status

```text
SDS-ALIAS-001
VERSION: 0.1-draft
STATUS: DRAFT / DO REVIEW
IMPLEMENTATION: NOT AUTHORIZED
```


---

## 16. Zatwierdzenie

Dokument zatwierdzony przez Architekta Operacyjnego w dniu 2026-10-09.

```text
SDS-ALIAS-001
VERSION: 1.0-approved
STATUS: APPROVED
IMPLEMENTATION: NOT AUTHORIZED
```
