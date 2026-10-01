# TASK-040 REPORT

STATUS:
DONE

CHANGED:
- UI: `app/presentation/streamlit/product_registry.py`, `composition.py`
- Application: `app/application/use_cases/get_current_sds_file.py`
- Filesystem: `app/infrastructure/filesystem/sds_pdf_storage.py`
- Read wiring: `app/infrastructure/db/repositories/current_sds_query.py`
- Tests: `tests/unit/test_task040_current_sds_download.py`

IMPLEMENTED:
- Pobieranie wyłącznie CURRENT SDS wskazanego produktu, z nazwą `original_filename`.
- Kontrolowany odczyt przez `SDS_ROOT_PATH + relative_path`; odrzucenie ścieżek absolutnych, UNC, traversal i ścieżek rozwiązanych poza rootem.
- MISSING bez zastępowania dokumentu i bez zmian w rekordzie; odczyt bez modyfikacji pliku.

VALIDATION:
- Focused Application/filesystem, Streamlit/AppTest i regresja widoku/importu: 50 passed, 2 skipped (`pytest` z izolowanym `--basetemp`).
- Izolowany katalog tymczasowy dla filesystem tests; bez danych operatora.
- `git diff --check` dla zmienionych śledzonych plików: PASS. Nowe pliki nie są jeszcze śledzone przez Git.

DATA SAFETY:
- operator data preserved: YES

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- SDS lifecycle change: NO
- new dependencies: NO

DEVIATIONS:
- Test rzeczywistego symlinku poza rootem pominięty tam, gdzie Windows nie pozwala go utworzyć; test wymuszonego `resolve()` poza rootem przeszedł.
- `GOV-001_Zasady_wspolpracy_v1.0-approved.md` nie występuje w repozytorium; zastosowano `AGENTS.md` i GOV-002.

NEXT:
- READY FOR CERBERUS REVIEW
