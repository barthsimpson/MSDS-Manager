# PATCH-015-R1 — Typografia, sidebar i gęstość Karty produktu

**Projekt:** MSDS Manager  
**Patch ID:** PATCH-015-R1  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI  

---

## 1. GOAL

Dopracować fizyczną ergonomię UI po `PATCH-015` bez zmiany jego architektury.

Zakres:

```text
1. większa i czytelniejsza typografia Karty produktu,
2. lepsze wykorzystanie wolnej przestrzeni bez zwiększania przewijania,
3. większy i czytelniejszy sidebar,
4. ikony przy sekcjach aplikacji,
5. zachowanie obecnego układu Produkty → Karta produktu,
6. bez zmian logiki biznesowej.
```

Nie przebudowuj ponownie nawigacji ani struktury widoków.

---

## 2. AUTHORITATIVE CONTEXT

Przeczytaj minimalnie:

1. `PATCH-015_Produkty_i_Karta_Produktu_Compact_UI.md`
2. `PATCH-015_REPORT.md`
3. `TASK-051-R1_REPORT.md`
4. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
5. root `AGENTS.md`

Physical UX decision Architekta:

```text
Struktura Produkty → Karta produktu: ACCEPTED
Układ Karty produktu: ACCEPTED
Przycisk „Otwórz kartę produktu” pod tabelą: ACCEPTABLE FOR MVP

Do poprawy:
- typografia,
- sidebar,
- wykorzystanie wolnej przestrzeni.
```

---

## 3. KNOWN STARTING POINTS

Rozpocznij od:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/product_registry.py
```

oraz bezpośrednio powiązanych lokalnych stylów / helperów Streamlit.

Nie wykonuj repo-wide refactor.

---

## 4. EKRAN `PRODUKTY`

Nie zmieniaj logiki ekranu.

Zachować:

```text
tabela produktów
wyszukiwanie
sortowanie
wybór wiersza
przycisk „Otwórz kartę produktu”
```

Założenie UX:

```text
10–15 widocznych wierszy
+ pionowy scroll tabeli dla dalszych rekordów
```

Jeżeli obecna tabela naturalnie skaluje się w ten sposób:

```text
NO CHANGE
```

Nie implementuj teraz row-click ani dodatkowej ikony nawigacji.

Można pozostawić tę możliwość do przyszłego refinementu.

---

## 5. KARTA PRODUKTU — TYPOGRAFIA

Obecny layout pozostaje bez zmian.

Popraw czytelność przez zwiększenie fontów i ograniczone wykorzystanie przestrzeni.

Docelowe wartości orientacyjne:

```text
Nazwa produktu / główny tytuł:
30–32 px

Producent / kod / status pod nagłówkiem:
15–16 px

Nagłówki sekcji:
20–22 px

Etykiety pól:
14–15 px

Wartości pól:
15–16 px

Tekst pomocniczy / secondary:
13–14 px minimum
```

Wartości mogą zostać lekko dopasowane do istniejącej skali Streamlit, ale efekt ma być wizualnie zauważalny przy zoom 100%.

Nie zwiększaj wysokości kart przez nadmierny padding.

Priorytet:

```text
większa czcionka
> większe puste odstępy
```

---

## 6. KARTA PRODUKTU — WYKORZYSTANIE PRZESTRZENI

Obecnie karta pozostawia dużo niewykorzystanej szerokości i wysokości.

Dopracuj:

```text
- wewnętrzne marginesy,
- proporcje kolumn,
- odstępy pomiędzy label/value,
- szerokość bloków,
- rozmieszczenie przycisków w nagłówku.
```

Nie dodawaj nowych informacji.

Nie twórz nowych kart.

Cel:

```text
więcej informacji czytelnych na jednym ekranie
bez pionowego rozciągania widoku.
```

---

## 7. SIDEBAR — TYPOGRAFIA

Sidebar jest obecnie zbyt drobny względem reszty aplikacji.

Zwiększ:

```text
etykieta „Sekcja”:
14–15 px

pozycje menu:
15–16 px

ikony:
18–20 px

obszar kliknięcia:
większy niż obecnie
```

Zachować kompaktowy charakter sidebaru.

Nie poszerzaj go nadmiernie.

---

## 8. SIDEBAR — IKONY

Dodaj czytelne ikony do pozycji:

```text
Produkty
Dodaj SDS
Decyzja BHP
Stanowiska
Widok nadzorczy
Analizy
```

Preferowane znaczenia:

```text
Produkty         → box / package
Dodaj SDS        → file-plus / document
Decyzja BHP      → check / shield-check
Stanowiska       → pin / location / users
Widok nadzorczy  → eye / monitor
Analizy          → chart
```

Użyj ikon już dostępnych w obecnym środowisku / Streamlit.

Nie dodawaj nowej biblioteki tylko dla ikon.

Jeżeli framework nie daje stabilnych ikon:

```text
użyj prostych Unicode / emoji tylko jako fallback
```

ale bez infantylnego wyglądu.

---

## 9. SIDEBAR — ERGONOMIA

Każda pozycja powinna mieć:

```text
ikona + tekst
czytelny odstęp
większy obszar kliknięcia
spójne wyrównanie
```

Aktywna sekcja powinna pozostać jednoznacznie rozpoznawalna.

Nie zmieniaj mechanizmu wyboru sekcji.

---

## 10. PRZYCISKI KARTY PRODUKTU

Zachować obecne akcje:

```text
Uzupełnij kod producenta
Korekta danych identyfikacyjnych
Dodaj nową rewizję SDS
Więcej akcji
```

Dopracuj wyłącznie:

```text
- czytelność tekstu,
- wysokość,
- odstęp między przyciskami,
- wyrównanie w jednym rzędzie.
```

Nie zmieniaj warunkowości ani use case'ów.

---

## 11. RESPONSYWNOŚĆ / ZOOM

Physical target:

```text
desktop
1920×1080
zoom 100%
```

Na tym widoku:

```text
- sidebar ma być czytelny bez przybliżania,
- główna karta ma wykorzystywać szerokość,
- większość informacji Karty produktu ma być widoczna bez scrollowania,
- żadna sekcja nie może się niepotrzebnie rozsypać na wiele wierszy.
```

Przy mniejszej szerokości dopuszczalne jest naturalne zawijanie.

Nie implementuj osobnego mobile layout.

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
DRY RUN
resolver
```

Nie implementuj:

```text
row-click navigation
nowej kolumny Akcje w tabeli
nowego sidebar framework
nowej dependency
```

Nie zmieniaj zaakceptowanego układu sekcji Karty produktu.

---

## 13. VALIDATION — LEVEL 1

Focused UI/AppTest.

Potwierdź co najmniej:

```text
1. Produkty:
   - tabela nadal działa,
   - wyszukiwanie działa,
   - sortowanie działa,
   - wybór + Otwórz kartę działa.

2. Karta produktu:
   - układ sekcji bez zmian logicznych,
   - akcje nagłówka działają,
   - brak utraty informacji,
   - brak regresji miejsc stosowania i danych administracyjnych.

3. Sidebar:
   - wszystkie sekcje dostępne,
   - aktywna sekcja działa,
   - ikony nie psują wyboru sekcji.

4. Dodaj SDS:
   - wcześniejsza poprawka „Kod producenta — opcjonalne” pozostaje.
```

Uruchom tylko focused UI regression.

Nie uruchamiaj pełnego pytest.

---

## 14. PHYSICAL UX REVIEW

Po implementacji:

```text
STOP
```

i przygotuj raport.

Finalna akceptacja dopiero po fizycznym review przy zoom 100%.

Architekt sprawdza:

```text
- ekran Produkty,
- Kartę produktu,
- sidebar,
- czytelność czcionek,
- wysokość strony,
- wykorzystanie wolnej przestrzeni.
```

---

## 15. STOP CONDITIONS

STOP / BLOCKED jeżeli:

1. większa typografia wymaga przebudowy layoutu poza PATCH,
2. ikony wymagają nowej dependency,
3. sidebar wymaga przebudowy mechanizmu nawigacji,
4. poprawa stylu zaczyna wymagać zmian Application,
5. występuje istotna regresja tabeli Produktów,
6. poprawka wymaga zmian w TASK-052 / JSON import.

---

## 16. REPORT

Utwórz:

```text
docs/task_reports/PATCH-015-R1_REPORT.md
```

Format:

```text
# PATCH-015-R1 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- files

IMPLEMENTED:
- product card typography
- spacing / density refinement
- sidebar typography
- sidebar icons
- action bar refinement

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
PATCH-015-R1
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Uruchomić dopiero po poleceniu:

```text
Wykonaj PATCH-015-R1.
```
