# TASK-055 REPORT

## STATUS

TECHNICAL IMPLEMENTATION: DONE. SIMILAR-MANUFACTURER LINK: STOP / DECISION REQUIRED. PHYSICAL UX: PENDING. REAL ALUCYNK OPERATOR COMMIT: NOT PERFORMED.

## CHANGED

- `app/application/dto/approved_import.py`, `app/application/dto/sds.py`, `app/application/use_cases/controlled_evidence_import.py`, `app/application/use_cases/register_stage1_sds.py`, `app/application/use_cases/import_sds.py`, `app/application/use_cases/plan_evidence_json_import.py`: osobny plan i rejestracja Etapu 1.
- `app/infrastructure/db/repositories/sds_acceptance.py`: kontrolowany zapis PRODUCT/SDS bez profilu i składników, z istniejącą transakcją i lifecycle.
- `app/application/ports/bhp_decision.py`, `app/application/use_cases/register_bhp_decision.py`, `app/infrastructure/db/repositories/bhp_decision.py`, `app/infrastructure/db/repositories/bhp_decision_query.py`, `app/application/dto/bhp_decisions.py`: bramka Safety w Application i repozytorium oraz stan pochodny do UI.
- `app/presentation/streamlit/evidence_import.py`, `app/presentation/streamlit/bhp_decision.py`: przegląd Etapu 1, jawne potwierdzenia, komunikat o oczekującym Safety i zablokowana decyzja BHP.
- Testy TASK-052/054, BHP oraz nowy `tests/integration/test_task055_stage1.py`.

## DECISION DOC UPDATES

- `docs/tasks/BDR-005_MSDS_Manager_v1.1-approved_STAGE1.md`: etapowa rejestracja, brak semantyki `NO/NO_DATA` przy braku ekstrakcji, późniejsze wzbogacenie tego samego `sds_id`.
- `docs/tasks/CORE-001_MSDS_Manager_v1.7-approved_STAGE1.md`: SDS może istnieć przed Safety; brak profilu to oczekujące wzbogacenie, nie ocena bezpieczeństwa.
- `docs/tasks/TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.2-approved_STAGE1.md`: `IDENTITY_REGISTRATION_READY` vs `SAFETY_ENRICHMENT_PENDING`, minimalny osobny use case i bramka BHP.
- Poprzednie rewizje pozostawiono jako historię. ORM, schema i migracje Alembic bez zmian.

## STAGE 1 IMPLEMENTATION

- `ApprovedImportPlan` przyjmuje `safety_profile=None` wyłącznie jako świadomy Etap 1. Wymaga poprawnego Evidence JSON, jednego logical SDS, rozstrzygnięć CREATE/LINK, obu pól zastosowania, zatwierdzeń człowieka i PDF z SHA-256 zgodnym z JSON. Plan i commit wiążą fingerprint JSON/PDF; przed zapisem ponownie sprawdzają stan tożsamości w zablokowanej transakcji.
- `RegisterStage1Sds` używa `ImportSds`, kontrolowanego resolvera i istniejącego repozytorium. Tworzy MANUFACTURER/PRODUCT lub wiąże istniejący PRODUCT, zapisuje SDS/PDF/metadane oraz `PENDING_APPROVAL`. Nie tworzy `SAFETY_PROFILE`, `SDS_COMPONENT` ani `NO_DATA`. LINK rewizji zachowuje `CURRENT/ARCHIVED`.
- Pełne `AcceptSds` / `AddSdsRevision` z Safety pozostają dostępne; ich regresja przeszła.
- Evidence identyfikacyjne są widoczne w przeglądzie JSON; repozytoryjny JSON ALUCYNK i zapisany PDF pozostają źródłami. Nie dodano field-level provenance ani nowego Core object.

## ALUCYNK READINESS

- Fixture `B001-P001_DOC-001.json`: `ALUCYNK`, kod producenta `NULL`, `issue_date=2023-01-23`, `revision=2.0`, kanoniczna propozycja `CX80 POLSKA` dla RAW `CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA`.
- Oczekiwany PDF: `ALUCYNK 23.01.2023 rew. 2.0.pdf`; SHA-256 `a5078d259e7d34ff1b89b54e39925ba0b642873a2a6ab22a21ed8af834c81442`.
- Realny PDF nie znajduje się w repozytorium, a `input_directory` manifestu na `V:` nie był dostępny w tym środowisku. Operator może wskazać fallback; ten również musi przejść SHA-256. Nie wykonano realnego COMMIT.
- Test użył kopii JSON z hashem kontrolowanego testowego PDF, izolowanej bazy PostgreSQL i tymczasowego SDS root. Zweryfikowano zapis, odczyt CURRENT PDF z karty produktu, brak profilu/składników, kod `NULL`, drugą rewizję i `CURRENT/ARCHIVED`.

## MANUFACTURER RESOLUTION

- UI pokazuje dokładne i podobne rekordy; CREATE przy podobnych wymaga osobnego potwierdzenia po przeglądzie. W izolowanym teście rekordy `CX80` i `Cx80` nie zostały scalone ani wybrane automatycznie; po jawnym CREATE powstał `CX80 POLSKA`.
- LINK do podobnego rekordu pod inną nazwą pozostaje **STOP / DECISION REQUIRED tylko dla tego wariantu**. Kontrakt TASK-053 dopuszcza LINK wyłącznie do dokładnej zatwierdzonej nazwy. Połączenie `CX80` z zatwierdzonym kanonicznym `CX80 POLSKA` wymagałoby odrębnej decyzji o tożsamości lub kontrolowanej normalizacji; nie obchodzono resolvera.

## BHP GATE

- Brak `SAFETY_PROFILE` dla CURRENT SDS jest pochodnym `SAFETY_ENRICHMENT_PENDING`. `RegisterBhpDecision` odrzuca wtedy finalną decyzję przed walidacją dowodu; repozytorium powtarza kontrolę w transakcji, również dla ścieżki nowego dowodu. UI pokazuje przyczynę i wyłącza przycisk zapisu. Nie dodano statusu PRODUCT/SDS.

## VALIDATION

- Powiązana regresja TASK-052/TASK-053/TASK-054/R1, `AcceptSds`, `AddSdsRevision`, `ImportSds`, Product Card, BHP i izolowana integracja Etapu 1: **139 passed, 1 skipped**; po rozszerzeniu testu Etapu 1 o LINK/rewizję: **24 passed** w skupionym zestawie.
- Test AppTest potwierdza plan Etapu 1 bez formularza Safety, jawne potwierdzenie podobnego producenta, rozdzielenie planu i COMMIT, rerun oraz blokadę BHP. Test integracyjny potwierdza read CURRENT PDF i brak danych Safety.
- `git diff --check -- app docs tests`: PASS dla śledzonych plików. Nowe pliki sprawdzono podczas przeglądu. Brak zmian w `migrations/versions`, modelach ORM i schemacie.

## OPERATOR SAFETY

- Operator DB writes: 0. Operator SDS_ROOT_PATH writes: 0. Realny ALUCYNK COMMIT: 0.
- Testy PostgreSQL utworzyły i usunęły wyłącznie jednorazowe bazy `task054_*`/`task053_*`; PDF trafiał do tymczasowego katalogu testowego. Katalogi `tmp/task055_pytest*` usunięto po testach.

## DEVIATIONS / RISKS

- Podobny producent nie może zostać jawnie powiązany jako LINK przez obecny kontrakt dokładnej nazwy; wymaga decyzji Architekta, jeśli operator zechce użyć takiego rekordu zamiast CREATE.
- Etap 2 Safety enrichment nie jest implementowany w TASK-055. System blokuje finalną decyzję BHP do czasu pojawienia się profilu dla bieżącego SDS.
- Bez realnego PDF na dostępnym dysku nie można potwierdzić automatycznego powiązania ALUCYNK w środowisku operatora; hash źródłowy pozostaje obowiązkowy.

## PHYSICAL UX: PENDING

Fizyczny przegląd przy `1920×1080`, zoom `100%` wymaga operatora. AppTest przeszedł; nie ma zatwierdzonego zrzutu ekranu po zmianach Etapu 1.

## NEXT

STOP → CERBERUS REVIEW → PHYSICAL UX → świadomy operator COMMIT ALUCYNK.
