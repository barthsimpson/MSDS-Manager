# TASK-005 — Pierwsza migracja Alembic i utworzenie schematu PostgreSQL

**Projekt:** MSDS Manager  
**Task ID:** TASK-005  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Wygenerować, zweryfikować i zastosować pierwszą wersjonowaną migrację Alembic tworzącą schemat aplikacyjny MSDS Manager w lokalnym PostgreSQL.

TASK-005 jest pierwszym Taskiem, który może wykonać kontrolowaną zmianę DDL w bazie `msds_manager`.

Po zakończeniu oczekiwany stan:

```text
Domain models           YES
ORM models              YES
Base.metadata           YES
Alembic revision        1
PostgreSQL app tables   9
```

Migracja musi wynikać z zaakceptowanego modelu ORM z TASK-004.

---

## 2. Warunek wejścia

TASK-004 jest zakończony statusem `DONE` i zaakceptowany.

Stan wejściowy:

- 9 modeli domenowych,
- 9 odpowiadających modeli ORM,
- `Base.metadata` zawiera dokładnie 9 tabel,
- Alembic wskazuje `Base.metadata`,
- Alembic ma 0 rewizji,
- PostgreSQL ma 0 tabel aplikacyjnych,
- 40/40 testów przechodzi,
- `.env` jest lokalny i ignorowany przez Git.

---

## 3. Obowiązujące źródła

Implementacja musi być zgodna z:

- CORE-001 v1.0-approved,
- BDR-001,
- BDR-002,
- BDR-003,
- BDR-004,
- BDR-005 v1.0-approved,
- TDR-001,
- TDR-002,
- TDR-003,
- zaakceptowanymi rezultatami TASK-003 i TASK-004,
- AGENTS.md.

TASK-005 nie zmienia modelu domenowego ani ORM.

Jeżeli autogenerate ujawni problem w modelu ORM, nie poprawiaj go bez analizy. Zastosuj STOP i zgłoś problem.

---

## 4. Zasada nadrzędna

`alembic revision --autogenerate` służy do przygotowania propozycji migracji.

**Wygenerowana migracja nie jest automatycznie poprawna ani automatycznie zatwierdzona.**

Obowiązuje sekwencja:

```text
Base.metadata
      ↓
alembic revision --autogenerate
      ↓
REVIEW MIGRATION FILE
      ↓
porównanie z ORM/Core
      ↓
dopiero po zgodności:
alembic upgrade head
```

Codex ma przeczytać wygenerowany plik migracji przed wykonaniem `upgrade`.

---

## 5. Generowanie pierwszej rewizji

Wygeneruj jedną początkową rewizję Alembic.

Preferowana nazwa logiczna:

```text
initial_core_schema
```

lub równoważna, jednoznaczna nazwa.

Przykładowe polecenie:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "initial core schema"
```

Nie twórz ręcznie kilku migracji dla poszczególnych tabel.

TASK-005 ma utworzyć **jedną początkową migrację Core**.

---

## 6. Zakres oczekiwanej migracji

Migracja powinna tworzyć dokładnie tabele wynikające z TASK-004:

```text
manufacturers
products
usage_locations
product_usage_locations
sds_documents
bhp_decisions
decision_evidence
safety_profiles
sds_components
```

Jeżeli rzeczywiste nazwy zatwierdzone w TASK-004 są minimalnie inne, zachowaj istniejące nazwy ORM.

Nie zmieniaj nazw tylko po to, aby dopasować je do przykładu.

---

## 7. Weryfikacja pliku migracji przed upgrade

Przed `alembic upgrade head` sprawdź ręcznie wygenerowany plik.

Zweryfikuj co najmniej:

### 7.1. Liczbę tabel

Migracja tworzy dokładnie 9 tabel aplikacyjnych.

### 7.2. PK i FK

Sprawdź obecność oczekiwanych:

- PK,
- FK Manufacturer → Product,
- FK Product → SDS,
- FK Product ↔ ProductUsageLocation,
- FK UsageLocation ↔ ProductUsageLocation,
- FK SDS → SafetyProfile,
- FK SDS → SdsComponent,
- FK SDS/Product → BhpDecision,
- relacji BHP Decision ↔ DecisionEvidence.

### 7.3. Typy

Sprawdź:

- `Numeric` dla ilości,
- właściwe typy dat/timestampów,
- `ARRAY(String)` dla H-statements, jeśli taki mapping zatwierdzono w TASK-004,
- zgodne odwzorowanie enumów jako `VARCHAR + CHECK`.

### 7.4. Nullable

Sprawdź szczególnie:

- `issue_date` — nullable,
- `revision` — nullable,
- `last_manual_edit_at` — nullable,
- opcjonalne dane składnika SDS — nullable,
- `notes` decyzji BHP — nullable.

### 7.5. Brak niezatwierdzonych elementów

Migracja nie może dodawać:

- `peak_factory_quantity`,
- `decided_by`,
- `decision_date`,
- confidence score,
- tabel dostawców,
- tabel magazynowych,
- tabel użytkowników,
- tabel REACH,
- dodatkowych słowników CLP.

### 7.6. Cascade delete

Sprawdź, czy migracja nie wprowadza niezatwierdzonego agresywnego `ON DELETE CASCADE`.

---

## 8. Dozwolone korekty pliku migracji

Codex może ręcznie poprawić wygenerowany plik migracji wyłącznie wtedy, gdy:

- autogenerate nie odwzorował poprawnie istniejącego modelu ORM,
- korekta nie zmienia modelu biznesowego,
- korekta jest jednoznacznie techniczna,
- zostanie opisana w raporcie.

Nie wolno używać pliku migracji do „naprawienia” lub zmiany modelu ORM/Core.

Jeżeli wymagane byłoby inne znaczenie danych lub relacji — STOP.

---

## 9. Upgrade

Dopiero po pozytywnej weryfikacji migracji uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Operacja ma zostać wykonana na lokalnej bazie developerskiej `msds_manager` skonfigurowanej w `.env`.

Nie wykonuj migracji na żadnej innej bazie.

---

## 10. Weryfikacja PostgreSQL po migracji

Po `upgrade head` potwierdź:

- istnieje tabela `alembic_version`,
- istnieje 9 tabel aplikacyjnych,
- wszystkie oczekiwane tabele są widoczne,
- nie ma dodatkowych tabel aplikacyjnych.

Użyj diagnostycznych zapytań SQL lub SQLAlchemy.

Nie wprowadzaj danych biznesowych.

---

## 11. Test downgrade / upgrade

Pierwsza migracja musi być odwracalna.

Po pozytywnym pierwszym upgrade wykonaj kontrolowany test:

```text
upgrade head
   ↓
downgrade base
   ↓
sprawdzenie: brak 9 tabel aplikacyjnych
   ↓
upgrade head
   ↓
sprawdzenie: 9 tabel aplikacyjnych
```

Warunki:

- test dotyczy wyłącznie lokalnej developerskiej bazy `msds_manager`,
- baza nie zawiera jeszcze danych biznesowych,
- po zakończeniu Tasku baza pozostaje na `head`,
- downgrade nie może naruszać tabel/systemowych schematów PostgreSQL.

Jeżeli downgrade wygenerowany przez Alembic nie jest poprawny — STOP przed ponownym uznaniem Tasku za DONE.

---

## 12. Kontrola idempotencji operacyjnej

Po zakończeniu migracji:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

uruchomione ponownie nie powinno próbować tworzyć tabel drugi raz ani kończyć się błędem.

Zaraportuj wynik.

---

## 13. Testy

Uruchom wszystkie dotychczasowe testy:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

TASK-005 nie powinien zmieniać zachowania domeny ani metadata-level tests.

Jeżeli istnieją testy integracyjne migracji, możesz je dodać tylko w minimalnym zakresie i bez nowej biblioteki.

Nie używaj SQLite.

---

## 14. Kontrola driftu ORM ↔ Database

Po finalnym `upgrade head` porównaj:

```text
Base.metadata
vs
rzeczywisty schema PostgreSQL
```

Możesz użyć Alembic autogenerate/check lub inspekcji SQLAlchemy.

Cel:

> brak niewykonanej różnicy pomiędzy zatwierdzonym ORM a aktualnym schema.

Nie generuj drugiej migracji tylko po to, aby „wyczyścić” nieoczekiwany drift. Najpierw zgłoś problem.

---

## 15. Alembic history / current

Po zakończeniu zaraportuj wyniki:

```powershell
.\.venv\Scripts\python.exe -m alembic history
.\.venv\Scripts\python.exe -m alembic current
```

Oczekiwany stan:

```text
1 revision
current = head
```

---

## 16. Git

Migracja jest częścią kodu projektu i musi być śledzona przez Git.

Sprawdź:

```powershell
git status --short
```

Nie wykonuj commita, jeżeli Task nie zawiera jawnego polecenia commitowania.

Nie dodawaj do Git:

- `.env`,
- danych PostgreSQL,
- plików SDS/BHP,
- backupów,
- sekretów.

---

## 17. Elementy poza zakresem

Nie implementuj w TASK-005:

- nowych modeli ORM,
- zmian modeli domenowych,
- nowych enumów,
- zaawansowanych partial unique indexes,
- constraintu „jeden CURRENT SDS” jeśli nie istnieje jeszcze w modelu,
- constraintu „jedna CURRENT decyzja BHP”,
- zgodności product_id decyzji i SDS na poziomie zaawansowanym,
- repozytoriów,
- CRUD,
- use cases,
- UI,
- danych seed,
- importu Excel,
- ekstrakcji PDF,
- REACH,
- backupu,
- systemu użytkowników,
- dodatkowych bibliotek.

Zaawansowane constraints należą do TASK-006.

---

## 18. Zasada STOP

Zatrzymaj Task przed `upgrade` lub dalszą zmianą, jeżeli:

- migracja generuje inną liczbę tabel niż 9,
- pojawiają się nieoczekiwane kolumny lub tabele,
- autogenerate chce usunąć/zmienić element spoza zatwierdzonego modelu,
- FK są sprzeczne z Core,
- downgrade jest niebezpieczny,
- pojawia się problem z enumami lub ARRAY wymagający zmiany decyzji,
- migracja wymaga modyfikacji domeny lub ORM,
- potrzebna byłaby nowa biblioteka,
- Task zaczyna wchodzić w TASK-006.

W takim przypadku raportuj `PARTIAL` albo `BLOCKED`.

---

## 19. Kryteria akceptacji

TASK-005 może otrzymać `DONE`, jeżeli:

1. istnieje dokładnie jedna początkowa rewizja Alembic,
2. plik migracji został jawnie zweryfikowany przed upgrade,
3. migracja odwzorowuje zatwierdzone 9 modeli ORM,
4. upgrade tworzy 9 tabel aplikacyjnych,
5. `alembic_version` wskazuje head,
6. downgrade do base usuwa schemat aplikacyjny bez błędu,
7. ponowny upgrade odtwarza schemat,
8. końcowy stan bazy to `head`,
9. ponowne `upgrade head` jest bezpieczne,
10. brak driftu ORM ↔ schema,
11. wszystkie testy przechodzą,
12. nie dodano niezatwierdzonych tabel/kolumn/reguł,
13. nie dodano nowych bibliotek,
14. `.env` pozostaje ignorowany,
15. TASK-006 nie został rozpoczęty.

---

## 20. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-005_REPORT.md
```

Raport musi zawierać:

### 1. Status
`DONE`, `PARTIAL` albo `BLOCKED`

### 2. Rewizja
- revision id,
- nazwa pliku,
- message.

### 3. Review wygenerowanej migracji
- liczba tabel,
- PK/FK,
- enumy,
- typ ilości,
- H-statements,
- nullable,
- brak elementów poza zakresem.

### 4. Ręczne korekty migracji
`BRAK` albo dokładny opis.

### 5. Upgrade
- polecenie,
- wynik.

### 6. PostgreSQL po upgrade
- `alembic_version`,
- lista/ilość tabel aplikacyjnych.

### 7. Downgrade / re-upgrade
- wyniki obu operacji.

### 8. Idempotencja
- wynik ponownego `upgrade head`.

### 9. Drift ORM ↔ schema
- wynik kontroli.

### 10. Testy
- polecenie,
- liczba testów,
- wynik.

### 11. Alembic history/current
- rzeczywiste wyniki.

### 12. Git / bezpieczeństwo

### 13. Odstępstwa

### 14. Problemy / ryzyka

### 15. Pytania do Cerberusa

### 16. Następny krok

```text
OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-006.
```

---

## 21. Zakończenie

Po TASK-005:

- baza ma pozostać na `head`,
- migracja ma pozostać w repozytorium,
- nie twórz nowych migracji,
- nie implementuj constraintów TASK-006,
- zapisz raport,
- przedstaw użytkownikowi krótkie podsumowanie,
- zatrzymaj się i oczekuj na Cerberus Review.
