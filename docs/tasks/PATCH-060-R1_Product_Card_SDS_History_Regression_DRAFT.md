# PATCH-060-R1 — Przywrócenie karty produktu i dostępu do SDS po TASK-060

**Projekt:** MSDS Manager  
**Status:** DRAFT — wymaga jawnej autoryzacji Architekta Operacyjnego  
**Tryb:** PATCH / GOV-002 Level 1 (focused + sprawdzenie rzeczywistego GUI)  
**Powiązanie:** TASK-060, TDR-014 v0.2-approved, CORE-001 v1.8-approved, BDR-012 v1.1-approved

## 1. Zgłoszenie operatora — dowód

Podczas ręcznego odbioru TASK-060, 2026-11-03, w zakładce **Produkty** wybrano `SYLGARD 160 Silicone Elastomer-Part A` (producent `DOW POLSKA SP.Z O.O.`, SDS `CURRENT`, rewizja `5.0`). Lista produktów wyświetla pozycję. Po **Otwórz kartę produktu** widoczny jest wyłącznie błąd: **„Nie udało się odczytać historii SDS.”** Karta nie pokazuje historii, PDF ani akcji **„Wycofaj błędnie zarejestrowany SDS”**. Dowody: zrzuty ekranu operatora `image(20261103-133755).png`, `image(20261103-133846).png` (jeżeli przekazane do repo; w przeciwnym razie opis niniejszy).

Zgłoszenie oznacza **FAIL fizycznego odbioru A6 TASK-060** i utratę istniejącej funkcji otwierania PDF. Nie dowodzi utraty pliku PDF ani danych. Nie zakładać przyczyny bez logów.

## 2. Cel i granice

Przywrócić renderowanie karty produktu i dostęp do PDF **bez naruszenia nowej funkcji wycofania SDS**. Jeden wynik: karta otwiera się prawidłowo dla istniejącego produktu z SDS `CURRENT`, pokazuje historię i udostępnia jego plik oraz akcję korekcyjną.

Bez zmian BDR/CORE/TDR, lifecycle BHP, modelu danych, nowej migracji, szerokiego refaktoringu, prac nad starszymi fixture, Paczką2 i Stage 2. **Bez zapisu/wycofywania rzeczywistych SDS.**

## 3. Dyspozycja dla Codexa

1. Odtwórz zgłoszony przebieg w tej samej konfiguracji, w której operator widział błąd. Zbierz **pełny wyjątek/traceback z serwera Streamlit**. Nie maskuj wyjątku ogólnym komunikatem na czas diagnostyki; szczegóły błędu do raportu/logu, a nie do publicznego UI.
2. Sprawdź w pierwszej kolejności trasę `app/presentation/streamlit/product_registry.py` → `composition.py` → odczyt historii SDS / `sds_invalidation`; zestaw zapytania i modele z faktycznym schematem DB. Rozróżnij **wadliwy odczyt**, **niezastosowaną migrację `e4c6f21a9d80` w danym środowisku** oraz **problem uprawnień/połączenia**. Nie zakładaj z góry, że winna jest migracja.
3. Jeżeli środowisko operatora nie ma wymaganego schematu, **STOP przed migracją** i opisz bezpieczne działanie; zgoda na PATCH nie uprawnia do migracji bazy operatora. Wykonaj migrację wyłącznie na odizolowanej bazie testowej, jeśli potrzebna do reprodukcji.
4. Jeżeli przyczyna leży w kodzie, wprowadź minimalną korektę w istniejącej ścieżce odczytu/renderowania. Nie dodawaj nowych warstw, fallbacków ukrywających niespójność ani fikcyjnej historii SDS.
5. Potwierdź zarówno zachowanie **starego dostępu do PDF**, jak i wyświetlanie historii oraz akcji wycofania dla `CURRENT`/`ARCHIVED`; dla `INVALIDATED` akcja nie jest dostępna, a PDF pozostaje czytelny.
6. Dodaj jeden celowany test regresyjny odwzorowujący pierwotny błąd na rzeczywistym schemacie lub prawidłowo zmockowanym kontrakcie; uruchom dotknięte testy `product_registry` i TASK-060. Sprawdź `git diff --check`.
7. Zapewnij możliwość fizycznego testu operatora, przekazując adres działającej aplikacji i identyfikator **testowego** produktu. Bez automatycznego klikania wycofania i bez modyfikacji rzeczywistych danych.

## 4. Kryteria akceptacji

- **R1:** Lista produktów nadal działa; kliknięcie **Otwórz kartę produktu** wyświetla poprawną kartę bez komunikatu o błędzie historii SDS.
- **R2:** W karcie dostępny jest istniejący SDS `CURRENT`, jego historia i otwarcie PDF; żaden plik/referencja PDF nie jest usuwany ani zmieniany.
- **R3:** Akcja **Wycofaj błędnie zarejestrowany SDS** jest widoczna w odpowiednim miejscu dla `CURRENT/ARCHIVED`; ścieżka formularza pozostaje zgodna z TASK-060, ale nie wymaga wykonania zapisu podczas tej kontroli.
- **R4:** Test regresyjny reprodukuje pierwotny przypadek i przechodzi po poprawce. Dotknięte testy nie wykazują nowej regresji.
- **R5:** Operator ręcznie potwierdza widok listy → karta → historia → PDF → dostępność akcji. **Bez tego PATCH pozostaje ACCEPTANCE PENDING.**

## 5. Raport i STOP

Zapisz `PATCH-060-R1_REPORT.md`: rzeczywisty traceback i przyczyna, środowisko/wersja Alembic, dokładne zmienione pliki, wyniki R1–R5 z rodzajem dowodu (test/log/oględziny operatora), lista testów, ograniczenia, zmiany DB/FS (oczekiwane: zero operator writes). Jeśli problem dotyczy wyłącznie nieprzeprowadzonej migracji środowiska operatora, nie modyfikuj kodu — zgłoś STOP z planem bezpiecznego wdrożenia. Nie rozpoczynaj kolejnego TASK.
