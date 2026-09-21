# PATCH-004 R1 — Jawna zależność `cryptography` dla odczytu AES-encrypted PDF SDS

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Domknąć PATCH-004 przez dodanie jawnej zależności projektu wymaganej przez `pypdf` do odczytu PDF szyfrowanych AES.

Potwierdzony przypadek rzeczywisty:

```text
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
```

Bez `cryptography`:

```text
encrypted = True
decrypt("") = 1
→ pypdf.errors.DependencyError:
  cryptography>=3.1 is required for AES algorithm
```

Po instalacji `cryptography` w `.venv`:

```text
encrypted = True
decrypt = 1
pages = 11
extract_text() = PASS
```

PATCH-004 R1 ma więc wyłącznie utrwalić brakującą zależność projektu i dodać regresję dla rzeczywistego przypadku AES.

---

## CONFIRMED ROOT CAUSE

Problem nie leży w:

```text
- parserze SDS,
- language detection,
- braku warstwy tekstowej,
- samym decrypt(""),
- konieczności OCR.
```

Root cause:

```text
pypdf wymaga pakietu cryptography do odszyfrowania obiektów AES,
ale zależność nie była zadeklarowana w projekcie.
```

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- `PATCH-004_Encrypted_PDF_Read.md`,
- `PATCH-004_REPORT.md`,
- ten PATCH,
- bezpośrednio powiązany plik zależności projektu,
- bezpośrednio powiązane focused tests PDF readera.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów.

Nie wykonuj repo-wide discovery.

---

## DO

### 1. Dodaj jawną zależność projektu

Dodaj `cryptography` do właściwego, obowiązującego pliku zależności projektu.

Użyj minimalnej specyfikacji zgodnej z aktualnym sposobem deklarowania dependencies w repo.

Wymaganie funkcjonalne:

```text
cryptography >= 3.1
```

Jeżeli projekt już stosuje nowszy minimalny baseline albo pinning wynikający z istniejącego stylu, zachowaj ten styl.

Nie twórz dodatkowego pliku zależności, jeśli projekt ma już jedno autorytatywne miejsce.

### 2. Nie zmieniaj istniejącej logiki PATCH-004

Zachowaj:

```python
reader = PdfReader(path)

if reader.is_encrypted:
    reader.decrypt("")
```

Nie refaktoryzuj tej logiki, jeśli nie jest to konieczne.

### 3. Dodaj focused regression dla AES-encrypted PDF

Test ma potwierdzić scenariusz:

```text
AES-encrypted PDF
+
decrypt("") succeeds
+
cryptography available
→ pages accessible
→ extract_text() returns text
```

Preferencja:

- jeżeli istniejąca polityka repo pozwala na mały fixture AES PDF, użyj fixture,
- w przeciwnym razie utwórz minimalny test w istniejącym stylu testów PDF readera.

Nie dodawaj dużego realnego SDS do repo, jeśli nie jest to konieczne.

### 4. Potwierdź brak regresji plain PDF

Istniejący zwykły PDF nadal:

```text
read → PASS
```

### 5. Potwierdź kontrolowany fail dla prawdziwie hasłowego PDF

Jeżeli istniejący test już to obejmuje:

```text
password-required PDF
→ controlled fail
```

Nie rozszerzaj zakresu tylko po to, aby tworzyć nowe mechanizmy password handling.

---

## EXPECTED CHANGE SURFACE

Preferowany zakres:

```text
1 plik dependencies
+
focused tests PDF readera
+
PATCH-004_R1_REPORT.md
```

Nie zmieniaj:

```text
parsera pól SDS
component parser
language detection
SDS acceptance
schema
migrations
Core lifecycle
UI
BHP workflow
supervisory view
```

---

## DO NOT

Nie:
- dodawaj OCR,
- dodawaj alternatywnej biblioteki PDF,
- zmieniaj `pypdf` bez konieczności,
- refaktoryzuj parsera,
- zmieniaj reguł rewizji SDS,
- implementuj password cracking,
- zapisuj odszyfrowanych kopii pliku,
- modyfikuj źródłowych SDS,
- wykonuj repo-wide review,
- analizuj historii Git,
- rozpoczynaj kolejnego tasku.

Jeżeli dodanie `cryptography` wymaga nieoczekiwanej przebudowy dependency management:

```text
STOP / BLOCKED
```

---

## VALIDATION — LEVEL 1

Uruchom wyłącznie focused tests związane z readerem PDF.

Wymagane:

```text
plain PDF → PASS
AES encrypted + empty-password decrypt → PASS
password-required PDF → CONTROLLED FAIL
textless PDF → zachowanie bez regresji
```

Jeżeli istniejący focused suite zawiera te przypadki, uruchom tylko ten suite.

Nie uruchamiaj automatycznie:

```text
pełnego pytest
PostgreSQL integration suite
Alembic
migracji
tymczasowych klastrów
```

---

## ACCEPTANCE CRITERIA

PATCH-004 R1 = DONE, gdy:

1. `cryptography` jest jawnie zadeklarowane w projekcie,
2. świeże środowisko projektu może zainstalować dependency bez ręcznego `pip install cryptography`,
3. AES-encrypted PDF z `decrypt("")` jest odczytywany,
4. plain PDF nadal działa,
5. password-required PDF nadal kończy się kontrolowanym błędem,
6. parser SDS nie został zmieniony,
7. focused tests PASS.

---

## PHYSICAL RE-TEST AFTER CODEX

Po zakończeniu PATCH-a użytkownik wykona fizyczny test na:

```text
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
```

Oczekiwany wynik:

```text
Dodaj SDS
→ wybór pliku
→ Odczytaj dane
→ formularz zostaje otwarty
→ brak "Could not read SDS PDF"
```

Dopiero po tym PATCH-004 można uznać za fizycznie zamknięty.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-004_R1_REPORT.md
```

Format:

```text
# PATCH-004 R1 REPORT

STATUS:
DONE / BLOCKED

ROOT CAUSE:
- ...

DEPENDENCY CHANGE:
- file:
- dependency:
- version rule:

VALIDATION:
- focused tests:
- plain PDF: PASS / FAIL
- AES encrypted PDF: PASS / FAIL
- password-required PDF: CONTROLLED FAIL / NOT TESTED
- textless PDF: PASS / FAIL / NOT TESTED

CHANGES OUTSIDE SCOPE:
- parser fields: NONE
- component parser: NONE
- language acceptance: NONE
- schema/migrations: NONE
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
Wykonaj PATCH-004 R1.
```
