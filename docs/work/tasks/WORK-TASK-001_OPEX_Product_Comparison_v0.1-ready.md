# WORK-TASK-001 — Porównanie SDS OPEX z rejestrem MSDS Manager

**Projekt:** MSDS Manager  
**Id:** WORK-TASK-001  
**Wersja:** 0.1-ready  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-09  
**Governance:** `WORK-GOV-001_Zasady_pracy_Cerberus_Work_v1.1-approved.md`  
**Tryb:** READ-ONLY / COMPARISON

---

## 1. Cel

Sprawdzić, czy produkt opisany w jednym wskazanym SDS istnieje już w MSDS Manager.

Na tym etapie:

```text
NIE rejestruj SDS
NIE twórz produktu
NIE zapisuj żadnych zmian
NIE podejmuj decyzji BHP
```

Rezultatem ma być wyłącznie klasyfikacja porównania oraz raport.

---

## 2. Obowiązujące źródła

Przed rozpoczęciem zadania przeczytaj i stosuj:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\governance\WORK-GOV-001_Zasady_pracy_Cerberus_Work_v1.1-approved.md
```

Dokument źródłowy SDS:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\sds_Work\T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf
```

Poprzedni raport analizy identyfikacyjnej:

```text
RAP-001_analiza_SDS_3M_OPEX.md
```

RAP-001 jest materiałem wejściowym do porównania, ale PDF SDS pozostaje źródłem nadrzędnym dla danych dokumentu.

---

## 3. Dane identyfikacyjne potwierdzone w RAP-001

Dla wskazanego SDS odczytano:

```text
Nazwa produktu:
OPEX® Acrylic Clear Metal Lacquer

Kod produktu:
T82C13

Producent / eksporter:
The Sherwin-Williams Company

Przedstawiciel w UE:
Valspar B.V.

Język:
polski

Data wydania / aktualizacji:
25, Listopad, 2022

Wersja:
8
```

Jeżeli podczas wykonywania zadania stwierdzisz sprzeczność pomiędzy PDF a powyższymi danymi:

```text
STOP / BLOCKED
```

Nie rozstrzygaj sprzeczności samodzielnie.

---

## 4. Zakres zadania

Wykonaj wyłącznie poniższe kroki:

1. Otwórz lokalny MSDS Manager.
2. Przejdź do rejestru produktów.
3. Wyszukaj produkt opisany w SDS, używając w szczególności:
   - nazwy produktu,
   - kodu `T82C13`,
   - producenta `The Sherwin-Williams Company`.
4. Jeżeli znajdziesz potencjalny rekord, odczytaj wyłącznie:
   - nazwę produktu,
   - kod produktu, jeżeli jest widoczny,
   - producenta,
   - status produktu,
   - dane CURRENT SDS, jeżeli są widoczne:
     - data SDS,
     - rewizja / wersja,
     - nazwa pliku.
5. Porównaj rekord aplikacji z dokumentem źródłowym.
6. Nadaj jeden status wyniku zgodnie z sekcją 5.
7. Zapisz raport zgodnie z sekcją 6.
8. Zatrzymaj się.

Nie analizuj innych produktów ani innych SDS.

---

## 5. Klasyfikacja wyniku

Wybierz dokładnie jeden status:

### `EXISTING_PRODUCT`

Użyj, gdy istnieje jeden jednoznaczny rekord PRODUCT odpowiadający produktowi z SDS.

### `NO_MATCH`

Użyj, gdy nie znaleziono rekordu odpowiadającego produktowi z SDS.

### `AMBIGUOUS`

Użyj, gdy:
- istnieje więcej niż jeden możliwy rekord,
- dane nie pozwalają jednoznacznie potwierdzić tożsamości produktu,
- występuje konflikt nazwy / kodu / producenta wymagający decyzji człowieka.

### `BLOCKED`

Użyj, gdy:
- MSDS Manager jest niedostępny,
- brakuje wymaganego dostępu,
- wykonanie porównania wymaga nieautoryzowanej operacji,
- występuje konflikt z governance lub niniejszym TASK.

---

## 6. Raport

Zapisz raport wyłącznie tutaj:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\reports\WORK-RAP-002_OPEX_Product_Comparison.md
```

Minimalna struktura:

```text
# WORK-RAP-002 — OPEX Product Comparison

TASK:
WORK-TASK-001

SOURCE SDS:
<pełna nazwa pliku>

SEARCH USED:
<jakich danych użyto do wyszukania>

MATCH FOUND:
YES / NO / AMBIGUOUS

MATCH DETAILS:
- nazwa:
- kod:
- producent:
- status produktu:
- CURRENT SDS:
  - data:
  - rewizja:
  - nazwa pliku:

COMPARISON:
<krótkie porównanie danych SDS z rekordem>

RESULT:
EXISTING_PRODUCT / NO_MATCH / AMBIGUOUS / BLOCKED

HUMAN REVIEW ITEMS:
<tylko jeśli wymagane>

OBSERVATIONS / PROPOSALS:
<opcjonalnie; nie są decyzją projektową>
```

---

## 7. DO NOT

Nie:

- twórz nowego PRODUCT,
- dodawaj SDS,
- twórz nowej rewizji SDS,
- edytuj danych istniejącego produktu,
- zapisuj danych do PostgreSQL,
- analizuj SAFETY_PROFILE,
- analizuj składników SDS,
- podejmuj decyzji BHP,
- otwieraj kolejnych SDS,
- zmieniaj kodu aplikacji,
- zmieniaj governance,
- formułuj decyzji architektonicznych.

---

## 8. STOP CONDITIONS

Zatrzymaj wykonanie i zapisz `BLOCKED`, jeżeli:

1. nie możesz odczytać `WORK-GOV-001 v1.1-approved`,
2. nie możesz odczytać wskazanego PDF,
3. nie możesz otworzyć MSDS Manager,
4. wymagane działanie wykracza poza READ-ONLY,
5. nie możesz zapisać raportu do `docs\work\reports`,
6. pojawia się niezgodność danych źródłowych wymagająca decyzji człowieka.

Nie obchodź blokady inną ścieżką.

---

## 9. Zakończenie

Po zapisaniu raportu:

```text
STOP
```

Nie rozpoczynaj następnego kroku bez nowego jawnego polecenia.

---

## 10. Authorization boundary

Ten dokument jest przygotowany do zatwierdzenia.

```text
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Samo istnienie pliku nie stanowi zgody na wykonanie zadania.
