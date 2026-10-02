# BDR-009 — ANALYTICS — Zestawienie zbiorcze: KPI, agregacje i semantyka dashboardu

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-009  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Powiązany UX:** `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved`  
**Zakres:** ANALYTICS-01 / ANALYTICS-02  
**Poza zakresem:** ANALYTICS-03 `Stan na dzień`

---

## 1. Cel decyzji

BDR-009 definiuje biznesowe znaczenie danych prezentowanych w zakładce:

```text
Analizy
→ Zestawienie zbiorcze
```

Dokument rozstrzyga:

- populację raportu,
- znaczenie KPI,
- semantykę filtrów,
- kategorie statusu BHP,
- znaczenie alertów `Wymaga uwagi`,
- reguły wykresów,
- relację dashboardu do istniejącej macierzy `PRODUCT × USAGE_LOCATION`,
- znaczenie tabel agregacyjnych.

BDR-009 nie projektuje zapytań SQL, DTO ani komponentów Streamlit. To należy do TDR-009.

---

## 2. Źródła i zasady nadrzędne

Obowiązujące pozostają w szczególności:

```text
PRODUCT = centralny obiekt systemu
MANUFACTURER 1:N PRODUCT
PRODUCT N:M USAGE_LOCATION
PRODUCT_USAGE_LOCATION.peak_quantity
SDS CURRENT / ARCHIVED
BHP_DECISION APPROVED / REJECTED
BHP_DECISION CURRENT / SUPERSEDED
BHP_DECISION 1:1 DECISION_EVIDENCE
USAGE_LOCATION ACTIVE / INACTIVE
```

Zestawienie zbiorcze jest widokiem informacyjnym.

Nie może:

```text
zmieniać danych operacyjnych
zmieniać lifecycle
tworzyć nowych statusów
podejmować decyzji BHP
automatycznie korygować MAX
```

---

## 3. Główna zasada raportu

`Zestawienie zbiorcze` pokazuje:

```text
CURRENT STATE
```

czyli bieżący stan wynikający z aktualnych danych operacyjnych.

Dashboard nie jest snapshotem historycznym.

Nie realizuje:

```text
Stan na dzień
```

i nie próbuje odtwarzać bieżącego stanu dla dowolnej daty historycznej.

---

## 4. Dwie warstwy prezentacji

Zatwierdzony UX dashboardu wprowadza warstwę agregacyjną, ale nie zastępuje wcześniej ustalonego znaczenia szczegółowego raportu.

Przyjmuje się model:

```text
WARSTWA A — DASHBOARD SUMMARY
KPI + wykresy + alerty + agregacje

WARSTWA B — ZESTAWIENIE SZCZEGÓŁOWE
PRODUCT × USAGE_LOCATION
```

### 4.1. Warstwa A

Służy do szybkiej oceny stanu systemu.

### 4.2. Warstwa B

Jednostka szczegółowego raportu pozostaje:

```text
PRODUCT × USAGE_LOCATION
```

Komórka ilościowa prezentuje:

```text
PRODUCT_USAGE_LOCATION.peak_quantity_value
+ UNIT_OF_MEASURE.code
```

Raport szczegółowy:

```text
nie służy do wpisywania monthly consumption
nie zmienia PRODUCT
nie tworzy snapshotu
```

Po przyszłym wdrożeniu `Stan na dzień` może otrzymać pomocniczą różnicę `+/-`, ale pozostaje to zakresem ANALYTICS-03.

---

## 5. Populacja dashboardu

Domyślną populacją `Analizy` są:

```text
wszystkie zarejestrowane PRODUCT
```

Nie usuwa się z dashboardu produktów tylko dlatego, że posiadają status:

```text
PENDING_APPROVAL
ACTIVE
REJECTED
INACTIVE
```

Status produktu jest informacją biznesową, nie kryterium istnienia rekordu.

Jednocześnie konkretne KPI i alerty mogą stosować własną regułę zakresu tam, gdzie wynika to z ich znaczenia.

---

## 6. KPI — `Produkty ogółem`

Definicja:

```text
COUNT(DISTINCT PRODUCT.product_id)
```

po zastosowaniu aktywnych filtrów wymiarowych.

KPI obejmuje wszystkie statusy PRODUCT.

Nie oznacza:

```text
tylko ACTIVE
```

---

## 7. KPI — `SDS CURRENT`

Definicja:

```text
liczba PRODUCT posiadających SDS.status = CURRENT
```

Jeden PRODUCT może posiadać maksymalnie jeden CURRENT SDS.

Wartość procentowa, jeśli prezentowana:

```text
PRODUCT z CURRENT SDS
/
PRODUCT w aktualnym zakresie filtrów
```

### Status SDS w dashboardzie

Na poziomie produktu stosujemy pochodny stan raportowy:

```text
MA CURRENT SDS
BRAK CURRENT SDS
```

Nie używamy `ARCHIVED` jako statusu produktu.

---

## 8. KPI — `BHP zatwierdzone`

Produkt jest liczony jako `BHP zatwierdzone`, gdy:

```text
PRODUCT
→ posiada CURRENT SDS
→ dla tego CURRENT SDS istnieje BHP_DECISION.record_status = CURRENT
→ decision_status = APPROVED
```

Wartość procentowa, jeśli prezentowana:

```text
BHP APPROVED
/
PRODUCT z CURRENT SDS
```

Nie przenosi się decyzji BHP ze starszego ARCHIVED SDS.

---

## 9. Status BHP — kategorie dashboardu

Dashboard nie tworzy nowych statusów domenowych.

Do prezentacji analitycznej stosuje się trzy kategorie pochodne:

```text
APPROVED
REJECTED
BRAK DECYZJI
```

Znaczenie:

```text
APPROVED
= CURRENT BHP_DECISION dla CURRENT SDS ma decision_status APPROVED

REJECTED
= CURRENT BHP_DECISION dla CURRENT SDS ma decision_status REJECTED

BRAK DECYZJI
= PRODUCT posiada CURRENT SDS,
  ale nie posiada CURRENT BHP_DECISION dla tego SDS
```

Nie stosujemy kategorii:

```text
W TRAKCIE
```

ponieważ obecny model BHP nie posiada takiego statusu.

---

## 10. KPI — `Braki / do uzupełnienia`

KPI liczy:

```text
DISTINCT PRODUCT
```

które spełniają co najmniej jeden warunek wymagający uwagi.

Jednego produktu nie liczymy wielokrotnie.

Warunki:

### B1 — brak CURRENT SDS

```text
PRODUCT bez SDS.status = CURRENT
```

### B2 — brak decyzji BHP

```text
PRODUCT ma CURRENT SDS
i brak CURRENT BHP_DECISION dla tego SDS
```

### B3 — brak aktywnego miejsca stosowania

Dotyczy wyłącznie PRODUCT:

```text
usage_status = ACTIVE
lub
usage_status = PENDING_APPROVAL
```

Warunek:

```text
brak powiązania z ACTIVE USAGE_LOCATION
```

PRODUCT `REJECTED` i `INACTIVE` nie są oznaczane jako brak lokalizacji tylko dlatego, że nie posiadają aktywnego przypisania.

### B4 — niedostępny dokument źródłowy

Produkt wymaga uwagi, jeśli kontrolowany read wykrywa:

```text
CURRENT SDS file = MISSING
lub
CURRENT BHP_DECISION evidence file = MISSING
```

Brak fizycznego pliku nie usuwa rekordu historycznego.

---

## 11. `Stanowiska aktywne`

Definicja:

```text
COUNT(USAGE_LOCATION WHERE status = ACTIVE)
```

Nie jest to liczba relacji `PRODUCT_USAGE_LOCATION`.

Jedna aktywna lokalizacja liczona jest jeden raz niezależnie od liczby przypisanych produktów.

---

## 12. Wykres — `Produkty wg producenta`

Definicja:

```text
MANUFACTURER
→ COUNT(DISTINCT PRODUCT)
```

Wykres korzysta z aktualnego zakresu filtrów.

Producent jest osobnym obiektem Core.

Nie agregujemy po swobodnym tekście producenta.

---

## 13. Wykres — `Status BHP`

Wykres przedstawia rozkład:

```text
APPROVED
REJECTED
BRAK DECYZJI
```

dla produktów posiadających CURRENT SDS.

Produkty bez CURRENT SDS nie są sztucznie klasyfikowane jako `BRAK DECYZJI BHP`.

Ich problem jest prezentowany osobno jako:

```text
BRAK CURRENT SDS
```

w sekcji `Wymaga uwagi`.

---

## 14. Wykres — `Nowe / zaktualizowane SDS`

Dla MVP używamy:

```text
SDS.registered_at
```

a nie `issue_date`.

Powód:

```text
issue_date może być NULL
i opisuje dokument producenta,
nie moment zdarzenia w MSDS Manager
```

### 14.1. Nowe SDS

`Nowe SDS` oznacza:

```text
pierwszy zarejestrowany SDS dla PRODUCT
```

w danym okresie.

### 14.2. Zaktualizowane SDS

`Zaktualizowane SDS` oznacza:

```text
kolejny zarejestrowany SDS dla istniejącego PRODUCT
```

który w kontrolowanym workflow staje się nowym CURRENT, a poprzedni CURRENT przechodzi do ARCHIVED.

Wykres mierzy zdarzenia rejestracji SDS w systemie.

---

## 15. Semantyka filtra czasu

`Zakres dat` nie jest filtrem historycznego stanu całego dashboardu.

Dla MVP oznacza:

```text
OKRES ZDARZEŃ SDS
```

i wpływa przede wszystkim na wykres:

```text
Nowe / zaktualizowane SDS
```

KPI current-state:

```text
Produkty ogółem
SDS CURRENT
BHP zatwierdzone
Braki / do uzupełnienia
Stanowiska aktywne
```

nie zmieniają znaczenia na „stan na wskazaną datę”.

Jeżeli UX zachowuje pole u góry dashboardu, etykieta powinna jasno komunikować znaczenie, np.:

```text
Okres trendu SDS
```

a nie sugerować snapshot historyczny.

---

## 16. Filtr `Producent`

Filtr ogranicza:

```text
PRODUCT
```

do wybranego `MANUFACTURER`.

Wpływa na KPI, wykresy, alerty i zestawienia dotyczące produktów.

Nie zmienia globalnej definicji liczby wszystkich USAGE_LOCATION, chyba że UI jawnie prezentuje:

```text
Stanowiska dla wybranego producenta
```

Dla spójności MVP rekomendowane jest, aby KPI `Stanowiska aktywne` po wyborze producenta liczył:

```text
DISTINCT ACTIVE USAGE_LOCATION
powiązane z produktami tego producenta
```

---

## 17. Filtr `Status SDS`

Dozwolone wartości raportowe:

```text
Wszystkie
Ma CURRENT SDS
Brak CURRENT SDS
```

Nie udostępnia się filtra `ARCHIVED` jako statusu bieżącego produktu.

Historia SDS pozostaje osobnym poziomem danych.

---

## 18. Filtr `Status BHP`

Dozwolone wartości:

```text
Wszystkie
APPROVED
REJECTED
Brak decyzji
```

Nie dodaje się `W trakcie`.

---

## 19. Filtr `Lokalizacja`

Filtr działa względem:

```text
USAGE_LOCATION
```

Dla bieżącej analityki standardowo prezentuje lokalizacje:

```text
ACTIVE
```

Opcjonalna pozycja:

```text
Brak aktywnej lokalizacji
```

może służyć do diagnostyki braków.

Lokalizacje `INACTIVE` nie uczestniczą w bieżącej analityce miejsc stosowania.

---

## 20. Sekcja `Wymaga uwagi`

Minimalny zakres kart:

```text
Brak CURRENT SDS
Brak decyzji BHP
Brak aktywnego miejsca stosowania
Niedostępny dokument źródłowy
```

UX może połączyć dwa ostatnie typy plików w jedną kartę:

```text
Niedostępny dokument
```

z rozróżnieniem:

```text
SDS
EVIDENCE
```

w widoku szczegółowym.

Każda liczba oznacza:

```text
COUNT(DISTINCT PRODUCT)
```

dla danego problemu.

---

## 21. Podsumowanie wg producenta

Dashboard może prezentować agregacyjną tabelę:

| Producent | Produkty | SDS CURRENT | BHP APPROVED | Braki | Ostatni SDS |
|---|---:|---:|---:|---:|---|

Znaczenie:

```text
Produkty
= COUNT DISTINCT PRODUCT producenta

SDS CURRENT
= PRODUCT producenta z CURRENT SDS

BHP APPROVED
= PRODUCT producenta spełniające regułę z §8

Braki
= DISTINCT PRODUCT producenta spełniające B1-B4

Ostatni SDS
= MAX(SDS.registered_at) dla produktów producenta
```

### Korekta etykiety UX

Zamiast niejednoznacznego:

```text
Ostatnia aktualizacja
```

rekomendowana jest etykieta:

```text
Ostatni SDS
```

lub:

```text
Ostatnia rejestracja SDS
```

ponieważ jest jednoznacznie oparta na istniejącej dacie `SDS.registered_at`.

---

## 22. Nazwa tabeli agregacyjnej a szczegółowe `Zestawienie zbiorcze`

Aby nie utracić wcześniej zatwierdzonego znaczenia raportu:

```text
PRODUCT × USAGE_LOCATION
```

rekomenduje się nazwać agregacyjną tabelę producentów:

```text
Podsumowanie producentów
```

a określenie:

```text
Zestawienie zbiorcze
```

zachować dla szczegółowej warstwy raportowej `PRODUCT × USAGE_LOCATION`.

Dopuszczalny UX:

```text
Analizy
├── Dashboard
│   ├── KPI
│   ├── wykresy
│   ├── Wymaga uwagi
│   └── Podsumowanie producentów
│
└── Zestawienie zbiorcze
    └── PRODUCT × USAGE_LOCATION
```

Może to być jeden ekran z sekcjami lub dwa podwidoki. TDR-009 dobierze minimalne rozwiązanie zgodne z zatwierdzonym UX.

---

## 23. Ochrona przed podwójnym liczeniem

Agregacje produktowe używają:

```text
DISTINCT product_id
```

gdy join do:

```text
SDS
BHP_DECISION
PRODUCT_USAGE_LOCATION
USAGE_LOCATION
```

mógłby zwielokrotnić rekord PRODUCT.

Nie wolno interpretować liczby relacji `PRODUCT × LOCATION` jako liczby produktów.

---

## 24. NO_DATA / brak danych

Dashboard nie zamienia braku danych na wynik negatywny.

Przykłady:

```text
brak CURRENT SDS
≠ ARCHIVED SDS

brak BHP_DECISION
≠ REJECTED

brak aktywnej lokalizacji
≠ INACTIVE PRODUCT

MISSING file
≠ usunięty rekord
```

---

## 25. Relacja do ANALYTICS-03

BDR-009 nie implementuje `Stan na dzień`.

Zachowuje wcześniejszą zasadę:

```text
Zestawienie zbiorcze
= CURRENT STATE

Stan na dzień
= ręczny historyczny snapshot / przegląd
```

Po wdrożeniu ANALYTICS-03 szczegółowe `Zestawienie zbiorcze` może prezentować pomocniczo:

```text
MAX
Stan na dzień
Różnica +/-
```

bez automatycznej zmiany MAX.

---

## 26. Model techniczny

Dla MVP obowiązuje zatwierdzony kierunek:

```text
MODEL A — DYNAMIC READ MODEL
```

BDR-009 nie tworzy:

```text
analytics schema
materialized view
data warehouse
ETL
nowych tabel
```

Techniczny sposób zapytań i kompozycji należy do TDR-009.

---

## 27. Poza zakresem

BDR-009 nie rozstrzyga:

- `ANALYTICS-03 — Stan na dzień`,
- snapshotów przeglądów,
- historycznego `as-of`,
- eksportu do konkretnego formatu,
- automatycznych ocen ryzyka,
- REACH,
- R8,
- parsera SDS,
- AI,
- polityki uprawnień.

---

## 28. Zatwierdzone decyzje Architekta

Architekt Operacyjny zatwierdził:

```text
D1. Zachować dwa poziomy:
    dashboard summary + szczegółowe PRODUCT × USAGE_LOCATION.

D2. Tabelę producentów nazwać:
    "Podsumowanie producentów",
    nie "Zestawienie zbiorcze".

D3. Zakres dat interpretować jako:
    "Okres trendu SDS",
    a nie historyczny stan dashboardu.

D4. Status BHP na wykresie:
    APPROVED / REJECTED / BRAK DECYZJI,
    bez "W TRAKCIE".

D5. Braki = DISTINCT PRODUCT spełniające B1-B4.

D6. "Ostatnia aktualizacja" zastąpić:
    "Ostatni SDS" / "Ostatnia rejestracja SDS".
```

---

## 29. Status

```text
BDR-009 v1.0-approved
APPROVED
```

Następny krok:

```text
TDR-009
→ dynamiczny read model
→ query contracts
→ kompozycja dashboardu
→ walidacja i granice wydajności
```
