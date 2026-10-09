# SDS-SCHEMA-001 — Kanoniczna mapa sekcji i podsekcji SDS (REACH)

**Projekt:** MSDS Manager  
**Dokument:** SDS-SCHEMA-001  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-09  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus  
**Podstawa prawna:** Rozporządzenie Komisji (UE) 2020/878 zmieniające załącznik II do REACH

---

## 1. Cel

Dokument definiuje kanoniczny szkielet struktury karty charakterystyki (SDS), który ma być używany przez przyszły moduł ekstrakcji danych jako warstwa odniesienia niezależna od producenta i układu graficznego PDF.

Zasada:

```text
REACH / 2020/878
→ kanoniczne sekcje i podsekcje
→ wykrycie sekcji w PDF
→ biblioteka aliasów / wariantów
→ ekstrakcja danych
→ evidence JSON DRAFT
→ walidacja
→ weryfikacja człowieka
→ MSDS Manager
```

Ten dokument NIE definiuje jeszcze:
- biblioteki aliasów,
- reguł producentów,
- parsera PDF,
- kontraktu końcowego JSON,
- zapisu do PostgreSQL,
- automatycznej decyzji BHP.

---

## 2. Zasada kanoniczna

Parser nie może opierać znaczenia danych wyłącznie na położeniu tekstu lub dowolnej etykiecie producenta.

Każdy odczyt powinien zostać przypisany co najmniej do:

```text
section
subsection
page
source_text / source_location
extraction_state
```

Podstawowe stany ekstrakcji warstwy roboczej:

```text
FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE
```

Reguła ochronna:

```text
UNREADABLE / AMBIGUOUS / NOT_FOUND
≠
NO
```

oraz:

```text
NO SOURCE EVIDENCE
→ NO IMPORTABLE VALUE
```

---

## 3. Kanoniczna mapa SDS

### SEKCJA 1 — Identyfikacja substancji/mieszaniny i identyfikacja przedsiębiorstwa

| ID | Kanoniczny tytuł |
|---|---|
| 1.1 | Identyfikator produktu |
| 1.2 | Istotne zidentyfikowane zastosowania substancji lub mieszaniny oraz zastosowania odradzane |
| 1.3 | Dane dotyczące dostawcy karty charakterystyki |
| 1.4 | Numer telefonu alarmowego |

### SEKCJA 2 — Identyfikacja zagrożeń

| ID | Kanoniczny tytuł |
|---|---|
| 2.1 | Klasyfikacja substancji lub mieszaniny |
| 2.2 | Elementy oznakowania |
| 2.3 | Inne zagrożenia |

### SEKCJA 3 — Skład/informacja o składnikach

W zależności od przypadku SDS zawiera odpowiednio 3.1 albo 3.2.

| ID | Kanoniczny tytuł |
|---|---|
| 3.1 | Substancje |
| 3.2 | Mieszaniny |

### SEKCJA 4 — Środki pierwszej pomocy

| ID | Kanoniczny tytuł |
|---|---|
| 4.1 | Opis środków pierwszej pomocy |
| 4.2 | Najważniejsze ostre i opóźnione objawy oraz skutki narażenia |
| 4.3 | Wskazania dotyczące wszelkiej natychmiastowej pomocy lekarskiej i szczególnego postępowania z poszkodowanym |

### SEKCJA 5 — Postępowanie w przypadku pożaru

| ID | Kanoniczny tytuł |
|---|---|
| 5.1 | Środki gaśnicze |
| 5.2 | Szczególne zagrożenia związane z substancją lub mieszaniną |
| 5.3 | Informacje dla straży pożarnej |

### SEKCJA 6 — Postępowanie w przypadku niezamierzonego uwolnienia do środowiska

| ID | Kanoniczny tytuł |
|---|---|
| 6.1 | Indywidualne środki ostrożności, wyposażenie ochronne i procedury w sytuacjach awaryjnych |
| 6.2 | Środki ostrożności w zakresie ochrony środowiska |
| 6.3 | Metody i materiały zapobiegające rozprzestrzenianiu się skażenia i służące do usuwania skażenia |
| 6.4 | Odniesienia do innych sekcji |

### SEKCJA 7 — Postępowanie z substancjami i mieszaninami oraz ich magazynowanie

| ID | Kanoniczny tytuł |
|---|---|
| 7.1 | Środki ostrożności dotyczące bezpiecznego postępowania |
| 7.2 | Warunki bezpiecznego magazynowania, w tym informacje dotyczące wszelkich wzajemnych niezgodności |
| 7.3 | Szczególne zastosowanie(-a) końcowe |

### SEKCJA 8 — Kontrola narażenia/środki ochrony indywidualnej

| ID | Kanoniczny tytuł |
|---|---|
| 8.1 | Parametry dotyczące kontroli |
| 8.2 | Kontrola narażenia |

### SEKCJA 9 — Właściwości fizyczne i chemiczne

| ID | Kanoniczny tytuł |
|---|---|
| 9.1 | Informacje na temat podstawowych właściwości fizycznych i chemicznych |
| 9.2 | Inne informacje |

### SEKCJA 10 — Stabilność i reaktywność

| ID | Kanoniczny tytuł |
|---|---|
| 10.1 | Reaktywność |
| 10.2 | Stabilność chemiczna |
| 10.3 | Możliwość występowania niebezpiecznych reakcji |
| 10.4 | Warunki, których należy unikać |
| 10.5 | Materiały niezgodne |
| 10.6 | Niebezpieczne produkty rozkładu |

### SEKCJA 11 — Informacje toksykologiczne

| ID | Kanoniczny tytuł |
|---|---|
| 11.1 | Informacje na temat klas zagrożenia zdefiniowanych w rozporządzeniu (WE) nr 1272/2008 |
| 11.2 | Informacje o innych zagrożeniach |

### SEKCJA 12 — Informacje ekologiczne

| ID | Kanoniczny tytuł |
|---|---|
| 12.1 | Toksyczność |
| 12.2 | Trwałość i zdolność do rozkładu |
| 12.3 | Zdolność do bioakumulacji |
| 12.4 | Mobilność w glebie |
| 12.5 | Wyniki oceny właściwości PBT i vPvB |
| 12.6 | Właściwości zaburzające funkcjonowanie układu hormonalnego |
| 12.7 | Inne szkodliwe skutki działania |

### SEKCJA 13 — Postępowanie z odpadami

| ID | Kanoniczny tytuł |
|---|---|
| 13.1 | Metody unieszkodliwiania odpadów |

### SEKCJA 14 — Informacje dotyczące transportu

| ID | Kanoniczny tytuł |
|---|---|
| 14.1 | Numer UN lub numer identyfikacyjny ID |
| 14.2 | Prawidłowa nazwa przewozowa UN |
| 14.3 | Klasa(-y) zagrożenia w transporcie |
| 14.4 | Grupa pakowania |
| 14.5 | Zagrożenia dla środowiska |
| 14.6 | Szczególne środki ostrożności dla użytkowników |
| 14.7 | Transport morski luzem zgodnie z instrumentami IMO |

### SEKCJA 15 — Informacje dotyczące przepisów prawnych

| ID | Kanoniczny tytuł |
|---|---|
| 15.1 | Przepisy prawne dotyczące bezpieczeństwa, zdrowia i ochrony środowiska specyficzne dla substancji lub mieszaniny |
| 15.2 | Ocena bezpieczeństwa chemicznego |

### SEKCJA 16 — Inne informacje

Sekcja 16 nie posiada w części B rozporządzenia równorzędnego zestawu numerowanych podsekcji analogicznego do sekcji 1–15.

---

## 4. Warstwa parsera — identyfikatory kanoniczne

Dla implementacji zaleca się utrzymywanie stabilnych identyfikatorów niezależnych od języka i tytułu producenta, np.:

```text
SDS_01_01_PRODUCT_IDENTIFIER
SDS_01_03_SUPPLIER_DETAILS
SDS_02_01_CLASSIFICATION
SDS_02_02_LABEL_ELEMENTS
SDS_03_02_MIXTURE_COMPONENTS
SDS_11_01_TOXICOLOGICAL_HAZARD_CLASSES
SDS_11_02_OTHER_HAZARDS
```

Tytuł znaleziony w PDF jest dowodem lokalizacji i wariantem językowym, ale nie staje się identyfikatorem domenowym.

---

## 5. Biblioteka aliasów — przyszły artefakt

Kolejna warstwa powinna mapować rzeczywiste warianty znalezione w kartach SDS na kanoniczne ID.

Przykład:

```text
canonical_id:
SDS_01_03_SUPPLIER_DETAILS

canonical_title:
Dane dotyczące dostawcy karty charakterystyki

observed_aliases:
- Dane dostawcy
- Informacje o dostawcy
- Supplier details
- Details of the supplier of the safety data sheet
```

Alias pomaga znaleźć sekcję lub pole, ale NIE rozstrzyga automatycznie znaczenia podmiotu.

Przykład:

```text
manufacturer
supplier
EU representative
importer
distributor
```

to role, które mogą występować obok siebie i nie mogą zostać automatycznie utożsamione.

---

## 6. Zasada walidacji przyszłego extractora

Parser ma preferować:

```text
brak wyniku / HUMAN REVIEW
```

zamiast:

```text
wartość nieudowodniona / zgadywana
```

Minimalny ślad dowodowy pola w roboczym JSON:

```json
{
  "value": "...",
  "section": "1.3",
  "page": 1,
  "source_text": "...",
  "extraction_state": "FOUND"
}
```

Dopuszczalne stany robocze:

```text
FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE
```

Nie są one odpowiednikiem wartości domenowych Core takich jak `YES`, `NO`, `NO_DATA` czy `NOT_APPLICABLE`.

---

## 7. Źródło normatywne

Rozporządzenie Komisji (UE) 2020/878 z dnia 18 czerwca 2020 r. zmieniające załącznik II do rozporządzenia (WE) nr 1907/2006 (REACH).

Część B załącznika II definiuje 16 tytułów sekcji i wymagane podtytuły; dla sekcji 3 stosuje się odpowiednio 3.1 albo 3.2.

---

## 8. Status

```text
SDS-SCHEMA-001
VERSION: 1.0-approved
STATUS: APPROVED
```

Dokument nie autoryzuje implementacji.

Po zatwierdzeniu może stać się podstawą do:

```text
SDS-ALIAS-001
→ biblioteka aliasów i wariantów z realnych SDS

SDS-JSON-001
→ kontrakt evidence JSON DRAFT

następnie
→ Task implementacyjny dla Codexa
```
