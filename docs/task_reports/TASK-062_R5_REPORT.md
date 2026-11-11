# TASK-062-R5 — 3M DP-490: aktywacja aliasów i Evidence JSON DRAFT

**Status:** DONE w zakresie R5. **Data:** 2026-11-10. Trzy logiczne SDS w jednym roboczym pliku Evidence JSON DRAFT pozostają `PENDING_REVIEW`; wynik nie zatwierdza producenta, produktu ani importu. **STOP** przed integracją z aplikacją.

## Preflight i zakres

Pracowano wyłącznie w pierwotnym repozytorium `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, na `main`. HEAD i lokalny `origin/main` przed pracą: `7f6e86c70ea51e72ae6540d5e3def273395d5999`. Zastane pliki robocze nie zostały wyczyszczone. Przeczytano dyspozycję R5, raport R4, TDR-012, SDS-ALIAS-001, SDS-JSON-001, zatwierdzone BDR-005 v1.2 i CORE-001 v1.9 oraz kod R2/R3. Dotychczasowy katalog zawierał dziewięć `ACTIVE` A-001–A-009. Oryginalny śledzony PDF 3M pod `docs/sds_Work/` ma 49 stron z warstwą tekstową; SHA-256 przed i po: `deef7ecb51cde457b298155d875d1e88062e1cf94f2b2f35eed6325479730d48`.

Zmodyfikowano istniejący matcher i pipeline R3. Nie utworzono osobnego parsera 3M. Reguły są ograniczone przez etykietę, sekcję i układ: zakresy logicznych SDS, §1.1/§1.3, nagłówek, następną linię, dwie kolumny oraz sąsiednie etykiety negatywne. Nie wykorzystują nazwy pliku, marki, numeru strony jako stałej domenowej ani twardych wartości produktu. Z operacyjnej nazwy usuwane są tylko `®` i `™`; `source_text` zachowuje dosłowny zapis.

## Alias i reguła po decyzji Architekta

| R4 | Katalog / stan końcowy | Wynik |
|---|---|---|
| C-01 / R-01, R-02 | A-010 `Identyfikator produktu` → `product.product_name`, **ACTIVE** | Następny wiersz §1.1; zestawowe §1.1 działa bez drukowanego `SEKCJA 1`, wyłącznie we własnym zakresie. Nie przechwytuje etykiet `Nazwa produktu`/`Nazwa wyrobu` OPEX/SYLGARD. |
| C-02 / R-05 | **Bez aliasu ACTIVE** dla skalarnego kodu | Zatwierdzona reguła kontekstowa rozpoznaje `Numery identyfikacyjne produktu`: przy wielu identyfikatorach `AMBIGUOUS`, `value=null`, z cytatem §1.1; bez bloku `NOT_FOUND`. Nie wybiera pierwszego kodu i nie tworzy pola listowego. |
| C-03 / R-03 | A-011 `Data aktualizacji` → `document_metadata.issue_date`, **ACTIVE** | Bieżąca data DD/MM/YYYY → ISO z nagłówka; sąsiednie `Zastępuje wersję` wykluczone. |
| C-04 / R-03 | A-012 `Numer wersji` → `document_metadata.revision`, **ACTIVE** | Elastyczne odstępy w etykiecie, zachowane `13.00`/`14.00`; bez numeru ID dokumentu i wersji transportu. |
| C-05 / R-04 | A-013 `Dane dotyczące dostawcy karty charakterystyki` → `parties[].name`, **ACTIVE**, rola `SUPPLIER` | Nazwa z `Adres:` wyłącznie w §1.3, przed ulicą; krótki cytat bez całego adresu. Bez copyright, e-maila i automatycznego `MANUFACTURER`. |

Droga statusowa: C-01–C-05 w R4 były `CANDIDATE`; Architekt zatwierdził pakiet w R5. A-010–A-013 wpisano jako `APPROVED`, sprawdzono na oryginalnych stronach i przypadkach negatywnych (**4 passed, 1 etapowo skipped**), po czym przełączono na `ACTIVE` i wykonano pełną regresję (**23 passed, 0 skipped**). C-02 pozostawiono poza katalogiem ACTIVE, ponieważ pluralna etykieta nie pozwala bezpiecznie wyznaczyć jednego `manufacturer_product_code`; jej zatwierdzona reguła kontekstowa zwraca jedynie nieimportowalny stan `AMBIGUOUS`. A-001–A-009 pozostają `ACTIVE` bez zmiany definicji.

## Wynik 3M — trzy logiczne DRAFT z jednego PDF

Źródło: `tmp/task062r5_final_evidence_20261110/3M.evidence.json` i `3M.validation.json` (`schema=SDS-JSON-001`, `schema_version=0.1`). Dla wszystkich `G1=PASS`, `G2=PASS`, `G3=PASS`, `review_status=PENDING_REVIEW`, walidacja dokumentu `REQUIRES_HUMAN_REVIEW`. `G3` zgłasza brak zatwierdzonego producenta dla każdej karty oraz wieloznaczność kodu dla dwóch pierwszych. Importowy walidator struktury `_validate_document` zaakceptował wszystkie trzy struktury; nie uruchamiano importera ani połączenia z DB.

| Dokument / PDF | `product_name` operacyjne | `issue_date` / `revision` | `manufacturer_product_code` | `parties[]` |
|---|---|---|---|---|
| `DOC-001` / 1–3, zestaw | `3M Scotch-Weld DP-490 Black Structural Adhesive Kit` — `FOUND`, dowód s. 1 §1.1 `3M™ Scotch-Weld™ ... Kit` | `2023-07-06` / `13.00` — `FOUND`, s. 1 nagłówek `Data aktualizacji:` / `Numer ... wersji:` | `AMBIGUOUS`, `null`, dowód s. 1 §1.1: `Numery ... identyfikacyjne produktu`, trzy `UU-...` i trzy `710...` | `SUPPLIER`: `3M Poland Sp. z o.o.`, `FOUND`, s. 1 §1.3 `Dane dotyczące dostawcy karty` i `Adres: ... 3M Poland Sp. z o.o. al.` |
| `DOC-002` / 4–26, Part B | `3M Scotch-Weld DP-490 Black Structural Adhesive Part B` — `FOUND`, dowód s. 4 §1.1 `3M™ Scotch-Weld™ ... Part B` | `2023-07-06` / `14.00` — `FOUND`, s. 4 nagłówek | `AMBIGUOUS`, `null`, dowód s. 4 §1.1: dwa `UU-...` i dwa `710...` | `SUPPLIER`: `3M Poland Sp. z o.o.`, `FOUND`, s. 4 §1.3 |
| `DOC-003` / 27–49, Part A | `3M Scotch-Weld DP-490 Black Structural Adhesive Part A` — `FOUND`, dowód s. 27 §1.1 `3M™ Scotch-Weld™ ... Part A` | `2023-04-26` / `14.00` — `FOUND`, s. 27 nagłówek | `NOT_FOUND`, `null`, bez dowodu: w §1.1 brak bloku identyfikatorów | `SUPPLIER`: `3M Poland Sp. z o.o.`, `FOUND`, s. 27 §1.3 |

Pełne, literalne `source_text`, etykieta, sekcja i numer strony są przy każdym `FOUND` i przy obu `AMBIGUOUS` w JSON. Aktualne daty pochodzą z `Data aktualizacji`, a `17/11/2022` i `19/12/2022` po `Zastępuje wersję` nie zostały użyte. `19-3248-2`, `19-2630-2` i `19-2691-4` są ID dokumentów, nie kodami produktu; UFI i nazwy plików też nie tworzą kodu. PDF i Evidence zachowują źródłową rolę `SUPPLIER`; brak automatycznego przypisania `PRODUCT.manufacturer_id`. `safety_profile={}` i `components=[]` w każdym DRAFT, zgodnie z tożsamościowym zakresem PoC.

## Regresja OPEX/SYLGARD i testy negatywne

Wykonano CLI R3 na sześciu oryginalnych PDF: OPEX, B002-01..04 i 3M, każdy z osobnym `*.evidence.json` oraz `*.validation.json` w ignorowanym `tmp/task062r5_final_evidence_20261110/`. Wszystkie sześć przebiegów zakończyło się kodem 0 i `G1/G2/G3=PASS`. OPEX: `OPEX Acrylic Clear Metal Lacquer`, `T82C13`, `2022-11-25`, `8`, oddzielne role `MANUFACTURER_EXPORTER` i `EU_REPRESENTATIVE`. B002-01..04: nazwy `SYLGARD 160/170 ... Part A/B`, właściwe daty `2021-10-28`, `2022-11-01`, `2021-10-26`, `2022-11-07`, rewizje `5.0`, `5.0`, `4.1`, `7.0`, kod `NOT_FOUND`, tylko `SUPPLIER = DOW POLSKA SP.Z O.O.`. W Evidence pozostały literalne `®`/`™`; operacyjne `product_name` ich nie zawiera.

Komenda końcowa: `.\.venv\Scripts\python.exe -B -m pytest tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py tests/unit/test_task062_r5_3m_aliases.py -q -p no:cacheprovider --basetemp tmp/task062r5_verified_pytest_20261110` → **23 passed in 13.74s**. Sprawdzono oryginalne PDF, G1/G2/G3, strony i cytaty, brak mieszania trzech kart, uszkodzone glify, nieaktywny alias, sąsiednie kolumny daty, `Zastępuje wersję`, wersję transportu, copyright, rozróżnienie adresu od dostawcy, UFI/ID dokumentu jako negatywne kody, brak dowodu oraz zamianę roli. Jedna próba umieszczenia dowodu Part A przy Part B powoduje `G2=FAIL`; sztuczne nadanie kodu dokumentu przy `AMBIGUOUS` powoduje `G1=FAIL`.

## R5-1–R5-8

| ID | Wynik i dowód |
|---|---|
| R5-1 | PASS: pierwotne `main`, HEAD/origin wyżej, dziewięć zastanych ACTIVE, niezmieniony SHA i 49 stron źródła; zastane pliki pozostawione. |
| R5-2 | PASS: CLI i test dają dokładnie `DOC-001` 1–3, `DOC-002` 4–26, `DOC-003` 27–49, bez nakładania. |
| R5-3 | PASS: w każdej karcie `FOUND` dla nazwy, bieżącej daty, rewizji i `SUPPLIER`; dowody z własnego §1.1/§1.3 lub nagłówka. |
| R5-4 | PASS: dwa kody `AMBIGUOUS`/`null` z dowodem, Part A `NOT_FOUND`/`null`; brak wyboru ID dokumentu, UFI lub nazwy pliku. |
| R5-5 | PASS: G1/G2/G3 i walidator struktury, wszystkie `PENDING_REVIEW`; brak producenta w Core, brak importu i zależności DB w pipeline. |
| R5-6 | PASS: R4 CANDIDATE → decyzja APPROVED → 4 testy kandydatów PASS → A-010–A-013 ACTIVE → 23 testy PASS; A-001–A-009 bez regresji, C-02 nieaktywowany. |
| R5-7 | PASS: pięć wcześniejszych PDF i 3M w CLI oraz R2/R3/R5 w pytest; przypadki negatywne opisane wyżej. |
| R5-8 | PASS lokalny: trzy logiczne 3M DRAFT i raport walidacji w `tmp/`; zakres plików poniżej, bez integracji aplikacji. |

**Pliki zadania:** zmienione śledzone `config/sds_aliases.json`, `app/infrastructure/filesystem/sds_alias_matcher.py`, `tests/unit/test_task062_r2_aliases.py`; zmienione zastane nieśledzone artefakty R3 `app/infrastructure/filesystem/sds_evidence_pipeline.py` i `tests/unit/test_task062_r3_evidence.py`; nowy `tests/unit/test_task062_r5_3m_aliases.py` i ten raport. Istniejący nieśledzony CLI `scripts/extract_sds_evidence.py` został użyty bez zmian. Diagnostyka JSON i pytest wyłącznie w ignorowanym `tmp/`. `git diff --check` dla śledzonych zmian czysty. Nie zmieniono Core, BDR/TDR, UI, schematu/migracji PostgreSQL, danych operacyjnych ani PDF. Pierwotny etap R5 zakończono bez commita i push; ich kontrolowane wykonanie zostało następnie jawnie zlecone przez Cerberusa.

## Uzupełnienie — kontrolowane utrwalenie, 2026-11-11

Zależność uruchomieniowa: CLI `scripts/extract_sds_evidence.py` importuje pipeline R3 `app/infrastructure/filesystem/sds_evidence_pipeline.py`; pipeline importuje matcher R2/R5 `app/infrastructure/filesystem/sds_alias_matcher.py`, który wczytuje `config/sds_aliases.json`. Biblioteka `pypdf` jest zadeklarowana w śledzonym `pyproject.toml`. Te cztery pliki kodu i katalogu, wraz z istniejącym manifestem zależności, wystarczają do uruchomienia ekstraktora na dostarczonym po pobraniu repozytorium pliku PDF. Testy R2/R3 korzystają z lokalnych PDF OPEX i SYLGARD w `data/sds/Paczki/`; korpus ten nie jest częścią commita i musi być dostępny do odtworzenia pełnej regresji. Test R5 używa już śledzonego PDF 3M w `docs/sds_Work/`.

Do commita wybrano wyłącznie: `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `config/sds_aliases.json`, `scripts/extract_sds_evidence.py`, `tests/unit/test_task062_r2_aliases.py`, `tests/unit/test_task062_r3_evidence.py`, `tests/unit/test_task062_r5_3m_aliases.py` i niniejszy raport. Kontrola składni AST sześciu plików Python i importów trzech modułów uruchomieniowych: PASS. Regresja R2/R3/R5: **23 passed**. `git diff --cached --check`: PASS. SHA commita i potwierdzenie `origin/main` zostaną podane po publikacji w komunikacie końcowym.

**Odstępstwo/ryzyko:** C-02 nie otrzymał aliasu ACTIVE, zgodnie z bezpieczną ścieżką dopuszczoną w R5. `AMBIGUOUS` ma `value=null` i źródłowy dowód roboczy; importer nie może potraktować tego jako kodu. Rozstrzygnięcie jednego kodu oraz producenta wymaga późniejszej decyzji operatora. Bez OCR, Safety/Components i integracji z aplikacją. **STOP po raporcie.**
