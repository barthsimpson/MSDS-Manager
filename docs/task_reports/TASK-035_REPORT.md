# TASK-035 REPORT — SPRINT-007 Acceptance / Checkpoint

## STATUS

**PASS**

## BASELINE

- TASK-033: DONE; UNIT_OF_MEASURE, FK w current/history i rewizja Alembic a97e2cb7f31d.
- TASK-034: DONE; wybór ACTIVE w Application i Streamlit, kody w Product details i supervisory.
- Oczekiwany i potwierdzony Alembic head: a97e2cb7f31d.
- Baza operatora przed i po acceptance: 3 manufacturers, 2 products, 3 usage_locations, 0 product_usage_locations, 7 product_history, 0 usage_location_history, 0 product_usage_location_history, 4 sds_documents, 4 safety_profiles, 6 sds_components, 3 bhp_decisions, 3 decision_evidence, 5 unit_of_measure. Wszystkie liczności bez zmian.

## FULL REGRESSION

- Końcowy przebieg pełnego pytest na jednorazowym PostgreSQL: **232 passed, 0 failed, 0 errors, 0 skipped**.
- E2E: PASS w pełnym zestawie, w tym wcześniejsze scenariusze Sprintów 2–4, SDS, BHP, rewizji, usuwania produktu oraz widoku nadzorczego.
- SAWarning: NONE; testy uruchomiono z -W error::sqlalchemy.exc.SAWarning.
- Pierwszy przebieg: 224 passed, 6 failed, 0 errors, 0 skipped. Wszystkie porażki sklasyfikowano jako nieaktualne fixture lub asercje testowe po zatwierdzonej zmianie schema/kontraktu:

| Test | Przyczyna | Korekta testu |
|---|---|---|
| test_core_integrity | Fixture podawał stare tekstowe nazwy kolumn jednostek. | Referencje unit_id do seed. |
| test_patch006_sds_revision | Fixture ORM podawał tekst jednostki, w tym dawny kod l/month. | Referencje unit_id do seed l. |
| test_patch007_product_identity | Fixture ORM podawał stare pola tekstowe. | Referencje unit_id do seed l. |
| test_patch008_delete_product | Dwa fixture ORM podawały stare pola tekstowe. | Referencje unit_id do seed l. |
| test_streamlit_shell | Test pustych danych biznesowych liczył pięć obowiązkowych rekordów słownika. | Wyłączenie unit_of_measure z licznika danych biznesowych. |
| test_task016_acceptance | E2E używał dawnego konstruktora bez repository jednostek i tekstowych kodów. | Wstrzyknięcie repository i unit_id seed. |

- Nie wykryto defektu kodu produkcyjnego. W TASK-035 zmieniono wyłącznie testy i ten raport.

## VALIDATION

- Alembic current: a97e2cb7f31d (head) na izolowanym klastrze i w bazie operatora.
- Alembic check: „No new upgrade operations detected”; schema drift: NONE.
- Izolowany cykl upgrade → przykładowy zapis → downgrade → odtworzenie kodu kg w current/history → usunięcie fixture → re-upgrade: PASS. Bazy operatora nie cofano.
- Schema/integrity: pięć kolumn UNIT_OF_MEASURE, deterministyczny seed l/ml/kg/g/szt, UNIQUE code, CHECK category/status, FK obu pól w current/history i CHECK pary monthly: PASS w testach PostgreSQL.
- Application: ACTIVE akceptowane; unknown, INACTIVE, brak MAX unit i monthly value bez unit kontrolowanie odrzucane. NULL/NULL i monthly 0 z aktywną jednostką: PASS.
- History: unit_id i wartości zachowane w snapshotach; zmiana samej jednostki tworzy snapshot. Nowe testy wymusiły błąd historii po zapisie current przy assign i update: rollback current PASS w obu przypadkach.
- Streamlit/AppTest: add/edit korzystają z ACTIVE; brak free-text; widoczny code, UUID ukryte; INACTIVE czytelne w tabeli, niedostępne jako nowy wybór; monthly puste i 0: PASS.
- Product details i supervisory: kody jednostek, bez UUID; semantyka wierszy supervisory i 0 != NULL zachowana.
- Dane operatora: **preserved = YES**. Przed i po acceptance liczności wszystkich 13 tabel były identyczne; head i pięć aktywnych jednostek bez zmian.
- Cleanup: 12 tabel biznesowych w izolowanym klastrze miało 0 rekordów po testach; klaster i własne artefakty tymczasowe usunięto. Brak rekordów TASK-035 w bazie operatora.

## DEFINITION OF DONE

| # | Kryterium | Wynik i dowód |
|---|---|---|
| 1 | unit_of_measure istnieje | PASS — ORM, migracja i odczyt PostgreSQL. |
| 2 | seed l/ml/kg/g/szt | PASS — pięć ACTIVE w bazie operatora i testach. |
| 3 | code UNIQUE | PASS — test constraint. |
| 4 | category VOLUME/MASS/COUNT | PASS — CHECK i test nieprawidłowej wartości. |
| 5 | status ACTIVE/INACTIVE | PASS — CHECK i test nieprawidłowej wartości. |
| 6 | MAX kontrolowana referencja | PASS — unit_id FK, walidacja Application. |
| 7 | Monthly kontrolowana referencja | PASS — unit_id FK, walidacja Application. |
| 8 | monthly NULL → unit NULL | PASS — testy Domain, DB i UI. |
| 9 | 0 != NULL | PASS — testy Application, read model i UI. |
| 10 | INACTIVE bez nowego wyboru | PASS — list_active, use case i AppTest. |
| 11 | INACTIVE czytelne historycznie | PASS — test integracyjny current/history i odczyt kodu. |
| 12 | Zmiana jednostki tworzy snapshot | PASS — test integracyjny historii. |
| 13 | Current + history atomowe | PASS — testy rollback assign i update po błędzie historii. |
| 14 | Brak free-text jednostki w UI | PASS — AppTest obu formularzy. |
| 15 | UI pokazuje kod | PASS — AppTest i Product details. |
| 16 | UUID niewidoczne w UI | PASS — AppTest i formatowanie read models. |
| 17 | Brak automatycznej konwersji | PASS — brak silnika/kolumn konwersji w kodzie i schema. |
| 18 | Brak importu legacy | PASS — brak mappera/importu, migracja wymaga pustych tabel. |
| 19 | Pełna regresja | PASS — 232/232. |
| 20 | Alembic check bez driftu | PASS — brak nowych operacji. |

## SCOPE

- Core changed? NO.
- Schema changed in TASK-035? NO.
- Migration added in TASK-035? NO.
- Dependencies added? NO; pyproject.toml bez zmian.
- Conversion engine? NO.
- Legacy mapping? NO.

## RISKS / DEVIATIONS

- Sześć nieaktualnych testów zostało dostosowanych wyłącznie do zatwierdzonego kontraktu UNIT_OF_MEASURE; pierwszy przebieg i klasyfikacja są udokumentowane wyżej.
- Wskazany w TASK-035 dokument GOV-001 nie występuje w bieżącym repozytorium. Dostępne AGENTS.md i zatwierdzone dokumenty Sprintu/TDR/GOV-002 nie wykazały konfliktu.
- Testy użyły izolowanego klastra oraz transakcji rollback. Dane operatora pozostały nienaruszone.

## FINAL CONCLUSION

**READY TO CLOSE SPRINT-007** — wszystkie 20 kryteriów PASS. Formalne zamknięcie pozostaje decyzją Architekta Operacyjnego.

## NEXT

OCZEKUJĘ NA JAWNE POLECENIE.
