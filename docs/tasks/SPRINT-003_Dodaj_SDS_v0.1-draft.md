# SPRINT-003 — Dodaj SDS

**Projekt:** MSDS Manager  
**Sprint ID:** SPRINT-003  
**Wersja:** 0.1-draft  
**Status:** Draft — do zatwierdzenia  
**Etap Roadmapy:** R4 — SDS  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca Tasków:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  

---

## 1. Cel Sprintu

Zbudować pierwszy kompletny workflow użytkownika:

```text
[ Dodaj SDS ]
      ↓
wskaż PDF
      ↓
odczytaj kilka potrzebnych pól
      ↓
pokaż dane w formularzu
      ↓
użytkownik sprawdza / poprawia
      ↓
[ ZAPISZ ]
      ↓
PRODUCT + MANUFACTURER + SDS
+ SAFETY_PROFILE
+ SDS_COMPONENTS
      ↓
PRODUCT = PENDING_APPROVAL
SDS = CURRENT
```

Sprint ma **automatyzować ręczne przepisywanie kilku danych z SDS**.

Nie budujemy platformy do inteligentnego przetwarzania dokumentów.

---

## 2. Zasada MVP

Automatyczny odczyt PDF jest pomocą dla użytkownika, nie osobnym subsystemem.

Wariant bazowy biznesowo pozostaje prosty:

```text
PDF
 ↓
formularz
 ↓
ręczne wpisanie / poprawienie danych
 ↓
zapis
```

Automatyzacja ma jedynie wstępnie uzupełnić formularz.

Jeżeli pole:
- nie zostanie odczytane,
- zostanie odczytane niepewnie,
- zostanie odczytane błędnie,

użytkownik może je ręcznie wpisać lub poprawić przed zapisem.

Nie budujemy:
- confidence score,
- trwałych draftów,
- kolejki przetwarzania,
- workflow engine,
- parser framework,
- mechanizmu uczenia,
- AI decision engine.

---

## 3. Obowiązujące źródła

Sprint realizuje istniejące zatwierdzone decyzje, w szczególności:

- CORE-001 — aktualna zatwierdzona wersja,
- BDR-001 — tożsamość PRODUCT,
- BDR-003 — SDS, aktualność i wersjonowanie,
- BDR-005 — SAFETY_PROFILE i zakres danych z SDS,
- TDR-001 — stos technologiczny,
- TDR-002 — `SDS_ROOT_PATH`,
- TDR-003 — granice warstw,
- SPRINT-002 v1.2-approved,
- root `AGENTS.md`.

Jeżeli implementacja ujawni brak decyzji biznesowej:

```text
STOP
```

Nie zgaduj.

---

## 4. Zakres biznesowy

Sprint ma umożliwić użytkownikowi:

1. otwarcie funkcji `Dodaj SDS`,
2. wskazanie pliku PDF SDS,
3. walidację, że plik jest dostępny i jest PDF,
4. odczyt wybranych pól,
5. prezentację danych w edytowalnym formularzu,
6. ręczną korektę danych,
7. akceptację albo rezygnację,
8. zapis do Core dopiero po `ZAPISZ / AKCEPTUJ`,
9. utworzenie nowego PRODUCT, jeśli dokument dotyczy nowego produktu,
10. użycie istniejącego PRODUCT, jeśli dokument dotyczy już istniejącego produktu,
11. utworzenie lub użycie MANUFACTURER,
12. utworzenie SDS,
13. zapis SAFETY_PROFILE,
14. zapis SDS_COMPONENTS w zatwierdzonym minimalnym zakresie,
15. ustawienie nowego SDS jako CURRENT,
16. archiwizację poprzedniego CURRENT dla tego PRODUCT,
17. ustawienie PRODUCT = PENDING_APPROVAL po zatwierdzeniu nowego CURRENT SDS.

---

## 5. Minimalne dane odczytywane z SDS

### 5.1. Dane identyfikacyjne

Automatyczny odczyt ma próbować odczytać co najmniej:

```text
product_name
manufacturer_product_code
manufacturer_name
use_description
use_restriction
issue_date
revision
```

Jeżeli pole nie zostanie odczytane — formularz pozostawia możliwość ręcznego wpisania.

---

## 6. Minimalny SAFETY_PROFILE

Zakres pozostaje zgodny z BDR-005.

Automatyczny odczyt dotyczy wybranych informacji z Sekcji 2 i 11, w szczególności:

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

Nie odczytujemy strukturalnie całej Sekcji 11.

---

## 7. SDS_COMPONENTS

Z Sekcji 3 odczytujemy wyłącznie zatwierdzony minimalny zakres:

```text
component_name
cas_number
ec_number
reach_registration_number
concentration_text
classification_text
hazard_statements
```

Jeżeli dane są niepełne:

```text
NULL / brak wartości
```

Nie zgadujemy.

Nie interpretujemy zagrożenia składnika jako klasyfikacji całego produktu.

---

## 8. Język SDS

Dla obecnego wdrożenia:

```text
required_sds_language = PL
```

Jeżeli dokument nie jest w wymaganym języku:
- nie zapisujemy PRODUCT,
- nie zapisujemy SDS,
- nie zapisujemy SAFETY_PROFILE,
- nie zapisujemy SDS_COMPONENTS.

Nie tłumaczymy dokumentu automatycznie w celu przyjęcia go do Core.

---

## 9. Plik SDS

Plik SDS pozostaje dokumentem źródłowym poza PostgreSQL.

Aplikacja:
- odczytuje plik,
- zapisuje metadane,
- zapisuje `relative_path`,
- nie nadpisuje PDF,
- nie usuwa PDF,
- nie zmienia nazwy PDF,
- nie przenosi PDF.

Dla MVP użytkownik wskazuje dokument znajdujący się w `SDS_ROOT_PATH`.

Nie budujemy repozytorium uploadów ani storage service.

---

## 10. Draft

W Sprint 3 słowo `DRAFT` oznacza wyłącznie:

> dane odczytane z PDF i pokazane użytkownikowi w formularzu przed zapisem.

Draft:
- nie jest zapisywany do PostgreSQL,
- nie ma własnej tabeli,
- nie ma statusów,
- nie ma historii,
- nie jest osobnym obiektem Core.

Po anulowaniu formularza:

```text
brak zmian w Core
```

---

## 11. Akceptacja

Dopiero jawne:

```text
ZAPISZ / AKCEPTUJ
```

powoduje zapis do Core.

Operacja ma być atomowa.

Dla nowego produktu:

```text
MANUFACTURER (jeśli nowy)
PRODUCT
PRODUCT_HISTORY initial snapshot — jeśli wymagany przez istniejący mechanizm historii
SDS CURRENT
SAFETY_PROFILE
SDS_COMPONENTS
PRODUCT = PENDING_APPROVAL
```

Dla istniejącego produktu z nowym SDS:

```text
poprzedni SDS CURRENT → ARCHIVED
nowy SDS → CURRENT
nowy SAFETY_PROFILE
nowe SDS_COMPONENTS
PRODUCT → PENDING_APPROVAL
```

Wszystko w jednej transakcji.

Błąd dowolnego elementu:

```text
ROLLBACK całości
```

---

## 12. Identyfikacja PRODUCT

Obowiązuje zatwierdzona tożsamość:

```text
product_name
manufacturer_product_code
manufacturer_id
```

Nowa nazwa, nowy kod/numer lub inny producent = nowy PRODUCT.

System może pokazać użytkownikowi potencjalne dopasowanie, ale nie może samodzielnie scalać produktów.

---

## 13. MANUFACTURER

Producent jest osobną encją.

Przy akceptacji:
- jeśli producent już istnieje — użyj istniejącego,
- jeśli nie istnieje — utwórz nowy.

Nie buduj rozbudowanego systemu deduplikacji producentów.

W razie niejednoznaczności użytkownik dokonuje wyboru.

---

## 14. Duplikaty SDS

Nie budujemy zaawansowanego deduplikatora.

Jeżeli system wykryje oczywisty konflikt / potencjalny duplikat:
- pokaż użytkownikowi komunikat,
- nie scalaj automatycznie,
- nie wybieraj „lepszej” wersji,
- nie używaj fuzzy matching / similarity score / AI.

Użytkownik podejmuje decyzję.

---

## 15. CURRENT / ARCHIVED

Jeden PRODUCT może posiadać maksymalnie jeden:

```text
SDS = CURRENT
```

Zatwierdzenie nowego SDS dla istniejącego PRODUCT:

```text
old CURRENT → ARCHIVED
new SDS     → CURRENT
```

Operacja jest częścią jednej transakcji akceptacji.

---

## 16. Dostępność pliku

Po zapisaniu SDS system ma umieć rozróżnić:

```text
AVAILABLE
MISSING
```

Brak pliku po rejestracji:
- nie usuwa SDS,
- nie usuwa historii,
- nie zmienia automatycznie CURRENT/ARCHIVED.

---

## 17. UI Sprintu 3

Dodaj w Streamlit prostą funkcję:

```text
[ Dodaj SDS ]
```

Minimalny przebieg UI:

```text
1. wybierz PDF z SDS_ROOT_PATH
2. [ Odczytaj dane ]
3. formularz
4. użytkownik poprawia pola
5. [ Zapisz ]
```

Nie buduj:
- dashboardu,
- kreatora wieloetapowego,
- zaawansowanego wizard UI,
- workflow engine,
- background jobs.

Prosty ekran jest wystarczający.

---

## 18. Parser — zasada techniczna

Parser ma być minimalną funkcją / adapterem:

```text
extract_sds(pdf_path)
→ extracted data
```

Ma:
- odczytać tyle, ile potrafi,
- zwrócić brak danych dla nierozpoznanych pól,
- nie podejmować decyzji biznesowych,
- nie zapisywać do PostgreSQL,
- nie tworzyć PRODUCT,
- nie ustawiać statusów.

Nie buduj platformy parserów.

---

## 19. Technologia odczytu PDF

Nie tworzymy osobnego TDR tylko po to, aby wybrać parser.

Codex ma użyć **najprostszego rozwiązania zgodnego z istniejącymi zależnościami projektu**, jeśli takie rozwiązanie już jest dostępne.

Jeżeli do odczytu tekstowego PDF konieczna jest nowa biblioteka:
- STOP,
- zgłoś minimalną potrzebną bibliotekę i uzasadnienie,
- nie instaluj jej samodzielnie bez zgody.

OCR nie jest wymaganiem Sprintu 3.

Jeżeli PDF jest skanem i tekstu nie da się odczytać:

```text
formularz ręczny
```

---

## 20. Manual fallback

Automatyczna ekstrakcja nie może blokować użytkownika.

Jeżeli parser zwróci mało danych:

```text
użytkownik uzupełnia ręcznie
```

To jest prawidłowy scenariusz MVP.

Nie próbuj „ratować” każdego dokumentu kolejną technologią.

---

## 21. BHP — poza Sprintem

SPRINT-003 kończy się na:

```text
PRODUCT = PENDING_APPROVAL
SDS = CURRENT
```

Nie implementujemy:
- decyzji BHP,
- dowodu BHP,
- APPROVED / REJECTED workflow,
- ACTIVE / REJECTED produktu po decyzji.

To należy do R5.

---

## 22. Historia

SPRINT-003 korzysta z istniejącego mechanizmu historii.

Nie tworzymy nowego history framework.

Jeżeli zaakceptowany workflow zmienia historyzowane pola PRODUCT, zapis ma pozostać zgodny z TDR-004.

Historia SDS wynika przede wszystkim z kolejnych rekordów SDS i `CURRENT / ARCHIVED`.

---

## 23. Poza zakresem

Nie implementujemy:

- AI/LLM do interpretacji SDS,
- OCR jako wymogu,
- confidence score,
- trwałych draftów,
- workflow engine,
- event sourcing,
- queue/background jobs,
- vector database,
- embeddings,
- REACH,
- BHP,
- automatycznej oceny zgodności,
- rozbudowanej deduplikacji,
- storage service,
- upload service,
- importu Excel,
- kodów kreskowych,
- przeglądów okresowych.

---

## 24. Backlog Sprintu 3

### TASK-017 — Minimal SDS Application Contracts

Zakres:
- port/adaptacja odczytu PDF,
- DTO wyniku ekstrakcji,
- use case przygotowania danych do formularza,
- minimalne kontrakty rejestracji SDS,
- bez zapisu Core podczas odczytu.

Nie implementować parser framework.

---

### TASK-018 — Minimal SDS PDF Extraction

Zakres:
- odczyt tekstowego PDF,
- ekstrakcja kilku zatwierdzonych pól,
- odczyt minimalnego SAFETY_PROFILE,
- odczyt SDS_COMPONENTS,
- brak danych → NULL,
- testy na rzeczywistych przykładowych SDS.

Jeżeli potrzebna jest nowa biblioteka → STOP.

OCR poza zakresem.

---

### TASK-019 — Accept SDS / Core Transaction

Zakres:
- walidacja formularza,
- dopasowanie / utworzenie MANUFACTURER,
- rozpoznanie istniejącego / nowego PRODUCT zgodnie z Core,
- utworzenie PRODUCT, jeśli wymagane,
- utworzenie SDS,
- CURRENT / ARCHIVED,
- SAFETY_PROFILE,
- SDS_COMPONENTS,
- PRODUCT = PENDING_APPROVAL,
- jedna transakcja,
- rollback,
- testy PostgreSQL.

---

### TASK-020 — Streamlit „Dodaj SDS”

Zakres:
- wybór PDF z `SDS_ROOT_PATH`,
- `Odczytaj dane`,
- edytowalny formularz,
- manual fallback,
- `Zapisz`,
- komunikaty błędów,
- brak zapisu przed akceptacją.

Bez BHP.

---

### TASK-021 — Sprint 3 End-to-End Acceptance

Scenariusz:
1. wskaż kontrolowany PDF SDS,
2. odczytaj dane,
3. popraw / uzupełnij formularz,
4. zaakceptuj,
5. potwierdź PRODUCT,
6. potwierdź MANUFACTURER,
7. potwierdź SDS CURRENT,
8. potwierdź SAFETY_PROFILE,
9. potwierdź SDS_COMPONENTS,
10. potwierdź PRODUCT = PENDING_APPROVAL,
11. potwierdź brak częściowego zapisu przy błędzie,
12. potwierdź PostgreSQL,
13. cleanup fixture,
14. pełna regresja.

---

## 25. Definition of Done Sprintu 3

Sprint jest gotowy do closure, gdy:

1. użytkownik ma funkcję `Dodaj SDS`,
2. może wskazać PDF z `SDS_ROOT_PATH`,
3. system próbuje odczytać zatwierdzone pola,
4. brak automatycznego odczytu nie blokuje formularza ręcznego,
5. użytkownik może poprawić dane,
6. przed `Zapisz` nie powstają rekordy Core,
7. po `Zapisz` powstaje spójny zestaw danych,
8. nowy PRODUCT powstaje tylko zgodnie z Core,
9. istniejący PRODUCT może otrzymać nowy SDS,
10. producent jest poprawnie powiązany,
11. SDS jest CURRENT,
12. poprzedni CURRENT przechodzi na ARCHIVED,
13. SAFETY_PROFILE jest zapisany,
14. SDS_COMPONENTS są zapisane w minimalnym zakresie,
15. PRODUCT po nowym SDS = PENDING_APPROVAL,
16. operacja jest atomowa,
17. rollback działa,
18. PDF nie jest modyfikowany,
19. brak parser framework / AI platform,
20. brak BHP,
21. pełne testy przechodzą,
22. E2E Sprintu 3 przechodzi.

---

## 26. Kryterium sukcesu biznesowego

Sprint 3 ma zakończyć się sytuacją:

> **Użytkownik bierze kartę SDS, wskazuje PDF, system przepisuje za niego część danych, użytkownik je sprawdza i zapisuje produkt wraz z kartą.**

Jeżeli automatyczny odczyt nie zadziała:

> **Użytkownik może po prostu wpisać dane ręcznie i nadal zakończyć proces.**

To jest wystarczające dla MVP.

---

## 27. Ochrona przed przekombinowaniem

Codex nie może samodzielnie:
- projektować „inteligentnego systemu dokumentowego”,
- rozszerzać ekstrakcji poza zatwierdzone pola,
- dodawać AI,
- dodawać OCR bez decyzji,
- dodawać confidence scoring,
- tworzyć trwałego draft persistence,
- tworzyć parser registry/plugin framework,
- dodawać background workers,
- rozdzielać prostego workflow na nowe subsystemy,
- wprowadzać nowych usług „na przyszłość”.

Jeżeli rozwiązanie zaczyna wymagać takiej architektury:

```text
STOP
```

i wróć do manual fallback.

---

## 28. Stan wejściowy Sprintu

SPRINT-002:

```text
CLOSED
```

Stan techniczny po TASK-016:

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

---

## 29. Stan końcowy oczekiwany

```text
SPRINT-002
Product Registry
       ✅
        ↓
SPRINT-003
Dodaj SDS
        ↓
PDF
        ↓
minimal extraction
        ↓
editable form
        ↓
user acceptance
        ↓
PRODUCT + SDS + SAFETY DATA
        ↓
PRODUCT = PENDING_APPROVAL
        ↓
READY FOR R5 — BHP DECISION
```

---

## 30. Autoryzacja

Dokument Sprintu nie stanowi automatycznie zgody na wykonanie Tasków.

Po zatwierdzeniu Sprintu każdy Task wymaga osobnego polecenia.

Status po zatwierdzeniu:

```text
SPRINT-003 v1.0-approved
```
