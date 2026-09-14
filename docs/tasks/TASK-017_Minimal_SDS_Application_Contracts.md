# TASK-017 — Minimal SDS Application Contracts

**Projekt:** MSDS Manager  
**Task ID:** TASK-017  
**Sprint:** SPRINT-003 v1.0-approved — „Dodaj SDS”  
**Status:** READY  
**Typ:** Application Contracts / Ports / DTO / Use Cases  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Przygotować minimalne kontrakty warstwy Application potrzebne do workflow:

```text
PDF SDS
   ↓
odczyt kilku pól
   ↓
formularz do weryfikacji
   ↓
późniejsza akceptacja i zapis do Core
```

TASK-017 **nie implementuje jeszcze parsera PDF, Streamlit UI ani zapisu SDS do PostgreSQL**.

Celem jest wyłącznie ustalenie prostych, jednoznacznych granic pomiędzy:

```text
presentation
application
future PDF extractor
future persistence workflow
```

zgodnie z zatwierdzonym SPRINT-003.

---

## 2. Zasada MVP

Kontrakty mają wspierać prosty model:

```text
extract_sds(pdf_path)
→ kilka odczytanych pól
→ użytkownik może je poprawić
→ później zapis
```

Nie projektuj platformy dokumentowej.

Nie twórz:
- parser framework,
- plugin registry,
- confidence score,
- workflow engine,
- trwałych draftów,
- event bus,
- background jobs,
- AI/LLM abstraction,
- OCR abstraction „na przyszłość”.

---

## 3. Źródła obowiązujące

Przed implementacją przeczytaj co najmniej:

- `SPRINT-003 v1.0-approved`,
- aktualny zatwierdzony `CORE-001`,
- `BDR-001`,
- `BDR-003`,
- `BDR-005`,
- `TDR-001`,
- `TDR-002`,
- `TDR-003`,
- `TDR-004`,
- root `AGENTS.md`,
- zaakceptowane raporty TASK-015 i TASK-016.

W razie konfliktu:

```text
STOP
```

Nie zgaduj.

---

## 4. Stan wejściowy

Po SPRINT-002 / TASK-016:

```text
pytest                  100 passed
Alembic head            e0dd7d6468bf
schema                  12 tables
schema drift            none
business data           0
Product Registry        working
Product Administration  working
Usage Locations         working
History                 working
```

TASK-017 nie powinien zmieniać tego stanu schema.

---

## 5. Zakres kontraktów Application

Zaprojektuj minimalne kontrakty potrzebne do dwóch przyszłych etapów:

### A. Przygotowanie danych z PDF

```text
PrepareSdsDraft
```

lub równoważny minimalny use case.

Odpowiedzialność:
- przyjąć referencję/ścieżkę do PDF,
- delegować odczyt do portu ekstrakcji,
- zwrócić DTO danych do formularza,
- nie zapisywać nic do Core,
- nie tworzyć PRODUCT,
- nie tworzyć SDS,
- nie podejmować decyzji biznesowych.

### B. Przyjęcie danych do przyszłego zapisu

Zdefiniuj DTO wejściowe dla późniejszej akceptacji SDS.

TASK-017 może zdefiniować wejściowy kontrakt dla przyszłego use case'u akceptacji, ale **nie implementuje jeszcze transakcji zapisu**.

---

## 6. Port ekstrakcji PDF

Dodaj jeden prosty port, np.:

```text
SdsExtractorPort
```

Minimalna odpowiedzialność:

```text
extract(pdf_path) -> ExtractedSdsData
```

Port:
- nie zna PostgreSQL,
- nie zna Streamlit,
- nie zapisuje danych,
- nie tworzy encji Core,
- nie ustawia statusów,
- nie interpretuje decyzji BHP.

Nie twórz wielu portów dla sekcji 1/2/3/11, jeśli jeden prosty kontrakt wystarcza.

---

## 7. DTO — extracted SDS

Zdefiniuj minimalny DTO wyniku odczytu PDF, obejmujący zatwierdzony zakres Sprintu.

### 7.1. Dane identyfikacyjne

Co najmniej:

```text
product_name
manufacturer_product_code
manufacturer_name
use_description
use_restriction
issue_date
revision
```

Wartości mogą być:

```text
None
```

jeżeli parser nie odczytał pola.

Nie używaj confidence score.

---

## 8. DTO — SAFETY_PROFILE

DTO ma przenosić minimalny zatwierdzony zakres:

```text
product_definition
hazardous_classification_status
clp_classification_text
signal_word
hazard_statements
supplemental_hazard_statements
pbt_status
vpvb_status
carcinogenicity_status
germ_cell_mutagenicity_status
reproductive_toxicity_status
endocrine_section_2_status
endocrine_section_11_status
skin_sensitization_status
respiratory_sensitization_status
```

Nie dodawaj pól spoza zatwierdzonego BDR-005.

---

## 9. DTO — SDS_COMPONENT

Dodaj prosty DTO składnika, np.:

```text
SdsComponentDraft
```

Zakres:

```text
component_name
cas_number
ec_number
reach_registration_number
concentration_text
classification_text
hazard_statements
```

Lista składników może być pusta.

Brak pola:

```text
None
```

Nie zgaduj danych.

---

## 10. DTO — draft do formularza

Złóż dane w jeden prosty DTO, np.:

```text
SdsDraft
```

obejmujący:

```text
source_relative_path
product data
manufacturer data
sds metadata
safety profile draft
components[]
```

To jest **DTO Application**, nie encja domenowa i nie tabela.

Nie zapisuj go do PostgreSQL.

---

## 11. Manual fallback

Kontrakty muszą umożliwiać później ręczne poprawienie dowolnego pola formularza.

Dlatego:
- DTO nie może być immutable w sposób blokujący UI,
- brak automatycznego odczytu nie może być błędem całego procesu,
- `None` jest prawidłowym wynikiem ekstrakcji dla pól opcjonalnych / nieodczytanych.

Nie implementuj automatycznej walidacji biznesowej podczas ekstrakcji.

---

## 12. Walidacja pliku

TASK-017 może zdefiniować minimalny port / use case potrzebny do sprawdzenia:

```text
plik istnieje
plik ma rozszerzenie .pdf
plik znajduje się w SDS_ROOT_PATH
```

Preferuj wykorzystanie istniejącego filesystem/config infrastructure.

Nie kopiuj pliku.
Nie przenoś pliku.
Nie zmieniaj nazwy.

Jeżeli istniejące porty filesystem wystarczają — użyj ich.

Nie twórz nowego storage service.

---

## 13. Język SDS

Kontrakt Application powinien umożliwiać przyszłemu extractorowi / walidatorowi zwrócenie informacji, czy dokument spełnia wymagany język.

Dla obecnego wdrożenia:

```text
PL
```

Nie implementuj tłumaczenia.

Nie dodawaj systemu wielojęzycznego ponad to, co jest potrzebne do istniejącej reguły.

---

## 14. Duplikaty

TASK-017 nie implementuje deduplikacji.

Może zdefiniować minimalny wynik / kontrakt przyszłego sprawdzenia potencjalnego konfliktu, ale tylko jeśli jest to niezbędne dla kolejnego use case'u.

Preferowane:

```text
brak deduplikatora w TASK-017
```

Nie twórz:
- fuzzy matching,
- similarity score,
- hash engine,
- duplicate service.

---

## 15. Future Accept SDS Input DTO

Przygotuj minimalny DTO, który późniejszy TASK-019 będzie mógł przyjąć po ręcznej korekcie formularza.

Przykładowo:

```text
AcceptSdsInput
```

zawierający zatwierdzony przez użytkownika stan:

```text
source_relative_path
product_name
manufacturer_product_code
manufacturer_name
use_description
use_restriction
issue_date
revision
safety_profile
components[]
```

Nie implementuj jeszcze:
- tworzenia Manufacturer,
- tworzenia Product,
- tworzenia SDS,
- CURRENT/ARCHIVED,
- PENDING_APPROVAL,
- transakcji Core.

---

## 16. Błędy Application

Zdefiniuj tylko minimalne błędy, jeśli naprawdę są potrzebne.

Dopuszczalne przykłady:

```text
SdsFileNotFoundError
InvalidSdsFileTypeError
SdsOutsideRootPathError
UnsupportedSdsLanguageError
```

Nie twórz rozbudowanej hierarchii wyjątków.

Jeżeli istniejące wyjątki projektu wystarczają — użyj ich.

---

## 17. Granice architektury

Obowiązuje:

```text
presentation
   ↓
application
   ↓
domain

infrastructure
implements application ports
```

Application może znać:
- DTO,
- port `SdsExtractorPort`,
- filesystem port,
- existing repository ports, jeśli potrzebne do przyszłego contractu.

Application nie może importować:
- Streamlit,
- SQLAlchemy,
- psycopg,
- konkretnych modeli ORM,
- bibliotek PDF.

Port ekstrakcji nie może zależeć od konkretnej biblioteki PDF.

---

## 18. Brak zmian Domain

TASK-017 nie powinien zmieniać:
- encji domenowych,
- statusów,
- enumów,
- reguł Core,
- historii Core.

Jeżeli kontrakt wymaga nowego znaczenia biznesowego:

```text
STOP
```

---

## 19. Brak zmian schema

TASK-017 nie zmienia:
- ORM,
- PostgreSQL schema,
- Alembic migrations.

Oczekiwane po Tasku:

```text
Alembic head = e0dd7d6468bf
tables       = 12
schema drift = none
```

Jeżeli potrzebna byłaby migracja:

```text
STOP
```

---

## 20. Brak nowych zależności

TASK-017 nie wymaga biblioteki PDF.

Nie dodawaj żadnych nowych pakietów.

Jeżeli do samych kontraktów potrzebna byłaby nowa zależność:

```text
STOP
```

---

## 21. Testy

Dodaj testy jednostkowe Application obejmujące co najmniej:

### PrepareSdsDraft
- poprawny wynik z fake/stub extractora,
- `None` dla nieodczytanych pól jest akceptowane,
- pusta lista składników jest akceptowana,
- brak zapisu do DB,
- brak tworzenia PRODUCT/SDS.

### DTO
- poprawne przeniesienie danych identyfikacyjnych,
- poprawne przeniesienie SafetyProfile,
- poprawne przeniesienie components,
- brak confidence score.

### Architecture
- Application nie importuje biblioteki PDF,
- Application nie importuje Streamlit/SQLAlchemy,
- Domain bez zmian infrastrukturalnych.

Nie testuj prawdziwego PDF w TASK-017.

To zakres TASK-018.

---

## 22. Regression

Po implementacji:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- wszystkie testy PASS,
- brak SAWarning.

---

## 23. Alembic validation

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
e0dd7d6468bf (head)
No new upgrade operations detected.
```

---

## 24. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored / nietrackowany,
- brak sekretów,
- brak PDF/MSG w repo,
- brak dumpów/backupów,
- brak nowych zależności,
- brak commit/push bez polecenia.

---

## 25. Poza zakresem

TASK-017 NIE implementuje:

```text
PDF parser implementation
OCR
AI/LLM
Streamlit Add SDS UI
CreateProduct
CreateManufacturer
RegisterSds persistence
CURRENT / ARCHIVED transition
PENDING_APPROVAL transition
SAFETY_PROFILE persistence
SDS_COMPONENT persistence
duplicate detection engine
BHP
REACH
```

---

## 26. STOP CONDITIONS

Zatrzymaj Task jako `PARTIAL / BLOCKED`, jeśli:
- potrzebna jest zmiana Core,
- potrzebny jest nowy status/enum,
- potrzebna jest schema/migracja,
- potrzebna jest nowa biblioteka,
- potrzebna jest implementacja parsera,
- zakres zaczyna realizować TASK-018/019/020,
- potrzebna jest decyzja biznesowa nieobecna w zatwierdzonych źródłach.

---

## 27. Definition of Done

TASK-017 = DONE, gdy:

1. istnieje minimalny `SdsExtractorPort` lub równoważny port,
2. istnieje DTO wyniku ekstrakcji,
3. istnieje DTO SafetyProfile draft,
4. istnieje DTO komponentu SDS,
5. istnieje jeden prosty DTO draftu/formularza,
6. istnieje minimalny `PrepareSdsDraft` lub równoważny use case,
7. brak odczytanego pola może być reprezentowany jako `None`,
8. pusta lista components jest poprawna,
9. ekstrakcja nie zapisuje nic do Core,
10. nie powstaje PRODUCT/SDS podczas przygotowania draftu,
11. istnieje minimalny input DTO dla przyszłej akceptacji,
12. Application nie zna biblioteki PDF,
13. nie ma parser framework,
14. nie ma confidence score,
15. nie ma trwałego draft persistence,
16. nie zmieniono Domain,
17. nie zmieniono ORM/schema,
18. nie utworzono migracji,
19. brak nowych zależności,
20. pełny pytest PASS,
21. brak SAWarning,
22. Alembic pozostaje `e0dd7d6468bf (head)`,
23. brak driftu,
24. TASK-018 nie został rozpoczęty.

---

## 28. Raport

Utwórz:

```text
docs/task_reports/TASK-017_REPORT.md
```

Raport ma zawierać:

1. status,
2. zmienione pliki,
3. port ekstrakcji,
4. DTO extracted data,
5. DTO SafetyProfile,
6. DTO components,
7. DTO draft/form,
8. PrepareSdsDraft,
9. future AcceptSdsInput,
10. obsługę None/manual fallback,
11. walidację ścieżki/pliku,
12. granice architektury,
13. testy unit,
14. pełną regresję,
15. SAWarning,
16. Alembic current/check,
17. potwierdzenie braku zmian Domain/ORM/schema,
18. potwierdzenie braku nowych bibliotek,
19. Git/bezpieczeństwo,
20. odstępstwa/ryzyka.

Raport zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-018.
```

---

## 29. Autoryzacja

Sama obecność pliku TASK-017 nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wykonaj TASK-017.
```

Po zakończeniu zatrzymuje się i nie rozpoczyna TASK-018.
