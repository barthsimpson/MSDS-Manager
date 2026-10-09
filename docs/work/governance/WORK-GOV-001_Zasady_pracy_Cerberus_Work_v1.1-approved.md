# WORK-GOV-001 — Zasady pracy Cerberus × ChatGPT Work

**Projekt:** MSDS Manager  
**Wersja:** 1.1-approved  
**Status:** APPROVED  
**Data:** 2026-10-08  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus  

## 1. Cel

Ustalić prosty, powtarzalny standard pracy ChatGPT Work przy zadaniach wykonywanych na lokalnym projekcie MSDS Manager.

Standard ma ograniczyć:
- przypadkowe rozszerzanie zakresu,
- zapisywanie raportów w domyślnych lokalizacjach Work,
- utratę śledzenia źródeł i raportów,
- powtarzające się ustalenia sesyjne,
- nieautoryzowane decyzje architektoniczne lub biznesowe.

## 2. Role

### Człowiek — Architekt Operacyjny
- definiuje cel biznesowy,
- zatwierdza zakres i decyzje,
- zatwierdza zapis danych do MSDS Manager,
- rozstrzyga przypadki `REQUIRES HUMAN REVIEW`.

### Cerberus
- przygotowuje kolejne, pojedyncze zadania dla Work,
- pilnuje kolejności,
- definiuje granice i STOP conditions,
- przegląda raport Work,
- odróżnia obserwację od decyzji projektowej,
- zatwierdza przejście do następnego kroku po decyzji Architekta.

### ChatGPT Work
- wykonuje wyłącznie jawnie zlecony krok,
- korzysta wyłącznie ze wskazanych plików / aplikacji,
- nie zgaduje brakujących danych,
- zgłasza niejednoznaczności,
- tworzy raport w ustalonej lokalizacji projektu,
- zatrzymuje się po wykonaniu zadania.

### Codex
- pozostaje wykonawcą zmian kodu aplikacji,
- Work nie zastępuje Codexa.

## 3. Granice odpowiedzialności Work

Work może:
- czytać wskazane dokumenty SDS,
- odczytywać informacje z aplikacji,
- porównywać dane,
- przygotowywać propozycje,
- raportować rozbieżności i niepewności.

Work nie może bez osobnego jawnego polecenia:
- modyfikować kodu,
- modyfikować schema / PostgreSQL,
- podejmować decyzji BHP,
- zmieniać Core / BDR / TDR / governance,
- rozstrzygać niejednoznaczności zamiast człowieka,
- zapisywać danych do MSDS Manager,
- usuwać / przenosić / nadpisywać plików źródłowych SDS.

## 4. Lokalny obszar roboczy Work i stałe dostępy

Root projektu:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager
```

Work powinien mieć nadane stałe uprawnienia do poniższych katalogów roboczych.

### 4.1. Macierz dostępu

| Katalog | Tryb dostępu Work | Przeznaczenie |
|---|---|---|
| `docs\work\governance\` | READ | obowiązujące zasady, governance i instrukcje startowe |
| `docs\work\tasks\` | READ | zadania przygotowane dla Work |
| `docs\work\reports\` | READ + WRITE | zapis i późniejszy odczyt raportów Work |
| `docs\sds_Work\` | READ | źródłowe dokumenty SDS przeznaczone do kontrolowanej analizy |

Pełne ścieżki:

```text
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\governance
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\tasks
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\work\reports
C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\sds_Work
```

### 4.2. Zasada trwałego dostępu

Jeżeli środowisko Work umożliwia zapamiętanie uprawnienia do folderu, dla powyższych katalogów należy nadać dostęp trwały / stały w zakresie zgodnym z macierzą.

Celem jest ograniczenie powtarzających się przerw i pytań o dostęp do tych samych plików podczas kolejnych kroków tego samego procesu.

### 4.3. Dostęp techniczny nie jest autoryzacją biznesową

Nadanie Work stałego dostępu do katalogu:

```text
NIE oznacza
zgody na dowolne użycie wszystkich znajdujących się w nim plików.
```

Obowiązuje rozdzielenie:

```text
PERMISSION
= Work technicznie może odczytać / zapisać w danym katalogu

TASK SCOPE
= Work może wykonać wyłącznie działania jawnie wskazane w bieżącym zadaniu
```

Przykład:

```text
Work ma READ do całego docs\sds_Work\
ale WORK-TASK wskazuje jeden konkretny SDS
→ Work analizuje tylko ten wskazany SDS.
```

### 4.4. Ograniczenia dostępu

Work bez osobnej decyzji nie otrzymuje stałego dostępu do:

```text
repozytorium kodu poza wskazanymi katalogami roboczymi
plików .env
sekretów / kluczy
backupów bazy
dumpów PostgreSQL
katalogów operatora spoza projektu
innych lokalizacji użytkownika
```

Jeżeli nowe zadanie wymaga dodatkowego katalogu:

```text
STOP
→ zgłoś potrzebę dostępu
→ decyzja Architekta
→ aktualizacja governance, jeśli dostęp ma być stały
```

Work nie przenosi plików SDS do `docs\work`.

## 5. Miejsca zapisu

### Governance
```text
docs\work\governance\
```

### Zadania
```text
docs\work\tasks\
```

### Raporty
```text
docs\work\reports\
```

Domyślna lokalizacja zapisu Work nie jest lokalizacją docelową projektu.

## 6. Zasada łatwego udostępniania raportów do Cerberusa

```text
Work
→ zapisuje raport w docs\work\reports\
→ zatrzymuje się
→ Człowiek dołącza ten konkretny plik .md do czatu z Cerberusem
→ Cerberus wykonuje review
→ dopiero potem powstaje następne zadanie
```

Nie kopiujemy treści raportu ręcznie, jeżeli plik `.md` jest dostępny.

## 7. Zasada jednego kroku

Cerberus przekazuje Work tylko jeden bieżący krok.

Obowiązuje:

```text
TASK
→ WORK EXECUTION
→ REPORT
→ CERBERUS REVIEW
→ ARCHITEKT DECISION
→ NEXT TASK
```

Work nie rozpoczyna kolejnego etapu samodzielnie.

## 8. Zasada źródeł

Dla każdej wartości odczytanej z SDS Work podaje, jeśli możliwe:

```text
plik
strona
sekcja / miejsce odczytu
wartość
```

Nazwa pliku:
- służy do identyfikacji dokumentu,
- nie jest dowodem daty, wersji ani nazwy produktu, jeżeli treść PDF tego nie potwierdza.

## 9. Statusy wyników Work

```text
READY FOR COMPARISON
REQUIRES HUMAN REVIEW
BLOCKED
```

Work nie tworzy własnych statusów biznesowych MSDS Manager.

## 10. Obserwacja != decyzja projektowa

Raport Work może zawierać sekcję:

```text
OBSERVATIONS / PROPOSALS
```

ale takie uwagi:
- nie zmieniają Core,
- nie zmieniają BDR/TDR,
- nie stają się wymaganiami implementacyjnymi,
- wymagają osobnej decyzji Architekta i Cerberusa.

Work powinien formułować je jako:

```text
obserwacja:
propozycja do oceny:
możliwa luka:
```

a nie jako obowiązującą decyzję systemową.

## 11. STOP conditions

Work zatrzymuje zadanie i raportuje, gdy:
- wskazany plik jest niedostępny,
- dokument zawiera kilka kart SDS i nie można jednoznacznie wskazać właściwej,
- wymagane pole jest niejednoznaczne,
- wykonanie wymaga dostępu poza wskazanym zakresem,
- wykonanie wymaga zapisu / modyfikacji nieautoryzowanych danych,
- pojawia się konflikt z instrukcją zadania,
- potrzebna jest decyzja biznesowa, BHP lub architektoniczna.

## 12. Raport minimalny

Każdy raport Work zawiera:

```text
TASK / SCOPE
FILES USED
RESULT
SOURCE EVIDENCE
STATUS
HUMAN REVIEW ITEMS — jeśli dotyczy
OBSERVATIONS / PROPOSALS — opcjonalnie
```

## 13. Reguła startowa każdej sesji Work

Przed wykonaniem zadania Work:

```text
1. odczytuje WORK-GOV-001 z docs\work\governance\
2. odczytuje jeden bieżący WORK-TASK-XXX z docs\work\tasks\
3. respektuje zakres plików / aplikacji wskazany w TASK
4. zapisuje raport do docs\work\reports\
5. korzysta z nadanych stałych dostępów zgodnie z macierzą z sekcji 4
```

Jeżeli:
- governance jest niedostępny,
- task jest niedostępny,
- wymagany SDS jest niedostępny,
- raportu nie można zapisać w `docs\work\reports\`,
- wykonanie wymaga katalogu spoza zatwierdzonej macierzy,

obowiązuje:

```text
STOP
→ zgłoś brak / potrzebę dostępu
→ nie obchodź ograniczenia inną lokalizacją
```

## 14. Aktualny PoC

Pierwszy PoC dotyczy kontrolowanego odczytu i późniejszego transferu SDS do MSDS Manager.

Na początku:

```text
Work może analizować SDS
Work może przygotować dane
Work może porównywać z aplikacją

Work zatrzymuje się przed finalnym zapisem danych
```

Decyzja BHP pozostaje zawsze poza odpowiedzialnością Work.

## 15. Authorization boundary

Ten dokument stanowi zatwierdzony standard startowy dla zadań Work w projekcie MSDS Manager.

Sam dokument nie autoryzuje żadnego konkretnego zadania Work.
