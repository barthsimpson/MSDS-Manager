# TASK-050 — Manufacturer Product Code Optional + JSON→DB Impact Analysis

**Projekt:** MSDS Manager  
**Task ID:** TASK-050  
**Tryb:** ANALYSIS / ARCHITECTURE IMPACT  
**Status:** READY / NOT AUTHORIZED FOR IMPLEMENTATION  
**Wykonawca:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus  

---

## 1. CEL

Przeanalizować wpływ zatwierdzonej decyzji biznesowej:

```text
manufacturer_product_code
→ pole opcjonalne
→ brak kodu nie blokuje rejestracji PRODUCT ani SDS
→ kod może zostać uzupełniony ręcznie później
```

oraz sprawdzić, czy istniejący workflow `AcceptSds` może zostać wykorzystany jako docelowa ścieżka:

```text
Evidence JSON DRAFT
→ walidacja
→ identity resolution
→ CREATE albo LINK
→ Application
→ Repository / SQLAlchemy
→ PostgreSQL
```

bez tworzenia równoległego mechanizmu rejestracji PRODUCT/SDS.

TASK-050 jest WYŁĄCZNIE analizą wpływu.

Nie wykonuj zmian implementacyjnych.

---

## 2. KONTEKST

Przeczytaj wyłącznie niezbędne źródła:

1. aktualny `CORE-001` — najnowsza wersja approved,
2. `BDR-003`,
3. `BDR-005`,
4. `BDR-007`,
5. `TDR-006`,
6. `TDR-012`,
7. `SDS-JSON-001`,
8. `BATCH-001_GOLDEN_DECISIONS.md`,
9. `JSON_DB_PRECHECK_REPORT.md`,
10. `GOV-001`,
11. `GOV-002`,
12. root `AGENTS.md`.

Nie wykonuj repo-wide discovery bez konkretnej potrzeby.

---

## 3. ZATWIERDZONA DECYZJA BIZNESOWA

`manufacturer_product_code` nie jest już wymaganiem typu MUST HAVE.

Obowiązuje:

| Sytuacja | Zachowanie |
|---|---|
| kod wykryty w SDS | wartość może zostać zaproponowana do zatwierdzenia |
| kod niewykryty | `NULL` |
| użytkownik zna kod | może wprowadzić go ręcznie |
| użytkownik nie zna kodu | proces może być kontynuowany |
| kod ustalony później | użytkownik może go uzupełnić |
| brak kodu | NIE powoduje `BLOCKED` |
| brak kodu | NIE powoduje sztucznej wartości zastępczej |

Zabronione jest zastępowanie kodu przez:

```text
product_name
UFI
CAS
nazwę pliku
dowolny sztuczny identyfikator
```

---

## 4. WAŻNA KONSEKWENCJA CORE — DO ANALIZY

Aktualny Core traktuje:

```text
product_name
manufacturer_product_code
manufacturer_id
```

jako tożsamość PRODUCT.

Nowa decyzja oznacza potencjalny konflikt z dotychczasową regułą:

```text
zmiana manufacturer_product_code
→ nowy PRODUCT
```

Jeżeli PRODUCT został utworzony z:

```text
manufacturer_product_code = NULL
```

a użytkownik później uzupełnia brakujący kod, oczekiwane zachowanie biznesowe jest:

```text
ten sam PRODUCT
→ uzupełnienie brakującej informacji
```

a NIE:

```text
utworzenie nowego PRODUCT
```

TASK-050 ma:

1. wskazać wszystkie obowiązujące dokumenty i miejsca kodu, które utrwalają dotychczasową regułę,
2. określić minimalną zmianę decyzji biznesowej / Core konieczną przed implementacją,
3. NIE zmieniać Core samodzielnie.

---

## 5. KOREKTA INTERPRETACJI JSON → DB PRECHECK

BATCH-001 służy do testowania procesu:

```text
PDF SDS
→ Evidence JSON DRAFT
→ JSON validation / mapping
→ Application
→ PostgreSQL
```

Na etapie:

```text
JSON → walidacja → mapowanie → identity resolution
```

brak ponownego dostępu do oryginalnego PDF NIE powinien sam w sobie blokować analizy mapowania danych.

Rozdziel:

### ETAP A — DATA MAPPING / DRY RUN

```text
Evidence JSON
→ walidacja kontraktu
→ mapowanie pól
→ identyfikacja CREATE / LINK / HUMAN REVIEW
```

Ten etap nie wymaga zapisu PDF.

### ETAP B — CONTROLLED SDS REGISTRATION / COMMIT

Pełna rejestracja SDS nadal musi respektować obowiązujące BDR/TDR dotyczące:

```text
fizycznego PDF
SDS_ROOT_PATH
kontrolowanego importu
CURRENT / ARCHIVED
human approval
```

Nie zmieniaj tych zasad w TASK-050.

---

## 6. PRZYPADEK REFERENCYJNY — ALUCYNK

PRECHECK potwierdził, że Evidence JSON dla ALUCYNK zawiera poprawnie rozpoznane:

```text
product_name = ALUCYNK
manufacturer
issue_date
revision
```

oraz:

```text
manufacturer_product_code = NOT_FOUND / NULL
```

Brak PRODUCT `ALUCYNK` w PostgreSQL NIE oznacza błędu ekstrakcji.

Oznacza:

```text
JSON rozpoznał produkt
+
w DB nie istnieje jeszcze odpowiadający PRODUCT
```

TASK-050 ma przeanalizować przypadek ALUCYNK jako scenariusz:

```text
CREATE candidate
```

a nie jako błąd rozpoznania produktu.

---

## 7. CREATE-OR-LINK — ANALIZA

Przeanalizuj minimalny mechanizm decyzyjny:

| Stan | Oczekiwany wynik |
|---|---|
| jednoznaczny PRODUCT istnieje | `LINK` |
| PRODUCT nie istnieje | `CREATE CANDIDATE` |
| kilka możliwych PRODUCT | `HUMAN REVIEW` |
| jednoznaczny MANUFACTURER istnieje | `LINK` |
| MANUFACTURER nie istnieje | `CREATE CANDIDATE` |
| kilka możliwych MANUFACTURER | `HUMAN REVIEW` |
| `manufacturer_product_code=NULL` | nie blokuje |
| niejednoznaczna tożsamość | `HUMAN REVIEW` |

Nie projektuj fuzzy matching jako automatycznej decyzji.

Nie łącz produktów wyłącznie na podstawie podobieństwa nazw.

Nie twórz automatycznie nowych rekordów podczas tej analizy.

---

## 8. ISTNIEJĄCY `AcceptSds`

PRECHECK wskazuje, że istniejący `AcceptSds`:

```text
może utworzyć MANUFACTURER
może utworzyć PRODUCT
może utworzyć SDS
```

ale aktualnie wymaga danych, których BATCH-001 JSON może nie zawierać, m.in.:

```text
manufacturer_product_code
use_description
use_restriction
```

Sprawdź:

1. które z tych wymagań wynikają z Core/BDR,
2. które są wyłącznie obecnym kontraktem Application/UI,
3. które pola rzeczywiście muszą być obowiązkowe przy pierwszej rejestracji PRODUCT,
4. czy `AcceptSds` może zostać minimalnie dostosowany do obsługi Evidence JSON,
5. czy można wykorzystać istniejącą logikę zamiast tworzyć nowy parallel create workflow.

Nie zakładaj automatycznie, że `use_description` i `use_restriction` mają stać się opcjonalne.

Jeżeli ich obecne wymaganie blokuje JSON → DB, wskaż to jako osobną decyzję wymaganą od Architekta.

---

## 9. PRODUCENT — NORMALIZACJA I TOŻSAMOŚĆ

`BATCH-001_GOLDEN_DECISIONS.md` jest zatwierdzonym źródłem referencyjnym człowieka.

Przykłady:

```text
"CX80 POLSKA, CX80 GmbH"
→ canonical: "CX80 POLSKA"

"CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA"
→ canonical: "CX80 POLSKA"
```

Golden Decisions mogą być używane wyłącznie dla identycznych zatwierdzonych przypadków.

Nowy lub tylko podobny wariant:

```text
→ CANDIDATE
→ HUMAN REVIEW
```

Sprawdź, jak CREATE/LINK dla MANUFACTURER powinien wykorzystać wartość kanoniczną bez automatycznego scalania istniejących rekordów `CX80` / `Cx80`.

Nie twórz biblioteki normalizacji runtime w TASK-050.

---

## 10. ZAKRES ANALIZY TECHNICZNEJ

Sprawdź wpływ co najmniej na:

```text
Domain PRODUCT
ORM PRODUCT
PostgreSQL schema
constraints / NOT NULL / indexes / unique constraints
AcceptSdsInput
AcceptSds
AddSdsRevisionInput
AddSdsRevision
ImportSds
repositories
history
Streamlit add-SDS / product forms
product edit UI
SDS-JSON → Application mapping
tests
```

Sprawdź także:

```text
czy manufacturer_product_code jest NOT NULL w DB
czy migration będzie wymagana
czy istnieją unique constraints zależne od kodu
czy kod jest używany w wyszukiwaniu/deduplikacji
czy kod jest chroniony jako identity field
czy UI pozwala obecnie na późniejsze uzupełnienie kodu
```

---

## 11. NIE IMPLEMENTUJ

TASK-050 NIE autoryzuje:

```text
production code changes
Core changes
BDR/TDR changes
schema changes
Alembic migration
DB writes
testowego COMMIT
PDF import
PRODUCT creation
MANUFACTURER creation
CURRENT / ARCHIVED changes
SDS-ALIAS changes
SDS-JSON changes
runtime normalization library
```

---

## 12. RAPORT

Utwórz:

```text
docs/task_reports/TASK-050_IMPACT_ANALYSIS_REPORT.md
```

Raport ma zawierać:

### A. CURRENT STATE

- gdzie `manufacturer_product_code` jest wymagany,
- Domain,
- ORM/schema,
- Application,
- UI,
- tests,
- identity/deduplication.

### B. CORE / DECISION CONFLICT

Jednoznacznie wskaż:

```text
czy nowa decyzja wymaga rewizji Core / BDR
```

oraz dokładnie jakiej reguły.

### C. ACCEPTSDS REUSE

Odpowiedz:

```text
Czy istniejący AcceptSds może być podstawą JSON → DB?
YES / NO / YES WITH CHANGES
```

Wskaż minimalne konieczne zmiany.

### D. ALUCYNK WALKTHROUGH

Pokaż bez zapisu:

```text
ALUCYNK JSON
→ product identity candidate
→ manufacturer resolution
→ CREATE / LINK / HUMAN REVIEW
→ pola brakujące
→ pola gotowe
```

### E. PDF BOUNDARY

Oddziel:

```text
JSON DATA MAPPING
```

od:

```text
FULL SDS REGISTRATION WITH PDF
```

i wskaż, na którym etapie fizyczny PDF jest rzeczywiście wymagany.

### F. REQUIRED DECISIONS BEFORE IMPLEMENTATION

Lista tylko realnych decyzji człowieka.

### G. EXPECTED CHANGE SURFACE

Lista plików / warstw, które wymagałyby późniejszej implementacji.

### H. MIGRATION IMPACT

```text
schema migration required: YES / NO
reason:
```

### I. RECOMMENDATION

Jedna z:

```text
READY_FOR_ARCHITECTURAL_DECISION
BLOCKED_BY_MISSING_DECISION
NO_CHANGE_REQUIRED
```

---

## 13. VALIDATION

To Task analityczny.

Nie uruchamiaj pełnego pytest / Alembic / E2E.

Dozwolone:

```text
targeted source inspection
read-only DB/schema inspection
read-only SQLAlchemy inspection
existing migration inspection
focused grep/search
```

Bez zapisów do operator DB.

---

## 14. STOP CONDITIONS

STOP / BLOCKED, jeżeli:

1. stan repo jest sprzeczny z aktualnym Core,
2. nie można ustalić, skąd wynika obowiązkowość pola,
3. rozwiązanie wymaga zgadywania reguły tożsamości,
4. nie można rozdzielić CREATE od LINK bez nowej decyzji,
5. implementacja wymagałaby wykonania zmian przed zatwierdzeniem decyzji.

---

## 15. AUTHORIZATION

```text
TASK-050
STATUS: READY
PHASE: IMPACT ANALYSIS ONLY
IMPLEMENTATION: NOT AUTHORIZED
```

Uruchomienie:

```text
Wykonaj TASK-050 — wyłącznie analizę wpływu.
```

Po raporcie:

```text
STOP
→ CERBERUS REVIEW
→ ARCHITEKT DECISION
```
