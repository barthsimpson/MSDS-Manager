# TASK-060 — Raport przygotowania odbioru funkcjonalnego

**Data:** 2026-11-03  
**Status odbioru:** **PENDING / NOT VERIFIED** — brak wyniku fizycznych oględzin GUI. Nie przypisano PASS ani CORRECTION REQUIRED i nie deklaruje się zamknięcia TASK-060.  
**Plan:** `docs/tasks/TASK-060_ACCEPTANCE_PLAN_Cerberus.md`.

## Środowisko odbiorowe

| Element | Potwierdzony stan |
|---|---|
| Aplikacja | [http://127.0.0.1:8760](http://127.0.0.1:8760); lokalny health endpoint zwrócił HTTP 200. Serwer pozostaje uruchomiony do oględzin. |
| Baza | Izolowana baza PostgreSQL `msds_task060_accept_f5dcbfce1be3`, odmienna od bazy skonfigurowanej dla operatora. |
| Migracja | `alembic_version = e4c6f21a9d80` (odczyt z izolowanej bazy). |
| Pliki | Tymczasowy `SDS_ROOT_PATH` w `tmp/msds_task060_accept_f5dcbfce1be3/sds`; oba testowe PDF istnieją. Osobny tymczasowy katalog dowodów BHP. |
| Produkt | `TASK-060 ODBIÓR — Odtłuszczacz testowy`, kod `TASK060-ACCEPT`, `product_id=d75d985f91fb44c49528b1924120e61e`, status `ACTIVE`. |
| SDS A | `TASK060_A_ARCHIVED.pdf`, `sds_id=2cdd9f347db94a6b9e3ba852bb4385f4`, status `ARCHIVED`. |
| SDS B | `TASK060_B_CURRENT.pdf`, `sds_id=7f0c5f28688d4340a249896c9d9cd902`, status `CURRENT`. |
| Audyt | `0` rekordów wycofania dla produktu — środowisko pozostaje w stanie początkowym. |

W izolowanej bazie przygotowano również historyczne decyzje BHP dla obu SDS oraz testowe pliki dowodów. Nie kopiowano ani nie zmieniano PDF operatora. Nie uruchamiano migracji ani wycofania w bazie operatora.

## Kontrola techniczna przed oględzinami

Serwer odpowiada, a odczyt `alembic_version`, produktu, obu SDS, liczby audytów i plików PDF przeszedł w transakcji read-only. `AppTest.from_file` uruchomił rzeczywisty entry point aplikacji z konfiguracją izolowanej bazy, otworzył kartę wskazanego produktu przez stan sesji i potwierdził obecność historii SDS oraz akcji przy A i B bez wyjątku aplikacji. Ta kontrola nie zastępuje fizycznych oględzin.

Automatyczny dostęp do przeglądarki nie był dostępny: host narzędzia Browser Use zgłosił niedostępność. Nie uzyskano zrzutu ekranu ani oceny układu 1920×1080. Użytkownikowi udostępniono adres i instrukcję: **Produkty → wyszukaj `TASK060-ACCEPT` → zaznacz wiersz → Otwórz kartę produktu**.

## Lista z planu odbioru

| Punkt fizycznej kontroli | Wynik |
|---|---|
| Akcja tylko przy `CURRENT`/`ARCHIVED` w „Więcej akcji” | **NOT VERIFIED fizycznie**; AppTest potwierdza akcje przy A i B. |
| Tożsamość produktu, producent, PDF/status; brak zapisu przy otwarciu | **NOT VERIFIED fizycznie**; brak audytu w aktualnym odczycie DB. |
| Blokada zapisu bez powodu i potwierdzenia | **NOT VERIFIED fizycznie**; wcześniejszy AppTest TASK-060 przeszedł. |
| Jawne `NO_CURRENT` / konkretny `ARCHIVED`, bez domyślnego replacement | **NOT VERIFIED fizycznie**; wcześniejszy AppTest TASK-060 przeszedł. |
| Wycofanie `ARCHIVED` bez zmiany `CURRENT` | **NOT VERIFIED w odbiorze**; nie wykonywano operacji na tym produkcie. |
| Wycofanie `CURRENT`, `PENDING_APPROVAL`, brak reaktywacji starej decyzji | **NOT VERIFIED w odbiorze**; nie wykonywano operacji na tym produkcie. |
| `INVALIDATED` z datą, powodem, historycznym PDF i bez ponownej akcji | **NOT VERIFIED w odbiorze**; brak wycofanego SDS w stanie początkowym. |
| Czytelność i przewijanie na ekranie desktopowym 1920×1080 | **NOT VERIFIED**; brak fizycznego zrzutu i oceny człowieka. |

## Wynik i dalszy warunek

**Nie ma podstaw do wyniku PASS ani CORRECTION REQUIRED.** Przed zamknięciem odbioru potrzebny jest opis faktycznych oględzin człowieka, w tym zachowania formularza, historii/PDF i układu. Jeśli operator wykona wycofanie wyłącznie w tej izolowanej bazie, wynik należy dopisać po odczytowym sprawdzeniu stanu. Jeżeli wskaże problem, raport należy uzupełnić o minimalną korektę. Dziesięć starszych nieprzechodzących testów z raportu implementacyjnego pozostaje osobnym zagadnieniem checkpointu i nie było ponownie uruchamianych przy przygotowaniu GUI.

W tej czynności nie modyfikowano kodu aplikacji ani danych operatora. Poza raportem zapisano wyłącznie tymczasowe PDF, logi i metadane środowiska w `tmp/`; testowa baza i katalogi pozostają dostępne do odbioru. **STOP — bez kolejnego Tasku.**
