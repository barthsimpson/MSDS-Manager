# PATCH-015-R2 — UI Polish: ikony, hierarchia akcji i porządek Karty produktu

**Projekt:** MSDS Manager  
**Patch ID:** PATCH-015-R2  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI  

---

## 1. GOAL

Dopracować finalną ergonomię i spójność wizualną Karty produktu po `PATCH-015` i `PATCH-015-R1`, bez zmiany architektury ekranu ani logiki biznesowej.

Zakres:

```text
1. zamiana emoji w sidebarze na spójne ikony,
2. uporządkowanie górnego paska akcji Karty produktu,
3. stonowane kolory dashboardowe dla akcji,
4. wypełnione przyciski Dodaj / Edytuj,
5. przeniesienie „Dodaj miejsce” pod tabelę miejsc stosowania,
6. usunięcie dublowania edycji danych administracyjnych,
7. zachowanie wariantu B dla danych administracyjnych:
   jedna akcja „Edytuj” w nagłówku sekcji, bez dodatkowego rozwijania.
```

---

## 2. AUTHORITATIVE CONTEXT

Przeczytaj minimalnie:

1. `PATCH-015_Produkty_i_Karta_Produktu_Compact_UI.md`
2. `PATCH-015_REPORT.md`
3. `PATCH-015-R1_Typografia_Sidebar_Product_Card_UI.md`
4. `PATCH-015-R1_REPORT.md`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
6. root `AGENTS.md`

Zatwierdzone decyzje UX Architekta:

```text
Produkty → Karta produktu: ACCEPTED
Układ Karty produktu: ACCEPTED
Typografia / sidebar: ACCEPTED DIRECTION
Dane administracyjne: wariant B
```

---

## 3. KNOWN STARTING POINTS

Rozpocznij od:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/product_registry.py
```

oraz bezpośrednio powiązanych helperów stylu i testów UI.

Nie wykonuj repo-wide refactor.

---

## 4. SIDEBAR — IKONY

Usuń emoji / Unicode fallback użyty w `PATCH-015-R1`.

Zastosuj spójne ikony dostępne w aktualnym środowisku Streamlit lub przez istniejący mechanizm ikon.

Docelowe znaczenia:

```text
Produkty         → package / box
Dodaj SDS        → file-plus / document-plus
Decyzja BHP      → shield-check / check-circle
Stanowiska       → settings / gears
Widok nadzorczy  → eye / monitor / dashboard
Analizy          → chart / bar-chart
```

Dla `Stanowiska` preferowany symbol:

```text
gear / gears
```

Nie dodawaj nowej dependency tylko dla ikon.

Jeżeli obecny Streamlit nie daje stabilnego mechanizmu:

```text
STOP / BLOCKED
```

zamiast wracać do emoji.

---

## 5. GÓRNY PASEK AKCJI KARTY PRODUKTU

Akcje:

```text
Uzupełnij kod producenta
Korekta danych identyfikacyjnych
Dodaj nową rewizję SDS
Więcej akcji
```

mają być wizualnie związane z nagłówkiem produktu i umieszczone możliwie wysoko.

Preferowany układ:

```text
[Nazwa produktu + metadata/status]
[akcje w jednym rzędzie po prawej / pod metadata, ale nad kartami danych]
```

Nie pozostawiaj dużej pustej przestrzeni pomiędzy nagłówkiem a przyciskami.

---

## 6. KOLORY AKCJI — DASHBOARD STYLE

Wprowadź stonowaną hierarchię wizualną.

### Primary / główne akcje

Przykłady:

```text
Uzupełnij kod producenta
Dodaj miejsce
Edytuj
```

powinny mieć:

```text
delikatny fill
spokojny niebieski / granatowy tonal
czytelny kontrast
```

### Secondary

Przykłady:

```text
Korekta danych identyfikacyjnych
Dodaj nową rewizję SDS
```

mogą być:

```text
secondary fill / tonal fill / jasny outline z delikatnym tłem
```

### Destrukcyjne

```text
Usuń produkt
```

pozostaje w:

```text
Więcej akcji
```

i nie może konkurować wizualnie z podstawowymi akcjami.

Nie używaj agresywnych / jaskrawych kolorów.

Cel:

```text
spójny dashboard biznesowy
```

---

## 7. MIEJSCA STOSOWANIA

Przycisk:

```text
+ Dodaj miejsce
```

przenieś:

```text
POD tabelę miejsc stosowania
```

Preferowane wyrównanie:

```text
lewa lub prawa krawędź tabeli
```

ale musi być jednoznacznie czytelne, że akcja dotyczy tabeli powyżej.

Nie zmieniaj samej tabeli ani jej logiki.

---

## 8. DANE ADMINISTRACYJNE — WARIANT B

Zatwierdzony wariant:

```text
Nagłówek sekcji „Dane administracyjne”
                         [Edytuj]
```

Wymagania:

```text
- dokładnie jedna jawna akcja edycji,
- brak dodatkowego rozwijania / listwy „Edytuj dane administracyjne”,
- brak dublowania tej samej funkcji,
- obecne pola pozostają widoczne w trybie read-only.
```

Jeżeli istnieje obecna listwa / expander pełniący tę samą funkcję:

```text
usuń go z normalnego widoku
```

Po kliknięciu `Edytuj` użyj istniejącego, zatwierdzonego workflow edycji.

Nie twórz nowego use case.

---

## 9. PRZYCISKI LOKALNE

Przyciski sekcyjne:

```text
Dodaj miejsce
Edytuj
Pobierz SDS
```

powinny mieć wyraźniejszy fill / tonal style zamiast bardzo lekkiego outline.

Wymagania:

```text
- czytelne przy zoom 100%,
- spójne wysokości,
- spójne promienie / padding,
- bez przesadnej wysokości.
```

---

## 10. KARTA PRODUKTU — HIERARCHIA STATUSÓW

Bez zmiany danych można lekko uporządkować statusy w nagłówku:

```text
Status użytkowania
SDS CURRENT
Rewizja SDS
BHP
```

mogą być prezentowane jako kompaktowe badge/chip, jeśli można to zrobić lokalnie bez nowego komponentu.

Jeżeli wymaga to większej przebudowy:

```text
SKIP
```

Nie jest to warunek DONE.

---

## 11. EKRAN PRODUKTY

Nie zmieniaj zaakceptowanego zachowania:

```text
wybór wiersza
→ Otwórz kartę produktu
```

Nie dodawaj teraz:

```text
row-click
kolumny Akcje
ikony przejścia w wierszu
```

To pozostaje przyszłym refinementem.

---

## 12. DO NOT

Nie zmieniaj:

```text
Domain
Application
Repository
PostgreSQL
Alembic
routing logic
PRODUCT identity
SDS lifecycle
BHP lifecycle
JSON import
resolver
DRY RUN
```

Nie dodawaj:

```text
nowej dependency
nowego frameworka UI
nowego systemu design tokens
```

Nie przebudowuj ponownie struktury Karty produktu.

---

## 13. VALIDATION — LEVEL 1

Focused UI/AppTest.

Potwierdź co najmniej:

```text
1. Sidebar:
   - wszystkie sekcje działają,
   - brak emoji,
   - ikony nie zmieniają wartości routingu.

2. Karta produktu:
   - akcje pozostają funkcjonalne,
   - pasek akcji jest wyżej i kompaktowy,
   - brak regresji danych.

3. Miejsca stosowania:
   - tabela działa,
   - „Dodaj miejsce” jest pod tabelą.

4. Dane administracyjne:
   - dokładnie jedna akcja „Edytuj”,
   - brak dublującego expandera/listwy,
   - istniejący workflow edycji działa.

5. Dodaj SDS:
   - „Kod producenta — opcjonalne” pozostaje.

6. Produkty:
   - tabela / sortowanie / wyszukiwanie / otwarcie karty bez regresji.
```

Nie uruchamiaj pełnego pytest.

---

## 14. PHYSICAL UX REVIEW

Po implementacji:

```text
STOP
```

Finalna akceptacja po przeglądzie przy:

```text
1920×1080
zoom 100%
```

Architekt sprawdza:

```text
- sidebar,
- górny pasek akcji,
- kolory przycisków,
- miejsca stosowania,
- dane administracyjne,
- spójność całego ekranu.
```

---

## 15. STOP CONDITIONS

STOP / BLOCKED jeżeli:

1. prawdziwe ikony wymagają nowej dependency,
2. kolorowanie wymaga przebudowy globalnego theme poza lokalny PATCH,
3. usunięcie duplikatu edycji wymaga zmiany Application,
4. zmiana akcji wymaga nowego use case,
5. poprawka zaczyna obejmować TASK-052 / JSON import,
6. wymagany jest repo-wide redesign.

---

## 16. REPORT

Utwórz:

```text
docs/task_reports/PATCH-015-R2_REPORT.md
```

Format:

```text
# PATCH-015-R2 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- files

IMPLEMENTED:
- sidebar real icons
- top action hierarchy
- dashboard button colors
- Add place below table
- administrative data Variant B
- local button fill refinement

VALIDATION:
- focused AppTest
- related UI regression
- git diff --check

SCOPE:
- Domain change: NO
- Application change: NO
- schema change: NO
- migration: NONE
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY FOR PHYSICAL UX REVIEW
```

---

## 17. AUTHORIZATION

```text
PATCH-015-R2
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Uruchomić dopiero po poleceniu:

```text
Wykonaj PATCH-015-R2.
```
