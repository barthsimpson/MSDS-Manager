# TDR-014 — Kontrolowane wycofanie błędnie zarejestrowanego SDS

**Projekt:** MSDS Manager  
**Wersja:** 0.2-approved  
**Status:** APPROVED — zatwierdzony przez Architekta Operacyjnego 2026-11-03  
**Data:** 2026-11-03  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Podstawa:** CORE-001 v1.8-approved_BDR012; BDR-012 v1.1-approved; TDR-014 v0.1-draft; TDR-014 Technical Precheck Report (2026-11-03)

## 1. Cel i zasada minimalizmu

Jedna akcja użytkownika **„Wycofaj błędnie zarejestrowany SDS”** w istniejącej karcie produktu. Dokument zostaje oznaczony `INVALIDATED`, ale jego rekord, PDF, historia, Safety, Components i dowody BHP pozostają w bazie. Nie wprowadza się nowego workflow, warstwy usług, statusu BHP ani fizycznego DELETE.

Zakres tej funkcji nie obejmuje przywracania SDS już oznaczonego `INVALIDATED`, masowej korekty danych, housekeeping plików ani zmian Stage 1/Stage 2.

## 2. Kontrakt biznesowy (bez modyfikacji BDR-012)

| SDS wycofywany | Operacja | Skutek dla produktu |
|---|---|---|
| `ARCHIVED` | `ARCHIVED → INVALIDATED`, bez zamiany `CURRENT` | bieżący SDS i `PRODUCT.usage_status` bez zmian |
| `CURRENT`, wariant `NO_CURRENT` | `CURRENT → INVALIDATED`, brak SDS zastępczego | brak `CURRENT`; `PRODUCT → PENDING_APPROVAL` |
| `CURRENT`, wariant `RESTORE_ARCHIVED` | `CURRENT → INVALIDATED`; jawnie wybrany SDS tego samego produktu `ARCHIVED → CURRENT` | `PRODUCT → PENDING_APPROVAL`; wymagana nowa decyzja BHP |

Wybór SDS zastępczego **nie ma wartości domyślnej**. Nie ma przejścia `INVALIDATED → CURRENT/ARCHIVED` w standardowym workflow. Nie wybiera się SDS na podstawie rewizji lub daty automatycznie.

## 3. Minimalny model danych

1. Rozszerzyć `SdsDocumentStatus` oraz bazowy CHECK dla SDS o `INVALIDATED`. Pozostawić istniejący unikalny indeks częściowy zapewniający maksymalnie jeden `CURRENT` na PRODUCT.
2. Dodać pojedynczą tabelę `sds_invalidation` wyłącznie dla tego rodzaju operacji:

| Kolumna | Wymaganie |
|---|---|
| `invalidation_id` | UUID, PK |
| `product_id` | FK do PRODUCT, NOT NULL |
| `invalidated_sds_id` | FK do SDS, NOT NULL, UNIQUE — wycofanie tylko raz |
| `invalidated_from_status` | `CURRENT` albo `ARCHIVED`, NOT NULL |
| `restored_sds_id` | FK do SDS, NULL gdy nie przywrócono |
| `reason` | TEXT, niepuste po trim |
| `invalidated_at` | TIMESTAMPTZ, nadany przez system |

Klucze obce chronią przed usunięciem historii. `restored_sds_id != invalidated_sds_id`, gdy występuje. Kontrolę przynależności obu SDS do PRODUCT wykonuje Application w transakcji. **Bez dodatkowych indeksów bez uzasadnienia zapytaniem.** Brak ogólnego event sourcingu i globalnego audit frameworka.

Osobna tabela jest w tym TDR przyjętym, pojedynczym śladem audytowym; nie tworzy drugiego lifecycle. Pola `restored_sds_id` i `invalidated_at` służą historii operacji, **nie stanowią bramki czasowej BHP**.

## 4. Jedna operacja Application / jedna transakcja

Preferowany use case `InvalidateSds` korzysta z dotychczasowego `TransactionExecutor`, Domain i Repository. UI nie wykonuje SQL. Wejście obejmuje `product_id`, `invalidated_sds_id`, `reason`, jawny wybór wariantu, opcjonalnie `restored_sds_id`, oraz zapamiętany status targetu i identyfikator `CURRENT` dla wykrycia stale state.

W jednej transakcji:

1. Zablokować PRODUCT, potem uczestniczące SDS w deterministycznej kolejności; zastosować zgodną kolejność także wobec operacji BHP mogących modyfikować ten sam PRODUCT/SDS. Bez nowego mechanizmu blokad — wykorzystać istniejące repozytoria i PostgreSQL.
2. Ponownie sprawdzić: PRODUCT/SDS istnieją i są powiązane; target nadal ma oczekiwany `CURRENT/ARCHIVED`; bieżący `CURRENT` nie zmienił się; replacement, jeśli wybrany, nadal jest `ARCHIVED` tego samego PRODUCT; powód nie jest pusty; target nie był wcześniej wycofany.
3. Zmienić target na `INVALIDATED`; opcjonalnie replacement z `ARCHIVED` na `CURRENT`.
4. Jeśli target był `CURRENT`, ustawić PRODUCT na `PENDING_APPROVAL` oraz zapisać PRODUCT_HISTORY **jeżeli status rzeczywiście się zmienił**.
5. Jeśli target był `CURRENT`, zamknąć istniejącym statusem `SUPERSEDED` wszelkie fizycznie `CURRENT` decyzje BHP dotyczące wycofywanego SDS oraz — jeśli występuje — przywróconego SDS. Nie usuwać decyzji ani ich dowodów. Jeżeli target był `ARCHIVED`, nie ingerować w decyzje BHP ani status produktu.
6. Zapisać `sds_invalidation` z przyczyną, czasem, wcześniejszym statusem i wyborem replacement.
7. COMMIT; dowolna niezgodność, błąd audytu, historii lub zapisu → ROLLBACK całości.

**Reguła BHP:** stara decyzja przywróconego SDS nie odzyskuje ważności tylko dlatego, że SDS znowu jest `CURRENT`. Po operacji nowa decyzja powstaje wyłącznie przez istniejący `RegisterBhpDecision`, który tworzy nowy rekord `CURRENT` i dowód. Odczyty bieżącej decyzji muszą respektować aktualny SDS, `record_status=CURRENT` oraz standardowe bramki BHP. **Nie implementować `latest_restore_at`, porównań `registered_at` ani dodatkowych statusów.**

## 5. GUI — istniejąca karta produktu

W sekcji SDS / historia SDS, w grupie **„Więcej akcji”** przy konkretnym `CURRENT` albo `ARCHIVED`, dodać **„Wycofaj błędnie zarejestrowany SDS”**. Nie pokazywać akcji dla `INVALIDATED`.

Po kliknięciu wyświetlić potwierdzenie z identyfikacją produktu, producenta, PDF, rewizji i aktualnego statusu oraz skutkami operacji. Obowiązkowo: `reason`, jawny checkbox potwierdzenia, przy `CURRENT` wybór `RESTORE_ARCHIVED` (z listą bez preselect) albo `NO_CURRENT`, i końcowy przycisk „Wycofaj SDS”. Nie zapisywać przy samym otwarciu formularza.

Po sukcesie odświeżyć widok: `INVALIDATED` jako **„Wycofany / błędna rejestracja”**, data i powód wycofania, historyczny PDF nadal dostępny; aktualny SDS lub brak `CURRENT`; przy wycofaniu wcześniejszego `CURRENT` status `PENDING_APPROVAL`. Przy zmianie danych podczas formularza: komunikat o konieczności odświeżenia, bez ponowienia z automatycznym wyborem.

Wystarcza rozszerzenie obecnego Product Card i odczytu SDS; **nie budować nowego ekranu modułowego ani osobnego mechanizmu uprawnień**.

## 6. Migracja i bezpieczeństwo danych

Jedna migracja Alembic: rozszerzenie CHECK/enum SDS i dodanie `sds_invalidation`, bez zmiany istniejących SDS, PRODUCT, decyzji, PDF, Safety/Components. Po upgrade audyt jest pusty. Downgrade wolno wykonać tylko gdy nie ma `INVALIDATED` ani rekordów audytu; inaczej ma bezpiecznie odmówić, bez automatycznego mapowania statusów i kasowania historii.

Operacja wycofania **nigdy nie usuwa, nie przesuwa i nie nadpisuje PDF** ani nie zmienia `SDS.relative_path`.

## 7. Weryfikacja proporcjonalna do ryzyka

- Testy Application/DB: wszystkie trzy warianty; pusty powód, nieprawidłowy lub obcy replacement, ponowne wycofanie, stale state, nie więcej niż jeden `CURRENT`, poprawność audytu i PRODUCT_HISTORY.
- Testy transakcji: awaria zapisu audytu/historii → pełny rollback; stare decyzje BHP są `SUPERSEDED`, a nowe mogą powstać przez istniejący rejestrator, bez automatycznej reaktywacji; `ARCHIVED` nie zmienia bieżącej decyzji ani PRODUCT.
- Migracja: upgrade, bezpieczny downgrade bez danych, blokowany downgrade z `INVALIDATED`.
- UI: reason i potwierdzenie wymagane, brak automatycznego replacement, prawidłowa historia/PDF i komunikat stale state. Fizyczny przegląd na istniejącej karcie produktu według UI-GUIDE-001.
- Regresja powiązana: rejestracja SDS/revision, BHP/evidence, odczyty bieżącego SDS i PRODUCT. Pełny Level 3 na końcowym acceptance, nie przy każdym drobnym poprawieniu.

Testy na izolowanej/testowej bazie i SDS root; **nie wycofywać żadnego rzeczywistego SDS operatora w ramach implementacji bez odrębnej zgody i scenariusza akceptacyjnego**.

## 8. Granice i STOP

Bez Paczki2, Stage 2, orphan cleanup, deduplikacji, RBAC, nowego frameworka czy przebudowy ogólnego BHP. STOP przy sprzeczności z Core/BDR, niemożności zapewnienia atomowości, niezgodnym lifecycle BHP, braku bezpiecznej migracji lub konieczności zmian domenowych poza zakresem; zgłosić konkretny blocker. Nie wykonywać innych poprawek przy okazji.

## 9. Authorization boundary

TDR-014 v0.2 jest **APPROVED** decyzją Architekta Operacyjnego z 2026-11-03. Wykonanie implementacji autoryzowano osobno dla TASK-060 w tym samym dniu. Sam TDR nie jest niezależną autoryzacją przyszłych zmian poza TASK-060.

## 10. Historia

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-11-02 | Draft | Pierwszy projekt statusu `INVALIDATED`, audytu, transakcji, BHP, GUI |
| 0.2-approved | 2026-11-03 | Approved | Architekt Operacyjny zatwierdził wersję 0.2 bez zmian merytorycznych wobec draftu; uproszczony lifecycle BHP z `CURRENT/SUPERSEDED` |
