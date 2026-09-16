# TASK-027 — Streamlit „Widok nadzorczy”

## Status

DONE — 2026-09-16. Wykonano wyłącznie TASK-027 zgodnie z jego aktualnym plikiem. Przeczytano AGENTS.md, CORE-001 v1.2, SPRINT-005, TASK-026 i jego raport oraz istniejące ekrany TASK-020/024. Dwie kopie draftu SPRINT-005 mają identyczną zawartość. Starszy proponowany backlog Sprintu numeruje UI jako TASK-028; aktualny TASK-027 jawnie definiuje UI i wskazuje integrację PostgreSQL jako zakończoną w TASK-026. Nie zmieniano dokumentów źródłowych ani decyzji biznesowych.

## Zmienione pliki

- `app/presentation/streamlit/app.py` — jedna nowa pozycja nawigacji i wywołanie widoku.
- `app/presentation/streamlit/composition.py` — podłączenie istniejącego service i adaptera.
- `app/presentation/streamlit/supervisory.py` — nowy ekran tylko do odczytu.
- `tests/unit/test_streamlit_supervisory.py` — 13 AppTests.
- `tests/unit/test_streamlit_shell_unit.py` — aktualizacja oczekiwanej nawigacji.
- `tests/integration/test_streamlit_shell.py` — nawigacja do widoku, pusty odczyt przez rzeczywisty composition i kontrola braku zapisów.
- `docs/task_reports/TASK-027_REPORT.md` — raport.

## Nawigacja i composition

Dodano „Widok nadzorczy” na końcu istniejącej nawigacji. Pozostałe ekrany i domyślna sekcja pozostają bez przebudowy.

Istniejący `build_shell_composition` przekazuje konfigurację z `load_settings` do `ShellComposition`. Metoda `list_supervisory_products` otwiera sesję przez istniejącą fabrykę i wywołuje `ListSupervisoryProducts(SqlAlchemySupervisoryQuery(session, settings=...)).execute()`. Sesja zamyka się po odczycie; shell nadal zwalnia engine w `finally`. Nie ma nowego composition root ani cache. Opcjonalne pole settings zachowuje zgodność dotychczasowych konstruktorów testowych; brak konfiguracji przy wywołaniu nowego odczytu daje kontrolowany błąd, bez fallbacku ścieżek.

## Tabela i prezentacja

Jedna tabela `st.dataframe`, jeden otrzymany PRODUCT = jeden wiersz. Zawiera dokładnie wymagane kolumny: Produkt, Producent, Kod producenta, Miejsca stosowania, SDS, Data SDS, Rewizja SDS, Status produktu, BHP, Warunki / uwagi, Wymaga działania.

Lokalizacje i powody są łączone separatorem `; `. Brak lokalizacji, daty, rewizji lub notes jest wyświetlany jako `—`. Data ma format ISO. Notes są wyświetlane bez interpretacji.

SDS jest formatowany jako CURRENT, BRAK CURRENT SDS lub BRAK PLIKU SDS według pól DTO. BHP pokazuje APPROVED, REJECTED lub BRAK DECYZJI. `requires_action=False` daje OK, a True wyświetla wszystkie przekazane `action_reasons`. Widok nie wybiera CURRENT ani nie przelicza powodów; nie importuje SQL/ORM i nie sprawdza filesystemu.

## Filtry, pusta baza i błędy

Są dokładnie trzy filtry: Wszystkie / Wymagają działania, status produktu, miejsce stosowania. Działają łącznie. Filtr lokalizacji sprawdza przynależność do `usage_locations`, również dla produktu z wieloma miejscami. Opcja wszystkich lokalizacji używa wartości None, więc nie koliduje z nazwą lokalizacji.

Pusta lista service daje `Brak produktów do wyświetlenia.`. Brak wyników filtrowania daje osobny komunikat i pozostawia filtry dostępne. `SupervisoryReadError` oraz kontrolowany błąd composition dają `Nie udało się odczytać danych widoku nadzorczego.` bez ujawniania szczegółów technicznych i bez prób naprawy.

Ekran jest read-only: brak edycji, zapisów, przycisków operacji, upload/download dokumentów, workflow i dashboardów.

## Weryfikacja

| Kontrola | Wynik |
|---|---|
| Focused AppTests i testy jednostkowe shella | 15 passed (13 nowych AppTests + 2 shell), 3.50 s |
| Istniejące focused TASK-026 | 15 passed |
| Integracja read model PostgreSQL | 9 passed |
| Pełny pytest | 175 passed, 11.90 s; baseline 162 + 13 nowych |
| SAWarning | Brak; pytest z `-W error::sqlalchemy.exc.SAWarning` |
| Alembic current — izolowana baza | `e0dd7d6468bf (head)` |
| Alembic check — izolowana baza | `No new upgrade operations detected.` |
| Alembic current — skonfigurowana baza | `e0dd7d6468bf (head)` |
| Alembic check — skonfigurowana baza | `No new upgrade operations detected.` |
| Cleanup | 0 produktów po regresji; klaster i fixture usunięte |

AppTests pokrywają wszystkie dziewięć wymaganych scenariuszy, dodatkowo formatowanie brakujących pól, REJECTED, brak pliku SDS, łączenie i reset filtrów oraz kontrolowany błąd composition. Test powodów przekazuje gotowe wartości DTO niezależnie od jego pozostałych pól, sprawdzając prezentację zamiast ponownego testowania reguł TASK-026.

Polecenia:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_streamlit_supervisory.py tests/unit/test_streamlit_shell_unit.py -q -W error::sqlalchemy.exc.SAWarning
.\.venv\Scripts\python.exe scripts/verify_task026.py
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Ponownie wykorzystano istniejący, niezmieniony skrypt izolowanej weryfikacji: wykonuje pełny pytest oraz Alembic na tymczasowym PostgreSQL 17, z osobnym basetemp pod `.venv`. Nie jest to rozpoczęcie kolejnego Tasku.

Pierwszy focused przebieg miał timeout pierwszego AppTest przy domyślnych 3 s; ustawiono timeout 10 s, zgodnie z czasem używanym przez istniejące testy shella. Kolejny focused przebieg i pełna regresja przeszły. Pierwsze bezpośrednie wywołanie Alembic wymagało dodania zainstalowanych binariów PostgreSQL do PATH (libpq); po ustawieniu PATH oba polecenia przeszły bez instalowania zależności.

## Core, Git i bezpieczeństwo

Brak zmian Core, Domain, ORM, schematu, migracji Alembic, zależności i reguł TASK-026. Regresja działała na izolowanej bazie; na skonfigurowanej bazie wykonano jedynie odczyt Alembic current/check. Nie zmieniano `.env`, nie dodawano sekretów ani trwałych fixture.

Nie wykonano commit, push, reset ani odwracania zastanych zmian. Zastane usunięcia/niedostępne fixture `.pytest_tmp` pozostawiono nietknięte. Ogólny git diff sygnalizuje odmowę dostępu do tych wcześniejszych fixture; kontrola whitespace plików zakresu Tasku przechodzi. Git zgłasza również standardową konwersję LF → CRLF dla zmienionych plików tekstowych.

## Odstępstwa

Brak odstępstw funkcjonalnych lub architektonicznych. Nie dodano opcjonalnego wyszukiwania produktu. Nie rozpoczęto kolejnego Tasku ani szerszej akceptacji E2E Sprintu.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
