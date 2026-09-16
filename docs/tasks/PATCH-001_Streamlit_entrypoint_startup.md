# PATCH-001 — Naprawa uruchamiania Streamlit

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT

## GOAL

Usunąć błąd fizycznego uruchomienia aplikacji:

```text
ModuleNotFoundError:
No module named 'app.presentation'; 'app' is not a package
```

Zaobserwowany przy:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/app.py
```

Zwykły Python poprawnie rozpoznaje pakiet projektu:

```text
app -> <repo>\app\__init__.py
app.__path__ -> <repo>\app
```

Hipoteza robocza: kolizja nazwy pakietu `app` z entry pointem `app.py` podczas uruchamiania przez Streamlit.

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:
- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów ani raportów TASK-026..028, jeśli nie pojawi się konkretny konflikt.

## KNOWN STARTING POINTS

```text
app/presentation/streamlit/app.py
app/presentation/streamlit/
```

Najpierw zweryfikuj lokalnie hipotezę konfliktu nazwy. Nie wykonuj repo-wide architecture review.

## EXPECTED CHANGE SURFACE

Preferowane rozwiązanie:

```text
app/presentation/streamlit/app.py
→ app/presentation/streamlit/main.py
```

Zaktualizuj wyłącznie bezpośrednie odwołania do starego entry pointu, jeśli istnieją i są potrzebne do poprawnego uruchomienia/testów.

Nie zmieniaj composition ani logiki ekranów, chyba że sama zmiana nazwy ujawni bezpośrednio konieczną korektę importu.

## DO

1. Potwierdź przyczynę błędu minimalną inspekcją.
2. Jeżeli potwierdzona jest kolizja `app` / `app.py`, zmień nazwę entry pointu na `main.py`.
3. Zachowaj dotychczasową zawartość i zachowanie aplikacji.
4. Zaktualizuj tylko konieczne referencje do ścieżki startowej.
5. Potwierdź, że aplikacja może wystartować poleceniem:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/main.py
```

Walidacja startu nie wymaga długotrwałego ręcznego działania serwera. Wystarczy potwierdzić brak wcześniejszego błędu importu i poprawne wejście aplikacji w normalny startup.

## DO NOT

Nie:
- przebudowuj UI,
- zmieniaj funkcji aplikacji,
- refaktoryzuj composition,
- zmieniaj Application/Domain/Infrastructure,
- zmieniaj PostgreSQL/schema/Alembic,
- dodawaj dependencies,
- poprawiaj innych zauważonych problemów,
- wykonuj repo-wide review,
- analizuj historii Git,
- rozpoczynaj kolejnego Tasku.

Jeżeli hipoteza kolizji nazwy okaże się błędna i naprawa wymaga szerszej zmiany:

```text
STOP / BLOCKED
```

Nie rozszerzaj samodzielnie PATCH-a.

## VALIDATION — LEVEL 1

Wykonaj tylko walidację proporcjonalną do zmiany:

1. focused testy dotyczące Streamlit shell/entry pointu, jeśli istnieją,
2. fizyczny smoke-start nowego entry pointu,
3. potwierdzenie braku `ModuleNotFoundError`.

Nie uruchamiaj automatycznie:
- pełnego pytest,
- TASK-026 verification,
- PostgreSQL integration suite,
- Alembic current/check,
- nowego klastra PostgreSQL.

Jeżeli istniejący focused test wymaga bazy tylko z powodu sposobu konstrukcji testu, użyj istniejącego mechanizmu — nie buduj nowego.

## STOP CONDITIONS

STOP, jeżeli:
- rename nie usuwa problemu,
- wymagane są zmiany poza warstwą Streamlit/bezpośrednimi referencjami,
- pojawia się nowy problem architektoniczny,
- potrzebna byłaby zmiana Core/schema/dependencies.

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-001_REPORT.md
```

Format:

```text
STATUS: DONE / BLOCKED

CAUSE:
- ...

CHANGED:
- ...

VALIDATION:
- focused tests: ...
- physical Streamlit startup: PASS / FAIL
- ModuleNotFoundError: RESOLVED / NOT RESOLVED

SCOPE:
- business logic: unchanged
- Core/schema/Alembic: unchanged
- dependencies: unchanged

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
```

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-001.
```
