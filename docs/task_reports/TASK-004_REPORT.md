# TASK-004 REPORT

## 1. Status

DONE

Warstwa persistence SQLAlchemy 2.x odwzorowuje wszystkie 9 modeli domenowych.
`Base.metadata` jest podłączone do Alembic, ale nie wygenerowano rewizji, nie
uruchomiono migracji i nie utworzono tabel.

## 2. Wykonano

- utworzono jawny `DeclarativeBase` o nazwie `Base`,
- dodano 9 modeli ORM w `app/infrastructure/db/models/`,
- odwzorowano podstawowe PK, FK i wymagane relacje Core,
- zachowano relacje 1:1 dla profilu bezpieczeństwa i dowodu decyzji,
- odwzorowano enumy jako `VARCHAR + CHECK`,
- odwzorowano domenowy `Decimal` jako `Numeric`,
- kolekcje H-statements odwzorowano jako PostgreSQL `ARRAY(String)`,
- ustawiono `target_metadata = Base.metadata` w Alembic,
- dodano testy wyłącznie na poziomie metadata,
- wykonano testy regresyjne i odczytowe kontrole PostgreSQL.

Nie wykonano `create_all`, `alembic revision`, `alembic upgrade` ani żadnego DDL.

## 3. Utworzone pliki

- `app/infrastructure/db/models/base.py`,
- `app/infrastructure/db/models/column_types.py`,
- `app/infrastructure/db/models/catalog.py`,
- `app/infrastructure/db/models/documents.py`,
- `app/infrastructure/db/models/safety.py`,
- `tests/unit/test_orm_metadata.py`,
- `docs/task_reports/TASK-004_REPORT.md`.

## 4. Zmienione pliki

- `app/infrastructure/db/models/__init__.py`,
- `migrations/env.py`.

Nie zmieniono domeny, presentation, `pyproject.toml`, `.env` ani dokumentów Core.

## 5. Mapa Domain → ORM 9 → 9

| Domain Model | ORM Model | Tabela | PK | Główne FK | Istotne nullable | Odstępstwa |
|---|---|---|---|---|---|---|
| `Manufacturer` | `ManufacturerModel` | `manufacturers` | `manufacturer_id` | brak | brak | brak |
| `Product` | `ProductModel` | `products` | `product_id` | `manufacturer_id → manufacturers` | brak | brak |
| `UsageLocation` | `UsageLocationModel` | `usage_locations` | `location_id` | brak | brak | `status` pozostaje tekstem, bez nowego enumu |
| `ProductUsageLocation` | `ProductUsageLocationModel` | `product_usage_locations` | `(product_id, location_id)` | `product_id → products`, `location_id → usage_locations` | brak | techniczny złożony PK, brak osobnego identyfikatora |
| `SdsDocument` | `SdsDocumentModel` | `sds_documents` | `sds_id` | `product_id → products` | `issue_date`, `revision` | brak |
| `BhpDecision` | `BhpDecisionModel` | `bhp_decisions` | `decision_id` | `product_id → products`, `sds_id → sds_documents`, `evidence_id → decision_evidence` | `notes` | `evidence_id` jest unikalnym FK dla relacji 1:1 |
| `DecisionEvidence` | `DecisionEvidenceModel` | `decision_evidence` | `evidence_id` | brak | brak | relacja zwrotna 1:1 jest opcjonalna po stronie samodzielnego dowodu |
| `SafetyProfile` | `SafetyProfileModel` | `safety_profiles` | `sds_id` | `sds_id → sds_documents` | `product_definition`, `clp_classification_text`, `signal_word`, `last_manual_edit_at` | `sds_id` jest równocześnie PK i FK, co egzekwuje 1:1 |
| `SdsComponent` | `SdsComponentModel` | `sds_components` | `component_id` | `sds_id → sds_documents` | `cas_number`, `ec_number`, `reach_registration_number`, `concentration_text`, `classification_text` | brak |

## 6. Relacje i klucze

- `ManufacturerModel.products` ↔ `ProductModel.manufacturer` — 1:N,
- `ProductModel.product_usage_locations` ↔
  `UsageLocationModel.product_usage_locations` przez rekord asocjacyjny — N:M,
- `ProductModel.sds_documents` ↔ `SdsDocumentModel.product` — 1:N,
- `SdsDocumentModel.safety_profile` ↔ `SafetyProfileModel.sds_document` — 1:1,
- `SdsDocumentModel.components` ↔ `SdsComponentModel.sds_document` — 1:N,
- `SdsDocumentModel.bhp_decisions` ↔ `BhpDecisionModel.sds_document` — 1:N,
- `ProductModel.bhp_decisions` ↔ `BhpDecisionModel.product` — 1:N,
- `BhpDecisionModel.evidence` ↔ `DecisionEvidenceModel.decision` — 1:1.

Nie ustawiono `ON DELETE CASCADE` ani ORM-owego cascade delete. Nie dodano
zaawansowanych constraintów procesowych przeznaczonych dla TASK-006.

## 7. Strategia enumów

Wszystkie zatwierdzone enumy używają jednej strategii SQLAlchemy:

- `Enum(..., native_enum=False)`,
- przechowywanie jako `VARCHAR`,
- jawny `CHECK` z zatwierdzonymi wartościami,
- `validate_strings=True`,
- stabilna nazwa constraintu,
- wartości pochodzą bezpośrednio z enumów domenowych.

Strategia jest prosta i odwracalna oraz nie tworzy natywnych typów PostgreSQL
przed zatwierdzeniem przyszłej migracji.

## 8. Typy istotne

- `quantity_value`: `Numeric`, nigdy `Float`; zachowuje semantykę `Decimal`,
- `issue_date`: `Date`,
- `registered_at`, `approved_at`, `last_manual_edit_at`: `DateTime` bez dodawania
  nowej polityki timezone ani server defaults,
- `hazard_statements` i `supplemental_hazard_statements`: PostgreSQL
  `ARRAY(String)`, zachowują kolejność i nie tworzą dodatkowej encji CLP,
- identyfikatory i pozostałe teksty: `String`, bez narzucania niezatwierdzonej
  strategii UUID lub limitów długości.

## 9. Alembic

- `target_metadata`: `Base.metadata`,
- `.\.venv\Scripts\python.exe -m alembic history`: OK, kod wyjścia 0,
- liczba plików rewizji: 0,
- `alembic revision --autogenerate`: NIE URUCHOMIONO,
- `alembic upgrade`: NIE URUCHOMIONO.

## 10. PostgreSQL

Wykonano wyłącznie diagnostyczny `SELECT` z `information_schema`.

- liczba tabel poza `pg_catalog` i `information_schema`: **0**,
- utworzone tabele: 0,
- zmodyfikowane dane: brak.

## 11. Testy — polecenia i wyniki

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Wynik końcowy: **40 passed**, kod wyjścia 0.

12 nowych testów metadata-level pokrywa:

- dokładny zestaw 9 tabel,
- PK i FK,
- strukturę tabeli asocjacyjnej,
- obie relacje 1:1,
- dokładne wartości i strategię enumów,
- `Numeric` zamiast `Float`,
- nullable pól opcjonalnych i non-null pól wymaganych,
- brak niezatwierdzonych kolumn i tabel,
- brak wywołania `create_all`,
- brak cascade delete.

Dodatkowo wszystkie 28 testów z TASK-001..003 pozostało zielonych.

Kompilacja wszystkich 9 definicji `CreateTable` dla dialektu PostgreSQL w
pamięci: OK. Definicje nie zostały wykonane na bazie.

## 12. Kontrola architektury

- modele ORM znajdują się wyłącznie w `app/infrastructure/db/models`: TAK,
- `app/domain` importuje SQLAlchemy/infrastructure/UI: NIE,
- modele domenowe zmienione pod ORM: NIE,
- presentation zmienione: NIE,
- CRUD/repositories/use cases dodane: NIE,
- `create_all()` w kodzie aplikacji/migracji/skryptach: NIE,
- migracje lub tabele utworzone: NIE,
- nowe biblioteki: NIE,
- `pyproject.toml` zmieniony: NIE.

## 13. Odstępstwa

BRAK.

## 14. Problemy / ryzyka

- constrainty procesowe „jeden CURRENT” i zgodność produktu decyzji z produktem
  SDS pozostają celowo poza zakresem do TASK-006,
- `ARRAY(String)` jest świadomie PostgreSQL-specific, zgodnie z zatwierdzonym
  stosem technicznym,
- schemat istnieje obecnie tylko jako metadata i wymaga osobno zatwierdzonej
  migracji w przyszłym Tasku.

## 15. Pytania do Cerberusa

BRAK.

## 16. Git / bezpieczeństwo

- `.env` ignored: TAK,
- `.env` tracked: NIE,
- `.env` zmieniony lub ujawniony: NIE,
- sekrety dodane: NIE,
- dokumenty SDS/BHP dodane do repozytorium: NIE,
- lokalne pliki baz danych dodane: NIE,
- konfiguracja PostgreSQL lub systemowy `PATH` zmienione: NIE.

Plik specyfikacji `docs/tasks/TASK-004_SQLAlchemy_Persistence_Mapping.md` był
nieśledzony już na wejściu i nie został zmodyfikowany w ramach implementacji.

## 17. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-005.
