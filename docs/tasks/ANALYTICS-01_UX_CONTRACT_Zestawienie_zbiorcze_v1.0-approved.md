# ANALYTICS-01 — Kontrakt UX — Zestawienie zbiorcze

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 — Zakładka Analizy  
**Dokument:** UX Contract  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

---

## 1. Cel

Zakładka `Analizy` ma umożliwiać szybkie uzyskanie odpowiedzi:

> Jaki jest aktualny stan zarządzania produktami chemicznymi, dokumentacją SDS, decyzjami BHP i miejscami stosowania?

Nie zastępuje widoków operacyjnych:

```text
Produkty
Dodaj SDS
Decyzja BHP
Stanowiska
Widok nadzorczy
```

lecz agreguje informacje z tych obszarów.

Model UX:

```text
dane operacyjne
→ read model Analizy
→ dashboard zarządczo-operacyjny
```

---

## 2. UX target

Zatwierdzony kierunek wizualny:

```text
nowoczesny dashboard SaaS
inspiracja stylistyczna: Monday.com
bez kopiowania brandingu
```

Cechy:

- szeroki layout,
- lekki i czytelny interfejs,
- karty KPI,
- pastelowe statusy,
- wykresy,
- sekcja alertów,
- tabela zbiorcza,
- spójność z istniejącym sidebar MSDS Manager,
- złożoność backendu nie może przenosić się na złożoność operatora.

Docelowy układ:

```text
Analizy
└── Zestawienie zbiorcze

[ FILTRY ]

[ KPI ][ KPI ][ KPI ][ KPI ][ KPI ]

[ Produkty wg producenta ]
[ Status BHP ]
[ Nowe / zaktualizowane SDS ]

[ Wymaga uwagi ]

[ Zestawienie zbiorcze ]
```

---

## 3. Filtry

Pierwszy ekran przewiduje:

```text
Zakres dat
Producent
Status SDS
Status BHP
Lokalizacja
Eksport
```

`Eksport` pozostaje funkcjonalnie do doprecyzowania przed implementacją.

---

## 4. KPI

Zatwierdzony zakres kart:

```text
Produkty ogółem
SDS CURRENT
BHP zatwierdzone
Braki / do uzupełnienia
Stanowiska aktywne
```

Dokładne definicje agregacji i przypadków brzegowych należą do osobnej decyzji biznesowej `BDR-009`.

---

## 5. Wizualizacje

### 5.1. Produkty wg producenta

Typ:

```text
bar chart
```

Cel:

```text
liczba produktów wg producenta
```

### 5.2. Status BHP

Typ:

```text
donut / pie
```

Finalne kategorie muszą być zgodne z istniejącym modelem Core.

Nie wolno tworzyć nowego statusu BHP tylko dla potrzeb wykresu.

### 5.3. Nowe / zaktualizowane SDS

Typ:

```text
line / area chart
```

Cel:

```text
pokazać dynamikę rejestracji / zmian SDS w czasie
```

Dokładna definicja „nowe” i „zaktualizowane” należy do `BDR-009`.

---

## 6. Sekcja `Wymaga uwagi`

Dashboard ma wyróżniać problemy wymagające działania operatora.

Pierwszy zakres:

```text
Brak decyzji BHP
Brak miejsca stosowania
Brak / niedostępny dokument
```

Sekcja jest operacyjna, a nie tylko statystyczna.

Docelowo element powinien prowadzić do listy rekordów źródłowych, ale drill-down może być wdrożony etapowo.

---

## 7. Zestawienie zbiorcze

Tabela końcowa dashboardu:

| Producent | Produkty | SDS CURRENT | BHP OK | Braki | Ostatnia aktualizacja |
|---|---:|---:|---:|---:|---|

Tabela ma stanowić podstawowy widok kontrolny pod dashboardem.

Dokładne reguły agregacji kolumn należą do `BDR-009`.

---

## 8. Model MVP — decyzja architektoniczna

Dla `ANALYTICS-01 / ANALYTICS-02` zatwierdzono:

```text
MODEL A — DYNAMIC READ MODEL
```

czyli:

```text
Streamlit dashboard
→ Application / analytics read model
→ zapytania agregujące PostgreSQL
→ istniejące dane operacyjne
```

Dla MVP nie tworzymy osobnej warstwy:

```text
analytics schema
materialized views
data warehouse
ETL
osobnej bazy analitycznej
```

### Uzasadnienie

- niewielki wolumen danych,
- istniejący PostgreSQL jest źródłem bieżącego stanu,
- szybsze zweryfikowanie wartości biznesowej,
- brak przedwczesnej warstwy BI,
- możliwość późniejszej optymalizacji bez zmiany kontraktu UX.

---

## 9. Granica decyzji Model A

Model A dotyczy przede wszystkim:

```text
ANALYTICS-01 — zakładka Analizy
ANALYTICS-02 — Zestawienie zbiorcze / current-state dashboard
```

Nie przesądza technicznego modelu:

```text
ANALYTICS-03 — Stan na dzień
```

Jeżeli `Stan na dzień` będzie wymagał odtwarzania historycznych snapshotów, może wymagać osobnej decyzji schema / persistence.

Nie wolno na podstawie Modelu A upraszczać wymagań historycznych `Stan na dzień`.

---

## 10. Nawigacja

Docelowy kierunek:

```text
KPI / wykres / alert
→ lista rekordów
→ widok operacyjny
```

Pierwsza implementacja może dostarczyć dashboard bez pełnego drill-down, jeśli Task jawnie tak określi.

---

## 11. Poza zakresem

ANALYTICS-01 nie wprowadza:

```text
AI
predykcji
automatycznej oceny ryzyka
REACH
R8
parsera SDS
automatycznej decyzji BHP
data warehouse
materialized views
```

---

## 12. Następny krok

Po zatwierdzeniu niniejszego UX Contract:

```text
BDR-009
→ definicje KPI
→ definicje agregacji
→ znaczenie statusów na dashboardzie
→ reguły sekcji "Wymaga uwagi"
→ definicja "nowe / zaktualizowane SDS"

następnie:

TDR-009
→ dynamiczny read model
→ query contracts
→ UI composition
→ validation / performance boundaries
```

---

## 13. Status

```text
ANALYTICS-01 UX CONTRACT
VERSION: 1.0-approved
STATUS: APPROVED

MVP ANALYTICS MODEL:
MODEL A — DYNAMIC READ MODEL
APPROVED
```
