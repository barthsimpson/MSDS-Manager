# TASK-050 — analiza wpływu opcjonalnego kodu produktu producenta

**Tryb:** ANALYSIS / ARCHITECTURE IMPACT  
**Data:** 2026-10-12  
**Zakres wykonany:** przegląd wskazanych decyzji, kodu, migracji, testów i metadanych PostgreSQL przez SQLAlchemy Inspector. Bez zmian implementacyjnych, migracji, zapisu DB i PDF.

## A. CURRENT STATE

| Warstwa | Utrwalona reguła / skutek |
|---|---|
| Decyzje | Najnowszy `CORE-001 v1.5`, §3.2 i §19 pkt 2–3: `product_name + manufacturer_product_code + manufacturer_id` tworzą tożsamość; nowy kod oznacza nowy PRODUCT, a pola tożsamości nie są zwykłymi polami edycji. `BDR-003` wymaga PRODUCT i PDF przed SDS; kod wymienia wśród danych do ekstrakcji, lecz nie ustanawia osobnego warunku obecności kodu. `BDR-005` wymaga akceptacji całego draftu. `SDS-JSON-001` dopuszcza `manufacturer_product_code=NOT_FOUND/null` na etapie Evidence JSON. |
| Domain / DTO | `Product.manufacturer_product_code: str` w `app/domain/models/catalog.py`; `ProductListItem`, `ProductDetails`, `UpdateProductIdentityInput`, `SupervisoryProductRow`, `BhpDecisionProduct` także używają `str`. `SdsDraft`/`AcceptSdsInput` dopuszczają `str | None` na poziomie typu, lecz walidacja zapisu odrzuca brak. `AddSdsRevisionInput` używa `product_id` i nie wymaga kodu. |
| ORM / PostgreSQL | `ProductModel.manufacturer_product_code` jest `nullable=False` (`app/infrastructure/db/models/catalog.py:31`); migracja początkowa `fdaac4f8756e_initial_core_schema.py:43` tworzy kolumnę `NOT NULL`. Odczyt bieżącej bazy przez SQLAlchemy Inspector potwierdził `nullable=False`. Nie ma unique constraint ani indeksu na `products` (Inspector: `[]`/`[]`); migracja i ORM nie definiują unikalności trójki tożsamości. `manufacturers.manufacturer_name` też nie ma unikalności w ORM. |
| Application / repository | `AcceptSds._validate` wymaga niepustych `manufacturer_product_code`, `product_name`, `manufacturer_name`, `use_description`, `use_restriction` i pliku. `SqlAlchemySdsAcceptanceRepository.accept` rozwiązuje producenta po dokładnej nazwie, tworzy go przy braku; produkt wyszukuje po dokładnej trójce i pobiera pierwszy wynik przez `scalar()`, a przy braku tworzy PRODUCT. Nie zgłasza wieloznaczności, gdy kilka produktów ma tę samą trójkę. Przy LINK aktualizuje `use_description`/`use_restriction`. `_persist_sds` tworzy SDS i profil, archiwizuje wcześniejszy CURRENT, ustawia `PRODUCT.usage_status=PENDING_APPROVAL` oraz dopisuje `PRODUCT_HISTORY`. `ImportSds` obsługuje PDF i deleguje do istniejącej rejestracji. |
| Późniejsze uzupełnienie kodu | `UpdateProductIdentity` wymaga niepustego kodu wejściowego i pozwala zmienić nazwę, kod oraz producenta w istniejącym `product_id`; repozytorium wykonuje UPDATE bez wpisu historii tożsamości. Formularz `product_registry.py` udostępnia tę edycję. Technicznie potrafiłby zapisać nowy kod do tego samego rekordu po dopuszczeniu NULL. `PATCH-007_Edycja_podstawowych_danych_produktu.md` autoryzował korektę błędnie wpisanych pól bez zmiany `product_id`, a test `test_patch007_product_identity.py` utrwala ją; kod nie odróżnia korekty błędu od nowej tożsamości przewidzianej przez Core. |
| UI / odczyty | `add_sds.py:138` oznacza „Kod producenta *”; opis użycia i ograniczenia też mają `*`. Rejestr, szczegóły, rewizja, widok nadzorczy i BHP wyświetlają kod jako tekst. `ListSupervisoryProducts` sortuje po kodzie jako `str`; mieszanka `None`/`str` przy tej samej nazwie produktu spowoduje błąd porównania w Pythonie. DTO i formularz edycji wymagają obsługi `None`/prezentacji „brak kodu”. Repozytorium nadzorcze sortuje także po kodzie w PostgreSQL. |
| Testy | `test_orm_metadata.py` wprost wymaga `NOT NULL`; `test_update_product_identity.py` odrzuca pusty kod; testy akceptacji, importu, nadzoru i UI stosują wyłącznie niepuste kody. Wymagają aktualizacji i przypadków `NULL`/późniejszego uzupełnienia. |

Obecny `PRODUCT_HISTORY` zawiera status i dane administracyjne, bez pól tożsamości. Kod jest używany do wyszukiwania w `_resolve_product` i sortowania, lecz brak DB unique constraint oznacza, że nie ma bazy egzekwującej deduplikację tożsamości. `NULL` nie może zostać potraktowane jako pusty napis, wildcard ani sztuczna wartość zastępcza.

## B. CORE / DECISION CONFLICT

**Rewizja Core jest wymagana: YES.** Nowa zatwierdzona zasada `manufacturer_product_code=NULL` oraz późniejsze `NULL → znany kod` w **tym samym** PRODUCT koliduje z literalnym „nowy kod = nowy PRODUCT” w `CORE-001 v1.5` §3.2 i §19 pkt 2–3. Minimalna rewizja musi określić: kod może być nieznany (`NULL`) przy utworzeniu; pierwsze uzupełnienie z `NULL` jest dopełnieniem informacji o tym samym `product_id`; trzeba rozstrzygnąć regułę dla zmiany kodu już znanego oraz relację tej operacji do edycji nazwy/producenta. Bez tej decyzji nie wolno implementować wyjątku w Application ani migracji.

`BDR-003`, `BDR-005`, `BDR-007` i `TDR-006` nie wymagają zmiany zasad PDF ani lifecycle z powodu opcjonalnego kodu. Wymagają jednak spójnego zapisu odpowiedniej rewizji decyzji biznesowej/Core przed implementacją. `CORE-001` podaje BDR-002 v1.1 jako rodowód reguły PRODUCT; dostępny plik BDR-002 v1.2 jest uzupełnieniem o cykl `USAGE_LOCATION` i nie podaje nowej reguły kodu. Osobna rozbieżność wymaga rozstrzygnięcia: `PATCH-007` dopuszcza poprawienie błędnej tożsamości w tym samym rekordzie, a Core mówi, że nowa nazwa/kod/producent oznacza nowy PRODUCT. Obecny kod nie kontroluje granicy między korektą błędu a rzeczywistą zmianą tożsamości.

`use_description` i `use_restriction` są w Core polami PRODUCT i administracyjnie edytowalnymi (§3.3), ale Core nie ustanawia wprost, że ich brak ma blokować samo rozpoznanie tożsamości. Ich `NOT NULL` w DB i niepustość w `AcceptSds`/UI to obecny kontrakt implementacji. Nie wynika z nowej decyzji o kodzie, że pola te mają stać się opcjonalne.

## C. ACCEPTSDS REUSE

**YES WITH CHANGES.** Istniejący `AcceptSds` oraz `SqlAlchemySdsAcceptanceRepository` mogą być podstawą docelowej rejestracji CREATE/LINK i zachowania transakcji, historii oraz CURRENT/ARCHIVED. Nie mogą obecnie bezpośrednio przyjąć Evidence JSON: brak walidatora/mapperu JSON, kontrolowanego DRY RUN, jawnego wyniku tożsamości i obsługi `NULL` w walidacji/repozytorium/DB. Obecny `accept` sam tworzy MANUFACTURER/PRODUCT przy braku dokładnego dopasowania, a `_resolve_product` bierze pierwszy rekord zamiast zatrzymać wieloznaczność.

Minimalny kierunek późniejszej zmiany: osobna warstwa wejściowa waliduje JSON i dowody, wyznacza kandydatów CREATE/LINK/HUMAN REVIEW bez zapisu, po decyzji człowieka przekazuje **jawnie wskazaną** tożsamość do dotychczasowej rejestracji SDS. Ścieżka LINK może korzystać z istniejącego `AddSdsRevision` i wspólnego `_persist_sds`; ścieżka CREATE z dostosowanego `AcceptSds`. Nie ma potrzeby drugiego mechanizmu tworzenia PRODUCT/SDS. Repozytorium musi odróżnić `NULL` przez `IS NULL`, wykrywać wiele kandydatów i nie podejmować cichej decyzji na podstawie pierwszego rekordu. To propozycja zakresu technicznego, nie autoryzacja implementacji.

## D. ALUCYNK WALKTHROUGH — wyłącznie DATA MAPPING

| Krok | Wynik bez zapisu |
|---|---|
| JSON | `B001-P001_DOC-001.json`: `ALUCYNK`, `manufacturer_product_code=NOT_FOUND/null`, producent w sekcji 1.3, `issue_date=2023-01-23`, `revision=2.0`, dowody pól; cały dokument nadal `PENDING_REVIEW`. |
| PRODUCT | Precheck ORM: brak produktu o nazwie zawierającej `ALUCYNK`. Wynik to **CREATE CANDIDATE**, a nie błąd ekstrakcji. Brak kodu nie blokuje tego etapu i nie uprawnia do zastąpienia go nazwą, UFI, CAS lub nazwą pliku. |
| MANUFACTURER | Literal producenta odpowiada zatwierdzonemu przykładowi w B001-Q005; referencyjna nazwa kanoniczna to `CX80 POLSKA`. W DB nie było dokładnego rekordu o tej nazwie, są oddzielne `CX80` i `Cx80`. Wynik: **HUMAN REVIEW** wyboru istniejącego manufacturer_id albo **CREATE CANDIDATE** dla kanonicznego producenta; bez automatycznego scalenia lub założenia, że któryś istniejący rekord jest tożsamy. |
| Pola gotowe / brakujące | Nazwa, data, rewizja i dowody są gotowe do oceny. `use_description` i `use_restriction` nie występują w tym JSON; obecny `AcceptSds` wymaga ich ręcznego uzupełnienia. `safety_profile={}` i `components=[]`; obecne repozytorium wypełniłoby statusy bezpieczeństwa `NO_DATA`, mimo że sekcji bezpieczeństwa nie zebrano w tym JSON. Cała karta i te wartości wymagają zatwierdzenia przed Core. |
| Wynik | **CREATE CANDIDATE + MANUFACTURER HUMAN REVIEW**. Nie wykonano CREATE, LINK, zmiany statusów ani COMMIT. |

Zasada docelowego resolvera: jednoznacznie ustalony PRODUCT/MANUFACTURER → proponowany LINK; brak → CREATE CANDIDATE; więcej niż jeden lub niepewność → HUMAN REVIEW. Gdy kod jest `NULL`, sama podobna nazwa nie uzasadnia LINK; dokładne kryterium jednoznaczności wymaga decyzji Architekta. Golden Decisions wolno użyć tylko dla identycznego rozstrzygniętego przypadku; wariant podobny pozostaje CANDIDATE/HUMAN REVIEW.

## E. PDF BOUNDARY

**Etap A — JSON DATA MAPPING / DRY RUN:** walidacja koperty, stanów i dowodów, mapowanie pól, odczyt PRODUCT/MANUFACTURER/SDS i raport CREATE/LINK/HUMAN REVIEW nie wymagają ponownego dostępu do oryginalnego PDF. Brak PDF dla ALUCYNK w poprzednim prechecku nie blokuje tej analizy. Bez PDF nie można natomiast ponownie potwierdzić SHA-256 i treści cytowanych dowodów.

**Etap B — FULL SDS REGISTRATION / COMMIT:** `BDR-003` §5, `BDR-007` §9 i `TDR-006` §11 wymagają istniejącego właściwego PRODUCT, zwalidowanego PDF, nowej kopii w `SDS_ROOT_PATH` oraz jawnego zatwierdzenia przed rekordem SDS. `ImportSds` wykonuje kontrolowany zapis pliku i kompensację; rejestracja zmienia poprzedni CURRENT na ARCHIVED oraz nowy SDS na CURRENT. Sam Evidence JSON nie zastępuje PDF ani decyzji człowieka. Status `COMPLETE` ekstrakcji nie jest `APPROVED` w `SDS-JSON-001`.

## F. REQUIRED DECISIONS BEFORE IMPLEMENTATION

1. Architekt musi zatwierdzić rewizję reguły tożsamości w Core/odpowiedniej decyzji biznesowej: `NULL` przy CREATE, pierwsze uzupełnienie kodu w tym samym PRODUCT oraz zachowanie przy późniejszej zmianie kodu znanego. Należy równocześnie rozstrzygnąć granicę między korektą błędnych danych z PATCH-007 a utworzeniem nowego PRODUCT przy rzeczywistej zmianie nazwy/kodu/producenta.
2. Architekt musi określić kryterium jednoznacznego LINK przy `manufacturer_product_code=NULL` i procedurę HUMAN REVIEW dla niejednoznacznych/zdublowanych produktów oraz powiązania kanonicznego producenta z istniejącym `manufacturer_id`. Brak DB unique constraint oznacza, że sam odczyt pierwszego wyniku nie jest regułą tożsamości.
3. Architekt musi zdecydować, czy `use_description` i `use_restriction` mają pozostać wymagane i być uzupełniane przez człowieka przed CREATE, czy ma się zmienić ich kontrakt. Zmiana wymagania wymaga osobnej analizy Core/schema; TASK-050 jej nie przyjmuje automatycznie.
4. Architekt musi określić, czy i na jakich warunkach można rejestrować SDS z sekcji 1 JSON bez zatwierdzonych danych bezpieczeństwa; obecny zapis domyślnego `NO_DATA` nie może być utożsamiony z odczytem treści SDS. Indywidualna akceptacja całej karty pozostaje obowiązkowa zgodnie z BDR-005/SDS-JSON-001.

Dla konkretnego ALUCYNK dodatkowo człowiek musi podjąć decyzję operacyjną o MANUFACTURER CREATE/LINK i zatwierdzić dane draftu; to nie jest decyzja automatycznego mappera.

## G. EXPECTED CHANGE SURFACE — przyszły, osobno autoryzowany Task

- Decyzje: rewizja `CORE-001` i właściwej BDR reguły PRODUCT identity; ewentualne doprecyzowanie TDR importera JSON. Bez zmian `SDS-ALIAS-001`, Golden Decisions ani lifecycle SDS.
- Domain/DTO: `app/domain/models/catalog.py`, `app/application/dto/{products,sds,supervisory,bhp_decisions}.py` oraz inne DTO z kodem jako `str`.
- Application: `accept_sds.py`, `update_product_identity.py`, resolver/mapper Evidence JSON i DRY RUN; `add_sds_revision.py` oraz `import_sds.py` tylko w zakresie przekazania jawnej decyzji i zachowania istniejącej orkiestracji.
- Infrastructure: `app/infrastructure/db/models/catalog.py`, `repositories/sds_acceptance.py`, `repositories/product.py`, read models/sortowanie nadzorcze, nowa migracja zmieniająca nullability. `product_history` nie przechowuje kodu; zakres audytu późniejszego uzupełnienia trzeba uwzględnić w projekcie, bez automatycznej zmiany schema w tym Tasku.
- UI: `app/presentation/streamlit/add_sds.py`, `product_registry.py` i prezentacje kodu w widokach nadzorczym/BHP; `composition.py` dla kontrolowanego wejścia JSON, jeśli zostanie zatwierdzone.
- Testy przyszłej implementacji: ORM/schema NULL, AcceptSds CREATE z NULL i bez placeholdera, późniejsze `NULL→kod` przy niezmiennym `product_id` i zachowanych SDS/BHP/powiązaniach, odmowa niezatwierdzonej zmiany znanego kodu, wieloznaczny LINK, producent `CX80`/`Cx80`, sortowanie/rendering NULL, DRY RUN bez zapisu oraz dotychczasowa transakcja PDF/SDS/lifecycle. Celowane pliki m.in. `tests/unit/test_{orm_metadata,accept_sds,update_product_identity,task026_supervisory}.py`, `tests/integration/test_{task019_accept_sds,task036_import_postgresql,patch007_product_identity}.py`, testy UI.

## H. MIGRATION IMPACT

**schema migration required: YES.** Powód: bieżące PostgreSQL i ORM mają `products.manufacturer_product_code NOT NULL`; zapis rzeczywistego `NULL` wymaga zmiany kolumny na nullable przez osobną migrację Alembic po zatwierdzeniu Core. Nie ma istniejącego unikalnego constraintu lub indeksu zależnego od kodu do przebudowy. Samo `DROP NOT NULL` nie ustanawia jednak jednoznacznego CREATE/LINK; reguły identyfikacji i obsługa równoczesnych prób CREATE wymagają projektu Application/DB. Istniejące niepuste kody mogą pozostać bez backfillu; żadnej migracji nie uruchomiono.

## I. RECOMMENDATION

**READY_FOR_ARCHITECTURAL_DECISION.** Wpływ jest ustalony, a `AcceptSds` nadaje się do wykorzystania po zatwierdzeniu czterech decyzji z sekcji F. Implementacja pozostaje wstrzymana. Raport nie zmienia poprzedniego `JSON_DB_PRECHECK_REPORT.md`; doprecyzowuje, że jego `BLOCKED` odnosi się do kontrolowanego COMMIT, podczas gdy mapowanie/dry-run ALUCYNK jest możliwe bez PDF. Zgodnie z TASK-050: STOP po raporcie.
