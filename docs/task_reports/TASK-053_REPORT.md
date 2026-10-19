# TASK-053 REPORT

STATUS:
DONE

CHANGED:
- `docs/tasks/TASK-053_Approved_Import_Plan_Controlled_Commit_Foundation.md` — dokument dostarczony przez użytkownika.
- `app/application/dto/approved_import.py`, `app/application/dto/sds.py`
- `app/application/use_cases/controlled_evidence_import.py`
- `app/infrastructure/db/controlled_evidence_registration.py`
- `app/infrastructure/db/repositories/sds_acceptance.py`
- `tests/unit/test_task053_approved_import.py`
- `tests/integration/test_task053_controlled_import.py`
- `docs/task_reports/TASK-053_REPORT.md`

IMPLEMENTED:
- Jawny `ApprovedImportPlan` powstaje z aktualnego DRY RUN i kompletu potwierdzeń człowieka. Obsługuje dowolnego producenta i produkt, decyzje CREATE/LINK oraz znany lub nieznany kod.
- Controlled Commit używa istniejących `ImportSds`, `AcceptSds` i `AddSdsRevision`. Dla PRODUCT CREATE repozytorium wymusza jawne decyzje, zamiast cicho wybierać pierwszy rekord. Kontrolowany wariant repozytorium jest dostępny wyłącznie w transakcji importu z blokadą tożsamości.
- W rejestracyjnej transakcji PostgreSQL blokowane są tabele tożsamości, ponownie odczytywani są wszyscy kandydaci i porównywane są ich ID oraz kody. Zmiana daje `STALE_RESOLUTION`; plan nie przełącza samoczynnie CREATE na LINK.

APPROVED IMPORT PLAN:
- Binding: SHA-256 bajtów Evidence JSON, `document_key`, nazwa źródła, SHA-256 wybranego PDF i nazwa oryginalna PDF.
- Human decisions: jawny CREATE/LINK producenta i produktu, wybrane ID dla LINK, osobne potwierdzenie LINK przy kodzie JSON `NULL`, dane ręczne, safety, PDF oraz identyfikator zatwierdzającego.
- Readiness: brak dowolnego potwierdzenia, pola ręcznego, pełnego safety payload lub PDF uniemożliwia utworzenie planu. Pełny safety payload zawiera jawnie podane statusy wymagane przez obecny Core; importer nie wypełnia braków automatycznym `NO_DATA`.

REVALIDATION:
- Source fingerprint: zmiana JSON daje `SOURCE_CHANGED`; zmiana PDF daje `PDF_CHANGED`.
- Manufacturer / Product: ponowny odczyt exact w transakcji przed rejestracją, kontrola wybranego ID, liczby i tożsamości kandydatów; dla kodu JSON `NULL` również kontrola znanego kodu w DB.
- Stale resolution: `STALE_RESOLUTION`, rollback i kompensacja nowego pliku.

CONTROLLED COMMIT:
- Manufacturer: CREATE lub jawny LINK do wybranego ID.
- Product: CREATE z kodem znanym albo `NULL`; LINK wyłącznie do zatwierdzonego ID przez `AddSdsRevision`, bez korekty istniejącego kodu.
- SDS: istniejąca rejestracja oraz lifecycle `CURRENT/ARCHIVED`.
- PDF: istniejący `ImportSds` i `SdsPdfStorage`; zapis wykluczający overwrite, bezpieczna ścieżka i zachowanie `original_filename`.
- Transaction: blokada tabel i revalidation przed zapisem; jeden commit PostgreSQL albo rollback.

ALUCYNK ISOLATED ACCEPTANCE:
- Manufacturer: utworzono `CX80 POLSKA` na izolowanej bazie.
- Product: utworzono `ALUCYNK`, `manufacturer_product_code IS NULL`.
- Manual inputs: jawne wartości testowe `use_description` i `use_restriction`.
- Safety: kompletny, jawnie dostarczony testowy payload i symulowane potwierdzenie człowieka; nie jest to merytoryczna ocena rzeczywistego SDS ALUCYNK.
- PDF: testowe bajty PDF z sygnaturą, zapisane wyłącznie w tymczasowym SDS root.
- SDS lifecycle: pierwszy SDS `CURRENT`; po jawnym LINK produktu i kolejnej rewizji pierwszy `ARCHIVED`, drugi `CURRENT`.
- DB rows po pierwszym COMMIT: 1 Manufacturer, 1 Product, 1 SDS. `original_filename` i kontrolowany `relative_path` zachowane, plik istnieje.

ROLLBACK / COMPENSATION:
- Testy potwierdziły brak częściowego zapisu przy stale Manufacturer CREATE, stale Product CREATE, brakującym LINK target i zmianie kodu produktu z zatwierdzonego snapshotu.
- Wstrzyknięta awaria DB po flush SDS wycofuje Manufacturer/Product/SDS i usuwa jedynie nowo zapisany PDF.
- Awaria filesystem nie uruchamia rejestracji w DB. Udany COMMIT zachowuje zarejestrowane PDF.

OPERATOR SAFETY:
- Operator PostgreSQL writes: `0` w kodzie i testach TASK-053. Testy tworzyły wyłącznie jednorazowe bazy `task053_*`, usuwane po scenariuszu.
- Operator SDS_ROOT_PATH writes: `0`; użyto tylko tymczasowych katalogów testowych.
- Realny import BATCH-001_CX: nie wykonano.

VALIDATION:
- Focused unit + isolated PostgreSQL + temporary SDS root: `18 passed`.
- Related regression (`TASK-052`, `AcceptSds`, `AddSdsRevision`, `ImportSds`, product identity): `63 passed, 1 skipped`.
- `ImportSds` regression obejmuje no-overwrite, kolizje UUID, path safety, cleanup i pozostawienie pliku po sukcesie.
- `git diff --check` dla śledzonych zmian: PASS. Nowe pliki: brak końcowych spacji.
- Tymczasowe bazy `task053_*` zostały usunięte przez fixtures.

SCOPE:
- UI: NO.
- Operator import: NO.
- Core / Domain / schema / migracje: NO.
- Nowe zależności: NO.
- OCR / runtime AI: NO.

RISKS / DEVIATIONS:
- Bez UI lub uwierzytelnionego kanału zatwierdzeń Application przyjmuje jawny `HumanApproval` od zaufanego wywołującego. Testy symulują tę decyzję; nie stanowią faktycznej aprobaty danych ALUCYNK.
- Nie uruchomiono starszych testów integracyjnych, które zapisują do skonfigurowanej bazy operatora. Powiązane use case'y sprawdzono testami jednostkowymi i nową integracją na izolowanych bazach.

NEXT:
- STOP — Cerberus review i decyzja Architekta. Realny import BATCH-001_CX wymaga osobnego Tasku.
