# TASK-020 — Streamlit „Dodaj SDS”

## 1. Status

`DONE`

Dodano cienki widok Streamlit spinający `PrepareSdsDraft` i `AcceptSds`. Nie rozpoczęto TASK-021.

## 2. Zmienione pliki

- `app/presentation/streamlit/app.py`
- `app/presentation/streamlit/add_sds.py`
- `app/presentation/streamlit/composition.py`
- `tests/unit/test_streamlit_add_sds.py`
- `tests/unit/test_streamlit_shell_unit.py`
- `tests/integration/test_streamlit_shell.py`
- `docs/task_reports/TASK-020_REPORT.md`

Nie dodano zależności, migracji, tabel ani zmian Domain/ORM/schema.

## 3. Widok i wybór PDF

Sekcja `Dodaj SDS` jest dostępna w nawigacji obok `Produkty` i `Stanowiska`. Kompozycja udostępnia listę istniejących plików `.pdf` znalezionych rekurencyjnie w skonfigurowanym `SDS_ROOT_PATH`. UI operuje na ścieżce względnej. Nie ma uploadu ani kopiowania, przenoszenia, zmiany nazwy lub usuwania plików.

## 4. PrepareSdsDraft i stan sesji

Po kliknięciu `Odczytaj dane` widok wywołuje `composition.prepare_sds_draft`, które przez istniejące `SdsFileValidator` i `PdfSdsExtractor` deleguje do `PrepareSdsDraft`. Wynik `SdsDraft` jest przechowywany wyłącznie pod kluczem `add_sds_draft` w `st.session_state`. Nie ma trwałego draftu w bazie.

## 5. Formularz

Formularz udostępnia edycję:

- danych produktu/SDS: nazwa, kod producenta, producent, zastosowanie, ograniczenie, rewizja, opcjonalna data wydania,
- `SAFETY_PROFILE`: definicja, klasyfikacja CLP, hasło, kody H, uzupełniające kody H oraz wszystkie zatwierdzone statusy,
- `SDS_COMPONENTS`: nazwa, CAS, WE, REACH, stężenie, klasyfikacja i kody H.

Statusy korzystają wyłącznie z `YES`, `NO`, `NO_DATA`, `NOT_APPLICABLE`. Można zmienić, usunąć lub dodać składnik. Brak danych parsera pozostaje edytowalnym pustym polem.

## 6. Akceptacja i anulowanie

`Zapisz / Akceptuj` buduje `AcceptSdsInput` z aktualnego draftu i wywołuje wyłącznie `composition.accept_sds`, która przekazuje operację do `AcceptSds` i istniejącego `TransactionExecutor`. UI nie wykonuje SQL, commit/rollback ani własnego ustawiania statusów.

Po sukcesie draft jest usuwany, a użytkownik otrzymuje komunikat o zapisaniu SDS i oczekiwaniu produktu na decyzję BHP. `Anuluj` usuwa draft ze stanu sesji i nie wywołuje `AcceptSds`.

## 7. Obsługa błędów

Kontrolowane błędy walidacji, ścieżki, języka, danych i persystencji są prezentowane przez `st.error`. UI nie pokazuje stack trace, SQL, `DATABASE_URL` ani sekretów. Błąd nie jest prezentowany jako sukces.

## 8. Testy UI

Dodano AppTest obejmujący:

- wybór i odczyt pliku,
- wypełnienie formularza draftem,
- ręczną korektę produktu,
- przekazanie korekty do `AcceptSdsInput`,
- wywołanie akceptacji jeden raz i wyczyszczenie draftu,
- anulowanie bez wywołania akceptacji.

Wynik focused UI tests: `6 passed`.

## 9. Smoke/E2E SDS 30470

Nie wykonano osobnego smoke testu UI na fixture 30470, ponieważ zgodnie z TASK-019 aplikacja wymaga pliku fizycznie pod `SDS_ROOT_PATH`, a UI nie kopiuje fixture z `docs/tasks`. Odczyt fixture i backendowy zapis są pokryte testami TASK-018/TASK-019. Ograniczenie pozostaje zgodne z zasadą produkcyjną.

## 10. Walidacja końcowa

- Pełny pytest: `119 passed`.
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS, brak `SAWarning`.
- `alembic current`: `e0dd7d6468bf (head)`.
- `alembic check`: `No new upgrade operations detected.`
- Diagnostyka zmienionych plików: brak błędów.
- Nie zmieniono Domain, ORM, Alembic ani PostgreSQL schema.
- Brak nowych zależności.

## 11. Architektura

```text
Streamlit
  -> ShellComposition
  -> PrepareSdsDraft / AcceptSds
  -> Infrastructure adapters
  -> TransactionExecutor / PostgreSQL
```

Widok nie importuje modeli ORM, repozytoriów, SQLAlchemy, psycopg ani `pypdf`. Adaptery są składane w `composition.py`.

## 12. Git / bezpieczeństwo

Nie wykonano commit ani push. Nie dodano sekretów, nowych fixture PDF/MSG, dumpów ani backupów. Istniejące zmiany wcześniejszych tasków pozostały nietknięte. `git diff --check` i `git diff --cached --check` należy potwierdzić w końcowej kontroli.

## 13. Odstępstwa i ryzyka

Widok jest celowo minimalny i nie rozstrzyga duplikatów, producenta, bezpieczeństwa chemicznego ani BHP. Te decyzje pozostają w Application/Core. Pełny manual smoke UI z 30470 wymaga wcześniejszej kontrolowanej obecności fixture w `SDS_ROOT_PATH`; aplikacja nie wykonuje takiego kopiowania.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-021.
