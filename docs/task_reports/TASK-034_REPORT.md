# TASK-034 REPORT

STATUS: **DONE**

CHANGED:
- Application: DTO szczegółów przypisania udostępnia techniczne unit_id obok kodów; istniejące use case'y Assign/Update i walidacja ACTIVE zostały wykorzystane bez zmiany reguł.
- Repositories/read models: Product details zwraca unit_id oraz code dla obu pól ilościowych; supervisory nadal zwraca code.
- Streamlit: formularze dodawania i edycji wybierają jednostki wyłącznie z list_active(); kod jest etykietą, UUID nie jest pokazywany. Brakujące jednostki są walidowane przed zapisem.
- Tests: rozszerzono testy Application, AppTest i PostgreSQL dla ACTIVE/INACTIVE, NULL/0, kodów odczytu i historii; dostosowano powiązany fixture supervisory do schema TASK-033.

IMPLEMENTED:
- ACTIVE unit selection: MAX i monthly korzystają z jednego słownika aktywnych jednostek.
- MAX validation: brak wyboru odrzucany w UI; Application odrzuca brak, nieistniejące i INACTIVE unit_id.
- Monthly NULL/0 validation: brak wartości zapisuje NULL/NULL; 0 wymaga jednostki ACTIVE.
- Product details display: kod jednostki w tabeli, unit_id dostępne wyłącznie dla logiki edycji.
- Supervisory display: kody jednostek, bez UUID.
- History unit preservation: snapshoty przechowują oba unit_id, w tym po zmianie samej jednostki.

VALIDATION:
- Focused + related regression: 84 passed, 1 skipped. Pominięto zastany test wymagający całkowicie pustej bazy operatora; pozostałe testy przeszły.
- PostgreSQL integration: PASS; current/history, odczyt INACTIVE, Product details, supervisory i 0 != NULL potwierdzone w transakcjach wycofywanych po testach.
- Streamlit/AppTest: PASS; wybór ACTIVE, brak free-text, wymagane jednostki, edycja INACTIVE i niewidoczne UUID.
- SAWarning: NONE przy -W error::sqlalchemy.exc.SAWarning.
- Po walidacji: product_usage_locations = 0, product_usage_location_history = 0; pięć jednostek nadal ACTIVE.
- git diff --check dla zmienionych śledzonych plików: PASS.

SCOPE:
- schema change: NO
- migration: NONE w TASK-034
- conversion engine: NONE
- legacy mapping: NONE
- new dependencies: NONE

RISKS / DEVIATIONS:
- Pierwszy przebieg integracyjny natrafił na zastane ograniczenie dostępu do .pytest_tmp. Powtórzono go z osobnym katalogiem --basetemp w .venv; zestaw przeszedł.
- Nie wykonano trwałej modyfikacji danych operatora. Testy PostgreSQL korzystały z transakcji rollback.

NEXT:
- READY FOR TASK-035 po odrębnym, jawnym poleceniu.
