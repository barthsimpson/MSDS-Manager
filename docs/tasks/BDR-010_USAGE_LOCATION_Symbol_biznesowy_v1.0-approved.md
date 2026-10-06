# BDR-010 — Symbol biznesowy USAGE_LOCATION

**Projekt:** MSDS Manager  
**Dokument:** BDR-010  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-05  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

## 1. Cel

Rozszerzyć `USAGE_LOCATION` o krótki symbol biznesowy nadawany przez użytkownika, tak aby w normalnym interfejsie nie prezentować technicznego UUID jako identyfikatora lokalizacji.

Obecny model:

```text
USAGE_LOCATION
├── location_id
├── location_name
└── status
```

Docelowy model:

```text
USAGE_LOCATION
├── location_id
├── location_code
├── location_name
└── status
```

## 2. Decyzja

`location_id` pozostaje technicznym, niezmiennym UUID używanym przez bazę, relacje i historię.

`location_code` jest krótkim symbolem biznesowym nadawanym przez użytkownika.

Przykład:

```text
MZT | Magazyn Techniczny
UTR | Warsztat UTR
REG | Regeneracja
```

W normalnym UI użytkownik identyfikuje miejsce przez `location_code + location_name`, a nie przez UUID.

## 3. Reguły `location_code`

`location_code`:

- jest wymagane w docelowym modelu,
- jest unikalne w systemie,
- jest nadawane świadomie przez użytkownika,
- nie zastępuje `location_id` jako PK/FK,
- nie jest automatycznie generowane z nazwy,
- nie może być zgadywane przez migrację,
- jest stabilnym oznaczeniem referencyjnym.

Minimalny format:

```text
1–32 znaki
A–Z
0–9
-
_
```

Application normalizuje:

```text
trim
→ uppercase
```

## 4. Lifecycle

BDR-010 nie zmienia lifecycle:

```text
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Dezaktywacja i reaktywacja zachowują ten sam `location_id` i `location_code`.

## 5. Istniejące dane

Istniejące rekordy nie posiadają `location_code`.

Nie wolno:

```text
zgadywać symbolu z location_name
używać fragmentu UUID
generować technicznego placeholdera jako symbolu biznesowego
```

Przejście:

```text
schema foundation
→ legacy może przejściowo mieć NULL
→ użytkownik uzupełnia symbole
→ walidacja kompletności
→ finalne NOT NULL
```

## 6. Docelowy UX

```text
Symbol | Lokalizacja | Status | Akcja
--------------------------------------
MZT    | Magazyn Techniczny | ACTIVE   | Dezaktywuj
UTR    | Warsztat UTR       | ACTIVE   | Dezaktywuj
REG    | Regeneracja        | INACTIVE | Reaktywuj
```

UUID nie jest kolumną biznesową.

Akcja lifecycle musi należeć do konkretnego wiersza.

## 7. Tworzenie

Nowa lokalizacja wymaga:

```text
Symbol lokalizacji
Nazwa lokalizacji
```

Nowy rekord otrzymuje `ACTIVE`.

Bez poprawnego i unikalnego symbolu nowa lokalizacja nie może zostać utworzona.

## 8. Historia

`location_id` pozostaje stabilnym kluczem dla historii.

W MVP symbol nie jest zwykłym polem swobodnie edytowalnym. Ewentualna korekta symbolu wymaga osobnego kontrolowanego działania.

BDR-010 nie rozszerza historii o wersjonowanie `location_code`.

## 9. Ochrona zakresu

BDR-010 nie zmienia PRODUCT, PRODUCT_USAGE_LOCATION, ilości, SDS, BHP ani ANALYTICS.

Nie tworzy hierarchii lokalizacji.

## 10. Status

```text
BDR-010
VERSION: 1.0-approved
STATUS: APPROVED
```
