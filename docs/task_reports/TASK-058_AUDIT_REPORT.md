# TASK-058-AUDIT — integralność po przerwaniu wykonania

**STATUS: PASS**

**Data kontroli i ponowienia:** 2026-10-26
**Tryb:** wyłącznie odczyt; zakres TASK-058 / BATCH-001_CX.

Wszystkie zapisy zadeklarowane przez TASK-058 są kompletne. Nie znaleziono częściowego zapisu DB/PDF ani osieroconego PDF przypisywalnego TASK-058. Skan całego `SDS_ROOT_PATH` ujawnił starsze pliki bez referencji i jedną wcześniejszą podwójną referencję; szczegóły w kontroli C. Nie przypisano tych stanów TASK-058.

## Kontrole A–E

| Kontrola | Wynik | Dowód |
|---|---|---|
| A. Stan DB | PASS | Liczniki 5/35/37/41 zgodne z raportem. Osiem CREATE ma po jednym PRODUCT, SDS `CURRENT` i PRODUCT_HISTORY. Jedna korekta P023 ma kompletny audit `CORRECTION`; P012/P037 bez nowych zapisów. |
| B. DB ↔ filesystem | PASS | Osiem docelowych PDF istnieje pod `SDS_ROOT_PATH` według `SDS.relative_path`, każdy zaczyna się od `%PDF-`, ma pojedynczą referencję SDS i exact SHA-256 zgodne z manifestem oraz JSON. |
| C. Orphan / partial-write scan | PASS dla TASK-058; starsze znaleziska | Brak brakujących plików DB i brak niezarejestrowanych plików w `imported/`. 139 wcześniejszych plików bez referencji DB oraz jedna wcześniejsza podwójna referencja są opisane niżej. |
| D. Lifecycle / transakcje | PASS | Zero produktów z więcej niż jednym SDS `CURRENT`; zero SDS i PRODUCT_HISTORY z nieistniejącym PRODUCT. Stan P023 odpowiada audytowi, P012/P037 preflight. |
| E. Migracje | PASS | `current` i jedyny `head`: `b7d4a1f03962`; `alembic check`: `No new upgrade operations detected.` |

## A i D — baza operatorowa

| Tabela | Oczekiwano | Odczytano |
|---|---:|---:|
| MANUFACTURER | 5 | 5 |
| PRODUCT | 35 | 35 |
| SDS | 37 | 37 |
| PRODUCT_HISTORY | 41 | 41 |

W bazie jest jeden `PRODUCT_IDENTITY_CHANGE`: `30f1f944d7244a43bfb017658bb775a6` dla P023, `change_kind=CORRECTION`. Audit zapisuje producenta `5a43d93166e845d597a296986f2798f7` (`CX80`) → `a11c4d78f64b41f89de6ec0196a9254b` (`CX80 Polska`), a pola starej i nowej nazwy oraz kodu są równe. Bieżący PRODUCT `e8d4fa16679240adb1bf094578367f05` zachował nazwę `CX80 Płyn Konserwująco Naprawczy`, kod `0300-F0DT-500F-GJ25` i ten sam ID. SDS `ba4ecda7d9d1479782acbb84bd5ccf48` pozostaje `CURRENT`. Nie ma korekty P023 bez audytu.

Każda z ośmiu pozycji CREATE (P005, P008, P011, P014, P025, P026, P028, P031) ma dokładnie jeden zgłoszony PRODUCT, jeden SDS `CURRENT` i jeden PRODUCT_HISTORY. W PRODUCT i jego historii `use_description` oraz `use_restriction` są `NULL`. Dla tych SDS stwierdzono **0 SAFETY_PROFILE, 0 SDS_COMPONENT i 0 BHP_DECISION**; w całej starszej bazie tabele te mają odpowiednio 6, 6 i 4 rekordy. P028 to odrębny PRODUCT `4be209382f24438f8d6d7ad92df78c72`, `XBRAKE CLEANER liquid`, kod `NULL`, producent `CX80 Polska`.

P012: brak PRODUCT `CLEANER PROF` utworzonego dla tej pozycji i brak jej nowego SDS/audytu. Wcześniejszy `Cleaner prof` (`ba2c9debc0c04ab3899ae1ce1f059e7f`) ma nadal SDS `f7eb70cce36b49c7a83bfe12f8c0a8b7` `CURRENT`, zgodnie z preflight. Odrębny P008 ma nazwę `CX80 CLEANER PROF` i PDF z innym SHA. P012 pozostał `REVIEW_IDENTITY` bez zatwierdzonego LINK.

P037: wcześniejszy PRODUCT `833c0080c0a34bd1a40f5b2be18b82a6` zachował producenta `a635199aa44944bbbf31cb63808f58d3` (`Cx80`) i trzy wcześniej wykazane SDS; `3da9cedfc58a47158694746b015bbaf2` pozostaje jedynym `CURRENT`. Nie ma nowego SDS ani correction audit. Źródło P037 z 2023-01-24 nadal wymaga decyzji wobec bieżącego SDS z 2026-09-01.

Zapytania kontrolne nie wykazały: produktu z więcej niż jednym `CURRENT`, SDS z nieistniejącym `product_id`, PRODUCT_HISTORY z nieistniejącym `product_id` ani częściowej korekty P023/P037.

## B — osiem PDF TASK-058

`SDS_ROOT_PATH`: `C:\Users\bartosz.murawski\Projects\MSDS-Manager\data\sds`. `relative_path` pochodzi z DB; expected SHA z manifestu i JSON. Actual SHA przeliczono z docelowego pliku. Każdy wiersz ma poprawną sygnaturę `%PDF-` i dokładnie jedną referencję SDS.

| Manifest | SDS ID | `relative_path` | Expected SHA-256 | Actual SHA-256 | Wynik |
|---|---|---|---|---|---|
| P005 | `607a5a70214f44ea9998ab6bfca772a5` | `imported/454d449c-195a-4dc5-94c8-117d3bbc1286.pdf` | `1e0ea1966a591aee27e7e3e2a33bde8bfc8a7703f6618dc2a3bb0b42a247d3a2` | `1e0ea1966a591aee27e7e3e2a33bde8bfc8a7703f6618dc2a3bb0b42a247d3a2` | PASS |
| P008 | `57a5bf2c635742249e3e4a87cc78fdad` | `imported/297e3860-b6ea-4839-9a4f-dd86af23b7d0.pdf` | `d0cd7e31cd45940a50b8a43f0501ea22546383a4646fa2073783a3b4e0dfefa0` | `d0cd7e31cd45940a50b8a43f0501ea22546383a4646fa2073783a3b4e0dfefa0` | PASS |
| P011 | `dcbfd55af29b485ea1d74368767c1972` | `imported/976c209e-29c2-4eff-a516-1cc8e951c7eb.pdf` | `fef92edb18208349fddf6e28ee50674a38e8933643bac71f64e12d1666d8388b` | `fef92edb18208349fddf6e28ee50674a38e8933643bac71f64e12d1666d8388b` | PASS |
| P014 | `0df8111fce2c4006a70f9c3b5e35fcac` | `imported/ec4ef660-2402-4643-85ca-3d9b70772e0e.pdf` | `09d9f4d2dad6216456a783fcfc46ac5e5fd24aca6ea792145ec1bf0c969cbba9` | `09d9f4d2dad6216456a783fcfc46ac5e5fd24aca6ea792145ec1bf0c969cbba9` | PASS |
| P025 | `53b7a9ec15ff40bf9f49107c2cbcbd4a` | `imported/e9ff547b-1010-4c28-83cb-f4e62a4762eb.pdf` | `6d517c2a8a69b9af78ebc1f624cf3023754ce0112a52c53487cb0d6d31b8ba88` | `6d517c2a8a69b9af78ebc1f624cf3023754ce0112a52c53487cb0d6d31b8ba88` | PASS |
| P026 | `b1c6f751031f40bc80642c06e95cafa3` | `imported/23a8b841-2abd-43c2-960d-5f74c4b66086.pdf` | `87e88d63777ff61389d07f615075cd3f57dac029584f5f6567fb204fb8ec55b0` | `87e88d63777ff61389d07f615075cd3f57dac029584f5f6567fb204fb8ec55b0` | PASS |
| P028 | `d1ce1d9b6ed0451695deaace0e0f0500` | `imported/6f115dcb-b311-477c-b842-4a46e2666dea.pdf` | `d4be1dde7758e20ea442df5f9905f3d5de61f2f054fc464448ec213a3d66dc20` | `d4be1dde7758e20ea442df5f9905f3d5de61f2f054fc464448ec213a3d66dc20` | PASS |
| P031 | `a39635fb5a414dde93bcf179f0bec6b0` | `imported/d11a4b24-efba-4994-a752-07149420fa16.pdf` | `7b144cda7552d0652f718a52c1fb9245ceedda417f3cad7b26c046b484aa1307` | `7b144cda7552d0652f718a52c1fb9245ceedda417f3cad7b26c046b484aa1307` | PASS |

Wszystkie 11 źródłowych PDF z katalogu `Paczki/Paczka1 cx` istnieją pod dokładnymi nazwami z manifestu i mają przeliczony SHA zgodny z manifestem. Poza tymi wejściowymi kopiami, ośmioma nowymi plikami, wcześniejszym SDS P012 i P023 oraz wcześniej zarejestrowanym plikiem archiwalnym P028 nie znaleziono dodatkowego niezarejestrowanego pliku o SHA któregokolwiek z tych 11 źródeł.

## C — skan całego `SDS_ROOT_PATH`

| Kategoria | Wynik |
|---|---|
| Wszystkie pliki | 175 PDF |
| Unikalne pliki wskazane przez DB | 36 (37 rekordów SDS) |
| `FILES_WITHOUT_DB_REFERENCE` | 139: 134 wejściowe PDF w `Paczki/` (w tym 37 w `Paczka1 cx`) i 5 starszych PDF w katalogu głównym |
| `DB_REFERENCES_WITHOUT_FILE` | 0 |
| `DUPLICATE_DB_RELATIVE_PATH` | 1 ścieżka, wskazana przez 2 wcześniejsze archiwalne SDS |
| Pliki w `imported/` bez referencji | 0 (33/33 wskazane przez DB) |

Pięć PDF w katalogu głównym bez referencji DB: `CX 80 XBAKE CLEANER rew. 01-08-2015.pdf`, `cx80 TIRE PROTECTOR 30.01.2019 rew. 2.0.pdf`, `CX80 TIRE PROTECTOR rew. 1.2 02.10.2018.pdf`, `Cyna Cynel -Pbfree-z-topnikiem-SW26 rew. 2.2 2018.08.31.pdf`, `cyna_SDS-SLZ-bezołowiowe-z-topnikiem-EVO-EVO11-PRO-SW26-1.1.2 v.5.pdf`. Wszystkie 139 plików bez referencji mają datę utworzenia najpóźniej 2026-10-09, a osiem docelowych PDF TASK-058 datę 2026-10-24. Klasyfikacja: **PRE-EXISTING / PROVENANCE UNKNOWN** dla pięciu plików głównych; 134 to kopie źródłowe w katalogach `Paczki/`. Żaden z nich nie jest niezarejestrowanym plikiem w `imported/`.

`DUPLICATE_DB_RELATIVE_PATH`: `Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf` wskazują archiwalne SDS `ecba2904093f40bf96e2762b6a9ebf09` i `3e8346e132bf4bb69016fc5524434472`. Oba rekordy oraz wspólna ścieżka występowały już w preflight TASK-058; plik ma datę utworzenia 2026-09-21. To wcześniejszy stan, bez związku z ośmioma nowymi PDF.

## E — migracje

| Polecenie odczytowe | Wynik |
|---|---|
| `alembic current` | `b7d4a1f03962 (head)` |
| `alembic heads` | jeden `b7d4a1f03962 (head)` |
| `alembic check` | PASS — `No new upgrade operations detected.` |

**NO WRITES PERFORMED** w operator DB, `SDS_ROOT_PATH` ani katalogu źródłowym. Zapisano wyłącznie ten raport audytowy. Nie wznawiano TASK-058, nie naprawiano wcześniejszych stanów i nie uruchomiono Paczki2.

## Ponowienie audytu

Ponowna kontrola odczytowa 2026-10-26 potwierdziła status **PASS** bez zmiany powyższych wyników. Transakcje zapytań DB ustawiono jako `READ ONLY`. Ponownie stwierdzono liczniki 5/35/37/41, jeden audit P023 `CORRECTION`, osiem kompletów PRODUCT/SDS/HISTORY i zero rekordów Safety/Components/BHP powiązanych z ośmioma nowymi SDS. P012 ma jeden wcześniejszy SDS `CURRENT`, P023 jeden `CURRENT`, a P037 trzy wcześniejsze SDS, z których jeden jest `CURRENT`. Brak naruszeń referencji PRODUCT i lifecycle.

Ponownie przeliczono SHA-256 ośmiu docelowych PDF i wszystkich 11 PDF źródłowych; każde osiem docelowych SHA zgadza się z tabelą B, a dla 11 źródeł manifest, JSON i bajty PDF są zgodne. Ponowny skan: 175 PDF, 139 plików bez referencji DB (134 źródłowe w `Paczki/`, 5 starszych w katalogu głównym), 0 brakujących plików DB, 0 niezarejestrowanych plików w `imported/` i ta sama wcześniejsza podwójna ścieżka dwóch archiwalnych SDS. Nie znaleziono dodatkowego niezarejestrowanego PDF o SHA jednego z 11 źródeł poza katalogiem źródłowym. `alembic current` i jedyny `head` to `b7d4a1f03962`; `alembic check` ponownie zgłosił `No new upgrade operations detected.`

**NO WRITES PERFORMED** w danych biznesowych i PDF także podczas ponowienia; zaktualizowano wyłącznie ten raport.
