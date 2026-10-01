# PATCH-010 — Korekta referencji wersji CORE-001 / TDR-007

**Projekt:** MSDS Manager  
**Patch:** PATCH-010  
**Status:** READY / AUTHORIZED BY ARCHITEKT OPERACYJNY  
**Data:** 2026-10-01  
**Typ:** dokumentacyjny / no production code  
**Nadzór:** Cerberus — Agent Architekt  

---

## 1. Cel

Usunąć dwie niespójności redakcyjne powstałe podczas zatwierdzania:

1. `CORE-001 v1.3-approved` zawiera w sekcji statusowej stare odwołania do `v1.2-approved`.
2. `TDR-007 v1.1-approved` zawiera stare odwołania do `CORE-001 v1.3-draft` / `CORE-001 v1.2-approved`.

Patch nie zmienia żadnej decyzji biznesowej ani technicznej.

---

## 2. Do

### CORE-001

W zatwierdzonym `CORE-001 v1.3-approved`:

- sekcja statusowa ma wskazywać `CORE-001 v1.3-approved` jako aktualny dokument,
- tekst ma jasno stwierdzać, że v1.3 zastępuje v1.2 jako aktualne źródło Core,
- nie zmieniaj treści merytorycznej modelu.

### TDR-007

W `TDR-007 v1.1-approved`:

- `Podstawa Core` → `CORE-001 v1.3-approved`,
- sekcja kontekstu obowiązującego → `CORE-001 v1.3-approved`,
- usuń tekst sugerujący, że v1.3 nadal jest draftem,
- zachowaj wszystkie decyzje techniczne bez zmian.

---

## 3. Do not

Nie:
- zmieniaj numerów wersji,
- twórz nowej rewizji merytorycznej,
- zmieniaj schema,
- zmieniaj kodu,
- zmieniaj TASK-038,
- zmieniaj lifecycle BHP/SDS.

---

## 4. Walidacja

Potwierdź:

```text
CORE-001 → wszędzie aktualny status = v1.3-approved
TDR-007 → wszędzie podstawa Core = CORE-001 v1.3-approved
brak zmian merytorycznych
git diff --check = PASS
```

---

## 5. Authorization

Architekt Operacyjny zatwierdził wykonanie tej korekty dokumentacyjnej.
