# PATCH-015 — Rozdzielenie listy Produkty i Karty produktu + kompaktowy układ szczegółów

**Projekt:** MSDS Manager  
**Patch ID:** PATCH-015  
**MODE:** PATCH  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Wykonawca:** Codex OpenAI  

---

## 1. GOAL

Rozdzielić obecny ekran `Produkty`, który jednocześnie pokazuje tabelę i rozbudowane szczegóły zaznaczonego produktu, na dwa czytelne widoki:

```text
1. Produkty
   → tabela / lista produktów
   → wejście do Karty produktu

2. Karta produktu
   → pełny widok jednego PRODUCT
   → kompaktowy układ typu master-detail / monday.com
```

Dodatkowo poprawić pozostałość UI:

```text
Kod producenta *
→ Kod producenta — opcjonalne
```

Zmiana jest wyłącznie prezentacyjna / nawigacyjna.

Nie zmienia Domain, Application, Repository, schema ani lifecycle.

---

## 2. AUTHORITATIVE CONTEXT

Czytaj minimalnie:

1. `CORE-001_MSDS_Manager_v1.6-approved_BDR009.md`
2. `BDR-009_Opcjonalny_kod_producenta_i_tozsamosc_PRODUCT_v1.0-approved.md`
3. `TDR-013_Kontrolowany_import_Evidence_JSON_do_MSDS_Manager_v1.1-approved.md`
4. `TASK-051-R1_REPORT.md`
5. `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved`
6. root `AGENTS.md`

Nie rozszerzaj zakresu poza UI i nawigację.

---

## 3. KNOWN STARTING POINTS

Rozpocznij od:

```text
app/presentation/streamlit/product_registry.py
app/presentation/streamlit/add_sds.py
app/presentation/streamlit/composition.py
```

oraz bezpośrednio powiązanych testów Streamlit / AppTest dla rejestru produktów.

Jeżeli rzeczywiste nazwy są inne, znajdź wyłącznie bezpośredni odpowiednik.

---

## 4. DECISION — EKRAN `PRODUKTY`

Ekran `Produkty` ma pełnić wyłącznie rolę:

```text
LIST / SEARCH / SELECT / NAVIGATE
```

### 4.1. Zachować tabelę produktów

Tabela pozostaje głównym elementem ekranu.

Powinna nadal prezentować co najmniej obecne kolumny:

```text
Produkt
Kod producenta
Producent
Status
SDS
Rewizja SDS
BHP
```

Nie usuwaj danych ani istniejących statusów.

### 4.2. Przejście do Karty produktu

Każdy wiersz produktu otrzymuje jednoznaczną akcję:

```text
Otwórz kartę produktu
```

Preferowany wariant:

```text
mała ikona / przycisk w osobnej kolumnie Akcje
```

Dopuszczalne jest również kliknięcie nazwy produktu, jeżeli Streamlit / obecna tabela wspiera to stabilnie.

Wymaganie nadrzędne:

```text
użytkownik świadomie wybiera konkretny PRODUCT
→ przechodzi do Karty produktu
```

Nie opieraj na samej checkbox selection obecnego widoku, jeżeli powoduje to automatyczne rozwijanie szczegółów pod tabelą.

### 4.3. Usunąć szczegóły produktu spod tabeli

Na ekranie `Produkty` NIE renderować już pod tabelą:

```text
Tożsamość
SDS
BHP
Miejsca stosowania
Dane administracyjne
Akcje produktu
```

Tabela ma pozostać kompaktowa i samodzielna.

### 4.4. Akcje ogólne

Na ekranie listy mogą pozostać wyłącznie akcje dotyczące rejestru jako całości, np.:

```text
Dodaj SDS
```

Nie przenoś tu akcji specyficznych dla konkretnego PRODUCT.

---

## 5. DECISION — `KARTA PRODUKTU`

Karta produktu nie jest osobną pozycją w lewym sidebarze.

Wejście:

```text
Produkty
→ Otwórz kartę produktu
→ Karta produktu
```

Powrót:

```text
Produkty > <nazwa produktu>
```

lub równoważny, czytelny przycisk / breadcrumb:

```text
← Produkty
```

---

## 6. KARTA PRODUKTU — UKŁAD

Karta ma wykorzystywać szerokość ekranu i ograniczyć pionowe przewijanie.

### 6.1. Nagłówek produktu

Górny blok:

```text
Nazwa produktu
Producent
Kod producenta / Brak danych
Status używania
SDS status
Rewizja SDS
```

Po prawej, w jednym rzędzie:

```text
[Uzupełnij kod producenta]
[Korekta danych identyfikacyjnych]
[Dodaj nową rewizję SDS]
[⋯]
```

### 6.2. Warunkowość akcji

`Uzupełnij kod producenta`:

```text
widoczny tylko gdy manufacturer_product_code = NULL
```

`Korekta danych identyfikacyjnych`:

```text
widoczna zawsze dla istniejącego PRODUCT
```

`Dodaj nową rewizję SDS`:

```text
zgodnie z obecnymi regułami
```

Rzadkie / destrukcyjne akcje, np.:

```text
Usuń produkt
```

przenieść do:

```text
[⋯] / Więcej
```

lub pozostawić w osobnym, dyskretnym miejscu na dole Karty, jeśli menu technicznie nie jest uzasadnione.

Nie eksponować destrukcyjnej akcji na równi z podstawowymi akcjami.

---

## 7. KARTA PRODUKTU — SEKCJE

### 7.1. Wiersz 1 — dwie kolumny

```text
┌────────────────────────────┬────────────────────────────┐
│ TOŻSAMOŚĆ PRODUKTU         │ SDS I BHP                  │
└────────────────────────────┴────────────────────────────┘
```

#### Tożsamość produktu

Pokazać kompaktowo:

```text
Nazwa produktu
Kod producenta
Producent
Status użytkowania
```

Dla `NULL`:

```text
Kod producenta: Brak danych
```

#### SDS i BHP

Połączyć bieżące informacje SDS i BHP w jeden kompaktowy blok:

```text
Stan SDS
Rewizja SDS
Data wydania / rewizji
Plik SDS + Pobierz
Stan BHP
```

Nie zmieniać znaczenia danych.

---

### 7.2. Wiersz 2 — Miejsca stosowania

Szeroki blok:

```text
MIEJSCA STOSOWANIA                          [+ Dodaj miejsce]
```

Tabela pozostaje pozioma.

Nie renderować każdej właściwości miejsca jako osobnego pionowego pola.

---

### 7.3. Wiersz 3 — Dane administracyjne

Jeden kompaktowy blok:

```text
DANE ADMINISTRACYJNE                         [Edytuj]
```

Wewnątrz układ 2-kolumnowy, jeśli miejsce pozwala:

```text
Opis użycia              | Ograniczenia użycia
Typ odpadu               | Kod odpadu
```

Jeżeli występują istniejące informacje:

```text
Dane bezpieczeństwa
Składniki
```

mogą pozostać jako kompaktowe rozwijane elementy / linki w tej sekcji.

Nie rozwijaj automatycznie długich sekcji.

---

## 8. `DODAJ SDS` — KOD PRODUCENTA

Popraw etykietę:

```text
Kod producenta *
```

na:

```text
Kod producenta — opcjonalne
```

albo równoważnie:

```text
Kod producenta
(opcjonalne)
```

Pole nie może mieć oznaczenia `*`.

Nie zmieniaj Application / Domain — backend już poprawnie dopuszcza `NULL`.

---

## 9. ZACHOWANIE KONTEKSTU

Przy powrocie:

```text
Karta produktu
→ Produkty
```

preferowane jest zachowanie:

```text
filtrów
sortowania
```

oraz — jeśli obecna implementacja pozwala bez dodatkowej architektury:

```text
pozycji / zaznaczenia poprzedniego produktu
```

Nie buduj nowego mechanizmu persistence UI tylko dla PATCH-015.

Jeżeli zachowanie pełnego stanu wymagałoby większej przebudowy:

```text
zachowaj co najmniej filtry/sortowanie
```

lub pozostaw obecne zachowanie i odnotuj w raporcie.

---

## 10. ERGONOMIA

Cel:

```text
desktop 1920×1080
→ większość Karty produktu widoczna bez przewijania
→ minimalne pionowe przewijanie
```

Zasady:

- używać `st.columns` / obecnego mechanizmu kolumn,
- unikać szerokich pustych pasów,
- akcje grupować w jednym poziomym rzędzie,
- statusy pokazywać kompaktowo,
- brak zbędnych nagłówków pośrednich,
- sekcje rzadko używane zwijać,
- zachować czytelność przy zoom 100%.

Nie wprowadzaj custom framework / nowych dependency.

---

## 11. DO NOT

Nie zmieniaj:

```text
Domain
Application business rules
Repository
PostgreSQL schema
Alembic
PRODUCT identity rules
SDS lifecycle
BHP lifecycle
CURRENT / ARCHIVED
CODE_COMPLETION
CORRECTION semantics
JSON import
resolver
DRY RUN
```

Nie zmieniaj sidebaru poza tym, co niezbędne do nawigacji do Karty produktu.

Nie dodawaj pozycji:

```text
Karta produktu
```

do sidebaru.

---

## 12. VALIDATION — LEVEL 1

Uruchom focused UI/AppTest.

Potwierdź co najmniej:

```text
1. Produkty:
   - tabela renderuje się
   - szczegóły nie renderują się pod tabelą
   - istnieje akcja otwarcia Karty produktu

2. Karta produktu:
   - renderuje wybrany PRODUCT
   - posiada powrót do Produkty
   - akcje są w nagłówku
   - Tożsamość i SDS/BHP są obok siebie
   - Miejsca stosowania są tabelą
   - Dane administracyjne są kompaktowe

3. manufacturer_product_code = NULL:
   - „Brak danych”
   - widoczny „Uzupełnij kod producenta”

4. manufacturer_product_code != NULL:
   - brak przycisku „Uzupełnij kod producenta”

5. Dodaj SDS:
   - pole kodu nie ma *
   - oznaczone jako opcjonalne

6. Existing actions:
   - korekta identity działa
   - uzupełnienie kodu działa
   - dodanie rewizji SDS pozostaje dostępne
```

Nie uruchamiaj pełnego pytest.

---

## 13. PHYSICAL UX REVIEW

Po wykonaniu Codex ma zatrzymać się przed dalszymi zmianami.

Cerberus + Architekt wykonują fizyczny przegląd:

```text
Produkty
Karta produktu
Dodaj SDS
```

na zoom 100%.

PATCH nie jest finalnie przyjęty przed physical UX review.

---

## 14. STOP CONDITIONS

STOP / BLOCKED jeżeli:

1. rozdzielenie widoków wymaga zmiany Application API,
2. tabela nie pozwala stabilnie wskazać `product_id`,
3. Streamlit wymaga nowej dependency,
4. nawigacja wymaga przebudowy całego shell/router,
5. istniejący use case zostaje omijany przez UI,
6. akcje produktu musiałyby duplikować business logic,
7. poprawka zaczyna obejmować JSON import / TASK-052.

---

## 15. REPORT

Utwórz:

```text
docs/task_reports/PATCH-015_REPORT.md
```

Format:

```text
# PATCH-015 REPORT

STATUS:
DONE / BLOCKED

CHANGED:
- files

IMPLEMENTED:
- Products list-only view
- Product Card view
- header actions
- compact sections
- optional manufacturer code label

VALIDATION:
- focused AppTest
- related UI regression
- git diff --check

SCOPE:
- Domain change: NO
- Application change: NO
- schema change: NO
- migration: NONE
- new dependencies: NO

DEVIATIONS:
- NONE / list

NEXT:
- READY FOR PHYSICAL UX REVIEW
```

---

## 16. AUTHORIZATION

```text
PATCH-015
STATUS: READY
EXECUTION: NOT AUTHORIZED
```

Uruchomić dopiero po poleceniu:

```text
Wykonaj PATCH-015.
```
