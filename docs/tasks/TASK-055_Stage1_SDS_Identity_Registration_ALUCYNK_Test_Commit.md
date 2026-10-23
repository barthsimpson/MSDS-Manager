# TASK-055 — Stage 1 SDS Identity Registration + ALUCYNK Test Commit Readiness

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2 + PHYSICAL UX REVIEW  
**Właściciel decyzji:** Architekt Operacyjny  
**Wykonawca:** Codex  

## 1. GOAL

Wdrożyć zatwierdzone rozdzielenie procesu SDS na dwa etapy tak, aby **Etap 1** mógł zarejestrować w MSDS Managerze realny dokument SDS wraz z rozpoznaną tożsamością i metadanymi, bez wymuszania jeszcze ekstrakcji Sekcji 2/3/11.

Docelowy rezultat tego Tasku:

```text
Evidence JSON + źródłowy PDF
→ validation / DRY RUN
→ human review identity
→ PRODUCT + SDS + PDF + metadata
→ dostęp do SDS przez bazę / kartę produktu
```

Po wykonaniu technicznym system ma być gotowy do **jednego świadomego operator COMMIT dla ALUCYNK**.

Codex NIE wykonuje realnego COMMIT ALUCYNK.

---

## 2. APPROVED ARCHITECT DECISION — STAGE SPLIT

Architekt Operacyjny zatwierdził rozdzielenie:

### ETAP 1 — SDS IDENTITY REGISTRATION

Może powstać zarejestrowany SDS zawierający:

- powiązany PRODUCT,
- powiązany MANUFACTURER,
- `manufacturer_product_code = NULL`, jeśli kod nie został odnaleziony,
- `original_filename`,
- źródłowy PDF,
- `issue_date`, jeśli odczytana,
- `revision`, jeśli odczytana,
- status wersji SDS zgodny z istniejącym `CURRENT / ARCHIVED`,
- zachowane source evidence dla danych identyfikacyjnych.

Brak ukończonej ekstrakcji Safety w Etapie 1:

```text
NIE oznacza NO_DATA
NIE oznacza NO
NIE tworzy pustego / syntetycznego SAFETY_PROFILE
NIE tworzy fikcyjnych SDS_COMPONENT
```

### ETAP 2 — SDS SAFETY ENRICHMENT

Osobny przyszły Sprint / commit obejmie:

- Sekcję 2,
- Sekcję 3,
- Sekcję 11,
- `SAFETY_PROFILE`,
- `SDS_COMPONENT`,
- walidację `YES / NO / NO_DATA / NOT_APPLICABLE`,
- human review danych bezpieczeństwa.

Etap 2 wzbogaca **ten sam `sds_id`**. Nie tworzy nowego SDS wyłącznie dlatego, że dodano Safety/Components.

---

## 3. STATUS / LIFECYCLE RULES

Nie dodawaj nowego statusu SDS.

```text
CURRENT / ARCHIVED
```

nadal opisuje wyłącznie wersję dokumentu.

Nie używaj statusu SDS do oznaczania kompletności Safety.

Po Etapie 1 PRODUCT może istnieć jako `PENDING_APPROVAL`, ale brak Safety enrichment musi blokować świadomą finalną decyzję BHP, jeżeli obecny workflow pozwalałby ją wykonać bez wymaganych danych.

Preferowana realizacja bez schema change:

```text
brak SAFETY_PROFILE dla CURRENT SDS
→ derived state: SAFETY ENRICHMENT PENDING
→ brak możliwości finalnej decyzji BHP
```

Nie dodawaj nowej kolumny/statusu bez STOP i decyzji Architekta.

---

## 4. AUTHORITATIVE CONTEXT

Minimalnie użyj:

1. `GOV-001_Zasady_wspolpracy_v1.0-approved`
2. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
3. aktualny `CORE-001` z BDR-009
4. `BDR-005_MSDS_Manager_v1.0-approved`
5. `BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved`
6. `TDR-006_Kontrolowany_import_SDS_v1.0-approved`
7. `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved`
8. `TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved`
9. `TASK-052` + raport
10. `TASK-053` + raport
11. `TASK-054` + raport
12. `TASK-054-R1` + raport
13. `BATCH-001_CX/BATCH-001_MANIFEST.json`
14. `BATCH-001_CX/BATCH-001_GOLDEN_DECISIONS.md`
15. `B001-P001_DOC-001.json`

Jeżeli repo zawiera nowsze zatwierdzone wersje tych samych dokumentów, użyj nowszych canonical sources.

---

## 5. KNOWN STARTING POINTS

Sprawdź wyłącznie bezpośrednio powiązane miejsca:

```text
app/application/...
  plan / controlled Evidence JSON import
  AcceptSds / AddSdsRevision / ImportSds

app/presentation/streamlit/evidence_import.py
app/presentation/streamlit/composition.py

app/infrastructure/filesystem/evidence_source_pdf.py

tests dotyczące TASK-052 / TASK-053 / TASK-054 / TASK-054-R1
```

Nie wykonuj repo-wide refactor/discovery bez dowodu potrzeby.

---

## 6. REQUIRED IMPLEMENTATION

### A. Rozdziel commit readiness

Obecny path traktujący brak pełnego Safety jako bezwzględny blocker dla rejestracji SDS należy zmienić zgodnie z decyzją Etapu 1.

Wprowadź jawne rozróżnienie:

```text
IDENTITY_REGISTRATION_READY
SAFETY_ENRICHMENT_PENDING
```

To mogą być stany Application/DTO/derived state.

**Nie dodawaj statusów do Core ani schema.**

Etap 1 jest READY, gdy co najmniej:

- Evidence JSON jest poprawny,
- wybrano jeden logical SDS,
- PRODUCT identity została rozstrzygnięta przez człowieka,
- MANUFACTURER został rozstrzygnięty przez człowieka,
- source PDF jest poprawnie bound zgodnie z TASK-054-R1,
- `issue_date` / `revision` są przyjęte zgodnie z Evidence JSON,
- wymagane dane PRODUCT spoza ekstrakcji, które są nadal NOT NULL w obecnym modelu, zostały jawnie podane przez operatora,
- operator zatwierdził Stage 1 plan.

Brak `SAFETY_PROFILE` / `SDS_COMPONENT` nie blokuje Stage 1 registration.

### B. Persistence

Stage 1 ma utworzyć / powiązać:

```text
MANUFACTURER
PRODUCT
SDS
PDF w SDS_ROOT_PATH
```

zgodnie z istniejącymi transakcjami i TDR-006.

Nie zapisuj:

```text
syntetycznego SAFETY_PROFILE
pustego SAFETY_PROFILE udającego ocenę
NO_DATA wynikającego tylko z braku ekstrakcji
fikcyjnych SDS_COMPONENT
```

Jeżeli obecny `AcceptSds` nie może zostać bezpiecznie użyty bez pełnego Safety, dodaj minimalny osobny Application use case dla Stage 1 zamiast osłabiać pełny workflow w sposób niekontrolowany.

Nie twórz równoległej logiki SQL w UI.

### C. BHP gate

Jeżeli po Stage 1 istniejący UI/use case umożliwia utworzenie finalnej decyzji BHP dla SDS bez Safety enrichment, zablokuj tę akcję na warstwie Application i odzwierciedl blokadę w UI.

Komunikat użytkowy np.:

```text
Dane bezpieczeństwa SDS nie zostały jeszcze uzupełnione.
Najpierw wykonaj analizę bezpieczeństwa SDS.
```

Nie dodawaj nowego statusu PRODUCT/SDS.

### D. Manufacturer — pierwszy test ALUCYNK

Dla ALUCYNK zachowaj:

```text
RAW:
CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA

approved canonical from Golden Decision:
CX80 POLSKA
```

Podobne rekordy w DB nie mogą zostać automatycznie połączone.

UI ma pokazać kandydatów. LINK do istniejącego producenta wymaga jawnego wyboru operatora.

Nie twórz automatycznie duplikatu tylko przez wielkość liter / podobną nazwę bez human confirmation.

Jeżeli obecne kontrakty TASK-053 nie pozwalają na human-confirmed LINK do podobnego producenta, zatrzymaj tylko ten fragment jako `STOP / DECISION REQUIRED` — nie omijaj resolvera i nie wykonuj silent link.

### E. UI Stage 1

W widoku Evidence JSON:

- nie wymagaj wypełniania Safety do Stage 1 plan,
- pokaż wyraźnie:

```text
Etap 1 — Rejestracja SDS i danych nagłówkowych
Safety / składniki: do uzupełnienia w kolejnym etapie
```

- zachowaj oddzielny DRY RUN → plan → COMMIT,
- zachowaj finalne potwierdzenie operatora,
- po sukcesie przejdź do karty produktu,
- karta produktu musi umożliwiać pobranie/otwarcie CURRENT SDS.

### F. Dokumentacja decyzji

Zaktualizuj w repozytorium wyłącznie w zakresie zatwierdzonej decyzji:

- BDR-005 — dodaj regułę etapowej rejestracji SDS i późniejszego Safety enrichment,
- aktualny CORE-001 — doprecyzuj, że zarejestrowany SDS może istnieć przed Safety enrichment; `SAFETY_PROFILE`/`SDS_COMPONENT` pozostają docelowym zakresem danych SDS, ale brak ich jeszcze po Stage 1 nie może być interpretowany semantycznie jako NO/NO_DATA,
- TDR-013 — zrewiduj commit readiness na Stage 1 vs Stage 2.

Nie zmieniaj innych decyzji.

Jeżeli lokalna konwencja wymaga nowych numerów wersji dokumentów, zachowaj ich identyfikatory i zwiększ wyłącznie wersję rewizji.

---

## 7. ALUCYNK TEST FIXTURE / EXPECTED RESULT

Użyj istniejącego:

```text
B001-P001_DOC-001.json
```

Oczekiwane:

```text
product_name: ALUCYNK
manufacturer_product_code: NULL
issue_date: 2023-01-23
revision: 2.0
source PDF: ALUCYNK 23.01.2023 rew. 2.0.pdf
source SHA-256: zgodny z JSON
manufacturer canonical proposal: CX80 POLSKA
safety: PENDING ENRICHMENT
components: PENDING ENRICHMENT
```

Test integracyjny ma używać izolowanej PostgreSQL + temporary SDS root + testowego PDF o kontrolowanym hash / fixture zgodnym z kontraktem.

**Nie wykonuj realnego operator COMMIT ALUCYNK.**

---

## 8. ACCEPTANCE CRITERIA

| ID | Kryterium | Dowód |
|---|---|---|
| A1 | Stage 1 plan może być READY bez Safety/Components | test Application |
| A2 | Brak Safety nie tworzy `NO_DATA` ani pustego SafetyProfile | test persistence |
| A3 | PRODUCT + SDS + PDF mogą zostać zapisane w izolowanym środowisku | integration test |
| A4 | `manufacturer_product_code=NULL` pozostaje dozwolone | integration test |
| A5 | source PDF binding nadal wymaga SHA-256 | regression R1 |
| A6 | CURRENT/ARCHIVED bez nowych statusów | code/schema review |
| A7 | BHP decision blocked while Safety enrichment absent | Application/UI test |
| A8 | UI pokazuje Stage 1 i Safety pending zamiast formularza Safety jako blocker | AppTest + physical review |
| A9 | human-confirmed manufacturer resolution, no silent similar-name link | test resolver/UI |
| A10 | karta produktu po Stage 1 pokazuje SDS i pozwala go pobrać/otworzyć | integration/AppTest |
| A11 | schema/Alembic unchanged, jeśli nie pojawi się zatwierdzona konieczność | alembic/diff check |
| A12 | operator DB i operator SDS_ROOT_PATH pozostają bez zmian | report evidence |

---

## 9. VALIDATION — LEVEL 2

Wykonaj:

- focused unit/Application tests dla Stage 1 readiness,
- focused tests T052/T053/T054/R1,
- PostgreSQL integration na izolowanej bazie,
- temporary SDS root,
- BHP gate test,
- Streamlit/AppTest,
- related regression `AcceptSds`, `AddSdsRevision`, `ImportSds`, Product Card,
- `git diff --check`.

Nie uruchamiaj pełnego Level 3, jeśli nie ma dowodu potrzeby.

Jeżeli schema się nie zmienia, brak nowej migracji.

---

## 10. DO NOT

Nie implementuj w TASK-055:

- ekstrakcji Sekcji 2,
- ekstrakcji Sekcji 3,
- ekstrakcji Sekcji 11,
- nowych reguł CLP/REACH,
- `SAFETY_PROFILE` enrichment,
- `SDS_COMPONENT` enrichment,
- batch commit wielu SDS,
- automatycznej aktywacji alias candidates,
- samouczącej biblioteki aliasów,
- nowych statusów PRODUCT/SDS,
- realnego operator COMMIT ALUCYNK,
- zmian danych operatora,
- nowych dependencies bez decyzji.

---

## 11. STOP CONDITIONS

STOP / BLOCKED jeżeli:

1. poprawne Stage 1 wymaga nowego statusu lub schema change niezatwierdzonego wyżej,
2. persistence bez Safety wymagałoby zapisania fikcyjnych danych,
3. nie można zablokować BHP decision bez przebudowy Core poza zakresem,
4. source binding nie zachowuje SHA-256,
5. manufacturer resolution wymaga silent link / zgadywania,
6. trzeba zmienić tożsamość PRODUCT poza BDR-009,
7. zmiana wymaga nowych dependencies,
8. operator DB / SDS_ROOT_PATH musiałyby zostać użyte do testów,
9. pojawia się konflikt z nowszym approved canonical source.

Nie rozszerzaj zakresu samodzielnie.

---

## 12. REPORT

Utwórz:

```text
docs/task_reports/TASK-055_REPORT.md
```

Raport ma zawierać:

- STATUS,
- CHANGED,
- DECISION DOC UPDATES,
- STAGE 1 IMPLEMENTATION,
- ALUCYNK READINESS,
- MANUFACTURER RESOLUTION,
- BHP GATE,
- VALIDATION,
- OPERATOR SAFETY,
- DEVIATIONS / RISKS,
- PHYSICAL UX: PENDING,
- NEXT: STOP → CERBERUS REVIEW → PHYSICAL UX → świadomy operator COMMIT ALUCYNK.

Po raporcie zatrzymaj się.

---

## 13. AUTHORIZATION

TASK-055 jest **AUTHORIZED** decyzją Architekta Operacyjnego z 2026-10-23.

Wykonaj wyłącznie TASK-055.
