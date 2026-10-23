# TASK-054 — Human Review + Controlled Commit UI + ALUCYNK First Operator Import

**Projekt:** MSDS Manager  
**Task ID:** TASK-054  
**MODE:** INTEGRATION  
**VALIDATION:** LEVEL 2 + PHYSICAL UX REVIEW  
**REPORT:** STANDARD INTEGRATION  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI

## 1. GOAL

Zbudować operator-facing workflow wykorzystujący zaakceptowane TASK-052 i TASK-053:

`Evidence JSON DRAFT → DRY RUN → HUMAN REVIEW → ApprovedImportPlan → REVALIDATION → CONTROLLED COMMIT → PRODUCT + SDS + PDF`.

Pierwszym realnym przypadkiem operacyjnym po wdrożeniu ma być `BATCH-001_CX → ALUCYNK → jeden logical SDS`.

TASK-054 nie jest batch importerem. Obowiązuje: `1 operator action → 1 logical SDS → 1 jawne zatwierdzenie → 1 controlled commit`.

## 2. STARTING STATE

TASK-052 = ACCEPTED: validator, mapper, Manufacturer Resolver, Product Resolver, DRY RUN.

TASK-053 = ACCEPTED: ApprovedImportPlan, source binding, HumanApproval, DB revalidation, STALE_RESOLUTION, Controlled Commit, ImportSds, AcceptSds, AddSdsRevision, rollback/compensation.

TASK-053 potwierdził pełny COMMIT w isolated PostgreSQL + temporary SDS_ROOT_PATH. Operator DB i operator SDS_ROOT_PATH nie zostały zmienione.

## 3. AUTHORITATIVE CONTEXT

Przeczytaj minimalnie:
1. `TASK-052_Evidence_JSON_Validator_DRY_RUN_Identity_Resolver.md`
2. `TASK-052_REPORT.md`
3. `TASK-053_Approved_Import_Plan_Controlled_Commit_Foundation.md`
4. `TASK-053_REPORT.md`
5. `TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved.md`
6. `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md`
7. `TDR-006_Kontrolowany_import_SDS_v1.0-approved.md`
8. `BDR-007_Kontrolowany_import_SDS_v1.0-approved.md`
9. `BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved.md`
10. `CORE-001_MSDS_Manager_v1.6-approved_BDR009.md`
11. `UI-GUIDE-001_Standard_UI_Dashboard_Layout_v1.0-approved.md`
12. `GOV-001_Zasady_wspolpracy_v1.0-approved.md`
13. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`
14. root `AGENTS.md`

Sprzeczność authoritative context ze stanem repo → `STOP / BLOCKED`. Nie zgaduj.

## 4. SCOPE

TASK-054 dodaje wyłącznie operator-facing warstwę dla istniejącego mechanizmu:

`Streamlit UI → TASK-052 DRY RUN → human decisions → TASK-053 ApprovedImportPlan → TASK-053 Controlled Commit`.

Dozwolone są minimalne zmiany Application tylko dla poprawnego spięcia UI z istniejącymi use case'ami. Nie twórz drugiego importera ani alternatywnego persistence workflow.

## 5. UI LOCATION

Wykorzystaj istniejący obszar `Dodaj SDS`. Nie dodawaj nowej głównej pozycji sidebaru tylko dla Evidence JSON.

Ekran ma być zgodny z UI-GUIDE-001: modern business dashboard, szeroki layout, mało scrollowania, jasna hierarchia akcji, bez surowego pionowego formularza Streamlit.

Preferowany układ:

`[ŹRÓDŁA I STATUS] [DRY RUN / RESOLUTION]`

`[TOŻSAMOŚĆ PRODUKTU] [SDS / SAFETY]`

`[DANE RĘCZNE / REVIEW]`

`[SUMMARY / WARNINGS / BLOCKERS]`

`[ZATWIERDŹ PLAN] [ANULUJ]`

Po zatwierdzeniu planu: `[WYKONAJ CONTROLLED COMMIT]`.

## 6. SOURCE SELECTION

Operator wskazuje jawnie dwa źródła:

- Evidence JSON,
- odpowiadający mu PDF SDS.

Dla pierwszego realnego przypadku:

- Evidence JSON: `B001-P001_DOC-001.json`,
- produkt: `ALUCYNK`.

PDF musi zostać wybrany jawnie przez użytkownika. Nie wybieraj PDF automatycznie na podstawie podobieństwa nazwy pliku. UI może wyświetlić nazwę spodziewanego source document z JSON tylko jako informację pomocniczą.

## 7. DRY RUN STEP

Po wskazaniu JSON operator uruchamia `DRY RUN`.

UI pokazuje co najmniej:

- validation status,
- product_name,
- manufacturer_product_code,
- manufacturer canonical value,
- manufacturer resolution,
- manufacturer candidates / similar records,
- product resolution,
- issue_date,
- revision,
- manual inputs required,
- safety completeness,
- commit readiness,
- warnings,
- blockers.

Statusy techniczne tłumacz na czytelny tekst użytkowy bez ukrywania znaczenia, np.:

- `CREATE_CANDIDATE` → Nowy rekord — wymaga potwierdzenia,
- `LINK_CANDIDATE` → Powiązanie z istniejącym rekordem — wymaga potwierdzenia,
- `HUMAN_REVIEW` → Wymaga decyzji użytkownika,
- `STALE_RESOLUTION` → Stan danych zmienił się — uruchom ponownie DRY RUN.

## 8. MANUFACTURER REVIEW

Operator jawnie zatwierdza `CREATE Manufacturer` albo `LINK Manufacturer`.

Dla ALUCYNK expected DRY RUN:

`canonical manufacturer = CX80 POLSKA`.

Znane podobne rekordy mogą obejmować `CX80`, `CX80 Polska`, `Cx80`. Nie wolno ich automatycznie wybierać.

UI pokazuje: proposed canonical name, exact result, similar existing records, chosen human action.

## 9. PRODUCT REVIEW

Operator jawnie zatwierdza `CREATE Product` albo `LINK Product`.

Dla ALUCYNK:

- `product_name = ALUCYNK`,
- `manufacturer_product_code = Brak danych`.

Brak kodu producenta NIE BLOKUJE CREATE. UI nie pokazuje `NULL` / `None`.

Jeżeli wybrany jest LINK produktu przy JSON code=NULL, wymagane pozostaje oddzielne jawne potwierdzenie zgodnie z TASK-053.

## 10. MANUAL PRODUCT DATA

Przed utworzeniem ApprovedImportPlan operator musi podać:

- `use_description`,
- `use_restriction`.

UI: `Opis zastosowania *`, `Ograniczenia zastosowania *`.

Nie wypełniaj ich automatycznie na podstawie domysłów.

## 11. SAFETY HUMAN REVIEW

To krytyczna granica TASK-054.

BATCH-001_CX / TASK-052 nie zapewnia kompletnego safety payload wymaganego do Core COMMIT. UI ma umożliwić świadomą weryfikację / uzupełnienie wszystkich pól safety wymaganych przez istniejący `AcceptSds` / Core.

Reguła:

- wartość wyekstrahowana → może być pokazana jako propozycja,
- brak ekstrakcji → puste / wymaga decyzji użytkownika.

ZAKAZ: `brak ekstrakcji → automatyczne NO_DATA`.

Operator może wybrać `NO_DATA` wyłącznie jako świadomą reprezentację treści źródłowego SDS, a nie jako zastępstwo za brak działania parsera.

UI ma odróżniać:

- wartość z Evidence JSON,
- wartość uzupełnioną ręcznie,
- brak decyzji.

Nie implementuj automatycznej decyzji BHP.

## 12. SOURCE EVIDENCE VISIBILITY

Dla danych pochodzących z Evidence JSON operator powinien widzieć co najmniej:

- field,
- value,
- state,
- page,
- section/context, jeśli dostępne,
- source_text.

Pełny viewer PDF nie jest wymagany, jeśli obecna architektura go nie posiada. Operator musi jednak móc pobrać / otworzyć wskazany PDF lub jawnie wybrać go przed zatwierdzeniem.

## 13. APPROVED IMPORT PLAN UI

Przycisk `Zatwierdź plan importu` jest dostępny tylko jeśli:

- JSON VALID,
- Manufacturer decision complete,
- Product decision complete,
- required NULL-code confirmation complete, jeśli dotyczy,
- use_description supplied,
- use_restriction supplied,
- safety payload complete,
- PDF selected and valid.

Po zatwierdzeniu pokaż summary: Produkt, Producent, CREATE/LINK decisions, Kod producenta, SDS issue date, SDS revision, PDF, Manual inputs, Safety complete, Source fingerprint bound.

Plan pozostaje jawnie oddzielony od COMMIT.

## 14. CONTROLLED COMMIT UI

Dopiero po poprawnym ApprovedImportPlan pokaż akcję `Wykonaj import`.

Przycisk musi być jednoznaczny jako operacja zapisująca dane i nie może uruchamiać się domyślnie.

Przed finalnym wywołaniem wymagaj świadomego potwierdzenia, np. `Potwierdzam zapis produktu i SDS do MSDS Managera.`

## 15. STALE / SOURCE CHANGE BEHAVIOR

Jeżeli między ApprovedImportPlan a COMMIT zmieni się JSON, PDF, Manufacturer state, Product state lub LINK target, UI pokazuje:

`Plan nie jest już aktualny. Uruchom ponownie DRY RUN i zatwierdź nowy plan.`

Nie wykonuj silent repair ani automatycznej zmiany CREATE → LINK.

## 16. SUCCESS RESULT

Po udanym COMMIT UI pokazuje co najmniej:

- Import zakończony,
- Product created/linked,
- SDS registered,
- SDS status,
- original_filename.

Dla nowego produktu po pierwszym SDS wynik ma być zgodny z obecnym lifecycle Core / AcceptSds. Nie podejmuj decyzji BHP automatycznie.

Po sukcesie zaoferuj przejście do `Karta produktu` bez tworzenia kolejnej kopii importu przy odświeżeniu strony.

## 17. IDEMPOTENCY / DOUBLE SUBMIT PROTECTION

UI nie może wykonać tego samego COMMIT ponownie przez Streamlit rerun, refresh, podwójne kliknięcie ani powrót do wcześniejszego stanu formularza.

Po udanym COMMIT: plan consumed / UI session state cleared or locked. Ponowne użycie starego planu → STOP.

Jeżeli trwała idempotency wymaga schema change → `STOP / BLOCKED`.

## 18. FIRST REAL OPERATOR IMPORT — ALUCYNK

TASK-054 ma przygotować aplikację do pierwszego realnego importu `ALUCYNK`.

Jednak:

`CODEX MUST NOT execute operator COMMIT on behalf of the user.`

Podczas implementacji i testów:

- operator DB writes = 0,
- operator SDS_ROOT_PATH writes = 0.

Po technicznej walidacji Codex zatrzymuje się na:

`READY FOR PHYSICAL UX REVIEW / OPERATOR COMMIT`.

Następnie Architekt Operacyjny:

1. uruchamia UI,
2. wybiera `B001-P001_DOC-001.json`,
3. wybiera realny PDF ALUCYNK,
4. wykonuje Human Review,
5. uzupełnia manual inputs,
6. uzupełnia / zatwierdza realny safety payload na podstawie SDS,
7. zatwierdza ApprovedImportPlan,
8. świadomie naciska `Wykonaj import`.

Dopiero to jest pierwszy realny COMMIT.

## 19. IMPORTANT — NO BATCH IMPORT YET

Nie implementuj `Import all`, `Commit batch`, `Select all` ani automatycznego zapisu 35 JSON do Core.

BATCH-001_CX pozostaje źródłem kolejnych przypadków, ale TASK-054 dotyczy jednego logical SDS na raz. Pierwszy acceptance case: `ALUCYNK only`.

## 20. IMPORTANT — NO ALIAS LIBRARY WORK

TASK-054 nie rozwija:

- SDS-ALIAS,
- alias candidate management,
- CANDIDATE → ACTIVE workflow,
- pattern learning,
- multi-manufacturer extraction learning.

Mechanizm biblioteki aliasów będzie osobnym etapem. Nie rozszerzaj parsera przy okazji.

## 21. UI-GUIDE-001 REQUIREMENTS

Stosuj co najmniej:

- master/detail logic where applicable,
- wide layout,
- 2-column sections when useful,
- compact forms,
- horizontal Save / Cancel style actions,
- real icons, no emoji,
- `Brak danych` instead of NULL / None,
- clear status chips with text,
- subdued business colors,
- minimal scroll.

Dla istotnej zmiany UI wymagany jest `TECHNICAL VALIDATION + PHYSICAL UX REVIEW`.

Target physical review: `1920×1080`, zoom `100%`.

Sprawdź readability, font hierarchy, action hierarchy, scroll amount, source/review/commit separation, warnings/blockers visibility, duplicate actions, button context.

## 22. EXPECTED CHANGE SURFACE

Przewidywane:

- `app/presentation/streamlit/`,
- `app/application/` — wiring / minimal orchestration only if needed,
- composition / dependency wiring,
- `tests/unit/`,
- `tests/integration/`,
- Streamlit/AppTest tests.

Nie przewiduje się:

- `app/domain/`,
- ORM model changes,
- `migrations/`,
- schema changes.

Jeżeli potrzebna jest zmiana Core / Domain / schema → `STOP / BLOCKED`.

## 23. VALIDATION — LEVEL 2

### Application / UI focused

Testuj co najmniej:

- JSON selection,
- PDF selection,
- DRY RUN rendering,
- CREATE/LINK human decisions,
- similar manufacturer display,
- NULL manufacturer code display = `Brak danych`,
- manual input validation,
- safety incomplete blocker,
- ApprovedImportPlan creation,
- source/PDF changed behavior,
- STALE_RESOLUTION rendering,
- commit confirmation,
- success state,
- double-submit protection.

### Streamlit/AppTest

Potwierdź:

- COMMIT button unavailable before ready plan,
- COMMIT requires explicit confirmation,
- rerun does not duplicate successful commit,
- warnings/blockers remain visible.

### Integration

Użyj wyłącznie `isolated PostgreSQL + temporary SDS_ROOT_PATH`.

Potwierdź ścieżkę:

`ALUCYNK-like JSON → review → ApprovedImportPlan → commit → Product + SDS + PDF`.

Nie używaj operator DB do testów automatycznych.

### Related regression

Minimalnie:

- TASK-052 planner/resolver,
- TASK-053 controlled commit,
- AcceptSds,
- AddSdsRevision,
- ImportSds,
- Product Card navigation after success.

Nie uruchamiaj pełnego pytest bez dowodu potrzeby.

## 24. PHYSICAL UX REVIEW

Po testach technicznych uruchom aplikację dla Architekta Operacyjnego.

Codex raportuje:

```text
TECHNICAL IMPLEMENTATION: DONE
PHYSICAL UX REVIEW: PENDING
OPERATOR COMMIT: PENDING
```

Nie deklaruj TASK-054 jako finalnie ACCEPTED przed fizycznym review użytkownika. Nie wykonuj realnego importu samodzielnie.

## 25. STOP CONDITIONS

STOP / BLOCKED jeśli:

1. UI wymaga zmiany Core.
2. UI wymaga schema / Alembic change.
3. TASK-053 nie pozwala bezpiecznie utworzyć ApprovedImportPlan z UI.
4. Controlled Commit wymaga obejścia Application.
5. Potrzebny byłby bezpośredni SQL / ORM w Streamlit.
6. Nie można oddzielić plan approval od COMMIT.
7. Brak safety danych wymagałby synthetic `NO_DATA`.
8. UI musiałoby automatycznie podejmować decyzję BHP.
9. Nie można zabezpieczyć przed double submit / rerun bez zmiany schema.
10. Realny operator commit byłby potrzebny do automatycznych testów.
11. Implementacja wymaga batch importu.
12. Implementacja wymaga zmian SDS-ALIAS / parsera.
13. Potrzebna jest nowa dependency bez zatwierdzenia.
14. Trzeba zgadywać identity albo source document.

## 26. REPORT

Utwórz `docs/task_reports/TASK-054_REPORT.md`.

Raport ma zawierać:

- STATUS,
- CHANGED,
- IMPLEMENTED,
- UI FLOW: source selection, DRY RUN, manufacturer review, product review, manual inputs, safety review, ApprovedImportPlan, controlled commit,
- ALUCYNK READINESS: Evidence JSON, expected PDF, manufacturer resolution, product resolution, manufacturer_product_code, safety status, operator action still required,
- DOUBLE SUBMIT / RERUN SAFETY,
- VALIDATION: unit/application, Streamlit/AppTest, isolated PostgreSQL integration, temporary SDS root, related regression, git diff --check,
- OPERATOR SAFETY: operator DB writes, operator SDS_ROOT_PATH writes, real ALUCYNK import performed,
- PHYSICAL UX: status PENDING, app URL / launch command,
- SCOPE,
- RISKS / DEVIATIONS,
- NEXT.

## 27. ACCEPTANCE CRITERIA

TASK-054 technical implementation is DONE only if:

1. Existing `Dodaj SDS` exposes controlled Evidence JSON import flow.
2. JSON and PDF are selected explicitly.
3. DRY RUN is visible before decisions.
4. Manufacturer CREATE/LINK requires human decision.
5. Product CREATE/LINK requires human decision.
6. Similar manufacturer records never auto-link.
7. `manufacturer_product_code=NULL` is displayed as `Brak danych` and does not block CREATE.
8. Required manual PRODUCT fields must be supplied.
9. Safety incomplete state blocks plan approval.
10. Missing extraction never becomes automatic `NO_DATA`.
11. Source evidence is visible sufficiently for human review.
12. ApprovedImportPlan is separate from COMMIT.
13. COMMIT is unavailable before plan readiness.
14. COMMIT requires explicit final confirmation.
15. Source/PDF changes invalidate old plan.
16. `STALE_RESOLUTION` stops commit and requires new DRY RUN.
17. Successful flow uses TASK-053 Controlled Commit.
18. No direct SQL/ORM persistence exists in UI.
19. Double submit / rerun does not duplicate import.
20. ALUCYNK-like isolated E2E path passes.
21. Operator DB writes during Codex execution/tests = 0.
22. Operator SDS_ROOT_PATH writes during Codex execution/tests = 0.
23. Real ALUCYNK commit remains a conscious operator action.
24. No batch import is added.
25. No SDS-ALIAS/parser work is added.
26. No Core / Domain / schema / migration changes.
27. No new dependencies without approval.
28. Physical UX review is prepared at 1920×1080 / 100%.

Final acceptance requires additionally:

`PHYSICAL UX REVIEW: PASS by Architekt Operacyjny`.

The real ALUCYNK commit may then be performed by the Architekt through the approved UI.

## 28. AUTHORIZATION

```text
TASK-054
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Start only after explicit command:

`Wykonaj TASK-054.`

After implementation:

`STOP → TASK-054_REPORT → PHYSICAL UX REVIEW BY ARCHITEKT → optional real ALUCYNK operator commit → CERBERUS REVIEW`.

Do not automatically start BATCH-001 mass import. Do not automatically start alias-library work.
