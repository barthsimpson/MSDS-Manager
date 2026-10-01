# TDR-007 — Kontrolowany import i dostęp do DECISION_EVIDENCE

**Projekt:** MSDS Manager  
**Dokument:** TDR-007  
**Wersja:** 1.1-approved  
**Status:** Approved  
**Data:** 2026-10-01  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Podstawa biznesowa:** BDR-008 v1.0-approved  
**Podstawa Core:** CORE-001 v1.3-approved

---

## 1. Cel decyzji technicznej

TDR-007 definiuje techniczny mechanizm realizacji:

```text
UI-14 / DOC-02
— kontrolowany wybór, import i późniejszy dostęp do DECISION_EVIDENCE
```

zgodnie z zatwierdzonym kierunkiem:

```text
NO DEFAULT EVIDENCE
+
CONTROLLED WRITE-ONCE IMPORT
+
LATER READ / DOWNLOAD ACCESS
```

TDR-007 rozstrzyga:

- neutralny stan wyboru evidence,
- wybór istniejącego pliku,
- upload nowego pliku z komputera,
- walidację typów plików,
- adapter filesystem dla `BHP_EVIDENCE_ROOT_PATH`,
- bezkolizyjny zapis i ochronę przed overwrite,
- bezpieczeństwo ścieżek,
- kolejność filesystem ↔ PostgreSQL,
- rollback / compensation,
- dostęp do zarejestrowanego evidence,
- obsługę `MISSING`,
- granice zmian w UI / Application / Infrastructure,
- wymagane testy implementacyjne.

---

## 2. Kontekst obowiązujący

TDR-007 należy czytać łącznie z:

1. `BDR-008_Kontrolowany_dowod_BHP_v1.0-approved`,
2. `BDR-004 — Decyzja BHP, jej zakres i historia`,
3. `CORE-001_MSDS_Manager_v1.3-approved`,
4. `TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja`,
5. `TDR-003 — struktura warstw aplikacji`,
6. `TDR-006_Kontrolowany_import_SDS_v1.0-approved` — jako wzorzec techniczny storage, nie jako automatycznie kopiowana implementacja,
7. `GOV-001 v1.0-approved`,
8. `GOV-002 v1.0-approved`.

Obowiązujące pozostają:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
evidence wymagane
APPROVED / REJECTED
CURRENT / SUPERSEDED
```

TDR-007 nie zmienia modelu historii decyzji BHP.

---

## 3. Zasada architektoniczna

Obsługa evidence jest orkiestracją warstw:

```text
Streamlit
→ Application use case
→ evidence filesystem port
→ evidence filesystem adapter
→ istniejący mechanizm BHP_DECISION / DECISION_EVIDENCE
→ PostgreSQL
```

Streamlit nie wykonuje bezpośrednio:

- operacji zapisu do `BHP_EVIDENCE_ROOT_PATH`,
- operacji SQL / ORM,
- ustalania technicznej ścieżki docelowej,
- logiki overwrite,
- compensation,
- interpretacji poprawności biznesowej pliku.

Domain nie zna:

- Streamlit,
- lokalnych ścieżek Windows,
- `pathlib`,
- fizycznego mechanizmu storage.

---

## 4. Neutralny stan wyboru evidence

Pole:

```text
Dowód decyzji
```

musi rozpoczynać się stanem neutralnym:

```text
BRAK WYBORU
```

Technicznie:

```text
selected_evidence = None
```

Nie wolno:

```text
select first available file by default
```

Przycisk zapisu decyzji nie może skutecznie zatwierdzić rekordu bez jawnie wskazanego evidence.

---

## 5. Dwa tryby wejścia

UI udostępnia dwa jawne tryby:

```text
A. Wybierz istniejący dowód
B. Dodaj nowy dowód z komputera
```

Tryby są rozłączne dla pojedynczej operacji zapisu decyzji.

### A. Istniejący dowód

Użytkownik wybiera plik już obecny w `BHP_EVIDENCE_ROOT_PATH`.

Lista:
- nie wybiera automatycznie pierwszego elementu,
- pokazuje nazwę użytkową / względną identyfikację wystarczającą do świadomego wyboru,
- nie pokazuje technicznych UUID jako podstawowej etykiety,
- sygnalizuje plik niedostępny, jeśli rekord / ścieżka wskazuje stan `MISSING`.

### B. Nowy dowód

Użytkownik wskazuje plik lokalny przez upload Streamlit.

Wybranie pliku:
- nie zapisuje go od razu do repozytorium,
- przechowuje wejście w pamięci bieżącej operacji,
- trwały zapis następuje dopiero po zatwierdzeniu decyzji.

---

## 6. Dozwolone formaty

Dozwolone rozszerzenia:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Walidacja rozszerzenia jest case-insensitive.

TDR-007 nie wprowadza:
- parsera MSG,
- walidacji semantycznej treści,
- OCR,
- automatycznej klasyfikacji dokumentu,
- antywirusa.

---

## 7. Walidacja nowego pliku

Przed trwałym zapisem wymagane jest co najmniej:

```text
1. wejście istnieje,
2. plik nie jest pusty,
3. rozszerzenie należy do allowlist,
4. docelowa ścieżka pozostaje wewnątrz BHP_EVIDENCE_ROOT_PATH.
```

Dodatkowo, tam gdzie jest to tanie i deterministyczne, adapter może zastosować lekką walidację sygnatury dla znanych typów binarnych.

Nie wolno polegać wyłącznie na MIME przekazanym przez przeglądarkę.

Brak pełnej walidacji strukturalnej pliku nie jest błędem tego etapu.

---

## 8. Filesystem port / adapter

W `app/infrastructure/filesystem/` powinien istnieć albo zostać rozszerzony dedykowany adapter dla evidence.

Application korzysta z niego przez port / kontrakt.

Minimalne odpowiedzialności:

```text
list_existing_evidence(...)
store_new_evidence(...)
remove_unregistered_evidence(...)
resolve_existing_evidence_path(...)
read_existing_evidence(...)
check_availability(...)
```

Nazwy symboli mogą zostać dopasowane do konwencji repozytorium.

Nie tworzyć generycznego DMS ani wspólnego storage frameworka bez potrzeby.

---

## 9. Docelowa ścieżka nowego evidence

Nowe pliki są zapisywane w kontrolowanym podkatalogu:

```text
BHP_EVIDENCE_ROOT_PATH/imported/
```

Nazwa techniczna:

```text
<storage_uuid>.<normalized_extension>
```

Przykład:

```text
imported/550e8400-e29b-41d4-a716-446655440000.msg
```

`original_filename` pozostaje metadaną źródłową użytkownika.

Techniczna nazwa storage:
- nie pochodzi bezpośrednio z `original_filename`,
- nie zastępuje `evidence_id`,
- nie steruje znaczeniem biznesowym dowodu.

`original_filename` jest obowiązkową metadaną źródłową `DECISION_EVIDENCE` dla nowo rejestrowanych dowodów.

Obecny model persistence nie posiada tego pola. Dlatego TDR-007 v1.1 zatwierdza techniczną zmianę fundamentu przed wznowieniem UI-14 / DOC-02:

```text
DECISION_EVIDENCE
+ original_filename
```

Zmiana wymaga:

```text
Domain contract
+ ORM
+ PostgreSQL schema
+ Alembic migration
+ repository / mapping
+ focused tests
```

`original_filename` nie steruje ścieżką storage i nie zastępuje `relative_path` ani `evidence_id`.

Implementacja tej zmiany ma zostać wykonana osobnym Taskiem foundation przed wznowieniem TASK-037.

---

## 10. No-overwrite

Zapis nowego pliku musi używać trybu wykluczającego nadpisanie:

```text
generate UUID
→ target
→ create-exclusive
```

Jeżeli target istnieje:

```text
nie nadpisuj
→ wygeneruj nowy UUID
→ ponów ograniczoną liczbę prób
```

Brak możliwości uzyskania bezkolizyjnej ścieżki:

```text
ERROR / STOP
```

Zakazane:

```text
replace
silent overwrite
delete-then-write
```

---

## 11. Bezpieczeństwo ścieżek

Docelowa ścieżka nowego evidence powstaje wyłącznie z:

```text
BHP_EVIDENCE_ROOT_PATH
+ stały katalog imported
+ storage_uuid
+ kontrolowane rozszerzenie
```

`original_filename` nie może sterować strukturą katalogów.

Należy zablokować:

```text
../
..\
absolute path
UNC path
path traversal
wyjście poza BHP_EVIDENCE_ROOT_PATH
```

Resolved target musi należeć do resolved root.

---

## 12. Kolejność operacji — nowy evidence

Filesystem i PostgreSQL nie tworzą wspólnej transakcji ACID.

Obowiązuje jawna compensation.

Sekwencja:

```text
1. zweryfikuj PRODUCT / CURRENT SDS / dane decyzji
2. zweryfikuj nowy plik evidence
3. wyznacz bezpieczny relative_path
4. zapisz NOWY plik create-exclusive
5. potwierdź istnienie pliku
6. rozpocznij / kontynuuj transakcję decyzji BHP
7. utwórz DECISION_EVIDENCE
8. utwórz / zatwierdź BHP_DECISION
9. zachowaj CURRENT / SUPERSEDED
10. COMMIT PostgreSQL
11. po COMMIT plik staje się REGISTERED SOURCE
```

Jeżeli filesystem write się nie powiedzie:

```text
brak BHP_DECISION
brak DECISION_EVIDENCE
```

Jeżeli DB fail po utworzeniu pliku:

```text
ROLLBACK DB
→ usuń wyłącznie plik utworzony przez tę niezakończoną operację
→ zgłoś błąd
```

Po COMMIT compensation nie może usuwać zarejestrowanego evidence.

---

## 13. Kolejność operacji — istniejący evidence

Dla istniejącego pliku:

```text
1. użytkownik jawnie wybiera plik
2. Application potwierdza dostępność
3. Application potwierdza, że ścieżka należy do BHP_EVIDENCE_ROOT_PATH
4. tworzony jest / przypisywany DECISION_EVIDENCE
5. tworzona jest BHP_DECISION
6. COMMIT
```

Nie kopiuj istniejącego pliku ponownie tylko dlatego, że został wybrany.

Nie wolno automatycznie wybierać innego pliku, jeśli wskazany jest `MISSING`.

---

## 14. Cleanup failure

Jeżeli DB rollback się powiedzie, ale usunięcie nowego niezarejestrowanego pliku się nie powiedzie:

```text
operacja = FAILED
nie raportuj sukcesu
zwróć jednoznaczny błąd
wskaż orphan relative_path
```

Nie implementować background cleanup / janitora.

---

## 15. Ochrona po COMMIT

Po skutecznym COMMIT:

```text
evidence = REGISTERED SOURCE
```

Standardowy workflow nie może:

- nadpisywać pliku,
- usuwać pliku,
- modyfikować zawartości,
- przenosić pliku,
- podmieniać go innym plikiem „w miejscu”.

Korekta decyzji tworzy nowy rekord decyzji zgodnie z BDR-004.

---

## 16. Dostęp do evidence po rejestracji

UI-14 ma umożliwić późniejszy dostęp do dowodu powiązanego z decyzją.

Minimalny techniczny zakres:

```text
PDF
→ download / otwarcie przez przeglądarkę

JPG / JPEG / PNG
→ inline preview i/lub download

MSG
→ download; otwarcie zależy od systemu użytkownika
```

Nie implementować parsera MSG.

Nie implementować konwersji MSG → PDF.

---

## 17. MISSING

Jeżeli rekord evidence istnieje, ale fizycznego pliku nie można odnaleźć:

```text
availability = MISSING
```

UI:
- pokazuje czytelny stan niedostępności,
- nie usuwa rekordu,
- nie podstawia innego pliku,
- nie blokuje odczytu historii decyzji jako takiej.

Brak pliku nie może automatycznie zmieniać `APPROVED / REJECTED`.

---

## 18. Zmiany w UI

Dopuszczalne zmiany w ekranie `Decyzja BHP`:

```text
Dowód decyzji
[ brak wyboru ]

Tryb:
( ) istniejący plik
( ) dodaj z komputera
```

Dla istniejącego:
- neutralny placeholder,
- jawny wybór.

Dla uploadu:
- `file_uploader`,
- bez trwałego zapisu przed Submit.

Po istniejącej decyzji / w historii:
- przycisk / kontrolka otwarcia lub pobrania evidence,
- stan `MISSING`, jeśli plik niedostępny.

Nie przebudowywać całej nawigacji BHP.

---

## 19. Zmiany w Application

Application ma zapewniać co najmniej:

```text
list existing evidence
select existing evidence
validate new evidence
store new evidence
register decision + evidence
compensate on failure
read/download evidence
check availability
```

Preferowane jest:
- zachowanie istniejących use case'ów BHP,
- dodanie małych use case'ów / portów dla evidence,
- brak przenoszenia logiki filesystem do UI.

---

## 20. Zmiany w Infrastructure

Dozwolone minimalne zmiany:

```text
app/infrastructure/filesystem/
app/infrastructure/config/     # tylko jeśli potrzebne
app/infrastructure/db/         # istniejące repo / transaction wiring
app/presentation/streamlit/
app/application/
tests/
```

TDR-007 v1.1 rozdziela implementację na dwa kroki:

```text
KROK A — FOUNDATION
Domain + ORM + schema + Alembic + mapping
→ dodanie DECISION_EVIDENCE.original_filename

KROK B — UI-14 / DOC-02
UI + Application + filesystem + read/download
→ wznowienie TASK-037
```

Dla Kroku A oczekuje się kontrolowanej zmiany schema i jednej migracji Alembic.

Nie oczekuje się:

```text
new table
blob storage
cloud storage
zmiany relacji 1:1
zmiany lifecycle BHP
```

Zakres migracji ma być minimalny: dodanie jednej kolumny `original_filename` i niezbędne dostosowanie kontraktów.

---

## 21. Granice Core

TDR-007 v1.1 wymaga minimalnej rewizji Core w zakresie metadanych `DECISION_EVIDENCE`.

Relacje i lifecycle pozostają bez zmian:

```text
PRODUCT
→ SDS
→ BHP_DECISION
→ DECISION_EVIDENCE
```

oraz:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
APPROVED / REJECTED
CURRENT / SUPERSEDED
```

Zmiana Core ogranicza się do jawnego zachowania:

```text
original_filename
```

jako metadanej źródłowej dowodu.

---

## 22. Poza zakresem

TDR-007 nie obejmuje:

- parsera MSG,
- OCR,
- automatycznej analizy treści evidence,
- automatycznego dopasowania pliku do produktu,
- AI classification,
- wielu evidence dla jednej decyzji,
- workflow podpisu elektronicznego,
- DMS,
- S3 / object storage,
- fizycznego DELETE zarejestrowanego evidence,
- zmian lifecycle BHP,
- zmian schema poza zatwierdzonym `original_filename`,
- zmian Core poza zatwierdzonym `original_filename`,
- zmian SDS workflow,
- ADMIN-01,
- SDS-LEARN-01.

---

## 23. Wymagane testy implementacyjne

Task implementacyjny powinien potwierdzić co najmniej:

1. formularz startuje z `BRAK WYBORU`,
2. brak evidence → brak zapisu decyzji,
3. pierwszy plik z katalogu nie jest automatycznie wybierany,
4. jawny wybór istniejącego evidence → PASS,
5. istniejący evidence `MISSING` → czytelny stan / brak automatycznej zamiany,
6. upload `.msg` → PASS,
7. upload `.pdf` → PASS,
8. upload `.jpg/.jpeg/.png` → PASS,
9. nieobsługiwany format → reject,
10. pusty plik → reject,
11. nowy plik zapisany do `BHP_EVIDENCE_ROOT_PATH/imported/`,
12. nazwa techniczna bezkolizyjna,
13. brak overwrite,
14. path traversal blocked,
15. filesystem failure → brak decision/evidence,
16. DB failure po write → rollback + compensation delete,
17. cleanup failure → FAILED + orphan path,
18. successful COMMIT → plik pozostaje,
19. `BHP_DECISION 1:1 DECISION_EVIDENCE` zachowane,
20. korekta decyzji zachowuje CURRENT / SUPERSEDED,
21. PDF download/open → PASS,
22. obraz preview/download → PASS,
23. MSG download → PASS,
24. MISSING nie usuwa historii,
25. operator data preserved,
26. foundation migration dodaje wyłącznie `original_filename`,
27. Alembic upgrade/downgrade dla foundation → PASS,
28. Domain/ORM/repository zachowują `original_filename`,
29. brak innych zmian Core/schema,
30. new dependencies = NONE, o ile istniejące narzędzia wystarczają.

Testy filesystem:
```text
isolated tmp directory
```

Testy DB:
```text
isolated PostgreSQL / rollback
```

---

## 24. Expected change surface przyszłego Tasku

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
app/infrastructure/config/     # tylko jeśli konieczne
app/infrastructure/db/         # tylko minimalne wiring
tests/
```

Chronione:

```text
app/domain/                 # dozwolone tylko dla foundation original_filename
migrations/                  # jedna migracja foundation
Core docs                     # rewizja CORE-001 v1.3
SDS parser
UNIT_OF_MEASURE
```

---

## 25. Charakter Tasku implementacyjnego

Zakres dotyka:

```text
UI
+ Application
+ filesystem Infrastructure
+ BHP persistence transaction
```

Dlatego przyszły Task powinien mieć:

```text
MODE: INTEGRATION
VALIDATION: LEVEL 2
REPORT: SHORT / STANDARD INTEGRATION
```

Pełny LEVEL 3 wraca dopiero przy checkpoint / closure większego etapu.

---

## 26. STOP conditions

Codex zatrzymuje implementację, jeżeli:

1. wymagane jest schema change inne niż zatwierdzone `original_filename`,
2. wymagane jest Core change inne niż zatwierdzone `original_filename`,
3. istniejący model nie pozwala zachować `1:1`,
4. nie można zachować `CURRENT / SUPERSEDED`,
5. nie można zagwarantować no-overwrite,
6. zapis może wyjść poza `BHP_EVIDENCE_ROOT_PATH`,
7. compensation wymagałaby usunięcia pliku po COMMIT,
8. wymagany byłby parser MSG / OCR / DMS,
9. potrzebna jest nowa zależność bez zatwierdzenia,
10. poprawne wdrożenie wymaga przebudowy całego modułu BHP,
11. trzeba zgadywać semantykę istniejącego schema / kontraktów.

---

## 27. Kryterium techniczne

Po implementacji:

```text
Decyzja BHP
→ evidence = NONE na starcie
→ użytkownik jawnie wybiera istniejące
   lub uploaduje nowe
→ zapis decyzji wymaga evidence
→ nowy evidence trafia WRITE-ONCE do repozytorium
→ DB i filesystem pozostają spójne przez compensation
→ po COMMIT plik jest chroniony
→ później można go otworzyć / pobrać
→ MISSING jest sygnalizowany bez niszczenia historii
```

---

## 28. Authorization boundary

TDR-007 w wersji `Approved` może stanowić authoritative context dla przyszłego Tasku.

Sam TDR:

```text
nie autoryzuje implementacji
```

Implementacja wymaga:
- zatwierdzenia TDR-007,
- osobnego Tasku,
- jawnej autoryzacji Architekta Operacyjnego.

---

## 29. Status dokumentu

Aktualny status:

```text
TDR-007
VERSION: 1.1-approved
STATUS: Approved
```


Wersja 1.1-approved rozwiązuje konflikt persistence ujawniony w BLOCKED TASK-037 poprzez jawne dodanie `DECISION_EVIDENCE.original_filename` w osobnym kroku foundation. Jest obowiązującą decyzją techniczną dla tego zakresu.

---

## 30. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-01 | Draft | Pierwszy techniczny model neutralnego wyboru evidence, kontrolowanego importu do BHP_EVIDENCE_ROOT_PATH, compensation oraz późniejszego read/download |
| 1.0-approved | 2026-10-01 | Approved | Architekt Operacyjny zatwierdził TDR-007 bez zmian merytorycznych; dokument staje się obowiązującą decyzją techniczną dla UI-14 / DOC-02 |
| 1.1-draft | 2026-10-01 | Draft | Po BLOCKED TASK-037 dodano jawny krok foundation: `DECISION_EVIDENCE.original_filename`, minimalna rewizja Core, schema i Alembic przed wznowieniem UI-14 / DOC-02 |


| 1.1-approved | 2026-10-01 | Approved | Architekt Operacyjny zatwierdził rewizję TDR-007 dopuszczającą kontrolowaną zmianę schema dla `original_filename` w DECISION_EVIDENCE i rozdzielenie foundation TASK-038 od wznowienia TASK-037. |
