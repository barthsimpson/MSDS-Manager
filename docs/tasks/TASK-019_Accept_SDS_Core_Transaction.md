# TASK-019 — Accept SDS / Core Transaction

**Projekt:** MSDS Manager  
**Task ID:** TASK-019  
**Sprint:** SPRINT-003 — „Dodaj SDS”  
**Status:** READY  
**Typ:** Application / Persistence / PostgreSQL Integration  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI

## 1. Cel
Zaimplementować atomową akceptację zweryfikowanego przez użytkownika `AcceptSdsInput` i zapis do Core:

```text
AcceptSdsInput
→ walidacja
→ resolve/create MANUFACTURER
→ resolve/create PRODUCT
→ SDS CURRENT
→ SAFETY_PROFILE
→ SDS_COMPONENTS
→ PRODUCT = PENDING_APPROVAL
→ PRODUCT_HISTORY
→ COMMIT
```

Dowolny błąd = `ROLLBACK` całości. Przed jawnym ZAPISZ/AKCEPTUJ nie powstają rekordy Core.

## 2. Źródła obowiązujące
Przeczytaj root `AGENTS.md`, aktualny zatwierdzony `CORE-001`, SPRINT-003, TASK-017/018 i raporty, BDR-001, BDR-002 v1.2, BDR-003, BDR-005, TDR-001..004. Jeśli implementacja wymaga nowej decyzji biznesowej lub zmiany Core — STOP. Nie zgaduj.

## 3. Stan wejściowy
Po TASK-018 istnieją kontrakty SDS, `AcceptSdsInput`, `PdfSdsExtractor` i zatwierdzony `pypdf`. Parser nie zapisuje Core. Przed TASK-019 Alembic head = `e0dd7d6468bf`, schema = 12 tabel.

Jeżeli zatwierdzone encje SDS/SAFETY_PROFILE/SDS_COMPONENT nie mają jeszcze kompletnego ORM/schema, TASK-019 może dodać ich minimalne odwzorowanie i migrację Alembic. Nie rozszerzaj modelu ponad źródła.

## 4. Use case
Dodaj jeden jawny use case Application `AcceptSds` (lub nazwę zgodną z repo) przyjmujący `AcceptSdsInput`. To Application koordynuje całość; Streamlit nie wykonuje pojedynczych zapisów.

## 5. Walidacja przed zapisem
Przed pierwszym zapisem zweryfikuj co najmniej:
- plik istnieje i jest PDF,
- znajduje się w `SDS_ROOT_PATH`,
- spełnia wymaganą regułę językową `PL`,
- dostępne są wymagane dane tożsamości PRODUCT,
- producent został jednoznacznie wskazany/wybrany,
- statusy SafetyProfile należą do zatwierdzonych enumów.

`issue_date` i `revision` mogą być NULL. Nieprawidłowy język = zero zapisów Core.

## 6. MANUFACTURER
Producent istnieje → użyj istniejącego `manufacturer_id`. Nie istnieje → utwórz MANUFACTURER. Bez fuzzy matching, similarity, aliasów, lookupu i auto-merge. Niejednoznaczność ma dać kontrolowany błąd, nie automatyczny wybór.

## 7. PRODUCT identity
Tożsamość:
```text
product_name
manufacturer_product_code
manufacturer_id
```
Dokładne dopasowanie → istniejący PRODUCT. Brak dokładnego dopasowania → nowy PRODUCT. Nowa nazwa/kod/producent = nowy PRODUCT. Bez auto-merge i generic CRUD.

## 8. Nowy PRODUCT
W jednej transakcji utwórz:
```text
MANUFACTURER (jeśli nowy)
PRODUCT
SDS
SAFETY_PROFILE
SDS_COMPONENTS
PRODUCT_HISTORY initial snapshot
```
`PRODUCT.usage_status = PENDING_APPROVAL`.
Z formularza zapisuj wyłącznie zatwierdzone pola Core, w tym `use_description`, `use_restriction`.

## 9. Istniejący PRODUCT
Nie twórz duplikatu. Przy nowym zaakceptowanym SDS:
```text
old SDS CURRENT → ARCHIVED
new SDS         → CURRENT
PRODUCT         → PENDING_APPROVAL
```
Stary SDS, jego profil/składniki i historia pozostają. Nie przenoś decyzji BHP na nowy SDS.

## 10. SDS
Każdy zaakceptowany dokument ma własny `sds_id`. Zapisuj tylko zatwierdzone pola modelu, m.in. `product_id`, `original_filename`, `relative_path`, `issue_date`, `revision`, status CURRENT/ARCHIVED i `approved_at`, jeżeli należą do aktualnego modelu. `last_manual_edit_at` przy pierwszej akceptacji pozostaje NULL, jeśli pole istnieje.

Nazwa pliku, rewizja i data nie są techniczną tożsamością SDS. Maksymalnie jeden CURRENT na PRODUCT.

## 11. SAFETY_PROFILE
Dokładnie jeden profil dla nowego `sds_id`, zgodny z BDR-005:
`product_definition`, `hazardous_classification_status`, `clp_classification_text`, `signal_word`, `hazard_statements`, `supplemental_hazard_statements`, `pbt_status`, `vpvb_status`, `carcinogenicity_status`, `germ_cell_mutagenicity_status`, `reproductive_toxicity_status`, `endocrine_section_2_status`, `endocrine_section_11_status`, `skin_sensitization_status`, `respiratory_sensitization_status`.

Statusy tylko `YES`, `NO`, `NO_DATA`, `NOT_APPLICABLE`; `NO_DATA != NO`. Bez confidence score i provenance per field.

## 12. SDS_COMPONENTS
Każdy składnik należy do `sds_id`. Zakres:
`component_name`, `cas_number`, `ec_number`, `reach_registration_number`, `concentration_text`, `classification_text`, `hazard_statements`.

Lista może być pusta, braki = NULL. Bez lookupu, normalizacji chemii i przenoszenia klasyfikacji składnika na produkt.

## 13. PRODUCT status i historia
Po każdym zaakceptowanym nowym SDS: `PRODUCT = PENDING_APPROVAL`.

Nowy PRODUCT → initial PRODUCT_HISTORY snapshot. Istniejący PRODUCT zmieniający status → snapshot zgodny z TDR-004.

Twarda reguła:
```text
current state change + history snapshot = ONE TRANSACTION
```
Wykorzystaj istniejący `TransactionExecutor` i istniejące porty/repositories historii. Bez nowego history framework, audit log, event sourcing, triggerów lub JSONB audit trail.

Historia SDS wynika z zachowania kolejnych rekordów SDS CURRENT/ARCHIVED; nie twórz osobnej tabeli historii SDS bez zatwierdzonej potrzeby.

## 14. Atomowość
Logiczny przebieg:
```text
validate
→ resolve/create manufacturer
→ resolve/create product
→ archive old CURRENT
→ insert new SDS
→ insert SafetyProfile
→ insert Components
→ set Product PENDING_APPROVAL
→ ProductHistory snapshot
→ COMMIT
```
Każdy wyjątek → ROLLBACK. Po rollbacku nie może pozostać samotny MANUFACTURER, PRODUCT bez SDS, częściowy profil/skład, stan pośredni CURRENT/ARCHIVED ani historia bez odpowiadającego current state.

## 15. ORM / Alembic
Najpierw sprawdź istniejący Domain i ORM. Jeżeli SDS/SAFETY_PROFILE/SDS_COMPONENT wymagają persystencji, dodaj minimalne modele i jedną spójną migrację Alembic odwzorowującą wyłącznie zatwierdzony model. Bez `Base.metadata.create_all()` i bez tabel draftów.

Zabezpiecz FK SDS→PRODUCT, SAFETY_PROFILE→SDS, SDS_COMPONENT→SDS i zatwierdzone statusy. Regułę jednego CURRENT zabezpiecz co najmniej logiką Application/repository + testami. Nie buduj systemu concurrency/locking bez wymagania.

## 16. Plik i duplikaty
PDF pozostaje w `SDS_ROOT_PATH`; baza przechowuje referencję/metadane. Nie kopiuj, nie przenoś, nie zmieniaj nazwy, nie usuwaj i nie zapisuj PDF w PostgreSQL.

Nie buduj deduplikatora. Oczywisty konflikt → kontrolowany błąd i brak commit. Bez wyboru „nowszego” po dacie/rewizji, fuzzy matching i AI.

## 17. Testy
Dodaj testy Application/Domain oraz rzeczywiste testy PostgreSQL obejmujące:
- nowy manufacturer + nowy Product + CURRENT SDS + SafetyProfile + Components + initial ProductHistory,
- istniejący manufacturer bez duplikatu,
- istniejący Product bez duplikatu,
- old CURRENT→ARCHIVED + new CURRENT,
- Product→PENDING_APPROVAL + ProductHistory,
- pusta lista Components,
- opcjonalne issue_date/revision = NULL,
- błędny język → zero zapisów,
- błędna ścieżka/brak PDF → zero zapisów,
- dokładnie jeden CURRENT,
- rollback po kontrolowanym błędzie w środku transakcji i potwierdzenie braku częściowych rekordów.

Atomowości nie testuj wyłącznie mockami.

## 18. Poza zakresem
NIE implementuj: OCR, AI/LLM, confidence score, parser framework, workflow engine, background jobs, queue, storage/upload service, generic audit log, event sourcing, triggers, REACH, BHP_DECISION, DECISION_EVIDENCE, ACTIVE/REJECTED po decyzji BHP, Streamlit Add SDS UI, Excel import, fuzzy matching, chemical normalization, Internet lookup.

TASK-019 kończy się na:
```text
PRODUCT = PENDING_APPROVAL
SDS = CURRENT
```

## 19. STOP CONDITIONS
STOP/PARTIAL/BLOCKED, jeśli:
- wymagane jest rozszerzenie Core nieopisane w źródłach,
- potrzebny jest nowy status/enum biznesowy,
- `AcceptSdsInput` wymaga zmiany wymagającej decyzji biznesowej,
- nie da się jednoznacznie rozstrzygnąć PRODUCT/MANUFACTURER,
- TDR-004 nie pozwala bezpiecznie obsłużyć historii,
- potrzebna jest nowa biblioteka,
- konieczne byłoby rozpoczęcie BHP lub TASK-020,
- potrzebna jest nowa istotna decyzja techniczna.

Minimalna metoda repository, ORM lub migracja dokładnie odwzorowująca zatwierdzony model nie jest sama w sobie STOP.

## 20. Walidacja
```powershell
$env:PATH = "C:\\Program Files\\PostgreSQL\\17\\bin;$env:PATH"
.\\.venv\\Scripts\\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
.\\.venv\\Scripts\\python.exe -m alembic current
.\\.venv\\Scripts\\python.exe -m alembic check
git status --short
git diff --check
git diff --cached --check
```
Wymagane: pełny pytest PASS, brak SAWarning, Alembic spójny. Jeśli powstaje migracja, raportuj revision id, down_revision i liczbę tabel.

Potwierdź `.env` ignored, brak sekretów, nowych przypadkowych PDF/MSG, dumpów/backupów oraz brak commit/push bez polecenia.

## 21. Definition of Done
TASK-019 = DONE, gdy:
1. istnieje jeden use case AcceptSds,
2. dane wejściowe są zweryfikowanym formularzem,
3. Manufacturer/Product są używane lub tworzone zgodnie z Core,
4. Product po nowym SDS = PENDING_APPROVAL,
5. nowy SDS = CURRENT, poprzedni CURRENT = ARCHIVED,
6. maksymalnie jeden CURRENT na Product,
7. zapisane są SafetyProfile i Components,
8. ProductHistory jest zgodny z TDR-004,
9. całość jest jedną transakcją i rollback działa w PostgreSQL,
10. PDF nie jest modyfikowany,
11. nie ma trwałego draftu, BHP ani UI TASK-020,
12. pełna regresja i Alembic PASS,
13. brak niezatwierdzonego rozszerzenia Core,
14. TASK-020 nie został rozpoczęty.

## 22. Raport
Utwórz `docs/task_reports/TASK-019_REPORT.md`.

Raport: status; źródła; zmienione pliki; AcceptSds; walidacja; Manufacturer; Product identity; nowy/istniejący Product; CURRENT/ARCHIVED; SafetyProfile; Components; ProductHistory; transakcja/rollback; Domain/ORM/schema; migracja; testy Application/PostgreSQL; pełny pytest; SAWarning; Alembic current/check; Git/bezpieczeństwo; odstępstwa; ryzyka.

Zakończ:
```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-020.
```

## 23. Autoryzacja
Obecność pliku nie autoryzuje wykonania. Start dopiero po:
```text
Wykonaj TASK-019.
```
Po zakończeniu nie rozpoczynaj TASK-020.
