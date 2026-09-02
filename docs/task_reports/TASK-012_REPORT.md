# TASK-012 — raport wykonania

## 1. Status

**DONE** — minimalny shell Streamlit został utworzony i uruchomiony lokalnie.

## 2. Stan wejściowy

- CORE: v1.2-approved.
- Zweryfikowany pion Application → PostgreSQL z TASK-011.
- Testy bazowe: 91 passed.
- Alembic revisions: 4.
- PostgreSQL: `d2b4f6a8c190 (head)`.
- Tabele aplikacyjne: 9.
- Drift: brak.
- Rekordy biznesowe: 0.

## 3. Pliki presentation

Utworzono:

- `app/presentation/streamlit/app.py` — minimalny widok i entry point,
- `app/presentation/streamlit/composition.py` — composition root.

Dodano również testy presentation:

- `tests/unit/test_streamlit_shell_unit.py`,
- `tests/integration/test_streamlit_shell.py`.

Rozszerzono istniejący test granic architektury bez jego osłabiania.

## 4. Entry point Streamlit

Aplikację uruchamia polecenie:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/app.py
```

Nie wymaga ono zmiany systemowego PATH.

## 5. Struktura shell

Shell ustawia konfigurację strony, wyświetla tytuł `MSDS Manager`, tworzy
minimalną nawigację i renderuje jeden z dwóch neutralnych placeholderów. Nie ma
dashboardu, tabeli produktów, szczegółów ani formularzy.

## 6. Nawigacja Produkty/Stanowiska

Sidebar radio zawiera dokładnie:

```text
Produkty
Stanowiska
```

Test Streamlit AppTest przełącza obie wartości i potwierdza odpowiednie
nagłówki. UI nie zawiera przycisków `Dodaj produkt`, `Dodaj nowy SDS` ani innych
operacji zapisujących.

## 7. Composition root

`build_shell_composition()` składa:

```text
Settings
→ Engine
→ session factory
→ SqlAlchemyProductRepository
→ ListProducts
→ Streamlit shell
```

Engine jest zwalniany po renderowaniu. Composition root należy do zewnętrznej
warstwy presentation i nie zmienia zależności Application/Domain.

## 8. Settings

Użyto wyłącznie istniejącego `load_settings()` z TASK-002. Nie utworzono
drugiego parsera `.env`, nie użyto `python-dotenv` i nie zahardkodowano adresu
bazy, haseł ani ścieżek dokumentów.

## 9. Application/use case'y

Composition root wykonuje jeden bezpieczny, odczytowy `ListProducts` w celu
potwierdzenia połączenia całego pionu. Widok nie wywołuje repository bezpośrednio
i nie interpretuje danych biznesowo. Nie zaimplementowano Product Registry View.

## 10. Pusta baza

Pusta lista z `ListProducts` jest traktowana jako poprawny wynik. AppTest
uruchamia oba ekrany przy 0 rekordach. Start i nawigacja nie tworzą seeda ani
żadnych danych; liczba rekordów przed i po teście pozostaje równa 0.

## 11. Błędy konfiguracji/DB

Composition root przechwytuje `ConfigurationError`, `SQLAlchemyError`,
`OSError` i `ImportError`, zwalnia utworzony Engine i zwraca kontrolowany
`ShellInitializationError`. UI pokazuje stały komunikat:

```text
Nie udało się uruchomić aplikacji. Sprawdź konfigurację i połączenie z bazą.
```

Test z błędną konfiguracją potwierdza brak tracebacku w UI oraz brak testowego
sekretu i pełnego adresu bazy w komunikacie.

## 12. Brak logiki biznesowej w UI

`app.py` odpowiada tylko za tytuł, nawigację, wywołanie composition root,
placeholdery i kontrolowany błąd. Nie zawiera SQL, modeli ORM, Session,
commit/rollback, walidacji quantity ani reguł statusowych. Nie wykonuje zapisu.

## 13. Testy presentation

Dodano 4 testy:

- bezpieczny import bez uruchamiania composition root,
- kontrolowany i pozbawiony sekretu błąd konfiguracji,
- render i nawigacja obu sekcji na pustej bazie bez zapisu,
- render kontrolowanego błędu inicjalizacji w Streamlit.

Wynik: **4 passed**.

## 14. Testy architektury

Kontrola AST potwierdza dodatkowo:

- Application nie importuje presentation ani Streamlit,
- Domain nie importuje presentation ani Streamlit,
- dotychczasowe zakazy importu infrastructure/SQLAlchemy/psycopg pozostają,
- presentation może złożyć Application i infrastructure w composition root.

Wynik kontroli architektury: **3 passed**.

## 15. Manual Streamlit smoke

Uruchomiono rzeczywisty serwer headless na lokalnym porcie testowym. Streamlit
wystartował bez wyjątku i podał lokalny adres. Endpoint zdrowia zwrócił:

```text
HTTP 200
ok
```

Następnie proces został kontrolowanie zakończony. Tytuł, nawigację obu sekcji,
pusty stan, brak niedozwolonych przycisków i brak zapisu potwierdził dodatkowo
rzeczywisty runtime Streamlit AppTest.

## 16. Pełny pytest / `SAWarning`

Uruchomiono:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **95 passed**, kod wyjścia 0, brak `SAWarning`.

## 17. Brak zmian Domain/Application/ORM/schema

TASK-012 nie zmienił Domain, kontraktów Application, repozytoriów, ORM,
constraints ani konfiguracji Alembic. Nie utworzono migracji #5 ani nowej
tabeli. Zmiany robocze widoczne w tych obszarach pochodzą z wcześniejszych
zaakceptowanych Tasków i zostały zachowane.

## 18. `alembic current`

```text
d2b4f6a8c190 (head)
```

Liczba rewizji: 4.

## 19. `alembic check`

```text
No new upgrade operations detected.
```

Rzeczywisty drift: brak.

## 20. Finalny stan PostgreSQL

- Current/head: `d2b4f6a8c190`.
- Tabele aplikacyjne: 9.
- Rekordy w każdej z 9 tabel: 0.
- Start/nawigacja pozostawiły dane: nie.
- Constraints: bez zmian.

## 21. Git/bezpieczeństwo

- `git diff --check`: bez błędów, tylko ostrzeżenia LF/CRLF,
- `git diff --cached --check`: bez błędów,
- `.env`: ignorowany i nietrackowany,
- pełny `DATABASE_URL` i sekrety nie występują w UI ani raporcie,
- dumpy, backupy, PDF i MSG: brak,
- nowe biblioteki i zmiany `pyproject.toml`: brak,
- commit/push: nie wykonano,
- proces manualnego smoke został zakończony.

## 22. Odstępstwa

Brak.

## 23. Problemy/ryzyka

Brak blockerów. Shell świadomie nie utrzymuje globalnego cache Engine; przy
każdym rerun składa mały odczytowy pion i zwalnia zasoby. Optymalizacja cyklu
życia zasobów może zostać rozważona dopiero przy rzeczywistych widokach, bez
rozszerzania obecnego minimalnego zakresu.

## 24. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-013.
