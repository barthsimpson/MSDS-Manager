# TASK-029 — UI Foundation + Rejestr produktów

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Task ID:** TASK-029  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** SHORT  
**Status:** READY  
**Wykonawca:** Codex OpenAI

---

## GOAL

Uporządkować fundament interfejsu Streamlit oraz ekran `Produkty`, bez zmiany istniejącej logiki biznesowej.

Docelowy sposób pracy:

```text
Produkty
→ zwarta tabela rejestru
→ wybór produktu
→ czytelne szczegóły wybranego produktu
→ akcje istniejącego produktu
```

Task ma poprawić ergonomię, czytelność i wykorzystanie szerokości ekranu.

Nie dodaje nowych funkcji domenowych.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `SPRINT-006_UI_MVP_v1.0-approved.md`,
- ten TASK,
- bezpośrednio powiązany kod Streamlit dla:
  - shell / navigation,
  - ekranu `Produkty`,
  - composition,
- bezpośrednio powiązane AppTests / integration tests.

Nie czytaj ponownie całego CORE/BDR/TDR/Sprint history bez konkretnej potrzeby.

Jeżeli wymaganie Tasku koliduje z Core lub wymaga nowej decyzji biznesowej:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

Zweryfikuj lokalnie przede wszystkim:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/composition.py
```

oraz istniejący moduł ekranu `Produkty`, zawierający obecne funkcje:

```text
Edytuj dane produktu
Dodaj nową rewizję SDS
Usuń produkt
dane administracyjne
miejsca stosowania
```

i istniejące testy Streamlit dotyczące:

```text
shell/navigation
products
PATCH-006
PATCH-007
PATCH-008
```

Nie wykonuj repo-wide search, jeżeli te punkty wystarczają.

---

## UI DIRECTION

Interfejs ma mieć charakter desktopowej aplikacji operacyjnej:

```text
szeroki
zwarty
tabelaryczny
informacyjny
stabilny
```

Preferuj:

- wykorzystanie szerokości ekranu,
- niewielką ilość pustej przestrzeni,
- tabelę jako główny element rejestru,
- szczegóły podporządkowane wybranemu rekordowi,
- jasne sekcje,
- krótkie etykiety użytkowe,
- mało technicznych informacji.

Nie buduj:

- dashboardu,
- kafelków KPI,
- rozbudowanego design systemu,
- nowego frameworka UI,
- React/FastAPI,
- dużej warstwy custom CSS.

Dopuszczalny jest minimalny CSS wyłącznie wtedy, gdy Streamlit nie pozwala osiągnąć wymaganego rezultatu prostą konfiguracją.

---

## DO

### 1. Wide layout

Ustaw aplikację na szeroki layout.

Preferowane:

```python
st.set_page_config(layout="wide")
```

lub istniejący równoważny mechanizm, jeśli konfiguracja już istnieje.

Nie dubluj konfiguracji strony.

---

### 2. Zachowaj obecną nawigację

Podstawowe sekcje pozostają:

```text
Widok nadzorczy
Produkty
Dodaj SDS
Decyzja BHP
Stanowiska
```

TASK-029 może uporządkować prezentację nawigacji, ale:

- nie dodaje nowych modułów,
- nie usuwa istniejących ekranów,
- nie zmienia workflow.

---

### 3. Rejestr produktów — tabela jako punkt wejścia

Na ekranie `Produkty` głównym elementem ma być zwarta tabela.

Minimalne kolumny:

| Kolumna | Źródło |
|---|---|
| Produkt | product_name |
| Kod producenta | manufacturer_product_code |
| Producent | manufacturer |
| Status | usage_status |
| SDS | bieżący stan CURRENT SDS, jeżeli dostępny w istniejącym read modelu |
| BHP | bieżący stan decyzji, jeżeli dostępny w istniejącym read modelu |

Jeżeli `SDS` lub `BHP` wymagałyby nowej logiki aplikacyjnej wykraczającej poza istniejące dane ekranu:

```text
NIE implementuj ich w Tasku na siłę.
```

Zgłoś w raporcie.

Nie dodawaj SQL/ORM/filesystem logic do UI.

---

### 4. Ukryj UUID w normalnym workflow

Nie pokazuj w głównej tabeli:

```text
product_id UUID
```

Nie pokazuj technicznego UUID jako części zwykłych komunikatów sukcesu.

UUID nadal pozostaje wewnętrznym identyfikatorem i może być używany technicznie do selekcji.

Jeżeli potrzebne do diagnostyki, można je pokazać w:

```text
Dane techniczne
```

jako opcjonalny expander.

Nie dodawaj nowej kolumny biznesowego ID do schema.

---

### 5. Wybór produktu z rejestru

Preferowany UX:

```text
klik / zaznaczenie wiersza tabeli
→ szczegóły tego produktu
```

Najpierw sprawdź, czy używana wersja Streamlit obsługuje stabilne row selection bez zmiany dependency.

Jeżeli TAK:

```text
użyj row selection
```

Jeżeli NIE:

```text
zachowaj minimalny fallback wyboru produktu
```

Fallback nie powinien dublować pełnej informacji z tabeli ani dominować ekranu.

Nie aktualizuj Streamlit tylko po to, by uzyskać row selection.

---

### 6. Szczegóły wybranego produktu

Po wyborze produktu uporządkuj dane w czytelnych sekcjach.

Preferowana kolejność:

```text
Szczegóły produktu

[ Tożsamość ]
Nazwa
Kod producenta
Producent
Status

[ SDS ]
CURRENT SDS / podstawowe informacje dostępne już w ekranie

[ BHP ]
aktualny stan dostępny już w ekranie

[ Miejsca stosowania ]
istniejący fragment — bez redesignu logiki w TASK-029

[ Dane administracyjne ]
opis zastosowania
ograniczenia
typ odpadu
kod odpadu

[ Akcje ]
Edytuj dane produktu
Dodaj nową rewizję SDS
Usuń produkt
```

TASK-029 nie wykonuje jeszcze docelowego redesignu miejsc stosowania — to TASK-031.

Można jedynie wizualnie oddzielić obecną sekcję od reszty.

---

### 7. Akcje produktu

Zachowaj istniejące zachowanie PATCH-006/007/008:

```text
Edytuj dane produktu
Dodaj nową rewizję SDS
Usuń produkt
```

Akcje mają być jednoznacznie związane z aktualnie wybranym produktem.

`Usuń produkt` pozostaje:

- oddzielony od zwykłych akcji,
- zabezpieczony istniejącym potwierdzeniem,
- bez zmian w logice delete.

Nie zmieniaj lifecycle.

---

### 8. Status labels

W warstwie prezentacji można pokazać użytkownikowi przyjazne etykiety:

```text
ACTIVE           → Aktywny
PENDING_APPROVAL → Oczekuje na BHP
REJECTED         → Odrzucony
INACTIVE         → Nieaktywny
```

Wewnętrzne wartości domenowe pozostają bez zmian.

Kolor/badge jest opcjonalny i prezentacyjny.

Nie wprowadzaj nowej logiki statusów.

---

### 9. Komunikaty sukcesu

Usuń techniczne UUID z podstawowych komunikatów UI.

Przykład:

było:

```text
Produkt zapisany. (7bd18a8e...)
```

ma być:

```text
Produkt został zapisany.
```

Jeżeli identyfikator jest potrzebny diagnostycznie, niech pozostanie poza standardowym komunikatem.

---

## DO NOT

Nie:

- zmieniaj Core,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- aktualizuj Streamlit,
- zmieniaj parsera,
- zmieniaj AcceptSds,
- zmieniaj lifecycle SDS,
- zmieniaj lifecycle BHP,
- zmieniaj logiki PATCH-006/007/008,
- przebudowuj miejsc stosowania — TASK-031,
- przebudowuj `Dodaj SDS` — TASK-030,
- przebudowuj `Decyzja BHP` — TASK-030,
- zmieniaj `Widok nadzorczy` — TASK-031,
- dodawaj upload/storage service,
- dodawaj biznesowych ID do DB,
- implementuj R8/R10/R11,
- wykonuj opportunistic refactor.

Problem spoza zakresu:

```text
→ raport
```

Problem blokujący:

```text
→ STOP
```

---

## EXPECTED CHANGE SURFACE

Przewidywany zakres:

```text
app/presentation/streamlit/main.py
app/presentation/streamlit/<products_screen>.py
app/presentation/streamlit/composition.py   # tylko jeśli wymagane do istniejącego read modelu
tests/unit/test_streamlit_<products>.py
tests/unit/test_streamlit_shell_unit.py
tests/integration/test_streamlit_shell.py   # tylko jeśli potrzebne
docs/task_reports/TASK-029_REPORT.md
```

Nazwa modułu produktu może różnić się w repo — użyj istniejącego pliku, nie twórz równoległego ekranu.

### DO NOT TOUCH

Jeżeli nie pojawi się bezpośrednia potrzeba:

```text
Domain
ORM models
Alembic migrations
parser/PDF infrastructure
BHP persistence
SDS persistence
supervisory read model
```

---

## VALIDATION — LEVEL 2

Uruchom minimalną walidację proporcjonalną do zmiany.

### Focused UI tests

Pokryj co najmniej:

1. ekran `Produkty` ładuje się,
2. tabela nie pokazuje UUID jako kolumny biznesowej,
3. produkt można wybrać,
4. po wyborze widoczne są jego szczegóły,
5. akcje edit/revision/delete nadal są dostępne dla wybranego produktu,
6. brak produktu / pusta lista daje kontrolowany stan,
7. przyjazna prezentacja statusu nie zmienia wartości domenowej,
8. podstawowe komunikaty sukcesu nie eksponują UUID.

### Existing behavior regression

Nie testuj ponownie całego lifecycle PATCH-006/007/008.

Wystarczy potwierdzić, że UI nadal wywołuje istniejące akcje i ich focused tests pozostają PASS.

### Integration

Jeżeli zmienisz composition / sposób pobierania danych:

```text
uruchom istniejący powiązany integration test Streamlit/PostgreSQL
```

Jeżeli composition nie jest zmieniany:

```text
nie dodawaj sztucznego integration testu
```

### Full regression

Nie uruchamiaj pełnego repo-wide pytest w TASK-029 bez konkretnej przyczyny.

Pełna regresja jest obowiązkowa w TASK-032 ACCEPTANCE.

---

## ACCEPTANCE CRITERIA

TASK-029 = DONE, gdy:

1. aplikacja używa szerokiego layoutu,
2. `Produkty` jest przede wszystkim rejestrem tabelarycznym,
3. UUID nie występuje jako normalna kolumna użytkowa,
4. wybór produktu prowadzi do jego szczegółów,
5. szczegóły są podzielone na czytelne sekcje,
6. istniejące akcje edit/revision/delete pozostają dostępne,
7. akcja delete zachowuje potwierdzenie,
8. status produktu jest czytelny dla użytkownika,
9. komunikaty sukcesu nie eksponują UUID,
10. brak zmian Core/schema/migrations/dependencies,
11. focused tests PASS,
12. wymagane integration tests PASS, jeśli dotknięto composition,
13. nie rozpoczęto TASK-030.

---

## PHYSICAL REVIEW

Po wykonaniu Tasku Architekt Operacyjny wykona krótki walkthrough:

```text
uruchom aplikację
→ Produkty
→ oceń wykorzystanie szerokości
→ wybierz IDROLIN
→ sprawdź szczegóły
→ sprawdź akcje
→ wybierz XBRAKE CLEANER
→ sprawdź zmianę rekordu
```

Sprawdzamy głównie ergonomię.

Nie wykonujemy w tym review pełnego lifecycle SDS/BHP.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. wymagany row-selection wymaga zmiany/upgrade dependency,
2. rejestr produktów wymaga zmiany Core/schema,
3. pokazanie SDS/BHP wymaga nowej logiki biznesowej zamiast reuse istniejącego read modelu,
4. task zaczyna wymagać repo-wide refactor,
5. istniejący ekran produktu jest tak sprzężony z innymi ekranami, że zmiana wymaga decyzji architektonicznej,
6. konieczna byłaby zmiana lifecycle PATCH-006/007/008.

Nie obchodź blokera przez logikę w UI.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/TASK-029_REPORT.md
```

Format:

```text
# TASK-029 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

UI RESULT:
- wide layout: YES / NO
- product table first: YES / NO
- UUID hidden in normal UI: YES / NO
- product selection: ROW / FALLBACK / NO
- details structured: YES / NO
- edit action preserved: YES / NO
- new SDS revision action preserved: YES / NO
- delete confirmation preserved: YES / NO
- user-facing status labels: YES / NO
- success messages without UUID: YES / NO

VALIDATION:
- focused AppTests: ...
- related regression: ...
- integration: ... / NOT REQUIRED

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- lifecycle changes: NONE

RISKS / DEVIATIONS:
- NONE / ...

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-030.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-029.
```
