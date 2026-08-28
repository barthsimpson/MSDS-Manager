# TASK-004 — Modele SQLAlchemy / Persistence Mapping

**Projekt:** MSDS Manager  
**Task ID:** TASK-004  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Zaimplementować warstwę persistence dla zatwierdzonego modelu domenowego MSDS Manager przy użyciu SQLAlchemy 2.x.

TASK-004 ma odwzorować obiekty i relacje Core w modelach ORM umieszczonych wyłącznie w:

```text
app/infrastructure/db/models/
```

Task ma przygotować poprawne `Base.metadata` dla późniejszej migracji Alembic.

TASK-004 **nie tworzy jeszcze schematu bazy danych** i nie wykonuje żadnej migracji.

---

## 2. Warunek wejścia

TASK-003 jest zakończony statusem `DONE` i zaakceptowany.

Stan wejściowy projektu:

- domena zawiera 9 modeli i 8 zatwierdzonych enumów,
- testy domenowe przechodzą,
- PostgreSQL działa,
- baza `msds_manager` nie posiada tabel aplikacyjnych,
- Alembic nie posiada rewizji domenowych,
- `target_metadata` pozostaje niepodłączone do modelu aplikacji,
- nie istnieją jeszcze modele ORM Core.

---

## 3. Obowiązujące źródła

Implementacja musi być zgodna z:

- CORE-001 v1.0-approved,
- BDR-001,
- BDR-002,
- BDR-003,
- BDR-004,
- BDR-005 v1.0-approved,
- TDR-001,
- TDR-002,
- TDR-003,
- zaakceptowanym rezultatem TASK-003,
- AGENTS.md.

Jeżeli model domenowy TASK-003 ujawnia konflikt z zatwierdzonym BDR/CORE, nie dostosowuj ORM przez zgadywanie. Zastosuj STOP.

---

## 4. Zasada nadrzędna — Domain ≠ ORM

Modele domenowe i modele persistence są odrębnymi warstwami.

Obowiązuje:

```text
app/domain/models/
    = znaczenie biznesowe

app/infrastructure/db/models/
    = techniczne odwzorowanie PostgreSQL
```

Nie wolno:

- dodawać dekoratorów SQLAlchemy do modeli domenowych,
- importować SQLAlchemy w `app/domain`,
- przenosić reguł biznesowych do modeli ORM,
- zastępować modeli domenowych klasami SQLAlchemy.

TASK-004 nie może naruszyć niezależności domeny osiągniętej w TASK-003.

---

## 5. SQLAlchemy 2.x

Stosuj nowoczesny styl SQLAlchemy 2.x.

Preferowane mechanizmy:

```text
DeclarativeBase
Mapped[]
mapped_column()
relationship()
```

Nie stosuj legacy API, jeżeli nie ma uzasadnionej potrzeby.

---

## 6. Base

Utwórz jawny bazowy typ ORM, np. `Base`, w odpowiednim module pod `app/infrastructure/db/` lub `app/infrastructure/db/models/`.

`Base.metadata` ma zawierać cały zatwierdzony model persistence po zaimportowaniu wszystkich modeli.

Nie wywołuj:

```python
Base.metadata.create_all(...)
```

---

## 7. Modele ORM wymagane w TASK-004

### 7.1. ManufacturerModel

Tabela np. `manufacturers`.

Minimalne dane:
- `manufacturer_id` — PK,
- `manufacturer_name` — wymagane.

Relacja:

```text
MANUFACTURER 1:N PRODUCT
```

Nie dodawaj dostawcy.

### 7.2. ProductModel

Tabela np. `products`.

Minimalne pola:
- `product_id` — PK,
- `product_name`,
- `manufacturer_product_code`,
- `manufacturer_id` — FK,
- `use_description`,
- `use_restriction`,
- `usage_status`.

`usage_status` musi odwzorować:
- `PENDING_APPROVAL`
- `ACTIVE`
- `REJECTED`
- `INACTIVE`

Nie twórz unikalności na `product_name` ani `manufacturer_product_code`, jeżeli nie wynika ona jawnie z zatwierdzonych decyzji.

### 7.3. UsageLocationModel

Tabela np. `usage_locations`.

Pola:
- `location_id` — PK,
- `location_name`,
- `status`.

Nie twórz niezatwierdzonego enumu dla `status`.

### 7.4. ProductUsageLocationModel

Tabela asocjacyjna `product_usage_locations`.

Minimalnie:
- `product_id` — FK,
- `location_id` — FK,
- `quantity_value`,
- `quantity_unit`.

Relacja:
```text
PRODUCT N:M USAGE_LOCATION
```

Dopuszczalny jest złożony klucz główny `(product_id, location_id)`, jeżeli jest zgodny z zatwierdzonym znaczeniem rekordu.

Nie przechowuj `peak_factory_quantity` jako niezależnej kolumny.

### 7.5. SdsDocumentModel

Tabela np. `sds_documents`.

Minimalnie:
- `sds_id` — PK,
- `product_id` — FK,
- `original_filename`,
- `relative_path`,
- `issue_date` — nullable,
- `revision` — nullable,
- `document_status`,
- `registered_at`,
- `file_status`.

Enumy:
- `CURRENT`, `ARCHIVED`
- `AVAILABLE`, `MISSING`

Nie implementuj jeszcze zaawansowanego constraintu „maksymalnie jeden CURRENT SDS na produkt”, jeśli wymaga to strategii przeznaczonej dla TASK-006.

### 7.6. BhpDecisionModel

Tabela np. `bhp_decisions`.

Pola:
- `decision_id` — PK,
- `product_id` — FK,
- `sds_id` — FK,
- `decision_status`,
- `notes` — nullable,
- `registered_at`,
- `record_status`,
- `evidence_id`.

Enumy:
- `APPROVED`, `REJECTED`
- `CURRENT`, `SUPERSEDED`

Nie dodawaj `PENDING`, `decided_by` ani osobnej `decision_date`.

### 7.7. DecisionEvidenceModel

Tabela np. `decision_evidence`.

Pola:
- `evidence_id` — PK,
- `relative_path`,
- `evidence_type`,
- `file_format`,
- `file_status`.

Enumy:
- `EMAIL`, `DOCUMENT`, `PHOTO_SCAN`
- `MSG`, `PDF`, `JPG`, `JPEG`, `PNG`
- `AVAILABLE`, `MISSING`

Relacja:
```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Nie zapisuj zawartości binarnej pliku w PostgreSQL.

### 7.8. SafetyProfileModel

Tabela np. `safety_profiles`.

Relacja:
```text
SDS 1:1 SAFETY_PROFILE
```

Minimalne pola:
- `sds_id` — FK i logiczna identyfikacja profilu,
- `product_definition`,
- `hazardous_classification_status`,
- `clp_classification_text`,
- `signal_word`,
- `hazard_statements`,
- `supplemental_hazard_statements`,
- `pbt_status`,
- `vpvb_status`,
- `carcinogenicity_status`,
- `germ_cell_mutagenicity_status`,
- `reproductive_toxicity_status`,
- `endocrine_section_2_status`,
- `endocrine_section_11_status`,
- `skin_sensitization_status`,
- `respiratory_sensitization_status`,
- `approved_at`,
- `last_manual_edit_at` — nullable.

Statusowe pola bezpieczeństwa odwzorowują:
- `YES`
- `NO`
- `NO_DATA`
- `NOT_APPLICABLE`

Nie dodawaj confidence score ani jednego zbiorczego `endocrine_status`.

### 7.9. SdsComponentModel

Tabela np. `sds_components`.

Minimalne pola:
- `component_id` — PK,
- `sds_id` — FK,
- `component_name`,
- `cas_number` — nullable,
- `ec_number` — nullable,
- `reach_registration_number` — nullable,
- `concentration_text` — nullable,
- `classification_text` — nullable,
- `hazard_statements`.

Relacja:
```text
SDS 1:N SDS_COMPONENT
```

Nie przenoś klasyfikacji składnika do `SafetyProfile`.

---

## 8. Reprezentacja enumów

Wybierz jedną konsekwentną strategię SQLAlchemy dla zatwierdzonych enumów.

Wymagania:
- brak niezatwierdzonych wartości,
- czytelna przyszła migracja Alembic,
- brak mieszania strategii bez potrzeby,
- stabilne nazwy typów/constraints.

Jeżeli wybór między natywnym PostgreSQL ENUM a `VARCHAR + CHECK` ma istotne konsekwencje i nie wynika z TDR, wybierz najprostszy odwracalny wariant albo zgłoś pytanie w raporcie.

---

## 9. Reprezentacja `hazard_statements`

Nie twórz osobnej encji H-statement ani pełnej normalizacji słownika H.

W persistence wybierz prosty sposób przechowania kolekcji, łatwy do późniejszej migracji.

Nie rozbudowuj tego w system klasyfikacji CLP.

---

## 10. Typ ilości

`quantity_value` ma zachować semantykę domenowego `Decimal`.

Użyj odpowiedniego typu SQLAlchemy/PostgreSQL, np. `Numeric`.

Nie mapuj na nieprecyzyjny `Float`.

---

## 11. Daty i timestampy

Odwzoruj:
- `issue_date`,
- `registered_at`,
- `approved_at`,
- `last_manual_edit_at`

przy użyciu odpowiednich typów SQLAlchemy.

Nie dodawaj nowej polityki timezone ani server defaultów biznesowych bez zatwierdzonej potrzeby.

---

## 12. Relacje ORM

Zdefiniuj co najmniej:

```text
Manufacturer ↔ Products
Product ↔ SDS
Product ↔ ProductUsageLocations
UsageLocation ↔ ProductUsageLocations
SDS ↔ SafetyProfile
SDS ↔ SdsComponents
SDS ↔ BhpDecisions
BhpDecision ↔ DecisionEvidence
```

Nie stosuj agresywnych cascade delete dla obiektów historycznych.

---

## 13. Klucze obce i integralność

Dodaj podstawowe FK zgodne z modelem.

Nie implementuj jeszcze wszystkich zaawansowanych constraintów procesowych. TASK-006 będzie przeznaczony m.in. na:
- jeden CURRENT SDS na produkt,
- jedną CURRENT BHP decision na SDS,
- zgodność `product_id` pomiędzy decyzją i SDS,
- inne krytyczne constraints Core.

---

## 14. Ograniczenia usuwania

Nie implementuj automatycznego fizycznego kasowania historycznych rekordów.

Nie konfiguruj `ON DELETE CASCADE` jako domyślnej strategii dla historii.

Nie twórz jeszcze frameworka soft delete.

---

## 15. Alembic — przygotowanie, nie migracja

Po utworzeniu modeli ORM:

- `Base.metadata` powinno zawierać modele,
- możesz zaktualizować `migrations/env.py`, aby `target_metadata` wskazywało `Base.metadata`,
- **nie generuj rewizji**,
- **nie uruchamiaj `alembic upgrade`**,
- nie twórz tabel.

Oczekiwany stan:

```text
ORM models: YES
Base.metadata: YES
Alembic target_metadata: YES
Alembic revisions: 0
PostgreSQL application tables: 0
```

---

## 16. Testy TASK-004

Dodaj testy metadata-level bez tworzenia tabel w operacyjnej bazie.

Pokryj co najmniej:
1. oczekiwane tabele obecne w `Base.metadata`,
2. PK zdefiniowane,
3. FK obecne,
4. struktura `ProductUsageLocation`,
5. `SafetyProfile` 1:1 z SDS,
6. `DecisionEvidence` 1:1 z BHP decision,
7. enumy bez dodatkowych wartości,
8. `quantity_value` nie jest `Float`,
9. właściwe nullable dla pól opcjonalnych,
10. brak kolumny `peak_factory_quantity`,
11. brak `decided_by`,
12. brak osobnego `decision_date`,
13. brak confidence score,
14. brak tabel magazynowych/dostawców,
15. brak automatycznego tworzenia tabel przy imporcie modeli.

Uruchom wszystkie dotychczasowe testy.

---

## 17. Kontrola zgodności 9 → 9

W raporcie przygotuj mapę:

```text
Domain Model              ORM Model
--------------------------------------------
Manufacturer              ManufacturerModel
Product                   ProductModel
UsageLocation             UsageLocationModel
ProductUsageLocation      ProductUsageLocationModel
SdsDocument               SdsDocumentModel
BhpDecision               BhpDecisionModel
DecisionEvidence          DecisionEvidenceModel
SafetyProfile             SafetyProfileModel
SdsComponent              SdsComponentModel
```

Dla każdego wpisu wskaż:
- tabelę,
- PK,
- główne FK,
- istotne nullable,
- odstępstwa od modelu domenowego.

---

## 18. Kontrola bazy po Tasku

Po implementacji potwierdź, że PostgreSQL nadal nie ma tabel aplikacyjnych.

Dopuszczalne są wyłącznie diagnostyczne SELECT-y.

---

## 19. Kontrola architektury

Potwierdź:
- `app/domain` nadal nie importuje SQLAlchemy,
- nowe modele są wyłącznie w infrastructure,
- presentation nie została zmieniona,
- nie dodano CRUD/repositories/use cases,
- nie dodano nowych bibliotek,
- nie zmodyfikowano Core pod potrzeby ORM.

---

## 20. Elementy poza zakresem

Nie implementuj:
- migracji Alembic,
- `alembic revision --autogenerate`,
- `alembic upgrade`,
- `create_all`,
- CRUD,
- repositories,
- use cases,
- Streamlit UI,
- ekstrakcji PDF,
- parsera SDS,
- REACH,
- AI/LLM,
- importu Excel,
- deduplikacji,
- backupu,
- soft delete framework,
- pełnego audytu zmian,
- konwersji jednostek,
- nowych statusów,
- dodatkowej normalizacji słowników CLP.

---

## 21. Pliki chronione

Nie modyfikuj zatwierdzonych CORE, BDR, ADR, TDR, PDP, ROADMAP, GOV, Konstytucji ani IR.

Nie modyfikuj `.env`.

Nie zapisuj sekretów.

---

## 22. Zasada STOP

Zatrzymaj problematyczny fragment, jeżeli:
- odwzorowanie domeny wymaga nowej decyzji biznesowej,
- trzeba dodać nowy enum/status,
- relacja nie jest jednoznaczna,
- konieczna jest niezatwierdzona unikalność,
- potrzebna jest decyzja persistence o istotnym wpływie,
- potrzebna byłaby nowa biblioteka,
- implementacja wchodzi w TASK-005/006.

Bezpieczne części mogą zostać wykonane, a Task może zakończyć się `PARTIAL`.

---

## 23. Kryteria akceptacji

TASK-004 może otrzymać `DONE`, jeżeli:

1. istnieje komplet modeli ORM dla 9 modeli domenowych,
2. modele są wyłącznie w infrastructure,
3. `Base.metadata` zawiera właściwe tabele,
4. relacje i podstawowe FK odwzorowują Core,
5. typ ilości zachowuje precyzję `Decimal`,
6. modele nie dodają niezatwierdzonej logiki,
7. `target_metadata` Alembica wskazuje `Base.metadata`,
8. Alembic nadal posiada 0 rewizji,
9. PostgreSQL nadal posiada 0 tabel aplikacyjnych,
10. nie użyto `create_all`,
11. wszystkie testy przechodzą,
12. nie dodano nowych zależności,
13. domena nadal nie zależy od SQLAlchemy,
14. raport zawiera mapę zgodności 9 → 9,
15. Codex nie rozpoczął TASK-005.

---

## 24. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-004_REPORT.md
```

Raport musi zawierać:

1. Status — `DONE`, `PARTIAL` albo `BLOCKED`
2. Wykonano
3. Utworzone pliki
4. Zmienione pliki
5. Mapa Domain → ORM 9 → 9
6. Relacje i klucze
7. Strategia enumów
8. Typy istotne (`Decimal/Numeric`, daty, H-statements)
9. Alembic (`target_metadata`, liczba rewizji)
10. PostgreSQL (liczba tabel aplikacyjnych)
11. Testy — polecenia i wyniki
12. Kontrola architektury
13. Odstępstwa
14. Problemy / ryzyka
15. Pytania do Cerberusa
16. Git / bezpieczeństwo
17. Następny krok:

```text
OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-005.
```

---

## 25. Zakończenie

Po wykonaniu:
- zapisz raport,
- przedstaw krótkie podsumowanie użytkownikowi,
- nie generuj migracji,
- nie twórz tabel,
- nie rozpoczynaj TASK-005,
- oczekuj na Cerberus Review.
