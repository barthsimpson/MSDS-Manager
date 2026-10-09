# TASK-049 — BATCH-001 CX — LLM-assisted SDS → Evidence JSON DRAFT

**Projekt:** MSDS Manager  
**Task ID:** TASK-049  
**Tryb:** DATA BOOTSTRAP / CONTROLLED ANALYSIS  
**Batch:** BATCH-001  
**Źródło:** katalog `Paczka1 cx`  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Data:** 2026-10-09  
**Wykonawca:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus  

---

## 1. CEL

Przetworzyć wszystkie karty SDS z ręcznie przygotowanej paczki:

```text
Paczka1 cx
```

do kontrolowanych plików:

```text
Evidence JSON DRAFT
```

z wykorzystaniem zdolności analizy semantycznej Codexa / LLM.

Ten Task jest **bootstrapem danych i wiedzy o rzeczywistych SDS**.

Nie jest implementacją docelowego autonomicznego parsera runtime.

Celem jest jednocześnie:

```text
SDS PDF
→ Evidence JSON DRAFT
→ raport różnic / braków / wątpliwości
→ Cerberus review
→ human review źródłowych SDS
→ odpowiedzi referencyjne / Golden Data
```

---

## 2. KONTEKST OBOWIĄZUJĄCY

Przed pracą przeczytaj wyłącznie niezbędne źródła:

1. `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md`
2. `SDS-SCHEMA-001_Kanoniczna_mapa_sekcji_REACH_v1.0-approved.md`
3. `SDS-JSON-001_Kontrakt_Evidence_JSON_DRAFT_v1.0-approved.md`
4. `SDS-ALIAS-001_Biblioteka_aliasow_i_reguly_rozszerzania_v1.0-approved.md`
5. `CORE-001` — tylko gdy konieczne jest sprawdzenie znaczenia pola
6. `GOV-001`
7. `GOV-002`
8. root `AGENTS.md`

Nie wykonuj repo-wide discovery bez konkretnej potrzeby.

---

## 3. CHARAKTER TEGO TASKU

W tym Tasku:

```text
Codex / LLM może semantycznie interpretować treść SDS
```

ale:

```text
nie może zgadywać
nie może rozstrzygać niejednoznaczności bez dowodu
nie może modyfikować zatwierdzonych reguł
nie może automatycznie rozszerzać biblioteki aliasów
```

`SDS-ALIAS-001` jest pomocą i źródłem zatwierdzonych wzorców, ale NIE jest traktowany jako pełny słownik wszystkich wariantów spotykanych w paczce.

Nowy wariant:

```text
→ NEW PATTERN / ALIAS CANDIDATE w raporcie
→ bez aktywacji
→ bez zmiany SDS-ALIAS-001
```

---

## 4. GRANICA WEJŚCIA

Przetwarzaj wyłącznie pliki PDF znajdujące się w katalogu:

```text
Paczka1 cx
```

Jeżeli nie można jednoznacznie zidentyfikować dokładnie jednego katalogu wejściowego o tej nazwie:

```text
STOP / BLOCKED
→ podaj znalezione możliwości
→ poproś o pełną ścieżkę
```

Nie skanuj innych paczek.

Nie modyfikuj, nie przenoś i nie zmieniaj nazw źródłowych PDF.

---

## 5. GRANICA WYJŚCIA

Utwórz:

```text
docs/sds_bootstrap/BATCH-001_CX/
├── json/
└── BATCH-001_REPORT.md
```

Dopuszczalne są dodatkowo wyłącznie techniczne pliki manifestu potrzebne do identyfikowalności batcha.

Nie zapisuj nic do PostgreSQL.

Nie zapisuj danych przez Application use cases.

Nie importuj jeszcze danych do Core.

Nie modyfikuj production code.

Nie zmieniaj schema ani migracji.

---

## 6. PRZETWARZANIE KAŻDEGO PDF

Dla każdego PDF:

### 6.1. Identyfikacja źródła

Zapisz co najmniej:

```text
source_file
sha256
page_count
readability
```

Dozwolone stany czytelności:

```text
READABLE
PARTIALLY_READABLE
UNREADABLE
```

### 6.2. Rozpoznanie logicznych SDS

Nie zakładaj:

```text
1 PDF = 1 SDS
```

Sprawdź, czy PDF zawiera:

```text
1
lub
N
```

logicznych kart SDS.

Dla każdej logicznej karty ustal:

```text
document_key
page_range
```

Jeżeli podział nie jest jednoznaczny:

```text
AMBIGUOUS
→ raport
→ bez zgadywania
```

### 6.3. Ekstrakcja

Dla każdego logicznego SDS utwórz JSON zgodny z:

```text
SDS-JSON-001 v1.0-approved
```

Każde pole ma zachować kontrakt:

```text
value
state
evidence
```

Dozwolone stany ekstrakcji:

```text
FOUND
NOT_FOUND
AMBIGUOUS
UNREADABLE
```

Twarda reguła:

```text
FOUND
→ musi posiadać evidence
```

oraz:

```text
NOT_FOUND / AMBIGUOUS / UNREADABLE
≠
NO
```

### 6.4. Evidence

Dla każdego `FOUND` zapisz możliwie dokładnie:

```text
page
section
subsection, jeżeli możliwe
source_text
```

Nazwa pliku nie jest samodzielnym dowodem wartości domenowej.

### 6.5. Interpretacja semantyczna

Codex może wykorzystać znaczenie tekstu, kontekst tabel i strukturę dokumentu.

Jeżeli jednak występują co najmniej dwie sensowne interpretacje:

```text
state = AMBIGUOUS
```

i problem musi trafić do raportu.

Przykładowo nie wolno bez podstawy zrównywać:

```text
manufacturer
supplier
distributor
importer
EU representative
```

---

## 7. CO ANALIZUJEMY W PIERWSZEJ PACZCE

Przetwarzaj zakres przewidziany przez obowiązujący `SDS-JSON-001`.

Szczególnie kontroluj i raportuj:

```text
product name
manufacturer product code
podmioty i role z sekcji 1.3
SDS issue/update date
SDS revision/version
logical SDS segmentation
source evidence
```

Jeżeli kontrakt JSON zawiera dalsze pola, możesz je wypełnić tylko wtedy, gdy są jednoznacznie wspierane przez źródło.

Nie poszerzaj kontraktu JSON samodzielnie.

---

## 8. RAPORT PACZKI

Utwórz:

```text
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_REPORT.md
```

Raport ma być przede wszystkim narzędziem do wspólnej analizy:

```text
Codex
→ Cerberus
→ Człowiek
```

### 8.1. SUMMARY

Podaj:

```text
liczba PDF wejściowych
liczba logicznych SDS
liczba JSON utworzonych
READABLE
PARTIALLY_READABLE
UNREADABLE
COMPLETE
NEEDS_REVIEW
FAILED
```

`COMPLETE / NEEDS_REVIEW / FAILED` są wyłącznie statusami batch-processing, nie stanami domenowymi Core.

### 8.2. PROCESSED FILES

Tabela:

| ID | PDF | Logical SDS | Pages | JSON | Status |
|---|---|---:|---|---|---|

### 8.3. CLEAR

Wskaż typy danych, które w tej paczce były odczytywane jednoznacznie.

Nie trzeba przepisywać całej zawartości JSON.

### 8.4. AMBIGUITIES

Każda wątpliwość otrzymuje stabilne ID:

```text
B001-Q001
B001-Q002
...
```

Tabela:

| Issue ID | PDF | Page | Section | Field / role | Codex observation | Why ambiguous | Proposed options |
|---|---|---:|---|---|---|---|---|

Nie wybieraj sam jednej opcji, jeżeli dowód nie rozstrzyga.

### 8.5. NOT FOUND

Tabela oczekiwanych danych, których nie odnaleziono:

| PDF | Logical SDS | Expected field | Search area | Result |
|---|---|---|---|---|

### 8.6. UNREADABLE

Tabela:

| PDF | Pages | Problem | Impact |
|---|---|---|---|

Nie używaj OCR w tym Tasku.

### 8.7. NEW PATTERNS / ALIAS CANDIDATES

Zapisz nowe zaobserwowane warianty:

| Candidate ID | PDF | Page | Canonical target | Observed label / pattern | Context |
|---|---|---:|---|---|---|

To są wyłącznie obserwacje:

```text
CANDIDATE
```

Nie modyfikuj `SDS-ALIAS-001`.

### 8.8. LAYOUT DIFFERENCES

Wskaż istotne różnice w układzie dokumentów, np.:

```text
wartość w tym samym wierszu
wartość w kolejnym wierszu
tabela
nagłówek / stopka
powtarzalny header
kilka podmiotów w sekcji 1.3
kilka SDS w jednym PDF
nietypowy zapis daty / rewizji
```

### 8.9. QUESTIONS FOR HUMAN

Na końcu przygotuj krótką listę tylko tych pytań, których rzeczywiście nie można rozstrzygnąć z dokumentu.

Format:

```text
B001-Qxxx
PDF:
PAGE:
SECTION:
CODEX OBSERVATION:
QUESTION:
EXPECTED HUMAN ACTION:
- wskaż prawidłową wartość / rolę
- wskaż miejsce w SDS
```

---

## 9. HUMAN ANSWER MATRIX

Na końcu raportu dodaj pustą tabelę do późniejszego uzupełnienia:

| Issue ID | Human decision | Evidence page/section | Expected JSON result | Decision status |
|---|---|---|---|---|

Pole `Decision status` pozostaw:

```text
OPEN
```

do czasu review człowieka.

Codex NIE wypełnia decyzji człowieka.

---

## 10. ZASADA BRAKÓW

Jeżeli dane nie występują w SDS:

```text
NOT_FOUND
```

Jeżeli występują, ale nie wiadomo jak je interpretować:

```text
AMBIGUOUS
```

Jeżeli nie można ich odczytać technicznie:

```text
UNREADABLE
```

Nigdy nie zamieniaj tych stanów na:

```text
NO
0
false
"brak"
```

chyba że samo źródło jednoznacznie komunikuje taką wartość, a kontrakt domenowy na to pozwala.

---

## 11. SOURCE VS FILENAME

Nazwa pliku może wspierać identyfikację źródła.

Nie może być jedynym dowodem dla:

```text
product name
issue/update date
revision/version
manufacturer
classification
```

Jeżeli nazwa pliku i treść SDS są sprzeczne:

```text
treść SDS pozostaje źródłem
+
konflikt trafia do raportu
```

---

## 12. OCHRONA GRANIC

W TASK-049 zabronione jest:

```text
PostgreSQL write
Application import
Streamlit change
Domain change
Core change
schema change
Alembic migration
BHP decision
CURRENT / ARCHIVED decision
PRODUCT creation
OCR
nowa dependency
modyfikacja SDS-ALIAS
modyfikacja SDS-SCHEMA
modyfikacja SDS-JSON
modyfikacja źródłowych PDF
```

---

## 13. STOP CONDITIONS

Zatrzymaj cały Task jako `BLOCKED`, jeżeli:

1. nie można jednoznacznie znaleźć `Paczka1 cx`,
2. obowiązujące źródła projektowe są ze sobą sprzeczne,
3. `SDS-JSON-001` nie pozwala zapisać krytycznej obserwacji bez zmiany kontraktu,
4. wykonanie wymagałoby modyfikacji Core,
5. wykonanie wymagałoby zapisu do bazy,
6. wymagany byłby OCR dla większości paczki,
7. wymagane byłoby dodanie zależności lub trwałego kodu produkcyjnego,
8. istnieje ryzyko nadpisania źródłowych PDF.

Pojedynczy trudny PDF NIE blokuje całej paczki.

Dla pojedynczego PDF użyj:

```text
NEEDS_REVIEW
UNREADABLE
FAILED
```

i kontynuuj pozostałe dokumenty.

---

## 14. VALIDATION

Przed zakończeniem sprawdź:

```text
każdy wejściowy PDF ma wpis w raporcie
każdy utworzony JSON jest poprawnym JSON
każdy FOUND posiada evidence
każdy JSON wskazuje źródłowy PDF
żaden output nie znajduje się w katalogu źródłowym
brak zmian production code
brak zmian DB/schema
git diff --check dla utworzonych artefaktów = PASS
```

Nie uruchamiaj pełnego pytest / Alembic / E2E.

To nie jest Task implementacyjny ani checkpoint.

---

## 15. RAPORT KOŃCOWY CODEXA

Po zakończeniu odpowiedz krótko:

```text
TASK-049 REPORT

STATUS:
DONE / BLOCKED

BATCH:
BATCH-001_CX

INPUT:
- PDF count:

OUTPUT:
- logical SDS:
- JSON drafts:
- COMPLETE:
- NEEDS_REVIEW:
- UNREADABLE:
- FAILED:

HUMAN QUESTIONS:
- count:

NEW PATTERNS:
- count:

CHANGED:
- docs/sds_bootstrap/BATCH-001_CX/ only
- production code: NO
- DB: NO
- schema: NO

REPORT:
docs/sds_bootstrap/BATCH-001_CX/BATCH-001_REPORT.md

NEXT:
CERBERUS REVIEW

OCZEKUJĘ NA DECYZJĘ.
NIE IMPORTUJĘ DANYCH DO MSDS MANAGER.
NIE ROZPOCZYNAM BATCH-002.
```

---

## 16. AUTHORIZATION

```text
TASK-049
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Uruchom dopiero po jawnym poleceniu Architekta Operacyjnego:

```text
Wykonaj TASK-049.
```
