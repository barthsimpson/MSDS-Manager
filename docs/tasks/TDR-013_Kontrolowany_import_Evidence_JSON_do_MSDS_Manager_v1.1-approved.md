# TDR-013 — Kontrolowany import Evidence JSON do MSDS Manager

**Projekt:** MSDS Manager  
**Dokument:** TDR-013  
**Wersja:** 1.1-approved  
**Status:** Approved  
**Data:** 2026-10-12  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny po autoryzacji:** Codex OpenAI  

**Podstawa biznesowa / domenowa:**
- `BDR-009 v1.0-approved` — opcjonalny kod producenta i kontrolowana tożsamość PRODUCT,
- `CORE-001 v1.6-approved`,
- `BDR-003` — SDS, aktualność i wersjonowanie,
- `BDR-005` — ekstrakcja jako DRAFT + akceptacja człowieka,
- `BDR-007` — kontrolowany import SDS,
- `TDR-003` — granice warstw,
- `TDR-006` — kontrolowany import PDF,
- `TDR-012` — autonomiczny moduł ekstrakcji i Evidence JSON DRAFT,
- `SDS-JSON-001 v1.0-approved`,
- `BATCH-001_GOLDEN_DECISIONS.md`,
- `GOV-001`,
- `GOV-002`.

---

## 1. Cel decyzji technicznej

TDR-013 definiuje kontrolowany techniczny przepływ:

```text
Evidence JSON DRAFT
→ walidacja
→ DATA MAPPING
→ IDENTITY RESOLUTION
→ DRY RUN
→ HUMAN REVIEW
→ zatwierdzony plan importu
→ istniejące Application use cases
→ Repository / SQLAlchemy
→ PostgreSQL
```

Celem jest wykorzystanie Evidence JSON jako źródła danych dla istniejącego MSDS Manager bez tworzenia równoległego systemu rejestracji PRODUCT / SDS.

TDR-013 rozstrzyga:

- granicę pomiędzy analizą JSON a pełną rejestracją SDS,
- walidację wejściowego Evidence JSON,
- mapowanie pól JSON do modelu aplikacji,
- `CREATE / LINK / HUMAN REVIEW`,
- zachowanie przy `manufacturer_product_code = NULL`,
- kontrolowany wybór / utworzenie MANUFACTURER,
- kontrolowany wybór / utworzenie PRODUCT,
- wykorzystanie istniejących `AcceptSds`, `AddSdsRevision` i `ImportSds`,
- warunki finalnego COMMIT,
- zakaz bezpośredniego `JSON → SQL`,
- nullability `manufacturer_product_code`,
- minimalny audyt uzupełnienia / korekty tożsamości PRODUCT,
- ochronę przed sztucznym `NO_DATA`,
- granice testów i implementacji.

---

## 2. Zasada nadrzędna

Evidence JSON jest:

```text
źródłem roboczym
```

a nie bezpośrednią reprezentacją Core.

Obowiązuje:

```text
JSON
→ najpierw plan
→ potem decyzja człowieka
→ dopiero potem Application
```

Niedozwolone:

```text
JSON
→ INSERT / UPDATE PostgreSQL
```

oraz:

```text
JSON
→ automatyczna decyzja CREATE/LINK
→ COMMIT bez kontroli człowieka
```

---

## 3. Architektura

Docelowy przepływ:

```text
Evidence JSON
      │
      ▼
Application: ValidateEvidenceJson
      │
      ▼
Application: BuildSdsImportPlan
      │
      ├── Manufacturer Resolver
      │
      ├── Product Resolver
      │
      └── Domain/Core validation
      │
      ▼
DRY RUN RESULT
      │
      ├── CREATE CANDIDATE
      ├── LINK CANDIDATE
      ├── HUMAN REVIEW
      └── BLOCKED INPUT
      │
      ▼
HUMAN CONFIRMATION / MANUAL INPUT
      │
      ▼
Approved Import Plan
      │
      ▼
istniejące Application use cases
      │
      ├── AcceptSds          # nowy PRODUCT
      └── AddSdsRevision     # istniejący PRODUCT
      │
      ▼
ImportSds / storage
      │
      ▼
Repository / SQLAlchemy
      │
      ▼
PostgreSQL
```

Nie powstaje drugi mechanizm persistence PRODUCT/SDS.

---

## 4. Granica warstw

### Application

Application odpowiada za:

- walidację kontraktu wejścia,
- mapowanie Evidence JSON,
- wyznaczenie kandydatów,
- kontrolę jednoznaczności,
- przygotowanie DRY RUN,
- zebranie decyzji człowieka,
- budowę zatwierdzonego planu importu,
- wywołanie istniejących use case'ów rejestracyjnych.

### Infrastructure

Infrastructure odpowiada za:

- odczyt PostgreSQL przez istniejące repozytoria / read repositories,
- persistence przez SQLAlchemy,
- storage PDF zgodnie z TDR-006,
- techniczną walidację schema / transakcji.

### Domain

Domain nie zna:

- formatu pliku JSON,
- filesystem,
- SQLAlchemy,
- Streamlit,
- Codexa,
- LLM.

### Presentation / CLI

UI lub kontrolowane CLI:

- prezentuje DRY RUN,
- pozwala wybrać / zatwierdzić kandydata,
- pozwala podać wymagane dane ręczne,
- nie wykonuje SQL ani własnej logiki tożsamości.

---

## 5. Dwa odrębne etapy procesu

### ETAP A — JSON DATA MAPPING / DRY RUN

Wejście:

```text
Evidence JSON DRAFT
```

Proces:

```text
walidacja JSON
→ mapowanie
→ odczyt stanu bazy
→ CREATE / LINK / HUMAN REVIEW
→ raport
```

Ten etap:

```text
NIE wymaga fizycznego PDF
NIE zapisuje do PostgreSQL
NIE zmienia filesystem
NIE zmienia CURRENT / ARCHIVED
```

Brak PDF nie jest blockerem DRY RUN.

### ETAP B — CONTROLLED SDS REGISTRATION / COMMIT

Pełna rejestracja wymaga:

```text
zatwierdzonego planu importu
+
jawnej akceptacji człowieka
+
właściwego PDF
+
walidacji PDF / hash
+
istniejącego workflow Application
```

Dopiero ten etap może:

```text
utworzyć / powiązać PRODUCT
utworzyć / powiązać MANUFACTURER
utworzyć SDS
zmienić CURRENT / ARCHIVED
ustawić PENDING_APPROVAL
zapisać historię
```

---

## 6. Wejście Evidence JSON

Pierwsza implementacja przyjmuje wyłącznie JSON zgodny z:

```text
SDS-JSON-001 v1.0-approved
```

Walidacja G1 przed mapowaniem obejmuje co najmniej:

- schema / schema_version,
- source,
- documents[],
- document_key,
- page_range,
- dozwolone stany:
  - `FOUND`,
  - `NOT_FOUND`,
  - `AMBIGUOUS`,
  - `UNREADABLE`,
- regułę `FOUND → evidence`,
- brak wartości dla `NOT_FOUND / AMBIGUOUS / UNREADABLE`,
- poprawność typów i wymaganych pól technicznych.

Błąd kontraktu:

```text
INVALID_JSON
→ STOP dla tego dokumentu
→ brak DRY RUN identity
```

---

## 7. Granica dowodu źródłowego

Na etapie DRY RUN importer może korzystać z dowodów zapisanych w JSON.

Nie musi ponownie otwierać PDF.

Jednak:

```text
Evidence JSON evidence
≠ ponowne potwierdzenie źródła PDF
```

Przy finalnym COMMIT należy potwierdzić:

- właściwy PDF,
- zgodność źródła z JSON,
- SHA-256, jeżeli JSON go zawiera,
- zakres logicznego SDS,
- wymagane warunki TDR-006.

Rozbieżność PDF ↔ JSON:

```text
STOP / HUMAN REVIEW
```

---

## 8. Mapowanie danych — zakres pierwszej implementacji

Minimalne mapowanie:

```text
JSON product.product_name
→ PRODUCT.product_name

JSON product.manufacturer_product_code
→ PRODUCT.manufacturer_product_code

JSON parties[role=MANUFACTURER]
→ MANUFACTURER candidate

JSON document_metadata.issue_date
→ SDS.issue_date

JSON document_metadata.revision
→ SDS.revision

JSON source.original_filename
→ SDS.original_filename
```

Dane techniczne JSON takie jak:

```text
file_sha256
document_key
page_range
evidence
extraction_report
validation
```

służą kontroli procesu.

Nie stają się automatycznie nowymi polami Core.

---

## 9. `manufacturer_product_code`

Zgodnie z BDR-009 / Core v1.6:

```text
FOUND
→ wykorzystaj zatwierdzoną wartość

NOT_FOUND
→ value = NULL
→ NIE blokuje DRY RUN
→ NIE blokuje CREATE
```

Zabronione placeholdery:

```text
product_name
UFI
CAS
filename
UUID
inne sztuczne wartości
```

Technicznie:

```text
PRODUCT.manufacturer_product_code
→ nullable
```

Wymagana będzie migracja Alembic:

```text
NOT NULL
→ NULLABLE
```

bez backfillu wartości zastępczych.

---

## 10. Resolver MANUFACTURER

Wejściem resolvera jest zatwierdzona nazwa producenta.

Źródłem wartości może być:

```text
FOUND z Evidence JSON
+
identyczna zatwierdzona Golden Decision
+
ewentualna korekta człowieka
```

### 10.1. Dokładne dopasowanie

```text
1 dokładny rekord
→ MANUFACTURER LINK CANDIDATE

0 rekordów
→ MANUFACTURER CREATE CANDIDATE

>1 rekord
→ HUMAN REVIEW
```

### 10.2. Zakazy

Resolver NIE może automatycznie wybierać na podstawie:

- podobieństwa nazw,
- fuzzy matching,
- samej różnicy wielkości liter,
- częściowej zgodności,
- pierwszego zwróconego rekordu.

### 10.3. Golden Decisions

Golden Decisions mogą automatycznie zastosować wyłącznie:

```text
identyczny raw source value
→ zatwierdzony canonical value
```

Nowy albo tylko podobny wariant:

```text
CANDIDATE / HUMAN REVIEW
```

Golden Decision nie oznacza automatycznego wyboru `manufacturer_id`.

---

## 11. Resolver PRODUCT — kod znany

Jeżeli kod jest znany:

```text
product_name
+
manufacturer_id
+
manufacturer_product_code
```

tworzą kryterium kandydatów.

Wynik:

```text
0 kandydatów
→ PRODUCT CREATE CANDIDATE

1 kandydat
→ PRODUCT LINK CANDIDATE

>1 kandydat
→ HUMAN REVIEW
```

Resolver ma jawnie wykrywać wieloznaczność.

Niedozwolone:

```text
scalar() / first()
→ cichy wybór jednego z wielu
```

---

## 12. Resolver PRODUCT — kod NULL

Jeżeli:

```text
manufacturer_product_code = NULL
```

kandydaci są wyszukiwani po:

```text
product_name
+
manufacturer_id
```

Wynik:

```text
0
→ PRODUCT CREATE CANDIDATE

1
→ PRODUCT LINK CANDIDATE
→ wymagane jawne potwierdzenie człowieka

>1
→ HUMAN REVIEW
```

`NULL`:

```text
NIE jest wildcardem
NIE oznacza dowolnego kodu
NIE pozwala zignorować kodu istniejącego produktu bez decyzji człowieka
```

Jeżeli istnieje produkt o tej samej nazwie i producencie, ale z kodem znanym:

```text
JSON code = NULL
DB code = known
```

wynik pozostaje:

```text
LINK CANDIDATE / HUMAN CONFIRMATION
```

a nie automatyczny LINK.

---

## 13. Wynik DRY RUN

DRY RUN zwraca jawny plan, np.:

```text
SdsJsonImportPlan
├── json_identity
├── document_key
├── validation_status
├── manufacturer_resolution
│   ├── status
│   ├── canonical_name
│   └── candidate_ids[]
├── product_resolution
│   ├── status
│   └── candidate_ids[]
├── mapped_fields
├── required_manual_inputs[]
├── warnings[]
├── blockers[]
└── commit_readiness
```

Dozwolone statusy resolution:

```text
CREATE_CANDIDATE
LINK_CANDIDATE
HUMAN_REVIEW
INVALID
```

`commit_readiness`:

```text
NOT_READY
READY_FOR_CONTROLLED_COMMIT
```

Sam status `CREATE_CANDIDATE` lub `LINK_CANDIDATE` nie oznacza automatycznej zgody na COMMIT.

---

## 14. Manual inputs

Pola niepochodzące z obecnego zakresu Evidence JSON mogą być wymagane dopiero przed finalnym CREATE.

W szczególności obecny `AcceptSds` wymaga:

```text
use_description
use_restriction
```

TDR-013 nie zmienia ich kontraktu biznesowego.

Obowiązuje:

```text
brak w JSON
→ required_manual_input
→ NIE blokuje DRY RUN
→ blokuje finalny CREATE, jeśli obecny Core/Application nadal ich wymaga
```

Dane ręczne muszą być jawnie wprowadzone / potwierdzone przez człowieka.

---

## 15. HUMAN REVIEW

HUMAN REVIEW rozstrzyga co najmniej:

- wybór istniejącego MANUFACTURER,
- zgodę na utworzenie nowego MANUFACTURER,
- wybór istniejącego PRODUCT,
- zgodę na utworzenie nowego PRODUCT,
- wartość opcjonalnego kodu, jeżeli użytkownik ją zna,
- wymagane manual inputs,
- korekty wartości Evidence JSON,
- finalną akceptację danych do Core.

HUMAN REVIEW nie jest funkcją LLM.

---

## 16. Approved Import Plan

Po decyzji człowieka Application tworzy przejściowy:

```text
ApprovedSdsImportPlan
```

Plan zawiera co najmniej:

```text
source JSON fingerprint / hash
document_key
resolved manufacturer action:
  LINK(id) / CREATE(name)

resolved product action:
  LINK(id) / CREATE(fields)

mapped SDS metadata
manual inputs
human approval flag
warnings acknowledged
```

Plan:

- nie jest nowym obiektem Core,
- nie wymaga osobnej tabeli w MVP,
- nie jest trwałym workflow engine,
- służy związaniu decyzji człowieka z konkretnym wejściem JSON przed wywołaniem istniejących use case'ów.

Zmiana JSON po zatwierdzeniu planu:

```text
hash mismatch
→ plan invalid
→ ponowny DRY RUN / REVIEW
```

---

## 17. Wykorzystanie istniejących use case'ów

### 17.1. CREATE PRODUCT

Dla:

```text
PRODUCT CREATE
```

wykorzystać dostosowany:

```text
AcceptSds
```

Nie tworzyć równoległego `CreateProductFromJson`.

`AcceptSds` musi zostać dostosowany do:

- nullable `manufacturer_product_code`,
- jawnie rozstrzygniętego MANUFACTURER,
- braku cichego wyboru pierwszego produktu,
- danych z Approved Import Plan.

### 17.2. LINK PRODUCT / nowa rewizja SDS

Dla istniejącego PRODUCT:

```text
AddSdsRevision
```

pozostaje podstawą rejestracji kolejnej SDS.

`product_id` musi wynikać z jawnej decyzji planu.

### 17.3. PDF

`ImportSds` / istniejący storage z TDR-006 pozostaje odpowiedzialny za kontrolowany PDF.

---

## 18. CURRENT / ARCHIVED

TDR-013 nie zmienia lifecycle SDS.

Po finalnym zatwierdzeniu rejestracji nowej SDS:

```text
poprzedni CURRENT
→ ARCHIVED

nowy SDS
→ CURRENT

PRODUCT
→ PENDING_APPROVAL
```

DRY RUN musi przed COMMIT pokazać użytkownikowi przewidywany skutek:

```text
CURRENT_CHANGE = YES / NO
```

oraz, jeśli istnieje CURRENT:

```text
current_sds_id
→ would_archive = TRUE
```

Nie wolno zmienić CURRENT / ARCHIVED podczas DRY RUN.

---

## 19. SAFETY_PROFILE i częściowy JSON

Pierwszy Evidence JSON z TDR-012 / BATCH-001 może obejmować tylko część danych SDS.

Reguła nadrzędna:

```text
brak ekstrakcji pola
≠ NO_DATA z treści SDS
```

Importer nie może przekształcić:

```text
safety_profile = {}
```

w:

```text
domenowe NO_DATA
```

bez odpowiedniego dowodu / zatwierdzenia.

### 19.1. DRY RUN

Częściowy JSON może przejść:

```text
identity / metadata DRY RUN
```

### 19.2. COMMIT

Pełny COMMIT SDS do Core wymaga, aby dane objęte zatwierdzonym zakresem Core/BDR-005 były:

```text
wyekstrahowane i zatwierdzone
lub
jawnie uzupełnione przez człowieka
```

Jeżeli obecny Evidence JSON nie pokrywa wymaganego zakresu:

```text
commit_readiness = NOT_READY
```

Nie wolno uzupełniać braków automatycznym `NO_DATA`.

---

## 20. Multi-SDS PDF

TDR-013 zachowuje zasadę:

```text
1 PDF
→ 1..N logical SDS
```

Każdy:

```text
documents[document_key]
```

otrzymuje osobny:

```text
DRY RUN
→ Approved Import Plan
→ decyzję CREATE/LINK
```

Wspólny plik PDF nie oznacza wspólnej tożsamości PRODUCT.

Przy finalnej rejestracji kilku logicznych SDS z jednego PDF sposób referencjonowania / kopiowania źródła nie może tworzyć sprzeczności z TDR-006.

Jeżeli obecny storage nie wspiera tego bezpiecznie:

```text
STOP
→ osobna decyzja techniczna
```

---

## 21. Audyt uzupełnienia / korekty tożsamości PRODUCT

BDR-009 / Core v1.6 wymagają odtwarzalności:

```text
NULL → known manufacturer_product_code
```

oraz kontrolowanej korekty błędnych danych tożsamości.

Zatwierdza się jawny, domenowo specyficzny mechanizm:

```text
PRODUCT_IDENTITY_CHANGE
```

Nie jest to generyczny `AUDIT_LOG`.

Minimalne dane:

```text
change_id
product_id
change_kind
old_product_name
new_product_name
old_manufacturer_product_code
new_manufacturer_product_code
old_manufacturer_id
new_manufacturer_id
changed_at
```

Dozwolone `change_kind` MVP:

```text
CODE_COMPLETION
CORRECTION
```

### 21.1. CODE_COMPLETION

```text
old code = NULL
new code = known
product_id unchanged
```

### 21.2. CORRECTION

Jawna poprawa błędnie zapisanej:

```text
product_name
lub manufacturer_product_code
lub manufacturer_id
```

Nie jest to mechanizm normalnej zmiany produktu.

Rzeczywista zmiana tożsamości zgodnie z Core:

```text
→ new PRODUCT
```

---

---

## 21A. Jawna granica UX / API dla zmian tożsamości PRODUCT

Na podstawie BLOCKED TASK-051 doprecyzowuje się techniczną granicę pomiędzy:

```text
uzupełnieniem brakującego kodu
korektą błędnie zarejestrowanej tożsamości
rzeczywistą zmianą tożsamości produktu
```

Operacje te nie mogą korzystać z jednego ogólnego trybu „edycji danych produktu”.

### 21A.1. CODE_COMPLETION

Przejście:

```text
manufacturer_product_code:
NULL → known value
```

jest osobną, jawną operacją Application:

```text
CompleteManufacturerProductCode
```

Semantyka:

```text
uzupełnienie brakującej informacji
→ ten sam product_id
→ change_kind = CODE_COMPLETION
```

UI powinno prezentować tę operację jednoznacznie jako:

```text
Uzupełnij kod producenta
```

Nie jest to korekta błędu ani ogólna edycja identity.

### 21A.2. CONTROLLED CORRECTION

Korekta błędnie zarejestrowanych danych identity jest osobną, jawną operacją Application:

```text
CorrectProductIdentity
```

Semantyka:

```text
błędnie zapisane product_name
lub manufacturer_product_code
lub manufacturer_id
→ korekta istniejącego PRODUCT
→ ten sam product_id
→ change_kind = CORRECTION
```

UI powinno prezentować ją jednoznacznie jako:

```text
Korekta danych identyfikacyjnych
```

Przed zatwierdzeniem użytkownik musi wykonać świadome potwierdzenie znaczenia operacji, np.:

```text
Potwierdzam, że poprawiam błędnie zarejestrowane dane,
a nie rejestruję innego produktu.
```

Nie wymaga się osobnego pola `reason` ani `changed_by` w MVP.

### 21A.3. Rzeczywista zmiana tożsamości

Jeżeli zmiana oznacza rzeczywiście:

```text
nową nazwę produktu
lub
znany kod A → rzeczywiście inny kod B
lub
innego producenta
```

nie wolno użyć:

```text
CompleteManufacturerProductCode
CorrectProductIdentity
```

Oczekiwany wynik:

```text
→ nowy PRODUCT
```

zgodnie z BDR-009 i CORE-001 v1.6-approved.

### 21A.4. Ograniczenie istniejącego UpdateProductIdentity

Istniejący publiczny use case / UI:

```text
UpdateProductIdentity
```

nie może pozostać ogólną ścieżką pozwalającą dowolnie zmieniać identity bez rozstrzygnięcia intencji.

Implementacja ma:

```text
albo zastąpić go jawnymi operacjami:
- CompleteManufacturerProductCode
- CorrectProductIdentity

albo ograniczyć go tak,
aby publicznie reprezentował wyłącznie CONTROLLED CORRECTION.
```

Preferowane rozwiązanie:

```text
dwie jawne operacje Application
```

ponieważ rozdzielają semantykę `CODE_COMPLETION` i `CORRECTION`.

### 21A.5. Zakaz cichej klasyfikacji

System nie może sam uznać, że:

```text
każda zmiana identity = CORRECTION
```

ani że:

```text
każda zmiana kodu = CODE_COMPLETION
```

Klasyfikacja operacji wynika z jawnie wybranego use case'u i działania użytkownika.


## 22. Techniczny model PRODUCT_IDENTITY_CHANGE

Zalecana osobna tabela:

```text
product_identity_changes
```

Minimalnie:

```text
change_id                 PK
product_id                FK → PRODUCT
change_kind               VARCHAR + CHECK
old_product_name          NOT NULL
new_product_name          NOT NULL
old_manufacturer_product_code NULL
new_manufacturer_product_code NULL
old_manufacturer_id       FK-compatible value
new_manufacturer_id       FK-compatible value
changed_at                NOT NULL
```

Dokładne typy identyfikatorów mają odpowiadać istniejącym fizycznym typom PRODUCT / MANUFACTURER.

Nie wprowadzać nowego systemu użytkowników / `changed_by` wyłącznie dla tego mechanizmu.

Zmiana identity + wpis historii:

```text
jedna transakcja PostgreSQL
```

---

## 23. Schema changes

Implementacja TDR-013 wymaga co najmniej:

```text
products.manufacturer_product_code
NOT NULL → NULLABLE
```

oraz tabeli:

```text
product_identity_changes
```

Zmiany wyłącznie przez Alembic.

Nie zmieniać istniejących niepustych kodów.

Nie wykonywać automatycznego backfillu kodów.

---

## 24. Transakcje

### DRY RUN

```text
READ ONLY
```

Nie wykonuje:

- INSERT,
- UPDATE,
- DELETE,
- filesystem write.

### COMMIT CREATE/LINK

Wykorzystuje istniejącą transakcyjność workflow SDS.

Jeżeli operacja obejmuje korektę / uzupełnienie identity:

```text
identity update
+
PRODUCT_IDENTITY_CHANGE
```

muszą zostać zatwierdzone atomowo.

PDF + DB nadal podlegają compensation zgodnie z TDR-006.

---

## 25. Idempotencja i duplikaty

Importer nie może zakładać, że identyczny JSON oznacza brak duplikatu.

DRY RUN przed COMMIT sprawdza aktualny stan bazy.

Jeżeli od poprzedniego DRY RUN stan bazy się zmienił:

```text
Approved Import Plan
→ revalidation
```

Przed CREATE należy ponownie potwierdzić brak konfliktującego PRODUCT / MANUFACTURER.

Nie tworzymy w TDR-013 generycznego distributed lock.

---

## 26. Autonomia runtime

TDR-013 nie wprowadza LLM do działania aplikacji.

Runtime importera:

```text
BEZ LLM
BEZ ChatGPT Work
BEZ Cerberusa
BEZ Codexa
BEZ zewnętrznej usługi AI
```

Codex / LLM mogą przygotować Evidence JSON w procesie bootstrapowym poza runtime.

Aplikacja konsumuje wyłącznie artefakt zgodny z zatwierdzonym kontraktem.

---

## 27. Obsługa błędów

Minimalne kategorie:

```text
InvalidEvidenceJsonError
UnsupportedSchemaVersionError
AmbiguousManufacturerError
AmbiguousProductError
ImportPlanStaleError
ManualInputRequiredError
PdfRequiredForCommitError
PdfJsonMismatchError
IncompleteSafetyDataError
IdentityCorrectionNotAuthorizedError
```

Nazwy klas mogą zostać dopasowane do konwencji repozytorium.

Błąd kontrolowany:

```text
→ brak częściowego COMMIT
```

---

## 28. Przypadek referencyjny — ALUCYNK

Wejście:

```text
product_name = ALUCYNK
manufacturer_product_code = NULL
manufacturer canonical = CX80 POLSKA
issue_date = 2023-01-23
revision = 2.0
```

Stan z prechecku:

```text
PRODUCT ALUCYNK = 0
MANUFACTURER exact CX80 POLSKA = 0
istnieją CX80 / Cx80
```

Oczekiwany DRY RUN:

```text
MANUFACTURER
→ CREATE_CANDIDATE
   + warning: istnieją podobne CX80 / Cx80
   + HUMAN CONFIRMATION REQUIRED

PRODUCT
→ CREATE_CANDIDATE

manufacturer_product_code
→ NULL
→ ACCEPTABLE

use_description
→ MANUAL INPUT REQUIRED przed finalnym CREATE

use_restriction
→ MANUAL INPUT REQUIRED przed finalnym CREATE

safety data
→ INCOMPLETE FOR CORE COMMIT
   jeśli JSON nie zawiera zatwierdzonego zakresu

commit_readiness
→ NOT_READY
```

To jest poprawny wynik.

ALUCYNK nie jest:

```text
NOT RECOGNIZED
```

lecz:

```text
recognized in JSON
+
new PRODUCT candidate
```

---

## 29. Proponowany podział implementacji

Po zatwierdzeniu TDR:

### Task A — Foundation / schema / identity

```text
manufacturer_product_code nullable
PRODUCT_IDENTITY_CHANGE
Domain / ORM / Alembic
identity correction rules
focused PostgreSQL tests
```

Tryb:

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
```

### Task B — JSON DRY RUN / resolver

```text
SDS-JSON validator
mapper
manufacturer resolver
product resolver
SdsJsonImportPlan
read-only dry run
ALUCYNK test
```

Tryb:

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
```

### Task C — Controlled commit integration

```text
Approved Import Plan
AcceptSds / AddSdsRevision reuse
ImportSds PDF boundary
manual inputs
safety completeness gate
transaction / compensation
```

Tryb:

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
```

### Task D — Acceptance

```text
JSON → DRY RUN → HUMAN DECISION → COMMIT
```

na izolowanym PostgreSQL i kontrolowanym PDF.

Tryb:

```text
MODE: ACCEPTANCE
VALIDATION: LEVEL 3
```

Numeracja Tasków zostanie ustalona osobno.

---

## 30. Wymagana walidacja przyszłych Tasków

### Foundation

- ORM nullable,
- Alembic upgrade,
- downgrade,
- re-upgrade,
- alembic current,
- alembic check,
- constraints,
- operator data preservation,
- identity history transaction.

### DRY RUN

- zero DB writes,
- zero filesystem writes,
- exact manufacturer match,
- 0 / 1 / >1 candidates,
- code known,
- code NULL,
- no fuzzy auto-link,
- Golden Decision exact reuse,
- ALUCYNK scenario.

### COMMIT

- CREATE new PRODUCT with code NULL,
- LINK existing PRODUCT,
- no placeholder code,
- manual inputs enforced,
- PDF validation,
- CURRENT / ARCHIVED,
- rollback / compensation,
- no synthetic NO_DATA.

---

## 31. Data safety

Testy integracyjne używają izolowanego PostgreSQL.

Nie używać danych operatora do destructive testów.

Migracja:

```text
NOT NULL → NULLABLE
```

nie usuwa ani nie zmienia istniejących wartości kodu.

Nowa tabela historii rozpoczyna rejestrację zmian od momentu wdrożenia.

Nie rekonstruuje się fikcyjnej historii sprzed wdrożenia.

---

## 32. Poza zakresem

TDR-013 nie obejmuje:

- OCR,
- rozbudowy ekstraktora sekcji 2/3/11,
- fuzzy matching,
- automatycznego merge MANUFACTURER,
- automatycznej deduplikacji istniejących danych,
- automatycznej decyzji BHP,
- REACH,
- nowego DMS,
- przechowywania Evidence JSON jako nowego Core object,
- workflow użytkowników / ról,
- `changed_by`,
- generycznego audit log,
- zmiany CURRENT / ARCHIVED,
- zmiany `SDS-JSON-001`,
- automatycznego aktywowania aliasów.

---

## 33. STOP conditions dla przyszłych Tasków

Codex ma wykonać:

```text
STOP / BLOCKED
```

jeżeli:

1. implementacja wymaga zmiany Core poza `CORE-001 v1.6-approved`,
2. wymagany jest bezpośredni JSON → SQL,
3. resolver musiałby wybrać jeden z wielu kandydatów bez decyzji człowieka,
4. wymagany jest fuzzy matching jako automatyczna decyzja,
5. poprawne działanie wymaga placeholdera dla kodu produktu,
6. `NULL` miałby zostać potraktowany jako wildcard,
7. partial safety JSON miałby zostać zapisany jako sztuczne `NO_DATA`,
8. nie można wykorzystać istniejących `AcceptSds / AddSdsRevision / ImportSds` bez równoległego workflow,
9. nie można zagwarantować DRY RUN bez write,
10. PDF / JSON nie można jednoznacznie powiązać przed COMMIT,
11. multi-SDS PDF wymaga niezatwierdzonej zmiany modelu storage,
12. trzeba automatycznie scalić istniejących producentów,
13. migracja tworzy multiple Alembic heads,
14. zmiana identity nie może zostać zapisana atomowo z jej historią,
15. wymagana jest nowa dependency bez zatwierdzenia,
16. trzeba zgadywać semantykę istniejącego kontraktu.

---

## 34. Authorization boundary

TDR-013 po zatwierdzeniu może stanowić authoritative context dla Tasków implementacyjnych.

Sam TDR:

```text
NIE AUTORYZUJE IMPLEMENTACJI
NIE AUTORYZUJE MIGRACJI
NIE AUTORYZUJE COMMIT DANYCH BATCH-001
```

Każdy Task wymaga jawnego polecenia Architekta Operacyjnego.

---

## 35. Status dokumentu

```text
TDR-013
VERSION: 1.1-approved
STATUS: APPROVED
IMPLEMENTATION: NOT AUTHORIZED
```

---

## 36. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-12 | Draft | Zdefiniowano Evidence JSON → DRY RUN → CREATE/LINK/HUMAN REVIEW → Application → PostgreSQL, nullable manufacturer_product_code, granicę PDF, partial safety gate oraz audyt zmian tożsamości PRODUCT |
| 1.0-approved | 2026-10-12 | Approved | Architekt Operacyjny zatwierdził model kontrolowanego importu Evidence JSON, DRY RUN, CREATE/LINK/HUMAN REVIEW, reuse istniejących use case'ów, nullable manufacturer_product_code, partial safety gate oraz audyt zmian tożsamości PRODUCT |
| 1.1-approved | 2026-10-12 | Approved | Doprecyzowano po BLOCKED TASK-051 jawną granicę UX/API: osobne CompleteManufacturerProductCode dla NULL→kod, CorrectProductIdentity dla kontrolowanej korekty oraz zakaz używania ogólnej edycji identity do rzeczywistej zmiany produktu |
