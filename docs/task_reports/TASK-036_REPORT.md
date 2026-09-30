# TASK-036 REPORT

STATUS:
DONE

CHANGED:
- UI: upload PDF w formularzu pierwszego SDS i nowej rewizji.
- Application: use case importu, kontrakt storage i metadana `original_filename`.
- Filesystem: adapter kontrolowanego zapisu i kompensacyjnego usuwania.
- DB wiring: zachowany istniejący use case i transakcja SDS; zapis oryginalnej nazwy pliku.
- Tests: przypadki UI, filesystem, błędów i PostgreSQL.

IMPLEMENTED:
- Upload pozostaje w pamięci do jawnego zatwierdzenia formularza; dla nowego uploadu dane SDS są uzupełniane ręcznie.
- Walidacja nazwy `.pdf` bez ścieżki, niepustej zawartości i sygnatury `%PDF-`.
- Zapis wyłącznie do `SDS_ROOT_PATH/imported/<uuid>.pdf`, z kontrolą katalogu root i docelowej ścieżki.
- Tworzenie exclusive z ograniczonym ponawianiem po kolizji; bez nadpisywania istniejących plików.
- Po potwierdzeniu istnienia PDF rejestracja przez dotychczasowe use case i commit PostgreSQL.
- Przy niepowodzeniu rejestracji rollback DB i usunięcie tylko pliku utworzonego w tej operacji. Błąd cleanup zgłasza `relative_path` osieroconego pliku.
- Po skutecznym commit plik pozostaje; lifecycle `CURRENT/ARCHIVED` zachowany, także dla `revision = NULL`.
- Zachowany dotychczasowy wybór pliku z katalogu SDS i istniejący odczyt draftu.

VALIDATION:
- Focused unit i Streamlit/AppTest: 44 passed, 1 skipped (dowiązania symboliczne niedostępne w środowisku Windows).
- PostgreSQL integration dla importu: 2 passed na jednorazowym klastrze PostgreSQL, usuniętym po teście.
- Powiązana regresja SDS: 4 passed na osobnym jednorazowym klastrze PostgreSQL.
- Filesystem: izolowane katalogi `tmp_path`; sprawdzone walidacja wejścia, kolizje, brak overwrite, brak root, awaria rejestracji, compensation i orphan path.
- `git diff --check` dla repozytorium z pominięciem wcześniejszego `.pytest_tmp`: PASS. Nowe pliki sprawdzone pod kątem końcowych spacji: PASS.

DATA SAFETY:
- operator data preserved: YES. Wstępny przebieg integracyjny na skonfigurowanej bazie korzystał z transakcji z rollback; końcowe przebiegi wykonano na izolowanych klastrach.
- orphan test files after validation: NONE; wszystkie testowe PDF leżały w katalogach tymczasowych.

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- parser change: NO
- lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- Wstępny test integracyjny użył skonfigurowanej bazy z rollback zamiast od początku izolowanego klastra. Nie utrwalił danych; walidację powtórzono na izolowanym PostgreSQL.
- Plik `GOV-001_Zasady_wspolpracy_v1.0-approved.md` nie występuje w bieżącym repozytorium; zastosowano dostarczone instrukcje `AGENTS.md` oraz `GOV-002`.

NEXT:
- READY FOR CERBERUS REVIEW
