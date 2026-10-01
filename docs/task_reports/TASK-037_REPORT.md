# TASK-037 REPORT

STATUS:
DONE

CHANGED:
- UI: neutralny wybór dowodu, rozłączne tryby istniejący/upload, pobieranie i historia z oznaczeniem MISSING.
- Application: import dowodu z kompensacją, lista istniejących dowodów i kontrolowany odczyt.
- filesystem: dedykowany adapter BHP z allowlist, bezpiecznymi ścieżkami i zapisem create-exclusive.
- DB wiring/read: weryfikacja PRODUCT/CURRENT SDS przed importem, nazwy źródłowe i historia decyzji w odczycie.
- tests: adapter, use case, Streamlit/AppTest, PostgreSQL integration oraz skrypt izolowanej walidacji.

IMPLEMENTED:
- Ekran startuje z `BRAK WYBORU`; pierwszy plik nie jest zaznaczany automatycznie, a zapis bez dowodu jest odrzucany.
- Istniejący dowód jest wskazywany jawnie i walidowany pod kątem dostępności oraz położenia w `BHP_EVIDENCE_ROOT_PATH`; nie powstaje jego kopia.
- Upload pozostaje w pamięci do Submit. Dopuszczalne rozszerzenia `.msg`, `.pdf`, `.jpg`, `.jpeg`, `.png` są sprawdzane bez polegania na MIME; pusty plik i nieobsługiwany format są odrzucane.
- Nowy dowód trafia do `imported/<storage_uuid>.<extension>` przez `xb`, bez nadpisania. Nazwa źródłowa jest osobną metadaną w `DECISION_EVIDENCE`.
- Ścieżki bezwzględne, UNC i traversal są odrzucane. Import nie może wyjść poza resolved root.
- PRODUCT/CURRENT SDS są sprawdzane przed filesystem write. Po błędzie DB następuje rollback i usunięcie tylko pliku z niezakończonej operacji; błąd cleanup zgłasza orphan relative_path. Po COMMIT plik pozostaje.
- Dowód zarejestrowanej decyzji można pobrać w każdym dopuszczonym formacie. Brak fizycznego pliku daje czytelny stan MISSING bez usunięcia decyzji i bez podmiany dowodu.
- Zachowano relację decyzja:dowód 1:1 oraz korektę CURRENT/SUPERSEDED i APPROVED/REJECTED.

VALIDATION:
- 60 focused/related tests PASS w odizolowanym PostgreSQL, w tym Streamlit/AppTest, import, korekta, rollback, kompensacja, formaty, path safety, no-overwrite i MISSING.
- `alembic current` = `b379f54c12a0`; `alembic check` = PASS w izolowanym środowisku.
- `git diff --check` = PASS dla śledzonych zmian z wyłączeniem zastanych usunięć `.pytest_tmp`; nowe pliki kodu sprawdzono osobno pod kątem whitespace.

DATA SAFETY:
- operator data preserved: YES — po walidacji nadal 3 rekordy evidence z identycznym odciskiem dotychczasowych pól i revision `b379f54c12a0`.
- orphan test files after validation: NONE

SCOPE:
- schema change w TASK-037: NO (fundament i migrację wykonano w zaakceptowanych TASK-038/039)
- migration w TASK-037: NONE
- Core change w TASK-037: NO
- SDS lifecycle change: NO
- BHP lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- NONE

NEXT:
- READY FOR CERBERUS REVIEW
