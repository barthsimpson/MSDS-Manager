# TASK-006 REPORT

## 1. Status

DONE

PostgreSQL wymusza wszystkie trzy krytyczne reguły integralności Core. Druga
migracja jest odwracalna, baza pozostaje na `head`, testy integracyjne i
regresyjne przechodzą, a po testach nie pozostały dane biznesowe.

## 2. Zaimplementowane reguły

### Maksymalnie jeden CURRENT SDS na Product

Unikalny partial index:

```text
uq_sds_documents_one_current_per_product
UNIQUE (product_id) WHERE document_status = 'CURRENT'
```

Pozwala na wiele rekordów `ARCHIVED` dla produktu oraz po jednym `CURRENT` dla
różnych produktów.

### Maksymalnie jedna CURRENT BHP Decision na SDS

Unikalny partial index:

```text
uq_bhp_decisions_one_current_per_sds
UNIQUE (sds_id) WHERE record_status = 'CURRENT'
```

Pozwala na wiele rekordów `SUPERSEDED` dla SDS oraz po jednym `CURRENT` dla
różnych SDS. Predykat używa `record_status`, nie `decision_status`.

### Zgodność Product w BHP Decision i SDS

Dodano:

```text
uq_sds_documents_sds_product
UNIQUE (sds_id, product_id)

fk_bhp_decisions_sds_product
FOREIGN KEY (sds_id, product_id)
REFERENCES sds_documents (sds_id, product_id)
```

Baza odrzuca decyzję, której `product_id` różni się od produktu wskazanego SDS.

## 3. Strategia techniczna

- dwie reguły aktualności używają natywnych dla PostgreSQL partial unique indexes,
- zgodność pary Product + SDS używa deklaratywnego złożonego FK,
- para referencyjna w `sds_documents` jest jawnym kandydatem przez `UNIQUE`,
- prosty FK `bhp_decisions.sds_id → sds_documents.sds_id` został zastąpiony
  złożonym FK; prosty FK `product_id → products.product_id` pozostał,
- trigger nie jest potrzebny, ponieważ wszystkie reguły są jednoznacznie
  wymuszane przez indeksy i klucze,
- nie dodano workflow automatycznego archiwizowania ani supersede.

## 4. Zmiany ORM

`app/infrastructure/db/models/documents.py`:

- `SdsDocumentModel.__table_args__` zawiera partial unique index CURRENT oraz
  `UniqueConstraint(sds_id, product_id)`,
- `BhpDecisionModel.__table_args__` zawiera partial unique index CURRENT oraz
  złożony `ForeignKeyConstraint`,
- `BhpDecisionModel.sds_id` nie deklaruje już osobnego prostego FK,
- relacje Product/SDS/BhpDecision mają techniczne `overlaps`, ponieważ złożony
  FK współdzieli `product_id` z relacją Product; mappery przechodzą walidację bez
  `SAWarning`.

`app/infrastructure/db/models/catalog.py`:

- relacja `ProductModel.bhp_decisions` otrzymała wyłącznie techniczną deklarację
  `overlaps`.

Nie zmieniono modeli domenowych, enumów, pól biznesowych ani nullable.

`tests/unit/test_orm_metadata.py` rozszerzono o weryfikację obu indeksów,
unikalnej pary i złożonego FK.

## 5. Migracja

- revision id: `bae33dc76391`,
- plik: `migrations/versions/bae33dc76391_add_core_integrity_constraints.py`,
- message: `add core integrity constraints`,
- `down_revision`: `fdaac4f8756e`,
- liczba rewizji Alembic po Tasku: 2.

### Upgrade

- tworzy `uq_sds_documents_sds_product`,
- usuwa prosty `bhp_decisions_sds_id_fkey`,
- tworzy `fk_bhp_decisions_sds_product`,
- tworzy `uq_sds_documents_one_current_per_product`,
- tworzy `uq_bhp_decisions_one_current_per_sds`.

### Downgrade

- usuwa oba partial indexes,
- usuwa złożony FK,
- odtwarza prosty FK TASK-005,
- usuwa unikalność pary `(sds_id, product_id)`.

Migracja nie tworzy ani nie usuwa tabel i nie dodaje kolumn.

## 6. Review migracji przed upgrade

Plik został w całości przeczytany przed upgrade. Potwierdzono:

- nowe tabele: 0,
- usuwane tabele: 0,
- nowe pola biznesowe: 0,
- zmiany enumów: 0,
- operacje na enumowych CHECK-ach: 0,
- `ON DELETE CASCADE`: brak,
- triggery/stored procedures: brak,
- operacje poza trzema regułami Core: brak.

Autogenerate wygenerował niepoprawną technicznie kolejność: próbował utworzyć
złożony FK przed unikalnością pary referencyjnej, a w downgrade usuwał
unikalność przed zależnym FK. Ręcznie zmieniono wyłącznie kolejność operacji:

- upgrade najpierw tworzy kandydat `UNIQUE`, potem FK,
- downgrade najpierw usuwa FK, a potem kandydat `UNIQUE`.

Zestaw operacji i ich semantyka nie zostały zmienione.

## 7. Enum CHECK safety

W `migrations/env.py` dodano precyzyjny `include_object`, który odfiltrowuje
wyłącznie fałszywe operacje usunięcia odbitych CHECK-ów odpowiadających
constraintom oznaczonym w `Base.metadata` jako type-bound.

Efekt autogenerate TASK-006:

- propozycje usunięcia enumowych CHECK-ów: 0,
- CHECK-i usunięte przez migrację: 0,
- CHECK-i obecne po upgrade: 18/18,
- różnice nazw: 0,
- różnice zatwierdzonych wartości: 0,
- nieoczekiwane CHECK-i: 0.

Strategia `VARCHAR + CHECK` i semantyka enumów nie zostały zmienione.

## 8. Testy integrity

Plik: `tests/integration/test_core_integrity.py`.

Testy wymagają aktywnego lokalnego PostgreSQL oraz bazy `msds_manager` na head.
Każdy test działa we własnej transakcji zakończonej rollbackiem. Oczekiwane
błędy są izolowane savepointem i sprawdzane jako `sqlalchemy.exc.IntegrityError`
z nazwą constraintu zwróconą przez psycopg.

### Jeden CURRENT SDS

Setup:

- Product A: 1 CURRENT + 2 ARCHIVED,
- Product B: 1 CURRENT.

Oczekiwane i rzeczywiste wyniki:

- poprawna historia oraz CURRENT różnych produktów: zapis dozwolony,
- drugi CURRENT dla Product A: odrzucony przez
  `uq_sds_documents_one_current_per_product`.

### Jedna CURRENT BHP Decision

Setup:

- SDS A: 1 CURRENT decision + 2 SUPERSEDED,
- SDS B: własna CURRENT decision.

Oczekiwane i rzeczywiste wyniki:

- historia SUPERSEDED oraz CURRENT różnych SDS: zapis dozwolony,
- druga CURRENT dla SDS A: odrzucona przez
  `uq_bhp_decisions_one_current_per_sds`.

### Zgodność Product + SDS

Setup:

- Product A → SDS A,
- niezależny Product B.

Oczekiwane i rzeczywiste wyniki:

- decyzja `(Product B, SDS A)`: odrzucona przez
  `fk_bhp_decisions_sds_product`,
- decyzja `(Product A, SDS A)`: zapis dozwolony.

Wynik osobnego uruchomienia testów integrity: **3 passed**.

## 9. Testy regresji

Polecenie:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wynik: **44 passed**, kod wyjścia 0, brak `SAWarning`.

Zestaw obejmuje 41 testów jednostkowych i 3 testy integracyjne PostgreSQL.

## 10. Upgrade / downgrade / re-upgrade

### Upgrade

```text
Running upgrade fdaac4f8756e -> bae33dc76391,
add core integrity constraints
```

Wynik: kod wyjścia 0.

### Downgrade jednej rewizji

```text
Running downgrade bae33dc76391 -> fdaac4f8756e,
add core integrity constraints
```

Wynik: kod wyjścia 0. Po downgrade:

- current: `fdaac4f8756e`,
- tabele aplikacyjne: 9,
- partial indexes TASK-006: 0,
- unikalna para TASK-006: brak,
- złożony FK TASK-006: brak,
- prosty FK TASK-005: obecny,
- enumowe CHECK-i: 18.

### Re-upgrade

Wynik: kod wyjścia 0. Wszystkie constrainty TASK-006 zostały przywrócone.

## 11. PostgreSQL final state

- current revision: `bae33dc76391 (head)`,
- liczba rewizji: 2,
- liczba tabel aplikacyjnych: 9,
- partial unique indexes TASK-006: 2/2, oba `unique`,
- `uq_sds_documents_sds_product`: obecny,
- `fk_bhp_decisions_sds_product`: obecny,
- enumowe CHECK-i: 18/18,
- dane biznesowe/testowe po pełnym pytest: 0 rekordów łącznie,
- końcowy stan: head z aktywnymi trzema zabezpieczeniami.

`alembic history`:

```text
fdaac4f8756e -> bae33dc76391 (head), add core integrity constraints
<base> -> fdaac4f8756e, initial core schema
```

`alembic current`:

```text
bae33dc76391 (head)
```

## 12. Drift ORM ↔ DB

Po finalnym upgrade:

```text
alembic check
No new upgrade operations detected.
```

Kod wyjścia: 0. Rzeczywisty drift: **BRAK**.

Znany false positive enumowych CHECK-ów został odseparowany filtrem opisanym w
sekcji 7. Niezależna bezpośrednia inspekcja potwierdziła 18/18 constraintów i
identyczne z metadata zestawy dozwolonych wartości.

## 13. Architektura

- `app/domain` zmieniony: NIE,
- importy SQLAlchemy/infrastructure w domenie: BRAK,
- constraints umieszczone w persistence i migracji: TAK,
- logika workflow dodana: NIE,
- automatyczna archiwizacja/supersede: NIE,
- triggery/stored procedures: NIE,
- repositories/CRUD/use cases: NIE,
- UI zmienione: NIE,
- nowe biblioteki: NIE,
- `pyproject.toml` zmieniony: NIE.

## 14. Git / bezpieczeństwo

- obie migracje są dodane do indeksu Git (`A`),
- druga migracja TASK-006 jest śledzona w indeksie,
- commit wykonany: NIE,
- `git diff --check`: kod 0,
- `git diff --cached --check`: kod 0,
- `.env` ignored: TAK,
- `.env` tracked: NIE,
- `.env` zmieniony/ujawniony: NIE,
- sekrety dodane: NIE,
- dumpy/backupy/pliki lokalnej bazy: BRAK,
- dokumenty SDS/BHP w Git: BRAK,
- systemowy `PATH` zmieniony: NIE.

## 15. Odstępstwa

BRAK odstępstw biznesowych lub architektonicznych.

Wykonano dozwoloną techniczną korektę kolejności operacji w wygenerowanej
migracji oraz filtr znanego false positive type-bound CHECK-ów. Obie zmiany są
opisane w sekcjach 6 i 7.

## 16. Problemy / ryzyka

- pierwsza próba autogenerate TASK-006 zatrzymała się przed utworzeniem pliku z
  powodu błędu wcięcia w `migrations/env.py`; poprawiono wcięcie i sprawdzono
  moduł przez `py_compile`, bez wpływu na bazę,
- przyszłe zmiany enumowych CHECK-ów wymagają nadal osobnej, jawnej inspekcji ich
  wartości, ponieważ filtr celowo chroni znane type-bound constrainty przed
  fałszywym usunięciem,
- przejścia CURRENT → ARCHIVED i CURRENT → SUPERSEDED wymagają przyszłego
  workflow; TASK-006 jedynie blokuje stan niepoprawny.

## 17. Kandydaci do przyszłych decyzji

BRAK nowych reguł integralności do zatwierdzenia w ramach tego Tasku.

Przyszły workflow powinien wykonać zmianę statusu poprzedniego rekordu przed
utworzeniem nowego CURRENT, ale nie został zaprojektowany ani zaimplementowany.

## 18. Następny krok

OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-007.
