# TASK-055-R1 REPORT — CORRECTION

## STATUS

DONE — ogólny mechanizm human-confirmed manufacturer LINK. REAL ALUCYNK COMMIT: 0.

## CHANGED

- `app/application/manufacturer_identity.py`: wspólny odczyt dokładnych i podobnych kandydatów bez wpisanej na stałe pary producentów.
- `app/application/dto/approved_import.py`, `app/application/use_cases/controlled_evidence_import.py`, `app/application/use_cases/plan_evidence_json_import.py`: jawny wybór i potwierdzenie, snapshot ID/nazw kandydatów i wybranego rekordu, revalidation przed COMMIT.
- `app/presentation/streamlit/composition.py`, `app/presentation/streamlit/evidence_import.py`: wybór istniejącego `manufacturer_id` spośród pokazanych rekordów oraz osobne potwierdzenie każdego LINK.
- `app/infrastructure/db/repositories/sds_acceptance.py`: użycie wybranego ID i sprawdzenie nazwy ze snapshotu w kontrolowanej transakcji.
- Powiązane testy TASK-053/054/055 oraz izolowana integracja `tests/integration/test_task055_r1_manufacturer_link.py`.

## IMPLEMENTED

Resolver pokazuje dokładne i podobne rekordy jako kandydatów, bez samoczynnego wyboru. Operator może wskazać istniejący rekord i potwierdza powiązanie oddzielnym checkboxem. Bez wybranego ID albo potwierdzenia `ApprovedImportPlan` nie powstaje. Plan przechowuje `selected_id`, nazwę wybranego rekordu oraz snapshot `(manufacturer_id, manufacturer_name)` wszystkich pokazanych kandydatów. Bezpośrednio przed zapisem Application ponownie odczytuje kandydatów w zablokowanej transakcji; zmiana ID, nazwy lub listy daje `STALE_RESOLUTION` i kompensację nowego PDF. Repozytorium dodatkowo sprawdza ID, nazwę i potwierdzenie. CREATE pozostaje możliwy po jawnym przeglądzie podobnych rekordów, lecz istniejący dokładny rekord blokuje CREATE.

## ALUCYNK MANUFACTURER RESOLUTION

- Evidence JSON RAW: `CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA`; Golden canonical: `CX80 POLSKA`.
- Izolowana baza: `CX80`, `CX80 Polska`, `Cx80`. Wszystkie były widoczne jako podobni kandydaci; żaden nie został wybrany automatycznie.
- Test symulował jawny wybór ID rekordu `CX80 Polska`. Po testowym Stage 1 COMMIT PRODUCT `ALUCYNK` wskazuje to istniejące ID. Liczba MANUFACTURER przed/po: 3/3. Nazwy i ID `CX80` oraz `Cx80` nie uległy zmianie.
- Zmiana wybranego ID w planie oraz zmiana nazwy rekordu w bazie po zatwierdzeniu planu zatrzymały COMMIT.

## NO HARDCODE CONFIRMATION

W logice LINK nie ma pary `CX80 POLSKA → CX80 Polska` ani ogólnego automatycznego porównania nazw bez rozróżniania wielkości liter. CX80 służy tu jako fixture integracyjny. Istniejąca od TASK-052 Golden Decision mapująca RAW z Evidence JSON na kanoniczną propozycję pozostaje poza zmianą R1; nie wybiera rekordu DB. Nie dodano biblioteki normalizacji ani trwałej reguły aliasu producenta.

## VALIDATION

- Focused unit/Application, AppTest i izolowane PostgreSQL dla TASK-052/053/054/055 manufacturer resolution i controlled import: **62 passed**.
- Test z inną nazwą producenta potwierdza ten sam wymóg jawnego wyboru i potwierdzenia. Testy odmowne obejmują brak potwierdzenia, ID spoza pokazanych kandydatów oraz zmianę snapshotu przed COMMIT.
- `git diff --check -- app docs tests`: PASS. Brak zmian schema/Alembic, statusów SDS, Safety, BHP gate i Core lifecycle.

## OPERATOR SAFETY

- Integracja działała na jednorazowych bazach PostgreSQL oraz tymczasowym SDS root.
- Operator DB writes: 0. Operator SDS_ROOT_PATH writes: 0. REAL ALUCYNK COMMIT: 0.

## SCOPE

Wyłącznie ogólny human-confirmed LINK do pokazanego producenta i jego kontrola w planie/COMMIT. Bez fuzzy merge, automatycznego LINK, zmiany nazw, scalenia producentów, biblioteki normalizacji, migracji i nowych zależności.

## DEVIATIONS / RISKS

Lista podobnych rekordów pochodzi z istniejącego zapytania diagnostycznego. Jeśli właściwy rekord nie pojawi się na liście, operator nie może go powiązać tą ścieżką bez osobnego rozwiązania tożsamości. Realny PDF i fizyczny UX review ALUCYNK pozostają poza testem kodu.

## NEXT

STOP → CERBERUS REVIEW → PHYSICAL UX → OPERATOR TEST COMMIT ALUCYNK.
