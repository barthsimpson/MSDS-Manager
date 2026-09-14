# TASK-021 — Sprint 3 End-to-End Acceptance

**Projekt:** MSDS Manager  
**Task ID:** TASK-021  
**Sprint:** SPRINT-003 — „Dodaj SDS”  
**Status:** READY  
**Typ:** Acceptance / End-to-End / Sprint Closure Candidate  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Przeprowadzić końcową walidację Sprintu 3 jako jednego działającego workflow:

```text
SDS_ROOT_PATH
   ↓
Streamlit „Dodaj SDS”
   ↓
PrepareSdsDraft
   ↓
PdfSdsExtractor
   ↓
formularz / ręczna korekta
   ↓
AcceptSds
   ↓
TransactionExecutor
   ↓
PostgreSQL
   ↓
PRODUCT = PENDING_APPROVAL
SDS = CURRENT
SAFETY_PROFILE
SDS_COMPONENTS
PRODUCT_HISTORY
```

TASK-021 jest Taskiem acceptance.

Nie ma rozwijać nowych funkcji.

---

## 2. Źródła obowiązujące

Przed wykonaniem przeczytaj co najmniej:

- root `AGENTS.md`,
- SPRINT-003,
- TASK-017 + REPORT,
- TASK-018 + REPORT,
- TASK-019 + REPORT,
- TASK-020 + REPORT,
- aktualny CORE-001,
- BDR-001,
- BDR-003,
- BDR-005,
- TDR-001,
- TDR-002,
- TDR-003,
- TDR-004.

Jeżeli E2E ujawni potrzebę nowej decyzji biznesowej lub zmiany Core:

```text
STOP
```

Nie zgaduj.

---

## 3. Zasada TASK-021

Preferowany wynik:

```text
0 nowych funkcji
+
1 pełny scenariusz E2E
+
1 scenariusz kolejnego SDS dla istniejącego PRODUCT
+
pełna regresja
+
raport acceptance
```

Drobny jednoznaczny defekt techniczny można naprawić tylko wtedy, gdy:

- nie zmienia Core,
- nie zmienia schema,
- nie dodaje nowych funkcji,
- nie wymaga nowego statusu/enuma,
- nie rozszerza Sprintu.

Każdą korektę opisz w raporcie.

Jeżeli potrzebna byłaby nowa funkcja lub decyzja:

```text
PARTIAL / BLOCKED
```

---

## 4. Baseline

Przed E2E sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check

$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"

.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwany stan po TASK-020:

```text
pytest        119 passed
Alembic       e0dd7d6468bf (head)
schema        12 tables
drift         none
```

Jeżeli rzeczywisty stan różni się, wyjaśnij przyczynę.

---

## 5. Fixture SDS

Do głównego scenariusza użyj rzeczywistego dokumentu:

```text
30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

Na potrzeby E2E dokument musi być dostępny pod skonfigurowanym:

```text
SDS_ROOT_PATH
```

Fixture może zostać kontrolowanie skopiowany do katalogu testowego używanego jako `SDS_ROOT_PATH` wyłącznie w setupie testu.

Nie zmieniaj produkcyjnej zasady pracy z plikami.

Po teście fixture ma zostać usunięty z testowego katalogu root.

---

## 6. Scenariusz A — pierwszy SDS / nowy PRODUCT

### A1. Start UI

Uruchom Streamlit/AppTest z konfiguracją korzystającą z kontrolowanego `SDS_ROOT_PATH`.

Potwierdź, że widok:

```text
Dodaj SDS
```

jest dostępny.

### A2. Wybór pliku

Potwierdź, że fixture `30470...pdf` jest widoczny do wyboru.

### A3. Odczyt

Kliknij:

```text
Odczytaj dane
```

Potwierdź, że UI przechodzi przez `PrepareSdsDraft`.

### A4. Wypełnienie formularza

Potwierdź co najmniej poprawny odczyt:

```text
product_name
manufacturer_product_code
use_description
use_restriction
issue_date
revision
```

Dla fixture 30470 oczekiwane co najmniej:

```text
product_name = IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO
manufacturer_product_code = 30470
use_description = Farba lub inna podobna substancja.
use_restriction = Jedynie do stosowania przemysłowego.
issue_date = 2025-10-03
revision = 10.02
```

Producent może wymagać ręcznego wpisania, jeśli parser pozostawia `None`.

### A5. Manual correction

Ręcznie zmień co najmniej jedno pole edytowalne, np.:

```text
manufacturer_name
```

lub inne pole wymagające manual fallback.

Potwierdź, że do `AcceptSdsInput` trafia wartość po korekcie, a nie pierwotna wartość parsera.

### A6. SAFETY_PROFILE

Potwierdź, że formularz zawiera zatwierdzone pola profilu bezpieczeństwa.

Nie wymagaj, by wszystkie były automatycznie odczytane.

Braki mają pozostać edytowalne i zgodne z:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

### A7. SDS_COMPONENTS

Potwierdź, że odczytany co najmniej jeden składnik jest widoczny.

Dla fixture 30470 potwierdź co najmniej obecność składnika z:

```text
CAS = 111-76-2
```

### A8. Akceptacja

Kliknij:

```text
Zapisz / Akceptuj
```

Potwierdź, że UI wywołuje `AcceptSds`.

### A9. Stan PostgreSQL

Po sukcesie potwierdź w PostgreSQL:

```text
MANUFACTURER istnieje
PRODUCT istnieje
PRODUCT.usage_status = PENDING_APPROVAL
SDS.document_status = CURRENT
SAFETY_PROFILE istnieje
SDS_COMPONENTS istnieją
PRODUCT_HISTORY istnieje
```

Potwierdź brak częściowych rekordów.

### A10. Stan UI po sukcesie

Potwierdź:

- komunikat sukcesu,
- informację o oczekiwaniu na decyzję BHP,
- wyczyszczenie draftu z `session_state`.

---

## 7. Scenariusz B — kolejny SDS dla istniejącego PRODUCT

Celem jest potwierdzenie kluczowej reguły R4:

```text
old CURRENT → ARCHIVED
new SDS     → CURRENT
PRODUCT     → PENDING_APPROVAL
```

### B1. Przygotowanie drugiego dokumentu

Użyj kontrolowanego drugiego fixture reprezentującego kolejną wersję SDS tego samego PRODUCT.

Dopuszczalne podejście testowe:
- kopia fixture techniczna pod inną ścieżką/nazwą w testowym SDS_ROOT_PATH,
- z kontrolowaną zmianą danych wejściowych formularza po odczycie, np. rewizji,
- pod warunkiem że test nie udaje automatycznego odczytu nowej treści PDF.

Nie modyfikuj oryginalnego PDF.

### B2. Akceptacja drugiego SDS

Przejdź ten sam workflow do `AcceptSds`.

### B3. Weryfikacja

Potwierdź:

```text
PRODUCT count nadal = 1 dla tej tożsamości
SDS count = 2
stary SDS = ARCHIVED
nowy SDS = CURRENT
CURRENT count = 1
PRODUCT = PENDING_APPROVAL
powstał kolejny PRODUCT_HISTORY snapshot
```

Poprzedni SDS i jego profil/składniki pozostają w historii.

---

## 8. Scenariusz C — anulowanie

Sprawdź:

```text
Odczytaj dane
→ draft
→ Anuluj
```

Potwierdź:

- draft znika,
- `AcceptSds` nie jest wywołany,
- brak nowych rekordów Core.

---

## 9. Scenariusz D — błąd

Wykonaj jeden kontrolowany przypadek błędu, np.:

- brak wymaganego pola,
- plik poza root,
- niewłaściwy typ,
- kontrolowany błąd Application.

Potwierdź:

- czytelny komunikat `st.error`,
- brak stack trace dla użytkownika,
- brak częściowego zapisu Core,
- brak fałszywego komunikatu sukcesu.

---

## 10. PostgreSQL jako źródło prawdy

Nie kończ acceptance na UI.

Po każdym scenariuszu zapisującym dane potwierdź rzeczywisty stan PostgreSQL.

Sprawdź zgodność:

```text
UI
=
Application
=
PostgreSQL current state
=
history
```

Nie dodawaj SQL do Streamlit.

---

## 11. Historia

Potwierdź:

### po pierwszym SDS

```text
initial PRODUCT_HISTORY
```

### po kolejnym SDS

```text
kolejny PRODUCT_HISTORY snapshot
```

Nie twórz nowego history framework.

Historia SDS wynika z zachowania rekordów:

```text
ARCHIVED
CURRENT
```

---

## 12. Cleanup

Po całym E2E:

- usuń/rollbackuj wyłącznie dane fixture testowych,
- usuń testowy PDF z kontrolowanego testowego `SDS_ROOT_PATH`,
- nie twórz publicznych delete use case'ów,
- nie usuwaj danych produkcyjnych.

Po cleanup potwierdź, że baza wróciła do stanu sprzed testu.

Jeżeli testy korzystają z izolowanej transakcji / testowej bazy, wykorzystaj istniejący mechanizm.

---

## 13. Kontrola DoD SPRINT-003

W raporcie oznacz każdy punkt:

```text
PASS
FAIL
NOT VERIFIED
```

Sprawdź co najmniej:

1. istnieje funkcja `Dodaj SDS`,
2. użytkownik może wskazać PDF z `SDS_ROOT_PATH`,
3. system próbuje odczytać zatwierdzone pola,
4. brak odczytu nie blokuje manual fallback,
5. użytkownik może poprawić dane,
6. przed akceptacją nie powstają rekordy Core,
7. po akceptacji powstaje spójny zestaw danych,
8. nowy PRODUCT powstaje zgodnie z Core,
9. istniejący PRODUCT może otrzymać nowy SDS,
10. MANUFACTURER jest poprawnie powiązany,
11. SDS jest CURRENT,
12. poprzedni CURRENT przechodzi na ARCHIVED,
13. SAFETY_PROFILE jest zapisany,
14. SDS_COMPONENTS są zapisane,
15. PRODUCT = PENDING_APPROVAL,
16. operacja jest atomowa,
17. rollback działa,
18. PDF nie jest modyfikowany,
19. brak AI/OCR/parser framework,
20. brak BHP,
21. pełna regresja przechodzi,
22. E2E Sprintu 3 przechodzi.

Codex nie zamyka Sprintu samodzielnie.

---

## 14. Regression

Po E2E uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:

- wszystkie testy PASS,
- brak `SAWarning`.

Nie osłabiaj wcześniejszych testów.

---

## 15. Alembic / schema

TASK-021 nie powinien wymagać nowej migracji.

Potwierdź:

```text
alembic current = e0dd7d6468bf (head)
alembic check = No new upgrade operations detected.
schema = 12 tables
```

Jeżeli E2E wymaga schema change:

```text
STOP
```

---

## 16. Architektura

Potwierdź nadal:

```text
Streamlit
   ↓
Application
   ↓
Domain

Infrastructure implements ports
```

W szczególności:

- Streamlit bez SQL/ORM/commit/rollback,
- Application bez Streamlit/SQLAlchemy/pypdf,
- Domain bez Infrastructure,
- parser pozostaje w Infrastructure,
- transakcja pozostaje w istniejącym TransactionExecutor.

---

## 17. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:

- `.env` ignored / nietrackowany,
- brak sekretów,
- brak nowych niekontrolowanych PDF/MSG,
- brak dumpów/backupów,
- brak commit/push bez polecenia,
- brak trwałych fixture po E2E.

---

## 18. Poza zakresem

TASK-021 NIE implementuje:

```text
BHP workflow
Decision Evidence
ACTIVE / REJECTED po decyzji BHP
OCR
AI/LLM
REACH
barcode
periodic review
Excel import
new parser framework
new schema
new dependencies
new business statuses
```

Nie rozpoczynaj R5.

---

## 19. STOP CONDITIONS

Zatrzymaj jako `PARTIAL / BLOCKED`, jeśli:

- E2E ujawnia potrzebę nowej funkcji,
- potrzebna jest zmiana Core,
- potrzebna jest zmiana schema/migracja,
- potrzebny jest nowy status/enum,
- potrzebna jest nowa zależność,
- wymagana byłaby funkcja BHP,
- problemu nie da się naprawić bez rozszerzenia zakresu Sprintu.

---

## 20. Definition of Done TASK-021

TASK-021 = DONE tylko gdy:

1. baseline jest zielony,
2. realny SDS 30470 przechodzi przez UI,
3. parser wypełnia formularz,
4. manual correction działa,
5. AcceptSds zapisuje dane,
6. PRODUCT = PENDING_APPROVAL,
7. SDS = CURRENT,
8. SafetyProfile istnieje,
9. Components istnieją,
10. ProductHistory istnieje,
11. drugi SDS tego samego PRODUCT archiwizuje poprzedni CURRENT,
12. po drugim SDS nadal istnieje dokładnie jeden CURRENT,
13. anulowanie nie zapisuje Core,
14. kontrolowany błąd nie zapisuje częściowych danych,
15. PostgreSQL potwierdza stan,
16. cleanup działa,
17. pełny pytest PASS,
18. brak SAWarning,
19. Alembic bez driftu,
20. schema nadal 12 tabel,
21. brak nowych zależności,
22. wszystkie punkty DoD SPRINT-003 = PASS,
23. R5 nie został rozpoczęty.

---

## 21. Raport

Utwórz:

```text
docs/task_reports/TASK-021_REPORT.md
```

Raport ma zawierać:

1. status `DONE / PARTIAL / BLOCKED`,
2. baseline,
3. zmienione pliki,
4. informację, czy zmieniono production code i dlaczego,
5. sposób przygotowania testowego `SDS_ROOT_PATH`,
6. przebieg scenariusza A,
7. odczyt fixture 30470,
8. manual correction,
9. stan PostgreSQL po pierwszym SDS,
10. przebieg scenariusza B,
11. CURRENT/ARCHIVED po drugim SDS,
12. ProductHistory,
13. scenariusz anulowania,
14. scenariusz błędu,
15. cleanup,
16. pełny pytest,
17. SAWarning,
18. Alembic current/check,
19. schema/table count,
20. architekturę,
21. Git/bezpieczeństwo,
22. tabelę DoD SPRINT-003: PASS/FAIL/NOT VERIFIED,
23. odstępstwa i ryzyka,
24. rekomendację:
   - `READY FOR SPRINT-003 CLOSURE`
   albo
   - `NOT READY FOR SPRINT-003 CLOSURE`.

Codex nie podejmuje formalnej decyzji o zamknięciu Sprintu.

---

## 22. Autoryzacja

Sama obecność TASK-021 nie stanowi zgody na wykonanie.

Start dopiero po poleceniu:

```text
Wykonaj TASK-021.
```

Po wykonaniu:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM R5 ANI WORKFLOW BHP.
```
