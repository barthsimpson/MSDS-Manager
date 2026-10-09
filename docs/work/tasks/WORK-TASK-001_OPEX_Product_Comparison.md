# WORK-TASK-001 — Porównanie SDS OPEX z MSDS Manager

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED  
**Tryb:** READ-ONLY / COMPARISON  
**Governance:** `WORK-GOV-001_Zasady_pracy_Cerberus_Work_v1.0-approved.md`

## 1. Cel

Zweryfikować, czy produkt opisany w jednym wskazanym SDS istnieje już w MSDS Manager.

Na tym etapie NIE rejestruj SDS i NIE zapisuj żadnych danych.

## 2. Dokument źródłowy

Użyj wyłącznie pliku:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\sds_Work\T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf
```

Dane identyfikacyjne potwierdzone wcześniej:

```text
Nazwa produktu:
OPEX® Acrylic Clear Metal Lacquer

Kod produktu:
T82C13

Producent / eksporter:
The Sherwin-Williams Company

Przedstawiciel w UE:
Valspar B.V.

Data SDS:
25, Listopad, 2022

Wersja:
8
```

Jeżeli przy ponownym odczycie dokumentu stwierdzisz sprzeczność z powyższymi wartościami:

```text
STOP / BLOCKED
```

i opisz sprzeczność w raporcie.

## 3. Zadanie

1. Otwórz lokalny MSDS Manager w trybie odczytu.
2. Przejdź do rejestru produktów.
3. Wyszukaj produkt przy użyciu danych identyfikacyjnych z SDS, w szczególności:
   - `OPEX Acrylic Clear Metal Lacquer`,
   - `T82C13`,
   - `The Sherwin-Williams Company`.
4. Nie ograniczaj się wyłącznie do identycznego zapisu znak po znaku, ale nie zgaduj podobieństwa biznesowego.
5. Jeżeli znajdziesz potencjalny rekord, odczytaj wyłącznie:
   - nazwę produktu,
   - producenta,
   - status produktu,
   - dane CURRENT SDS, jeśli są widoczne:
     - data,
     - rewizja,
     - nazwa pliku.
6. Nie edytuj rekordu.
7. Nie otwieraj formularza zapisu nowego SDS, jeśli wymaga to rozpoczęcia operacji zapisu.
8. Nie twórz nowego produktu.
9. Nie podejmuj decyzji BHP.

## 4. Klasyfikacja wyniku

Wybierz dokładnie jeden wynik:

```text
EXISTING_PRODUCT
```

gdy istnieje jeden jednoznaczny rekord odpowiadający produktowi z SDS.

```text
NO_MATCH
```

gdy nie znaleziono odpowiadającego rekordu.

```text
AMBIGUOUS
```

gdy istnieje więcej niż jeden możliwy rekord albo zgodność nie jest wystarczająco jednoznaczna.

```text
BLOCKED
```

gdy nie można wykonać porównania z powodów technicznych lub dostępowych.

## 5. Raport

Zapisz raport wyłącznie tutaj:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\reports\WORK-RAP-002_OPEX_Product_Comparison.md
```

Minimalna treść raportu:

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
<nazwa / producent / status / CURRENT SDS jeśli dostępne>

RESULT:
EXISTING_PRODUCT / NO_MATCH / AMBIGUOUS / BLOCKED

HUMAN REVIEW ITEMS:
<tylko jeśli potrzebne>
```

## 6. STOP

Po zapisaniu raportu:

```text
ZATRZYMAJ SIĘ.
```

Nie przechodź do:
- tworzenia produktu,
- dodawania SDS,
- nowej rewizji,
- analizy Safety Profile,
- analizy składników,
- decyzji BHP,
- kolejnego pliku SDS.
