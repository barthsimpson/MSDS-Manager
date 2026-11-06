# TASK-060 — Kontrolowane wycofanie SDS z karty produktu (end-to-end)

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — zatwierdzone przez Architekta Operacyjnego 2026-11-03  
**TASK MODE:** INTEGRATION (GOV-002), walidacja LEVEL 2 + focused GUI  
**Numeracja:** precheck Codexa potwierdził TASK-059 jako ostatni w `docs/tasks/`, TASK-060 nie istniał na dzień 2026-11-03; sprawdzić ponownie przed zapisaniem w repo.

## Cel

Dostarczyć użytkownikowi działającą akcję **„Wycofaj błędnie zarejestrowany SDS”** w istniejącej karcie produktu, dokładnie w trzech wariantach z BDR-012, bez fizycznego DELETE PDF i bez nowego mechanizmu BHP. **Jeden zamknięty rezultat — działająca funkcja, a nie kolejny precheck.**

## Authority / sources

1. CORE-001_MSDS_Manager_v1.8-approved_BDR012.md
2. BDR-012_Wycofanie_blednie_zarejestrowanego_SDS_v1.1-approved.md
3. **TDR-014_Wycofanie_blednie_zarejestrowanego_SDS_v0.2-approved.md** — zatwierdzona specyfikacja techniczna
4. GOV-001, GOV-002, UI-GUIDE-001, AGENTS.md
5. TDR-014_TECHNICAL_PRECHECK_REPORT.md — konkretne ustalenia o obecnym kodzie, nie normatywna decyzja

Codex: przed implementacją umieść/zweryfikuj zatwierdzone źródła w repozytorium zgodnie z obowiązującą strukturą. Jeśli brakuje TDR-014 v0.2-approved lub tekst źródeł jest sprzeczny — STOP, wskaż brak. Nie odtwarzaj TDR z raportu.

## Known starting points — nie przeszukiwać repo od zera

- `app/domain/enums/statuses.py` (`SdsDocumentStatus`)
- `app/infrastructure/db/models/documents.py`, `app/infrastructure/db/models/catalog.py`
- `app/infrastructure/db/transactions.py::TransactionExecutor.execute`
- `app/infrastructure/db/repositories/sds_acceptance.py::_persist_sds` (wzorzec transakcji/historii)
- `app/infrastructure/db/repositories/bhp_decision.py::register` i `app/infrastructure/db/repositories/bhp_decision_query.py::get_current_decision`
- `app/infrastructure/db/repositories/supervisory_query.py`, `analytics_query.py`
- `app/presentation/streamlit/product_registry.py::_render_product_card`
- `app/presentation/streamlit/bhp_decision.py::_render_current_decision`
- `migrations/versions/` (head wg prechecku `b7d4a1f03962`, potwierdzić lokalnie)

## Zakres wykonania

1. **Schema i migracja:** `INVALIDATED`, `sds_invalidation` o minimalnym kontrakcie TDR, zachowanie jednego `CURRENT`, bezpieczny upgrade/downgrade; bez modyfikacji istniejących danych.
2. **Application / DB:** `InvalidateSds`, walidacja reason i stale state, jedna transakcja dla SDS / PRODUCT / historii / audytu / koniecznych zmian decyzji BHP. Zastosować istniejące `SUPERSEDED`; nie dodawać temporal gate i nowych statusów.
3. **Odczyty:** zachować rozróżnienie historycznego `INVALIDATED`; żadna wcześniejsza decyzja BHP nie staje się automatycznie aktywna po restore.
4. **UI:** istniejąca karta produktu → SDS / historia SDS → „Więcej akcji” → akcja wycofania, reason, jawny wybór replacement lub `NO_CURRENT`, checkbox potwierdzenia, czytelny wynik i możliwość otwarcia historycznego PDF.
5. **Testy:** focused/integration na izolowanej DB + temporary SDS root, rollback, przypadki BHP, migracja i read model; AppTest/form UI oraz fizyczny przegląd ekranu jeśli środowisko pozwala. Nie wykonywać zmian na rzeczywistych SDS operatora.

## Acceptance criteria

- A1: `ARCHIVED → INVALIDATED` nie zmienia `CURRENT`, statusu PRODUCT ani jego bieżącej decyzji BHP.
- A2: `CURRENT → INVALIDATED` wymaga jawnego `RESTORE_ARCHIVED` albo `NO_CURRENT`; kończy się `PRODUCT=PENDING_APPROVAL`.
- A3: Gdy restore: stara decyzja przywróconego SDS jest `SUPERSEDED`; zwykły `RegisterBhpDecision` pozwala podjąć nową decyzję, bez automatycznej reaktywacji.
- A4: Reason niepusty; powtórzenie i stale state kończą się bez częściowego zapisu; pełen audyt (status, czas, replacement) jest czytelny.
- A5: PDF, Safety, Components i wcześniejsze decyzje/dowody pozostają; brak zmian w filesystem.
- A6: UI wymusza potwierdzenie, nie preselectuje replacement, pokazuje `INVALIDATED` w historii z powodem/datą i umożliwia odczyt PDF.
- A7: Testy transakcyjne, integracyjne oraz migracje przechodzą; nie naruszono istniejącego workflow SDS/BHP.

## Walidacja i raport

LEVEL 2 według GOV-002: focused tests + adekwatne integracyjne, schema/Alembic, regresja dotkniętych obszarów, `git diff --check`. Osobno kontrola zachowania GUI; jeżeli nie wykonano oględzin, jawnie oznaczyć **NOT VERIFIED** i przekazać do acceptance. Nie uruchamiać nieuzasadnionej pełnej regresji w tym TASK.

Raport `TASK-060_REPORT.md`: lista plików, wynik A1–A7 z dowodami testów, wyniki migracji, DB/FS integrity, czy przeprowadzono oględziny GUI, zakres ewentualnych odstępstw, ryzyka oraz STOP. Podaj test count i commit/hash, jeżeli dotyczy. STOP po raporcie — bez automatycznego TASK-061 i bez testu na produkcyjnych dokumentach.

## Zakazy

Bez przepisywania Core, BDR lub TDR; bez prac przy Paczce2/Stage2, orphan PDF, manufacturer resolver, RBAC; bez usuwania źródeł. Gdy konieczna jest decyzja spoza BDR/TDR lub nowy mechanizm BHP — STOP z opisem konkretnej luki, bez rozwiązania na własną rękę.

## Authorization

**TASK-060 AUTHORIZED:** Architekt Operacyjny 2026-11-03 jawnie zatwierdził TDR-014 v0.2 oraz autoryzował wykonanie TASK-060. Zgoda obejmuje wyłącznie zamknięty zakres tego Tasku, migrację i testy na środowisku izolowanym; **nie obejmuje wykonywania wycofania istniejących SDS w bazie operatora ani uruchamiania następnego zadania**.

**Preflight:** Zweryfikuj, że numer TASK-060 nie został zajęty od ostatniego przeglądu repozytorium i zatwierdzone źródła są dostępne. W przypadku kolizji numeracji STOP, bez samodzielnego przenumerowania zadania.
