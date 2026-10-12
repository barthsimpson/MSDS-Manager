# JSON → DB PRECHECK — BATCH-001_CX

**Data:** 2026-10-12  
**Zakres:** jeden Evidence JSON DRAFT; odczyt plików i PostgreSQL przez SQLAlchemy, bez zapisu, COMMIT, kopiowania PDF i zmian Core/schema.

[`BATCH-001_GOLDEN_DECISIONS.md`](BATCH-001_GOLDEN_DECISIONS.md) jest zatwierdzonym źródłem referencyjnym człowieka dla kolejnych batchy. Rozstrzygnięcie wolno przenieść na identyczny przypadek; nowy lub tylko podobny wariant pozostaje `CANDIDATE / HUMAN REVIEW`. Nie zmieniono `SDS-ALIAS-001` ani nie utworzono biblioteki normalizacji runtime.

## Wybrany przypadek i kontrakt

Wybrano [`B001-P001_DOC-001.json`](json/B001-P001_DOC-001.json) (`ALUCYNK`). Raport batcha oznacza go `COMPLETE`; jest to jeden czytelny PDF i jedna logiczna karta SDS. `COMPLETE` opisuje ekstrakcję, a nie zatwierdzenie importu. W JSON `review_status=PENDING_REVIEW`, `validation.status=READY_FOR_HUMAN_REVIEW`, `issues=[]`.

JSON spełnia sprawdzoną minimalną strukturę `SDS-JSON-001` (`schema=SDS-JSON-001`, `schema_version=0.1`): koperta, `source`, jeden `documents[]/DOC-001`, zakres stron 1–12, produkt, metadane, podmiot, walidacja i raport ekstrakcji. Wszystkie cztery pola `FOUND` (nazwa produktu, data, rewizja, nazwa producenta) mają niepuste dowody z s. 1; data `2023-01-23` jest poprawna. `manufacturer_product_code` ma prawidłowe `NOT_FOUND`, `value=null`, pusty dowód. Dwanaście kontroli struktury i spójności: 12/12 PASS. To kontrola względem opisowego kontraktu, nie wykonanie istniejącego walidatora JSON: w `app/` nie ma obsługi `SDS-JSON-001`, `review_status` ani `extraction_report`. Nie weryfikowano treści PDF względem dowodów, bo pliku źródłowego nie odnaleziono.

## Mapowanie na stan aplikacji

| Evidence JSON | Cel w aplikacji | Wynik |
|---|---|---|
| `product.product_name=ALUCYNK` | `PRODUCT.product_name`; przy rewizji wymagany istniejący `product_id` | Nazwa odczytana, ale brak dopasowanego PRODUCT. |
| `product.manufacturer_product_code=NOT_FOUND` | `PRODUCT.manufacturer_product_code` (`NOT NULL`) | Brak kodu usuwa część klucza dopasowania; `AcceptSds` wymaga niepustego kodu. Nie wolno podstawiać kodu z nazwy/UFI. |
| `parties[0].role=MANUFACTURER`, długa nazwa literalna CX80 POLSKA… | `MANUFACTURER.manufacturer_name`, pośrednio `PRODUCT.manufacturer_id` | Ta sama literalna nazwa producenta i rola występują w decyzji B001-Q005; zatwierdzona postać kanoniczna pola to `CX80 POLSKA`, z literalem zachowanym w evidence. Nie oznacza to automatycznego wyboru rekordu DB. |
| `document_metadata.issue_date=2023-01-23`, `revision=2.0` | `SDS.issue_date`, `SDS.revision` | Typy i wartości mogą być jawnie zmapowane. |
| `source.original_filename`, plik PDF | `SDS.original_filename`, `SDS.relative_path` | Oryginalna nazwa jest metadaną; ścieżkę `imported/<UUID>.pdf` nadaje adapter storage dopiero podczas zapisu PDF. |
| `source.file_sha256`, `page_count`, `language`, `document_key`, `page_range`, `evidence`, `validation` | Kontrola przed importem | Brak odpowiadających pól PRODUCT/MANUFACTURER/SDS; nie są zapisywane przez obecny workflow SDS. |
| `safety_profile={}`, `components=[]` | `SAFETY_PROFILE`, `SDS_COMPONENT` | Repozytorium utworzyłoby profil bezpieczeństwa z domyślnym `NO_DATA` w polach statusowych i bez komponentów. Pusty JSON nie stanowi dowodu wartości `NO_DATA` z treści SDS. |

## Odczyt istniejącego stanu

Zapytanie ORM po nazwie zawierającej `ALUCYNK` (bez rozróżniania wielkości liter) zwróciło **0 PRODUCT**. Nie można wskazać istniejącego `product_id` ani jego SDS/CURRENT. Odczyt producentów wykazał dwa różne rekordy `CX80` (`5a43d93166e845d597a296986f2798f7`) i `Cx80` (`a635199aa44944bbbf31cb63808f58d3`), bez rekordu o dokładnej nazwie literalnej z JSON lub kanonicznej `CX80 POLSKA`. Brak jednoznacznego powiązania MANUFACTURER. Brak kodu producenta dodatkowo komplikuje tożsamość produktu, nawet gdyby podobna nazwa wystąpiła w DB.

`SDS_ROOT_PATH` i podkatalog `imported` istnieją. W skonfigurowanym root nie znaleziono PDF o nazwie źródłowej ani pliku z `ALUCYNK` w nazwie; brak go także w katalogu batcha w repozytorium. Nie można zatem sprawdzić SHA-256 z JSON (`a5078d259e7d34ff1b89b54e39925ba0b642873a2a6ab22a21ed8af834c81442`), sygnatury `%PDF-` i dowodów na stronach PDF. Sama dostępność root nie wystarcza do kontrolowanego importu.

## Ścieżka Application → SQLAlchemy → PostgreSQL

Obecne `ImportSds` przyjmuje ręcznie zbudowany `AcceptSdsInput` albo `AddSdsRevisionInput` i bajty PDF; nie przyjmuje Evidence JSON. Waliduje nazwę/rozszerzenie/sygnaturę PDF, zapisuje nową kopię bez nadpisania przez `SdsPdfStorage`, po czym wywołuje istniejący use case. W razie błędu rejestracji usuwa tylko nowy niezarejestrowany plik. Odpowiada to TDR-006 bez zmiany Core/schema, ale wymaga jawnej walidacji i mapowania JSON przed wywołaniem Application.

`AcceptSds` nie nadaje się tu do testowego COMMIT: wymaga kodu producenta, `use_description` i `use_restriction`, których JSON nie podaje. Jego repozytorium może też automatycznie utworzyć MANUFACTURER i PRODUCT, czego zabrania zakres prechecku. `AddSdsRevision` omija te pola, lecz wymaga istniejącego, świadomie wybranego `product_id`; takiego produktu nie znaleziono. Nie ma więc obecnie dopuszczalnej ścieżki do testowego COMMIT dla tego JSON.

Gdyby po spełnieniu warunków użyto `AddSdsRevision` dla istniejącego produktu, repozytorium utworzyłoby jeden `SDS_DOCUMENT` ze statusem `CURRENT`, jeden `SAFETY_PROFILE`, zero `SDS_COMPONENT`, jeden `PRODUCT_HISTORY` i nowy plik `SDS_ROOT_PATH/imported/<UUID>.pdf`. Zmieniłoby `PRODUCT.usage_status` na `PENDING_APPROVAL` i każdy wcześniejszy SDS `CURRENT` tego produktu na `ARCHIVED`. Nie utworzyłoby ani nie zmieniło MANUFACTURER, nie zmieniłoby tożsamości produktu i nie utworzyłoby decyzji BHP. Liczby wcześniejszych SDS nie można ustalić bez produktu docelowego. Jest zatem realne ryzyko zmiany `CURRENT/ARCHIVED`; workflow nie ma wariantu zapisu nowego SDS bez tego lifecycle.

## Warunki przed jednym testowym COMMIT

1. Człowiek zatwierdzi całą kartę i mapowanie pól z dowodami, zmieniając status logicznego dokumentu z `PENDING_REVIEW` na `APPROVED`; potwierdzi też, jak traktować pusty `safety_profile`, aby nie zapisać niedowiedzionych `NO_DATA` jako danych SDS.
2. Będzie istniał jednoznacznie wybrany PRODUCT z potwierdzonym `product_id`. Dziś go nie ma; ewentualne utworzenie produktu wymaga osobnego, jawnie autoryzowanego workflow, poza tym precheckiem. Człowiek rozstrzygnie brak kodu producenta i powiązanie tego PRODUCT z właściwym istniejącym MANUFACTURER (`CX80`/`Cx80` lub innym); bez automatycznego tworzenia producenta.
3. Oryginalny PDF zostanie udostępniony do kontrolowanego importu. Przed zapisem trzeba sprawdzić zgodność SHA-256, sygnaturę PDF, nazwę oraz dowody i zakres stron względem tego JSON; storage musi móc zapisać nową kopię w `SDS_ROOT_PATH/imported/` zgodnie z TDR-006.
4. Dla wybranego `product_id` trzeba odczytać istniejące SDS i wykluczyć niezamierzoną ponowną rejestrację tej samej karty; człowiek musi jawnie zaakceptować skutki `CURRENT → ARCHIVED`, nowy `CURRENT`, `PRODUCT.usage_status=PENDING_APPROVAL` i wpis historii.
5. Trzeba wykonać kontrolowaną walidację `SDS-JSON-001` i jawne mapowanie zatwierdzonych wartości do `AddSdsRevisionInput` oraz wejścia `ImportSds`, bez bezpośredniego SQL, zmian Core/schema ani automatycznej biblioteki normalizacji. Następnie osobna autoryzacja jednego testowego COMMIT.

BLOCKED
