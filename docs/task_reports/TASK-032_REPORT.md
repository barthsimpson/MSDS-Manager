# TASK-032 REPORT

STATUS:
BLOCKED — SPRINT-006 NOT READY FOR CLOSURE

BASELINE:
- git status: zastane zmiany TASK-031, nieśledzone pliki TASK-031/TASK-032 oraz 9 usuniętych śledzonych PDF w `.pytest_tmp`; TASK-032 ich nie zmienił.
- operator data preserved: YES — walidację uruchomiono na tymczasowym klastrze PostgreSQL.
- test isolation: istniejący `scripts/verify_task026.py`; osobny klaster, migracje, katalogi plików i `--basetemp`. Skrypt zatrzymał klaster i usunął jego katalog po błędzie.

SPRINT-006 WORKFLOW ACCEPTANCE:
- product register: wcześniejsze AppTests przeszły w pełnym zestawie; Sprint 2 E2E FAIL.
- product details: wcześniejsze AppTests przeszły; Sprint 2 E2E FAIL.
- first SDS: część testów przeszła; Sprint 3 E2E FAIL.
- manual fallback: testy jednostkowe/AppTests przeszły; pełne acceptance BLOCKED.
- new SDS revision: test `test_add_revision_preserves_product_usage_and_previous_bhp` FAIL.
- BHP decision: Sprint 4 E2E FAIL.
- product status refresh: niepotwierdzony w pełnym E2E; test Sprint 4 oczekiwał komunikatu z `ACTIVE`, którego nie otrzymał.
- product correction: testy objęte regresją; pełna akceptacja nieukończona.
- safe delete: test `test_delete_product_removes_owned_records_and_preserves_shared_data` FAIL.
- usage locations: testy UI/read model przeszły; Sprint 2 E2E FAIL.
- peak/monthly: PostgreSQL read model PASS w fazie integration; pełna akceptacja BLOCKED.
- supervisory PRODUCT x LOCATION: focused/integration PASS; nie stanowi to zaliczenia całego Sprintu.
- filters: AppTests przeszły w pełnym zestawie; pełna akceptacja BLOCKED.

UI ACCEPTANCE:
- wide layout: potwierdzone w kodzie (`layout="wide"`) i wcześniejszych testach.
- table-first: focused AppTests PASS; Sprint 2 E2E FAIL.
- UUID hidden: focused AppTests PASS; stary test Sprint 2 nadal oczekuje `product_id` w tabeli, więc E2E FAIL.
- compact forms: focused AppTests PASS; pełny checkpoint BLOCKED.
- required fields visible: focused AppTests PASS; pełny checkpoint BLOCKED.
- no stale state: niepotwierdzone w Sprint 4 E2E (FAIL).
- technical paths secondary: focused AppTests PASS; pełny checkpoint BLOCKED.

NO_DATA / ERROR STATES:
- Istniejące testy pustej bazy, braków SDS/BHP/lokalizacji/daty/rewizji/zużycia/plików i błędów odczytu były częścią pełnego zestawu; 208 testów przeszło, ale przy 5 FAIL nie uznaję całej grupy za zaliczoną.
- Brak skipów w izolowanym pełnym przebiegu; baza testowa była pusta na starcie.

FULL VALIDATION:
- pytest: FAIL — 5 failed, 208 passed, 0 skipped; uruchomiono `-W error::sqlalchemy.exc.SAWarning` na izolowanym PostgreSQL.
- SAWarning: brak zgłoszonego SAWarning w przebiegu, ale wymagany warunek 0 failed nie został spełniony.
- E2E: FAIL — Sprint 2, Sprint 3, Sprint 4 oraz testy rewizji i usunięcia; szczegóły poniżej.
- PostgreSQL integration: focused supervisory 10 passed; pełny zestaw 5 failed.
- Alembic current: NOT RUN — skrypt przerwał po błędzie pełnego pytest.
- Alembic check: NOT RUN — skrypt przerwał po błędzie pełnego pytest.
- schema drift: NOT VERIFIED; `alembic upgrade head` na tymczasowym klastrze PASS.
- constraints/integrity: częściowe pokrycie przez 208 zaliczonych testów; pełny warunek checkpointu niezaliczony.
- cleanup: tymczasowy klaster został zatrzymany i usunięty w `finally`; sprawdzenie końcowych liczników fixture nie zostało wykonane, bo skrypt przerwał przed tym etapem.

FAILURES — AUTOMATED ACCEPTANCE:
1. `tests/integration/test_patch006_sds_revision.py::test_add_revision_preserves_product_usage_and_previous_bhp` — FAIL; nie ustalono przyczyny bez ponownego wykonywania po warunku STOP.
2. `tests/integration/test_patch008_delete_product.py::test_delete_product_removes_owned_records_and_preserves_shared_data` — FAIL; nie ustalono przyczyny bez ponownego wykonywania po warunku STOP.
3. `tests/integration/test_task016_acceptance.py::test_task016_sprint2_end_to_end_acceptance` — FAIL; test sprawdza obecność `product_id` w tabeli, podczas gdy zatwierdzony SPRINT-006 ukrywa UUID w zwykłym widoku.
4. `tests/integration/test_task021_sprint3_acceptance.py::test_task021_real_sds_ui_to_postgresql_and_second_current` — FAIL; AppTest zgłosił `ValueError: '30470-second.pdf' is not in list` dla kontrolki klasyfikacji.
5. `tests/integration/test_task025_sprint4_acceptance.py::test_task025_bhp_ui_postgresql_acceptance` — FAIL; po zapisie nie było oczekiwanego komunikatu sukcesu zawierającego `ACTIVE`.

ARCHITECTURE:
- Streamlit SQL/ORM: ekranowe moduły nie wykonują SQL ani nie importują modeli ORM; istniejący `composition.py` wiąże adaptery przez SQLAlchemy.
- lifecycle in UI: brak zmian w TASK-032; niepotwierdzony końcowym E2E.
- Core change: NONE w TASK-032.
- schema change: NONE w TASK-032.
- dependencies: NONE w TASK-032.

GIT / SECURITY:
- git diff check: exit 0, lecz Git zgłosił `Permission denied` przy zastanych usuniętych plikach `.pytest_tmp`; `git diff --cached --check` bez uwag.
- .env: ignorowany przez `.gitignore`.
- secrets: brak nowych zmian w TASK-032 poza tym raportem; nie ujawniano zawartości `.env`.
- unintended PDF/MSG/dumps: nie dodano; zastane usunięcia PDF w `.pytest_tmp` pozostały nietknięte.
- commit/push: NONE.

SPRINT-006 DoD:
1. wide/compact layout: częściowo potwierdzone, checkpoint BLOCKED.
2. Products table-first: focused PASS, E2E FAIL.
3. UUID hidden: focused PASS, istniejący E2E FAIL.
4. Add SDS compact sections: focused PASS, pełny E2E FAIL.
5. required fields visible: focused PASS, pełny checkpoint BLOCKED.
6. unknown SDS date not defaulted to today: focused PASS, pełny checkpoint BLOCKED.
7. BHP state refresh after save: E2E FAIL.
8. usage assignments table + separate add/edit: focused PASS, Sprint 2 E2E FAIL.
9. supervisory PRODUCT x LOCATION: focused/integration PASS.
10. peak/monthly visible per location: focused/integration PASS.
11. product without location preserved: focused/integration PASS.
12. filters work: AppTests PASS.
13. no Core/schema changes: w TASK-032 YES; wcześniejsze zmiany nie były korygowane.
14. full validation PASS: NO.
15. physical Sprint Review remains for Architekt Operacyjny: YES.

KNOWN BACKLOG — NOT BLOCKING:
- UI-11, DATA-01, UI-12, UI-13, DOC-01, UI-14 / DOC-02, Stage 2 parser, R8, REACH.

RISKS / DEVIATIONS:
- Zgodnie z TASK-032 nie poprawiono błędów ani testów po wykryciu FAIL.
- Nie można uczciwie potwierdzić gotowości do zamknięcia Sprintu bez usunięcia pięciu porażek i ponownego pełnego checkpointu.
- Fizyczny przegląd UI nadal należy do Architekta Operacyjnego.

CLOSURE RECOMMENDATION:
NOT READY — pełny pytest i krytyczne E2E mają 5 porażek.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO SPRINTU.
