# TDR-008 — Kontrolowany dostęp do CURRENT SDS

**Projekt:** MSDS Manager  
**Dokument:** TDR-008  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-10-01  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel

TDR-008 definiuje techniczny mechanizm realizacji:

```text
UI-11 — otwieranie / pobieranie CURRENT SDS
```

Celem jest umożliwienie użytkownikowi pobrania fizycznego pliku CURRENT SDS bez wychodzenia do katalogów systemowych.

Zakres dotyczy wyłącznie kontrolowanego odczytu.

---

## 2. Kontekst obowiązujący

TDR-008 należy czytać łącznie z:

1. `BDR-003 — Dokument SDS, aktualność i wersjonowanie`
2. `BDR-007_Kontrolowany_import_SDS_v1.0-approved`
3. `TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja`
4. `TDR-003 — struktura warstw aplikacji`
5. `TDR-006_Kontrolowany_import_SDS_v1.0-approved`
6. `CORE-001 v1.3-approved`
7. `GOV-001 v1.0-approved`
8. `GOV-002 v1.0-approved`

Obowiązuje:

```text
PRODUCT
→ maksymalnie jeden SDS CURRENT
```

oraz:

```text
SDS_ROOT_PATH + relative_path
→ fizyczny plik SDS
```

---

## 3. Decyzja techniczna

UI-11 realizuje wzorzec:

```text
Streamlit
→ Application read use case
→ SDS filesystem port
→ SDS filesystem adapter
→ SDS_ROOT_PATH + relative_path
→ controlled read/download
```

Streamlit nie wykonuje bezpośrednio:

- `open()` na ścieżkach systemowych,
- operacji SQL/ORM,
- łączenia root path z relative_path,
- walidacji path traversal.

---

## 4. Zakres użytkowy

W widoku produktu dla CURRENT SDS należy udostępnić:

```text
[Pobierz SDS]
```

Opcjonalnie UI może prezentować także:

```text
[Otwórz SDS]
```

jeżeli framework realizuje to jako bezpieczne udostępnienie pliku w przeglądarce.

Minimalnym wymaganiem UI-11 jest:

```text
download
```

---

## 5. Źródło pliku

Źródłem dokumentu jest wyłącznie rekord CURRENT SDS wskazanego produktu.

Application pobiera:

```text
original_filename
relative_path
status
```

i zezwala na odczyt tylko dla:

```text
status = CURRENT
```

UI-11 nie służy do wyboru dowolnego pliku SDS z repozytorium.

---

## 6. Path safety

Fizyczna ścieżka jest rozwiązywana wyłącznie jako:

```text
SDS_ROOT_PATH + relative_path
```

Adapter musi potwierdzić, że resolved path znajduje się wewnątrz resolved `SDS_ROOT_PATH`.

Należy odrzucić:

```text
absolute path
UNC path
../
..\
path traversal
wyjście poza SDS_ROOT_PATH
```

`original_filename` nie steruje lokalizacją pliku.

---

## 7. Read-only

UI-11 nie może:

- nadpisywać PDF,
- modyfikować PDF,
- usuwać PDF,
- przenosić PDF,
- zmieniać nazwy PDF,
- tworzyć nowej wersji SDS,
- zmieniać CURRENT / ARCHIVED.

Obowiązuje:

```text
READ ONLY
```

---

## 8. Nazwa użytkowa downloadu

Jeżeli plik fizyczny jest przechowywany pod nazwą techniczną, np.:

```text
imported/<storage_uuid>.pdf
```

plik pobierany przez użytkownika powinien być prezentowany pod:

```text
original_filename
```

Nie pod UUID storage, o ile `original_filename` jest dostępne.

---

## 9. MISSING

Jeżeli rekord CURRENT SDS istnieje, ale fizyczny plik jest niedostępny:

```text
MISSING
```

UI:

- pokazuje czytelny komunikat,
- nie usuwa rekordu SDS,
- nie zmienia CURRENT / ARCHIVED,
- nie podstawia innego PDF,
- nie próbuje naprawiać ścieżki heurystycznie.

Przykład:

```text
Plik SDS jest obecnie niedostępny.
```

---

## 10. Application

Application powinno udostępnić mały read use case, np.:

```text
GetCurrentSdsFile
```

albo odpowiednik zgodny z konwencją repo.

Odpowiedzialności:

```text
1. potwierdź PRODUCT
2. pobierz CURRENT SDS
3. sprawdź metadane
4. wywołaj filesystem adapter
5. zwróć bytes/stream + original_filename
```

Nie przenosić logiki filesystem do presentation.

---

## 11. Filesystem adapter

Należy wykorzystać istniejący adapter SDS, jeżeli można go rozszerzyć bez rozbijania odpowiedzialności.

Minimalne wymagane operacje:

```text
resolve_sds_path(relative_path)
check_availability(relative_path)
read_sds(relative_path)
```

Nazwy mogą zostać dostosowane do repo.

Nie tworzyć nowego generic storage frameworka.

---

## 12. Persistence / schema

TDR-008 nie wymaga:

```text
schema change
Alembic migration
Core change
new table
new dependency
```

Jeżeli implementacja ujawni potrzebę którejkolwiek z powyższych zmian:

```text
STOP / BLOCKED
```

---

## 13. UI

Preferowane miejsce:

```text
Produkty
→ Szczegóły produktu
→ SDS
→ Plik: <original_filename>
→ [Pobierz SDS]
```

Przycisk ma dotyczyć wyłącznie wyświetlanego CURRENT SDS.

Nie przebudowywać nawigacji ani całej sekcji Produkt.

---

## 14. Testy

Przyszły Task implementacyjny powinien potwierdzić co najmniej:

1. produkt z CURRENT SDS i dostępnym PDF → download PASS,
2. nazwa downloadu = `original_filename`,
3. techniczny UUID storage nie jest nazwą użytkową downloadu,
4. brak CURRENT SDS → brak aktywnego downloadu / kontrolowany stan,
5. CURRENT SDS + brak fizycznego PDF → MISSING,
6. path traversal → blocked,
7. absolute path → blocked,
8. UNC path → blocked,
9. resolved path poza root → blocked,
10. plik nie jest modyfikowany,
11. lifecycle CURRENT / ARCHIVED bez zmian,
12. operator data preserved,
13. schema change = NONE,
14. migration = NONE,
15. Core change = NONE,
16. new dependencies = NONE.

---

## 15. Expected change surface

Oczekiwane:

```text
app/presentation/streamlit/
app/application/
app/infrastructure/filesystem/
tests/
```

Dopuszczalne minimalne read wiring w:

```text
app/infrastructure/db/
```

wyłącznie jeśli obecny read model nie przekazuje danych CURRENT SDS potrzebnych do use case.

Chronione:

```text
app/domain/
migrations/
Core docs
SDS lifecycle
BHP lifecycle
parser SDS
UNIT_OF_MEASURE
```

---

## 16. STOP conditions

Codex zatrzymuje implementację, jeżeli:

1. potrzebna jest zmiana schema,
2. potrzebna jest zmiana Core,
3. trzeba zmienić lifecycle CURRENT / ARCHIVED,
4. nie można zagwarantować path confinement,
5. trzeba zgadywać plik CURRENT,
6. trzeba heurystycznie naprawiać `relative_path`,
7. potrzebna jest nowa zależność,
8. wymagane byłoby tworzenie kopii PDF jako element normalnego odczytu,
9. implementacja wymaga przebudowy modułu SDS zamiast lokalnego read use case.

---

## 17. Kryterium techniczne

Po implementacji:

```text
Produkt
→ CURRENT SDS
→ [Pobierz SDS]
→ kontrolowany odczyt z SDS_ROOT_PATH
→ download jako original_filename
```

oraz:

```text
brak pliku
→ MISSING
→ historia i CURRENT pozostają bez zmian
```

---

## 18. Authorization boundary

TDR-008 po zatwierdzeniu może stanowić authoritative context dla Tasku UI-11.

Sam dokument:

```text
nie autoryzuje implementacji
```

Implementacja wymaga osobnego Tasku i jawnego polecenia Architekta Operacyjnego.

---

## 19. Status

```text
TDR-008
VERSION: 1.0-approved
STATUS: Approved
```


---

## 20. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-01 | Draft | Pierwszy techniczny model kontrolowanego odczytu i pobierania CURRENT SDS |
| 1.0-approved | 2026-10-01 | Approved | Architekt Operacyjny zatwierdził TDR-008 bez zmian merytorycznych |
