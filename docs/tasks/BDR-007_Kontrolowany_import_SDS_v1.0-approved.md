# BDR-007 — Kontrolowany import dokumentu SDS

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-007  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-09-30  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel decyzji

Celem BDR-007 jest umożliwienie użytkownikowi dodawania dokumentu SDS bezpośrednio z komputera do MSDS Manager, przy zachowaniu ochrony dokumentu źródłowego, identyfikowalności i obecnego modelu SDS.

Decyzja realizuje obszar backlogu:

```text
DOC-01 — dodawanie SDS z komputera / upload do kontrolowanego repozytorium
```

BDR-007 nie zmienia tożsamości dokumentu SDS, lifecycle `CURRENT / ARCHIVED`, modelu PRODUCT ani zasad decyzji BHP.

---

## 2. Problem

Dotychczasowy model zakładał, że fizyczny PDF SDS musi już znajdować się w `SDS_ROOT_PATH`, a aplikacja jedynie zapisuje jego metadane i ścieżkę względną.

Powoduje to dodatkową operację ręczną:

```text
użytkownik otrzymuje PDF
→ ręcznie kopiuje go do SDS_ROOT_PATH
→ dopiero potem rejestruje SDS w aplikacji
```

DOC-01 ma uprościć ten proces bez utraty kontroli nad plikami źródłowymi.

---

## 3. Decyzja główna

MSDS Manager może przyjąć wskazany przez użytkownika plik PDF znajdujący się poza `SDS_ROOT_PATH` i wykonać kontrolowany import do repozytorium SDS.

Docelowy proces:

```text
użytkownik wybiera PDF z komputera
        ↓
aplikacja waliduje wejście
        ↓
aplikacja tworzy NOWĄ kopię pliku w SDS_ROOT_PATH
        ↓
zapisuje original_filename + relative_path
        ↓
użytkownik zatwierdza rejestrację SDS
        ↓
rekord SDS zostaje utworzony zgodnie z obowiązującym lifecycle
```

---

## 4. Model ochrony pliku

Dla dokumentów SDS obowiązuje model:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Znaczenie:

### Import

Aplikacja może wykonać zapis nowej kopii PDF do kontrolowanego `SDS_ROOT_PATH` wyłącznie jako część jawnej operacji importu zainicjowanej przez użytkownika.

### Po rejestracji

Po skutecznym zarejestrowaniu SDS aplikacja nie może w standardowym workflow:

- nadpisywać pliku,
- modyfikować zawartości PDF,
- usuwać pliku,
- przenosić pliku,
- zmieniać nazwy istniejącego pliku w sposób niszczący identyfikowalność.

Plik staje się chronionym dokumentem źródłowym.

---

## 5. Dozwolony typ dokumentu

DOC-01 dotyczy wyłącznie dokumentów SDS w formacie:

```text
.pdf
```

Inny typ pliku nie może zostać przyjęty jako SDS w ramach tego workflow.

Walidacja formatu wejściowego należy do warstwy Application / Infrastructure, nie do logiki Streamlit.

---

## 6. Relacja do SDS_ROOT_PATH

`SDS_ROOT_PATH` pozostaje kontrolowanym repozytorium dokumentów SDS poza PostgreSQL.

Zmienia się wyłącznie dotychczasowa zasada całkowitego `read-only`.

Po BDR-007 obowiązuje:

```text
SDS_ROOT_PATH
= zapis nowego pliku wyłącznie przez kontrolowany import
+ brak overwrite istniejących plików
+ read-only dla plików już zarejestrowanych
```

Aplikacja nadal nie przechowuje binarnej zawartości PDF w PostgreSQL.

---

## 7. Metadane i ścieżka

Baza danych nadal przechowuje:

```text
original_filename
relative_path
```

Nie przechowuje pełnej lokalnej ścieżki systemowej jako podstawowego odwołania do SDS.

Fizyczna lokalizacja pozostaje wyznaczana jako:

```text
SDS_ROOT_PATH + relative_path
```

`original_filename` zachowuje nazwę pliku dostarczonego przez użytkownika, niezależnie od ewentualnej technicznej nazwy pliku w repozytorium.

---

## 8. Kolizje nazw i overwrite

Import nie może nadpisywać istniejącego pliku.

Jeżeli docelowa nazwa jest już zajęta, system musi zastosować kontrolowany mechanizm bezkolizyjnego zapisu, np.:

```text
unikalna nazwa techniczna
lub
unikalny podkatalog
```

Szczegółowy mechanizm należy do TDR.

Kolizja nazwy nie może prowadzić do:

```text
overwrite
usunięcia istniejącego pliku
cichego zastąpienia dokumentu
```

---

## 9. Warunek utworzenia rekordu SDS

Rekord SDS może zostać utworzony tylko wtedy, gdy:

1. istnieje właściwy `PRODUCT`,
2. plik PDF został skutecznie zwalidowany,
3. nowa kopia PDF istnieje w kontrolowanym `SDS_ROOT_PATH`,
4. użytkownik zatwierdzi rejestrację SDS.

Obowiązuje:

```text
brak PRODUCT → brak rekordu SDS
brak poprawnego PDF → brak rekordu SDS
błąd zapisu pliku → brak rekordu SDS
brak zatwierdzenia użytkownika → brak rekordu SDS
```

System nie tworzy rekordu wskazującego na plik, który nie został skutecznie zapisany.

---

## 10. Spójność importu i rejestracji

DOC-01 nie może pozostawiać niekontrolowanych częściowych rezultatów.

W szczególności błąd po stronie zapisu pliku lub rejestracji SDS musi być obsłużony tak, aby system nie deklarował sukcesu dla niekompletnej operacji.

Szczegółowa strategia techniczna dotycząca:

- pliku tymczasowego,
- finalizacji nazwy,
- cleanup po błędzie,
- kolejności zapisu filesystem ↔ database,
- rollback / compensation,

zostanie określona w TDR-006.

---

## 11. Lifecycle SDS bez zmian

BDR-007 nie zmienia zasad:

```text
CURRENT
ARCHIVED
```

Dodanie nowego pliku do repozytorium nie ustala automatycznie `CURRENT`.

Zmiana poprzedniego:

```text
CURRENT → ARCHIVED
```

oraz ustanowienie nowego:

```text
SDS → CURRENT
```

następują dopiero zgodnie z istniejącym, zatwierdzonym workflow rejestracji SDS.

Numer rewizji, data dokumentu ani nazwa pliku nie ustalają automatycznie aktualności.

---

## 12. Brak automatycznej interpretacji dokumentu

DOC-01 jest mechanizmem dostarczenia i rejestracji pliku.

Nie oznacza uruchomienia:

- parsera Stage 2,
- automatycznej analizy SDS,
- automatycznej decyzji BHP,
- automatycznej kwalifikacji prawnej,
- automatycznego tworzenia produktu na podstawie PDF.

Jeżeli istniejący manualny workflow pozwala wprowadzić dane SDS ręcznie, pozostaje on obowiązującym mechanizmem.

---

## 13. Źródło i identyfikowalność

Import powinien zachować identyfikowalność dokumentu co najmniej przez:

```text
sds_id
product_id
original_filename
relative_path
issue_date, jeśli dostępna
revision, jeśli dostępna
registered_at
status SDS
```

Aplikacja nie może traktować nazwy pliku jako technicznego identyfikatora SDS.

---

## 14. Bezpieczeństwo ścieżek

Import nie może umożliwiać zapisania pliku poza kontrolowanym `SDS_ROOT_PATH`.

Ścieżka pochodząca od użytkownika lub nazwa pliku nie może pozwalać na obejście katalogu bazowego.

Szczegółowe zabezpieczenia techniczne zostaną określone w TDR-006.

---

## 15. Granice decyzji

BDR-007 nie wprowadza:

- przechowywania PDF w PostgreSQL,
- fizycznego DELETE z poziomu standardowego workflow,
- edycji PDF,
- nadpisywania plików,
- zarządzania dowodami BHP,
- UI-11 — otwierania/pobierania CURRENT SDS,
- UI-14 / DOC-02 — podglądu dowodu BHP,
- parsera SDS Stage 2,
- automatycznej deduplikacji treści PDF,
- systemu DMS,
- wersjonowania binarnego pliku niezależnego od modelu SDS,
- zmian schema PostgreSQL,
- zmian modelu PRODUCT,
- zmian lifecycle SDS.

---

## 16. Wpływ na istniejące decyzje

BDR-007 jest nową decyzją uzupełniającą dotyczącą sposobu przyjęcia pliku SDS do kontrolowanego repozytorium.

### BDR-003

BDR-003 pozostaje obowiązujący w zakresie:

- tożsamości SDS,
- metadanych,
- `CURRENT / ARCHIVED`,
- dostępności pliku,
- historii,
- ochrony dokumentu po rejestracji.

BDR-007 zmienia wyłącznie wcześniejsze ograniczenie, zgodnie z którym aplikacja traktowała `SDS_ROOT_PATH` jako całkowicie `read-only`.

Po BDR-007 interpretacja brzmi:

```text
kontrolowany WRITE-ONCE podczas importu
→ READ-ONLY po rejestracji
```

### TDR-002

TDR-002 pozostaje obowiązujący dla konfiguracji `SDS_ROOT_PATH`, ścieżek względnych i przechowywania dokumentów poza PostgreSQL.

Jego dotychczasowa techniczna zasada całkowitego `read-only` wymaga doprecyzowania przez nowy TDR-006 przed implementacją DOC-01.

Nie należy modyfikować TDR-002 „przy okazji” implementacji.

---

## 17. Konsekwencja techniczna

Przed implementacją DOC-01 wymagany jest:

```text
TDR-006 — Kontrolowany zapis / import SDS do SDS_ROOT_PATH
```

TDR-006 ma rozstrzygnąć co najmniej:

- adapter filesystem,
- walidację PDF,
- sposób bezkolizyjnego zapisu,
- ochronę przed overwrite,
- bezpieczeństwo ścieżek,
- kolejność filesystem ↔ database,
- rollback / compensation,
- cleanup pliku przy nieudanej operacji,
- testy integracyjne,
- zakres zmian w UI/Application/Infrastructure.

Dopiero po zatwierdzeniu TDR-006 należy przygotować Task implementacyjny DOC-01.

---

## 18. Kryterium biznesowe DOC-01

Po wdrożeniu DOC-01 użytkownik powinien móc wykonać:

```text
Wybierz PDF z komputera
→ zatwierdź dane SDS
→ aplikacja zapisuje nową kopię w SDS_ROOT_PATH
→ aplikacja rejestruje SDS
→ dokument pozostaje chroniony przed zmianą przez standardowy workflow
```

bez ręcznego kopiowania pliku do katalogu SDS przed rozpoczęciem rejestracji.

---

## 19. Status decyzji

Architekt Operacyjny zatwierdził model:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Status:

```text
BDR-007
VERSION: 1.0-approved
STATUS: Approved
```

---

## 20. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-09-30 | Approved | Zatwierdzono kontrolowany import PDF SDS do `SDS_ROOT_PATH` w modelu WRITE-ONCE → READ-ONLY AFTER REGISTRATION; bez overwrite, bez zmian lifecycle SDS i bez przechowywania PDF w PostgreSQL |
