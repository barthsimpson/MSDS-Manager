# TASK-DRAFT — kontrolowana aktualizacja CORE-001: propozycja producenta i zatwierdzenie przez operatora

**Projekt:** MSDS-Manager  
**Data decyzji Architekta:** 2026-11-10  
**Status:** READY FOR CONTROLLED DOCUMENT UPDATE (numer i wersja CORE do potwierdzenia w preflight)  
**Tryb:** DOCUMENTATION ONLY / NO IMPLEMENTATION  
**Podstawowa zasada:** **Automatyzacja proponuje, człowiek zatwierdza, a Core pozostaje chroniony.**

## 1. Źródła i pierwszeństwo

1. Jawna decyzja Architekta z 2026-11-10 w bieżącej rozmowie — zatwierdza regułę propozycji i akceptacji producenta.
2. `CORE-001_MSDS_Manager_v1.7-approved_STAGE1.md` — dostępna baza ochrony Core (PRODUCT, MANUFACTURER, tożsamość).
3. `CORE-001_MSDS_Manager_v1.8-draft_BDR012.md` — odnaleziona kopia ma status DRAFT i odsyła do v1.7; raport R3 opisuje natomiast lokalny CORE v1.8 z nagłówkiem Approved i sprzecznym §22. **Rozstrzygnąć na aktualnym lokalnym repo przed redakcją.** Nie nadpisywać statusu w ciemno.
4. `BDR-005 v1.1-approved_STAGE1`, `TDR-012`, `SDS-JSON-001`, `SDS-ALIAS-001`, `TASK-062-R2_REPORT`, `TASK-062-R3_REPORT` — odczytać z aktualnego repo w zakresie dotyczącym identyfikacji, ról i Evidence JSON.
5. Aktualne `AGENTS.md`, `GOV-001`, `GOV-002`, ewentualny rejestr ADR/BDR oraz obowiązujący ARCH/konstytucja, jeśli istnieją.

Nie uznawaj poprzednich streszczeń za zastępstwo aktualnych dokumentów.

## 2. Cel i granica zmiany

Wprowadzić do obowiązującego CORE-001 czytelną zasadę, że dane identyfikacyjne producenta odczytane z SDS tworzą **propozycję do zatwierdzenia przez człowieka**, nigdy automatyczną relację `PRODUCT.manufacturer_id`.

To jest **uzupełnienie reguły domenowej i workflow**, a nie zmiana encji ani schematu bazy.

## 3. Zatwierdzona decyzja Architekta — treść normatywna do przeniesienia

### 3.1. Rozdzielenie źródła, propozycji i decyzji

- `Evidence JSON DRAFT` zachowuje literalną nazwę podmiotu, rolę rozpoznaną w `parties[]`, źródłowy cytat i lokalizację w SDS.
- Interpretacja biznesowa może wskazać **kandydata na producenta** na podstawie roli i dowodów źródłowych; nie nadpisuje przy tym roli źródłowej.
- W wyniku **jawnego zatwierdzenia operatora** następuje wybór istniejącego `manufacturer_id` albo kontrolowane utworzenie MANUFACTURER według dotychczasowych reguł.
- Dopiero zatwierdzona decyzja może być użyta do kontrolowanego planu rejestracji `PRODUCT → MANUFACTURER`.
- Brak rozstrzygniętej i zatwierdzonej tożsamości producenta blokuje **zapis PRODUCT**, lecz nie odczyt SDS, generowanie DRAFT ani dalszy przegląd jego danych.

### 3.2. Reguły propozycji według roli źródłowej

| Rola w Evidence | Zachowanie systemu | Warunek zapisu |
|---|---|---|
| `MANUFACTURER` | Proponuj podmiot jako producenta | Jawne potwierdzenie lub korekta przez operatora |
| `MANUFACTURER_EXPORTER` | Proponuj podmiot jako producenta; nie traktuj roli eksportera jako przeszkody | Jawne potwierdzenie lub korekta przez operatora |
| `SUPPLIER` | Proponuj podmiot jako **kandydata** na producenta, wyraźnie oznaczając, że SDS wskazuje rolę dostawcy, a nie producenta wprost | Jawne potwierdzenie lub wskazanie innego producenta przez operatora |
| `EU_REPRESENTATIVE` | Nie przypisuj samodzielnie roli producenta na podstawie samego przedstawicielstwa | Wymagana odrębna podstawa/świadomy wybór operatora |

Jeżeli istnieją sprzeczne lub liczne kandydatury, system ma je przedstawić do rozstrzygnięcia, a nie wybierać automatycznie na podstawie kolejności wystąpienia.

### 3.3. Przykłady referencyjne (nie hardkodować wyjątków)

- **OPEX:** `The Sherwin-Williams Company` w roli `MANUFACTURER_EXPORTER` → domyślna propozycja producenta; `Valspar B.V.` w roli `EU_REPRESENTATIVE` → zachowana odrębna rola, bez przejęcia tożsamości producenta.
- **SYLGARD:** `DOW POLSKA SP.Z O.O.` w roli `SUPPLIER` → kandydat do potwierdzenia, a nie automatycznie zatwierdzony producent. Operator może wskazać inną właściwą jednostkę grupy Dow.
- Wybór z istniejących producentów musi odbywać się przez ich **tożsamość rekordową** (`manufacturer_id`), nie samo podobieństwo nazw.

### 3.4. Ochrona Core i brak nowych wymagań

- Nie zmieniać modelu `MANUFACTURER 1:N PRODUCT`, definicji tożsamości produktu ani obowiązujących reguł niezmienności/audytu.
- Nie dodawać obowiązkowego niezależnego dochodzenia, certyfikatu producenta lub dodatkowego dokumentu, jeśli operator świadomie potwierdza uzasadnioną propozycję.
- Nie dodawać nowej tabeli `SUPPLIER`, kolumny roli w Core ani nowych statusów bez odrębnej decyzji.
- Nie przekształcać źródłowego `SUPPLIER` w `MANUFACTURER` wewnątrz Evidence JSON.
- Nie dopuszczać żadnego autonomicznego zapisu relacji produktu z producentem przed zatwierdzeniem.

## 4. Instrukcja wykonania dokumentacyjnego

1. Odczytaj status i numer ostatniej obowiązującej rewizji CORE z lokalnego repo oraz GOV/AGENTS/BDR. Wyjaśnij niespójność v1.8 (Approved vs treść §22), **nie anulując innych zatwierdzonych zmian** (np. `INVALIDATED` i REVIEW), jeśli rzeczywiście weszły w życie.
2. Ustal zgodny z rejestrem sposób zapisania decyzji Architekta jako ADR/BDR albo bezpośredniego zatwierdzonego uzupełnienia na podstawie lokalnej procedury. Jeśli nowy numer BDR jest wymagany, sprawdź rejestr — nie zgaduj numeru.
3. Przygotuj kompletną, nową rewizję CORE-001 lub minimalny kontrolowany aneks zgodnie z lokalnym sposobem wersjonowania. Umieść powyższą treść w §3/§4 oraz w części „Ekstrakcja i akceptacja danych SDS”, jeśli w obowiązującej rewizji taki rozdział istnieje.
4. Zaktualizuj historię zmian, status i referencje; nie przepisuj pozostałych rozdziałów przy okazji. Zastosuj jedną spójną informację o statusie w nagłówku, §22 i historii zmian.
5. Wykonaj kontrolę porównawczą przed/po, aby wykazać brak przypadkowej zmiany BHP, Safety, lifecycle SDS, produktów, ilości, miejsc użycia i innych chronionych reguł.
6. Zatrzymaj się po przygotowaniu dokumentacji i raporcie. Osobne zadanie dopiero później może objąć planer importu, operator UI i testy funkcjonalne.

## 5. Kryteria akceptacji

| ID | Warunek | Dowód |
|---|---|---|
| C1 | Ustalono faktycznie obowiązującą rewizję CORE i status v1.8, bez zgadywania | Lista plików, nagłówki, §22, historia, GOV/AGENTS |
| C2 | Wprowadzono jednoznaczną zasadę `propozycja → operator potwierdza → kontrolowany zapis` | Fragment zaktualizowanego CORE |
| C3 | `MANUFACTURER_EXPORTER` prowadzi do propozycji, a `SUPPLIER` do jawnie oznaczonej kandydatury | Tabela reguł i przykłady OPEX/SYLGARD |
| C4 | `EU_REPRESENTATIVE` nie jest samoczynnie producentem | Reguła negatywna w CORE |
| C5 | Brak decyzji operatora blokuje zapis PRODUCT, ale nie ekstrakcję/DRAFT | Reguła pozytywna i negatywna |
| C6 | Zachowano role, nazwy i evidence źródłowe, bez zamiany `SUPPLIER` na `MANUFACTURER` | Zapis w CORE oraz odwołanie do SDS-JSON-001 |
| C7 | Brak zmiany schematu, encji, migracji, kodu, UI i danych Core | Lista zmienionych plików i diff |
| C8 | Status, historia wersji i decyzje są ze sobą spójne; pozostałe reguły Core bez regresji | Kontrola diff i raport |

## 6. Raport wykonania

Zapisz raport w istniejącej konwencji raportów zadań. Uwzględnij: preflight wersji i źródeł, listę zmienionych dokumentów, mapowanie C1–C8 na konkretną treść, zakres i wyniki kontroli diff, brakujące źródła, odstępstwa oraz ewentualne uwagi dotyczące decyzji formalnej. **Nie raportuj testów kodu, których nie wykonano.**

## 7. STOP

STOP i raport bez zmian, jeżeli: status obowiązującego CORE jest rzeczywiście nierozstrzygalny, lokalne reguły wymagają nowej formalnej decyzji wykraczającej poza zatwierdzenie Architekta, albo aktualizacja wymagałaby zmiany modelu/schematu poza niniejszą autoryzacją. Zabezpiecz zastane pliki, nie wykonuj napraw przy okazji i nie rozpoczynaj implementacji.

**Koniec etapu:** dokumentacja gotowa do kontroli Cerberusa, brak zgody na modyfikację kodu i danych.
