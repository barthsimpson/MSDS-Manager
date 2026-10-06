# TDR-011 — ANALYTICS-03 — Review Snapshot Model / Schema

**Projekt:** MSDS Manager  
**Dokument:** TDR-011  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Data:** 2026-10-06  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Podstawa biznesowa:** BDR-011 v1.0-approved  
**Podstawa Core:** CORE-001 v1.5-approved  

---

## 1. Cel decyzji technicznej

TDR-011 definiuje techniczny model:

```text
ANALYTICS-03
Raport przeglądu / Stan na dzień
```

dla zatwierdzonych obiektów Core:

```text
REVIEW
REVIEW_ITEM
```

Dokument rozstrzyga model Domain, persistence PostgreSQL, constraints i indeksy, zamrożenie populacji DRAFT, baseline MAX i jednostkę, `observed_quantity`, finalizację `DRAFT → FINAL`, immutability `FINAL`, odczyt ostatniego `FINAL` dla ANALYTICS-02, migrację Alembic oraz granice Application / Repository / UI.

TDR-011 nie autoryzuje implementacji.

---

## 2. Kontekst obowiązujący

Minimalny authoritative context dla przyszłej implementacji:

```text
BDR-011 v1.0-approved
CORE-001 v1.5-approved
BDR-006 v1.0-approved
TDR-004 v1.0-approved
TDR-005 v1.0-approved
TDR-001
TDR-002
TDR-003
GOV-001
GOV-002
CHECKPOINT-009
```

Nie należy ponownie analizować całej historii projektu bez konkretnej potrzeby.

---

## 3. Zasada architektoniczna

Przegląd jest osobnym mechanizmem persistence:

```text
REVIEW / REVIEW_ITEM
```

i nie jest implementowany poprzez:

```text
PRODUCT_USAGE_LOCATION_HISTORY
```

Obowiązuje:

```text
current Core data
→ CreateReview
→ snapshot REVIEW / REVIEW_ITEM
→ operator observations
→ FinalizeReview
→ immutable FINAL
```

Historia Core i fizyczny przegląd pozostają rozdzielone.

---

## 4. Nazwy techniczne persistence

Proponowane mapowanie:

```text
Core REVIEW
→ physical_reviews

Core REVIEW_ITEM
→ physical_review_items
```

Domain:

```text
PhysicalReview
PhysicalReviewItem
ReviewStatus
```

Nazwy klas mogą zostać minimalnie dopasowane do istniejącego stylu repo, bez zmiany semantyki.

---

## 5. `physical_reviews`

Proponowany schema:

```text
physical_reviews
├── review_id      UUID PK
├── review_date    DATE NOT NULL
├── status         VARCHAR NOT NULL
├── created_at     TIMESTAMPTZ NOT NULL
└── finalized_at   TIMESTAMPTZ NULL
```

Status:

```text
DRAFT
FINAL
```

Preferowany model statusu: string + CHECK, zgodnie z istniejącym stylem projektu.

Constraints:

```text
CHECK status IN ('DRAFT', 'FINAL')
```

oraz:

```text
DRAFT → finalized_at IS NULL
FINAL → finalized_at IS NOT NULL
```

Nie wprowadzamy:

```text
approved_by
updated_at
cancelled_at
version number
```

bez nowej potrzeby.

---

## 6. Maksymalnie jeden aktywny DRAFT

Wymóg Core:

```text
maksymalnie 1 DRAFT
```

chroni PostgreSQL częściowym indeksem unikalnym:

```text
UNIQUE(status)
WHERE status = 'DRAFT'
```

Application wykonuje wcześniejszą kontrolę dla czytelnego komunikatu, ale DB constraint pozostaje ochroną przed race condition.

Nie tworzymy osobnej tabeli locków ani singletona.

---

## 7. `physical_review_items`

Proponowany schema:

```text
physical_review_items
├── review_item_id         UUID PK
├── review_id              UUID NOT NULL FK
├── product_id             UUID NOT NULL FK
├── location_id            UUID NOT NULL FK
├── baseline_max_quantity  NUMERIC NOT NULL
├── baseline_unit_id       UUID NOT NULL FK
└── observed_quantity      NUMERIC NULL
```

`baseline_max_quantity` i `observed_quantity` używają tego samego technicznego typu / precision / scale co istniejące `PRODUCT_USAGE_LOCATION.peak_quantity_value`, o ile repo nie ujawni sprzeczności.

Nie tworzymy osobnego:

```text
observed_unit_id
```

ponieważ:

```text
observed_unit = baseline_unit
```

jest regułą Core.

---

## 8. FK i ochrona danych historycznych

Relacje:

```text
physical_review_items.review_id
→ physical_reviews.review_id

physical_review_items.product_id
→ products.product_id

physical_review_items.location_id
→ usage_locations.location_id

physical_review_items.baseline_unit_id
→ unit_of_measure.unit_id
```

Dla `FINAL` nie stosujemy kasowania kaskadowego PRODUCT / USAGE_LOCATION / UNIT_OF_MEASURE.

Preferowane:

```text
ON DELETE RESTRICT / NO ACTION
```

---

## 9. Constraints REVIEW_ITEM

Minimalnie:

```text
baseline_max_quantity >= 0

observed_quantity IS NULL
OR observed_quantity >= 0
```

oraz:

```text
UNIQUE(review_id, product_id, location_id)
```

`0` pozostaje poprawną wartością.

`NULL` oznacza „nie sprawdzono / brak wiarygodnego wyniku”.

---

## 10. `difference`

Nie zapisujemy kolumny:

```text
difference
```

Różnica jest wyliczana:

```text
observed_quantity - baseline_max_quantity
```

Dla:

```text
observed_quantity IS NULL
```

wynik również jest `NULL`.

Powód: wartość jest pochodna i jej zapis tworzyłby ryzyko niespójności.

---

## 11. Utworzenie DRAFT — `CreatePhysicalReview`

Use case:

```text
CreatePhysicalReview(review_date)
```

wykonuje jedną transakcję:

```text
1. sprawdź brak aktywnego DRAFT
2. INSERT physical_reviews(status=DRAFT)
3. SELECT PRODUCT_USAGE_LOCATION
   JOIN USAGE_LOCATION
   WHERE USAGE_LOCATION.status = ACTIVE
4. INSERT physical_review_items
   z baseline MAX i baseline_unit_id
5. COMMIT
```

Nagłówek i pełna populacja powstają atomowo.

### Brak populacji

Jeżeli brak pozycji:

```text
EMPTY_REVIEW_POPULATION
```

i DRAFT nie powstaje.

---

## 12. Zamrożenie populacji

Po utworzeniu DRAFT `physical_review_items` nie są synchronizowane z current state.

Późniejsze zmiany:

```text
PRODUCT_USAGE_LOCATION
USAGE_LOCATION.status
peak_quantity
unit
```

nie zmieniają snapshotu.

Nie implementujemy:

```text
RefreshReviewPopulation
SyncReviewWithCurrentState
```

w MVP.

---

## 13. Aktualizacja obserwacji

Use case:

```text
UpdateReviewObservedQuantity(
    review_item_id,
    observed_quantity: Decimal | None
)
```

Reguły:

```text
parent REVIEW musi być DRAFT
observed_quantity = NULL albo >= 0
```

Repository wykonuje update tylko dla pozycji należącej do DRAFT.

Dla FINAL:

```text
FINAL_REVIEW_IMMUTABLE
```

Nie wystawiamy generycznego update omijającego lifecycle.

---

## 14. Odrzucenie rozpoczętego DRAFT

TDR-011 dopuszcza techniczną operację:

```text
DiscardPhysicalReviewDraft
```

wyłącznie dla:

```text
status = DRAFT
```

Powód:

- DRAFT nie jest zatwierdzonym historycznym wynikiem,
- Core dopuszcza tylko jeden aktywny DRAFT,
- przypadkowo rozpoczęty DRAFT nie może trwale blokować kolejnego przeglądu.

Operacja:

```text
DELETE physical_review_items
DELETE physical_reviews
```

w jednej transakcji.

Nie dodajemy statusu:

```text
CANCELLED
```

i nie zachowujemy porzuconych DRAFT jako historii.

Nigdy nie wolno zastosować tej operacji do FINAL.

---

## 15. Finalizacja — `FinalizePhysicalReview`

Use case:

```text
FinalizePhysicalReview(review_id)
```

wykonuje:

```text
DRAFT → FINAL
finalized_at = current timestamp
```

Finalizacja:

- nie modyfikuje REVIEW_ITEM,
- nie wymaga wypełnienia wszystkich `observed_quantity`,
- nie podstawia `0` za `NULL`,
- nie aktualizuje MAX,
- nie zapisuje historii Core.

Kontrolowane błędy:

```text
REVIEW_ALREADY_FINAL
REVIEW_NOT_FOUND
```

---

## 16. Ostrzeżenie przed niepełnym FINAL

Przed finalizacją kontrakt read/Application udostępnia:

```text
total_items
observed_items
unobserved_items
```

Jeżeli `unobserved_items > 0`, UI wymaga świadomego potwierdzenia finalizacji.

Application nie blokuje finalizacji, ponieważ BDR-011 dopuszcza FINAL z NULL.

---

## 17. Immutability FINAL

Immutability realizują kontrolowane write contracts:

```text
UpdateReviewObservedQuantity
→ tylko DRAFT

DiscardPhysicalReviewDraft
→ tylko DRAFT

FinalizePhysicalReview
→ tylko DRAFT → FINAL
```

Po FINAL repozytorium nie udostępnia operacji:

```text
update final
reopen final
delete final
replace items
```

Nie wprowadzamy triggerów PostgreSQL wyłącznie dla immutability.

Powód:

- projekt wykorzystuje Application-controlled writes,
- dodatkowa logika proceduralna DB byłaby nieproporcjonalna,
- constraints DB nadal chronią status i strukturę danych.

---

## 18. Ostatni FINAL dla ANALYTICS-02

Read model dla:

```text
PRODUCT × USAGE_LOCATION
```

wyznacza najnowszy snapshot według:

```text
review_date DESC
finalized_at DESC
```

Dopuszczalne technicznie jest użycie `ROW_NUMBER()` lub równoważnego SQLAlchemy.

### Semantyka NULL

Jeżeli najnowszy FINAL zawiera:

```text
observed_quantity = NULL
```

read model:

```text
NIE cofa się
do starszego FINAL z wartością
```

Pokazuje brak wyniku w najnowszym przeglądzie.

---

## 19. Read contracts

Minimalnie:

```text
GetActivePhysicalReviewDraft
GetPhysicalReview(review_id)
ListPhysicalReviews
GetLatestFinalReviewItemsForAnalytics
```

DTO pozycji może zawierać:

```text
review_item_id
product_id
product_name
location_id
location_code
location_name
baseline_max_quantity
unit_code
observed_quantity
difference
```

Nazwy display są odczytywane z aktualnych encji po stabilnych FK.

Nie kopiujemy nazw display do REVIEW_ITEM bez zatwierdzonej potrzeby.

---

## 20. Minimalne indeksy

Poza PK / UNIQUE / FK:

```text
physical_reviews(status)
physical_reviews(review_date, finalized_at)

physical_review_items(review_id)
physical_review_items(product_id, location_id, review_id)
```

oraz częściowy UNIQUE dla DRAFT.

Nie dodajemy indeksów „na przyszłość”.

---

## 21. Migracja Alembic

Jedna minimalna migracja tworzy:

```text
physical_reviews
physical_review_items
constraints
FK
indexes
```

Bez:

```text
backfill
migracji danych biznesowych
zmiany istniejących PRODUCT / LOCATION / UOM
```

Znany head z CHECKPOINT-009:

```text
d8f3a21c6046
```

Przyszły Task wykonuje pre-flight:

```text
alembic current
alembic heads
alembic check
```

Multiple heads / niejasny stan:

```text
STOP / BLOCKED
```

---

## 22. Upgrade / downgrade

Migracja posiada:

```text
upgrade
downgrade
```

Walidacja izolowanego PostgreSQL:

```text
upgrade
→ schema/constraints/indexes PASS
→ create DRAFT PASS
→ second DRAFT rejected
→ item constraints PASS
→ FINAL timestamp consistency PASS
→ downgrade PASS
→ re-upgrade PASS
→ alembic check PASS
```

Downgrade nie jest wykonywany na operator DB w normalnym wdrożeniu.

---

## 23. Domain

Minimalnie:

```text
PhysicalReview
PhysicalReviewItem
ReviewStatus
```

Reguły:

```text
ReviewStatus = DRAFT | FINAL

baseline_max_quantity >= 0
observed_quantity = None | Decimal >= 0
```

Domain nie zna SQLAlchemy, Streamlit, PostgreSQL ani Alembic.

---

## 24. Repository / transaction boundaries

Przegląd wykorzystuje istniejący mechanizm transakcji projektu.

Nie tworzymy nowego Unit of Work.

Atomowe są:

```text
CreatePhysicalReview:
header + pełna populacja items

DiscardPhysicalReviewDraft:
items + header

FinalizePhysicalReview:
status + finalized_at
```

Błąd:

```text
ROLLBACK
```

---

## 25. UI — granica TDR

Ekran:

```text
Analizy
→ Raport przeglądu
```

Minimalny workflow:

```text
brak DRAFT
→ Utwórz przegląd
→ wybierz review_date
→ utwórz snapshot

DRAFT
→ tabela pozycji
→ wpisuj / zmieniaj observed_quantity
→ NULL dozwolony
→ Zatwierdź przegląd
→ opcjonalnie Odrzuć draft

FINAL
→ read-only
```

TDR nie definiuje finalnego layoutu, kolorystyki, eksportu ani mobile/barcode UX.

---

## 26. Obsługa błędów

Minimalnie:

```text
ReviewDraftAlreadyExistsError
EmptyReviewPopulationError
ReviewNotFoundError
ReviewAlreadyFinalError
FinalReviewImmutableError
InvalidObservedQuantityError
```

Nazwy klas mogą zostać dopasowane do konwencji repo.

---

## 27. Data safety

Implementacja nie może modyfikować:

```text
existing PRODUCT data
PRODUCT_USAGE_LOCATION MAX
UNIT_OF_MEASURE
USAGE_LOCATION lifecycle
historii Core
```

Operator DB po migracji otrzymuje nowe puste tabele.

Pierwszy REVIEW powstaje dopiero po świadomej akcji użytkownika.

---

## 28. Validation zgodna z GOV-002

### Foundation / schema Task

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
```

Wymagane:

- focused Domain/schema tests,
- PostgreSQL integration,
- upgrade/downgrade/re-upgrade,
- constraints/FK/indexes,
- Alembic current/check,
- operator data safety.

Bez pełnego E2E.

### Application / UI Task

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
```

Wymagane:

- focused Application tests,
- transakcje,
- latest FINAL query,
- Streamlit/AppTest,
- powiązana regresja Analytics.

### Closure

Pełny LEVEL 3 dopiero przy acceptance/checkpoint ANALYTICS-03.

---

## 29. Proponowany podział implementacji

Po zatwierdzeniu TDR:

```text
Task A
Foundation + Domain + Schema

Task B
Application + Read Model + UI

Task C
Acceptance / Checkpoint
```

Numeracja Tasków / Sprintu zostanie ustalona osobno.

---

## 30. Poza zakresem

TDR-011 nie implementuje:

```text
export PDF/XLSX
barcode / QR
mobile workflow
zdjęcia / evidence przeglądu
harmonogramy
powiadomienia
role / permissions
approved_by
automatyczne przeliczenia jednostek
magazynu
ruchów materiałowych
automatycznej aktualizacji MAX
automatycznej decyzji BHP
REACH
```

---

## 31. STOP conditions dla przyszłych Tasków

STOP, jeżeli:

1. aktualny Core różni się od `CORE-001 v1.5-approved`,
2. implementacja wymaga nowego statusu REVIEW,
3. implementacja wymaga `FINAL → DRAFT`,
4. konieczna jest edycja / delete FINAL,
5. schema wymaga dodatkowej business data niewynikającej z BDR-011/Core,
6. trzeba zapisać alternatywną jednostkę observed,
7. wymagany byłby conversion engine,
8. nie można atomowo utworzyć header + population,
9. nie można zapewnić pojedynczego DRAFT bez przebudowy modelu,
10. istnieją multiple Alembic heads wymagające decyzji,
11. implementacja wymaga repo-wide refactor,
12. konieczna jest nowa dependency bez zatwierdzenia,
13. trzeba zgadywać znaczenie NULL / 0 / latest FINAL,
14. poprawne wykonanie wymaga zmiany historii Core.

Po minimalnej diagnostyce:

```text
STOP / BLOCKED
→ krótki raport
→ decyzja Architekta Operacyjnego
```

---

## 32. Zatwierdzone decyzje techniczne TDR-011

Architekt Operacyjny zatwierdził:

```text
T1. PostgreSQL tables:
    physical_reviews
    physical_review_items

T2. Review status:
    VARCHAR + CHECK DRAFT / FINAL

T3. Single DRAFT:
    partial UNIQUE index on status WHERE status='DRAFT'

T4. REVIEW_ITEM:
    baseline_unit_id FK do UNIT_OF_MEASURE
    bez observed_unit_id

T5. difference:
    derived, not stored

T6. snapshot creation:
    header + full population in one transaction

T7. empty population:
    controlled rejection; no empty DRAFT

T8. DRAFT discard:
    physical delete allowed only for DRAFT
    without CANCELLED status

T9. FINAL immutability:
    controlled Application/Repository write contracts
    no DB trigger in MVP

T10. latest FINAL:
     review_date DESC, finalized_at DESC
     latest NULL does not fall back to older observed value

T11. FKs historical:
     RESTRICT / NO ACTION, no cascade delete of referenced business data

T12. migration:
     one Alembic migration, no backfill
```

---

## 33. Authorization boundary

Po zatwierdzeniu TDR-011 może stanowić techniczną podstawę do przygotowania Sprintu / Tasków.

Sam dokument:

```text
NIE AUTORYZUJE IMPLEMENTACJI
```

---

## 34. Status

```text
TDR-011
VERSION: 1.0-approved
STATUS: APPROVED
```

TDR-011 v1.0-approved staje się obowiązującą decyzją techniczną dla ANALYTICS-03 i może stanowić podstawę do przygotowania Sprintu oraz Tasków implementacyjnych.

Sam dokument nie autoryzuje wykonania zmian w repozytorium.

---

## 35. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-06 | Draft | Pierwszy techniczny model REVIEW / REVIEW_ITEM, schema, lifecycle, single DRAFT, snapshot population, FINAL immutability i read model latest FINAL |
| 1.0-approved | 2026-10-06 | Approved | Architekt Operacyjny zatwierdził decyzje T1–T12 bez zmian merytorycznych |
