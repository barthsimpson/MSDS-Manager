# TASK-054 REPORT

STATUS:
```text
TECHNICAL IMPLEMENTATION: DONE
PHYSICAL UX REVIEW: PENDING
OPERATOR COMMIT: PENDING
TASK-054 FINAL ACCEPTANCE: PENDING
```

CHANGED:
- `docs/tasks/TASK-054_Human_Review_Commit_UI_ALUCYNK.md` — Task dostarczony przez użytkownika.
- `app/presentation/streamlit/evidence_import.py` — nowy widok pojedynczego importu Evidence JSON.
- `app/presentation/streamlit/add_sds.py` — zakładka Evidence JSON w istniejącym „Dodaj SDS”.
- `app/presentation/streamlit/composition.py` — połączenie widoku z TASK-052 i TASK-053 oraz odczyt wyniku.
- `app/presentation/streamlit/main.py` — przejście do karty produktu po sukcesie.
- `tests/unit/test_task054_evidence_ui.py`, `tests/unit/test_streamlit_add_sds.py` — bramki UI i regresja ręcznego dodawania.
- `tests/integration/test_task054_operator_flow.py` — izolowany przepływ ALUCYNK-like.
- `docs/task_reports/TASK-054_REPORT.md`.

IMPLEMENTED:
- Jeden wybór Evidence JSON, jeden wybór PDF i jeden logical SDS na operację.
- Czytelny DRY RUN z walidacją, resolution, kandydatami, podobnymi producentami, ostrzeżeniami, blokadami i dowodami źródłowymi.
- Jawne CREATE/LINK producenta i produktu; podobne rekordy nie są automatycznie łączone. LINK jest dostępny dla dokładnej zatwierdzonej tożsamości zgodnie z TASK-053.
- Wymagane dane ręczne, wszystkie dziesięć statusów safety i potwierdzenie przeglądu źródłowego SDS. Brak ekstrakcji pozostaje pusty; `NO_DATA` może wybrać tylko operator.
- Osobne `ApprovedImportPlan` i `ControlledEvidenceImport`. PDF musi być wybrany, mieć sygnaturę PDF i zgadzać się z SHA-256 źródła w JSON.
- Finalne potwierdzenie zapisu, prezentacja sukcesu i przejście do karty produktu.

UI FLOW:
1. **Source selection:** operator wskazuje JSON oraz PDF; nazwa PDF z JSON jest jedynie wskazówką.
2. **DRY RUN:** TASK-052 wykonuje odczyt w transakcji PostgreSQL `READ ONLY`. Operator wybiera jeden `document_key`.
3. **Manufacturer review:** proponowana nazwa kanoniczna, dokładne i podobne rekordy oraz jawne CREATE/LINK.
4. **Product review:** produkt, kod jako „Brak danych”, kandydaci, jawne CREATE/LINK; LINK przy kodzie JSON `NULL` wymaga odrębnego potwierdzenia.
5. **Manual inputs:** `use_description` i `use_restriction` są wymagane i potwierdzane.
6. **Safety review:** dziesięć wymaganych statusów, dane uzupełniające i tabela `field/value/state/page/context/source_text` z Evidence JSON.
7. **ApprovedImportPlan:** przycisk jest zablokowany do zakończenia przeglądu, poprawnego PDF oraz kompletu decyzji. Po zatwierdzeniu widoczny jest zamrożony skrót planu i binding SHA-256.
8. **Controlled commit:** osobne świadome potwierdzenie uruchamia TASK-053; wynik zawiera SDS, status, `original_filename` i przejście do karty produktu.

ALUCYNK READINESS:
- Evidence JSON: `docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json`; DRY RUN `VALID` według TASK-052.
- Oczekiwany PDF według JSON: `ALUCYNK 23.01.2023 rew. 2.0.pdf`; operator musi wskazać realny plik, którego SHA-256 odpowiada Evidence JSON. PDF nie jest dołączony do repozytorium.
- Manufacturer: proponowane `CX80 POLSKA`, `CREATE_CANDIDATE`; podobne rekordy w operator DB według TASK-052: `CX80`, `CX80 Polska`, `Cx80`.
- Product: `ALUCYNK`, warunkowy `CREATE_CANDIDATE`; manufacturer product code: „Brak danych”.
- SDS: data `2023-01-23`, rewizja `2.0`.
- Safety: `INCOMPLETE_SAFETY_DATA`; realna treść SDS wymaga decyzji operatora dla wszystkich statusów. Operator musi także podać oba pola zastosowania i zatwierdzić plan przed zapisem.

DOUBLE SUBMIT / RERUN SAFETY:
- Zatwierdzony plan jest zamrożony w sesji; zmiana JSON, PDF lub `document_key` usuwa plan i wymaga ponownego DRY RUN.
- Przed wywołaniem zapisu plan otrzymuje stan `consumed`; po sukcesie lub kontrolowanym błędzie jest usuwany. Rerun pokazuje wynik zamiast przycisku COMMIT.
- TASK-053 ponownie sprawdza źródła i stan DB. `STALE_RESOLUTION`, `SOURCE_CHANGED` i `PDF_CHANGED` kończą próbę komunikatem wymagającym nowego planu.
- Odświeżenie przeglądarki nie przywraca planu z poprzedniej sesji. Nie dodano trwałej tabeli idempotencji.

VALIDATION:
- Unit/application + Streamlit/AppTest: `11 passed` — DRY RUN, podobny producent, brak kodu, kompletność safety, approval, final confirmation, PDF change, LINK z kodem JSON `NULL`, stale, sukces i rerun oraz regresja ręcznego dodawania.
- Isolated PostgreSQL + temporary SDS root: test ALUCYNK-like `PASS`; sprawdzono CREATE Manufacturer/Product, kod `NULL`, SDS `CURRENT`, PDF oraz odczyt karty produktu. Test wykorzystał symulowane wartości review i testowy PDF, nie realny dokument ALUCYNK.
- Related regression: `103 passed, 1 skipped` — TASK-052, TASK-053, `AcceptSds`, `AddSdsRevision`, `ImportSds`, Product Card i test TASK-054. Pominięcie pochodzi z istniejącego testu regresyjnego.
- `git diff --check` dla śledzonych zmian: PASS. Nowe pliki: brak końcowych spacji.
- Aplikacja działa pod `http://127.0.0.1:8501`; `/_stcore/health` zwrócił HTTP 200.

OPERATOR SAFETY:
- Operator DB writes podczas implementacji i testów: `0`.
- Operator `SDS_ROOT_PATH` writes podczas implementacji i testów: `0`.
- Realny import ALUCYNK: **nie wykonano**.
- Testy integracyjne tworzyły i usuwały wyłącznie jednorazowe bazy `task054_*` / `task053_*`; pliki SDS trafiały do tymczasowych katalogów testowych.

PHYSICAL UX:
- Status: **PENDING** — wymagany przegląd przez Architekta Operacyjnego przy `1920×1080`, zoom `100%`.
- URL: `http://127.0.0.1:8501` → „Dodaj SDS” → „Import z Evidence JSON”.
- Komenda uruchomienia: `.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/main.py --server.headless true --server.address 127.0.0.1 --server.port 8501`.
- Do oceny: czytelność, hierarchia pól i akcji, przewijanie, widoczność ostrzeżeń, rozdzielenie źródeł / review / planu / COMMIT.

SCOPE:
- Bez zmian Core, Domain, ORM, schema, migracji, parsera i SDS-ALIAS.
- Bez nowych zależności i bez importu batchowego.
- Brak bezpośredniego SQL/ORM persistence w widoku UI.

RISKS / DEVIATIONS:
- TASK-053 zatwierdza LINK producenta tylko przy dokładnej zatwierdzonej tożsamości. Podobne rekordy są pokazywane, lecz ich ewentualne powiązanie pod inną nazwą wymaga odrębnego rozstrzygnięcia poza tym przepływem.
- Pierwszy przebieg integracji został zatrzymany przez uprawnienia starego `.pytest_tmp`; powtórzenie z wydzielonym `--basetemp` przeszło. Nie był to błąd aplikacji.
- Fizyczny przegląd UI oraz merytoryczna ocena realnego PDF ALUCYNK pozostają decyzją Architekta Operacyjnego.

NEXT:
- STOP → fizyczny UX review przez Architekta Operacyjnego → ewentualny świadomy operator COMMIT ALUCYNK w UI → Cerberus review.
- Nie rozpoczynać automatycznie importu pozostałych JSON ani prac SDS-ALIAS.
