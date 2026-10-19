# PATCH-015 REPORT

STATUS:
DONE

CHANGED:
- `app/presentation/streamlit/product_registry.py`
- `app/presentation/streamlit/main.py`
- `app/presentation/streamlit/add_sds.py`
- `tests/unit/test_product_registry_view.py`
- `tests/unit/test_streamlit_add_sds.py`
- `docs/task_reports/PATCH-015_REPORT.md`

IMPLEMENTED:
- Products list-only view: tabela z dotychczasowymi kolumnami, wyszukiwaniem, sortowaniem i jawną akcją otwarcia karty po wyborze wiersza; bez szczegółów pod tabelą.
- Product Card view: wybrany `product_id`, powrót do listy i zachowanie wyszukiwania oraz sortowania.
- Header actions: warunkowe uzupełnienie kodu, korekta tożsamości i nowa rewizja SDS; usuwanie produktu w rozwijanej sekcji „Więcej akcji”.
- Compact sections: Tożsamość produktu i SDS/BHP obok siebie, pozioma tabela miejsc stosowania, dwukolumnowe dane administracyjne z przyciskiem edycji.
- Optional manufacturer code label: „Kod producenta — opcjonalne” w formularzu Dodaj SDS.

VALIDATION:
- Focused AppTest i related UI regression: `32 passed` (`test_product_registry_view.py`, `test_streamlit_add_sds.py`, `test_streamlit_shell_unit.py`).
- `git diff --check` dla zmienionych plików: PASS.

SCOPE:
- Domain change: NO
- Application change: NO
- schema change: NO
- migration: NONE
- new dependencies: NO

DEVIATIONS:
- Akcja „Otwórz kartę produktu” jest pod tabelą dla świadomie wybranego wiersza, zamiast w osobnej kolumnie Akcje.
- Po powrocie zachowane są wyszukiwanie i sortowanie; zaznaczenie wiersza może wymagać ponownego wyboru.
- Fizyczny przegląd przy zoom 100% pozostaje do wykonania przez Cerberus + Architekta.

NEXT:
- READY FOR PHYSICAL UX REVIEW
