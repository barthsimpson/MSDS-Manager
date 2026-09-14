# TASK-018 — Minimal SDS PDF Extraction

**Projekt:** MSDS Manager  
**Task ID:** TASK-018  
**Sprint:** SPRINT-003 v1.0-approved — „Dodaj SDS”  
**Status:** READY  
**Typ:** Infrastructure Adapter / PDF Extraction / Unit Tests  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Zaimplementować **najprostszy możliwy adapter odczytu tekstowego PDF SDS**, zgodny z kontraktami Application przygotowanymi w TASK-017.

TASK-018 ma:

```text
PDF tekstowy
   ↓
odczyt tekstu
   ↓
próba odczytu kilku zatwierdzonych pól
   ↓
ExtractedSdsData
```

Jeżeli jakiegoś pola nie uda się jednoznacznie odczytać:

```text
None
```

To jest prawidłowy wynik MVP.

Nie budujemy inteligentnego parsera dokumentów.

---

## 2. Zasada nadrzędna MVP

Automatyczny odczyt ma wyłącznie:

> **oszczędzić użytkownikowi ręcznego przepisywania kilku pól z SDS.**

Nie jest celem TASK-018:
- pełne rozumienie dokumentu,
- analiza semantyczna całego SDS,
- OCR,
- AI/LLM,
- confidence scoring,
- klasyfikator dokumentów,
- parser framework,
- obsługa wszystkich możliwych layoutów producentów.

Jeżeli parser nie rozpozna pola:
- zwraca `None`,
- UI w TASK-020 pozwoli wpisać wartość ręcznie.

---

## 3. Źródła obowiązujące

Przed implementacją przeczytaj co najmniej:

- `SPRINT-003` — zatwierdzony przez użytkownika zakres Sprintu,
- `TASK-017` i `TASK-017_REPORT`,
- aktualny `CORE-001`,
- `BDR-001`,
- `BDR-003`,
- `BDR-005`,
- `TDR-001`,
- `TDR-002`,
- `TDR-003`,
- root `AGENTS.md`.

W razie konfliktu lub potrzeby nowej interpretacji biznesowej:

```text
STOP
```

Nie zgaduj.

---

## 4. Stan wejściowy

Po TASK-017:

```text
pytest                  104 passed
Alembic head            e0dd7d6468bf
schema                  12 tables
schema drift            none
business data           0
```

Dostępne kontrakty Application obejmują m.in.:

```text
SdsExtractorPort
SdsFileValidatorPort
ExtractedSdsData
SdsSafetyProfileDraft
SdsComponentDraft
SdsDraft
AcceptSdsInput
PrepareSdsDraft
```

TASK-018 ma zaimplementować adapter do `SdsExtractorPort`.

---

## 5. Zakres implementacji

Dodaj minimalny adapter infrastrukturalny, np.:

```text
app/infrastructure/filesystem/pdf_sds_extractor.py
```

lub równoważny zgodny z istniejącą strukturą repozytorium.

Adapter:

```text
implements SdsExtractorPort
```

i zwraca:

```text
ExtractedSdsData
```

Nie modyfikuj kontraktu `SdsExtractorPort`, chyba że istnieje techniczny blocker wymagający STOP.

---

## 6. Biblioteka PDF

Najpierw sprawdź istniejące zależności projektu.

Jeżeli w aktualnym środowisku jest już dostępna biblioteka umożliwiająca prosty odczyt tekstu z PDF, użyj jej.

Jeżeli **nie ma żadnej odpowiedniej biblioteki PDF**, nie instaluj nowej samodzielnie.

W takim przypadku:

```text
STOP / BLOCKED
```

i raportuj:
- jaka minimalna biblioteka jest potrzebna,
- dlaczego,
- do czego dokładnie będzie użyta.

Nie proponuj ciężkiego stosu OCR/AI.

Preferowana klasa rozwiązania:

```text
prosty reader PDF → text
```

---

## 7. Dokument testowy

Do walidacji użyj zatwierdzonego/przekazanego przykładowego SDS:

```text
30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

To jest dokument źródłowy testowy.

Nie modyfikuj go.
Nie kopiuj go do repo, jeśli obecne zasady repozytorium na to nie pozwalają.
Nie zapisuj jego treści w kodzie produkcyjnym.

Test może użyć kontrolowanej ścieżki fixture zgodnie z istniejącą organizacją testów.

---

## 8. Minimalny zakres ekstrakcji — dane identyfikacyjne

Parser ma próbować odczytać:

```text
product_name
manufacturer_product_code
manufacturer_name
use_description
use_restriction
issue_date
revision
```

Dla przykładowego SDS oczekiwane źródła znajdują się głównie w Sekcji 1 oraz nagłówku/stopce dokumentu.

Nie twórz heurystyk opartych wyłącznie na nazwie pliku, jeśli dane są dostępne w treści PDF.

Nazwa pliku może być pomocnicza tylko wtedy, gdy istniejące źródła to dopuszczają.

---

## 9. Manufacturer — ostrożność

W SDS może występować podmiot opisany jako dostawca karty.

Nie zakładaj automatycznie, że każda nazwa firmy w Sekcji 1 jest `MANUFACTURER`, jeśli dokument nie wskazuje tego jednoznacznie w zgodzie z zatwierdzonym modelem.

Jeżeli nie da się jednoznacznie rozstrzygnąć:

```text
manufacturer_name = None
```

Manual fallback jest prawidłowy.

Nie zgaduj producenta na podstawie domeny e-mail lub nazwy pliku.

---

## 10. Minimalny SAFETY_PROFILE — Sekcja 2

Parser ma próbować odczytać:

```text
product_definition
hazardous_classification_status
clp_classification_text
signal_word
hazard_statements
supplemental_hazard_statements
pbt_status
vpvb_status
endocrine_section_2_status
```

Źródłem jest Sekcja 2.

Nie interpretuj informacji o składnikach z Sekcji 3 jako klasyfikacji produktu.

---

## 11. Minimalny SAFETY_PROFILE — Sekcja 11

Parser ma próbować odczytać:

```text
carcinogenicity_status
germ_cell_mutagenicity_status
reproductive_toxicity_status
endocrine_section_11_status
skin_sensitization_status
respiratory_sensitization_status
```

Jeżeli Sekcja 11:
- nie zawiera jednoznacznej informacji,
- używa sformułowania „brak danych”,
- nie pozwala bez interpretacji wyznaczyć statusu,

zwróć:

```text
NO_DATA
```

zgodnie z zatwierdzonym modelem statusów bezpieczeństwa.

Nie przekształcaj braku danych w `NO`.

---

## 12. Statusy bezpieczeństwa

Używaj wyłącznie zatwierdzonych wartości istniejącego enuma:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

Nie dodawaj nowych statusów.

Nie twórz:
- UNKNOWN,
- PROBABLY,
- MAYBE,
- UNCERTAIN,
- LOW_CONFIDENCE.

---

## 13. Sekcja 3 — składniki

Parser ma próbować odczytać listę składników z Sekcji 3.

Dla każdego składnika, jeśli dostępne:

```text
component_name
cas_number
ec_number
reach_registration_number
concentration_text
classification_text
hazard_statements
```

Nie uzupełniaj danych spoza SDS.

Nie:
- normalizuj nazw chemicznych,
- sprawdzaj CAS w Internecie,
- poprawiaj numerów REACH,
- wyliczaj stężeń,
- interpretuj toksyczności.

---

## 14. Hazard statements

Kody H mają być zachowane jako kody, np.:

```text
H302
H315
H319
```

Nie twórz w TASK-018 własnej bazy opisów H.

Jeżeli tekst dokumentu zawiera pełny opis, ale nie daje się bezpiecznie wyodrębnić kodu:

```text
nie zgaduj kodu
```

---

## 15. Supplemental hazard statements

Dla danych uzupełniających z Sekcji 2 parser może zapisać tekst w zatwierdzonym polu:

```text
supplemental_hazard_statements
```

Nie twórz nowych struktur dla każdego rodzaju informacji dodatkowej.

---

## 16. Język dokumentu

Dla obecnego wdrożenia wymagany jest:

```text
PL
```

TASK-018 może zastosować prostą kontrolę języka tylko wtedy, gdy da się ją wykonać jednoznacznie i bez dodatkowego frameworka.

Dopuszczalne jest minimalne podejście oparte na obecności charakterystycznych nagłówków SDS, np.:

```text
KARTA CHARAKTERYSTYKI
SEKCJA 1
SEKCJA 2
```

Jeżeli nie można wiarygodnie określić języka prostym sposobem, adapter może zwrócić brak/neutralną informację zgodnie z kontraktem TASK-017, a pełna decyzja wejściowa może zostać dopięta później.

Nie implementuj:
- biblioteki language detection,
- tłumaczenia,
- AI language classifier.

---

## 17. Parser ma być odporny na brak pól

Brak:
- rewizji,
- daty,
- producenta,
- pojedynczych pól profilu,
- składników,

nie może powodować wyjątku całego parsera, jeśli sam PDF jest czytelny.

Zwróć `None`, pustą listę lub `NO_DATA` zgodnie z istniejącym kontraktem.

---

## 18. Kiedy parser może zgłosić błąd

Dopuszczalne są błędy techniczne dla przypadków:

```text
plik nie istnieje
plik nie jest PDF
plik nie może zostać otwarty
PDF jest uszkodzony
PDF nie zawiera możliwego do odczytu tekstu
```

Dla skanu bez warstwy tekstowej:

```text
brak OCR
```

Zwróć kontrolowany błąd / wynik wskazujący, że wymagany będzie manual fallback.

Nie uruchamiaj OCR.

---

## 19. Brak zapisu do Core

TASK-018:

```text
NIE zapisuje do PostgreSQL
NIE tworzy PRODUCT
NIE tworzy MANUFACTURER
NIE tworzy SDS
NIE tworzy SAFETY_PROFILE
NIE tworzy SDS_COMPONENT
NIE zmienia statusu PRODUCT
NIE ustawia CURRENT
```

Adapter tylko odczytuje PDF i zwraca DTO Application.

---

## 20. Brak zmian Domain / schema

TASK-018 nie powinien zmieniać:

- Domain,
- enumów,
- ORM,
- Alembic,
- PostgreSQL schema.

Oczekiwane:

```text
Alembic head = e0dd7d6468bf
tables       = 12
schema drift = none
```

Jeżeli potrzebna byłaby zmiana Domain/schema:

```text
STOP
```

---

## 21. Testy jednostkowe parsera

Dodaj testy obejmujące co najmniej:

### A. Prosty PDF tekstowy
- tekst zostaje odczytany,
- `ExtractedSdsData` jest zwracane.

### B. Brak pola
- brak pola → `None`,
- parser nie zgaduje.

### C. Safety status
- `NO_DATA` pozostaje `NO_DATA`,
- brak danych nie staje się `NO`.

### D. Components
- lista składników może być pusta,
- częściowo odczytany składnik może zawierać `None`.

### E. Skan / brak tekstu
- kontrolowany wynik/błąd,
- brak OCR.

---

## 22. Test na rzeczywistym SDS 30470

Dodaj kontrolowany test integracyjny ekstraktora na dostępnym przykładowym SDS:

```text
30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

Test ma potwierdzić co najmniej, jeśli tekst PDF pozwala:

```text
product_name = IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO
manufacturer_product_code = 30470
use_description = Farba lub inna podobna substancja.
use_restriction = Jedynie do stosowania przemysłowego.
revision = 10.02
```

oraz sensowny odczyt wybranych danych Sekcji 2 i co najmniej jednego składnika Sekcji 3.

Nie wymagaj od parsera 100% wszystkich pól z całego dokumentu.

---

## 23. Nie testuj jakości „AI”

Nie twórz metryk:
- accuracy,
- confidence,
- precision/recall,
- model score.

Acceptance TASK-018 polega na tym, że prosty parser:
- odczytuje oczywiste pola,
- nie zgaduje,
- pozwala na manual fallback.

---

## 24. Regression

Po implementacji:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Wymagane:
- wszystkie testy PASS,
- brak SAWarning.

---

## 25. Alembic validation

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
- brak przypadkowo dodanych PDF/MSG,
- brak dumpów/backupów,
- brak commit/push bez polecenia.

---

## 27. Poza zakresem

TASK-018 NIE implementuje:

```text
OCR
AI/LLM
confidence score
parser framework
plugin architecture
background jobs
Streamlit UI
AcceptSds persistence
CreateProduct
CreateManufacturer
RegisterSds
CURRENT/ARCHIVED transition
PENDING_APPROVAL transition
BHP
REACH
Internet lookup
chemical normalization
CAS validation service
```

---

## 28. STOP CONDITIONS

Zatrzymaj Task jako `PARTIAL / BLOCKED`, jeśli:

- brak jest jakiejkolwiek biblioteki do odczytu PDF i potrzebna jest nowa zależność,
- konieczna byłaby zmiana Domain,
- konieczna byłaby zmiana kontraktów TASK-017 poza minimalną korektą techniczną,
- potrzebna jest schema/migracja,
- potrzebny jest OCR,
- implementacja zaczyna wymagać AI/LLM,
- parser wymaga niezatwierdzonej interpretacji bezpieczeństwa,
- zakres zaczyna realizować TASK-019 lub TASK-020.

---

## 29. Definition of Done

TASK-018 = DONE, gdy:

1. istnieje prosty adapter implementujący `SdsExtractorPort`,
2. adapter odczytuje tekst z PDF,
3. parser próbuje odczytać zatwierdzone pola identyfikacyjne,
4. parser próbuje odczytać minimalny SAFETY_PROFILE,
5. parser próbuje odczytać SDS_COMPONENTS,
6. brak pola → `None` / `NO_DATA`,
7. parser nie zgaduje danych,
8. parser nie używa OCR,
9. parser nie używa AI/LLM,
10. parser nie używa confidence score,
11. parser nie zapisuje do Core,
12. parser nie zmienia Domain,
13. parser nie zmienia schema,
14. nie powstaje migracja,
15. test rzeczywistego SDS 30470 przechodzi w minimalnym zatwierdzonym zakresie,
16. pełny pytest PASS,
17. brak SAWarning,
18. Alembic nadal `e0dd7d6468bf (head)`,
19. brak driftu,
20. TASK-019 nie został rozpoczęty.

---

## 30. Raport

Utwórz:

```text
docs/task_reports/TASK-018_REPORT.md
```

Raport ma zawierać:

1. status,
2. użyty mechanizm/bibliotekę PDF,
3. informację, czy była już zależnością projektu,
4. zmienione pliki,
5. implementację `SdsExtractorPort`,
6. sposób odczytu tekstu,
7. odczytywane pola identyfikacyjne,
8. odczytywane pola SafetyProfile,
9. odczyt SDS_COMPONENTS,
10. zachowanie dla brakujących pól,
11. zachowanie dla PDF bez warstwy tekstowej,
12. wynik testu SDS 30470,
13. testy unit/integration,
14. pełny pytest,
15. SAWarning,
16. Alembic current/check,
17. brak zmian Domain/ORM/schema,
18. Git/bezpieczeństwo,
19. odstępstwa,
20. ryzyka.

Raport zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-019.
```

---

## 31. Autoryzacja

Sama obecność pliku TASK-018 nie stanowi zgody na wykonanie.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wykonaj TASK-018.
```

Po zakończeniu zatrzymuje się i nie rozpoczyna TASK-019.
