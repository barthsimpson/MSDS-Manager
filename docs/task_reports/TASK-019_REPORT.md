# TASK-019 — Accept SDS / Core Transaction

## 1. Status

`DONE`

Wykonano TASK-019 zgodnie z zakresem. Nie rozpoczęto TASK-020.

## 2. Źródła

Uwzględniono TASK-019, kontrakty TASK-017, adapter PDF i raport TASK-018, istniejący Core/ORM/schema oraz `TransactionExecutor`. Nie zmieniano zatwierdzonego modelu biznesowego.

## 3. Zmienione pliki

- `app/application/ports/sds_extractor.py`
- `app/application/ports/__init__.py`
- `app/application/exceptions.py`
- `app/application/use_cases/accept_sds.py`
- `app/application/use_cases/__init__.py`
- `app/infrastructure/filesystem/sds_file_validator.py`
- `app/infrastructure/db/repositories/sds_acceptance.py`
- `app/infrastructure/db/repositories/__init__.py`
- `tests/unit/test_accept_sds.py`
- `tests/unit/test_sds_file_validator.py`
- `tests/integration/test_task019_accept_sds.py`
- `docs/task_reports/TASK-019_REPORT.md`

## 4. AcceptSds

Dodano jeden jawny use case `AcceptSds`. Przed delegowaniem zapisu sprawdza wymagane pola tożsamości i użycia, język `PL`, `language_valid`, statusy SafetyProfile oraz wymagane nazwy składników. Następnie sprawdza plik przez `SdsFileValidator` i przekazuje zaakceptowany formularz do jednego repozytorium persystencji.

## 5. Walidacja i SDS_ROOT_PATH

`SdsFileValidator` wymaga istniejącego pliku PDF, rozwiązuje ścieżkę względem skonfigurowanego `SDS_ROOT_PATH` i odrzuca traversal/ścieżki spoza katalogu oraz pliki inne niż PDF. Błąd walidacji występuje przed pierwszym zapisem Core.

## 6. Manufacturer

Repozytorium wykonuje dokładne dopasowanie po nazwie producenta. Istniejący jednoznaczny rekord jest używany ponownie. Brak rekordu tworzy nowy `MANUFACTURER`. Więcej niż jeden rekord o tej samej nazwie kończy się kontrolowanym błędem. Nie ma fuzzy matching, aliasów, lookupu ani auto-merge.

## 7. Product identity

Dopasowanie PRODUCT odbywa się dokładnie po:

```text
product_name + manufacturer_product_code + manufacturer_id
```

Brak dopasowania tworzy nowy PRODUCT. Istniejący PRODUCT jest używany bez duplikowania, a zatwierdzone pola użycia są aktualizowane.

## 8. SDS CURRENT/ARCHIVED

Każda akceptacja tworzy nowy `sds_id`, zapisuje nazwę pliku, ścieżkę względną, datę, rewizję, `AVAILABLE` i `CURRENT`. Przed zapisem nowego SDS poprzedni CURRENT dla produktu jest ustawiany na `ARCHIVED`. Istniejący indeks częściowo unikalny oraz logika aplikacyjna utrzymują maksymalnie jeden CURRENT.

PDF nie jest kopiowany, przenoszony, zmieniany ani zapisywany w PostgreSQL.

## 9. SafetyProfile

Dla każdego SDS zapisywany jest dokładnie jeden `SafetyProfileModel`. Wszystkie zatwierdzone pola kontraktu są mapowane. Brak statusu zostaje zapisany jako `NO_DATA`, a `NO_DATA` nie jest zamieniane na `NO`. `approved_at` jest ustawiane przy akceptacji, a `last_manual_edit_at` pozostaje `NULL`.

## 10. Components

Komponenty są przypisywane do nowego `sds_id` i zapisują wyłącznie pola z `SdsComponentDraft`: nazwa, CAS, WE, REACH, stężenie, klasyfikacja i kody H. Pusta lista jest poprawna. Brak wymaganej nazwy składnika jest kontrolowanym błędem formularza.

## 11. ProductHistory

Po każdej akceptacji tworzony jest snapshot `ProductHistory` z bieżącym stanem PRODUCT po ustawieniu `PENDING_APPROVAL`, wraz z `use_description`, `use_restriction`, waste fields i timestampem. Przy nowym produkcie jest to initial snapshot; przy kolejnym SDS powstaje kolejny snapshot.

## 12. Transakcja i rollback

`SqlAlchemySdsAcceptanceRepository` nie wykonuje commit. Całość jest uruchamiana przez istniejący `TransactionExecutor`, który commit wykonuje dopiero po sukcesie i rollbackuje sesję dla wyjątku. Test PostgreSQL wymusza wyjątek po `flush()` repozytorium i potwierdza brak częściowego MANUFACTURER oraz PRODUCT, a tym samym brak SDS/profilu/składników/historii.

## 13. Domain / ORM / schema

Nie dodano nowych statusów, tabel ani zmian Domain. Istniejący ORM i schema już zawierały wymagane `SDS_DOCUMENTS`, `SAFETY_PROFILES`, `SDS_COMPONENTS` oraz `PRODUCT_HISTORY`. Nie utworzono migracji.

- Alembic revision: `e0dd7d6468bf (head)`
- liczba tabel: bez zmian, 12
- drift: brak

## 14. Testy

- Unit AcceptSds i walidatora: `7 passed`.
- Integracja PostgreSQL TASK-019: `2 passed`.
- Łączny focused run po końcowych zmianach: `9 passed`.
- Pełny pytest: `117 passed`.
- `-W error::sqlalchemy.exc.SAWarning`: bez ostrzeżeń SQLAlchemy.
- `alembic current`: `e0dd7d6468bf (head)`.
- `alembic check`: `No new upgrade operations detected.`

Testy obejmują nowy producent/produkt, ponowne użycie tożsamości, CURRENT/ARCHIVED, profil, składnik, historię, ścieżki opcjonalne oraz rollback PostgreSQL.

## 15. Git / bezpieczeństwo

Nie wykonano commit ani push. Nie dodano sekretów, dumpów, backupów, OCR, AI/LLM ani nowych fixture PDF. Istniejące niezależne zmiany wcześniejszych tasków pozostały nietknięte. `git diff --check` i `git diff --cached --check` nie wykazały błędów.

## 16. Odstępstwa i ryzyka

Rozpoznawanie producenta i produktu jest celowo dokładne, bez automatycznego scalania. Walidator wymaga fizycznej obecności PDF w `SDS_ROOT_PATH`. Akceptacja kończy się na `PRODUCT = PENDING_APPROVAL` i `SDS = CURRENT`; nie obejmuje BHP, decyzji ani UI TASK-020.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-020.
