# TASK-020 — Streamlit „Dodaj SDS”

**Projekt:** MSDS Manager  
**Task ID:** TASK-020  
**Sprint:** SPRINT-003 — „Dodaj SDS”  
**Status:** READY  
**Typ:** Presentation / Streamlit / Integration  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Zaimplementować minimalny ekran Streamlit:

```text
[ Dodaj SDS ]
```

który spina istniejące mechanizmy z TASK-017, TASK-018 i TASK-019 w jeden prosty workflow użytkownika:

```text
wybór PDF
   ↓
PrepareSdsDraft
   ↓
formularz edytowalny
   ↓
użytkownik poprawia dane
   ↓
[ Zapisz / Akceptuj ]
   ↓
AcceptSds
   ↓
PRODUCT = PENDING_APPROVAL
SDS = CURRENT
```

TASK-020 ma być cienką warstwą UI.

Nie przenoś logiki biznesowej do Streamlit.

---

## 2. Zasada nadrzędna

Streamlit:

- prezentuje dane,
- zbiera korekty użytkownika,
- wywołuje use case'y,
- prezentuje wynik lub błąd.

Streamlit nie:

- parsuje PDF samodzielnie,
- wykonuje SQL,
- zna SQLAlchemy,
- wykonuje commit/rollback,
- tworzy PRODUCT bez `AcceptSds`,
- ustala statusy biznesowe,
- interpretuje bezpieczeństwo chemiczne.

---

## 3. Źródła obowiązujące

Przed implementacją przeczytaj co najmniej:

- root `AGENTS.md`,
- SPRINT-003,
- TASK-017 + REPORT,
- TASK-018 + REPORT,
- TASK-019 + REPORT,
- aktualny CORE-001,
- BDR-001,
- BDR-003,
- BDR-005,
- TDR-001,
- TDR-002,
- TDR-003,
- TDR-004.

Jeżeli implementacja wymaga nowej decyzji biznesowej lub zmiany Core:

```text
STOP
```

Nie zgaduj.

---

## 4. Stan wejściowy

Po TASK-019 istnieją:

```text
PrepareSdsDraft
AcceptSds
SdsFileValidator
PdfSdsExtractor
AcceptSdsInput
SdsDraft
SdsSafetyProfileDraft
SdsComponentDraft
TransactionExecutor
```

Backend workflow SDS jest gotowy.

Stan techniczny po TASK-019:

```text
pytest        117 passed
Alembic       e0dd7d6468bf (head)
schema        12 tables
drift         none
```

TASK-020 nie powinien zmieniać schema ani Domain.

---

## 5. Zakres UI

Dodaj prostą funkcję / sekcję Streamlit:

```text
Dodaj SDS
```

Minimalny przebieg:

```text
1. wybór pliku SDS z SDS_ROOT_PATH
2. [ Odczytaj dane ]
3. wyświetlenie formularza
4. ręczna korekta
5. [ Zapisz / Akceptuj ]
6. komunikat sukcesu / błędu
```

Bez wieloetapowego kreatora.

---

## 6. Wybór PDF

Użytkownik ma wybrać istniejący plik PDF znajdujący się w:

```text
SDS_ROOT_PATH
```

Preferuj prosty wybór z listy plików dostępnych w katalogu root lub prosty input ścieżki względnej zgodny z istniejącą architekturą.

Nie implementuj uploadu pliku.

Nie:
- kopiuj,
- przenoś,
- usuwaj,
- zmieniaj nazwy PDF.

UI operuje na `relative_path`.

---

## 7. Odczyt danych

Po kliknięciu:

```text
[ Odczytaj dane ]
```

UI wywołuje:

```text
PrepareSdsDraft
```

Nie wywołuje parsera bezpośrednio.

Wynik:

```text
SdsDraft
```

ma zostać zapisany wyłącznie w stanie sesji Streamlit / formularza.

Nie zapisuj draftu do PostgreSQL.

---

## 8. Manual fallback

Jeżeli parser:
- nie odczyta części pól,
- zwróci `None`,
- nie odczyta producenta,
- zwróci pustą listę składników,

formularz nadal ma być dostępny.

Użytkownik może ręcznie wpisać/poprawić dane.

Brak automatycznego odczytu nie jest powodem do zablokowania workflow, jeśli backendowe reguły akceptacji pozwalają na ręczne uzupełnienie braków.

---

## 9. Formularz — dane produktu i SDS

Formularz ma udostępniać co najmniej pola wynikające z `SdsDraft` / `AcceptSdsInput`:

```text
product_name
manufacturer_product_code
manufacturer_name
use_description
use_restriction
issue_date
revision
source_relative_path
```

`source_relative_path` nie powinien być dowolnie edytowany poza wyborem pliku.

Pola powinny być edytowalne tam, gdzie przewiduje to workflow ręcznej korekty.

---

## 10. Formularz — SAFETY_PROFILE

Wyświetl edytowalne pola zatwierdzone w BDR-005:

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

Dla pól statusowych używaj wyłącznie istniejących wartości:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

Nie dodawaj nowych statusów.

---

## 11. Formularz — SDS_COMPONENTS

Pokaż składniki w prostej edytowalnej formie, np. tabeli/listy.

Zakres jednego składnika:

```text
component_name
cas_number
ec_number
reach_registration_number
concentration_text
classification_text
hazard_statements
```

Nie buduj osobnego modułu zarządzania składnikami.

Użytkownik ma móc:
- poprawić odczytany składnik,
- usunąć błędnie odczytany wiersz z draftu,
- dodać brakujący składnik ręcznie.

Zmiany dotyczą wyłącznie draftu przed akceptacją.

---

## 12. Akceptacja

Po kliknięciu:

```text
[ Zapisz / Akceptuj ]
```

UI:

1. buduje `AcceptSdsInput` z aktualnego formularza,
2. wywołuje `AcceptSds`,
3. nie wykonuje żadnego własnego zapisu do DB.

Po sukcesie pokaż czytelny komunikat, np.:

```text
SDS został zapisany.
Produkt oczekuje na decyzję BHP.
```

Nie ustawiaj statusów bezpośrednio w UI.

---

## 13. Rezygnacja

Dodaj prostą możliwość:

```text
[ Anuluj ]
```

Po anulowaniu:
- draft jest usuwany ze stanu sesji,
- nie powstaje żaden rekord Core,
- użytkownik wraca do stanu początkowego ekranu.

Nie zapisuj anulowanego draftu.

---

## 14. Obsługa błędów

UI ma przechwycić kontrolowane błędy Application i pokazać komunikat użytkownikowi.

Przykładowe kategorie:
- plik nie istnieje,
- plik poza SDS_ROOT_PATH,
- niewłaściwy typ pliku,
- niewłaściwy język,
- brak wymaganych danych,
- niejednoznaczny producent,
- konflikt danych,
- błąd transakcji.

Nie pokazuj:
- stack trace użytkownikowi,
- DATABASE_URL,
- sekretów,
- szczegółów SQL.

Nie ukrywaj błędu jako sukcesu.

---

## 15. Stan sesji

Użyj minimalnego `st.session_state` do przechowania:
- wybranego pliku,
- aktualnego draftu,
- stanu formularza.

Nie twórz trwałego draft persistence.

Po:
- sukcesie zapisu,
- anulowaniu,

wyczyść draft ze stanu sesji.

---

## 16. Istniejący PRODUCT

UI nie musi samodzielnie rozstrzygać, czy PRODUCT już istnieje.

To robi `AcceptSds` zgodnie z Core.

UI może jedynie pokazać dane z formularza.

Nie buduj ekranu merge/dedupe.

---

## 17. Manufacturer

Jeżeli `manufacturer_name` nie został odczytany:
- pole formularza pozostaje puste,
- użytkownik uzupełnia je ręcznie.

UI nie wykonuje fuzzy matching.

Jeżeli backend zwróci niejednoznaczność:
- pokaż błąd,
- nie wybieraj producenta automatycznie.

---

## 18. Brak BHP

TASK-020 kończy się na:

```text
SDS zapisany
PRODUCT = PENDING_APPROVAL
```

Nie dodawaj:
- uploadu decyzji BHP,
- APPROVED / REJECTED,
- ACTIVE / REJECTED produktu,
- dowodów `.msg`,
- formularza decyzji BHP.

To należy do kolejnego etapu.

---

## 19. Brak nowych zależności

TASK-020 powinien korzystać z istniejącego Streamlit.

Nie dodawaj nowych bibliotek UI.

Jeżeli potrzebna byłaby nowa zależność:

```text
STOP
```

---

## 20. Brak zmian schema

TASK-020 nie zmienia:
- Domain,
- ORM,
- Alembic,
- PostgreSQL schema.

Oczekiwane:

```text
Alembic head = e0dd7d6468bf
schema        = 12 tables
drift         = none
```

Jeżeli UI wymaga schema change:

```text
STOP
```

---

## 21. Testy UI

Dodaj testy Streamlit AppTest lub równoważne istniejące testy prezentacji obejmujące co najmniej:

### A. Stan początkowy
- widoczna funkcja `Dodaj SDS`,
- brak draftu,
- brak zapisu Core.

### B. Odczyt PDF
- wybór poprawnego fixture / ścieżki,
- `Odczytaj dane`,
- formularz wypełniony danymi z `PrepareSdsDraft`.

### C. Manual correction
- użytkownik może zmienić pole,
- zmieniona wartość trafia do `AcceptSdsInput`.

### D. Missing fields
- `None` nie blokuje formularza,
- użytkownik może uzupełnić ręcznie.

### E. Components
- odczytana lista jest widoczna,
- możliwa korekta,
- możliwe usunięcie/dodanie draftowego wiersza.

### F. Save
- `AcceptSds` zostaje wywołany raz,
- UI nie wykonuje SQL,
- sukces czyści draft,
- pojawia się komunikat sukcesu.

### G. Error
- kontrolowany błąd Application jest pokazany użytkownikowi,
- draft nie zostaje zapisany do Core,
- brak stack trace / sekretów.

### H. Cancel
- draft zostaje usunięty,
- `AcceptSds` nie jest wywołany.

---

## 22. Test manualny na SDS 30470

Jeżeli środowisko testowe na to pozwala, wykonaj kontrolowany manual/automated smoke test na:

```text
30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

Do testu produkcyjnego workflow plik powinien znajdować się pod skonfigurowanym `SDS_ROOT_PATH` zgodnie z zasadą TASK-019.

Nie kopiuj pliku automatycznie przez aplikację.

Potwierdź:
- odczyt danych,
- możliwość korekty,
- zapis przez `AcceptSds`,
- PRODUCT = PENDING_APPROVAL,
- SDS = CURRENT.

Po teście usuń/rollbackuj wyłącznie fixture techniczne zgodnie z istniejącym mechanizmem testowym.

---

## 23. Regression

Po implementacji uruchom:

```powershell
$env:PATH = "C:\\Program Files\\PostgreSQL\\17\\bin;$env:PATH"
.\\.venv\\Scripts\\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- wszystkie testy PASS,
- brak `SAWarning`.

---

## 24. Alembic validation

Uruchom:

```powershell
.\\.venv\\Scripts\\python.exe -m alembic current
.\\.venv\\Scripts\\python.exe -m alembic check
```

Oczekiwane:

```text
e0dd7d6468bf (head)
No new upgrade operations detected.
```

---

## 25. Architektura

Potwierdź:

```text
Streamlit
   ↓
PrepareSdsDraft / AcceptSds
   ↓
Application
   ↓
Infrastructure
```

Streamlit nie importuje:
- SQLAlchemy ORM models,
- repositories infrastrukturalnych bezpośrednio,
- psycopg,
- pypdf jako parsera bezpośrednio.

Kompozycja zależności może używać istniejącego composition root.

---

## 26. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored / nietrackowany,
- brak sekretów,
- brak nowych PDF/MSG,
- brak dumpów/backupów,
- brak commit/push bez jawnego polecenia.

---

## 27. Poza zakresem

NIE implementuj:

```text
BHP workflow
Decision Evidence
OCR
AI/LLM
confidence score
parser framework
REACH
barcode
periodic review
Excel import
upload service
storage service
generic audit
new history framework
new schema
new dependencies
```

---

## 28. STOP CONDITIONS

Zatrzymaj TASK-020 jako `PARTIAL / BLOCKED`, jeśli:
- potrzebna jest zmiana Core,
- potrzebna jest zmiana schema/migracja,
- potrzebna jest nowa biblioteka,
- istniejące `PrepareSdsDraft` / `AcceptSds` są niewystarczające i wymagają decyzji biznesowej,
- UI wymaga nowego statusu lub reguły,
- wymagane byłoby rozpoczęcie BHP,
- problemu nie da się rozwiązać bez przeniesienia logiki biznesowej do UI.

---

## 29. Definition of Done

TASK-020 = DONE, gdy:

1. istnieje widok `Dodaj SDS`,
2. użytkownik może wybrać PDF z SDS_ROOT_PATH,
3. `Odczytaj dane` wywołuje `PrepareSdsDraft`,
4. formularz jest edytowalny,
5. `None` może być ręcznie uzupełnione,
6. SafetyProfile jest dostępny do korekty,
7. Components są dostępne do korekty,
8. `Zapisz/Akceptuj` wywołuje `AcceptSds`,
9. UI nie zapisuje bezpośrednio do DB,
10. anulowanie nie tworzy Core,
11. sukces czyści draft,
12. błędy Application są prezentowane czytelnie,
13. PRODUCT po sukcesie = PENDING_APPROVAL,
14. SDS po sukcesie = CURRENT,
15. brak BHP,
16. brak nowych zależności,
17. brak zmian Domain/ORM/schema,
18. testy UI PASS,
19. pełna regresja PASS,
20. brak SAWarning,
21. Alembic nadal `e0dd7d6468bf (head)`,
22. brak driftu,
23. TASK-021 nie został rozpoczęty.

---

## 30. Raport

Utwórz:

```text
docs/task_reports/TASK-020_REPORT.md
```

Raport ma zawierać:

1. status,
2. zmienione pliki,
3. umiejscowienie widoku `Dodaj SDS`,
4. sposób wyboru PDF,
5. integrację `PrepareSdsDraft`,
6. stan sesji/draft,
7. formularz danych produktu/SDS,
8. SafetyProfile,
9. Components,
10. manual fallback,
11. integrację `AcceptSds`,
12. anulowanie,
13. obsługę błędów,
14. testy UI,
15. smoke/E2E SDS 30470, jeśli wykonany,
16. pełny pytest,
17. SAWarning,
18. Alembic current/check,
19. architekturę,
20. Git/bezpieczeństwo,
21. odstępstwa i ryzyka.

Zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-021.
```

---

## 31. Autoryzacja

Sama obecność pliku TASK-020 nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po poleceniu:

```text
Wykonaj TASK-020.
```

Po zakończeniu zatrzymuje się i nie rozpoczyna TASK-021.
