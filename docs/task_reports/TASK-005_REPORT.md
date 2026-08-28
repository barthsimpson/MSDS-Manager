# TASK-005 REPORT

## 1. Status

DONE

Utworzono, zweryfikowano i zastosowano jedną początkową migrację Core. Test
downgrade/re-upgrade i test idempotencji zakończyły się poprawnie. Lokalna baza
`msds_manager` pozostaje na `head` z dokładnie 9 tabelami aplikacyjnymi.

## 2. Rewizja

- revision id: `fdaac4f8756e`,
- plik: `migrations/versions/fdaac4f8756e_initial_core_schema.py`,
- message: `initial core schema`,
- `down_revision`: `None`,
- liczba rewizji: 1.

Plik został wygenerowany poleceniem:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "initial core schema"
```

Przed generowaniem potwierdzono bez ujawniania poświadczeń, że celem jest
`localhost:5432/msds_manager`, a baza ma 0 tabel aplikacyjnych.

## 3. Review wygenerowanej migracji

Plik został w całości odczytany i zweryfikowany przed pierwszym upgrade.

### Tabele

Migracja tworzy dokładnie 9 tabel:

- `manufacturers`,
- `products`,
- `usage_locations`,
- `product_usage_locations`,
- `sds_documents`,
- `bhp_decisions`,
- `decision_evidence`,
- `safety_profiles`,
- `sds_components`.

`upgrade()` zawiera 9 wywołań `op.create_table`, a `downgrade()` 9 wywołań
`op.drop_table` w kolejności bezpiecznej względem FK.

### PK i FK

- wszystkie tabele mają oczekiwane PK,
- `product_usage_locations` ma złożony PK `(product_id, location_id)`,
- obecny jest FK Manufacturer → Product,
- obecne są FK Product/UsageLocation → ProductUsageLocation,
- obecny jest FK Product → SDS,
- obecne są FK SDS/Product → BhpDecision,
- `BhpDecision.evidence_id` jest unikalnym FK do `decision_evidence`,
- `SafetyProfile.sds_id` jest PK i FK do SDS,
- obecne są FK SDS → SdsComponent.

### Enumy i typy

- 18 kolumn enumowych używa `VARCHAR + CHECK`, `native_enum=False` i wyłącznie
  zatwierdzonych wartości,
- `quantity_value` używa `Numeric`, nie `Float`,
- `issue_date` używa `Date`,
- timestampy używają `DateTime`,
- 3 kolekcje H-statements używają PostgreSQL `ARRAY(String)`.

### Nullable

Potwierdzono nullable dla:

- `sds_documents.issue_date`,
- `sds_documents.revision`,
- `bhp_decisions.notes`,
- `safety_profiles.product_definition`,
- `safety_profiles.clp_classification_text`,
- `safety_profiles.signal_word`,
- `safety_profiles.last_manual_edit_at`,
- opcjonalnych danych `sds_components`.

### Brak elementów poza zakresem

- brak `peak_factory_quantity`, `decided_by`, `decision_date` i confidence score,
- brak tabel dostawców, magazynowych, użytkowników, REACH i słowników CLP,
- brak `ON DELETE CASCADE`,
- brak zaawansowanych constraintów TASK-006,
- brak danych seed.

## 4. Ręczne korekty migracji

Usunięto jedną końcową spację z dokumentacyjnego nagłówka `Revises:` po
wykryciu przez `git diff --cached --check`. Była to wyłącznie korekta
formatowania; kod `upgrade()`, `downgrade()` i semantyka migracji nie zostały
zmienione.

Przed autogenerate zmieniono wyłącznie `migrations/env.py`, aby Alembic pobierał
rzeczywisty URL przez `load_settings()` zamiast placeholdera z `alembic.ini`.
Sekret nie został zapisany w konfiguracji ani raporcie.

## 5. Upgrade

Polecenie:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Wynik pierwszego wykonania: kod wyjścia 0, wykonano:

```text
Running upgrade  -> fdaac4f8756e, initial core schema
```

## 6. PostgreSQL po upgrade

- `alembic_version`: `fdaac4f8756e`,
- tabela `alembic_version`: istnieje,
- liczba tabel aplikacyjnych: 9,
- dodatkowe tabele aplikacyjne: brak.

Końcowa lista tabel:

```text
bhp_decisions
decision_evidence
manufacturers
product_usage_locations
products
safety_profiles
sds_components
sds_documents
usage_locations
```

Nie wprowadzono żadnych danych biznesowych.

## 7. Downgrade / re-upgrade

### Downgrade

```powershell
.\.venv\Scripts\python.exe -m alembic downgrade base
```

- wynik: kod wyjścia 0,
- liczba tabel aplikacyjnych po downgrade: 0,
- liczba rekordów w `alembic_version`: 0.

### Re-upgrade

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

- wynik: kod wyjścia 0,
- ponownie utworzono dokładnie 9 tabel,
- `alembic_version`: `fdaac4f8756e`,
- końcowy stan bazy: `head`.

## 8. Idempotencja

Ponowne wykonanie `alembic upgrade head` na bazie będącej już na `head`
zakończyło się kodem 0. Nie próbowano ponownie tworzyć tabel i nie wystąpił błąd.

## 9. Drift ORM ↔ schema

Rzeczywisty wynik szczegółowego porównania:

- drift poza enumowymi CHECK-ami: 0,
- oczekiwane enumowe CHECK-i: 18,
- CHECK-i obecne w PostgreSQL: 18,
- różnice nazw lub dozwolonych wartości: 0,
- nieoczekiwane CHECK-i: 0.

Surowe `alembic check` zwróciło fałszywy alarm dotyczący usunięcia 18 CHECK-ów.
Przyczyną jest ograniczenie pluginu porównującego: constrainty wygenerowane przez
`Enum(native_enum=False, create_constraint=True)` są w metadata oznaczone jako
SQLAlchemy `type-bound`, więc nie zostały skojarzone z odpowiadającymi im
constraintami odczytanymi z PostgreSQL.

W celu wykluczenia rzeczywistego driftu wykonano dwa niezależne porównania:

1. Alembic `compare_metadata` po pominięciu wyłącznie 18 znanych, type-bound
   CHECK-ów — 0 różnic dla tabel, kolumn, typów, nullable, PK, FK i unique.
2. Bezpośrednia inspekcja wszystkich CHECK-ów — identyczne nazwy i dokładne
   zestawy zatwierdzonych wartości dla 18/18 constraintów.

Nie wygenerowano drugiej migracji, nie usunięto CHECK-ów i nie zmieniono ORM.

## 10. Testy

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Wynik: **40 passed**, kod wyjścia 0. Wszystkie testy domenowe, konfiguracji,
fabryk DB i metadata ORM pozostały zielone.

## 11. Alembic history/current

`alembic history`:

```text
<base> -> fdaac4f8756e (head), initial core schema
```

`alembic current`:

```text
fdaac4f8756e (head)
```

Oba polecenia zakończyły się kodem 0.

## 12. Git / bezpieczeństwo

- migracja znajduje się w repozytorium i została dodana do indeksu Git (`A`),
- nie wykonano commita,
- `.env` jest ignorowany: TAK,
- `.env` jest śledzony: NIE,
- `.env` zmieniony lub ujawniony: NIE,
- hasła/sekrety dodane do plików: NIE,
- dokumenty SDS/BHP dodane: NIE,
- dumpy, backupy i lokalne pliki baz danych dodane: NIE,
- nowe biblioteki: NIE,
- konfiguracja systemowego PostgreSQL lub systemowy `PATH` zmienione: NIE.

Do `PATH` dodawano katalog PostgreSQL wyłącznie w środowisku poszczególnych
procesów kontrolnych.

## 13. Odstępstwa

BRAK odstępstw od modelu Core/ORM i zakresu migracji.

Surowy `alembic check` nie może obecnie służyć samodzielnie do kontroli driftu
enumowych CHECK-ów; zastosowano dozwoloną przez Task inspekcję SQLAlchemy i
szczegółowe porównanie wartości constraintów.

## 14. Problemy / ryzyka

- przyszły surowy autogenerate/check może ponownie zaproponować usunięcie
  type-bound CHECK-ów; każda taka propozycja wymaga review i nie może być
  automatycznie zastosowana,
- zaawansowane constrainty procesowe pozostają celowo poza zakresem TASK-005.

## 15. Pytania do Cerberusa

BRAK pytań blokujących. W przyszłym zadaniu technicznym można rozważyć jawne
ustandaryzowanie filtra porównywania type-bound CHECK-ów, bez zmiany ich
semantyki ani generowania migracji usuwającej constrainty.

## 16. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-006.
