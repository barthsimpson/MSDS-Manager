# BDR-001 — Tożsamość produktu chemicznego

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-001  
**Wersja:** 1.1-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Powiązane IR:** IR-001-04, IR-001-05, IR-001-06, IR-001-09  

---

## 1. Cel decyzji

Celem BDR-001 jest jednoznaczne zdefiniowanie, czym w MSDS Manager jest **produkt chemiczny**, jakie dane stanowią jego tożsamość oraz jak system ma odróżniać produkt od dokumentu SDS, jego wersji, informacji o bezpieczeństwie i statusu stosowania.

Decyzja stanowi element Core projektu i jest podstawą do późniejszego zaprojektowania modelu danych, relacji produkt–SDS oraz logiki importu i automatycznej ekstrakcji danych z kart charakterystyki.

---

## 2. Kontekst

Centralnym obiektem MSDS Manager jest produkt chemiczny stosowany lub rozważany do stosowania w przedsiębiorstwie.

Produkt nie może być utożsamiany z pojedynczym plikiem PDF ani z konkretną wersją karty charakterystyki.

Przykładowa karta SDS wskazuje dla produktu m.in.:

- nazwę produktu: `IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO`,
- kod produktu: `30470`,
- zastosowanie: `Farba lub inna podobna substancja`,
- ograniczenie zastosowania: `Jedynie do stosowania przemysłowego`,
- kolejną wersję dokumentu SDS z własną datą i numerem wersji.

Dane identyfikujące produkt i dane opisujące jego bezpieczeństwo występują w tej samej karcie SDS, ale pełnią różne role w systemie.

---

## 3. Definicja produktu

**Produkt chemiczny** jest trwałym obiektem biznesowym reprezentującym konkretną pozycję ewidencyjną produktu chemicznego.

Produkt posiada własną tożsamość niezależną od:

- konkretnego pliku SDS,
- numeru wersji SDS,
- daty wydania SDS,
- lokalizacji pliku PDF,
- decyzji BHP,
- miejsca stosowania,
- wyników analiz bezpieczeństwa.

---

## 4. Wewnętrzny identyfikator systemowy

Każdy produkt otrzymuje własny, niezmienny identyfikator systemowy:

`product_id`

`product_id` jest technicznym identyfikatorem rekordu w systemie.

Nie może być zastąpiony przez:

- nazwę produktu,
- kod produktu producenta,
- nazwę pliku,
- numer SDS.

---

## 5. Biznesowa identyfikacja produktu

Podstawowe dane identyfikacyjne produktu obejmują:

- `product_name` — nazwę handlową produktu,
- `manufacturer_product_code` — kod/numer produktu producenta lub dostawcy, jeśli występuje,
- powiązanie z producentem lub dostawcą zgodnie z przyszłym BDR.

Dla przykładu:

```text
product_name = IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO
manufacturer_product_code = 30470
```

Nazwa produktu i kod producenta są podstawowymi identyfikatorami biznesowymi, ale nie stanowią technicznego klucza głównego bazy danych.

---

## 6. Reguła nowej pozycji w bazie

W MSDS Manager przyjmuje się prostą regułę ewidencyjną:

> **Nowa nazwa produktu lub nowy numer/kod produktu oznacza nową pozycję `PRODUCT` w bazie.**

System nie próbuje automatycznie rozstrzygać, czy zmiana nazwy lub kodu była wyłącznie zmianą handlową producenta.

Jeżeli pojawia się:

- nowa nazwa,
- nowy numer produktu,
- nowy kod produktu,

tworzony jest nowy rekord `PRODUCT` z nowym `product_id`.

Poprzednia pozycja pozostaje w bazie wraz z historią dokumentów i decyzji.

Nie stosuje się mechanizmu automatycznego przepisywania poprzedniej tożsamości produktu na nową nazwę lub kod.

---

## 7. Zastosowanie produktu

Informacje dotyczące zastosowania są cechą produktu, ale nie stanowią jego tożsamości.

Przykładowe pola:

- `use_description`,
- `use_restriction`.

Dla przykładowej karty:

```text
use_description = Farba lub inna podobna substancja
use_restriction = Jedynie do stosowania przemysłowego
```

Zmiana zasadności stosowania produktu nie tworzy nowego `PRODUCT`.

W takim przypadku zmieniany jest **Status stosowania**.

---

## 8. Status stosowania produktu

Każdy produkt posiada pole:

`usage_status`

Status stosowania określa aktualny stan produktu w procesie firmowym.

Dopuszczalne statusy MVP:

### 8.1. `PENDING_APPROVAL`

**Przed dopuszczeniem**

Znaczenie:

- produkt jest zarejestrowany,
- SDS jest już w bazie,
- brak jeszcze akceptacji Specjalisty BHP.

Sugerowana prezentacja UI: **żółty**.

### 8.2. `ACTIVE`

**Dopuszczony / stosowany**

Znaczenie:

- produkt posiada wymaganą akceptację Specjalisty BHP,
- produkt jest dopuszczony do stosowania.

Sugerowana prezentacja UI: **zielony**.

### 8.3. `REJECTED`

**Niedopuszczony**

Znaczenie:

- Specjalista BHP podjął decyzję o niedopuszczeniu produktu,
- produkt pozostaje w bazie,
- jego SDS i dowód decyzji są zachowane.

Sugerowana prezentacja UI: **czerwony**.

### 8.4. `INACTIVE`

**Wyłączony ze stosowania**

Znaczenie:

- produkt był wcześniej stosowany lub dopuszczony,
- nastąpiło wyłączenie ze stosowania,
- produkt pozostaje w bazie wraz z historią.

Sugerowana prezentacja UI: **szary**.

Kolory są elementem prezentacji interfejsu i nie stanowią części logiki domenowej.

---

## 9. Cykl życia produktu

Podstawowy cykl statusów:

```text
SDS zarejestrowany
        ↓
PENDING_APPROVAL
      /      \
akceptacja   odmowa
   ↓          ↓
ACTIVE     REJECTED
   ↓
wyłączenie ze stosowania
   ↓
INACTIVE
```

Status `PENDING_APPROVAL` nie oznacza braku SDS.

Brak SDS jest odrębnym stanem kompletności dokumentacji i nie powinien być utożsamiany ze statusem stosowania.

---

## 10. Produkt a SDS

Produkt i SDS są odrębnymi obiektami.

Relacja domenowa:

```text
PRODUCT
   │
   └── 1 : N
       SDS_VERSION
```

Jeden produkt może posiadać wiele kolejnych wersji SDS.

Zmiana:

- daty SDS,
- numeru rewizji,
- treści karty,
- klasyfikacji bezpieczeństwa,

nie tworzy automatycznie nowego produktu, o ile nie zmienia się nazwa lub kod produktu zgodnie z regułą z sekcji 6.

---

## 11. Dane bezpieczeństwa

Dane opisujące bezpieczeństwo nie należą bezpośrednio do trwałej tożsamości produktu.

Są powiązane z konkretną wersją SDS.

Dotyczy to m.in.:

- klasyfikacji CLP,
- statusu „niebezpieczny / niesklasyfikowany”,
- hasła ostrzegawczego,
- zwrotów H,
- PBT/vPvB,
- rakotwórczości,
- mutagenności,
- szkodliwego działania na rozrodczość,
- właściwości zaburzających funkcjonowanie układu hormonalnego.

Model logiczny:

```text
PRODUCT
   │
   └── SDS_VERSION
          │
          └── SAFETY_PROFILE
```

Pozwala to zachować historię zmian profilu bezpieczeństwa w kolejnych wersjach SDS.

---

## 12. Automatyczna ekstrakcja danych z PDF

Aplikacja ma w MVP odczytywać z PDF karty SDS podstawowe dane identyfikacyjne produktu oraz wybrane dane bezpieczeństwa.

Automatycznie odczytane dane nie są od razu uznawane za zatwierdzone dane operacyjne.

Obowiązuje przepływ:

```text
PDF SDS
   ↓
AUTOMATYCZNA EKSTRAKCJA
   ↓
DANE ODCZYTANE
   ↓
WERYFIKACJA UŻYTKOWNIKA
   ↓
DANE ZATWIERDZONE
```

W szczególności parser może odczytać:

- nazwę produktu,
- kod produktu,
- zastosowanie,
- wybrane dane bezpieczeństwa.

Parser nie może samodzielnie zdecydować o utworzeniu nowego rekordu bez weryfikacji użytkownika.

Po zatwierdzeniu danych przez użytkownika obowiązuje reguła:

- nowa nazwa → nowy `PRODUCT`,
- nowy kod → nowy `PRODUCT`.

---

## 13. Niepewność i wartości brakujące

Dane bezpieczeństwa muszą rozróżniać co najmniej:

- `YES`,
- `NO`,
- `NO_DATA`,
- `NOT_APPLICABLE` — jeśli ma zastosowanie.

Wartość `Niedostępne` w SDS nie może zostać zapisana jako `NO`.

Przykład:

```text
carcinogenicity = NO_DATA
endocrine_disrupting = NO_DATA
```

jeżeli karta wskazuje brak dostępnych danych.

---

## 14. Relacja z producentem i dostawcą

Producent i dostawca pozostają odrębnym zagadnieniem domenowym.

BDR-001 ustala jedynie, że dane producenta/dostawcy mogą wspierać identyfikację produktu.

Nie rozstrzyga jeszcze:

- czy producent i dostawca są jednym typem encji,
- czy są dwoma rolami,
- czy relacja jest 1:N lub N:N.

Temat pozostaje do rozstrzygnięcia w IR-001-07.

---

## 15. Relacja z decyzją BHP

Decyzja BHP nie jest częścią tożsamości produktu.

Model logiczny:

```text
PRODUCT
   │
   ├── SDS_VERSION
   │
   └── BHP_DECISION
```

Decyzja BHP posiada własny status, datę, zakres, warunki oraz jeden dowód źródłowy w MVP.

`usage_status` i `BHP_DECISION` są odrębnymi informacjami:

- `usage_status` mówi, w jakim stanie stosowania znajduje się produkt,
- `BHP_DECISION` dokumentuje kto, kiedy, w jakim zakresie i na jakich warunkach podjął decyzję.

---

## 16. Konsekwencje decyzji

### Pozytywne

- prosta i jednoznaczna reguła ewidencyjna,
- brak automatycznych założeń o ciągłości produktu po zmianie nazwy lub kodu,
- zachowanie historii poprzednich pozycji,
- łatwe rozróżnienie produktów oczekujących, aktywnych, odrzuconych i wyłączonych,
- jasne oddzielenie statusu stosowania od statusu dokumentacji i decyzji BHP,
- możliwość prostego raportowania produktów wymagających działania.

### Koszty i ograniczenia

- zmiana nazwy lub kodu tworzy nowy rekord nawet wtedy, gdy producent traktuje produkt jako kontynuację poprzedniego,
- użytkownik musi zatwierdzić dane odczytane z SDS,
- nie przewiduje się automatycznego scalania rekordów.

---

## 17. Odrzucone warianty

### Wariant A — nazwa produktu jako klucz główny

Odrzucony.

Nazwa jest identyfikatorem biznesowym, nie technicznym kluczem bazy.

### Wariant B — kod producenta jako jedyny klucz produktu

Odrzucony.

Kod nie musi być globalnie unikalny i nie każdy produkt musi go posiadać.

### Wariant C — zachowanie tego samego `product_id` po zmianie nazwy lub kodu

Odrzucony.

W projekcie przyjęto regułę ewidencyjną: nowa nazwa lub nowy kod = nowa pozycja w bazie.

### Wariant D — jeden plik SDS = jeden produkt

Odrzucony.

Jeden produkt może posiadać wiele kolejnych wersji SDS.

### Wariant E — automatyczne tworzenie/scalanie produktów na podstawie PDF

Odrzucony dla MVP.

Automatyczne rozpoznanie ma charakter pomocniczy i wymaga zatwierdzenia użytkownika.

---

## 18. Ograniczenia dla implementacji

Codex nie może:

- użyć nazwy produktu jako technicznego klucza głównego,
- użyć kodu produktu jako jedynego identyfikatora systemowego,
- utożsamić produktu z dokumentem SDS,
- zapisać danych bezpieczeństwa jako niezmiennych cech `PRODUCT`,
- automatycznie scalać produktów,
- zachować tego samego `product_id` po zatwierdzonej zmianie nazwy lub kodu,
- automatycznie tworzyć nowego produktu bez zatwierdzenia użytkownika,
- interpretować `Niedostępne` jako `Nie`,
- utożsamiać `PENDING_APPROVAL` z brakiem SDS,
- usuwać `REJECTED` lub `INACTIVE` z bazy tylko dlatego, że nie są stosowane.

---

## 19. Rozstrzygnięcie IR

### IR-001-04

**Co dokładnie jest produktem chemicznym i co tworzy nowy produkt w systemie?**

Status: **Resolved**

Decyzja:
Produkt jest trwałym obiektem biznesowym reprezentującym konkretną pozycję ewidencyjną produktu chemicznego.

### IR-001-05

**Jaki identyfikator jednoznacznie identyfikuje produkt?**

Status: **Resolved**

Decyzja:
Każdy produkt posiada niezmienny `product_id`. Nazwa produktu i kod producenta są podstawowymi identyfikatorami biznesowymi.

### IR-001-06

**Czy zmiana nazwy handlowej tworzy nowy produkt, czy zmianę danych istniejącego produktu?**

Status: **Resolved**

Decyzja:
Nowa nazwa lub nowy numer/kod produktu oznacza utworzenie nowej pozycji `PRODUCT` z nowym `product_id`.

### IR-001-09

**Jakie statusy produktu są potrzebne i co oznaczają?**

Status: **Resolved**

Decyzja:
Dla MVP obowiązują cztery statusy stosowania:

- `PENDING_APPROVAL`,
- `ACTIVE`,
- `REJECTED`,
- `INACTIVE`.

---

## 20. Powiązane zagadnienia otwarte

BDR-001 nie zamyka:

- IR-001-07 — producent/dostawca,
- IR-001-08 — miejsca stosowania,
- IR-001-10 do IR-001-15 — szczegółowy model SDS,
- szczegółowej logiki decyzji BHP,
- zagadnień dotyczących zakresu minimalnej ekstrakcji SDS w MVP.

---

## 21. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zdefiniowano tożsamość produktu, `product_id`, relację produkt–SDS oraz zasadę weryfikacji danych odczytanych z PDF |
| 1.1-approved | 2026-08-25 | Approved | Zmieniono regułę tożsamości: nowa nazwa lub kod = nowa pozycja. Dodano `usage_status`: PENDING_APPROVAL, ACTIVE, REJECTED, INACTIVE |
