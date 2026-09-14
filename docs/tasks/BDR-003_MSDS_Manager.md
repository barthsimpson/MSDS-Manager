# BDR-003 — Dokument SDS, aktualność i wersjonowanie

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-003  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Powiązane IR:** IR-001-10, IR-001-11, IR-001-12, IR-001-13, IR-001-14, IR-001-15  

---

## 1. Cel decyzji

Celem BDR-003 jest jednoznaczne zdefiniowanie modelu dokumentu SDS w MSDS Manager, zasad jego identyfikacji, aktualności, wersjonowania, dostępności pliku oraz zachowania historii.

Dokument formalizuje zasady już przyjęte w CORE-001 i doprecyzowane w kolejnych decyzjach Architekta Operacyjnego.

---

## 2. Zasada nadrzędna

Dokument SDS jest osobnym obiektem domenowym powiązanym z produktem.

Nie jest produktem samym w sobie.

Model:

```text
PRODUCT
   │
   └── 1:N
       SDS
```

Jeden produkt może posiadać wiele kolejnych dokumentów SDS.

---

## 3. Tożsamość dokumentu SDS

Każdy zarejestrowany dokument SDS otrzymuje własny, niezmienny identyfikator systemowy:

`sds_id`

`sds_id` identyfikuje rekord dokumentu niezależnie od:

- nazwy pliku,
- lokalizacji pliku,
- numeru rewizji,
- daty wydania,
- nazwy produktu.

Nazwa pliku nie jest technicznym identyfikatorem SDS.

---

## 4. Minimalny zestaw danych rekordu SDS

Każdy rekord SDS przechowuje co najmniej:

- `sds_id`
- `product_id`
- `original_filename`
- `relative_path`
- `issue_date` — jeżeli możliwa do jednoznacznego odczytania
- `revision` — jeżeli możliwa do jednoznacznego odczytania
- `document_status`
- `registered_at`

Dodatkowo system może przechowywać status dostępności pliku zgodnie z sekcją 9.

---

## 5. Warunek utworzenia rekordu SDS

Rekord SDS może zostać utworzony tylko wtedy, gdy:

1. istnieje `PRODUCT`,
2. istnieje fizyczny plik PDF wskazany w `SDS_ROOT_PATH`,
3. użytkownik zatwierdzi rejestrację dokumentu.

Obowiązuje:

```text
brak PRODUCT → brak rekordu SDS
brak PDF     → brak nowego rekordu SDS
```

System nie tworzy pustych rekordów SDS oczekujących na przyszły dokument.

---

## 6. Rewizja i data dokumentu

Numer rewizji oraz data wydania/aktualizacji są metadanymi dokumentu.

Mogą zostać odczytane automatycznie z PDF i zapisane przy `sds_id`.

Nie są one technicznym identyfikatorem dokumentu.

Nie są również warunkiem utworzenia rekordu, jeżeli nie można ich jednoznacznie ustalić.

Aktualność dokumentu nie wynika automatycznie z:

- numeru rewizji,
- daty,
- nazwy pliku.

Powodem jest brak jednolitego sposobu oznaczania wersji SDS przez producentów.

---

## 7. Status dokumentu SDS

Dopuszczalne statusy dokumentu w MVP:

- `CURRENT`
- `ARCHIVED`

Reguła integralności:

> **Jeden PRODUCT może posiadać maksymalnie jeden zatwierdzony SDS ze statusem CURRENT.**

---

## 8. Zatwierdzenie nowego SDS

Dodanie pliku do katalogu lub jego automatyczne odczytanie nie zmienia statusu poprzedniego SDS.

Zmiana następuje dopiero w momencie zatwierdzenia nowego dokumentu przez użytkownika.

Operacja zatwierdzenia nowego SDS powoduje jednocześnie:

```text
poprzedni CURRENT → ARCHIVED
nowy SDS          → CURRENT
```

Operacja powinna być wykonana jako jedna spójna zmiana danych.

Poprzedni rekord SDS pozostaje w historii.

---

## 9. Dostępność fizycznego pliku

Status dokumentu (`CURRENT` / `ARCHIVED`) jest niezależny od dostępności fizycznego PDF.

System musi rozróżniać:

- `AVAILABLE` — plik istnieje we wskazanej lokalizacji,
- `MISSING` — rekord SDS istnieje, ale pliku nie można odnaleźć.

Przykładowe kombinacje:

```text
CURRENT + AVAILABLE
CURRENT + MISSING
ARCHIVED + AVAILABLE
ARCHIVED + MISSING
```

`CURRENT + MISSING` oznacza problem wymagający działania.

Usunięcie lub przeniesienie pliku poza aplikacją nie powoduje automatycznego usunięcia rekordu SDS z bazy.

---

## 10. Ochrona dokumentu źródłowego

Pliki SDS są przechowywane poza PostgreSQL w repozytorium wskazanym przez:

`SDS_ROOT_PATH`

Aplikacja traktuje katalog jako read-only.

Aplikacja nie może automatycznie:

- nadpisywać PDF,
- modyfikować PDF,
- usuwać PDF,
- zmieniać nazw plików,
- przenosić plików.

Baza przechowuje metadane i ścieżkę względną względem `SDS_ROOT_PATH`.

---

## 11. Identyfikowalność plików w katalogu

MSDS Manager nie narzuca sposobu nazewnictwa fizycznych plików SDS.

Użytkownik odpowiada za organizację katalogu źródłowego i zapewnienie identyfikowalności plików zgodnie z wymaganiami organizacyjnymi.

System zapewnia własną identyfikowalność przez:

- `sds_id`,
- `product_id`,
- `original_filename`,
- `relative_path`,
- rewizję,
- datę,
- historię statusu.

---

## 12. Duplikaty SDS

System nie implementuje zaawansowanej deduplikacji dokumentów SDS.

W szczególności nie:

- scala dokumentów,
- automatycznie wybiera „lepszej” wersji,
- interpretuje konfliktów za użytkownika.

Przy pierwszym zbiorczym wprowadzaniu SDS z katalogu, jeżeli zostanie wykryty konflikt wskazujący na zdublowanie dokumentu lub dokumentów przypisanych do tego samego produktu/numeru, system zatrzymuje automatyczne rozstrzygnięcie.

Powinien wyświetlić komunikat w rodzaju:

> „Masz zdublowane SDS nr 30470. Dokonaj wyboru właściwego pliku w katalogu danych.”

Użytkownik porządkuje katalog, a następnie ponawia operację.

---

## 13. Wersje językowe

MSDS Manager nie wprowadza w MVP osobnego, rozbudowanego mechanizmu zarządzania wariantami językowymi tej samej rewizji.

Każdy zatwierdzony PDF jest osobnym rekordem SDS z własnym `sds_id`.

Jeżeli użytkownik zdecyduje, że dany dokument ma być dokumentem obowiązującym dla produktu, otrzymuje status `CURRENT`.

Rozbudowana obsługa wariantów językowych może zostać dodana później, jeśli pojawi się uzasadniona potrzeba.

---

## 14. Nowy SDS a decyzja BHP

Zatwierdzenie nowego SDS dla istniejącego produktu może oznaczać zmianę:

- składu,
- klasyfikacji,
- zagrożeń,
- warunków stosowania,
- innych właściwości bezpieczeństwa.

Dlatego obowiązuje reguła:

> **Nowy zatwierdzony SDS wymaga nowej decyzji Specjalisty BHP.**

Po zatwierdzeniu nowego SDS jako `CURRENT`:

- poprzedni SDS przechodzi na `ARCHIVED`,
- poprzednia decyzja BHP pozostaje w historii,
- produkt przechodzi do statusu `PENDING_APPROVAL`,
- nowa decyzja BHP musi odnosić się do nowego `sds_id`.

System nie może automatycznie przenosić wcześniejszej decyzji BHP na nową wersję SDS.

---

## 15. Relacja PRODUCT–SDS–BHP

Model logiczny:

```text
PRODUCT
   │
   ├── SDS #1 ARCHIVED
   │      └── BHP_DECISION #1
   │
   └── SDS #2 CURRENT
          └── wymaga nowej BHP_DECISION
```

Pozwala to jednoznacznie ustalić, jaka karta SDS była podstawą konkretnej decyzji BHP.

---

## 16. Automatyczny odczyt danych z PDF

System może odczytywać z PDF m.in.:

- nazwę produktu,
- kod produktu,
- producenta,
- datę,
- rewizję,
- wybrane dane bezpieczeństwa.

Automatyczne odczytanie danych nie oznacza ich zatwierdzenia.

Obowiązuje przepływ:

```text
PDF
   ↓
odczyt automatyczny
   ↓
propozycja danych
   ↓
weryfikacja użytkownika
   ↓
zatwierdzony rekord SDS
```

Parser nie ustala samodzielnie statusu `CURRENT`.

---

## 17. Historia

System zachowuje historię:

- wszystkich zarejestrowanych SDS,
- zmian `CURRENT → ARCHIVED`,
- dat rejestracji,
- danych rewizji i dat dokumentu,
- dostępności pliku,
- relacji z produktem,
- powiązanych decyzji BHP.

Archiwizacja nie oznacza fizycznego usunięcia rekordu ani pliku.

---

## 18. Reguły integralności

1. SDS zawsze posiada `sds_id`.
2. SDS zawsze jest przypisany do istniejącego `PRODUCT`.
3. Nowy rekord SDS wymaga fizycznego PDF.
4. Jeden `PRODUCT` ma maksymalnie jeden `CURRENT`.
5. Zatwierdzenie nowego `CURRENT` archiwizuje poprzedni `CURRENT`.
6. Rewizja i data są metadanymi, a nie identyfikatorem.
7. Aktualność wynika z decyzji użytkownika.
8. Brak pliku po rejestracji nie usuwa rekordu SDS.
9. `document_status` i `file_status` są niezależne.
10. System nie rozstrzyga automatycznie duplikatów.
11. Nowy zatwierdzony SDS wymaga nowej decyzji BHP.
12. Poprzednia decyzja BHP pozostaje w historii.
13. Nowa decyzja BHP odnosi się do nowego `sds_id`.

---

## 19. Ograniczenia dla implementacji

Codex nie może:

- utożsamiać SDS z `PRODUCT`,
- używać nazwy pliku jako identyfikatora SDS,
- ustalać aktualności wyłącznie po dacie lub rewizji,
- dopuścić więcej niż jednego `CURRENT` dla jednego produktu,
- usuwać rekordu SDS po utracie fizycznego pliku,
- automatycznie scalać duplikatów,
- automatycznie przenosić decyzji BHP na nowy SDS,
- modyfikować fizycznych dokumentów źródłowych,
- tworzyć rekordu SDS bez fizycznego PDF,
- tworzyć rekordu SDS bez produktu.

---

## 20. Rozstrzygnięcie IR

### IR-001-10
**Co jednoznacznie identyfikuje dokument SDS niezależnie od nazwy pliku?**

Status: **Resolved**

Decyzja: własny niezmienny `sds_id`.

### IR-001-11
**Jaka reguła określa aktualną kartę SDS?**

Status: **Resolved**

Decyzja: dokument zatwierdzony przez użytkownika jako `CURRENT`; maksymalnie jeden `CURRENT` na produkt.

### IR-001-12
**Jak postępować z SDS bez numeru rewizji lub bez jednoznacznej daty wersji?**

Status: **Resolved**

Decyzja: rewizja i data są opcjonalnymi metadanymi; brak tych danych nie blokuje rejestracji, jeśli istnieje PDF i produkt.

### IR-001-13
**Jak wykrywać i obsługiwać duplikaty dokumentów SDS?**

Status: **Resolved**

Decyzja: brak zaawansowanej deduplikacji; konflikt jest komunikowany użytkownikowi do ręcznego uporządkowania katalogu.

### IR-001-14
**Jak obsługiwać kilka wersji językowych tej samej rewizji SDS?**

Status: **Resolved**

Decyzja: brak osobnego mechanizmu wariantów językowych w MVP; każdy zatwierdzony PDF posiada własny `sds_id`.

### IR-001-15
**Czy i kiedy poprzednia karta otrzymuje status archiwalny/nieaktualny?**

Status: **Resolved**

Decyzja: zatwierdzenie nowego SDS jako `CURRENT` powoduje automatyczne przejście poprzedniego `CURRENT` do `ARCHIVED`.

---

## 21. Konsekwencje decyzji

### Pozytywne

- prosty model wersjonowania,
- jednoznaczna historia dokumentów,
- brak zależności od sposobu numerowania rewizji przez producenta,
- zachowanie audytowalności po fizycznym usunięciu pliku,
- jasne powiązanie nowej wersji SDS z koniecznością ponownej decyzji BHP,
- ograniczenie niepotrzebnej złożoności systemu.

### Ograniczenia

- użytkownik odpowiada za porządek i identyfikowalność katalogu źródłowego,
- system nie rozstrzyga automatycznie duplikatów,
- warianty językowe nie mają osobnego modelu w MVP.

---

## 22. Powiązane dokumenty

BDR-003 jest zgodny z:

- CORE-001,
- BDR-001,
- BDR-002,
- ADR-003,
- PDP-001,
- Konstytucją projektu.

BDR-003 stanowi podstawę do opracowania:

**BDR-004 — Decyzja BHP, jej zakres i historia.**

---

## 23. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zdefiniowano identyfikację SDS, CURRENT/ARCHIVED, dostępność pliku, obsługę duplikatów, brak wymagania rewizji/daty oraz obowiązek nowej decyzji BHP po zatwierdzeniu nowego SDS |
