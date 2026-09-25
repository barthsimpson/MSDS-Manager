# TASK-029 REPORT

STATUS:
DONE

CHANGED:
- `main.py`: szeroki layout Streamlit.
- `product_registry.py`: zwarta tabela, wybór wiersza, sekcje szczegółów, etykiety statusów i komunikat rewizji bez UUID.
- `add_sds.py`: komunikat zapisu pierwszego SDS bez UUID.
- Testy UI produktu i komunikatu dodania SDS.

UI RESULT:
- wide layout: YES
- product table first: YES
- UUID hidden in normal UI: YES
- product selection: ROW
- details structured: YES
- edit action preserved: YES
- new SDS revision action preserved: YES
- delete confirmation preserved: YES
- user-facing status labels: YES
- success messages without UUID: YES

VALIDATION:
- focused AppTests: PASS — ekran pusty, tabela, wybór rekordu, szczegóły, akcje, statusy i komunikaty.
- related regression: PASS — 22 testy UI i powiązanych akcji edit/revision/delete.
- integration: NOT REQUIRED — composition niezmieniony.

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- lifecycle changes: NONE

RISKS / DEVIATIONS:
- SDS/BHP są odczytywane z istniejącego modelu nadzorczego. Gdy odczyt się nie powiedzie, rejestr nadal działa, a kolumny SDS/BHP pokazują brak danych i ostrzeżenie.
- AppTest nie udostępnia kliknięcia wiersza `st.dataframe`; test szczegółów wstrzykuje zdarzenie wyboru. Fizyczny walkthrough pozostaje do wykonania przez Architekta Operacyjnego.
- `add_sds.py` zmieniono wyłącznie w zakresie komunikatu sukcesu wymaganego przez Task; formularz i workflow pozostały bez zmian.
- W katalogu `.pytest_tmp` były już lokalne usunięcia śledzonych plików PDF; nie były częścią TASK-029.

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-030.
