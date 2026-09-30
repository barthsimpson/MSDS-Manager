# TDR-006 — Kontrolowany zapis / import SDS do SDS_ROOT_PATH

**Projekt:** MSDS Manager  
**Id dokumentu:** TDR-006  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-09-30  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Decyzja biznesowa nadrzędna:** BDR-007 v1.0-approved  

---

## 1. Cel decyzji technicznej

TDR-006 definiuje techniczny mechanizm realizacji:

```text
DOC-01 — dodawanie SDS z komputera / kontrolowany import PDF
```

zgodnie z zatwierdzonym modelem:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

TDR-006 rozstrzyga w szczególności:

- sposób przyjęcia pliku z UI,
- walidację PDF,
- adapter filesystem,
- sposób bezkolizyjnego zapisu,
- ochronę przed overwrite,
- bezpieczeństwo ścieżek,
- kolejność filesystem ↔ PostgreSQL,
- rollback / compensation,
- cleanup po błędzie,
- granice zmian w Application / Infrastructure / UI,
- minimalny zakres testów integracyjnych.

---

## 2. Kontekst obowiązujący

TDR-006 należy czytać łącznie z:

1. `BDR-007_Kontrolowany_import_SDS_v1.0-approved`,
2. `BDR-003 — Dokument SDS, aktualność i wersjonowanie`,
3. `CORE-001_MSDS_Manager_v1.2-approved`,
4. `TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja`,
5. `TDR-003 — struktura warstw aplikacji`,
6. `GOV-001 v1.0-approved`,
7. `GOV-002 v1.0-approved`.

BDR-007 zmienia wcześniejszą zasadę całkowitego `read-only` dla `SDS_ROOT_PATH` wyłącznie w zakresie kontrolowanego zapisu nowej kopii podczas importu.

Po skutecznej rejestracji dokument pozostaje chroniony i read-only z punktu widzenia standardowego workflow aplikacji.

---

## 3. Zasada architektoniczna

Import jest orkiestracją warstw:

```text
Streamlit
→ Application use case
→ filesystem port
→ filesystem adapter
→ istniejący mechanizm rejestracji SDS / repository
→ PostgreSQL
```

Streamlit nie wykonuje bezpośrednio:

- zapisu pliku do `SDS_ROOT_PATH`,
- operacji na SQLAlchemy / PostgreSQL,
- ustalania ścieżki technicznej,
- logiki overwrite / cleanup.

Logika importu należy do Application, a operacje plikowe do Infrastructure.

Domain nie zna:

- Streamlit,
- `SDS_ROOT_PATH`,
- `pathlib`,
- lokalnych ścieżek Windows,
- mechanizmu zapisu pliku.

---

## 4. Wejście z UI

W formularzu rejestracji pierwszego SDS oraz nowej rewizji SDS użytkownik może wskazać plik z komputera przez standardowy mechanizm uploadu Streamlit.

UI przyjmuje wyłącznie dokument SDS w formacie:

```text
.pdf
```

Wybranie pliku w UI nie oznacza jeszcze jego trwałego zapisu w `SDS_ROOT_PATH`.

Do momentu jawnego zatwierdzenia formularza plik pozostaje wyłącznie wejściem bieżącej operacji.

Trwały zapis następuje dopiero w kontrolowanym use case po akcji użytkownika zatwierdzającej rejestrację SDS.

---

## 5. Kontrakt wejściowy Application

Application powinien otrzymać co najmniej:

```text
product_id
original_filename
pdf_bytes / binary stream
issue_date
revision
pozostałe istniejące dane formularza SDS
```

`original_filename` jest metadaną biznesową dokumentu.

Nie jest używane jako docelowa ścieżka zapisu i nie może sterować lokalizacją w filesystem.

Pełna lokalna ścieżka źródłowa komputera użytkownika nie jest zapisywana w bazie.

---

## 6. Walidacja pliku

Przed trwałym zapisem wymagane jest co najmniej:

```text
1. wejście istnieje,
2. plik nie jest pusty,
3. rozszerzenie nazwy wejściowej = .pdf (case-insensitive),
4. zawartość posiada podstawową sygnaturę PDF (%PDF-),
5. zapis docelowy pozostaje wewnątrz SDS_ROOT_PATH.
```

Walidacja typu nie może opierać się wyłącznie na wartości MIME przekazanej przez przeglądarkę.

TDR-006 nie wprowadza:

- pełnej walidacji struktury PDF,
- parsera treści SDS,
- kontroli zgodności językowej dokumentu przez parser,
- antywirusa,
- deduplikacji po hash,
- OCR.

Jeżeli w przyszłości będą wymagane, wymagają osobnej decyzji.

---

## 7. Adapter filesystem

W `app/infrastructure/filesystem/` powinien istnieć albo zostać rozszerzony dedykowany adapter odpowiedzialny za kontrolowany zapis SDS.

Application korzysta z niego przez port / kontrakt, a nie przez bezpośrednie operacje `open()` / `Path` w use case.

Minimalna odpowiedzialność adaptera:

```text
validate destination root
store_new_pdf(...)
remove_unregistered_file(...)
resolve_existing_path(...)   # jeśli już istnieje odpowiednik do odczytu
```

Nazwy symboli mogą zostać dopasowane do istniejącej konwencji repozytorium.

Nie tworzyć generycznego DMS ani wspólnego frameworka storage bez potrzeby.

---

## 8. Struktura docelowej ścieżki

Nowo importowane dokumenty są zapisywane w kontrolowanym podkatalogu:

```text
SDS_ROOT_PATH/imported/
```

Docelowa nazwa techniczna nie pochodzi bezpośrednio z `original_filename`.

Przyjmujemy format:

```text
<storage_uuid>.pdf
```

Przykład:

```text
SDS_ROOT_PATH = D:\MSDS\SDS
relative_path = imported\550e8400-e29b-41d4-a716-446655440000.pdf
original_filename = 30470_Idrolin_Sherwin_PL.pdf
```

Baza przechowuje:

```text
original_filename
relative_path
```

Nie przechowuje pełnej ścieżki lokalnej jako podstawowego odwołania.

`storage_uuid` jest technicznym identyfikatorem nazwy pliku i nie zastępuje `sds_id`.

---

## 9. Ochrona przed kolizją i overwrite

Zapis nowego pliku musi być wykonany w trybie wykluczającym nadpisanie istniejącego pliku.

Dozwolony mechanizm:

```text
generate UUID
→ target = SDS_ROOT_PATH/imported/<uuid>.pdf
→ create exclusive
```

Jeżeli target istnieje:

```text
nie nadpisuj
→ wygeneruj nowy UUID
→ ponów ograniczoną liczbę prób
```

Jeżeli nie można uzyskać bezkolizyjnej ścieżki:

```text
STOP / ERROR
```

Nie wolno używać operacji, której normalne zachowanie może cicho zastąpić istniejący plik.

---

## 10. Bezpieczeństwo ścieżek

Ścieżka docelowa jest budowana wyłącznie przez aplikację z:

```text
SDS_ROOT_PATH
+ stały podkatalog imported
+ wygenerowana nazwa techniczna
```

`original_filename` nie może być częścią ścieżki sterującą katalogami.

W szczególności wejście użytkownika nie może umożliwiać:

```text
../
..\
ścieżki absolutnej
UNC path
obejścia SDS_ROOT_PATH
```

Adapter przed zapisem powinien zweryfikować, że rozstrzygnięta ścieżka docelowa znajduje się wewnątrz rozstrzygniętego `SDS_ROOT_PATH`.

Brak poprawnego lub dostępnego `SDS_ROOT_PATH` oznacza przerwanie operacji.

---

## 11. Kolejność operacji filesystem ↔ database

Filesystem i PostgreSQL nie tworzą wspólnej transakcji ACID.

Dlatego DOC-01 stosuje jawny mechanizm kompensacyjny.

Sekwencja po zatwierdzeniu formularza:

```text
1. zweryfikuj PRODUCT i dane wejściowe
2. zweryfikuj PDF
3. wyznacz bezpieczną relative_path
4. zapisz NOWY plik PDF metodą create-exclusive
5. potwierdź, że plik istnieje w SDS_ROOT_PATH
6. rozpocznij / kontynuuj transakcję rejestracji SDS
7. utwórz rekord SDS z original_filename + relative_path
8. wykonaj istniejący lifecycle CURRENT / ARCHIVED
9. COMMIT PostgreSQL
10. po COMMIT dokument staje się chronionym źródłem read-only
```

Jeżeli zapis pliku nie powiedzie się:

```text
nie twórz rekordu SDS
```

Jeżeli operacja DB nie powiedzie się po utworzeniu nowego pliku:

```text
ROLLBACK DB
→ compensation: usuń wyłącznie plik utworzony przez tę niezakończoną operację
→ zgłoś błąd
```

Usunięcie w ramach compensation jest dozwolone wyłącznie dlatego, że SDS nie został skutecznie zarejestrowany i plik nie osiągnął stanu chronionego dokumentu źródłowego.

---

## 12. Reguła ochrony po COMMIT

Po skutecznym COMMIT rekordu SDS:

```text
relative_path wskazuje istniejący PDF
→ plik = REGISTERED SOURCE
→ standardowy workflow aplikacji nie może go usuwać, nadpisywać, przenosić ani modyfikować
```

Mechanizm compensation nie może usuwać pliku po skutecznym COMMIT.

Brak pliku wykryty później pozostaje przypadkiem `MISSING` zgodnie z BDR-003 i nie usuwa rekordu z historii.

---

## 13. Awaria i niepełny cleanup

Jeżeli DB rollback się powiedzie, ale cleanup nowo utworzonego pliku nie powiedzie się:

```text
operacja = FAILED
nie raportuj sukcesu
zwróć jednoznaczny błąd techniczny
wskaż relative_path osieroconego pliku do ręcznego cleanupu
```

Nie twórz automatycznego mechanizmu masowego czyszczenia katalogu ani background janitora w ramach DOC-01.

Przypadek ten powinien być możliwy do wykrycia i przetestowania.

---

## 14. Brak automatycznej deduplikacji

DOC-01 nie wykonuje automatycznej deduplikacji plików po:

- nazwie,
- hash,
- rozmiarze,
- dacie,
- rewizji,
- treści.

Ponowne wskazanie tego samego PDF może utworzyć nową kopię techniczną wyłącznie wtedy, gdy istniejący workflow rejestracji SDS dopuszcza utworzenie nowego rekordu.

Konflikty biznesowe dotyczące tego, czy dokument jest właściwą nową rewizją SDS, nadal rozstrzyga istniejący workflow i użytkownik.

---

## 15. Lifecycle SDS

TDR-006 nie zmienia:

```text
CURRENT
ARCHIVED
```

Import pliku nie ustala samodzielnie statusu dokumentu.

Zmiana:

```text
poprzedni CURRENT → ARCHIVED
nowy SDS → CURRENT
```

pozostaje odpowiedzialnością istniejącego mechanizmu rejestracji nowego SDS i musi zachować dotychczasową spójność transakcyjną danych PostgreSQL.

Nie ustalaj CURRENT na podstawie:

- nazwy pliku,
- numeru rewizji,
- daty SDS.

---

## 16. Zmiany w UI

DOC-01 może zmienić istniejące formularze:

```text
Dodaj pierwszy SDS
Dodaj nową rewizję SDS
```

w taki sposób, aby użytkownik:

```text
wybrał PDF z komputera
→ uzupełnił / potwierdził istniejące dane SDS
→ zatwierdził zapis
```

Pole ręcznego wpisywania `relative_path`, jeżeli obecnie jest eksponowane użytkownikowi w tym workflow, powinno zostać zastąpione kontrolowanym uploadem.

`relative_path` staje się wynikiem technicznym importu, nie daną wpisywaną ręcznie przez operatora dla nowego uploadu.

TDR-006 nie implementuje UI-11 otwierania CURRENT SDS ani UI-14 podglądu dowodu BHP.

---

## 17. Zmiany w Application

Application powinien orkiestracyjnie zapewniać:

```text
walidację wejścia
→ kontrolowany zapis nowego PDF
→ rejestrację SDS
→ compensation po błędzie DB
```

Preferowane jest wykorzystanie istniejącego use case rejestracji SDS i rozszerzenie go minimalnym kontraktem storage, jeżeli pozwala to zachować czytelne odpowiedzialności.

Jeżeli istniejący use case nie może zostać bezpiecznie rozszerzony bez mieszania odpowiedzialności, dopuszczalny jest osobny use case importujący, który deleguje do istniejącej logiki rejestracji SDS.

Codex nie może przy okazji przepisywać całego workflow SDS.

---

## 18. Zmiany w Infrastructure

Dozwolone są minimalne zmiany w:

```text
app/infrastructure/filesystem/
app/infrastructure/config/
app/infrastructure/db/        # tylko istniejące repozytoria / transaction wiring, jeśli konieczne
```

Nie oczekuje się:

```text
zmiany schema PostgreSQL
nowej migracji Alembic
nowych tabel
blob storage
zewnętrznego object storage
```

`SDS_ROOT_PATH` pozostaje konfiguracją środowiska zgodnie z TDR-002.

---

## 19. Granice Core

TDR-006 nie zmienia Core.

W szczególności bez zmian pozostają:

- PRODUCT jako centralny obiekt,
- SDS jako osobny obiekt 1:N względem PRODUCT,
- `sds_id`,
- `original_filename`,
- `relative_path`,
- `issue_date`,
- `revision`,
- `CURRENT / ARCHIVED`,
- wymaganie istnienia fizycznego PDF,
- historia SDS,
- relacja SDS → BHP_DECISION.

---

## 20. Poza zakresem

TDR-006 nie obejmuje:

- UI-11 — otwierania / pobierania CURRENT SDS,
- UI-14 / DOC-02 — dowodu BHP,
- parsera Stage 2,
- OCR,
- automatycznej analizy SDS,
- automatycznej decyzji BHP,
- REACH,
- skanowania antywirusowego,
- hash-based deduplication,
- przechowywania PDF w PostgreSQL,
- chmury / S3 / object storage,
- generycznego DMS,
- fizycznego DELETE zarejestrowanego SDS,
- zmian schema,
- zmian lifecycle SDS.

---

## 21. Wymagane testy implementacyjne DOC-01

Task implementacyjny powinien potwierdzić co najmniej:

1. upload poprawnego PDF → plik zapisany w `SDS_ROOT_PATH/imported/`,
2. baza przechowuje poprawny `original_filename`,
3. baza przechowuje `relative_path`, nie pełną ścieżkę lokalną,
4. zapis używa technicznej bezkolizyjnej nazwy,
5. istniejący plik nie może zostać nadpisany,
6. plik nie-PDF jest odrzucany,
7. pusty plik jest odrzucany,
8. `.pdf` bez sygnatury `%PDF-` jest odrzucany,
9. nazwa wejściowa zawierająca elementy ścieżki nie pozwala wyjść poza `SDS_ROOT_PATH`,
10. błąd filesystem → brak rekordu SDS,
11. błąd DB po zapisie pliku → rollback DB + usunięcie nowo utworzonego niezarejestrowanego pliku,
12. błąd cleanup → brak sukcesu + jednoznaczne zgłoszenie orphan path,
13. skuteczny COMMIT → plik pozostaje i nie jest usuwany przez compensation,
14. rejestracja pierwszego SDS działa,
15. rejestracja kolejnej rewizji zachowuje CURRENT / ARCHIVED,
16. `revision = NULL` nadal jest poprawne,
17. brak zmian schema / Alembic,
18. brak zmian parsera / Core.

Testy filesystem powinny używać izolowanego katalogu tymczasowego.

Testy DB powinny być izolowane od danych operatora.

---

## 22. Ryzyka i kontrole

### RYZYKO 1 — overwrite istniejącego PDF

Kontrola:

```text
techniczna nazwa UUID
+ create-exclusive
+ brak operacji replace
```

### RYZYKO 2 — path traversal

Kontrola:

```text
original_filename tylko jako metadata
+ target generowany przez aplikację
+ resolved target musi należeć do SDS_ROOT_PATH
```

### RYZYKO 3 — plik zapisany, DB nie zapisany

Kontrola:

```text
DB rollback
+ compensation delete wyłącznie nowego niezarejestrowanego pliku
```

### RYZYKO 4 — DB wskazuje brakujący plik

Kontrola:

```text
filesystem write musi zakończyć się sukcesem przed COMMIT SDS
```

### RYZYKO 5 — scope creep do DMS / parsera

Kontrola:

```text
STOP
→ osobna decyzja
```

---

## 23. Expected change surface dla Tasku DOC-01

Oczekiwane obszary:

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
app/infrastructure/config/     # tylko jeśli konieczne
app/infrastructure/db/         # tylko minimalne transaction wiring, jeśli konieczne
tests/
```

Chronione przed nieuzasadnioną zmianą:

```text
app/domain/
migrations/
Core docs
parser SDS
BHP workflow
UNIT_OF_MEASURE
```

---

## 24. Charakter przyszłego Tasku

Implementacja DOC-01 dotyka:

```text
UI
+ Application
+ filesystem Infrastructure
+ istniejącej transakcji rejestracji SDS
```

Dlatego przyszły Task powinien mieć:

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
REPORT: SHORT / STANDARD INTEGRATION
```

Pełna regresja i checkpoint LEVEL 3 nie są wymagane wyłącznie dla tego pojedynczego Tasku, chyba że DOC-01 zostanie włączony do zamknięcia większego Sprintu.

---

## 25. STOP conditions dla implementacji

Codex powinien zatrzymać Task DOC-01, jeżeli:

1. realizacja wymaga zmiany schema,
2. realizacja wymaga zmiany Core,
3. istniejący lifecycle SDS nie pozwala zachować atomowości `CURRENT / ARCHIVED`,
4. implementacja wymaga przechowywania PDF w PostgreSQL,
5. nie można zagwarantować braku overwrite,
6. nie można ograniczyć zapisu do `SDS_ROOT_PATH`,
7. compensation wymagałaby usuwania pliku już skutecznie zarejestrowanego,
8. konieczne byłoby wdrożenie parsera / deduplikacji / DMS poza zakresem,
9. wymagana jest nowa zależność bez uzasadnienia i zatwierdzenia,
10. istniejące kontrakty repozytorium SDS są sprzeczne z BDR-007 / TDR-006.

Codex nie zgaduje rozwiązania poza tym TDR.

---

## 26. Kryterium techniczne DOC-01

Po implementacji system powinien realizować:

```text
wybór PDF z komputera
→ walidacja
→ jawne zatwierdzenie przez użytkownika
→ bezkolizyjny WRITE-ONCE do SDS_ROOT_PATH/imported
→ rejestracja SDS w PostgreSQL
→ zachowanie CURRENT / ARCHIVED
→ READ-ONLY po COMMIT
```

bez ręcznego kopiowania PDF przez operatora przed rejestracją.

---

## 27. Authorization boundary

TDR-006 po zatwierdzeniu będzie decyzją techniczną dla DOC-01.

Sam TDR:

```text
może stanowić authoritative context dla Tasku
```

ale:

```text
nie jest poleceniem wykonania implementacji
```

Implementacja wymaga osobnego, zamkniętego Tasku i jawnej autoryzacji Architekta Operacyjnego zgodnie z GOV-001.

---

## 28. Status dokumentu

Aktualny status:

```text
TDR-006
VERSION: 1.0-approved
STATUS: Approved
```

Architekt Operacyjny zatwierdził TDR-006 jako obowiązującą decyzję techniczną dla DOC-01. Wersja 1.0-approved zastępuje wersję 0.1-draft jako aktualne źródło decyzji technicznej.

---

## 29. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-30 | Draft | Pierwszy model techniczny kontrolowanego importu SDS: upload PDF, bezpieczny storage UUID, path safety, no-overwrite, filesystem→DB z compensation, izolowane testy |
| 1.0-approved | 2026-09-30 | Approved | Architekt Operacyjny zatwierdził TDR-006 bez zmian merytorycznych; dokument staje się obowiązującą decyzją techniczną dla DOC-01 |
