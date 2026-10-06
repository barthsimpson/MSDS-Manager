# TASK-046 REPORT

STATUS:
DONE

PRE-FLIGHT:
- revision before: `c7e5a82d9043`; jeden head Alembic przed dodaniem migracji.
- usage_locations: 3.
- NULL codes: 0.
- blank codes: 0.
- duplicate codes: 0.
- format violations: 0.
- fingerprint before (SHA-256 pól `location_id`, `location_code`, `location_name`, `status`, uporządkowanych po `location_id`): `ab2ace87ece20beea1162b622bf68b4de9dc2d5bdbd489c513cc6c0ad76eba4c`.
- usage_location_history: 0; product_usage_locations: 1. Powtórzony pre-flight bezpośrednio przed migracją był identyczny.

MIGRATION:
- revision id: `d8f3a21c6046`.
- previous head: `c7e5a82d9043`.
- new head: `d8f3a21c6046`.
- operation: wyłącznie `usage_locations.location_code VARCHAR(32) SET NOT NULL`; ORM odzwierciedla `nullable=False`.
- backfill: NO.

ISOLATED VALIDATION:
- upgrade przy kompletnych kodach: PASS.
- NULL rejection: PASS — PostgreSQL odrzucił upgrade; rewizja i rekord legacy pozostały bez zmian.
- downgrade do nullable: PASS.
- re-upgrade do NOT NULL: PASS.
- CHECK i UNIQUE: zachowane po upgrade, downgrade i re-upgrade.
- lokalizacje, historia i przypisania produktu: fingerprint niezmieniony.
- `alembic check`: `No new upgrade operations detected.`
- focused tests na izolowanym PostgreSQL: 72 passed, 1 skipped. Fixture’y testowe tworzące nowe lokalizacje dostosowano do formatu symbolu.

OPERATOR DB:
- upgrade: `alembic upgrade d8f3a21c6046` — PASS.
- nullable after: NO; typ `VARCHAR(32)`; CHECK i UNIQUE obecne.
- row counts before/after: `usage_locations` 3/3, `usage_location_history` 0/0, `product_usage_locations` 1/1.
- fingerprint after: `ab2ace87ece20beea1162b622bf68b4de9dc2d5bdbd489c513cc6c0ad76eba4c`.
- operator data preserved: YES — snapshot wszystkich istniejących pól lokalizacji identyczny przed i po.

VALIDATION:
- alembic current: `d8f3a21c6046 (head)`.
- alembic check: `No new upgrade operations detected.`
- focused unit + odczytowy shell na bazie operatora: 48 passed, bez zapisu danych.
- git diff --check: PASS dla zmian śledzonych.

SCOPE:
- business data changed: NO.
- UI change: NO.
- Application change: NO.
- Core change: NO.
- dependencies: NO.
- workflow `AssignLegacyUsageLocationCode`: zachowany.

DEVIATIONS:
- Pierwsze uruchomienie TASK-046 zakończyło się `BLOCKED` przy jednym kodzie NULL. Po uzupełnieniu symbolu przez użytkownika ponowiony pre-flight przeszedł; TASK-046 nie nadawał symboli.
- Historyczne testy TASK-043/045, które wymagają nullable legacy, pozostają testami etapu foundation; focused walidacja hardening użyła testów zgodnych z nowym head.
- Tymczasowy snapshot operatora i skrypty diagnostyczne usunięto po porównaniu danych. Zastane zmiany repozytorium pozostawiono bez zmian.

NEXT:
- READY FOR CERBERUS REVIEW.
