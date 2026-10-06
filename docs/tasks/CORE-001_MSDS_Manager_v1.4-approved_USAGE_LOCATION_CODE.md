# CORE-001 — MSDS Manager — v1.4-approved — USAGE_LOCATION location_code

**Projekt:** MSDS Manager  
**Id dokumentu:** CORE-001  
**Wersja:** 1.4-approved  
**Status:** APPROVED  
**Data rewizji:** 2026-10-05  
**Dokument bazowy:** CORE-001 v1.3-approved  
**Podstawa decyzji:** BDR-010 v1.0-approved  

## 1. Zakres rewizji

Rewizja 1.4 rozszerza wyłącznie model `USAGE_LOCATION` o biznesowy symbol lokalizacji.

## 2. USAGE_LOCATION

```text
USAGE_LOCATION
├── location_id
├── location_code
├── location_name
└── status
```

`location_id`:
- techniczny UUID,
- niezmienny,
- PK/FK,
- niewidoczny jako podstawowa informacja biznesowa w normalnym UI.

`location_code`:
- krótki symbol biznesowy,
- nadawany przez użytkownika,
- wymagany w docelowym modelu,
- unikalny,
- normalizowany do uppercase,
- stabilny w normalnym workflow,
- nie zastępuje `location_id`.

`status` pozostaje `ACTIVE / INACTIVE`.

## 3. Integralność Core

Dodaje się reguły:

```text
35. Docelowa USAGE_LOCATION posiada niepusty location_code.
36. location_code jest unikalny.
37. location_code nie jest PK/FK.
38. Standardowy UI nie eksponuje location_id jako biznesowego identyfikatora.
39. Migracja legacy nie może zgadywać location_code.
```

## 4. Stan przejściowy

Dopuszcza się techniczny stan:

```text
location_code = NULL
```

wyłącznie dla rekordów istniejących przed wdrożeniem BDR-010.

Nowe lokalizacje po wdrożeniu Application muszą posiadać symbol.

## 5. Historia

Historia nadal opiera się na `location_id`.

`location_code` nie jest w tej rewizji osobno wersjonowany.

## 6. Status

```text
CORE-001
VERSION: 1.4-approved
STATUS: APPROVED
BASE: v1.3-approved
CHANGE: USAGE_LOCATION.location_code
```
