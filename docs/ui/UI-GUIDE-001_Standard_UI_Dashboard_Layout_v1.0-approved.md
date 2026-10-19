# UI-GUIDE-001 — Standard UI / Dashboard Layout

**Projekt bazowy:** MSDS Manager  
**Dokument:** UI-GUIDE-001  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-10-19  
**Właściciel:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Zakres:** MSDS Manager oraz kolejne aplikacje korzystające z tego standardu UI  
**Implementacja:** dokument referencyjny; sam nie autoryzuje zmian w kodzie

---

## 1. Cel

UI-GUIDE-001 utrwala kierunek UI wypracowany i fizycznie zweryfikowany podczas:

```text
PATCH-015
PATCH-015-R1
PATCH-015-R2
PATCH-015-R3
```

Celem jest:

- zachowanie spójnego stylu kolejnych ekranów,
- ograniczenie projektowania widoków od zera,
- uniknięcie pionowego, formularzowego układu „surowego Streamlita”,
- wykorzystanie szerokości ekranu,
- minimalizacja przewijania,
- stworzenie wzorca również dla kolejnych aplikacji.

---

## 2. Zasada nadrzędna

Interfejs ma przypominać:

```text
nowoczesny dashboard biznesowy
```

a nie:

```text
surowy formularz Streamlit
```

Priorytet:

```text
1. czytelność
2. szybkość orientacji
3. wykorzystanie szerokości
4. jasna hierarchia akcji
5. minimalne przewijanie
6. spójność wizualna
```

---

## 3. Model MASTER → DETAIL

Domyślny wzorzec:

```text
LISTA / REJESTR
→ wybór obiektu
→ KARTA OBIEKTU
```

Przykład:

```text
Produkty
→ Otwórz kartę produktu
→ Karta produktu
```

### 3.1. Lista

Służy do:

- wyszukiwania,
- filtrowania,
- sortowania,
- porównania rekordów,
- szybkiego odczytu statusów,
- wejścia do szczegółów.

Nie pokazuje pełnych szczegółów pod tabelą.

### 3.2. Karta obiektu

Służy do:

- pracy na jednym rekordzie,
- akcji dotyczących tego rekordu,
- przeglądu statusów, dokumentów i relacji,
- lokalnej edycji.

Karta szczegółowa nie powinna być osobną pozycją głównego sidebaru.

---

## 4. Docelowe środowisko

Bazowy target:

```text
desktop
1920 × 1080
zoom 100%
```

Mobile nie jest bazowym targetem.

Większość kluczowych danych powinna być widoczna bez przewijania albo przy minimalnym scrollu.

---

## 5. Wykorzystanie przestrzeni

Preferować szerokość, nie wysokość.

Dobre:

```text
┌──────────────────────┬──────────────────────┐
│ Tożsamość            │ SDS / BHP            │
└──────────────────────┴──────────────────────┘
```

Unikać:

```text
Tożsamość
↓
SDS
↓
BHP
```

Pełną szerokość przeznaczać głównie dla:

- tabel,
- wykresów,
- list,
- danych wymagających porównania poziomego.

---

## 6. Referencyjna Karta obiektu

```text
HEADER OBIEKTU + STATUSY
ACTION BAR

┌──────────────────────┬──────────────────────┐
│ GŁÓWNA TOŻSAMOŚĆ     │ STATUS / DOKUMENTY   │
└──────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────┐
│ RELACJE / MIEJSCA / TABELA                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ DANE ADMINISTRACYJNE                        │
└─────────────────────────────────────────────┘
```

---

## 7. Header i Action Bar

Nagłówek ma pokazywać:

- nazwę obiektu,
- najważniejszy kontekst,
- kluczowe statusy,
- główne akcje.

Przykład:

```text
Cleaner prof
CX80 Polska · Kod producenta: Brak danych

[Oczekuje na BHP] [SDS: CURRENT] [Rewizja: 2.0]

[Uzupełnij kod] [Korekta] [Dodaj rewizję SDS] [Pobierz SDS] [Więcej]
```

Akcje powinny znajdować się wysoko, blisko obiektu i w jednym rzędzie.

---

## 8. Hierarchia przycisków

### Primary

`Dodaj`, `Zapisz`, `Przypisz`, `Uzupełnij`

Styl:

```text
stonowany fill
spokojny niebieski / granatowy
```

### Secondary

`Korekta`, `Pobierz`, `Dodaj rewizję`, `Edytuj`

Styl:

```text
secondary / tonal fill
```

### Neutral

`Anuluj`, `Powrót`

Styl:

```text
neutralny szary
```

### Danger

`Usuń`, `Archiwizuj`

Zasada:

- mniej eksponowane,
- preferowane w `Więcej akcji`,
- czerwony tylko dla działań destrukcyjnych.

---

## 9. Formularze

Przyciski formularza ustawiać poziomo:

```text
[Zapisz] [Anuluj]
```

zamiast:

```text
[Zapisz]
[Anuluj]
```

Formularze powinny:

- być krótkie,
- wykorzystywać kolumny,
- nie powielać akcji,
- ograniczać puste odstępy.

---

## 10. Sidebar

Każda pozycja:

```text
ikona + tekst
```

Referencyjne znaczenia:

```text
Produkty         → package / box
Dodaj SDS        → file-plus
Decyzja BHP      → shield-check
Stanowiska       → settings / gears
Widok nadzorczy  → eye / dashboard
Analizy          → chart
```

Nie używać emoji jako finalnego standardu.

Referencyjna skala:

- nagłówek sekcji: 14–15 px,
- pozycje menu: 15–16 px,
- ikony: 18–20 px.

---

## 11. Typografia

| Element | Zakres |
|---|---:|
| Główny tytuł obiektu | 30–32 px |
| Tytuł strony | 30–34 px |
| Nagłówek sekcji | 20–22 px |
| Wartości danych | 15–16 px |
| Etykiety pól | 14–15 px |
| Metadata / secondary | 13–15 px |
| Sidebar | 15–16 px |

Zasada:

```text
większa czytelność > większe puste odstępy
```

---

## 12. Dane read-only

Dane odczytowe rozkładać poziomo.

Preferowane:

```text
Opis użycia             Ograniczenia użycia
Typ odpadu              Kod odpadu
```

Dla danych administracyjnych obowiązuje referencyjny **Wariant B**:

```text
Dane administracyjne                         [Edytuj]

dane read-only
```

Bez dublującego expandera edycji.

---

## 13. Tabele

Tabela jest preferowanym sposobem prezentacji danych wielowierszowych.

Lista powinna typowo pomieścić około:

```text
10–15 wierszy
```

Dalsze rekordy mogą być przewijane.

Tabela powinna zachować:

- wyszukiwanie,
- sortowanie,
- statusy,
- czytelne kolumny.

---

## 14. Akcje przy tabelach

Akcja dotycząca dodania rekordu powinna być jednoznacznie związana z tabelą.

Jeżeli kontekst może być niejasny, preferować:

```text
[tabela]

[+ Dodaj]
```

Przykład:

```text
Miejsca stosowania
[tabela]

[+ Dodaj miejsce]
```

---

## 15. Statusy

Statusy mogą być prezentowane jako badge/chip, ale zawsze z tekstem.

Przykładowa semantyka:

```text
ACTIVE       → success / neutral-green
CURRENT      → info / neutral
PENDING      → warning
NO DECISION  → neutral
ERROR        → danger
```

Kolor nie jest jedynym nośnikiem informacji.

---

## 16. Brak danych / NULL

W UI używać:

```text
Brak danych
Brak decyzji
Brak przypisanych miejsc
```

Nie pokazywać użytkownikowi:

```text
NULL
None
```

---

## 17. Pola wymagane i opcjonalne

Pole wymagane:

```text
Nazwa produktu *
```

Pole opcjonalne:

```text
Kod producenta — opcjonalne
```

UI musi odpowiadać rzeczywistej walidacji Application.

---

## 18. Ikony

Preferowane:

- Material Symbols,
- ikony natywnie dostępne w używanym frameworku.

Nie dodawać nowej dependency tylko dla ikon bez zatwierdzenia.

Ikony mają wspierać funkcję, nie dekorację.

---

## 19. Kolorystyka

Standard:

```text
stonowana
biznesowa
dashboardowa
```

Kolor wspiera:

- hierarchię,
- status,
- akcję,
- ostrzeżenie.

Nie służy jako dekoracja.

---

## 20. Minimalizacja scrollowania

Przy projektowaniu każdego ekranu należy zadać pytanie:

```text
Czy te dane naprawdę muszą być ułożone pionowo?
```

Jeżeli nie:

```text
użyj kolumn / tabel / action row
```

---

## 21. Physical UX Review

Każda większa zmiana UI wymaga:

```text
TECHNICAL VALIDATION
+
PHYSICAL UX REVIEW
```

Minimalny physical review:

```text
1920×1080
zoom 100%
```

Sprawdzić:

- czytelność,
- fonty,
- hierarchię akcji,
- ilość scrollowania,
- sidebar,
- puste przestrzenie,
- dublowanie akcji,
- kontekst przycisków.

Testy AppTest nie zastępują oglądu fizycznego.

---

## 22. DO / DON'T

### DO

```text
master → detail
szerokie layouty
2 kolumny
tabele
akcje blisko obiektu
jedna funkcja = jedna akcja
stonowane kolory
ikony + tekst
czytelne statusy
```

### DON'T

```text
pełne szczegóły pod tabelą listy
pionowe formularze bez potrzeby
przyciski jeden pod drugim
emoji jako finalne ikony
duże puste przestrzenie
dublowanie Edytuj
destrukcyjne akcje jako primary
surowe NULL / None
przyciski oderwane od sekcji
```

---

## 23. Kolejne aplikacje

UI-GUIDE-001 jest referencyjny również dla kolejnych aplikacji.

Nie wymaga kopiowania ekranów 1:1.

Należy zachować:

- język wizualny,
- master-detail,
- hierarchię,
- typografię,
- sidebar,
- przyciski,
- zasady gęstości informacji,
- Physical UX Review.

Układ danych należy dostosować do domeny aplikacji.

---

## 24. Referencyjny ekran

Wzorzec:

```text
MSDS Manager
→ Produkty
→ Karta produktu
```

wypracowany przez:

```text
PATCH-015
PATCH-015-R1
PATCH-015-R2
PATCH-015-R3
```

Kierunek Physical UX:

```text
ACCEPTED
```

---

## 25. Governance

Przyszłe Taski / PATCH-e UI powinny:

- wskazywać `UI-GUIDE-001` jako authoritative UI context,
- jawnie opisywać odstępstwa,
- wymagać physical UX review dla istotnych zmian.

UI-GUIDE-001:

```text
nie zmienia Core
nie zmienia BDR/TDR
nie autoryzuje implementacji
```

---

## 26. Status dokumentu

```text
UI-GUIDE-001
VERSION: 1.0-approved
STATUS: APPROVED
IMPLEMENTATION AUTHORIZATION: NO
```

`UI-GUIDE-001 v1.0-approved` jest referencyjnym standardem UI dla MSDS Managera i kolejnych aplikacji.

---

## 27. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-19 | Draft | Pierwszy standard UI oparty na zaakceptowanym kierunku Produkty → Karta produktu i doświadczeniach PATCH-015 / R1 / R2 / R3 |
| 1.0-approved | 2026-10-19 | Approved | Architekt Operacyjny zatwierdził standard UI jako referencyjne źródło dla MSDS Managera i kolejnych aplikacji |
