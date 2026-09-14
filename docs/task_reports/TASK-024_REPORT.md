# TASK-024 — Streamlit „Decyzja BHP”

## 1. Status

`DONE`

Dodano cienki widok Streamlit do rejestracji decyzji BHP przez istniejące `RegisterBhpDecision`. Nie rozpoczęto TASK-025.

## 2. Zmienione pliki

- `app/application/dto/bhp_decisions.py`
- `app/application/dto/__init__.py`
- `app/presentation/streamlit/app.py`
- `app/presentation/streamlit/composition.py`
- `app/presentation/streamlit/bhp_decision.py`
- `app/infrastructure/db/repositories/bhp_decision_query.py`
- `app/infrastructure/db/repositories/__init__.py`
- `tests/unit/test_streamlit_bhp_decision.py`
- `tests/unit/test_streamlit_shell_unit.py`
- `tests/integration/test_streamlit_shell.py`
- `docs/task_reports/TASK-024_REPORT.md`

Nie zmieniono ORM, Domain, PostgreSQL schema ani Alembic.

## 3. Widok i wybór produktu

Dodano sekcję `Decyzja BHP` do istniejącej nawigacji Streamlit. Produkty są pobierane przez adapter query wyłącznie wtedy, gdy mają SDS `CURRENT`. Etykieta pokazuje nazwę produktu, kod producenta, producenta i status, a do dalszych operacji przekazywany jest rzeczywisty `product_id`.

Dla wybranego produktu widok pokazuje `sds_id` pośrednio przez rzeczywisty rekord CURRENT SDS oraz filename, issue date, revision i status `CURRENT`.

## 4. Bieżąca decyzja

Jeżeli dla SDS istnieje decyzja CURRENT, UI pokazuje status, registered_at, evidence path i notes oraz informuje, że nowy zapis zastąpi bieżącą decyzję. Starej decyzji nie można edytować bezpośrednio. CURRENT/SUPERSEDED pozostaje odpowiedzialnością TASK-023.

## 5. Evidence

Kompozycja listuje rekurencyjnie istniejące pliki pod `BHP_EVIDENCE_ROOT_PATH`, ograniczając listę do `.msg`, `.pdf`, `.jpg`, `.jpeg`, `.png`. Do Application przekazywana jest wyłącznie ścieżka względna. UI nie kopiuje, nie przenosi, nie usuwa, nie zmienia nazw i nie analizuje treści evidence.

Ostateczna walidacja root/path/extension odbywa się przez `BhpEvidenceValidator` w infrastrukturze.

## 6. Formularz i zapis

Formularz zawiera:

- produkt,
- CURRENT SDS,
- dowód decyzji,
- wyłącznie `APPROVED` lub `REJECTED`,
- opcjonalne notes,
- przycisk `Zapisz decyzję`.

UI buduje `RegisterBhpDecisionInput` i wywołuje wyłącznie `ShellComposition.register_bhp_decision`, które składa `RegisterBhpDecision`, validator evidence, repozytorium i `TransactionExecutor`. UI nie wykonuje SQL, commit/rollback, nie ustawia statusu produktu i nie tworzy rekordów BHP.

Po sukcesie komunikat wynika z `RegisterBhpDecisionResult`: pokazuje `ACTIVE` dla APPROVED albo `REJECTED` dla REJECTED. Widok wykonuje rerun z jednorazowym komunikatem, dzięki czemu pobiera aktualny status i bieżącą decyzję.

## 7. Obsługa braku i błędów

Brak produktu z CURRENT SDS pokazuje kontrolowaną informację i nie renderuje formularza. Brak evidence blokuje zapis przed wywołaniem Application. Błędy Application/Infrastructure są prezentowane przez `st.error`; testy nie ujawniły stack trace ani sekretów. Nie zmieniono historycznej decyzji ani statusu w przypadku brakującego pliku evidence.

## 8. Testy UI

AppTest pokrywa:

- produkt z CURRENT SDS i formularz,
- APPROVED z wynikiem ACTIVE,
- REJECTED z wynikiem REJECTED,
- notes przekazane do inputu Application,
- brak evidence bez wywołania rejestracji i bez fałszywego sukcesu,
- istniejącą decyzję CURRENT.

Focused testy UI: `8 passed`.

Nie wykonano osobnego manual smoke PostgreSQL przez UI; logika backendu i transakcje są pokryte testami TASK-023, a UI jest zweryfikowane AppTest z atrapą kompozycji.

## 9. Architektura

```text
Streamlit
  -> ShellComposition
  -> RegisterBhpDecision
  -> BhpEvidenceValidator / repository
  -> TransactionExecutor / PostgreSQL
```

Odczyt produktu/SDS/bieżącej decyzji został wydzielony do `SqlAlchemyBhpDecisionQuery`. Widok nie importuje ORM, repozytoriów infrastrukturalnych, SQLAlchemy, psycopg ani filesystem adapterów.

## 10. Walidacja końcowa

- pełny pytest: `137 passed`,
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS,
- brak `SAWarning`,
- `alembic current`: `e0dd7d6468bf (head)`,
- `alembic check`: `No new upgrade operations detected.`,
- diagnostyka zmienionych plików: brak błędów,
- schema bez zmian, bez migracji i driftu,
- brak nowych zależności.

## 11. Git / bezpieczeństwo

`.env` pozostaje ignorowany. Nie dodano evidence, sekretów, dumpów ani backupów. Nie wykonano commit ani push. `git diff --check` i `git diff --cached --check` nie wykazały błędów whitespace.

## 12. Odstępstwa i ryzyka

Widok nie posiada własnego podglądu treści evidence ani osobnego workflow edycji decyzji, zgodnie z zakresem. Bieżąca decyzja może wskazywać plik usunięty z filesystemu; rekord historyczny pozostaje ważny, a UI pokazuje zapisaną ścieżkę bez automatycznej naprawy.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-025.
