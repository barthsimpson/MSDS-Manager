# PATCH-060-R2 — Kontrolowana migracja bazy operatora (TASK-060)

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — Architekt Operacyjny, 2026-11-03  
**Tryb:** OPERATIONAL / DB MIGRATION, bez zmiany kodu  
**Źródła:** CORE-001 v1.8-approved_BDR012; BDR-012 v1.1-approved; TDR-014 v0.2-approved; TASK-060 AUTHORIZED; TASK-060_REPORT; PATCH-060-R1_REPORT; GOV-001/GOV-002; AGENTS.md.

## 1. Cel i autoryzacja

Przywrócić zgodność istniejącej aplikacji operatora na `localhost:8501` z jej bazą PostgreSQL przez wykonanie **wyłącznie zatwierdzonej migracji Alembic** `b7d4a1f03962 -> e4c6f21a9d80`, po utworzeniu i **zweryfikowaniu** kopii bezpieczeństwa. Rozwiązać potwierdzony błąd `UndefinedTable: sds_invalidation` przy odczycie historii SDS. Architekt Operacyjny jawnie autoryzował tę migrację pod wymienionymi warunkami.

Ta autoryzacja nie obejmuje wycofania żadnego SDS, zmian danych biznesowych, refaktoryzacji, aktualizacji zależności ani dodatkowych migracji.

## 2. Preflight — warunek rozpoczęcia

1. Sprawdź `AGENTS.md`, rzeczywisty katalog repozytorium, aktywną konfigurację aplikacji `localhost:8501` i cel DB. Zidentyfikuj bazę **bez ujawniania hasła, connection stringa lub sekretów**. Nie zakładaj, że port i baza są jednoznacznie powiązane bez potwierdzenia konfiguracji.
2. Odczytaj `alembic current`, `alembic heads`, `alembic_version`, obecność `sds_invalidation` i stan migracji w kodzie. Wymagane: baza `b7d4a1f03962`, jedyny head `e4c6f21a9d80`, brak rozbieżności schematu i brak oznak równoległego procesu migracyjnego.
3. Zanotuj przed zmianą liczniki: `MANUFACTURER`, `PRODUCT`, `SDS`, `PRODUCT_HISTORY`, `BHP_DECISION`, `SAFETY_PROFILE`, `SDS_COMPONENT`, `DECISION_EVIDENCE` oraz, o ile dostępne, liczniki innych tabel relacyjnych. Sprawdź brakujące referencje SDS -> PRODUCT i liczbę produktów z więcej niż jednym SDS `CURRENT`; odnotuj stan wyjściowy bez naprawiania danych.
4. Ustal minimalne bezpieczne okno migracyjne — nie powinno być równoległych zapisów do bazy operatora. Zastosuj istniejącą procedurę zatrzymania/wyciszenia zapisów; **nie wyłączaj ani nie restartuj usług niezwiązanych z tym projektem**. Jeżeli nie można bezpiecznie wykluczyć równoległych zapisów, STOP.
5. Upewnij się, że operacja dotyczy tej samej bazy, w której PATCH-060-R1 odtworzył `UndefinedTable` dla produktu `SYLGARD 160 Silicone Elastomer-Part A`, `product_id=8385e28101e6409c8110d33febbfdc86`.

## 3. Backup — twarda bramka przed zapisem

1. Wykonaj pełny, datowany backup **właściwej bazy operatora** narzędziem PostgreSQL (preferowany format custom, `pg_dump -Fc`; stosuj bezpieczne przekazanie poświadczeń). Zapisz backup poza katalogiem tymczasowym podlegającym automatycznemu czyszczeniu. Nie umieszczaj pliku backupu w repozytorium Git.
2. Sprawdź zakończenie `pg_dump` bez błędu, istnienie i niezerowy rozmiar pliku; wykonaj `pg_restore --list` i potwierdź, że archiwum można odczytać. Zapisz rozmiar, SHA-256, lokalizację, czas i identyfikację bazy.
3. **Zweryfikuj odtwarzalność**: jeśli istnieje bezpieczna, odizolowana testowa baza, odtwórz do niej backup i sprawdź co najmniej istnienie kluczowych tabel oraz zgodność liczników `PRODUCT`/`SDS`. Nie odtwarzaj do bazy operatora. Jeśli odtworzenia testowego nie można wykonać, uznaj backup za niewystarczająco zweryfikowany dla tej autoryzacji — STOP i zgłoś przeszkodę.
4. Dopiero po pozytywnym zakończeniu punktów 1–3 przejdź do migracji.

## 4. Wykonanie — jeden kontrolowany upgrade

1. Ponownie sprawdź tożsamość bazy i `alembic_version` tuż przed zapisem.
2. Uruchom standardową procedurą projektu **wyłącznie** `alembic upgrade e4c6f21a9d80` na bazie operatora. Nie uruchamiaj `downgrade`, `stamp`, resetu schematu, ręcznego DDL ani migracji wykraczających poza wskazany head.
3. Jeżeli migracja zgłosi błąd: **STOP**, zachowaj log i ustal stan faktyczny read-only. Nie ponawiaj automatycznie ani nie odtwarzaj backupu bez osobnej zgody Architekta Operacyjnego.

## 5. Postcheck — read-only

1. Potwierdź `alembic_version=e4c6f21a9d80`, obecność tabeli `sds_invalidation`, odpowiedniego CHECK/enum statusu `INVALIDATED` i niezmienność unikalności jednego SDS `CURRENT` na PRODUCT.
2. Porównaj liczniki z preflight (dla istniejących tabel oczekiwane: brak zmiany); nowa tabela audytu powinna być pusta. Zbadaj referencje SDS/PRODUCT i brak nowych naruszeń integralności.
3. Uruchom **odczytowo** `ShellComposition.list_sds_history` dla wskazanego `SYLGARD 160 Silicone Elastomer-Part A`; oczekiwane: brak wyjątku, obecność istniejącego SDS `CURRENT` / rev. `5.0`. Sprawdź tylko metadane i dostępność ścieżki PDF, bez modyfikacji lub wycofania dokumentu.
4. Niezwłocznie zgłoś niezgodność wyników i STOP; nie wykonuj dodatkowych napraw. Jeżeli postcheck PASS, przywróć zwykły tryb działania aplikacji według zastanej procedury i przekaż operatorowi `localhost:8501` do fizycznego testu: Produkty -> karta SYLGARD -> historia SDS -> otwarcie PDF -> obecność akcji. **Nie klikaj finalnego wycofania prawdziwego SDS**.

## 6. Raport i kryteria akceptacji

Zapisz `PATCH-060-R2_REPORT.md` (zgodnie z konwencją repozytorium) zawierający: identyfikację bazy bez sekretów; preflight i wersje Alembic; liczniki przed/po; lokalizację backupu (nie do repozytorium), rozmiar/SHA-256, `pg_restore --list` i wynik **testowego odtworzenia**; komendę/procedurę upgrade i wynik; read-only postcheck produktu SYLGARD/PDF; ewentualne odstępstwa i niezweryfikowane czynności. Nie dołączaj samego backupu ani danych poufnych.

**PASS tylko jeśli:** backup utworzony i sprawdzony przez próbne odtworzenie; wykonano wyłącznie wskazaną migrację; nowy schemat i liczniki/integralność PASS; odczyt historii SYLGARD nie zgłasza wyjątku; brak modyfikacji PRODUCT/SDS/PDF/BHP. Ręczne oględziny operatora pozostają osobnym warunkiem zamknięcia TASK-060.

**STOP:** brak zweryfikowanego backupu, rozbieżna baza/wersja, aktywne zapisy, nietypowy stan schematu, błąd migracji, problem integralności albo konieczność działania wykraczającego poza powyższy zakres.

## 7. Granice

- NO CODE CHANGES / NO CORE–BDR–TDR CHANGES / NO NEW MIGRATIONS.
- NO BUSINESS DATA WRITES (poza DDL/operacjami wymaganymi przez zatwierdzoną migrację).
- NO SDS INVALIDATION IN OPERATOR DB.
- NO AUTOMATIC RESTORE OR RETRY.
- NO TASK-061, NO PACZKA2, NO STAGE 2, NO unrelated repairs.
- STOP po raporcie, bez deklarowania akceptacji GUI za operatora.
