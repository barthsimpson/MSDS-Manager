# TASK-031 REPORT

STATUS:
DONE

CHANGED:
- Tabela przypisań miejsc stosowania i osobne akcje dodania oraz edycji w `product_registry.py`.
- Supervisory DTO, use case i adapter SQL zwracają wiersz na produkt × aktywną lokalizację, z ilościami przypisania.
- Widok nadzorczy pokazuje ilości i pięć grup filtrów.
- Testy UI, Application i PostgreSQL dostosowano do nowej jednostki wiersza; testy integracyjne tolerują istniejące dane operatora.

USAGE LOCATIONS UI:
- existing assignments table: YES
- add form separated: YES
- edit form separated: YES
- user-friendly quantity labels: YES
- unit dictionary added: NO
- existing use cases preserved: YES

SUPERVISORY READ MODEL:
- row unit = PRODUCT x LOCATION: YES
- multiple locations -> multiple rows: YES
- product without location preserved: YES
- peak quantity included: YES
- monthly consumption included: YES
- None vs 0 preserved: YES
- CURRENT SDS/BHP rules unchanged: YES
- requires_action rules unchanged: YES
- N+1 avoided: YES — dwa SELECT także dla wielu produktów

SUPERVISORY UI:
- required columns: YES
- product search: YES
- status filter: YES
- location filter: YES
- BHP filter: YES
- requires-action filter: YES
- read-only: YES

VALIDATION:
- focused usage UI tests: PASS — pusty stan, 1 i 2 przypisania, wartości 0/None, osobne formularze i istniejące use case'y.
- focused supervisory unit tests: PASS — powody działania na wierszach lokalizacji, brak lokalizacji i reguły CURRENT.
- PostgreSQL integration: PASS — 2 lokalizacje z 25 l / 100 l i 300 l / 10 l, produkt bez aktywnej lokalizacji, None względem 0 oraz dwa SELECT.
- supervisory AppTests: PASS — kolumny, formatowanie, filtry, pusty stan i kontrolowany błąd.
- related regression: PASS — 76 passed, 2 skipped. Pominięto wyłącznie testy wymagające pustej bazy; lokalna baza zawiera już produkty.

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- unit dictionary: NONE
- SDS/BHP lifecycle: NONE

RISKS / DEVIATIONS:
- Testy integracyjne korzystały z istniejącej biblioteki `libpq` z instalacji PostgreSQL 17, dodanej tylko do PATH procesu testowego.
- Fizyczny przegląd UI pozostaje po stronie Architekta Operacyjnego.
- Wstępne usunięcia śledzonych plików w `.pytest_tmp` nie były częścią TASK-031.

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-032.
