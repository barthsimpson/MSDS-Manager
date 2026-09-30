# TASK-036 — DOC-01 — Kontrolowany import SDS z komputera

**Projekt:** MSDS Manager  
**Obszar:** DOC-01 — dodawanie SDS z komputera / kontrolowany import PDF  
**Task ID:** TASK-036  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-09-30  
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

Wdrożyć DOC-01: umożliwić użytkownikowi wskazanie lokalnego pliku PDF SDS bezpośrednio w istniejącym UI, a następnie wykonać kontrolowany import nowej kopii do:

```text
SDS_ROOT_PATH/imported/
```

zgodnie z modelem:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Po pomyślnym zatwierdzeniu formularza system ma:

```text
wybrać PDF z komputera
→ zwalidować wejście
→ zapisać nową kopię bez overwrite
→ zarejestrować SDS
→ zachować CURRENT / ARCHIVED
→ pozostawić zarejestrowany PDF jako chronione źródło
```

Bez ręcznego kopiowania pliku przez operatora do `SDS_ROOT_PATH`.

---

# 2. AUTHORITATIVE CONTEXT

Przed wykonaniem przeczytaj wyłącznie niezbędny kontekst:

1. `BDR-007_Kontrolowany_import_SDS_v1.0-approved.md`
2. `TDR-006_Kontrolowany_import_SDS_v1.0-approved.md`
3. `CORE-001_MSDS_Manager_v1.2-approved`
4. `BDR-003 — Dokument SDS, aktualność i wersjonowanie`
5. `TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja`
6. `TDR-003 — struktura warstw aplikacji`
7. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
8. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
9. root `AGENTS.md`
10. istniejący workflow rejestracji pierwszego SDS i nowej rewizji SDS
11. `PATCH-009_REPORT.md` wyłącznie jako aktualny baseline metadanych SDS w UI

Nie wykonuj repo-wide discovery bez potrzeby.

Jeżeli istniejące kontrakty repozytorium SDS są sprzeczne z BDR-007 / TDR-006:

```text
STOP / BLOCKED
```

Nie zgaduj.

---

# 3. KNOWN STARTING POINTS

Minimalnie zlokalizuj istniejące miejsca odpowiedzialne za:

```text
Streamlit:
- formularz pierwszego SDS
- formularz nowej rewizji SDS
- composition / dependency wiring

Application:
- istniejący use case rejestracji SDS
- istniejący use case rejestracji nowej rewizji SDS
- porty używane przez workflow SDS

Infrastructure:
- config SDS_ROOT_PATH
- app/infrastructure/filesystem/
- repozytoria SDS
- transaction/session wiring

Tests:
- testy SDS
- testy CURRENT / ARCHIVED
- testy Streamlit/AppTest dla dodawania SDS
- testy PostgreSQL integracyjne SDS
```

Nazwy plików/symboli mogą różnić się od powyższych. Znajdź bezpośrednie odpowiedniki i nie rozszerzaj eksploracji poza konieczny zakres.

---

# 4. EXPECTED CHANGE SURFACE

Oczekiwane obszary zmian:

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
app/infrastructure/config/      # tylko jeśli konieczne
app/infrastructure/db/          # tylko minimalne transaction wiring, jeśli konieczne
tests/
docs/task_reports/TASK-036_REPORT.md
```

Chronione przed nieuzasadnioną zmianą:

```text
app/domain/
migrations/
Core docs
BDR/TDR
parser SDS
BHP workflow
UNIT_OF_MEASURE
pyproject.toml                  # bez nowych zależności, chyba że STOP + decyzja
```

---

# 5. DO

## 5.1. UI — upload PDF

W obu istniejących workflow:

```text
Dodaj pierwszy SDS
Dodaj nową rewizję SDS
```

dodaj wybór pliku PDF z komputera przez standardowy mechanizm uploadu Streamlit.

UI:

- przyjmuje wyłącznie `.pdf`,
- nie zapisuje samodzielnie pliku do filesystem,
- nie ustala `relative_path`,
- nie wykonuje SQL,
- przekazuje plik i dane formularza do Application,
- nie zapisuje trwale pliku przed jawnym zatwierdzeniem formularza.

Jeżeli obecny formularz eksponuje ręczne pole `relative_path` dla tego workflow, zastąp je kontrolowanym uploadem.

## 5.2. Application — orkiestracja importu

Application ma przyjąć co najmniej:

```text
product_id
original_filename
pdf_bytes / binary stream
issue_date
revision
pozostałe istniejące dane formularza SDS
```

i wykonać:

```text
walidacja wejścia
→ zapis nowego PDF przez filesystem port
→ rejestracja SDS
→ compensation przy błędzie DB
```

Preferuj minimalne rozszerzenie istniejącego use case rejestracji SDS.

Jeżeli bezpieczne rozszerzenie istniejącego use case mieszałoby odpowiedzialności, utwórz osobny use case importujący, który deleguje do istniejącej logiki rejestracji SDS.

Nie przepisuj całego workflow SDS.

## 5.3. Walidacja PDF

Przed trwałym zapisem wymagane jest:

```text
1. wejście istnieje
2. plik nie jest pusty
3. rozszerzenie nazwy wejściowej = .pdf, case-insensitive
4. zawartość rozpoczyna się od sygnatury %PDF-
5. target pozostaje wewnątrz SDS_ROOT_PATH
```

Nie polegaj wyłącznie na MIME z przeglądarki.

Nie implementuj pełnej walidacji struktury PDF.

## 5.4. Filesystem port / adapter

Application nie wykonuje bezpośrednio `open()` / `Path`.

Dodaj albo minimalnie rozszerz port i adapter filesystem odpowiedzialny za kontrolowany storage SDS.

Minimalne odpowiedzialności:

```text
validate destination root
store_new_pdf(...)
remove_unregistered_file(...)
resolve_existing_path(...)     # tylko jeśli istniejący workflow tego wymaga
```

Nazwy symboli dopasuj do istniejącej konwencji repo.

Nie buduj generycznego DMS ani frameworka storage.

## 5.5. Docelowa ścieżka

Nowo importowany plik zapisuj jako:

```text
SDS_ROOT_PATH/imported/<storage_uuid>.pdf
```

`storage_uuid`:

- jest techniczną nazwą pliku,
- nie jest `sds_id`,
- nie pochodzi z `original_filename`.

Baza nadal przechowuje:

```text
original_filename
relative_path
```

Nie zapisuj pełnej lokalnej ścieżki źródłowej komputera użytkownika.

## 5.6. No-overwrite

Zapis nowego PDF ma używać mechanizmu wykluczającego nadpisanie istniejącego pliku:

```text
generate UUID
→ target
→ create-exclusive
```

Jeżeli target istnieje:

```text
nie nadpisuj
→ nowy UUID
→ ograniczona liczba prób
```

Jeżeli nie uda się utworzyć bezkolizyjnej ścieżki:

```text
STOP / ERROR
```

Nie używaj `replace` ani mechanizmu z cichym overwrite.

## 5.7. Path safety

Docelowa ścieżka jest budowana wyłącznie z:

```text
SDS_ROOT_PATH
+ stały katalog imported
+ wygenerowany UUID
```

`original_filename` jest wyłącznie metadaną.

Zablokuj możliwość:

```text
../
..\
absolute path
UNC path
wyjścia poza SDS_ROOT_PATH
```

Przed zapisem sprawdź, że resolved target należy do resolved `SDS_ROOT_PATH`.

Brak poprawnego / dostępnego `SDS_ROOT_PATH`:

```text
ERROR
→ brak rekordu SDS
```

## 5.8. Filesystem ↔ PostgreSQL

Zachowaj dokładną sekwencję:

```text
1. zweryfikuj PRODUCT i dane wejściowe
2. zweryfikuj PDF
3. wyznacz bezpieczną relative_path
4. zapisz NOWY PDF create-exclusive
5. potwierdź istnienie pliku
6. rozpocznij / kontynuuj transakcję SDS
7. utwórz rekord SDS
8. zachowaj istniejący CURRENT / ARCHIVED lifecycle
9. COMMIT PostgreSQL
10. po COMMIT plik staje się REGISTERED SOURCE
```

Jeżeli filesystem write FAIL:

```text
brak rekordu SDS
```

Jeżeli DB FAIL po utworzeniu pliku:

```text
ROLLBACK DB
→ usuń wyłącznie plik utworzony przez tę niezakończoną operację
→ zgłoś błąd
```

Po skutecznym COMMIT compensation nie może usuwać zarejestrowanego pliku.

## 5.9. Cleanup failure

Jeżeli DB rollback zakończy się powodzeniem, ale usunięcie nowego niezarejestrowanego pliku się nie powiedzie:

```text
STATUS operacji = FAILED
nie raportuj sukcesu
zwróć jednoznaczny błąd
udostępnij relative_path osieroconego pliku do ręcznego cleanupu
```

Nie buduj background janitora ani automatycznego masowego cleanupu.

## 5.10. Lifecycle SDS

Nie zmieniaj:

```text
CURRENT
ARCHIVED
```

Nowa rewizja nadal ma korzystać z istniejącej reguły:

```text
previous CURRENT → ARCHIVED
new SDS → CURRENT
```

Nie wyznaczaj CURRENT na podstawie:

```text
nazwy pliku
revision
issue_date
```

`revision = NULL` pozostaje poprawnym przypadkiem.

---

# 6. DO NOT

Nie:

- zmieniaj schema PostgreSQL,
- twórz migracji Alembic,
- zmieniaj Core,
- zmieniaj modelu PRODUCT,
- zmieniaj lifecycle SDS,
- zapisuj PDF jako BLOB w PostgreSQL,
- implementuj UI-11,
- implementuj UI-14 / DOC-02,
- implementuj parsera Stage 2,
- implementuj OCR,
- implementuj antywirusa,
- implementuj deduplikacji po hash,
- implementuj DMS,
- implementuj cloud/S3/object storage,
- implementuj fizycznego DELETE zarejestrowanego SDS,
- refaktoruj niezwiązanych obszarów,
- dodawaj nowych zależności bez STOP i decyzji,
- używaj danych operatora do testów w sposób trwały.

---

# 7. VALIDATION — LEVEL 2

Potwierdź co najmniej:

```text
1. poprawny PDF → zapis w SDS_ROOT_PATH/imported/
2. original_filename zachowane w DB
3. relative_path w DB, bez pełnej ścieżki źródłowej
4. nazwa techniczna = bezkolizyjna UUID .pdf
5. istniejący plik nie jest nadpisywany
6. non-PDF → reject
7. empty file → reject
8. .pdf bez %PDF- → reject
9. malicious/path-like original_filename nie wychodzi poza SDS_ROOT_PATH
10. filesystem failure → brak rekordu SDS
11. DB failure po write → rollback + compensation delete
12. cleanup failure → FAILED + orphan relative_path
13. successful COMMIT → plik pozostaje
14. pierwszy SDS → PASS
15. kolejna rewizja → CURRENT / ARCHIVED PASS
16. revision = NULL → PASS
17. Streamlit/AppTest dla obu formularzy → PASS
18. PostgreSQL integration → PASS
19. operator data preserved → YES
20. schema change → NONE
21. migration → NONE
22. parser/Core change → NONE
23. git diff --check → PASS
```

Testy filesystem:

```text
isolated temporary directory
```

Testy PostgreSQL:

```text
isolated / rollback
bez trwałej modyfikacji danych operatora
```

Nie uruchamiaj pełnego LEVEL 3 checkpointu tylko z powodu tego Tasku.

Focused + related regression wystarczy, chyba że ujawniony problem wymaga szerszej diagnostyki.

---

# 8. ACCEPTANCE CONDITIONS

TASK-036 = DONE, jeżeli:

```text
operator wybiera PDF z komputera
→ upload nie zapisuje pliku przed zatwierdzeniem
→ zatwierdzenie wykonuje kontrolowany WRITE-ONCE
→ zapis trafia do SDS_ROOT_PATH/imported/
→ brak overwrite
→ relative_path jest bezpieczny
→ DB i filesystem są spójne przez compensation
→ pierwszy SDS działa
→ kolejna rewizja działa
→ CURRENT / ARCHIVED zachowane
→ zarejestrowany PDF pozostaje chroniony
→ brak zmian schema/Core/parsera
```

---

# 9. STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. implementacja wymaga zmiany schema,
2. implementacja wymaga zmiany Core,
3. istniejący lifecycle nie pozwala zachować spójności `CURRENT / ARCHIVED`,
4. wymagane byłoby przechowywanie PDF w PostgreSQL,
5. nie można zagwarantować no-overwrite,
6. nie można ograniczyć zapisu do `SDS_ROOT_PATH`,
7. compensation musiałaby usuwać plik po skutecznym COMMIT,
8. konieczny byłby parser / deduplikacja / DMS poza zakresem,
9. wymagana jest nowa zależność,
10. istniejący kod storage/rejestracji jest sprzeczny z BDR-007/TDR-006,
11. poprawny test wymaga trwałej modyfikacji danych operatora,
12. trzeba zgadywać decyzję biznesową lub techniczną nieopisaną w zatwierdzonych źródłach.

Nie wykonuj opportunistic work.

---

# 10. REPORT

Utwórz:

```text
docs/task_reports/TASK-036_REPORT.md
```

Raport krótki / standard integration:

```text
# TASK-036 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- UI
- Application
- filesystem
- db wiring, jeśli dotyczy
- tests

IMPLEMENTED:
- upload
- validation
- safe storage
- no-overwrite
- path safety
- filesystem→DB orchestration
- compensation
- CURRENT/ARCHIVED preservation

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
- parser change: NO
- lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY FOR CERBERUS REVIEW
- albo BLOCKED — <reason>
```

---

# 11. AUTHORIZATION BOUNDARY

Dokument Tasku:

```text
TASK-036
STATUS: READY / NOT AUTHORIZED FOR EXECUTION
```

Samo istnienie Tasku nie stanowi zgody na implementację.

Start wyłącznie po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-036.
```
