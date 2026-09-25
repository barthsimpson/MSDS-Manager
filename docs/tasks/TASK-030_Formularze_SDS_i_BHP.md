# TASK-030 — Formularze SDS i BHP

**Projekt:** MSDS Manager  
**Sprint:** SPRINT-006 — Operacyjny UI MVP v1.0-approved  
**Task ID:** TASK-030  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2  
**REPORT:** SHORT  
**Status:** READY  
**Wykonawca:** Codex OpenAI

---

## GOAL

Uporządkować trzy istniejące workflow formularzowe:

```text
Dodaj SDS
Nowa rewizja SDS
Decyzja BHP
```

tak, aby były krótsze, czytelniejsze i mniej techniczne, bez zmiany ich logiki biznesowej.

Task ma poprawić ergonomię pracy operatora, nie zachowanie Core.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `SPRINT-006_UI_MVP_v1.0-approved.md`,
- ten TASK,
- `TASK-029_REPORT.md`,
- bezpośrednio powiązany kod Streamlit dla:
  - `Dodaj SDS`,
  - nowej rewizji SDS w ekranie produktu,
  - `Decyzja BHP`,
  - composition tylko w zakresie używanym przez te ekrany,
- bezpośrednio powiązane AppTests i integration tests.

Nie czytaj ponownie całego CORE/BDR/TDR/history bez konkretnej potrzeby.

Jeżeli wymaganie UI wymaga zmiany Core, schema albo istniejącego lifecycle:

```text
STOP / BLOCKED
```

---

## KNOWN STARTING POINTS

Zweryfikuj lokalnie przede wszystkim:

```text
app/presentation/streamlit/add_sds.py
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/composition.py
```

oraz istniejący moduł widoku BHP, najpewniej:

```text
app/presentation/streamlit/<bhp_screen>.py
```

Użyj istniejącego pliku w repo; nie twórz równoległego ekranu BHP.

Powiązane testy:

```text
tests/unit/test_streamlit_add_sds.py
testy product_registry / AddSdsRevision
testy Streamlit BHP
tests/integration/test_streamlit_shell.py
```

Nie wykonuj repo-wide discovery, jeśli wskazane punkty wystarczają.

---

# CZĘŚĆ A — `Dodaj SDS`

## 1. Zachowaj istniejący workflow

Workflow pozostaje:

```text
wybierz PDF
→ Odczytaj dane
→ użytkownik sprawdza / poprawia formularz
→ Zapisz / Akceptuj
→ PRODUCT + CURRENT SDS
→ PRODUCT = PENDING_APPROVAL
```

Manual fallback pozostaje pełnoprawnym scenariuszem.

Parser jest tylko pomocą.

Nie rozwijaj parsera.

---

## 2. Uporządkuj formularz w sekcje

Obecny formularz jest zbyt długi i pionowy.

Zmień prezentację na logiczne grupy wykorzystujące szerokość ekranu.

Preferowany układ:

```text
[ Dokument SDS ]
Plik
Data dokumentu | Rewizja

[ Produkt ]
Nazwa produktu | Kod producenta
Producent
Opis zastosowania | Ograniczenia zastosowania

[ Dane bezpieczeństwa — opcjonalne ]
Safety Profile

[ Skład / Sekcja 3 — opcjonalne ]
SDS Components
```

Dopuszczalne jest użycie:

```text
st.columns(...)
st.expander(...)
```

bez tworzenia nowego frameworka UI.

---

## 3. Pola wymagane muszą być widoczne przed zapisem

Na podstawie **istniejącej walidacji AcceptSds** oznacz wszystkie pola wymagane w UI, np.:

```text
Nazwa produktu *
Producent *
Opis zastosowania *
Ograniczenia zastosowania *
```

oraz inne pola, jeśli aktualny kontrakt faktycznie ich wymaga.

WAŻNE:

```text
nie dodawaj nowych required fields
nie usuwaj existing required fields
```

UI ma tylko odzwierciedlić istniejącą walidację.

Dodaj krótki opis:

```text
* pole wymagane
```

---

## 4. Dane chemiczne jako opcjonalne

Zgodnie z zaakceptowanym MVP:

```text
Safety Profile
SDS Components
```

nie mogą dominować formularza.

Preferowane:

```text
expander zamknięty domyślnie
```

np.:

```text
Dane bezpieczeństwa — opcjonalne
Składniki — opcjonalne
```

Nie zmieniaj mechanizmu zapisu.

Nie zmieniaj PATCH-005.

---

## 5. Manual fallback ma być czytelny

Jeżeli `Odczytaj dane`:

- nie odczyta wszystkich pól,
- zwróci pustą chemię,
- zwróci dane wymagające ręcznej korekty,

użytkownik nadal ma normalnie pracować na formularzu.

Nie pokazuj komunikatu sugerującego, że brak pełnej ekstrakcji jest awarią całego workflow.

Kontrolowany błąd odczytu PDF pozostaje błędem technicznym, ale ręczne uzupełnienie danych nie może zostać ukryte przez redesign.

---

## 6. Komunikaty

Zachowaj komunikat bez UUID wprowadzony w TASK-029.

Po sukcesie preferowane:

```text
SDS został zapisany.
Produkt oczekuje na decyzję BHP.
```

Nie pokazuj UUID w podstawowym komunikacie.

---

# CZĘŚĆ B — Nowa rewizja SDS

## 7. Zachowaj lifecycle PATCH-006

Nie zmieniaj:

```text
existing PRODUCT
→ old CURRENT = ARCHIVED
→ new SDS = CURRENT
→ PRODUCT = PENDING_APPROVAL
→ old BHP not inherited
```

Nie implementuj auto-matchowania produktu.

---

## 8. Czytelny kontekst produktu

W formularzu nowej rewizji pokaż nad formularzem biznesowy kontekst:

```text
Produkt
Producent
Kod producenta
Aktualny SDS / rewizja, jeśli dostępne
```

Nie pokazuj UUID jako podstawowej informacji.

---

## 9. Pola nowej rewizji

Minimalny UI:

```text
Plik PDF *
Rewizja
Data dokumentu
```

Jeżeli istniejący kontrakt traktuje rewizję lub datę jako opcjonalne, pozostaw je opcjonalne.

Nie zmieniaj reguł BDR-003.

---

## 10. Krytyczna korekta UX — data SDS

**Nie podstawiaj bieżącej daty jako domyślnej daty dokumentu.**

Reguła:

```text
jeżeli data została rzeczywiście odczytana / istnieje w draft
→ pokaż ją

jeżeli data jest nieznana
→ pole puste / None
```

Nie wolno utożsamiać:

```text
registered_at
```

z:

```text
issue_date
```

To jest korekta prezentacyjna / input default.

Nie zmieniaj schema.

---

# CZĘŚĆ C — `Decyzja BHP`

## 11. Zachowaj istniejący workflow

Workflow pozostaje:

```text
PRODUCT + CURRENT SDS
→ wybór evidence
→ APPROVED / REJECTED
→ notes
→ Zapisz
→ status PRODUCT
```

Nie zmieniaj:

```text
CURRENT / SUPERSEDED
1:1 DECISION_EVIDENCE
APPROVED → ACTIVE
REJECTED → REJECTED
```

Nie analizuj treści evidence.

---

## 12. Kontekst decyzji BHP

Na górze ekranu, po wyborze produktu, pokaż w zwartej formie:

```text
Produkt
Producent
Kod producenta
Status produktu
CURRENT SDS
Rewizja SDS
Data SDS
```

Pokaż wyłącznie dane już dostępne w istniejącym UI / composition.

Nie twórz nowego read modelu, jeśli nie jest konieczny.

---

## 13. Dowód decyzji

Obecny model filesystemu pozostaje bez zmian:

```text
BHP_EVIDENCE_ROOT_PATH
```

Użytkownik wybiera istniejący plik z katalogu.

W normalnym formularzu pokazuj przede wszystkim:

```text
nazwa pliku
status dostępności
```

Nie eksponuj pełnej ścieżki jako głównej informacji.

Pełna ścieżka może pozostać w technicznym detalu, jeśli już jest potrzebna.

Nie dodawaj:

```text
upload service
file picker systemowy
kopiowania plików
przenoszenia plików
```

---

## 14. Przyjazne etykiety decyzji

W UI dopuszczalne:

```text
APPROVED → Dopuszczony
REJECTED → Niedopuszczony
```

Wartości domenowe pozostają bez zmian.

Nie dodawaj nowych statusów.

---

## 15. Natychmiastowe odświeżenie po zapisie

Po zapisie decyzji ekran ma od razu pokazać aktualny stan.

Przykład:

```text
przed:
PENDING_APPROVAL

użytkownik zapisuje APPROVED

po:
ACTIVE
```

Nie może pozostać w UI stary status w:

- selectorze produktu,
- nagłówku,
- szczegółach,
- bieżącym podsumowaniu.

Użyj standardowego mechanizmu Streamlit:

```text
session state / rerun / ponowny read
```

w najmniejszym potrzebnym zakresie.

Nie obchodź lifecycle lokalną zmianą labela bez ponownego odczytu rzeczywistego stanu.

---

## 16. Bieżąca decyzja

Jeżeli istniejący ekran pokazuje bieżącą decyzję, zachowaj:

```text
decision status
registered_at
notes
evidence
```

i uporządkuj wizualnie.

Nie zmieniaj historii decyzji.

---

# WSPÓLNE ZASADY UI

## 17. Compact forms

Preferuj:

```text
2 kolumny tam, gdzie naturalne
krótkie sekcje
opcjonalne dane w expanderach
```

Nie buduj bardzo długiej jednej kolumny.

---

## 18. Business-first labels

Preferuj polskie etykiety użytkowe.

Nie pokazuj:

```text
product_id
sds_id
decision_id
relative_path
```

jako podstawowych nazw formularza.

Techniczne wartości mogą istnieć pod spodem.

---

## 19. Nie zmieniaj stylu TASK-029

Zachowaj:

```text
wide layout
spójny sposób nagłówków
spójny sposób statusów
brak UUID w normalnym UI
```

Nie cofaj zmian TASK-029.

---

# DO NOT

Nie:

- zmieniaj Core,
- zmieniaj schema,
- dodawaj migracji,
- zmieniaj dependencies,
- rozwijaj parsera,
- dodawaj OCR,
- dodawaj alias dictionary,
- zmieniaj AcceptSds validation,
- zmieniaj required fields,
- zmieniaj lifecycle SDS,
- zmieniaj lifecycle BHP,
- zmieniaj transaction behavior,
- implementuj upload/storage service,
- kopiuj/przenoś/usuwaj plików,
- przebudowuj ekran miejsc stosowania,
- przebudowuj Widok nadzorczy,
- implementuj TASK-031,
- dodawaj R8/R10/R11,
- wykonuj opportunistic refactor.

---

# EXPECTED CHANGE SURFACE

Przewidywany zakres:

```text
app/presentation/streamlit/add_sds.py
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/<existing_bhp_screen>.py
app/presentation/streamlit/composition.py   # tylko jeśli absolutnie konieczne

tests/unit/test_streamlit_add_sds.py
tests/unit/<product_registry_revision_tests>.py
tests/unit/<bhp_streamlit_tests>.py
tests/integration/test_streamlit_shell.py   # tylko jeśli composition/state integration tego wymaga

docs/task_reports/TASK-030_REPORT.md
```

### DO NOT TOUCH

Jeżeli nie ma bezpośredniej konieczności:

```text
Domain
ORM
Alembic
SDS persistence
BHP persistence
PDF parser
supervisory read model
usage locations persistence
```

---

# VALIDATION — LEVEL 2

## A. `Dodaj SDS`

Focused AppTests powinny potwierdzić:

1. formularz renderuje sekcje,
2. istniejące required fields są oznaczone,
3. chemia jest opcjonalna / subordinate,
4. manual fallback nadal działa,
5. `Odczytaj dane` nadal wypełnia istniejący draft,
6. `Zapisz / Akceptuj` nadal wywołuje istniejący use case,
7. komunikat sukcesu nie zawiera UUID.

Nie testuj ponownie parsera.

---

## B. Nowa rewizja SDS

Potwierdź:

1. wybrany PRODUCT jest jednoznacznie pokazany,
2. formularz nie tworzy nowego produktu,
3. brak odczytanej daty:

```text
issue_date = None
```

a nie data bieżąca,
4. jawnie podana data jest przekazywana bez zmiany,
5. istniejące focused tests PATCH-006 nadal PASS.

Nie testuj ponownie całego lifecycle PostgreSQL, jeśli kod Application/Persistence nie został zmieniony.

---

## C. Decyzja BHP

Potwierdź:

1. kontekst PRODUCT + CURRENT SDS jest czytelny,
2. evidence jest prezentowany nazwą pliku,
3. pełna techniczna ścieżka nie dominuje UI,
4. APPROVED/REJECTED nadal przekazują istniejące wartości domenowe,
5. po sukcesie UI ponownie odczytuje stan,
6. APPROVED pokazuje ACTIVE bez ręcznego refreshu strony,
7. REJECTED pokazuje REJECTED bez ręcznego refreshu strony,
8. istniejące focused tests BHP nadal PASS.

---

## D. Integration

Jeżeli zmiana dotyczy wyłącznie prezentacji i session state:

```text
focused AppTests + related regression
```

Jeżeli zmienisz composition albo sposób ponownego odczytu danych przez rzeczywistą warstwę Application:

```text
uruchom istniejący powiązany integration test
```

Nie dodawaj sztucznej integracji tylko dla liczby testów.

---

## E. Full regression

Nie uruchamiaj pełnego repo-wide pytest bez konkretnej przyczyny.

Pełna regresja jest obowiązkowa w:

```text
TASK-032 — ACCEPTANCE
```

---

# ACCEPTANCE CRITERIA

TASK-030 = DONE, gdy:

1. `Dodaj SDS` jest podzielony na logiczne, zwarte sekcje,
2. formularz wykorzystuje szerokość ekranu,
3. istniejące wymagane pola są oznaczone przed zapisem,
4. Safety Profile i Components są wizualnie opcjonalne,
5. manual fallback pozostaje dostępny,
6. nowa rewizja SDS jasno pokazuje wybrany produkt,
7. nieznana data SDS nie jest zastępowana datą bieżącą,
8. `Decyzja BHP` jasno pokazuje PRODUCT + CURRENT SDS,
9. evidence jest prezentowany użytkowo przez nazwę pliku,
10. po decyzji status produktu odświeża się automatycznie,
11. brak UUID i technicznych ścieżek w podstawowym workflow,
12. brak zmian Core/schema/migrations/dependencies,
13. brak zmian parsera i lifecycle,
14. focused tests PASS,
15. wymagane related integration tests PASS,
16. nie rozpoczęto TASK-031.

---

# PHYSICAL REVIEW

Po wykonaniu Tasku Architekt Operacyjny wykona trzy krótkie testy.

### 1. Dodaj SDS

```text
Dodaj SDS
→ wybierz PDF
→ Odczytaj dane
→ sprawdź układ formularza
→ sprawdź oznaczenie required fields
→ sprawdź opcjonalną chemię
```

Nie trzeba zapisywać produktu, jeśli ocena dotyczy tylko układu.

### 2. Nowa rewizja

```text
Produkty
→ wybierz produkt
→ Dodaj nową rewizję SDS
→ sprawdź kontekst produktu
→ sprawdź, że data nie jest automatycznie dzisiejsza
```

### 3. Decyzja BHP

Na produkcie `PENDING_APPROVAL`:

```text
Decyzja BHP
→ wybierz evidence
→ APPROVED
→ Zapisz
```

Oczekiwane bez ręcznego odświeżania:

```text
PRODUCT = ACTIVE
BHP = Dopuszczony
```

---

# STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. oznaczenie pól required wymaga zmiany kontraktu AcceptSds,
2. brak domyślnej daty wymaga zmiany schema/Core,
3. poprawny refresh BHP wymaga zmiany lifecycle/persistence,
4. evidence filename wymaga nowego storage service,
5. potrzebna jest nowa dependency,
6. Task zaczyna wymagać przebudowy parsera,
7. implementacja zaczyna wymagać repo-wide refactor.

Nie obchodź blokera przez duplikowanie logiki w Streamlit.

---

# REPORT — SHORT

Utwórz:

```text
docs/task_reports/TASK-030_REPORT.md
```

Format:

```text
# TASK-030 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- ...

ADD SDS UI:
- compact sections: YES / NO
- required fields visible: YES / NO
- optional chemistry subordinate: YES / NO
- manual fallback preserved: YES / NO
- UUID hidden: YES / NO

SDS REVISION UI:
- product context visible: YES / NO
- current SDS context visible: YES / NO
- unknown issue_date defaults to None: YES / NO
- lifecycle unchanged: YES / NO

BHP UI:
- product/current SDS context visible: YES / NO
- evidence shown as filename: YES / NO
- user-facing decision labels: YES / NO
- product status refresh after save: YES / NO
- BHP lifecycle unchanged: YES / NO

VALIDATION:
- focused Add SDS AppTests: ...
- focused revision tests: ...
- focused BHP AppTests: ...
- related regression: ...
- integration: ... / NOT REQUIRED

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- lifecycle/persistence changes: NONE

RISKS / DEVIATIONS:
- NONE / ...

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-031.
```

---

# AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj TASK-030.
```
