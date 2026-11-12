# TASK-DRAFT CORE — producent: raport aktualizacji dokumentacyjnej

**STATUS: DONE — DRAFTS FOR CERBERUS REVIEW.** Data: 2026-11-10. Wykonano wyłącznie zmianę dokumentacyjną. BDR-005 v1.2-draft i CORE-001 v1.9-draft **nie są obowiązujące** do czasu osobnego zatwierdzenia; aktualnym Core pozostaje v1.8-approved. Bez implementacji i zmian danych.

## Preflight i wyjaśnienie v1.8

Pierwotny katalog `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, `main`, lokalny HEAD i `origin/main` `8f82529da006615eed8b5ca96995873fd7aa9725`. Zastane nieśledzone pliki TASK-062-R3, dane i dokumenty pozostały nietknięte. `CORE-001_MSDS_Manager_v1.8-approved_BDR012.md` ma nagłówek `1.8-approved` / `Approved` oraz zatwierdzony wpis historii z 2026-11-03; późniejsze dokumenty TASK-060/TDR-014 używają jej jako zatwierdzonej. W §22 pozostawiono trzy zdania z projektu `v1.8-draft`, sprzeczne z nagłówkiem i historią. To błąd statusowego opisu w zatwierdzonym pliku, nie cofnięcie decyzji BDR-012 ani reguł `INVALIDATED`. Obowiązującą rewizją jest v1.8; v1.9-draft ma spójny nowy §22, nie modyfikuje pliku v1.8.

Przeczytano aktualne `AGENTS.md`, GOV-001/002, BDR-005 v1.1, CORE-001 v1.7/v1.8, TDR-012, SDS-JSON-001, SDS-ALIAS-001 i raporty TASK-062-R2/R3 w zakresie tożsamości. GOV-001 §21 pozwala zachować identyfikator przy rewizji tej samej decyzji. BDR-005 już reguluje ekstrakcję, draft i akceptację producenta (§§17–19A), więc zapis decyzji Architekta z 2026-11-10 przygotowano jako **BDR-005 v1.2-draft**, bez wymyślania nowego numeru BDR. Poprzedni raport STOP nadmiernie traktował tę formalizację jako konieczność nowej odrębnej decyzji; ta kontynuacja przygotowuje tylko projekty dokumentów, nie oznacza ich jako Approved. GOV-001 §19 i CORE-001 §21 nadal wymagają zatwierdzonego BDR przed wejściem nowej reguły do obowiązującego Core.

## Zmienione dokumenty i kontrola C1–C8

Utworzono kompletne kopie bazowych wersji z ograniczonymi zmianami:

- `docs/tasks/BDR-005_MSDS_Manager_v1.2-draft_Manufacturer_Proposal.md` — nagłówek Draft, reguła nazwy w §18, nowe §18A, doprecyzowania §19/§19A i §25, referencje oraz historia.
- `docs/tasks/CORE-001_MSDS_Manager_v1.9-draft_Manufacturer_Proposal.md` — nagłówek Draft, reguła w §3.2, tabela i decyzja w §4.1, granica ekstrakcja/zapis w §12, spójny §22 i historia.
- Niniejszy raport, zastępujący wcześniejszy lokalny raport blokady.

| ID | Wynik | Dowód |
|---|---|---|
| C1 | PASS | v1.8-approved potwierdza nagłówek, historia i późniejsze referencje; pozostawiony tekst draft w §22 wskazany i wyjaśniony. |
| C2 | PASS w projektach | CORE v1.9 §4.1 i §12: automatyzacja proponuje, operator potwierdza/koryguje, dopiero kontrolowany zapis; BDR-005 v1.2 §18A. |
| C3 | PASS w projektach | Tabele §4.1 CORE i §18A BDR: `MANUFACTURER_EXPORTER` → propozycja, `SUPPLIER` → jawnie oznaczony kandydat; przykłady OPEX/SYLGARD bez wyjątków produktowych. |
| C4 | PASS w projektach | `EU_REPRESENTATIVE` nie jest samodzielną podstawą propozycji; Valspar zachowuje odrębną rolę. |
| C5 | PASS w projektach | CORE §3.2/§12 i BDR §18A/§19A: bez decyzji operatora brak zapisu PRODUCT, ale odczyt SDS, DRAFT i przegląd trwają. |
| C6 | PASS w projektach | CORE §4.1/§12 i BDR §18A zachowują nazwę, źródłową rolę, cytat i lokalizację w Evidence oraz oryginalny PDF; `SUPPLIER` nie jest przepisywany w JSON na `MANUFACTURER`. |
| C7 | PASS | Trzy nowe pliki dokumentacyjne; bez zmiany kodu, UI, schematu, migracji, PostgreSQL, danych i zatwierdzonych dokumentów. |
| C8 | PASS dla projektów | Nagłówek, §22 i historia CORE v1.9 mówią `Draft`; BDR v1.2 ma `Draft` w nagłówku i historii. Porównania kopii do baz pokazują zmiany tylko w wymienionych miejscach. v1.8 pozostaje obowiązująca. |

**Kontrola porównawcza:** `git diff --no-index` między BDR-005 v1.1/v1.2 i CORE-001 v1.8/v1.9. Zmiany CORE dotyczą wyłącznie nagłówka, §3.2, §4.1, §12, §22 i wpisu historii; nie zmieniono pozostałych reguł PRODUCT, BHP, Safety, lifecycle SDS, REVIEW, ilości, miejsc użycia, jednostek ani `INVALIDATED`. Zmiany BDR dotyczą wyłącznie nagłówka, §18, §18A, §19, §19A, §25, referencji i historii. Nie uruchamiano testów kodu, ponieważ nie zmieniono kodu. Bez commita i push.

## Korekta po kontroli merytorycznej Cerberusa

- BDR-005 §18 i CORE-001 §3.2: z operacyjnej nazwy produktu usuwa się tylko `®` i `™`; Evidence JSON DRAFT zachowuje dosłowną nazwę oraz dowód z treści SDS.
- BDR-005 §19/§19A: akceptacja pełnego draftu i jawne zatwierdzenie ograniczonego Etapu 1 mają odrębny zakres; Etap 2 uzupełnia Safety/Components tego samego `sds_id` po osobnej akceptacji.
- BDR-005 §25: brak trwałego provenance pól w Core nie wyklucza dowodów na poziomie pól w roboczym Evidence JSON DRAFT.

Oba dokumenty pozostają projektami Draft do końcowej kontroli Cerberusa; poza wskazanymi doprecyzowaniami zachowano dotychczasową treść projektów.

**Do zatwierdzenia:** najpierw BDR-005 v1.2, następnie CORE-001 v1.9, po kontroli Cerberusa. Decyzja Architekta określa treść biznesową; statusy plików pozostają Draft do formalnego odbioru. Nie rozpoczynać planera importu, UI ani innej implementacji na podstawie projektów. **STOP.**
