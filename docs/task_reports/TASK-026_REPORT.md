# TASK-026 — Supervisory Read Model + PostgreSQL

## 1. Status

`DONE` — 2026-09-15. Wykonano wyłącznie TASK-026. Nie rozpoczęto TASK-027.

Wcześniejszy STOP z powodu braku źródeł został rozwiązany po jawnym poleceniu wznowienia i udostępnieniu BDR-004 oraz CHECKPOINT-004. Przeczytano obowiązujące źródła Tasku: root AGENTS.md, CORE-001 v1.2, BDR-002/003/004/005, TDR-003/004, SPRINT-005, CHECKPOINT-004 i raporty TASK-021/025. Faktyczna nazwa dostarczonego checkpointu w repo: `docs/tasks/CHECKPOINT-004_SPRINT-004_R5_CLOSED (1) (1).md`.

Zakres PostgreSQL wynika z jawnego TASK-026, który łączy read model i integrację. Nie wykonywano odrębnego TASK-027 ani UI opisanego w planie Sprintu.

## 2. Pochodzenie i przegląd zastanych zmian

Punktem odniesienia Git był commit `e554b22` (`Sprint4`). Przed wznowieniem working tree zawierał cztery zmienione pliki eksportów `__init__.py` oraz nieśledzone DTO, port, service, adapter i test integracyjny TASK-026. Pliki istniały już przed poprzednim STOP; poprzednia realizacja dodała jedynie raport BLOCKED.

`git log --all -- ...` nie wykazał historii plików implementacji TASK-026. Git nie pozwala ustalić autora ani sposobu utworzenia nieśledzonych plików. Ich pochodzenie można potwierdzić wyłącznie jako zastany, niezacommitowany szkic; nie przypisano ich konkretnemu autorowi i nie uznano za zaakceptowane.

Przegląd wykazał i usunął:

- reguły nadzorcze w Infrastructure oraz service jedynie delegujący do portu;
- arbitralny wybór CURRENT przez `setdefault`;
- domyślne katalogi plików `.`;
- typ `object` dla daty SDS zamiast `date | None`;
- sprawdzanie plików bez kontroli wyjścia poza root;
- brak osobnych testów reguł i niepełne pokrycie scenariuszy PostgreSQL;
- test integracyjny zatwierdzający fixture i czyszczący je przez wzorce identyfikatorów — zastąpiono transakcjami z rollbackiem.

Zachowano istniejące eksporty nazw kontraktów. DTO i service poprawiono, adapter oraz test integracyjny przepisano i zweryfikowano od nowa.

## 3. Zmienione i dodane pliki w zakresie TASK-026

| Obszar | Pliki |
|---|---|
| DTO | `app/application/dto/supervisory.py`, `app/application/dto/__init__.py` |
| Port | `app/application/ports/supervisory_query.py`, `app/application/ports/__init__.py` |
| Service | `app/application/use_cases/list_supervisory_products.py`, `app/application/use_cases/__init__.py` |
| Błąd odczytu | `app/application/exceptions.py` |
| Adapter | `app/infrastructure/db/repositories/supervisory_query.py`, `app/infrastructure/db/repositories/__init__.py` |
| Dostępność plików | `app/infrastructure/filesystem/file_availability.py` |
| Testy | `tests/unit/test_task026_supervisory.py`, `tests/integration/test_task026_supervisory_read_model_postgresql.py` |
| Izolowana weryfikacja | `scripts/verify_task026.py` |
| Raport | `docs/task_reports/TASK-026_REPORT.md` |

Dokumenty dostarczone przez użytkownika oraz wcześniejsze zmiany poza Taskiem pozostawiono bez modyfikacji.

## 4. Read model, service i port

Istnieje jeden immutable DTO `SupervisoryProductRow` z polami wymaganymi przez §5 Tasku. `usage_locations` i `action_reasons` są krotkami; data SDS ma typ `date | None`. Nie dodano pól przyszłościowych.

`SupervisoryQueryPort.list_products()` zwraca bieżące fakty w tym DTO, z neutralnymi domyślnymi polami oceny. Kontrakt jawnie wskazuje, że wynik gotowy dla konsumenta zwraca dopiero `ListSupervisoryProducts.execute()`.

Service pobiera fakty przez port, tworzy ocenione DTO przez `dataclasses.replace`, oblicza wszystkie powody i `requires_action`, a następnie sortuje po `product_name`, `manufacturer_product_code`, `product_id`. Nie modyfikuje DTO otrzymanych z portu. Application nie importuje ORM, konfiguracji infrastruktury ani Streamlit.

## 5. PostgreSQL adapter i agregacja

`SqlAlchemySupervisoryQuery(session, settings=settings)` wymaga jawnego obiektu konfiguracji `Settings`, pochodzącego z istniejącego `load_settings()`. Nie ma fallbacku do `.`.

Odczyt wykonuje dwa SELECT niezależnie od liczby produktów; pusta baza wymaga jednego SELECT:

1. PRODUCT + MANUFACTURER oraz LEFT JOIN CURRENT SDS, CURRENT BHP_DECISION i DECISION_EVIDENCE;
2. aktywne USAGE_LOCATION połączone z PRODUCT_USAGE_LOCATION, agregowane w pamięci po product_id.

Wybierane są potrzebne kolumny, bez ładowania encji ORM i relacji SAFETY_PROFILE/SDS_COMPONENT. Lokalizacje nie uczestniczą w głównym joinie, więc wiele lokalizacji nie mnoży produktów. INACTIVE location jest wykluczona. Nazwy lokalizacji mają stabilny porządek.

Adapter nie zawiera reguł `action_reasons`. Nie wykonuje commit, update ani flush. `session.no_autoflush` chroni przed zapisem niezwiązanych zmian oczekujących w sesji; test potwierdza odczyt wartości zapisanej w DB mimo niezapisanej zmiany obiektu ORM.

## 6. CURRENT SDS i BHP

SDS wybierany jest wyłącznie przez `document_status = CURRENT`, a decyzja przez `record_status = CURRENT` i `sds_id` aktualnego SDS. Daty/revizje nie rozstrzygają aktualności. ARCHIVED SDS i SUPERSEDED decyzje nie dostarczają bieżących metadanych.

Brak CURRENT SDS daje `current_sds_id = None`. Brak CURRENT decyzji dla tego SDS daje `None` w polach metadanych decyzji i `False` w dostępności evidence.

Powtórzenie produktu w głównym wyniku, bez joinu lokalizacji, oznacza niejednoznaczny CURRENT i podnosi `SupervisoryReadError`; odczyt nie zwraca częściowego wyniku ani nie wybiera pierwszego rekordu. Nie ma `setdefault` rozstrzygającego CURRENT.

Testy jednostkowe wstrzykują sprzeczne wyniki odczytu osobno dla SDS i decyzji, bez wyłączania constraintów. Testy PostgreSQL potwierdzają działanie istniejących indeksów `uq_sds_documents_one_current_per_product` i `uq_bhp_decisions_one_current_per_sds`.

## 7. Dostępność plików

Techniczny helper sprawdza bieżące istnienie regularnego pliku względem skonfigurowanych `SDS_ROOT_PATH` i `BHP_EVIDENCE_ROOT_PATH`. Odrzuca referencje bez ścieżki, ścieżki absolutne i wyjścia poza rozstrzygnięty root. Katalog zamiast pliku, brak pliku lub błąd dostępu daje `False`.

Nie odczytuje treści dokumentów, nie kopiuje ani nie modyfikuje źródłowych plików. Nie aktualizuje `file_status` w DB. Test potwierdza zmianę dostępności między odczytami po utworzeniu plików, przy niezmienionym zapisanym `file_status = MISSING`.

## 8. Reguły w Application

| Warunek | Powód |
|---|---|
| PRODUCT PENDING_APPROVAL | BRAK DECYZJI BHP |
| PRODUCT REJECTED | PRODUKT ODRZUCONY |
| Brak CURRENT SDS | BRAK CURRENT SDS |
| CURRENT SDS istnieje, pliku brak | BRAK PLIKU SDS |
| Brak aktywnej lokalizacji | BRAK MIEJSCA STOSOWANIA |
| CURRENT decyzja istnieje, evidence niedostępne | BRAK PLIKU DOWODU BHP |

`requires_action = bool(action_reasons)`. Powody współistnieją. Brak rekordu SDS nie tworzy dodatkowo powodu brakującego pliku SDS; brak decyzji nie tworzy powodu brakującego evidence.

Sam INACTIVE produktu, miesięczne zużycie NULL/0, notes NULL, brak decided_by/decision_date ani historyczne SDS/decyzje nie dodają powodów.

## 9. Weryfikacja

Końcowy przebieg na rzeczywistym, izolowanym PostgreSQL 17:

| Kontrola | Wynik |
|---|---|
| Focused tests | **15 passed**, 0.67 s |
| TASK-026 PostgreSQL integration | **9 passed**, 0.76 s |
| Pełny pytest | **162 passed**, 15.44 s |
| SAWarning | Brak; wszystkie przebiegi z `-W error::sqlalchemy.exc.SAWarning` |
| Alembic current, baza testowa | `e0dd7d6468bf (head)` |
| Alembic check, baza testowa | `No new upgrade operations detected.` |
| Alembic current, baza skonfigurowana | `e0dd7d6468bf (head)` |
| Alembic check, baza skonfigurowana | `No new upgrade operations detected.` |
| Produkty w bazie testowej po pełnej regresji | **0** |
| Cleanup klastra i plików tymczasowych | PASS |

Pokryto wszystkie scenariusze reguł i dziewięć wymagań PostgreSQL z Tasku, w tym pustą bazę, wiele aktywnych lokalizacji, wyłączenie INACTIVE, przewagę CURRENT nad nowszym ARCHIVED, ignorowanie SUPERSEDED, brak dziedziczenia decyzji starego SDS i dostępność plików. Pełna regresja obejmuje również dotychczasowe testy architektury i integralności Core.

Powtarzalne uruchomienie:

```powershell
.\.venv\Scripts\python.exe scripts/verify_task026.py
```

Skrypt korzysta z zainstalowanych binariów `C:\Program Files\PostgreSQL\17\bin`, tworzy tymczasowy klaster na osobnym porcie loopback i bazę `msds_manager`, stosuje wyłącznie istniejące migracje do head, uruchamia trzy fazy pytest, Alembic i cleanup. Konfiguracja jest przekazywana procesom przez environment; `.env` pozostaje bez zmian.

Każda faza używa własnego `--basetemp` pod tymczasowym katalogiem `.venv/task026-*`, ponieważ zastany `.pytest_tmp` zawiera śledzone fixture i zgłasza odmowę dostępu. Pierwszy przebieg zakończył się sukcesem, lecz ukrywał stdout procesów potomnych. Wersja przechwytująca pipe ujawniła problem odziedziczonych uchwytów Windows przy starcie PostgreSQL; klaster zatrzymano i usunięto. Końcowa wersja przechwytuje wyjście do plików i przeszła pełną weryfikację z wynikami powyżej. Uruchomienie lokalnego klastra wymagało zatwierdzonego wykonania poza sandboxem.

## 10. Core, schema i Git / bezpieczeństwo

- Nie zmieniono Domain, ORM models, migracji, konfiguracji Alembic ani zależności.
- Istniejące migracje zastosowano wyłącznie do utworzenia schematu tymczasowej bazy testowej. Nie wykonano upgrade ani zapisów na bazie operacyjnej.
- Skonfigurowana baza miała 6 produktów przed i po weryfikacji; odczyt potwierdził 12 tabel biznesowych i 0 niejednoznacznych CURRENT SDS/decyzji.
- Nowe testy integracyjne używają rollbacku zamiast commit/cleanup danych przez wzorce identyfikatorów. Pozostała regresja działała na izolowanej bazie.
- Nie dodano trwałych fixture SDS/evidence, sekretów, backupów ani dumpów. `.env` pozostaje ignorowany.
- Nie wykonano commit, push, reset ani odwracania zastanych zmian. Wcześniejsze usunięcia fixture `.pytest_tmp` pozostawiono nietknięte.
- Kontrole whitespace dla zakresu Tasku i indeksu Git nie wykazały błędów.

## 11. Odstępstwa i ograniczenia

Brak odstępstw biznesowych i architektonicznych. Dodano mały helper dostępności plików oraz skrypt izolowanej weryfikacji, bez nowych zależności ani frameworków. Jeden DTO służy do przekazania faktów i ocenionego wyniku; właściwym punktem wejścia konsumenta jest service.

Dostępność opisuje stan filesystemu w momencie odczytu i może zmienić się później. Dwa SELECT korzystają z transakcji wywołującego; Task nie wprowadza nowego poziomu izolacji ani mechanizmu snapshotów. Skrypt weryfikacji jest dostosowany do Windows i PostgreSQL 17 wskazanych w Tasku.

Definition of Done TASK-026 spełnione. Nie dodano UI, zapisu wymagań działania, tabel, historii, scoringu, cache ani workflow problemów.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-027.
