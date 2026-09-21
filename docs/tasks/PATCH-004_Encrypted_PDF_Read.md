# PATCH-004 — Odczyt zaszyfrowanych / copy-protected PDF SDS

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Naprawić odczyt poprawnych PDF SDS, które:

- otwierają się normalnie dla użytkownika,
- mają warstwę tekstową,
- są oznaczone jako encrypted / copy-protected,
- mogą zostać odczytane przez `pypdf` po standardowym `decrypt("")`,
- obecnie kończą się w aplikacji błędem:

```text
Could not read SDS PDF: <path>
```

Reprezentatywny przypadek:

```text
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
```

Nie zmieniaj parsera pól SDS. PATCH dotyczy wyłącznie technicznego odczytu tekstu z PDF.

---

## CONFIRMED CASE

Dla reprezentatywnego PDF:

```text
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
```

dokument:
- jest poprawnym SDS,
- ma tekstową zawartość,
- jest zabezpieczony / copy-protected,
- daje się otworzyć przez `pypdf`,
- tekst można wydobyć po obsłużeniu encrypted PDF i `decrypt("")`.

Obecna aplikacja zatrzymuje się przed parserem pól i zwraca:

```text
Could not read SDS PDF
```

---

## BUSINESS RULE

Obowiązująca zasada:

```text
Jeżeli PDF można technicznie bezpiecznie otworzyć i odczytać jego warstwę tekstową,
aplikacja powinna przekazać tekst dalej do istniejącego parsera SDS.
```

Zabezpieczenie typu:

```text
copy:no
```

nie ma być traktowane jako automatyczny błąd odczytu, jeśli biblioteka może legalnie otworzyć dokument bez hasła użytkownika.

Nie omijaj haseł właściciela/użytkownika wymagających znajomości sekretu.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- bezpośrednio powiązany adapter / reader PDF,
- bezpośrednio powiązane focused tests.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów ani raportów historycznych.

Nie wykonuj repo-wide discovery.

---

## DO

### 1. Zlokalizuj reader PDF

Znajdź minimalny kod odpowiedzialny za:

```text
PDF path
→ PdfReader
→ extract_text()
→ raw text
```

Nie rozszerzaj analizy poza bezpośredni reader/adapter i jego testy.

### 2. Dodaj obsługę encrypted PDF

Preferowane zachowanie:

```python
reader = PdfReader(path)

if reader.is_encrypted:
    result = reader.decrypt("")
```

Następnie kontynuuj istniejący odczyt tekstu.

Jeżeli API używanej wersji `pypdf` zwraca status decrypt, obsłuż go zgodnie z dokumentacją biblioteki i obecnym stylem kodu.

### 3. Zachowaj bezpieczny fail

Jeżeli:

- PDF wymaga rzeczywistego hasła,
- `decrypt("")` nie pozwala na odczyt,
- dokument jest uszkodzony,
- `extract_text()` nadal nie daje treści wymaganej przez pipeline,

zachowaj istniejący kontrolowany błąd:

```text
Could not read SDS PDF
```

Nie próbuj zgadywać haseł.

### 4. Nie zmieniaj parsera SDS

Po uzyskaniu tekstu przekaż go do istniejącego parsera bez zmian.

Nie poprawiaj w tym PATCH-u:
- aliases,
- product_name extraction,
- manufacturer extraction,
- component parsing,
- language detection,
- revision/date parsing.

---

## EXPECTED CHANGE SURFACE

Preferowany zakres:

```text
1 reader/adapter PDF
+
focused tests
+
PATCH-004_REPORT.md
```

Bez zmian:

```text
schema
migrations
dependencies
Core lifecycle
SDS acceptance rules
component parser
UI layout
BHP workflow
supervisory view
```

---

## DO NOT

Nie:
- dodawaj OCR,
- dodawaj drugiej biblioteki PDF,
- zmieniaj dependency versions,
- przebudowuj parsera,
- implementuj password cracking,
- zapisuj odszyfrowanej kopii PDF na dysku,
- kopiuj ani modyfikuj źródłowego SDS,
- zmieniaj UI,
- wykonuj repo-wide review,
- analizuj historii Git,
- rozpoczynaj kolejnego tasku.

Jeżeli obecna wersja `pypdf` nie pozwala na tę poprawkę bez zmiany dependencies:

```text
STOP / BLOCKED
```

---

## VALIDATION — LEVEL 1

Wykonaj focused validation.

### A. Existing plain PDF

Istniejący zwykły PDF nadal:

```text
read → PASS
```

### B. Encrypted / copy-protected PDF

Dodaj focused test dla dokumentu reprezentującego:

```text
reader.is_encrypted == True
decrypt("") succeeds
extract_text() returns text
→ PASS
```

Jeżeli użycie realnego pliku testowego jest zgodne z istniejącą polityką repo, można użyć reprezentatywnego fixture.
Jeżeli nie, zbuduj minimalny test jednostkowy bez dodawania dużych artefaktów.

### C. Password-protected failure

Jeżeli obecna architektura testów na to pozwala, potwierdź:

```text
decrypt("") fails
→ controlled read error
```

Nie rozszerzaj zakresu tylko po to, aby stworzyć ten test, jeśli wymagałby nowego frameworka fixture.

### D. No broad validation

Nie uruchamiaj automatycznie:

- pełnego pytest,
- PostgreSQL integration suite,
- Alembic,
- migracji,
- tymczasowego klastra.

Tylko focused tests związane z readerem PDF.

---

## ACCEPTANCE CRITERIA

PATCH-004 = DONE, gdy:

1. zwykłe PDF-y nadal są odczytywane,
2. encrypted/copy-protected PDF możliwy do otwarcia przez `decrypt("")` jest odczytywany,
3. PDF wymagający realnego hasła nadal kończy się kontrolowanym błędem,
4. parser pól SDS nie został zmieniony,
5. dependencies nie zostały zmienione,
6. focused tests PASS.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. poprawka wymaga nowej biblioteki,
2. poprawka wymaga zmiany dependencies,
3. `decrypt("")` nie działa z obecną wersją `pypdf`,
4. potrzebna byłaby zmiana parsera SDS,
5. problem wynika z innej warstwy niż PDF reader i wymaga szerszej ingerencji.

Nie naprawiaj problemów pobocznych.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-004_REPORT.md
```

Format:

```text
# PATCH-004 REPORT

STATUS:
DONE / BLOCKED

CAUSE:
- ...

CHANGED:
- ...

BEHAVIOR:
- plain PDF read: PASS / FAIL
- encrypted PDF with empty-password decrypt: PASS / FAIL
- password-required PDF: CONTROLLED FAIL / NOT TESTED

VALIDATION:
- focused tests: ...

CHANGES OUTSIDE SCOPE:
- parser fields: NONE
- language acceptance: NONE
- schema/migrations: NONE
- dependencies: NONE
- UI: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-004.
```
