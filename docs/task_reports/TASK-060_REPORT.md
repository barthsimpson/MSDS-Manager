# TASK-060 — Raport wykonania

**Data:** 2026-11-03  
**Wynik:** Implementacja zakończona; fizyczne oględziny GUI: **NOT VERIFIED**.  
**Stan bazowy:** `main`, HEAD `3411f6dd3f503042d9636ab32384bda49ca7da43`, z zastanymi niezacommitowanymi zmianami. Nie utworzono commita.

## Preflight i zakres

W `docs/tasks/` potwierdzono pojedynczy `TASK-060_TDR014_InvalidateSds_EndToEnd_AUTHORIZED.md`; poprzedni numer to `TASK-059`. Potwierdzono obecność i treść `TDR-014_Wycofanie_blednie_zarejestrowanego_SDS_v0.2-approved.md` (status APPROVED, 2026-11-03) oraz wskazanych CORE v1.8 i BDR-012 v1.1. Nie edytowano tych dokumentów.

Dodano status `INVALIDATED`, tabelę `sds_invalidation` i migrację `e4c6f21a9d80` po `b7d4a1f03962`. Migracja rozszerza także długość kolumny statusu SDS z 8 do 11 znaków; wykrył to test na PostgreSQL. Częściowy indeks jednego `CURRENT` na PRODUCT pozostał bez zmian. Downgrade odmawia działania przy rekordach `INVALIDATED` lub audytu.

`InvalidateSds` waliduje powód i jawny wariant. Repozytorium blokuje PRODUCT, następnie SDS w ustalonej kolejności, weryfikuje stan, zapisuje zmiany i audyt w istniejącym `TransactionExecutor`. Rejestracja SDS i BHP korzysta teraz ze zgodnej kolejności blokady PRODUCT. Wycofanie `CURRENT` zamyka fizycznie bieżące decyzje wycofywanego i przywróconego SDS przez istniejące `SUPERSEDED`; nie wprowadzono nowego statusu BHP ani bramki czasowej. Bezpośredni odczyt decyzji BHP wymaga SDS `CURRENT`.

Karta produktu pokazuje historię SDS, datę/powód/status wcześniejszy i wskazany zamiennik, dostęp do historycznego PDF oraz akcję w „Więcej akcji” przy konkretnym `CURRENT/ARCHIVED`. Formularz wymaga powodu, checkboxu i jawnego wyboru `RESTORE_ARCHIVED` albo `NO_CURRENT`; replacement początkowo ma wartość pustą. Stale state kończy się komunikatem i rollbackiem.

## A1–A7

| Kryterium | Wynik | Dowód |
|---|---|---|
| A1 — ARCHIVED | **PASS** | `tests/integration/test_task060_sds_invalidation.py::test_archived_invalidation_keeps_current_product_and_bhp`: bieżący SDS, PRODUCT i decyzje BHP bez zmian; audyt wskazuje `ARCHIVED`. |
| A2 — CURRENT | **PASS** | `test_no_current_preserves_related_data_and_writes_audit`, `test_restore_supersedes_old_decisions_then_existing_register_works`: jawny wariant, brak albo jeden przywrócony `CURRENT`, PRODUCT `PENDING_APPROVAL`. Wymóg wyboru egzekwuje `app/application/use_cases/invalidate_sds.py`. |
| A3 — nowe BHP po restore | **PASS** | Test restore sprawdza `SUPERSEDED` obu wcześniejszych decyzji, brak bieżącej decyzji A po restore i nowy zapis przez istniejący `RegisterBhpDecision`. Izolowany PostgreSQL potwierdził ten przebieg z realnym indeksem częściowym. |
| A4 — reason/stale/audit/rollback | **PASS** | `test_invalid_inputs_and_stale_state_leave_database_unchanged`, `test_replacement_from_another_product_is_rejected`, `test_audit_failure_rolls_back_every_change`, `test_history_failure_rolls_back_every_change`; `sds_invalidation` zapisuje poprzedni status, czas, trimmed reason i replacement. Migracja wymusza niepusty reason i unikalne jednorazowe wycofanie. |
| A5 — zachowanie źródeł | **PASS** | Test `NO_CURRENT` potwierdza zachowanie `relative_path`, Safety, Components, decyzji i Evidence oraz niezmienione bajty PDF w tymczasowym katalogu. Kod invalidation nie wywołuje zapisu filesystem. |
| A6 — UI | **PASS** dla AppTest; **NOT VERIFIED** wizualnie | `tests/unit/test_task060_sds_invalidation_ui.py`: blokada zapisu bez reason/checkboxu/wyboru, brak preselect replacement, prezentacja `INVALIDATED` z powodem i datą, brak akcji dla wycofanego SDS i odczyt PDF. Fizyczne oględziny przerwał Computer Use, bo nie mógł z dostateczną pewnością ustalić adresu aktywnej przeglądarki. Nie ponawiano sterowania oknem. |
| A7 — testy/migracje/regresja | **PASS** dla aktualnego focused + izolowanego PostgreSQL; ograniczenie poniżej | 58 testów focused/AppTest PASS; 23 aktualne testy regresyjne PASS na osobnej bazie PostgreSQL. Migracja: upgrade od bazy pustej do head, downgrade bez danych, ponowny upgrade i blokada downgrade przy `INVALIDATED` PASS. Izolowany scenariusz Application + BHP na PostgreSQL PASS. |

## Walidacja i ograniczenia

- `58 passed` — `test_task060_sds_invalidation.py`, `test_task060_sds_invalidation_ui.py`, istniejący `test_product_registry_view.py`, `test_register_bhp_decision.py`, `test_streamlit_bhp_decision.py`.
- `23 passed` — na tymczasowej izolowanej bazie PostgreSQL: `test_patch009_revision_metadata.py` oraz dwa aktualne zestawy jednostkowe BHP. Baza testowa została usunięta po wykonaniu skryptu w bloku `finally`.
- PostgreSQL migration/integrity: head `e4c6f21a9d80`, tabela audytu pusta po upgrade, downgrade pustego schematu, ponowny upgrade, zapis przykładowego wycofania/przywrócenia i nowej decyzji BHP, odmowa downgrade przy danych; wszystkie kroki PASS. Nie użyto bazy operatora.
- Dodatkowa próba 17 starszych testów integracyjnych na tej samej izolowanej bazie dała `7 passed, 10 failed`. Ich fixture są niezgodne z wcześniejszymi zatwierdzonymi zmianami: brak wymaganego `usage_locations.location_code` po TASK-046 i brak Safety przed rejestracją BHP po Core v1.7. Nie zmieniano tych testów w TASK-060 i nie przypisuje się ich błędów nowej funkcji. Ryzyko: pełna historyczna regresja pozostaje niezielona.
- `git diff --check` dla zmienionych śledzonych plików zakończył się kodem 0; Git wypisał tylko ostrzeżenia o konwersji LF/CRLF. Nie wykonano pełnej regresji Level 3 zgodnie z GOV-002 dla trybu INTEGRATION.
- Fizycznego ekranu nie oceniono. Tymczasowy serwer podglądu został zatrzymany; żaden zapis w podglądzie nie był możliwy. Brak potwierdzenia układu 1920×1080 z UI-GUIDE-001 należy przekazać do acceptance.

## Zmienione pliki

- Domain/DTO/Application: `app/domain/enums/statuses.py`, `app/application/dto/__init__.py`, `app/application/dto/sds_invalidation.py`, `app/application/use_cases/__init__.py`, `app/application/use_cases/invalidate_sds.py`.
- Persistence/migracja: `app/infrastructure/db/models/__init__.py`, `app/infrastructure/db/models/documents.py`, `app/infrastructure/db/repositories/__init__.py`, `app/infrastructure/db/repositories/sds_invalidation.py`, `app/infrastructure/db/repositories/sds_acceptance.py`, `app/infrastructure/db/repositories/bhp_decision.py`, `app/infrastructure/db/repositories/bhp_decision_query.py`, `migrations/versions/e4c6f21a9d80_task_060_sds_invalidation.py`.
- UI: `app/presentation/streamlit/composition.py`, `app/presentation/streamlit/product_registry.py`.
- Testy: `tests/integration/test_task060_sds_invalidation.py`, `tests/unit/test_task060_sds_invalidation_ui.py`, `tests/unit/test_product_registry_view.py`.

Nie wykonywano wycofania rzeczywistego SDS ani migracji bazy operatora. Istniejące niezwiązane zmiany w drzewie roboczym pozostawiono bez ingerencji. **STOP po TASK-060 i tym raporcie.**
