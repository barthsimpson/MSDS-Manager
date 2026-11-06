# PATCH-060-R3 — raport korekty prezentacji SDS wycofanego

**Data:** 2026-11-06  
**Podstawa:** `docs/tasks/PATCH-060-R3_Withdrawn_SDS_Status_UI_AUTHORIZED.md`  
**Wynik:** implementacja i focused tests **PASS**; fizyczne oględziny operatora **NOT VERIFIED**.

## Zmiany

- `app/presentation/streamlit/product_registry.py`: lista i karta rozpoznają brak CURRENT wyłącznie przy potwierdzonym audycie wycofania SDS z `CURRENT` bez przywrócenia następcy. Prezentują wspólny komunikat oraz czerwony symbol ostrzegawczy; kolumna BHP zachowuje dotychczasowy odczyt. Historia pokazuje pełny `sds_id`, nazwę pliku, datę i powód wycofania, poprzedni status, informację o następcy, funkcjonalne miejsce przechowywania i zakres dostępu do historycznego PDF. Główny przycisk pobierania pozostaje niedostępny bez CURRENT.
- `tests/unit/test_product_registry_view.py`: przypadki XBRAKE CLEANER, XBRAKE CLEANER liquid i zwykły brak SDS; pozytywne i negatywne warunki audytu oraz odczyt historycznego PDF.
- Nie zmieniano `composition.py` ani repozytorium `sds_invalidation.py`; istniejący odczyt historii wystarczył. Zastane zmiany tych i innych plików w katalogu roboczym pozostawiono bez ingerencji.

## Kryteria R3-1–R3-6

| Kryterium | Wynik |
|---|---|
| R3-1 | **PASS w AppTest / NOT VERIFIED fizycznie:** fixture XBRAKE CLEANER z `TEST_DELETE_001.pdf`, audytem `CURRENT → INVALIDATED` bez następcy i bez CURRENT ma na liście i karcie „Brak bieżącego SDS — wycofano bieżący dokument”. Rzeczywistego widoku operatora nie udało się obejrzeć. |
| R3-2 | **PASS:** XBRAKE CLEANER liquid z CURRENT pozostaje „Oczekuje na BHP”; produkt bez CURRENT i bez audytu nie otrzymuje oznaczenia wycofania. Testy obejmują również audyt z `ARCHIVED`, przywróconego następcę i sprzeczny stan z CURRENT w historii. |
| R3-3 | **PASS w AppTest:** tekst, czerwony symbol i znak ostrzegawczy są obecne; historia pokazuje nazwę, pełny `sds_id`, czas, powód, poprzedni status i informację o następcy. Kolor w rzeczywistej przeglądarce pozostaje do obejrzenia. |
| R3-4 | **PASS w AppTest / NOT VERIFIED fizycznie:** historia wskazuje archiwum SDS produktu i dostęp tylko do historycznego PDF. „Otwórz PDF” wywołuje istniejący odczyt i przygotowuje „Pobierz historyczny PDF”; główne „Pobierz SDS” jest wyłączone. Nie przenoszono pliku ani nie ujawniono absolutnej ścieżki. |
| R3-5 | **PASS w zakresie patcha:** zmiany dotyczą wyłącznie renderowania i testów. Nie zmieniano schematu, danych operatora, Core/BDR/TDR, statusów domenowych, cyklu SDS/BHP ani PDF. Istniejące testy listy, wyszukiwania, sortowania, wyboru i pobierania CURRENT przechodzą. |
| R3-6 | **PARTIAL:** 31 focused unit/AppTest przeszło. `git diff --check -- app/presentation/streamlit/product_registry.py tests/unit/test_product_registry_view.py` zakończył się kodem 0 (ostrzeżenia LF/CRLF). Fizyczne oględziny na `localhost:8501` są **NOT VERIFIED**: serwer uruchomił się, lecz narzędzie Computer Use przerwało sesję, ponieważ kontrola polityki URL dla bieżącej przeglądarki Windows nie jest obsługiwana. Nie wykonano żadnej akcji wycofania. |

## Testy i granice odbioru

Polecenie: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_product_registry_view.py tests/unit/test_task060_sds_invalidation_ui.py -q --basetemp tmp/patch060_r3_focused3` — **31 passed**. Tymczasowy serwer uruchomiony do oględzin został zatrzymany. Nie wykonywano zapisu do bazy operatora.

Pozostałe ryzyko: brak fizycznego potwierdzenia kolorystyki, czytelności tabeli i karty oraz otwarcia PDF w przeglądarce operatora. Odbiór R3-6 wymaga tych oględzin na `localhost:8501` bez ponownego wycofywania SDS. **STOP po raporcie.**
