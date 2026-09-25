# TASK-030 REPORT

STATUS:
DONE

CHANGED:
- `add_sds.py`: zwarte sekcje dokumentu i produktu, oznaczenie pól wymaganych, opcjonalna chemia w expanderach i ręczne wypełnienie bez parsera.
- `product_registry.py`: kontekst produktu i bieżącego SDS przy nowej rewizji oraz pusta domyślnie data dokumentu.
- `bhp_decision.py`: czytelny kontekst produktu i SDS, nazwy plików dowodów, przyjazne etykiety i odczyt aktualnego stanu po rerun.
- Powiązane testy AppTest i testy formularza rewizji.

ADD SDS UI:
- compact sections: YES
- required fields visible: YES
- optional chemistry subordinate: YES
- manual fallback preserved: YES
- UUID hidden: YES

SDS REVISION UI:
- product context visible: YES
- current SDS context visible: YES, gdy istniejący odczyt nadzorczy jest dostępny
- unknown issue_date defaults to None: YES
- lifecycle unchanged: YES

BHP UI:
- product/current SDS context visible: YES
- evidence shown as filename: YES
- user-facing decision labels: YES
- product status refresh after save: YES
- BHP lifecycle unchanged: YES

VALIDATION:
- focused Add SDS AppTests: PASS — odczyt, korekta, ręczny szkic, sekcje, wymagane pola, opcjonalna chemia i komunikat bez UUID.
- focused revision tests: PASS — kontekst produktu/SDS, istniejący PRODUCT, brak domyślnej daty i jawnie podana data.
- focused BHP AppTests: PASS — kontekst, nazwa pliku dowodu, wartości domenowe, ponowny odczyt i aktualny stan ACTIVE/REJECTED.
- related regression: PASS — 36 testów powiązanych formularzy, kontraktów i shell.
- integration: NOT REQUIRED — composition i sposób odczytu przez Application niezmienione.

SCOPE:
- Core change: NONE
- schema/migrations: NONE
- dependencies: NONE
- parser: NONE
- lifecycle/persistence changes: NONE

RISKS / DEVIATIONS:
- Stan bieżącego SDS w formularzu rewizji zależy od istniejącego odczytu nadzorczego z TASK-029; gdy odczyt jest niedostępny, ekran pokazuje „Brak danych”.
- Po decyzji BHP rerun odczytuje stan przez istniejące metody composition. Testy AppTest używają kompozycji, która odzwierciedla zapis; fizyczny walkthrough pozostaje do wykonania przez Architekta Operacyjnego.
- W `.pytest_tmp` pozostają usunięcia śledzonych plików PDF obecne przed TASK-030; nie były częścią zmian.

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-031.
