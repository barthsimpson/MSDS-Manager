# PATCH-014 — Widok nadzorczy — kompaktowy pasek filtrów

**Projekt:** MSDS Manager  
**Patch:** PATCH-014  
**Wersja:** 0.1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-07  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

## MODE

```text
PATCH
```

## GOAL

Zmniejszyć pionową wysokość filtrów w `Widoku nadzorczym` i ujednolicić ich ergonomię z zatwierdzonym kompaktowym paskiem filtrów w module `Analizy`.

Obecnie filtry:

```text
Szukaj produktu
Wymaga działania
Status produktu
Lokalizacja
BHP
```

są ułożone pionowo i zajmują znaczną część wysokości ekranu przed tabelą.

Docelowo wszystkie pięć kontrolek ma być dostępnych w jednym poziomym pasku nad tabelą.

## AUTHORITATIVE CONTEXT

Przeczytaj wyłącznie:

```text
GOV-002_Lean_Codex_Task_Optimization_v1.0-approved
PATCH-013_REPORT.md
root AGENTS.md
ten PATCH
```

PATCH-013 jest wzorcem UX dla kompaktowego toolbaru filtrów w `Analizach`.

Nie czytaj ponownie całego Core / BDR / TDR / historii projektu bez konkretnej potrzeby.

## KNOWN STARTING POINTS

```text
app/presentation/streamlit/supervisory.py
```

oraz istniejący focused test / AppTest dla `Widoku nadzorczego` z TASK-031 / późniejszych regresji.

Jeżeli dokładna nazwa pliku testowego różni się w repo, znajdź bezpośrednio test importujący lub uruchamiający `supervisory.py`.

## EXPECTED CHANGE SURFACE

```text
app/presentation/streamlit/supervisory.py
existing focused supervisory UI test
docs/task_reports/PATCH-014_REPORT.md
```

Nie rozszerzaj zakresu bez konkretnej konieczności.

## DO

### 1. Jeden poziomy pasek filtrów

Ułóż pięć istniejących filtrów w jednym rzędzie, analogicznie do `Analizy`.

Preferowany układ szerokości:

```text
Produkt        — szersze pole
Działanie      — węższy select
Status         — węższy select
Lokalizacja    — średni select
BHP            — węższy select
```

Dopuszczalne użycie np. `st.columns(...)` zgodnie z istniejącym stylem projektu.

### 2. Krótkie etykiety

Zmień wyłącznie etykiety prezentacyjne:

```text
Szukaj produktu   → Produkt
Wymaga działania  → Działanie
Status produktu   → Status
Lokalizacja       → Lokalizacja
BHP               → BHP
```

Wartości i semantyka filtrów pozostają bez zmian.

Dla `Działanie` zachowaj istniejące opcje, np.:

```text
Wszystkie
Wymagają działania
```

Nie zmieniaj logiki filtrowania.

### 3. Zachowanie tabeli

Tabela ma znaleźć się bezpośrednio pod paskiem filtrów z małym, spójnym odstępem.

Nie dodawaj:

```text
karty „Filtry”
expandera
osobnego nagłówka filtrów
dodatkowych separatorów
```

Cel:

```text
więcej danych tabelarycznych widocznych bez scrollowania
```

### 4. Zachowanie istniejącej funkcjonalności

Muszą pozostać identyczne:

```text
wyszukiwanie produktu
filtr wymaga działania
filtr statusu produktu
filtr lokalizacji
filtr BHP
łączenie filtrów
read-only charakter widoku
wynikowa tabela
```

Zmiana dotyczy tylko prezentacji / layoutu.

## DO NOT

Nie zmieniaj:

```text
Application
Domain
Infrastructure
supervisory read model
SQL / ORM
schema
Alembic
Core
logiki statusów
logiki action reasons
nazw / znaczenia wartości filtrowania
```

Nie twórz wspólnego frameworka filtrów dla całej aplikacji.

Nie przenoś funkcji z `analytics.py` do nowego modułu tylko w celu współdzielenia kilku linii UI.

Jeżeli można odwzorować układ lokalnie w `supervisory.py`, preferuj rozwiązanie lokalne i małe.

## VALIDATION

```text
LEVEL 1
```

Wymagane focused checks:

```text
Widok nadzorczy renderuje 5 filtrów
etykiety:
- Produkt
- Działanie
- Status
- Lokalizacja
- BHP

dotychczasowe wartości filtrów pozostają dostępne
filtry nadal przekazują te same wartości do istniejącego odczytu
tabela nadal renderuje się poprawnie
brak UUID / technicznych pól dodanych do UI
```

Uruchom tylko bezpośrednio właściwe testy Streamlit/AppTest i ewentualnie istniejący shell regression, jeżeli jest potrzebny z powodu sposobu renderowania widoku.

Bez:

```text
pełnego pytest
E2E całej aplikacji
Alembic current/check
PostgreSQL migration tests
```

ponieważ PATCH nie zmienia danych ani schema.

Na końcu:

```text
git diff --check
```

dla zmienionego zakresu.

## ACCEPTANCE UX

Fizyczny test przy typowym desktopowym zoom 100%:

```text
Widok nadzorczy
→ nagłówek
→ jeden kompaktowy rząd filtrów
→ tabela
```

Oczekiwany efekt ma odpowiadać gęstością filtrom `Analizy`.

Pole `Produkt` może być wyraźnie szersze od pozostałych czterech kontrolek.

## STOP CONDITIONS

STOP / BLOCKED, jeżeli poprawne wykonanie wymaga:

```text
zmiany Application / read modelu
zmiany znaczenia filtrów
zmiany schema / migracji
nowej dependency
repo-wide refactor
```

Nie rozszerzaj zakresu „przy okazji”.

## REPORT

**SHORT REPORT**

```text
STATUS: DONE / BLOCKED

CHANGED:
- supervisory.py
- focused test

IMPLEMENTED:
- compact 5-control filter bar
- short labels
- unchanged filter semantics

VALIDATION:
- focused AppTest
- optional shell regression if needed
- git diff --check

SCOPE:
- Application change: NO
- Infrastructure change: NO
- schema change: NO
- migration: NONE
- Core change: NO
- dependencies: NONE

NEXT:
- READY FOR PHYSICAL UX REVIEW
```

## AUTHORIZATION

```text
PATCH-014
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Start dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj PATCH-014.
```
