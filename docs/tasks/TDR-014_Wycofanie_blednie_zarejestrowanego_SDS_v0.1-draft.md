# TDR-014 — Kontrolowane wycofanie błędnie zarejestrowanego SDS

**Projekt:** MSDS Manager  
**Dokument:** TDR-014  
**Wersja:** 0.1-draft  
**Status:** Draft  
**Data:** 2026-11-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Podstawa biznesowa:** BDR-012 v1.1-approved  
**Podstawa Core:** CORE-001 v1.8-draft BDR012  

---

## 1. Cel decyzji technicznej

TDR-014 definiuje minimalny techniczny mechanizm realizacji:

```text
Wycofaj błędnie zarejestrowany SDS
```

zgodnie z zatwierdzonym BDR-012 v1.1.

Mechanizm ma umożliwić:

- `ARCHIVED → INVALIDATED`,
- `CURRENT → INVALIDATED`,
- opcjonalne jawne `ARCHIVED → CURRENT` dla tego samego PRODUCT,
- zachowanie PDF i wszystkich danych historycznych,
- zapis obowiązkowego powodu i czasu wycofania,
- `PRODUCT → PENDING_APPROVAL` po wycofaniu CURRENT,
- brak automatycznej reaktywacji wcześniejszej decyzji BHP,
- spójną atomową transakcję,
- obsługę z GUI bez bezpośredniego SQL ani filesystem writes.

TDR nie autoryzuje implementacji.

---

## 2. Kontekst obowiązujący

TDR-014 należy czytać łącznie co najmniej z:

1. `BDR-012 v1.1-approved`,
2. aktualnym `CORE-001` po zatwierdzeniu rewizji obejmującej BDR-012,
3. `BDR-003 — Dokument SDS, aktualność i wersjonowanie`,
4. `BDR-004 — Decyzja BHP, jej zakres i historia`,
5. `BDR-007 — Kontrolowany import dokumentu SDS`,
6. `TDR-003 — struktura warstw aplikacji`,
7. `TDR-004 — Mechanizm historii danych Core`,
8. `TDR-006 — Kontrolowany zapis / import SDS do SDS_ROOT_PATH`,
9. `TDR-007 — DECISION_EVIDENCE`,
10. `TDR-013 v1.2-approved_STAGE1`,
11. `GOV-001`,
12. `GOV-002`,
13. `UI-GUIDE-001`.

TDR-014 nie zmienia zatwierdzonego modelu importu SDS ani Stage 1 / Stage 2.

---

## 3. Zasada architektoniczna

Operacja jest przypadkiem użycia Application:

```text
Streamlit
→ Application use case
→ Domain validation
→ Repository / transaction
→ PostgreSQL
```

Wycofanie SDS nie wymaga operacji na filesystem.

Streamlit nie wykonuje bezpośrednio:

- `UPDATE` / `INSERT` SQL,
- zmiany statusu SDS,
- zmiany `PRODUCT.usage_status`,
- zapisu audytu wycofania,
- usuwania / przenoszenia / nadpisywania PDF.

PDF pozostaje write-once/read-only po rejestracji.

---

## 4. Rozszerzenie statusu SDS

Persistence SDS musi dopuścić:

```text
CURRENT
ARCHIVED
INVALIDATED
```

`INVALIDATED` oznacza wyłącznie kontrolowane wycofanie błędnie zarejestrowanego SDS.

Nie zmienia się zasada:

```text
maksymalnie jeden CURRENT na PRODUCT
```

Nie wprowadza się standardowego:

```text
INVALIDATED → CURRENT
INVALIDATED → ARCHIVED
```

---

## 5. Model audytu — `SDS_INVALIDATION`

Wprowadza się jedną tabelę audytową:

```text
sds_invalidation
```

Minimalny model:

```text
sds_invalidation
├── invalidation_id            UUID PK
├── product_id                 UUID NOT NULL FK → products
├── invalidated_sds_id         UUID NOT NULL UNIQUE FK → sds
├── invalidated_from_status    VARCHAR NOT NULL
├── restored_sds_id            UUID NULL FK → sds
├── reason                     TEXT NOT NULL
└── invalidated_at             TIMESTAMPTZ NOT NULL
```

### 5.1. `invalidated_from_status`

Dozwolone:

```text
CURRENT
ARCHIVED
```

Nie zapisujemy `INVALIDATED → INVALIDATED`.

### 5.2. `restored_sds_id`

- `NULL` przy wycofaniu ARCHIVED,
- `NULL` przy wycofaniu CURRENT bez przywrócenia wcześniejszego SDS,
- wskazuje jawnie wybrany wcześniejszy SDS przy wariancie przywrócenia.

`restored_sds_id` nie może być równy `invalidated_sds_id`.

Application musi potwierdzić, że oba SDS należą do tego samego PRODUCT.

### 5.3. `reason`

- obowiązkowe,
- po trim nie może być puste,
- przechowuje opis podany przez operatora,
- brak słownika reason codes w tym etapie.

Preferowany CHECK:

```text
length(btrim(reason)) > 0
```

### 5.4. `invalidated_at`

Czas operacji nadawany przez system w ramach tej samej transakcji.

### 5.5. Dlaczego osobna tabela

Nie dodajemy pól `invalidation_reason` / `invalidated_at` bezpośrednio do SDS, ponieważ osobny rekord:

- jest jawnym śladem audytowym operacji,
- przechowuje status wejściowy,
- wiąże opcjonalnie SDS przywrócony,
- dostarcza punkt czasowy potrzebny do kontroli decyzji BHP po przywróceniu,
- nie przeciąża rekordu dokumentu logiką zdarzeniową.

Nie budujemy ogólnego event sourcingu ani uniwersalnego audit logu.

---

## 6. Constraints i indeksy

Minimalnie:

```text
PK(invalidation_id)
UNIQUE(invalidated_sds_id)
FK(product_id → products.product_id) ON DELETE RESTRICT
FK(invalidated_sds_id → sds.sds_id) ON DELETE RESTRICT
FK(restored_sds_id → sds.sds_id) ON DELETE RESTRICT
CHECK(invalidated_from_status IN ('CURRENT','ARCHIVED'))
CHECK(length(btrim(reason)) > 0)
CHECK(restored_sds_id IS NULL OR restored_sds_id <> invalidated_sds_id)
```

Indeksy:

```text
product_id
restored_sds_id
invalidated_at
```

Nie dodajemy nowych indeksów „na przyszłość”.

Istniejący mechanizm zapewniający maksymalnie jeden `CURRENT` dla PRODUCT ma pozostać zachowany; TDR-014 nie przebudowuje go przy okazji.

---

## 7. Application contract

Preferowany use case:

```text
InvalidateSds
```

Nazwy klas mogą zostać dopasowane do konwencji repo bez zmiany semantyki.

Minimalne wejście:

```text
product_id
invalidated_sds_id
reason
replacement_choice
restored_sds_id | NULL
expected_target_status
expected_current_sds_id | NULL
```

`replacement_choice` jest stanem Application/DTO, nie nowym statusem Core.

Dozwolone wartości logiczne:

```text
NOT_APPLICABLE      # target był ARCHIVED
RESTORE_ARCHIVED    # target był CURRENT i wybrano wcześniejszy SDS
NO_CURRENT          # target był CURRENT i świadomie pozostawiono brak CURRENT
```

Dla `RESTORE_ARCHIVED` `restored_sds_id` jest wymagane.

Dla `NO_CURRENT` `restored_sds_id = NULL`.

Dla `NOT_APPLICABLE` target musi być `ARCHIVED`.

---

## 8. Preflight i stale-state protection

UI może zbudować plan na podstawie odczytu, ale przed zapisem Application musi ponownie zweryfikować stan w transakcji.

Minimalnie sprawdza:

1. PRODUCT istnieje,
2. target SDS istnieje i należy do PRODUCT,
3. target ma nadal oczekiwany status `CURRENT` albo `ARCHIVED`,
4. target nie jest `INVALIDATED`,
5. bieżący CURRENT jest zgodny z `expected_current_sds_id`,
6. przy `RESTORE_ARCHIVED` wskazany SDS:
   - istnieje,
   - należy do tego samego PRODUCT,
   - ma nadal status `ARCHIVED`,
   - nie jest targetem,
7. reason po trim nie jest pusty,
8. nie istnieje wcześniejszy `SDS_INVALIDATION` dla targetu.

Jeżeli stan różni się od zatwierdzonego planu:

```text
STOP / stale state
ROLLBACK
```

UI ma wymagać odświeżenia i ponownej decyzji operatora.

Application nie dopasowuje automatycznie starej decyzji użytkownika do nowego stanu.

---

## 9. Transakcja — ARCHIVED → INVALIDATED

Dla targetu `ARCHIVED`:

```text
1. lock / revalidate PRODUCT + target SDS
2. target SDS: ARCHIVED → INVALIDATED
3. INSERT SDS_INVALIDATION
   invalidated_from_status = ARCHIVED
   restored_sds_id = NULL
4. PRODUCT bez zmiany usage_status
5. COMMIT
```

Bieżący `CURRENT` SDS pozostaje bez zmian.

Nie zapisujemy `PRODUCT_HISTORY`, jeżeli żadne pole PRODUCT faktycznie się nie zmieniło.

---

## 10. Transakcja — CURRENT → INVALIDATED bez replacement

Dla świadomego wariantu `NO_CURRENT`:

```text
1. lock / revalidate PRODUCT + target SDS
2. target SDS: CURRENT → INVALIDATED
3. INSERT SDS_INVALIDATION
   invalidated_from_status = CURRENT
   restored_sds_id = NULL
4. PRODUCT.usage_status → PENDING_APPROVAL
5. zapis właściwego PRODUCT_HISTORY, jeśli status PRODUCT uległ zmianie
6. COMMIT
```

Po operacji PRODUCT nie ma `CURRENT` SDS.

System nie tworzy pustego SDS ani placeholdera.

---

## 11. Transakcja — CURRENT → INVALIDATED + restore ARCHIVED

Dla `RESTORE_ARCHIVED`:

```text
1. lock / revalidate PRODUCT + target SDS + restored SDS
2. target SDS: CURRENT → INVALIDATED
3. restored SDS: ARCHIVED → CURRENT
4. INSERT SDS_INVALIDATION
   invalidated_from_status = CURRENT
   restored_sds_id = wybrany SDS
5. PRODUCT.usage_status → PENDING_APPROVAL
6. zapis właściwego PRODUCT_HISTORY, jeśli status PRODUCT uległ zmianie
7. COMMIT
```

Wszystkie zmiany są jedną transakcją.

Niedopuszczalny jest trwały stan częściowy.

---

## 12. Kolejność locków

Repository powinno blokować potrzebne rekordy przed finalną walidacją i zapisem.

Preferowana kolejność:

```text
PRODUCT
→ SDS-y zaangażowane w operację w deterministycznej kolejności po sds_id
```

Celem jest:

- stale-state protection,
- uniknięcie dwóch równoległych zmian CURRENT,
- ograniczenie ryzyka deadlocku.

Dokładny SQL należy do Infrastructure; Application nie wykonuje raw SQL.

---

## 13. BHP — brak nowego statusu decyzji

TDR-014 nie dodaje nowej wartości do:

```text
BHP_DECISION.record_status
```

Pozostaje:

```text
CURRENT
SUPERSEDED
```

Wycofanie SDS nie usuwa ani nie przepisuje istniejących rekordów decyzji BHP.

Decyzja związana z SDS `INVALIDATED` jest historyczna i nie może sterować bieżącym `PRODUCT.usage_status`.

---

## 14. BHP po przywróceniu wcześniejszego SDS

Najważniejsza reguła:

> wcześniejsza decyzja BHP przypisana do przywróconego SDS nie może automatycznie odzyskać skutku operacyjnego.

`SDS_INVALIDATION.invalidated_at` jest punktem czasu przywrócenia, gdy `restored_sds_id` wskazuje dany SDS.

Dla SDS przywróconego do CURRENT za operacyjnie aktualną można uznać dopiero decyzję BHP zarejestrowaną **po najnowszym takim przywróceniu**.

Reguła read model / gate:

```text
latest_restore_at = MAX(sds_invalidation.invalidated_at)
                    WHERE restored_sds_id = current_sds_id

jeżeli latest_restore_at istnieje:
    skuteczna decyzja BHP musi mieć registered_at > latest_restore_at
```

Jeżeli `latest_restore_at` nie istnieje, dla SDS nieprzywracanego przez BDR-012 obowiązuje dotychczasowa logika.

Nie wykonuje się backfillu fikcyjnych zdarzeń dla starych SDS.

---

## 15. Rejestracja nowej decyzji BHP po restore

Przywrócony SDS:

```text
CURRENT
+
PRODUCT = PENDING_APPROVAL
```

musi przejść zwykły workflow nowej decyzji BHP.

Obowiązujące pozostają wszystkie dotychczasowe bramki, w szczególności:

- wymagany Safety enrichment dla CURRENT SDS,
- wymagane pola administracyjne, jeśli nadal obowiązują w aktualnym workflow,
- wymagany DECISION_EVIDENCE.

Jeżeli istniejący `RegisterBhpDecision` nie potrafi bezpiecznie zarejestrować nowej decyzji dla SDS posiadającego historyczny rekord `CURRENT`, implementacja ma użyć istniejącego kontrolowanego mechanizmu korekty / supersede albo zatrzymać się na STOP. Nie wolno tworzyć równoległego lifecycle BHP ani silent overwrite.

---

## 16. Read model produktu i decyzji BHP

Po wycofaniu `CURRENT`:

- `PRODUCT.usage_status` pokazuje `PENDING_APPROVAL`,
- decyzja BHP powiązana z `INVALIDATED` SDS jest prezentowana wyłącznie historycznie,
- jeśli brak CURRENT SDS, UI pokazuje jawny brak bieżącej karty,
- jeśli przywrócono SDS, UI pokazuje go jako CURRENT, ale bez automatycznego „odzyskania” wcześniejszej decyzji BHP.

Po nowej decyzji wydanej po restore dotychczasowy model statusu produktu wraca do standardowego workflow.

---

## 17. Safety / Components

Wycofanie SDS nie wykonuje DELETE ani UPDATE treści:

```text
SAFETY_PROFILE
SDS_COMPONENT
```

Dane pozostają związane z `invalidated_sds_id`.

Read model bieżącego produktu nie może używać Safety / Components z `INVALIDATED` jako aktualnego profilu produktu.

Jeżeli przywrócony SDS nie posiada jeszcze Safety enrichment, obowiązuje istniejący `SAFETY_ENRICHMENT_PENDING` i blokada BHP.

---

## 18. Filesystem

Operacja wycofania nie modyfikuje `SDS_ROOT_PATH`.

Zakazane:

```text
DELETE PDF
MOVE PDF
RENAME PDF
OVERWRITE PDF
COPY nowego PDF w ramach invalidation
```

Po COMMIT `relative_path` i plik źródłowy pozostają niezmienione.

Brak pliku fizycznego jest odrębnym problemem dostępności źródła i nie może być „naprawiany” przy okazji invalidation.

---

## 19. UI contract

UI implementuje wymagania BDR-012 v1.1.

Minimalnie:

```text
Produkt
→ SDS / historia SDS
→ działania dodatkowe
→ Wycofaj błędnie zarejestrowany SDS
```

Dla `CURRENT` i `ARCHIVED` akcja jest dostępna.

Dla `INVALIDATED` nie jest dostępna.

Kliknięcie nie zapisuje od razu; otwiera kontrolowany panel/modal z:

- identyfikacją produktu i SDS,
- statusem wejściowym,
- obowiązkowym powodem,
- ostrzeżeniem o zachowaniu PDF/historii,
- dla CURRENT: wyborem `RESTORE_ARCHIVED` albo `NO_CURRENT`,
- listą ARCHIVED bez domyślnego wyboru,
- finalnym podsumowaniem skutków,
- jawnym checkboxem potwierdzenia,
- przyciskiem finalnym `Wycofaj SDS`.

UI nie wykonuje heurystycznego wyboru replacement.

---

## 20. Prezentacja INVALIDATED

`INVALIDATED` pozostaje widoczny w historii SDS.

UI pokazuje co najmniej:

```text
Wycofany / błędna rejestracja
invalidated_at
reason
```

PDF historycznego SDS pozostaje możliwy do otwarcia / pobrania zgodnie z istniejącym mechanizmem dostępu.

`INVALIDATED` nie może być prezentowany jako zwykły `ARCHIVED`.

---

## 21. Obsługa błędów

Minimalne kontrolowane błędy Application:

```text
SdsNotFoundError
SdsInvalidationNotAllowedError
SdsAlreadyInvalidatedError
InvalidInvalidationReasonError
ReplacementSdsNotFoundError
ReplacementSdsNotArchivedError
ReplacementSdsDifferentProductError
SdsInvalidationStaleStateError
```

Nazwy klas mogą zostać dopasowane do konwencji repo.

Błąd persistence / audit / history:

```text
ROLLBACK całej operacji
```

---

## 22. Migracja Alembic

Jedna spójna migracja powinna:

1. rozszerzyć istniejący constraint/status SDS o `INVALIDATED`,
2. utworzyć `sds_invalidation`,
3. dodać constraints i minimalne indeksy,
4. nie modyfikować istniejących rekordów CURRENT/ARCHIVED,
5. nie tworzyć syntetycznych eventów invalidation/restore,
6. nie modyfikować PDF ani danych biznesowych.

Migration review musi ustalić rzeczywistą nazwę tabeli/kolumny statusu i istniejący sposób constraintu; nie wolno zgadywać schematu z dokumentacji.

---

## 23. Downgrade

Nie wolno mapować automatycznie:

```text
INVALIDATED → ARCHIVED
```

ani:

```text
INVALIDATED → CURRENT
```

Jeżeli w bazie istnieje choć jeden:

- SDS o statusie `INVALIDATED`, albo
- rekord `sds_invalidation`,

downgrade do schema bez BDR-012 ma zostać kontrolowanie zablokowany / zakończony błędem przed utratą danych semantycznych.

W pustym / testowym stanie downgrade może:

- usunąć tabelę `sds_invalidation`,
- przywrócić wcześniejszy constraint SDS.

Test migracji musi obejmować oba zachowania.

---

## 24. Data safety

Migracja i implementacja nie mogą:

- zmienić statusu istniejących SDS,
- zmienić PRODUCT,
- zmienić decyzji BHP,
- zmienić Safety / Components,
- zmienić relative_path / original_filename,
- modyfikować plików w SDS_ROOT_PATH,
- tworzyć invalidation records przed świadomą akcją operatora.

Po samym upgrade tabela `sds_invalidation` jest pusta.

---

## 25. Testy — Domain / Application

Wymagane co najmniej:

1. reason pusty / whitespace → reject,
2. target `INVALIDATED` → reject,
3. target o innym statusie niż CURRENT/ARCHIVED → reject,
4. ARCHIVED → INVALIDATED, current bez zmian,
5. CURRENT → INVALIDATED + NO_CURRENT,
6. CURRENT → INVALIDATED + RESTORE_ARCHIVED,
7. replacement nie-ARCHIVED → reject,
8. replacement z innego PRODUCT → reject,
9. replacement = target → reject,
10. brak domyślnego replacement,
11. stale expected status/current → reject,
12. idempotentna ponowna próba tego samego targetu → reject bez drugiego audytu,
13. przy CURRENT PRODUCT kończy jako PENDING_APPROVAL,
14. przy ARCHIVED status PRODUCT pozostaje bez zmian.

---

## 26. Testy — PostgreSQL / transakcja / BHP

Wymagane co najmniej:

1. `sds_invalidation` zapisuje dokładny target/status/reason/time/replacement,
2. UNIQUE target chroni przed drugim invalidation event,
3. current invalidation + restore jest atomowe,
4. błąd insert audytu → rollback statusów SDS i PRODUCT,
5. błąd PRODUCT_HISTORY → rollback statusów SDS i invalidation,
6. po rollback nie pozostaje częściowy audit,
7. stare decyzje BHP nie są usuwane ani nadpisywane,
8. decyzja dla INVALIDATED nie steruje bieżącym produktem,
9. historyczna decyzja przywróconego SDS sprzed `latest_restore_at` nie reaktywuje się,
10. nowa decyzja zarejestrowana po restore może stać się skuteczna przez istniejący workflow,
11. Stage 1 SDS bez Safety po restore nadal blokuje finalną decyzję BHP,
12. zachowany jest maksymalnie jeden CURRENT SDS.

---

## 27. Testy — filesystem / UI

Filesystem:

- przed/po operacji SHA PDF targetu i replacement pozostają identyczne,
- brak nowych PDF,
- brak DELETE/MOVE/RENAME.

UI / AppTest:

- akcja widoczna dla CURRENT/ARCHIVED,
- niewidoczna lub disabled dla INVALIDATED,
- reason wymagany,
- checkbox potwierdzenia wymagany,
- lista replacement bez wyboru domyślnego,
- poprawne podsumowanie CURRENT/ARCHIVED,
- stale state daje komunikat i brak zapisu,
- po sukcesie widok pokazuje INVALIDATED i nowy CURRENT albo brak CURRENT.

Wymagany fizyczny przegląd GUI zgodnie z UI-GUIDE-001 na docelowym widoku desktopowym.

---

## 28. Walidacja migracji

Zmiana schema wymaga:

```text
review
→ upgrade
→ focused PostgreSQL tests
→ downgrade w stanie bez invalidation
→ re-upgrade
→ guarded downgrade test po utworzeniu INVALIDATED
→ alembic current
→ alembic heads
→ alembic check
```

Nie wykonujemy syntetycznej naprawy danych operatora w celu wymuszenia downgrade.

---

## 29. Regresja

Minimalna powiązana regresja obejmuje:

- rejestrację pierwszego SDS,
- AddSdsRevision / CURRENT→ARCHIVED,
- kontrolowany import PDF,
- Stage 1 registration i Safety gate,
- BHP decision + evidence,
- Product Card / historia SDS,
- PRODUCT_HISTORY dla zmiany usage_status.

Pełny repo-wide LEVEL 3 nie jest wymagany dla pojedynczego Tasku foundation/UI, lecz wraca przy acceptance/checkpoint tej funkcji.

---

## 30. Podział implementacji

Preferowany podział zgodny z GOV-002:

```text
Task A — Foundation / Domain / Schema / Application transaction
MODE: INTEGRATION
VALIDATION: LEVEL 2

Task B — Read Model + Streamlit GUI + physical UX
MODE: INTEGRATION
VALIDATION: LEVEL 2

Task C — Acceptance / real case "test delete" / checkpoint
MODE: ACCEPTANCE
VALIDATION: LEVEL 3
```

Nie łączyć implementacji z porządkowaniem starych orphan PDF ani Paczką2.

---

## 31. Poza zakresem

TDR-014 nie implementuje:

- fizycznego DELETE SDS/PDF,
- reaktywacji `INVALIDATED`,
- edycji PDF,
- deduplikacji dokumentów,
- cleanup orphan PDF,
- RBAC / permissions,
- `changed_by` / użytkowników systemowych,
- słownika reason codes,
- Stage 2 extraction,
- Paczki2,
- normalizacji producentów,
- nowego ogólnego audit logu,
- event sourcingu.

---

## 32. STOP conditions

Codex zatrzymuje implementację, jeżeli:

1. rzeczywisty schema SDS nie pozwala bezpiecznie dodać `INVALIDATED` bez szerszej zmiany niż TDR,
2. istniejący lifecycle posiada dodatkowy status lub mechanizm sprzeczny z BDR-012,
3. nie można zachować maksymalnie jednego CURRENT,
4. wymagany byłby fizyczny DELETE / MOVE PDF,
5. nie można wykonać całej operacji w jednej transakcji PostgreSQL,
6. PRODUCT_HISTORY nie pozwala poprawnie zapisać zmiany `usage_status`,
7. istniejący BHP workflow wymaga zmiany semantyki `CURRENT / SUPERSEDED`, aby zapewnić brak auto-reaktywacji,
8. poprawne rozwiązanie wymaga backfillu wymyślonych zdarzeń historycznych,
9. wymagany byłby nowy framework / dependency,
10. trzeba zmieniać Stage 1 / Stage 2 poza integracją bramki,
11. potrzebna jest decyzja biznesowa niewynikająca z BDR-012.

Przy STOP:

```text
bez obejścia
bez raw SQL w UI
bez silent data fix
→ raport do Cerberusa / Architekta
```

---

## 33. Kryterium końcowe

Po pełnym wdrożeniu funkcji:

```text
operator wybiera konkretny SDS
→ Wycofaj błędnie zarejestrowany SDS
→ podaje reason
→ dla CURRENT jawnie wybiera replacement albo NO_CURRENT
→ potwierdza
→ Application revalidates + locks
→ jedna transakcja
→ target = INVALIDATED
→ opcjonalny ARCHIVED = CURRENT
→ PRODUCT = PENDING_APPROVAL przy wycofaniu CURRENT
→ audit SDS_INVALIDATION zapisany
→ PDF i historia bez zmian
→ historyczna BHP nie reaktywuje się
→ UI pokazuje wynik
```

---

## 34. Authorization boundary

TDR-014 po zatwierdzeniu może stanowić authoritative context dla przyszłych Tasków implementacyjnych.

Sam TDR:

```text
nie autoryzuje implementacji
```

Wymagane pozostają:

- zatwierdzony Core obejmujący BDR-012,
- zatwierdzony TDR-014,
- zamknięty Task,
- jawna autoryzacja Architekta Operacyjnego.

---

## 35. Status dokumentu

```text
TDR-014
VERSION: 0.1-draft
STATUS: Draft
```

Decyzja wymaga przeglądu i zatwierdzenia Architekta Operacyjnego przed przygotowaniem Tasku implementacyjnego.

---

## 36. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-11-02 | Draft | Pierwszy projekt techniczny dla BDR-012 v1.1: `INVALIDATED`, `SDS_INVALIDATION`, transakcja, BHP bez auto-reaktywacji, migracja, GUI i testy |
