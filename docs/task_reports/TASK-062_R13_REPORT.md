# TASK-062-R13 — COMPOUND: implementacja reguł i regresja

**Status:** CLOSED po pozytywnej weryfikacji i publikacji na `main` (SHA końcowego commita w przekazaniu końcowym; commit nie może zawierać własnego SHA). **STOP po R13.**

## Preflight i źródła

Punkt wyjścia: `main = origin/main = ca7138980b5c9a869bd5139a1a3d3884f7067a3d` (także zdalne `ls-remote`), 13 ACTIVE A-001–A-013. Zastane nieśledzone dokumenty R8/R10/R12 i taski R8–R13 pozostawiono poza etapem. Nie zmieniano źródłowych PDF. Trzy oryginały z `data/sds/Paczki/paczka 10 compound/`:

| ID | SHA-256 | Strony | Język |
|---|---|---:|---|
| CMP-01 R 20 | `683117193777c9baf15571ef4c046c7a8628436f99e55074db05533e25fac7e9` | 11 | EN |
| CMP-02 R 35 E | `89e54bed1c751bfa0e299d05fd57b73a05b3a187148256ad631d0852f36daa55` | 11 | PL |
| CMP-03 R 48 | `65449c00dfadc643bda3d60ef4516fd949d0f1b5d5aa8fabc09a470c4ba280c3` | 10 | PL |

## Wynik przed i po

R12: nazwa/kod/wersja `NOT_FOUND`, data CMP-01 `NOT_FOUND`, daty CMP-02/03 `AMBIGUOUS`, brak `parties[]`, język CMP-01 `und`. R13 odczytany z **zapisanych** `tmp/task062r13_compound_final/CMP-0N.evidence.json` i odpowiadających `validation.json`:

| ID | Zakres | Nazwa i cytat §1.1 s. 1 | Kod artykułu i cytat §1.1 s. 1 | Data i rewizja z nagłówka | `parties[]` | Język / bramki |
|---|---|---|---|---|---|---|
| CMP-01 | 1–11 | `Compound R 20`, `Trade name` | `04502000200`, `Article number` | `2021-11-29` z `Revision: 29.11.2021`; `16` z `Version 16 (replaces version 14)` | `SUPPLIER: Rösler Oberflächentechnik GmbH` | `en`; G1/G2/G3 PASS |
| CMP-02 | 1–11 | `Compound R 35 E`, `Nazwa handlowa` | `04502000355`, `Numer artykułu` | `2023-07-07` z `Aktualizacja: 07.07.2023`; `15` z `Wersja 15` | `SUPPLIER: Rösler Oberflächentechnik GmbH`; `DISTRIBUTOR: ZYGMUNT J. GLUCHOWSKI S.C.`; jeden wpis `DISTRIBUTOR AMBIGUOUS/null` | `pl`; G1/G2/G3 PASS |
| CMP-03 | 1–10 | `Compound R 48`, `Nazwa handlowa` | `04502000480`, `Numer artykułu` | `2023-07-07` z `Aktualizacja: 07.07.2023`; `15` z `Wersja 15` | jak CMP-02 | `pl`; G1/G2/G3 PASS |

Każdy `FOUND` ma stronę, sekcję/podsekcję, literalną etykietę i cytat. Kod artykułu jest tekstową propozycją `manufacturer_product_code`, bez zatwierdzenia tożsamości w Core. Daty `Printing date`/`Data druku` oraz poprzednia wersja `14` nie zostały podstawione jako bieżące wartości.

Rola łączona jest w każdym źródle na s. 1 §1.3: `Manufacturer/Supplier:` albo `Producent/Dostawcy:` wraz z `Rösler Oberflächentechnik GmbH` w kolejnym wierszu. Evidence zapisuje wyłącznie `SUPPLIER`, bez automatycznego `MANUFACTURER`. CMP-02/03 s. 1 §1.3 mają `Identyfikacja dystrybutora:` oraz wyraźną nazwę prawną `ZYGMUNT J. GLUCHOWSKI S.C.` — osobny pewny rekord. Osobne bloki `Filip Kapela` i `Lucjan Zalewski` / `Technika Obróbki` są zapisane jako **jeden wpis AMBIGUOUS/null z dwoma źródłowymi cytatami**, bez automatycznego tworzenia firm. `Z. Gluchowski i H. Gluchowska` pozostaje treścią bloku ZYGMUNT, nie nową firmą. Adres ostatniego bloku przechodzi na s. 2 i nie jest automatycznie łączony ani przypisywany do kolejnego SDS. Lista dystrybutorów **nie jest uznana za kompletną**; rozstrzygnięcie wymaga człowieka.

Wszystkie trzy dokumenty mają `PENDING_REVIEW` i `REQUIRES_HUMAN_REVIEW`. G3 zapisuje ostrzeżenie `MANUFACTURER_REQUIRES_HUMAN_REVIEW`, a dla CMP-02/03 także `DISTRIBUTOR_IDENTITY_AMBIGUOUS`. PASS bramek dotyczy zgodności DRAFT z dowodami, nie importu ani zatwierdzenia tożsamości.

## Implementacja, testy i kryteria

Katalog aliasów końcowo **bez zmian: 13 ACTIVE A-001–A-013**. Zatwierdzone etykiety COMPOUND są wąskimi regułami kontekstowymi, ograniczonymi do §1.1, §1.3 lub nagłówka; nie włączono A-014–A-017. G3 dopuszcza odrębne firmy o tej samej roli, ale odrzuca duplikat tej samej pary `(rola, nazwa)`. G2 sprawdza każde `FOUND` i dowody `AMBIGUOUS` względem właściwej strony PDF.

CLI bez zmian: `python -B -m scripts.extract_sds_evidence <oryginalny PDF> --output-dir tmp/task062r13_compound_final --source-id CMP-0N`, N=1…3. **3/3 kod 0** w końcowym przebiegu, zapisane 3 Evidence JSON DRAFT + 3 validation JSON; ponownie odczytane z dysku, SHA i pola zgodne z tabelą. Pierwszy przebieg też zakończył się 3/3 kodem 0 w osobnym katalogu. Bez nadpisywania starszych Evidence. Opcjonalna biblioteka fontTools nie jest zainstalowana; pypdf zgłasza ostrzeżenia dla fontów CMP-02/03, ale cytowane pola są czytelne i walidowane. Bez OCR i instalacji zależności.

Testy: `pytest` dla R2/R3/R5/R7/R9/R11/R13: **65 PASS, 0 FAIL, 0 SKIP** w końcowym przebiegu. Nowy test R13 sprawdza 3 oryginały, granice logicznych SDS i nagłówki, zera w kodzie, UFI/CAS, daty wydruku, wersję zastępowaną, konflikty wartości, role łączone, osoby i duplikaty dystrybutorów, tamper dowodów i detekcję języka. Pierwszy przebieg po dodaniu aliasów wykazał konflikt starego testu katalogu i granicy sekcji (4 FAIL); wycofano dodanie aliasów, zachowano 13 ACTIVE i poprawiono segmentację. Następny przebieg: 64 PASS; po dodatkowym teście konfliktów i powtórzonego nagłówka EN wykonano końcową regresję 65 PASS.

| Kryterium | Dowód | Wynik / brak |
|---|---|---|
| R13-1 | `main`, zdalny SHA, 13 ACTIVE, 3 SHA źródeł, status preflight | PASS; brak |
| R13-2 | zakresy 1–11 / 1–11 / 1–10, test złączonych SDS i nagłówka EN | PASS; brak |
| R13-3 | 3 nazwy i kody jako string, cytaty §1.1, negatywy UFI/CAS i obcego SDS | PASS; brak |
| R13-4 | daty/wersje PL/EN, test wydruku, poprzedniej wersji i konfliktu | PASS; brak |
| R13-5 | 3 `SUPPLIER` z rolą łączoną i regresja R11 | PASS; brak |
| R13-6 | pewny ZYGMUNT, dwa niepewne bloki z cytatami, test duplikatów i G2/G3 | PASS w zakresie bezpiecznego DRAFT; tożsamość niepewnych bloków do decyzji człowieka |
| R13-7 | `en/pl/pl` ze źródła, negatyw mieszanych markerów | PASS; brak |
| R13-8 | 3 CLI i zapisane JSON, 65 testów, G1/G2/G3 PASS, human review | PASS; brak |
| R13-9 | selektywny diff, `git diff --cached --check`, commit i zwykły push `main` | PASS po publikacji; SHA w przekazaniu końcowym |

Diff obejmuje wyłącznie `sds_alias_matcher.py`, `sds_evidence_pipeline.py`, nowy test R13 i niniejszy raport. Bez zmian Core, PostgreSQL, UI, importera, schematu JSON, aliasów i źródłowych PDF. Dane `tmp/` oraz zastane nieśledzone dokumenty nie są utrwalane. **STOP po R13; bez kolejnej paczki i integracji.**
