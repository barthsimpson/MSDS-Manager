# TASK-054-R1 REPORT

STATUS:
- TECHNICAL IMPLEMENTATION: DONE
- PHYSICAL UX / SCREENSHOT 1920×1080: PENDING
- OPERATOR COMMIT ALUCYNK: PENDING
- FINAL ACCEPTANCE: PENDING

CHANGED:
- `docs/tasks/TASK-054-R1_Automatyczne_powiazanie_Evidence_JSON_PDF.md` — Task dostarczony przez użytkownika.
- `app/infrastructure/filesystem/evidence_source_pdf.py` — odczyt source PDF wyłącznie z jawnego manifestu batcha i walidacja SHA-256.
- `app/presentation/streamlit/composition.py` — podłączenie resolvera do istniejącej warstwy UI.
- `app/presentation/streamlit/evidence_import.py` — wspólny blok źródeł, auto-binding, fallback i bramka DRY RUN.
- `tests/unit/test_task054_evidence_ui.py`, `tests/integration/test_task054_r1_source_binding.py` — scenariusze UI i izolowanego źródła.
- `docs/task_reports/TASK-054-R1_REPORT.md`.

SOURCE RESOLUTION:
- Runtime bierze lokalizację z repozytoryjnego `docs/sds_bootstrap/BATCH-001_CX/BATCH-001_MANIFEST.json`, pola `input_directory`. Wybiera wyłącznie wpis, którego `json` jest dokładnie nazwą wskazanego Evidence JSON, a `source_file` i `sha256` zgadzają się z polami `source.original_filename` i `source.file_sha256` JSON.
- Czyta tylko `input_directory/source_file`, po sprawdzeniu zwykłej nazwy pliku i pozostania ścieżki w katalogu batcha. Akceptuje PDF jedynie przy sygnaturze `%PDF-` i dokładnym SHA-256 bajtów równym JSON/manifestowi. Sama nazwa nigdy nie zatwierdza powiązania.
- W tym środowisku wskazany w manifeście dysk `V:` nie jest dostępny, więc realny ALUCYNK przechodzi do ręcznego fallbacku. Fallback jest dostępny także dla JSON bez wpisu w kontrolowanym manifeście; wymaga tej samej sygnatury i SHA-256 z JSON. Rozbieżność manifestu z JSON albo hash dostępnego PDF różny od oczekiwanego daje `PDF_MISMATCH` bez fallbacku i bez DRY RUN.

UI:
- Jeden zwarty blok „Evidence JSON / Źródłowy PDF”. Przy auto-bindingu operator wskazuje tylko JSON i widzi nazwę PDF oraz status „PDF powiązany / zweryfikowany; SHA-256 zgodny”.
- Gdy plik z manifestu jest niedostępny, pojawia się „Wskaż źródłowy PDF”. `Uruchom DRY RUN` znajduje się pod wspólnym blokiem i jest aktywny dopiero po poprawnym source binding.
- Zmiana JSON, fallback PDF lub wyniku source binding usuwa bieżący DRY RUN/ApprovedImportPlan. Zabezpieczenia TASK-053 `SOURCE_CHANGED` i `PDF_CHANGED` pozostały bez zmian.

VALIDATION:
- Focused AppTest, unit i targeted integration oraz regresja TASK-052/TASK-053 i ręcznego dodawania SDS: `64 passed`.
- Izolowany manifest + Evidence JSON + PDF: auto-binding, błędny hash przy tej samej nazwie, niedostępny source PDF, poprawny i błędny fallback: PASS.
- `git diff --check` dla zmienionego pliku śledzonego: PASS. Nowe pliki: brak końcowych spacji.
- Aplikacja pod `http://127.0.0.1:8501` odpowiada HTTP 200 na `/_stcore/health`.
- Ponowny zrzut 1920×1080 nie powstał: narzędzie Windows Computer Use zatrzymało dostęp do Chrome, ponieważ nie mogło wiarygodnie ustalić bieżącego URL karty. Fizyczny UX review pozostaje wymagany.

OPERATOR SAFETY:
- Operator DB writes: `0`.
- Operator `SDS_ROOT_PATH` writes: `0`.
- Realny ALUCYNK COMMIT: `0`.
- Integracja użyła wyłącznie izolowanych źródeł testowych, jednorazowej bazy PostgreSQL i tymczasowego SDS root; katalogi testowe R1 zostały usunięte.

SCOPE:
- Bez zmian TASK-052/TASK-053, Core, Domain, ORM, schema, Alembic, parsera, SDS-ALIAS, konfiguracji `.env` i zależności.
- Bez skanowania dysku, nowego staging, batch importu oraz zmian toru „Dodanie ręczne PDF”.

DEVIATIONS / BLOCKERS:
- Automatyczne powiązanie realnego PDF ALUCYNK nie może zostać pokazane w tym środowisku, bo istniejący `input_directory` manifestu na `V:` jest niedostępny. UI poprawnie pokaże ręczny fallback; nie dodano niezatwierdzonej alternatywnej lokalizacji.
- Fizyczny screenshot i ocena czytelności przy 1920×1080 / 100% pozostają do wykonania przez Architekta Operacyjnego.

NEXT:
- STOP → Cerberus review → fizyczny UX review → decyzja Architekta Operacyjnego. Realny COMMIT ALUCYNK pozostaje osobną świadomą akcją operatora.
