# TASK-037 — UI-14 / DOC-02 — Kontrolowany DECISION_EVIDENCE

**Projekt:** MSDS Manager  
**Obszar:** UI-14 / DOC-02 — dowód decyzji BHP  
**Task ID:** TASK-037  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-01  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## MODE

```text
INTEGRATION
```

## VALIDATION

```text
LEVEL 2
```

## REPORT

```text
SHORT / STANDARD INTEGRATION
```

---

# 1. GOAL

Wdrożyć `UI-14 / DOC-02` zgodnie z zatwierdzonym `BDR-008` i `TDR-007`.

Rezultat:

```text
Decyzja BHP
→ evidence = BRAK WYBORU na starcie
→ użytkownik jawnie:
   A. wybiera istniejący dowód
   albo
   B. dodaje nowy plik z komputera
→ zapis decyzji wymaga evidence
→ nowy evidence trafia WRITE-ONCE do BHP_EVIDENCE_ROOT_PATH
→ po COMMIT pozostaje chroniony
→ później użytkownik może otworzyć / pobrać dowód
→ MISSING jest sygnalizowany bez niszczenia historii
```

Task usuwa ryzyko automatycznego przypisania pierwszego przypadkowego pliku z katalogu jako dowodu decyzji.

---

# 2. AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj tylko niezbędny kontekst:

1. `BDR-008_Kontrolowany_dowod_BHP_v1.0-approved.md`
2. `TDR-007_Kontrolowany_import_i_dostep_DECISION_EVIDENCE_v1.0-approved.md`
3. `BDR-004 — Decyzja BHP, jej zakres i historia`
4. `CORE-001_MSDS_Manager_v1.2-approved`
5. `TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja`
6. `TDR-003 — struktura warstw aplikacji`
7. `TDR-006_Kontrolowany_import_SDS_v1.0-approved.md` wyłącznie jako wzorzec techniczny storage/compensation
8. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
9. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
10. root `AGENTS.md`
11. istniejący workflow `BHP_DECISION / DECISION_EVIDENCE`

Nie wykonuj repo-wide discovery bez potrzeby.

Jeżeli istniejący schema lub kontrakty evidence są sprzeczne z BDR-008 / TDR-007:

```text
STOP / BLOCKED
```

Nie zgaduj i nie zmieniaj schema samodzielnie.

---

# 3. KNOWN STARTING POINTS

Minimalnie zlokalizuj istniejące miejsca odpowiedzialne za:

```text
Streamlit:
- ekran Decyzja BHP
- wybór dowodu decyzji
- prezentację istniejącej decyzji / historii
- composition / dependency wiring

Application:
- use case rejestracji decyzji BHP
- use case korekty / nowej decyzji
- kontrakt DECISION_EVIDENCE
- read-side decyzji / evidence

Infrastructure:
- BHP_EVIDENCE_ROOT_PATH config
- filesystem evidence
- repositories BHP_DECISION / DECISION_EVIDENCE
- transaction/session wiring

Tests:
- BHP decision
- evidence
- CURRENT / SUPERSEDED
- Streamlit/AppTest
- PostgreSQL integration
```

Nazwy plików i symboli mogą różnić się od powyższych. Użyj bezpośrednich odpowiedników i nie rozszerzaj eksploracji poza potrzebny zakres.

---

# 4. EXPECTED CHANGE SURFACE

Oczekiwane:

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
app/infrastructure/config/     # tylko jeśli konieczne
app/infrastructure/db/         # tylko minimalne wiring
tests/
docs/task_reports/TASK-037_REPORT.md
```

Chronione:

```text
app/domain/
migrations/
Core docs
BDR/TDR
SDS parser
UNIT_OF_MEASURE
PRODUCT identity
SDS lifecycle
```

`pyproject.toml` bez nowych zależności, chyba że:

```text
STOP
→ decyzja Architekta Operacyjnego
```

---

# 5. DO

## 5.1. Neutralny stan evidence

Na ekranie `Decyzja BHP` pole dowodu ma startować jako:

```text
BRAK WYBORU
```

Technicznie:

```text
selected_evidence = None
```

Usuń zachowanie:

```text
pierwszy plik z listy
→ automatycznie wybrany
```

Zapis decyzji bez jawnie wskazanego evidence ma być kontrolowanie odrzucony.

---

## 5.2. Dwa jawne tryby wyboru

Dodaj dwa rozłączne warianty:

```text
A. Wybierz istniejący dowód
B. Dodaj nowy dowód z komputera
```

Dla pojedynczej operacji zapisu aktywny jest tylko jeden wariant.

### A. Istniejący dowód

- użytkownik jawnie wybiera plik,
- brak domyślnego zaznaczenia,
- potwierdź dostępność pliku,
- potwierdź, że ścieżka należy do `BHP_EVIDENCE_ROOT_PATH`,
- nie kopiuj pliku ponownie,
- nie podstawiaj innego pliku, jeśli wskazany jest `MISSING`.

### B. Nowy dowód

- użyj uploadu Streamlit,
- nie zapisuj pliku trwale przed Submit,
- trwały zapis wykonuje Application + filesystem adapter dopiero przy zatwierdzeniu decyzji.

---

## 5.3. Dozwolone formaty

Akceptuj wyłącznie:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Walidacja rozszerzenia case-insensitive.

Odrzuć:

```text
brak pliku
pusty plik
nieobsługiwane rozszerzenie
```

Nie polegaj wyłącznie na MIME przeglądarki.

Nie implementuj parsera MSG, OCR ani analizy semantycznej pliku.

---

## 5.4. Filesystem port / adapter

Application nie wykonuje bezpośrednio `open()` / `Path`.

Dodaj albo minimalnie rozszerz dedykowany port/adapter evidence.

Minimalne odpowiedzialności:

```text
list_existing_evidence(...)
store_new_evidence(...)
remove_unregistered_evidence(...)
resolve_existing_evidence_path(...)
read_existing_evidence(...)
check_availability(...)
```

Nazwy dopasuj do istniejącej konwencji repo.

Nie twórz generycznego DMS/storage frameworka.

---

## 5.5. Docelowy storage nowego evidence

Nowy plik zapisuj jako:

```text
BHP_EVIDENCE_ROOT_PATH/imported/<storage_uuid>.<normalized_extension>
```

Wymagania:

- techniczna nazwa nie pochodzi z `original_filename`,
- `storage_uuid` nie zastępuje `evidence_id`,
- rozszerzenie pochodzi z allowlist,
- `original_filename` zachowaj jako metadanę tylko wtedy, gdy istniejący model na to pozwala bez schema change.

Jeżeli wymagana identyfikowalność nie jest możliwa bez zmiany schema:

```text
STOP / BLOCKED
```

---

## 5.6. No-overwrite

Zapis nowego evidence:

```text
generate UUID
→ target
→ create-exclusive
```

Przy kolizji:

```text
nie nadpisuj
→ nowy UUID
→ ograniczona liczba prób
```

Zakazane:

```text
replace
silent overwrite
delete-then-write
```

---

## 5.7. Path safety

Docelowa ścieżka powstaje wyłącznie z:

```text
BHP_EVIDENCE_ROOT_PATH
+ imported
+ storage_uuid
+ kontrolowane rozszerzenie
```

`original_filename` nie steruje strukturą katalogów.

Zablokuj:

```text
../
..\
absolute path
UNC path
path traversal
wyjście poza BHP_EVIDENCE_ROOT_PATH
```

Resolved target musi należeć do resolved root.

---

## 5.8. Filesystem ↔ PostgreSQL — nowy evidence

Zachowaj sekwencję:

```text
1. zweryfikuj PRODUCT / CURRENT SDS / dane decyzji
2. zweryfikuj nowy evidence
3. wyznacz bezpieczny relative_path
4. zapisz NOWY plik create-exclusive
5. potwierdź istnienie pliku
6. rozpocznij / kontynuuj transakcję BHP
7. utwórz DECISION_EVIDENCE
8. utwórz BHP_DECISION
9. zachowaj CURRENT / SUPERSEDED
10. COMMIT PostgreSQL
11. po COMMIT plik = REGISTERED SOURCE
```

Filesystem FAIL:

```text
brak BHP_DECISION
brak DECISION_EVIDENCE
```

DB FAIL po write:

```text
ROLLBACK DB
→ compensation delete tylko pliku z tej niezakończonej operacji
→ ERROR
```

Po COMMIT compensation nie może usunąć evidence.

---

## 5.9. Istniejący evidence

Dla istniejącego pliku:

```text
jawny wybór użytkownika
→ availability check
→ root/path safety check
→ DECISION_EVIDENCE
→ BHP_DECISION
→ COMMIT
```

Nie twórz kolejnej kopii istniejącego pliku.

Nie zmieniaj go fizycznie.

---

## 5.10. Cleanup failure

Jeżeli rollback DB się powiedzie, ale compensation delete nie:

```text
operacja = FAILED
nie raportuj sukcesu
zwróć jednoznaczny błąd
wskaż orphan relative_path
```

Nie implementuj background janitora.

---

## 5.11. Ochrona po COMMIT

Po COMMIT evidence jest chronionym źródłem.

Standardowy workflow nie może:

- nadpisywać,
- usuwać,
- modyfikować,
- przenosić,
- podmieniać pliku w miejscu.

Korekta decyzji tworzy nowy rekord zgodnie z istniejącym lifecycle.

---

## 5.12. UI-14 — dostęp do dowodu

Po rejestracji umożliw użytkownikowi dostęp do evidence:

```text
PDF
→ download / browser open

JPG / JPEG / PNG
→ inline preview i/lub download

MSG
→ download
```

Nie implementuj:

```text
MSG parser
MSG → PDF
OCR
```

Nie eksponuj pełnych lokalnych ścieżek systemowych jako podstawowego UX.

---

## 5.13. MISSING

Jeżeli rekord evidence istnieje, ale plik fizyczny nie:

```text
MISSING
```

UI:

- pokazuje czytelny stan niedostępności,
- nie usuwa rekordu,
- nie podstawia innego pliku,
- nie zmienia `APPROVED / REJECTED`,
- pozostawia historię decyzji czytelną.

---

## 5.14. Lifecycle BHP

Nie zmieniaj:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
APPROVED / REJECTED
CURRENT / SUPERSEDED
```

Korekta decyzji nadal:

```text
previous CURRENT → SUPERSEDED
new decision → CURRENT
```

Nie twórz wielu evidence dla jednej decyzji.

---

# 6. DO NOT

Nie:

- zmieniaj schema PostgreSQL,
- twórz migracji Alembic,
- zmieniaj Core,
- zmieniaj modelu PRODUCT,
- zmieniaj SDS lifecycle,
- zmieniaj lifecycle BHP,
- zapisuj plików jako BLOB w PostgreSQL,
- implementuj parsera MSG,
- implementuj OCR,
- implementuj antywirusa,
- implementuj AI classification,
- implementuj automatycznego dopasowania evidence do produktu,
- implementuj wielu evidence na jedną decyzję,
- implementuj DMS,
- implementuj cloud/S3/object storage,
- implementuj fizycznego DELETE zarejestrowanego evidence,
- refaktoruj niezwiązanych obszarów,
- dodawaj nowych zależności bez STOP,
- trwale modyfikuj danych operatora w testach.

---

# 7. VALIDATION — LEVEL 2

Potwierdź co najmniej:

```text
1. ekran startuje z BRAK WYBORU
2. pierwszy plik z katalogu nie jest auto-selected
3. brak evidence → brak zapisu decyzji
4. jawny wybór istniejącego evidence → PASS
5. istniejący MISSING → czytelny stan, brak substytucji
6. upload .msg → PASS
7. upload .pdf → PASS
8. upload .jpg/.jpeg/.png → PASS
9. unsupported format → reject
10. empty file → reject
11. nowy plik → BHP_EVIDENCE_ROOT_PATH/imported/
12. techniczna nazwa bezkolizyjna
13. no-overwrite → PASS
14. path traversal blocked
15. filesystem failure → brak decision/evidence
16. DB failure po write → rollback + compensation delete
17. cleanup failure → FAILED + orphan path
18. successful COMMIT → plik pozostaje
19. 1:1 decision/evidence zachowane
20. correction → CURRENT / SUPERSEDED zachowane
21. PDF access/download → PASS
22. image preview/download → PASS
23. MSG download → PASS
24. MISSING nie niszczy historii
25. Streamlit/AppTest → PASS
26. PostgreSQL integration → PASS
27. filesystem isolation → PASS
28. operator data preserved → YES
29. orphan test files after validation → NONE
30. schema change → NONE
31. migration → NONE
32. Core change → NONE
33. new dependencies → NONE
34. git diff --check → PASS
```

Filesystem tests:

```text
isolated tmp directory
```

DB tests:

```text
isolated PostgreSQL / rollback
bez trwałej modyfikacji danych operatora
```

Nie wykonuj pełnego LEVEL 3 checkpointu wyłącznie dla TASK-037.

Focused + related regression wystarczy.

---

# 8. ACCEPTANCE CONDITIONS

TASK-037 = DONE, jeżeli:

```text
no default evidence
→ świadomy wybór operatora
→ existing lub upload
→ evidence wymagane
→ WRITE-ONCE dla nowego pliku
→ no-overwrite
→ path safety
→ compensation przy DB failure
→ 1:1 zachowane
→ CURRENT/SUPERSEDED zachowane
→ read/download działa
→ MISSING sygnalizowany
→ brak zmian schema/Core
```

---

# 9. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. implementacja wymaga schema change,
2. implementacja wymaga Core change,
3. istniejący model nie pozwala zachować `BHP_DECISION 1:1 DECISION_EVIDENCE`,
4. nie można zachować `CURRENT / SUPERSEDED`,
5. nie można zagwarantować no-overwrite,
6. nie można ograniczyć zapisu do `BHP_EVIDENCE_ROOT_PATH`,
7. compensation wymagałaby usunięcia pliku po COMMIT,
8. potrzebny jest parser MSG / OCR / DMS,
9. wymagana jest nowa zależność,
10. trzeba przebudować cały moduł BHP zamiast wykonać lokalną integrację,
11. poprawne testy wymagałyby trwałej zmiany danych operatora,
12. trzeba zgadywać znaczenie istniejącego schema lub kontraktów.

Nie wykonuj opportunistic work.

---

# 10. REPORT

Utwórz:

```text
docs/task_reports/TASK-037_REPORT.md
```

Minimalna struktura:

```text
# TASK-037 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- UI
- Application
- filesystem
- DB wiring, jeśli dotyczy
- tests

IMPLEMENTED:
- no-default evidence
- existing evidence selection
- upload
- validation
- safe storage
- no-overwrite
- path safety
- compensation
- read/download
- MISSING
- lifecycle preservation

VALIDATION:
- focused/related tests
- Streamlit/AppTest
- PostgreSQL integration
- filesystem isolation
- failure/compensation cases
- git diff --check

DATA SAFETY:
- operator data preserved: YES/NO
- orphan test files after validation: NONE / list

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- SDS lifecycle change: NO
- BHP lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY FOR CERBERUS REVIEW
- albo BLOCKED — <reason>
```

---

# 11. AUTHORIZATION BOUNDARY

```text
TASK-037
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Samo istnienie Tasku nie stanowi zgody na implementację.

Start wyłącznie po jawnym poleceniu:

```text
Wykonaj TASK-037.
```
