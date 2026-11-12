# TASK-062-R13 — COMPOUND: ekstrakcja PL/EN, kody artykułów, role podmiotów i regresja

**Status:** READY / AUTHORIZED — decyzja Architekta 2026-11-12  
**TASK MODE:** PATCH — ograniczona implementacja ekstraktora i walidacji Evidence + regresja  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repozytorium:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`; bez nowych gałęzi i worktree.  
**Punkt odniesienia:** R12 ACCEPTED diagnostycznie; ostatni potwierdzony commit R11: `ca7138980b5c9a869bd5139a1a3d3884f7067a3d`. Faktyczny stan `HEAD`, `origin/main` i plików zweryfikuj w preflight — nie zakładaj braku nowszych zmian.

## 1. Źródła i wiążąca decyzja

1. `docs/task_reports/TASK-062_R12_REPORT.md` — nadrzędne źródło **konkretnych** cytatów, trzech SHA-256, układów dokumentów i macierzy **R12-C01–C10**.
2. `docs/tasks/TASK-062_R12_COMPOUND_DIAGNOSTYKA_ALIASOW.md` oraz raport R11 — kontekst diagnostyki i wcześniejsze zachowanie ekstraktora.
3. Przed zmianą odczytaj lokalne `AGENTS.md`, obowiązujące GOV-001/GOV-002, TDR-012, SDS-JSON-001, SDS-ALIAS-001, BDR-005 i CORE-001 w obszarach faktycznie potrzebnych; w razie sprzeczności zastosuj STOP. Nie zgaduj nieodczytanej treści dokumentów.
4. **Architekt zatwierdził R12-C01–C10** z następującą semantyką:
   - `Article number` / `Numer artykułu` w §1.1 → **kandydat** `manufacturer_product_code` (tekst z zerami wiodącymi, z cytatem), bez automatycznego zatwierdzania tożsamości w Core;
   - angielski `Revision: DD.MM.YYYY` w kontekście nagłówka Compound → bieżąca data `issue_date` (ISO); `Version 16 (replaces version 14)` → tekstowa `revision="16"`, **nie `14`**;
   - wspólna etykieta `Manufacturer/Supplier:` / `Producent/Dostawcy:` → **`SUPPLIER`** ze źródłową etykietą zachowaną w evidence, **nie** automatyczne `MANUFACTURER`;
   - dopuszczalne **wiele** odrębnie potwierdzonych rekordów `DISTRIBUTOR` w `parties[]`; osób kontaktowych i niejednoznacznych bloków **nie** przekształcać automatycznie w firmy.
5. Reguła nadrzędna: **automatyzacja proponuje, człowiek zatwierdza, Core pozostaje chroniony**. G1/G2/G3 PASS dotyczy spójności DRAFT, nie zatwierdza produktu, producenta ani importu.

## 2. Cel

Na **trzech oryginalnych PDF paczki 10 COMPOUND** uzyskać poprawne Evidence JSON DRAFT: logiczny zakres SDS, nazwę produktu, jawny kod artykułu, właściwą datę aktualizacji, numer bieżącej wersji, bezpieczne role podmiotów oraz język źródła. Zachować poprawne dotychczasowe zachowania paczek OPEX/SYLGARD/3M/WEICON/LOCTITE/KCH i aktualny kontrakt Evidence.

## 3. Zakres techniczny i wyłączenia

**Dozwolone:** minimalne korekty `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py` (segmentacja, kontekst, mapowanie pól i wąska walidacja G2/G3), ewentualnie kontrolowana zmiana katalogu aliasów zgodna z jego obowiązującym procesem, nowy `tests/unit/test_task062_r13_compound.py` i raport R13. CLI utrzymuj bez zmiany, chyba że rzeczywiście niezbędna do celu i wykażesz przyczynę.

**Nie zmieniaj:** Core, modelu lub schematu bazy PostgreSQL, importera, UI, kontraktu SDS-JSON-001, źródłowych PDF, mechanizmu ręcznego zatwierdzania. Bez OCR, LLM, instalacji nieuzgodnionych zależności, regeneracji całego korpusu i niepowiązanych poprawek. Nie twórz reguł zależnych od nazwy pliku, marki, twardych kodów lub indeksów stron. Dane `tmp/` pozostają poza commitem.

**Alias catalog:** punkt wyjścia według R12: **13 ACTIVE A-001–A-013**. Preferuj istniejące aliasy i dopasowania kontekstowe; nowe literalne aliasy tylko, jeśli potrzebne i dopuszczone przez proces SDS-ALIAS-001. Zapisz liczbę i identyfikatory końcowe. Zatwierdzenie kandydata R12 nie oznacza nieograniczonego dodawania aliasów ACTIVE.

## 4. Implementacja zatwierdzonych R12-C01–C10

### C01 — granice i §1

Rozpoznaj `* SECTION 1:` (z wariantami odstępów) dla angielskiego SDS, obok obecnego `SEKCJA 1:` / `SEKCJA 1.`. Rozpoznaj podsekcje `- 1.1` i `- 1.3` w PL/EN, ale tylko we własnym logicznym SDS. Nie myl z `SECTION 10`, `SECTION 16`, powtarzanym nagłówkiem, numeracją stron ani `1.1` występującym w treści. Na oryginałach zakresy mają pozostać: CMP-01 1–11, CMP-02 1–11, CMP-03 1–10; test złączenia dwóch odrębnych kart ma wykazać faktyczną segmentację, nie przypadkowy zakres od początku PDF.

### C02 — nazwa §1.1 PL/EN

`Trade name:` → `Compound R 20`; `Nazwa handlowa:` → `Compound R 35 E` / `Compound R 48`. `FOUND` tylko z własnego §1.1, ze stroną, sekcją i cytatem. Bez pobierania tytułów powtarzanych na stronach 2+, nazw PDF, UFI, zastosowań ani danych kontaktowych.

### C03 — kod artykułu jako propozycja kodu produktu

W §1.1 rozpoznaj `Article number:` oraz `Numer artykułu:` i zapisz **dokładnie jako string**: CMP-01 `04502000200`, CMP-02 `04502000355`, CMP-03 `04502000480`. Pole `manufacturer_product_code` ma mieć `FOUND` z bezpośrednim evidence, bez automatycznej rejestracji lub potwierdzania producenta. Nigdy nie podstawiaj UFI, CAS, EINECS, identyfikatora SDS ani nazwy PDF. Sprzeczne wartości w obrębie jednego SDS → `AMBIGUOUS/null`.

### C04–C05 — sklejony nagłówek PL

Dla CMP-02/03 `Aktualizacja: 07.07.2023Wersja 15` rozdziel datę i wersję wyłącznie według jawnych etykiet. Wyniki: `issue_date="2023-07-07"`, `revision="15"`. Data `Data druku:` nie może stanowić źródła `issue_date`, nawet gdy identyczna. Weryfikuj poprawność kalendarzową, nie pobieraj stopki ani nazw PDF. Zgodne powtórzenia na stronach tej samej karty nie są konfliktem; sprzeczne bieżące daty lub wersje dają `AMBIGUOUS/null`.

### C06–C07 — sklejony nagłówek EN

Dla CMP-01 `Revision: 29.11.2021Version 16 (replaces version 14)` wyodrębnij `issue_date="2021-11-29"` i `revision="16"`. `Printing date` nie zastępuje bieżącej daty, a `replaces version 14` nie zastępuje bieżącej rewizji. Ogranicz regułę `Revision:` będącego datą do jednoznacznego kontekstu; nie zepsuj starszych układów, w których `Revision` jest numerem rewizji. Zachowuj evidence łącznie z etykietą i położeniem.

### C08 — wspólna rola w §1.3

Dla CMP-01 `Manufacturer/Supplier:` i CMP-02/03 `Producent/Dostawcy:` zapisz kandydata `SUPPLIER` z nazwą `Rösler Oberflächentechnik GmbH`. Dosłowny tekst wspólnej roli, źródłowa nazwa i miejsce (§1.3, strona) muszą pozostać w dowodzie. Nie wyciągaj z samej łączonej etykiety `MANUFACTURER`. Nie zapisuj telefonu/adresu/etykiety roli jako nazwy firmy. Nie zmieniaj poprawnego mapowania pojedynczego `Producent` → `MANUFACTURER` z R11.

### C09 — wielu dystrybutorów bez zgadywania granic

W CMP-02/03 rozpoznaj `Identyfikacja dystrybutora:` i **wiele** `DISTRIBUTOR` tylko dla bloków, w których nazwa podmiotu i granice rekordu dają się jednoznacznie wykazać cytatem i położeniem. Przykładowo `ZYGMUNT J. GLUCHOWSKI S.C.` jest jawnie wskazaną nazwą; następne wpisy `Z. Gluchowski i H. Gluchowska`, `Filip Kapela`, `Lucjan Zalewski`, `Technika Obróbki` wymagają rozróżnienia osoby kontaktowej, elementu nazwy firmy i niezależnego podmiotu. Nie przypisuj automatycznie każdej linii odrębnej firmie, nie ograniczaj się arbitralnie do pierwszego dystrybutora, nie łącz adresu przechodzącego na s. 2 z kolejnym SDS. Dla niejednoznacznych jednostek zachowaj cytat w diagnostyce/raporcie i status bezpiecznej niejednoznaczności zgodny z kontraktem; nie oznaczaj w pełni rozpoznanej listy, gdy pozostały nierozstrzygnięte bloki.

**Walidator G3:** R12 wskazuje odrzucanie powtarzanej roli. Dostosuj go **tylko jeśli** obowiązujący SDS-JSON-001 dopuszcza wiele `parties[]` z tą samą rolą. Odróżnij dwie firmy z rolą `DISTRIBUTOR` od zduplikowanego rekordu tej samej firmy; G2 musi weryfikować każdy `FOUND` względem własnego cytatu, a G3 zgodność roli i brak fałszywych podmiotów. Jeżeli kontrakt nie umożliwia bezpiecznego odwzorowania częściowej/niejednoznacznej listy, **STOP dla tej części i raport o konflikcie**, bez samodzielnej zmiany schema/Core. Niezależne kandydaty nadal wykonaj.

### C10 — język

CMP-01 `source.language="en"` na podstawie spójnych angielskich markerów `Safety data sheet`/`SECTION 1` (nie nazwy pliku ani jednego słowa). CMP-02/03 pozostają `pl`. Nie wymuszaj `en` dla dokumentów mieszanych/niejednoznacznych — bezpiecznie `und`.

## 5. Oczekiwane wyniki trzech PDF

| ID | Strony | `product_name` | `manufacturer_product_code` | `issue_date` | `revision` | Podmiot z roli łączonej | Język |
|---|---:|---|---|---|---|---|---|
| CMP-01 | 1–11 | `Compound R 20` | `04502000200` | `2021-11-29` | `16` | `SUPPLIER: Rösler Oberflächentechnik GmbH` | `en` |
| CMP-02 | 1–11 | `Compound R 35 E` | `04502000355` | `2023-07-07` | `15` | `SUPPLIER: Rösler Oberflächentechnik GmbH` | `pl` |
| CMP-03 | 1–10 | `Compound R 48` | `04502000480` | `2023-07-07` | `15` | `SUPPLIER: Rösler Oberflächentechnik GmbH` | `pl` |

Dodatkowo CMP-02/03 mają rozpoznawać **jednoznacznych** `DISTRIBUTOR` bez tworzenia firm z nazw osób. Liczbę pewnych podmiotów ustalaj ze źródła — nie zakładaj jej w kodzie. Dla każdego `FOUND` wymagaj cytatu, strony, sekcji i prawidłowej roli. Wszystkie DRAFT: `PENDING_REVIEW` i `REQUIRES_HUMAN_REVIEW`. Nie oznaczaj użytkownika ani producenta jako zatwierdzonych.

Źródła bez zmian: `data/sds/Paczki/paczka 10 compound/`, trzy różne SHA podane w raporcie R12. Użyj CLI z osobnymi identyfikatorami CMP-01…03 i **świeżym ignorowanym katalogiem** `tmp/task062r13_compound/`; nie nadpisuj istniejących Evidence.

## 6. Testy dopasowane do ryzyka

- Dodaj skupione testy `tests/unit/test_task062_r13_compound.py`: rzeczywiste trzy PDF i cytaty/strony/sekcje, segmentacja syntetycznie złączonych SDS PL/EN, wariant punktowanego `- 1.1`/`- 1.3`.
- Negatywy: błędne daty; `Printing date` i `Data druku` różne od aktualizacji; `Version 14` jako wersja zastępowana; konflikt bieżących `Revision`/`Wersja`; `Revision` jako tekstowy numer z wcześniejszych formatów; UFI/CAS zamiast numeru artykułu; numer artykułu z obcego SDS; nazwa firmy będąca etykietą roli; wielokrotnie ta sama rola u **różnych** dystrybutorów vs duplikat **tej samej** firmy; osoba/adres/email jako fałszywy dystrybutor; przejście bloku na s. 2 i granica sąsiedniego SDS; rozpoznanie `en` wyłącznie z jednego przypadkowego wyrazu.
- Regresja **dotkniętych funkcji** i wcześniejszych pakietów: `test_task062_r2_aliases.py`, `test_task062_r3_evidence.py`, `test_task062_r5_3m_aliases.py`, `test_task062_r7_weicon.py`, `test_task062_r9_loctite.py`, `test_task062_r11_kch.py` plus R13. Bez pełnego przypadkowego testowania całej aplikacji.
- Ponownie uruchom niezmieniony CLI na trzech oryginałach, odczytaj **rzeczywiście zapisane** Evidence i validation JSON z dysku. Nie wystarczy `pytest PASS` ani samo `G1/G2/G3 PASS` — ręcznie porównaj krytyczne wartości z PDF i wykaż w raporcie.

## 7. Kryteria akceptacji

| ID | Wymaganie | Dowód |
|---|---|---|
| **R13-1** | Preflight: istniejący `main`, up-to-date repo, 13 ACTIVE w punkcie wyjścia, nienaruszone SHA trzech źródeł i zastane dokumenty. | `git status`, katalog aliasów, SHA i strony. |
| **R13-2** | Poprawna segmentacja EN/PL, rozpoznanie `- 1.1`/`- 1.3`, trzy poprawne zakresy oraz test złączonych SDS. | 3 oryginały + test negatywny. |
| **R13-3** | Trzy prawidłowe nazwy i kody artykułów jako tekst z zerami, z evidence; wykluczenie UFI/CAS i obcego SDS. | 3 Evidence + focused tests. |
| **R13-4** | Daty i wersje PL/EN jak tabela; oddzielenie daty wydruku i wersji poprzedniej; brak regresji dawnych `Revision`. | 3 Evidence + negatywy i regresja. |
| **R13-5** | Trzy poprawne `SUPPLIER` Rösler z dosłowną rolą łączoną; bez zmiany jednoznacznego `Producent`/`Dystrybutor` z R11. | §1.3 s. 1, test G2/G3 i regresja. |
| **R13-6** | Bezpieczna obsługa wielu `DISTRIBUTOR`: każdy pewny wpis z osobnym dowodem, niepewne osoby/bloki bez fałszywego `FOUND`; zachowanie kontraktu. | Testy duplikatów, ról, częściowej niejednoznaczności, źródłowy rozbiór CMP-02/03 i jawne ograniczenia. |
| **R13-7** | `source.language=en` dla CMP-01 oraz `pl` dla CMP-02/03; brak regresji detekcji języka. | 3 Evidence + negatywy. |
| **R13-8** | 3 rzeczywiste CLI → 3 DRAFT + 3 validation; status human review; testy R13 i proporcjonalna regresja R2/R3/R5/R7/R9/R11. | Komendy, PASS/FAIL/SKIP, cytaty, bramki i stan na dysku. |
| **R13-9** | Ograniczony diff, raport, bez Core/DB/UI/importera/schema, bez niedozwolonych danych w Git; poprawna publikacja albo jawna blokada. | `git diff`, lista plików, Git SHA/status. |

## 8. Raport, Git, STOP

Zapisz `docs/task_reports/TASK-062_R13_REPORT.md` z tabelą R13-1…R13-9 (wymaganie → dowód → wynik → brak), porównaniem **przed/po** na każdym CMP, szczegółową listą dowiedzionych `parties[]` i **osobno** wpisów pozostawionych jako niejednoznaczne, wartościami ze źródła i zapisanych JSON, stanem 13 ACTIVE/nowych aliasów, uruchomionymi testami, plikami diff, odchyleniami i ograniczeniami. Nie deklaruj kompletności wielu dystrybutorów bez dowodów.

Po pozytywnej weryfikacji i braku STOP: **selektywny commit i zwykły push `origin/main`**, tylko kod ekstraktora/wąska walidacja, test R13, raport R13 i niezbędne zatwierdzone aliasy (jeżeli faktycznie dodano). Przed commitem `git diff --cached --stat` i `git diff --cached --check`; **bez `git add .`**. Nie dodawaj zastanych nieśledzonych TASK/REPORT z R8–R12, plików PDF, plików w `tmp/`, sekretów ani niepowiązanych zmian. Nie force-pushuj i nie resetuj repo. Po publikacji podaj SHA oraz synchronizację `HEAD=origin/main`; jeśli commit/push nie nastąpi, zaznacz to otwarcie.

**STOP** przy konflikcie ze schematem/enum Evidence, niedającym się jednoznacznie rozdzielić bloku osoby i firmy, potrzebie zmiany Core/DB/importera/kontraktu JSON, nierozwiązanej regresji lub niezgodnym evidence. Zatrzymaj tylko część zależną od blokady, dokończ niezależne elementy i zaraportuj, co wymaga decyzji. Żadnego automatycznego rozpoczęcia R14 ani integracji aplikacyjnej.
