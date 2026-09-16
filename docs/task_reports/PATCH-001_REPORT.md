# PATCH-001 REPORT

STATUS: DONE

CAUSE:
- Streamlit `modified_sys_path` dodaje katalog entry pointu na początek ścieżki importów. Przed zmianą `find_spec('app')` wskazywał `app/presentation/streamlit/app.py`, bez ścieżki pakietu. Lokalny plik przesłaniał pakiet projektu.

CHANGED:
- `app/presentation/streamlit/app.py` → `app/presentation/streamlit/main.py`; zawartość i zachowanie zachowane, w tym wcześniejsze zmiany TASK-027.
- Zaktualizowano bezpośrednie referencje w `tests/unit/test_streamlit_shell_unit.py`, `tests/integration/test_streamlit_shell.py`, `tests/integration/test_task016_acceptance.py`.
- Dodano ten raport. Composition i ekrany bez zmian.

VALIDATION:
- focused tests: **2 passed** (`tests/unit/test_streamlit_shell_unit.py`); kontrola whitespace PASS.
- W osobnym, świeżym procesie odtworzono pierwszeństwo katalogu entry pointu w `sys.path`: `app` wskazuje teraz root `app/__init__.py` i jest pakietem. AppTest nowej ścieżki wykonał aplikację z rzeczywistą konfiguracją: tytuł MSDS Manager, brak wyjątków i komunikatów błędu.
- physical Streamlit startup: PASS — `python -m streamlit run app/presentation/streamlit/main.py` z opcjami headless, loopback i wolnym portem; health `ok`, HTTP 200, normalny komunikat startu. Serwer zatrzymano po smoke check. Wykonanie samego skryptu potwierdził osobno powyższy AppTest.
- ModuleNotFoundError: RESOLVED.
- Nie uruchamiano pełnej regresji, integracyjnego zestawu PostgreSQL, Alembic ani tymczasowego klastra.

SCOPE:
- business logic: unchanged.
- Core/schema/Alembic: unchanged.
- dependencies: unchanged.
- Zastane zmiany innych Tasków pozostawiono; bez commit/push/reset.

RISKS / DEVIATIONS:
- AppTest ujawnił istniejące ostrzeżenie Streamlit o `use_container_width` na ekranie produktów; poza zakresem PATCH, bez zmian. Brak odstępstw funkcjonalnych.

Nowe polecenie uruchomienia z katalogu repozytorium:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/main.py
```

Walidację wykonano z katalogiem zainstalowanego PostgreSQL 17 w PATH, jak w dotychczasowym środowisku projektu.

OCZEKUJĘ NA JAWNE POLECENIE.
