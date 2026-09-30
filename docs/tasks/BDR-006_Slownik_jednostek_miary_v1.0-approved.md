# BDR-006 — Słownik jednostek miary

**Projekt:** MSDS Manager  
**Dokument:** BDR-006  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-09-29  
**Właściciel decyzji:** Architekt Operacyjny  
**Nadzór spójności:** Cerberus — Agent Architekt  

---

## 1. Cel decyzji

Celem BDR-006 jest ujednolicenie sposobu przechowywania i używania jednostek miary dla danych ilościowych przypisanych do relacji:

```text
PRODUCT × USAGE_LOCATION
```

Decyzja przygotowuje model danych pod dalszy rozwój aplikacji, w szczególności pod:

```text
ANALYTICS-02 — Zestawienie zbiorcze
ANALYTICS-03 — Stan na dzień
```

oraz eliminuje swobodne wpisywanie jednostek jako tekstu przez użytkownika.

---

## 2. Stan obecny

Obowiązujący Core przechowuje w `PRODUCT_USAGE_LOCATION`:

```text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Przy czym:

- `peak_quantity_value` jest obowiązkowe,
- `peak_quantity_unit` jest obowiązkowe,
- `monthly_consumption_value` jest opcjonalne,
- jeśli `monthly_consumption_value` jest podane, `monthly_consumption_unit` jest obowiązkowe,
- `0` jest poprawną wartością biznesową i nie oznacza braku danych,
- automatyczna konwersja jednostek pozostaje poza Core.

Obecne jednostki są przechowywane jako swobodny tekst.

Powoduje to ryzyko wariantów takich jak:

```text
l
L
litr
litry
szt
szt.
```

które utrudniają spójne raportowanie i przyszłe porównania wartości.

---

## 3. Problem biznesowy

Przyszłe raporty `Analizy` mają wykonywać porównania ilości, m.in.:

```text
MAX = 40 l
Stan na dzień = 45 l
Różnica = +5 l
```

Aby takie porównanie miało jednoznaczne znaczenie, jednostka nie może być dowolnym tekstem wpisywanym ręcznie.

Potrzebny jest jeden kontrolowany słownik jednostek.

---

## 4. Decyzja główna

W systemie zostaje wprowadzony wspólny słownik:

```text
UNIT_OF_MEASURE
```

Jednostka miary staje się kontrolowaną daną referencyjną.

Użytkownik nie wpisuje jednostki dowolnym tekstem.

Użytkownik wybiera jednostkę z aktywnego słownika.

---

## 5. Minimalny model biznesowy jednostki

Minimalna informacja o jednostce:

```text
UNIT_OF_MEASURE
├── unit_id
├── code
├── name
├── category
└── status
```

Znaczenie pól:

- `unit_id` — stabilny identyfikator jednostki,
- `code` — krótki kod prezentowany w danych ilościowych, np. `l`, `kg`, `szt`,
- `name` — pełna nazwa użytkowa, np. `litr`, `kilogram`, `sztuka`,
- `category` — rodzaj wielkości / sposób użycia jednostki,
- `status` — `ACTIVE` albo `INACTIVE`.

Dokładna reprezentacja techniczna pól, constraints i typów danych zostanie określona w TDR.

---

## 6. Kategorie jednostek

Minimalnie przewiduje się kategorie:

```text
VOLUME
MASS
COUNT
```

Przykłady:

| code | name | category |
|---|---|---|
| `l` | litr | VOLUME |
| `ml` | mililitr | VOLUME |
| `kg` | kilogram | MASS |
| `g` | gram | MASS |
| `szt` | sztuka | COUNT |

Lista jednostek nie jest zamknięta na poziomie BDR.

Dodanie kolejnej jednostki do zatwierdzonej kategorii nie wymaga zmiany logiki Core, o ile nie wprowadza nowych reguł przeliczania lub nowej semantyki biznesowej.

---

## 7. Jeden słownik dla danych ilościowych

Obowiązuje jeden wspólny słownik dla:

```text
peak quantity
monthly consumption
```

Nie tworzy się osobnych słowników jednostek dla MAX i zużycia miesięcznego.

Jednocześnie oba pola zachowują odrębną semantykę biznesową.

---

## 8. MAX i miesięczne zużycie

Jednostka ilości szczytowej/MAX jest przypisana do:

```text
peak_quantity_value
```

Jednostka miesięcznego zużycia jest przypisana do:

```text
monthly_consumption_value
```

BDR-006 nie zmienia obowiązujących zasad:

```text
peak_quantity_value
→ obowiązkowe dla relacji PRODUCT × LOCATION

monthly_consumption_value
→ opcjonalne
```

Jeżeli miesięczne zużycie nie jest podane:

```text
monthly_consumption_value = NULL
monthly_consumption_unit = NULL
```

Semantyka `0` i `NULL` pozostaje rozdzielona.

---

## 9. Brak automatycznej konwersji jednostek

System nie wykonuje automatycznych przeliczeń:

```text
kg ↔ g
l ↔ ml
```

Nie powstaje:

- silnik konwersji,
- tabela współczynników przeliczeniowych,
- automatyczne przeliczanie danych użytkownika,
- przeliczanie oparte na gęstości,
- automatyczna normalizacja ilości do jednostki bazowej.

Kategoria jednostki nie oznacza zgody na automatyczną konwersję.

Jej rolą jest uporządkowanie danych i przygotowanie spójnej prezentacji / walidacji.

---

## 10. Zasada dla `Stan na dzień`

Dla przyszłego raportu:

```text
ANALYTICS-03 — Stan na dzień
```

obowiązuje zasada:

> Jednostka ilości stwierdzonej podczas przeglądu jest taka sama jak jednostka MAX dla danego PRODUCT × LOCATION.

Przykład:

```text
MAX = 40 kg
Stan na dzień = wartość wpisywana również w kg
Różnica = liczona w kg
```

Użytkownik nie wybiera w `Stan na dzień` alternatywnej jednostki dla tej samej pozycji.

Dzięki temu:

```text
difference = observed_quantity - baseline_max_quantity
```

nie wymaga żadnego silnika konwersji.

---

## 11. Relacja do `Zestawienia zbiorczego`

`ANALYTICS-02 — Zestawienie zbiorcze` korzysta z jednostki MAX zapisanej dla relacji:

```text
PRODUCT × USAGE_LOCATION
```

Podpowiedź różnicy `+/-` po zatwierdzeniu `Stanu na dzień` jest prezentowana w tej samej jednostce.

Przykład:

```text
MAX: 40 l
Stan: 45 l
Różnica: +5 l
```

BDR-006 nie definiuje finalnego UX ani wyglądu raportu.

---

## 12. Status ACTIVE / INACTIVE

Jednostka może posiadać status:

```text
ACTIVE
INACTIVE
```

`ACTIVE`:

- może być wybierana przy nowych lub edytowanych danych.

`INACTIVE`:

- nie powinna być proponowana jako nowy wybór,
- może pozostać powiązana z istniejącymi lub historycznymi danymi.

Wycofanie jednostki nie może niszczyć ani przepisywać danych historycznych.

Fizyczne usuwanie jednostki posiadającej referencje nie jest dopuszczone jako standardowe zachowanie.

---

## 13. Dane historyczne

Wprowadzenie słownika jednostek nie zmienia istniejącej zasady historii danych PRODUCT × USAGE_LOCATION.

Zmiana jednostki MAX lub miesięcznego zużycia jest zmianą biznesowej informacji ilościowej i musi pozostać możliwa do odtworzenia zgodnie z obowiązującym mechanizmem historii.

Szczegółowa reprezentacja referencji do jednostki w tabelach historycznych zostanie ustalona technicznie w TDR.

---

## 14. Brak migracji danych z dotychczasowego pliku

Nie będzie wykonywana migracja danych biznesowych ze starego arkusza / starej bazy danych do nowego modelu.

Obowiązuje zasada:

```text
stare dane
→ nie są automatycznie importowane
→ nie są automatycznie mapowane
→ nie są automatycznie normalizowane
```

Dane zostaną ponownie wprowadzone ręcznie po przeglądzie.

Powód biznesowy:

> samo przeniesienie danych bez ich przeglądu utrwaliłoby wcześniejsze niepewne lub nieaktualne informacje.

BDR-006 nie wymaga budowy narzędzia importowego ani mechanizmu mapowania nazw jednostek ze starego Excela.

---

## 15. Techniczna migracja schematu

Brak migracji danych ze starego pliku nie oznacza rezygnacji z technicznej migracji schematu aplikacji.

Zmiana persistence będzie wymagała standardowej migracji Alembic:

```text
obecny schema
→ schema ze słownikiem UNIT_OF_MEASURE
```

Szczegóły dotyczące:

- tabel,
- FK,
- constraints,
- przejścia z obecnych pól tekstowych,
- obsługi lokalnych rekordów testowych,
- downgrade,
- seeding początkowych jednostek,

należą do TDR i Tasku implementacyjnego.

Nie należy projektować heurystycznej migracji danych legacy, której projekt nie potrzebuje.

---

## 16. Granice decyzji

BDR-006 nie wprowadza:

- automatycznej konwersji jednostek,
- magazynu,
- stanów magazynowych,
- przeliczania opakowań na masę lub objętość,
- przeliczania przez gęstość,
- importu starego Excela,
- edytora własnych współczynników konwersji,
- mechanizmu `Stan na dzień`,
- modelu snapshotów,
- finalnego UI `Analizy`.

Te obszary pozostają poza zakresem tej decyzji.

---

## 17. Wpływ na Core

BDR-006 zmienia sposób reprezentacji jednostek w modelu Core:

```text
BYŁO:
peak_quantity_unit: swobodny tekst
monthly_consumption_unit: swobodny tekst

MA BYĆ:
jednostka wskazywana z kontrolowanego UNIT_OF_MEASURE
```

Semantyka samych ilości pozostaje bez zmian.

Po zatwierdzeniu BDR-006 aktualny `CORE-001` powinien otrzymać odpowiednią rewizję, ponieważ obowiązujący Core opisuje jeszcze pola jednostek jako wartości tekstowe.

---

## 18. Konsekwencje decyzji

### Pozytywne

- jednolite jednostki w całej aplikacji,
- brak wariantów typu `L`, `litr`, `litry`,
- spójna baza dla `Analizy`,
- proste obliczanie różnic `+/-`,
- brak potrzeby silnika konwersji,
- łatwiejsze filtrowanie i raportowanie,
- możliwość wycofywania jednostek bez utraty historii,
- wspólny mechanizm dla MAX i miesięcznego zużycia.

### Ograniczenia

- użytkownik musi pracować w jednostce przypisanej do MAX podczas `Stan na dzień`,
- aplikacja nie przeliczy wartości wpisanej w innej jednostce,
- dodanie nowej semantyki jednostek może wymagać osobnej decyzji,
- potrzebna będzie zmiana schema i UI.

---

## 19. Powiązane dokumenty

BDR-006 wynika z i pozostaje powiązany z:

- `CORE-001_MSDS_Manager_v1.1-approved`,
- `BDR-002_MSDS_Manager_v1.2-approved`,
- `TDR-004_Mechanizm_historii_danych_Core_v1.0-approved`,
- `CHECKPOINT-006_SPRINT-006_UI_MVP_CLOSED`,
- `BACKLOG-001_MSDS_Manager_Post_CHECKPOINT-006`,
- Konstytucją projektu,
- zasadami governance projektu.

Po zatwierdzeniu BDR-006 wymagane będzie przygotowanie technicznej decyzji / projektu migracji oraz aktualizacji Core przed implementacją.

---

## 20. Decyzja zatwierdzona

Zatwierdzona decyzja:

```text
1. Wprowadzamy jeden centralny słownik UNIT_OF_MEASURE.

2. Jednostki nie są wpisywane dowolnym tekstem;
   użytkownik wybiera je ze słownika.

3. Jeden słownik obsługuje MAX i miesięczne zużycie.

4. Jednostki posiadają stabilną tożsamość oraz status ACTIVE / INACTIVE.

5. System nie wykonuje automatycznej konwersji jednostek.

6. W przyszłym `Stan na dzień` wartość obserwowana
   jest zawsze wpisywana w jednostce MAX.

7. Różnica względem MAX jest liczona wyłącznie
   w tej samej jednostce.

8. Nie wykonujemy migracji danych biznesowych
   ze starego Excela / starej bazy.

9. Dane produkcyjne zostaną wprowadzone ręcznie
   po przeglądzie.

10. Zmiana schema aplikacji zostanie wykonana
    standardową migracją Alembic.

11. BDR-006 nie implementuje `Analizy`,
    konwersji jednostek ani importu legacy.
```

---

## 21. Authorization boundary

BDR-006 v1.0-approved jest obowiązującym źródłem decyzji biznesowej dla obszaru jednostek miary.

Dokument:

```text
autoryzuje użycie decyzji jako podstawy do aktualizacji Core
autoryzuje przygotowanie TDR dla modelu technicznego i migracji
autoryzuje przygotowanie przyszłego Sprintu / Tasków
```

Nie stanowi jednak samodzielnej zgody na wykonanie zmian w repozytorium.

Implementacja nadal wymaga:

```text
zatwierdzonego zakresu technicznego
jawnego Sprintu / Tasku
jawnej autoryzacji wykonania dla Codexa
```

---

## 22. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-29 | Draft | Pierwsza wersja decyzji: centralny słownik jednostek, brak automatycznej konwersji, jednostka `Stan na dzień` dziedziczona z MAX, brak migracji danych legacy |
| 1.0-approved | 2026-09-29 | Approved | Architekt Operacyjny zatwierdził BDR-006 bez zmian merytorycznych |
