# PATCH-060-R3 — Jednoznaczna prezentacja SDS wycofanego w liscie i karcie produktu

**Projekt:** MSDS Manager  
**Parent:** TASK-060 (odbior warunkowy; korekta stwierdzona w tescie operatora)  
**Status:** AUTHORIZED — Architekt Operacyjny, 2026-11-06  
**Tryb GOV-002:** PATCH / focused tests + fizyczny odbior UI  
**Cel:** usunac mylace 'Oczekuje na BHP' jako jedyny komunikat dla produktu XBRAKE CLEANER, ktorego ostatni CURRENT SDS zostal wycofany bez przywrocenia nastepcy.

## Zrodla i granice

1. CORE-001 v1.8-approved_BDR012, BDR-012 v1.1-approved, TDR-014 v0.2-approved.
2. TASK-060 i jego raporty, PATCH-060-R1/R2, obserwacje operatora z 2026-11-06.
3. GOV-001/GOV-002, UI-GUIDE-001, AGENTS.md.

**Nie zmieniac** `PRODUCT.usage_status=PENDING_APPROVAL`, `SDS.document_status=INVALIDATED`, lifecycle BHP, historii, plikow, tabel ani migracji. Jest to korekta *prezentacji/odczytu*, nie nowe statusy domenowe.

## Kontrakt widoku

### A. Wykrywanie stanu — bez zgadywania

Wyroznij stan prezentacyjny **'SDS wycofany — brak biezacej karty'** tylko wtedy, gdy lacznie:
- produkt nie ma zadnego SDS `CURRENT`, oraz
- w istniejacym `sds_invalidation` znajduje sie zdarzenie dotyczace SDS tego produktu wycofanego z `CURRENT` w wariancie bez przywroconego SDS (`restored_sds_id IS NULL`).

Bazuj na aktualnym stanie i potwierdzonym audycie. Nie ustawiaj komunikatu tylko dlatego, ze produkt nie ma `CURRENT`. Nie traktuj historycznych INVALIDATED jako aktualnego braku, jesli zostal zarejestrowany pozniejszy poprawny CURRENT. Jesli wystapia sprzeczne dane/niejednoznacznosc, zachowaj neutralny komunikat 'Brak biezacego SDS' i zglos obserwacje; nie tworzyc kolejnej logiki statusowej.

### B. Lista Produkty

Dla potwierdzonego przypadku XBRAKE CLEANER:
- kolumna **Status**: `Brak biezacego SDS` (zamiast samego `Oczekuje na BHP`), wraz z widocznym komunikatem, ze wycofano biezacy dokument; 
- kolumna **SDS**: `Wycofany / bledna rejestracja`, odrozniony od `CURRENT`, `ARCHIVED` i ogolnego braku SDS;
- kolumna **BHP**: zachowaj prawdziwy, wynikajacy z istniejacego modelu stan decyzji, bez sugerowania zatwierdzenia;
- sposob prezentacji: kolor ostrzegawczy/czerwony adekwatny do przyjetego UI-GUIDE, **zawsze z tekstem i czytelnym znacznikiem** (np. ikona ostrzezenia), nigdy sam kolor.

Nie zmieniaj istniejacego 'Oczekuje na BHP' dla produktu z poprawnym `CURRENT` bez decyzji, np. XBRAKE CLEANER liquid. Nie zmieniaj wyszukiwania, sortowania ani wyboru produktu.

### C. Karta produktu i identyfikacja SDS

W naglowku karty produktu przy braku CURRENT pokaz ten sam komunikat, co na liscie. W sekcji historii kazdy `INVALIDATED` nadal przedstawiaj jako `Wycofany / bledna rejestracja` z wizualnym oznaczeniem i wymienionymi elementami:
- nazwa pliku SDS + **identyfikator `sds_id`** (np. jako skrot z mozliwoscia odczytu pelnego ID w szczegolach); bez nowego identyfikatora;
- data i powod wycofania z istniejacego audytu, poprzedni status i informacja, czy przywrocono zastepczy SDS;
- informacja: **'Przechowywanie: archiwum SDS tego produktu; dokument zachowany w dotychczasowej lokalizacji'**;
- informacja: **'Dostep: historyczny PDF — tylko do wgladu/pobrania; nie jest biezacym SDS produktu'**;
- istniejacy przycisk 'Otworz PDF' pozostaje dostepny w historii zgodnie z dotychczasowymi uprawnieniami i sciezka storage.

`SDS.relative_path` pozostaje bez zmian; nie ujawniaj absolutnych sciezek serwera ani nie przenos plikow. 'Miejsce przechowywania i udostepniania' oznacza **widoczna lokalizacje funkcjonalna** (Historia SDS produktu, historyczny dostep do PDF), nie nowy katalog, publiczny link ani oddzielne archiwum fizyczne. Nie dawaj INVALIDATED jako dokumentu biezacego przez glowny przycisk 'Pobierz SDS'.

### D. Brak nowych krokow i warunkow

Uzyc istniejacej warstwy odczytu historii/summary produktu i istniejacych komponentow Streamlit. Jezeli wystarczy punktowe rozszerzenie projection/DTO, nie tworzyc dodatkowej uslugi ani tabeli statusow. Bez zmian w Core, BDR, TDR, bazie operatora i bez kolejnych migracji. Nie wykonywac wycofania jakiegokolwiek SDS w ramach PATCH.

## Acceptance R3-1 — R3-6

- **R3-1:** XBRAKE CLEANER (po wycofaniu `TEST_DELETE_001.pdf`, wariant NO_CURRENT) na liscie i karcie jednoznacznie pokazuje brak biezacej karty z powodu wycofania, nie tylko 'Oczekuje na BHP'.
- **R3-2:** XBRAKE CLEANER liquid z `CURRENT` i bez decyzji BHP zachowuje dotychczasowy komunikat; inne produkty bez `CURRENT` i bez dowodu invalidacji nie sa falszywie oznaczane jako wycofane.
- **R3-3:** Wycofany SDS jest czytelnie oznaczony tekstem + kolorem + symbolem, ma istniejące `sds_id`, nazwe, czas, powod i informacje o poprzednim statusie / replacement.
- **R3-4:** Historia SDS wskazuje funkcjonalne miejsce przechowywania i zakres udostepniania historycznego PDF; przycisk otwarcia dziala, ale INVALIDATED nie jest prezentowany jako CURRENT. Bez przesuwania plikow i ujawniania absolutnych sciezek.
- **R3-5:** Bez zmian schema, danych, Core/BDR/TDR, lifecycle SDS/BHP i realnych PDF; zachowane wyszukiwanie, sortowanie, pobieranie CURRENT dla innych produktow.
- **R3-6:** Focused testy przypadkow pozytywnych i negatywnych + szybkie fizyczne ogledziny operatora na `localhost:8501` (bez kolejnej akcji wycofania); raportuje PASS/FAIL i ewentualne brakujace ogledziny.

## Wykonanie i raport

1. Przed zmiana potwierdz biezacy stan kodu i nazwy odpowiedzialnych funkcji (z raportu TASK-060: `app/presentation/streamlit/product_registry.py`, `app/presentation/streamlit/composition.py`, `app/infrastructure/db/repositories/sds_invalidation.py`). Pracuj lokalnie, bez szukania calego repo bez potrzeby.
2. Zmien tylko minimalny odczyt i renderowanie listy/karty/historii; nie dotykaj mechanizmu invalidacji.
3. Uruchom focused unit/AppTest, test z przypadkiem XBRAKE CLEANER i odrebnym XBRAKE CLEANER liquid; wykonaj `git diff --check`. Nie wykonuj destrukcyjnych operacji na bazie operatora.
4. Zapisz `PATCH-060-R3_REPORT.md`: zmienione pliki, wynik R3-1..R3-6, testy, obserwacje UI, pozostale ryzyka, STOP. Przy braku fizycznego ogledzin jawnie `NOT VERIFIED`.

**STOP:** sprzecznosc z CORE/BDR/TDR, wymog nowego statusu bazy, zmiany schematu lub brak dowodu pozwalajacego odroznic przypadki -> nie implementuj obejscia, zglos Cerberusowi. Bez dodatkowego refaktoringu i bez przechodzenia do nastepnego TASK.

## Autoryzacja

Architekt Operacyjny 2026-11-06 jawnie zatwierdzil korekte identyfikacji i wizualnego nadzoru SDS wycofanego, wlacznie z opisem, kolorem, identyfikatorem, miejscem przechowywania i udostepniania. Autoryzacja obejmuje tylko opisany PATCH, bez zmian danych operatora i bez fizycznego przenoszenia dokumentow.
