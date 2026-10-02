# PATCH-012 — ANALYTICS Dashboard Density + Navigation Polish

**Projekt:** MSDS Manager  
**Obszar:** ANALYTICS-01 / ANALYTICS-02  
**Patch:** PATCH-012  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
PATCH
```

---

## CONTEXT

Po wdrożeniu PATCH-011 przeprowadzono Physical UX Review modułu `Analizy`.

Ocena:

```text
LOCAL NAVIGATION      PASS
ZESTAWIENIE ZBIORCZE  PASS
DASHBOARD UX          PARTIAL PASS
```

Kierunek layoutu jest zatwierdzony.

Do dopracowania pozostają wyłącznie szczegóły prezentacji i skalowania:

- przyciski lokalnej nawigacji są zbyt wysokie / dominujące,
- aktywny przycisk ma zbyt alarmowy czerwony kolor,
- font przycisków jest zbyt mały względem szerokości elementu,
- dashboard jest zbyt wysoki przy standardowym zoom 100%,
- odstępy i wysokości kart / wykresów można skondensować bez utraty czytelności.

---

## GOAL

Dopracować prezentację `Analizy` tak, aby przy standardowym zoom:

```text
100%
```

moduł wyglądał bardziej zwarto, proporcjonalnie i profesjonalnie.

PATCH-012 nie zmienia struktury dashboardu ani logiki danych.

---

## AUTHORITATIVE CONTEXT

Przeczytaj wyłącznie:

1. `PATCH-011_REPORT.md`
2. `TASK-042_REPORT.md`
3. `ANALYTICS-01_UX_CONTRACT_Zestawienie_zbiorcze_v1.0-approved.md`
4. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
5. root `AGENTS.md`

Nie wykonuj repo-wide discovery.

---

## KNOWN STARTING POINTS

Minimalnie:

```text
app/presentation/streamlit/analytics.py
tests/unit/test_task042_streamlit_analytics.py
```

Opcjonalnie:

```text
app/presentation/streamlit/main.py
```

wyłącznie jeśli lokalny CSS / composition tego wymaga.

---

## DO

### 1. Lokalna nawigacja — wysokość i proporcja

Zmniejsz wizualną wysokość przycisków:

```text
Dashboard
Zestawienie zbiorcze
Raport przeglądu
```

Cel:

- mniej pionowej przestrzeni,
- przyciski mają wyglądać jak lokalne taby / segment control,
- nie jak główne CTA.

Nie zmniejszaj obszaru kliknięcia do poziomu utrudniającego obsługę.

---

### 2. Aktywny przycisk — neutralny kolor

Usuń czerwony kolor aktywnego przycisku.

Aktywny stan ma być neutralny / spokojny, np.:

```text
ciemny szary
neutralny granat
jasne neutralne tło + mocniejszy tekst
```

Nie używaj kolorów kojarzonych z:

```text
ERROR
ALERT
REJECTED
```

Aktywny stan ma nadal być jednoznacznie widoczny.

---

### 3. Czcionka lokalnej nawigacji

Zwiększ font przycisków względem obecnego stanu.

Cel:

```text
czytelniejsza lokalna nawigacja
bez zwiększania wysokości przycisku
```

Preferowany kierunek:

```text
większy font
mniejszy vertical padding
```

Nie używaj bardzo ciężkiego bold.

---

### 4. Hierarchia tytułów

Zachowaj:

```text
MSDS Manager
Analizy
[ local navigation ]

Dashboard / Zestawienie zbiorcze / Raport przeglądu
```

Zmniejsz zbędne odstępy pionowe pomiędzy:

```text
Analizy
local navigation
tytuł aktywnego widoku
opis
```

Bez zmniejszania czytelności.

---

### 5. Filtry — kondensacja

Panel filtrów ma być niższy.

Dopuszczalne:

- mniejszy vertical padding sekcji,
- ciaśniejsze odstępy label → control,
- kompaktowe odstępy pomiędzy pierwszym i drugim rzędem filtrów,
- zachowanie dwóch czytelnych rzędów.

Nie zmieniaj pól ani semantyki filtrów.

---

### 6. KPI cards — gęstość

Zmniejsz wysokość kart KPI.

Zachowaj:

```text
label
duża wartość
krótki opis
```

Cel:

```text
5 kart w jednym rzędzie
bardziej zwarty blok
bez utraty czytelności
```

Nie zmieniaj treści KPI.

---

### 7. Wykresy — wysokość

Zmniejsz wysokość trzech paneli wykresów około:

```text
10–15%
```

lub do najmniejszej wartości, która zachowuje:

- czytelne osie,
- legendy,
- pełne nazwy producentów,
- poprawny donut,
- widoczne linie trendu.

Nie zmieniaj danych ani typów wykresów.

---

### 8. Cel skalowania dashboardu

Przy:

```text
browser zoom = 100%
typowa rozdzielczość desktopowa
```

na pierwszym ekranie powinny być widoczne:

```text
local navigation
Dashboard heading
filtry
KPI
wykresy
oraz przynajmniej początek sekcji "Wymaga uwagi"
```

Bez ręcznego zoom-out.

Nie optymalizuj pod pojedynczy screenshot kosztem ogólnej czytelności.

---

### 9. Zestawienie zbiorcze

Nie zmieniaj struktury widoku.

Dopuszczalne wyłącznie kosmetyczne dostosowanie lokalnej nawigacji i nagłówków.

Tabela:

```text
PRODUCT × USAGE_LOCATION
```

pozostaje bez zmian funkcjonalnych.

---

## DO NOT

PATCH-012 nie obejmuje:

```text
zmian KPI
zmian filtrów
zmian wykresów biznesowych
zmian read model
zmian TASK-041
zmian BDR/TDR
nowych query
schema change
migration
Core change
Domain change
Application business logic change
Infrastructure change
aktywnego eksportu
ANALYTICS-03
React
custom JS
new dependencies
globalnego redesignu aplikacji
```

Nie zmieniaj kolorów statusów biznesowych tylko dlatego, że zmieniamy kolor aktywnej zakładki.

---

## EXPECTED CHANGE SURFACE

Preferowany:

```text
app/presentation/streamlit/analytics.py
tests/unit/test_task042_streamlit_analytics.py
docs/task_reports/PATCH-012_REPORT.md
```

Opcjonalnie:

```text
app/presentation/streamlit/main.py
```

wyłącznie jeśli konieczne do local presentation styling.

---

## VALIDATION

```text
LEVEL 1 — PATCH
REPORT: SHORT
```

Potwierdź co najmniej:

1. trzy przyciski local navigation nadal działają,
2. aktywny przycisk nadal jest jednoznaczny,
3. aktywny przycisk nie używa czerwonego / alarmowego koloru,
4. font przycisków jest większy niż przed PATCH-012,
5. przyciski są niższe / bardziej zwarte,
6. Dashboard nadal zawiera wszystkie filtry, KPI i wykresy,
7. `Wymaga uwagi` nadal renderuje się bez zmian logiki,
8. `Zestawienie zbiorcze` pozostaje funkcjonalnie bez zmian,
9. `Raport przeglądu` nadal jest placeholderem,
10. focused TASK-042 / PATCH-011 UI tests pozostają PASS po dostosowaniu oczekiwań presentation.

Testy automatyczne nie zastępują physical UX review.

---

## STOP CONDITIONS

```text
STOP / BLOCKED
```

jeżeli:

1. poprawa layoutu wymaga nowej dependency,
2. wymagany byłby custom JS,
3. trzeba zmienić Application / Infrastructure,
4. trzeba zmienić read model,
5. CSS wymaga globalnego redesignu innych ekranów,
6. poprawa jednego widoku psuje nawigację lub inne ekrany.

---

## REPORT

Utwórz:

```text
docs/task_reports/PATCH-012_REPORT.md
```

Minimalny format:

```text
# PATCH-012 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

IMPLEMENTED:
- navigation sizing:
- active state color:
- navigation typography:
- filter density:
- KPI density:
- chart height:
- spacing:

VALIDATION:
- focused AppTest:
- regression:
- git diff --check:

SCOPE:
- Application change: NO
- Infrastructure change: NO
- schema change: NO
- migration: NONE
- Core change: NO
- new dependencies: NO

DEVIATIONS:
- ...

NEXT:
- READY FOR CERBERUS REVIEW + PHYSICAL UX REVIEW
```

---

## AUTHORIZATION

PATCH-012 jest:

```text
READY / NOT AUTHORIZED FOR EXECUTION
```

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj PATCH-012.
```

Po wykonaniu:

```text
Codex report
→ Cerberus review
→ Physical UX Review
→ closure ANALYTICS-01 / ANALYTICS-02
   albo ostatni mały PATCH prezentacyjny
```
