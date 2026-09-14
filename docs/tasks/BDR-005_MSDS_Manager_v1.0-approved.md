# BDR-005 — Profil bezpieczeństwa i zakres ekstrakcji danych z SDS

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-005  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-27  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel decyzji

BDR-005 definiuje zakres danych bezpieczeństwa odczytywanych z SDS, model `SAFETY_PROFILE` i `SDS_COMPONENT`, reguły językowe, prezentację danych, workflow ekstrakcji i akceptacji oraz zasady ręcznej edycji po zatwierdzeniu.

BDR-005 nie tworzy systemu eksperckiego i nie zastępuje źródłowego dokumentu SDS.

## 2. Zasada nadrzędna

Profil bezpieczeństwa i skład należą do konkretnego dokumentu SDS:

```text
PRODUCT
   |
   +-- SDS
        |
        +-- SAFETY_PROFILE
        +-- SDS_COMPONENT 1:N
```

Zmiana SDS może oznaczać zmianę profilu bezpieczeństwa i składu.

## 3. Zakres źródłowy ekstrakcji MVP

Automatyczna ekstrakcja danych bezpieczeństwa obejmuje:

- Sekcję 2 — Identyfikacja zagrożeń,
- Sekcję 3 — Skład/informacja o składnikach,
- Sekcję 11 — Informacje toksykologiczne.

Nie tworzymy strukturalnej kopii całego SDS. Oryginalny PDF pozostaje źródłem informacji poza zatwierdzonym zakresem ekstrakcji.

## 4. Sekcja 3 — składniki SDS

Dane składników ujawnionych w Sekcji 3 są przechowywane strukturalnie. Każdy składnik należy do konkretnego `sds_id`.

Minimalny model:

```text
SDS_COMPONENT
├── component_id
├── sds_id
├── component_name
├── cas_number
├── ec_number
├── reach_registration_number
├── concentration_text
├── classification_text
└── hazard_statements
```

Pola są zapisywane tylko w zakresie, w jakim występują i mogą zostać jednoznacznie odczytane z SDS. Brak wartości nie może być uzupełniany przez zgadywanie.

## 5. Znaczenie danych Sekcji 3

`SDS_COMPONENT` opisuje składniki ujawnione w karcie.

`SAFETY_PROFILE` opisuje produkt/substancję lub mieszaninę jako całość.

Nie wolno automatycznie utożsamiać zagrożenia składnika z klasyfikacją całego produktu.

## 6. Prezentacja Sekcji 3

Dane Sekcji 3:

- są dostępne w bazie,
- nie są domyślnie prezentowane w głównym widoku rejestru,
- są dostępne użytkownikowi na żądanie przy konkretnym produkcie/SDS.

Interfejs może udostępnić je np. poprzez funkcję `[ Skład / Sekcja 3 ]`, otwierając tabelę lub okno szczegółów. BDR nie przesądza technicznej formy kontrolki UI.

## 7. SAFETY_PROFILE — zakres Sekcji 2 i 11

Minimalny zakres:

| Pole | Znaczenie | Źródło |
|---|---|---|
| `product_definition` | substancja / mieszanina | 2.1 |
| `hazardous_classification_status` | czy produkt jako całość jest sklasyfikowany jako niebezpieczny | 2.1 |
| `clp_classification_text` | klasyfikacja CLP produktu | 2.1 |
| `signal_word` | hasło ostrzegawcze | 2.2 |
| `hazard_statements` | zwroty H dotyczące produktu | 2.2 |
| `supplemental_hazard_statements` | zwroty/informacje uzupełniające, np. EUH | 2.2 |
| `pbt_status` | status PBT | 2.3 |
| `vpvb_status` | status vPvB | 2.3 |
| `carcinogenicity_status` | rakotwórczość | 11 |
| `germ_cell_mutagenicity_status` | działanie mutagenne na komórki rozrodcze | 11 |
| `reproductive_toxicity_status` | szkodliwe działanie na rozrodczość | 11 |
| `endocrine_section_2_status` | właściwości endokrynne wg Sekcji 2.3 | 2.3 |
| `endocrine_section_11_status` | właściwości endokrynne wg Sekcji 11.2.1 | 11.2.1 |
| `skin_sensitization_status` | działanie uczulające na skórę | 11 |
| `respiratory_sensitization_status` | działanie uczulające na drogi oddechowe | 11 |

## 8. Statusy informacji bezpieczeństwa

Dla właściwych pól stosujemy:

```text
YES
NO
NO_DATA
NOT_APPLICABLE
```

- `YES` — SDS jednoznacznie wskazuje występowanie cechy.
- `NO` — SDS jednoznacznie wskazuje brak cechy.
- `NO_DATA` — brak danych, informacja niedostępna lub brak możliwości jednoznacznego określenia.
- `NOT_APPLICABLE` — SDS jednoznacznie wskazuje, że zagadnienie nie ma zastosowania.

**`NO_DATA` nie może być interpretowane jako `NO`.**

## 9. Informacje endokrynne

Informacje z Sekcji 2.3 i 11.2.1 są przechowywane oddzielnie:

```text
endocrine_section_2_status
endocrine_section_11_status
```

System nie scala ich automatycznie i nie interpretuje, który wynik jest ważniejszy.

## 10. Dane poza SAFETY_PROFILE MVP

Nie strukturyzujemy w MVP pełnej Sekcji 11, w szczególności wszystkich LD50, LC50, ATE, pełnych opisów badań toksykologicznych ani wszystkich danych liczbowych ekspozycji. Pozostają one dostępne w PDF.

## 11. Reguła językowa SDS

MSDS Manager przyjmuje do rejestru wyłącznie SDS sporządzony w języku wymaganym w konfiguracji danego wdrożenia.

Dla obecnego wdrożenia:

```text
required_sds_language = PL
```

Model pozostawia możliwość wskazania innego wymaganego języka przy przyszłym wdrożeniu w innym kraju.

## 12. Brak właściwej wersji językowej

Jeżeli SDS nie jest w wymaganym języku:

- dokument zostaje odrzucony,
- nie tworzy się rekordu SDS w Core,
- nie tworzy się PRODUCT na podstawie odrzuconego dokumentu,
- nie uruchamia się właściwej ekstrakcji do Core.

Reguła „jest SDS → musi być PRODUCT” dotyczy dokumentu, który przeszedł walidację wejściową jako dopuszczalny SDS.

## 13. Zakaz tłumaczenia jako substytutu SDS

MSDS Manager nie tłumaczy obcojęzycznej karty charakterystyki w celu dopuszczenia jej do systemu.

Automatyczne tłumaczenie nie może zastąpić właściwej wersji językowej SDS, ponieważ mogłoby być źródłem błędu interpretacji treści bezpieczeństwa.

## 14. Język danych opisowych

Dane opisowe zachowują język wymaganego dokumentu. Dla obecnego wdrożenia są prezentowane po polsku.

Identyfikatory techniczne pozostają w standardowej postaci, np. `H315`, `CAS 111-76-2`, numer EC/WE i numer REACH.

## 15. Główny widok profilu bezpieczeństwa

Główny widok powinien udostępniać co najmniej:

- klasyfikację produktu jako niebezpieczny: TAK / NIE / BRAK DANYCH,
- hasło ostrzegawcze,
- kody zwrotów H,
- PBT,
- vPvB,
- rakotwórczość,
- mutagenność,
- toksyczność reprodukcyjną,
- właściwości endokrynne,
- działanie uczulające na skórę,
- działanie uczulające na drogi oddechowe.

`NO_DATA` musi być wizualnie i znaczeniowo odróżnione od `NO`.

BDR-005 nie definiuje kolorystyki interfejsu.

## 16. Poziomy prezentacji

Przyjmujemy trzy poziomy:

1. **Profil skrócony** — najważniejsze wskaźniki w głównym widoku.
2. **Szczegóły bezpieczeństwa** — pełniejsza klasyfikacja CLP, polskie opisy H, szczegóły Sekcji 2 i wybranych danych Sekcji 11, w tym oddzielne informacje endokrynne.
3. **Skład / Sekcja 3** — tabela składników dostępna na żądanie.

Użytkownik zachowuje możliwość otwarcia źródłowego PDF SDS.

## 17. Zasada ekstrakcji

Automatyczna ekstrakcja przygotowuje propozycję danych, a nie zatwierdzony rekord.

```text
PDF SDS
  ↓
walidacja wejściowa
  ↓
automatyczna ekstrakcja
  ↓
DRAFT
  ↓
weryfikacja użytkownika
  ↓
AKCEPTUJ / NIE AKCEPTUJ
```

## 18. Zakres draftu

Draft obejmuje jako jeden pakiet:

- dane identyfikacyjne produktu,
- producenta,
- metadane SDS,
- `SAFETY_PROFILE`,
- `SDS_COMPONENTS`.

Użytkownik ocenia całość przed zapisem do Core.

## 19. Akceptacja całego SDS

Użytkownik akceptuje albo odrzuca wynik ekstrakcji dla całego SDS.

Po `AKCEPTUJ` dane zostają zapisane do Core jako zatwierdzona reprezentacja dokumentu.

System zapisuje:

```text
approved_at
```

Akceptacja jest granicą kończącą automatyczne przetwarzanie tego SDS.

## 20. Odrzucenie draftu

Po `NIE AKCEPTUJ` draft nie jest zapisywany w Core.

Nie utrzymujemy w Core historii odrzuconych propozycji ekstrakcji.

Oryginalny plik pozostaje w katalogu zarządzanym przez użytkownika.

## 21. Brak confidence score

MVP nie przechowuje confidence score, procentowej pewności ekstrakcji ani automatycznych ocen „pewne/niepewne”.

Odpowiedzialność za zatwierdzenie propozycji danych spoczywa na użytkowniku.

## 22. Koniec automatycznego przetwarzania po akceptacji

Po zaakceptowaniu SDS system nie wykonuje ponownie automatycznej ekstrakcji ani reinterpretacji zatwierdzonych danych tego SDS.

Nie wolno w tle:

- ponownie analizować PDF,
- zmieniać zaakceptowanych wartości,
- „poprawiać” danych nową wersją parsera,
- uzupełniać pól bez świadomego działania użytkownika.

Nowy automatyczny proces dotyczy nowego dokumentu SDS.

## 23. Ręczna edycja po zatwierdzeniu

Po akceptacji użytkownik może ręcznie edytować dane zapisane w systemie dla poprawy czytelności lub lepszego odwzorowania treści dokumentu.

Zmiana:

- jest świadomą ingerencją użytkownika,
- odbywa się na odpowiedzialność użytkownika,
- nie modyfikuje PDF,
- nie uruchamia ponownej ekstrakcji,
- nie tworzy automatycznie nowego SDS.

System zapisuje:

```text
last_manual_edit_at
```

Brak ręcznej edycji:

```text
last_manual_edit_at = NULL
```

Każda kolejna ręczna edycja aktualizuje tę datę/czas.

## 24. Oryginał a reprezentacja danych

System rozróżnia:

```text
PDF SDS
= oryginalny dokument źródłowy

zaakceptowane dane w bazie
= zatwierdzona reprezentacja danych z dokumentu

ręcznie zmienione dane
= reprezentacja zmodyfikowana świadomie przez użytkownika
```

Ręczna edycja danych nie oznacza zmiany treści SDS.

## 25. Identyfikowalność na poziomie pól

MVP nie przechowuje dla każdego pola numeru strony, współrzędnych fragmentu PDF, cytatu źródłowego, osobnego fragmentu tekstu ani szczegółowej historii ekstrakcji pola.

Źródłem pozostaje cały PDF, a zakres ekstrakcji jest ograniczony do zatwierdzonych danych z Sekcji 2, 3 i 11.

## 26. Przygotowanie pod przyszły REACH

Dane Sekcji 3 mogą w przyszłości stanowić podstawę kontroli względem danych regulacyjnych:

```text
SDS_COMPONENT
     ↓
CAS / EC / REACH number
     ↓
zewnętrzny zestaw referencyjny
     ↓
MATCH / ALERT
```

BDR-005 nie definiuje jeszcze logiki oceny zgodności REACH.

Automatyczny alert regulacyjny nie może być utożsamiany z decyzją BHP.

## 27. Reguły integralności

1. `SAFETY_PROFILE` należy do konkretnego `sds_id`.
2. `SDS_COMPONENT` należy do konkretnego `sds_id`.
3. Zagrożenie składnika nie jest automatycznie klasyfikacją całego produktu.
4. `NO_DATA` nie oznacza `NO`.
5. Informacje endokrynne z Sekcji 2.3 i 11.2.1 są przechowywane osobno.
6. Do Core przyjmowany jest wyłącznie SDS w wymaganym języku.
7. Dla obecnego wdrożenia wymaganym językiem jest polski.
8. System nie tłumaczy SDS jako sposobu spełnienia wymagania językowego.
9. Wynik automatycznej ekstrakcji jest draftem.
10. Draft wymaga jawnej akceptacji użytkownika.
11. Odrzucony draft nie jest zapisywany w Core.
12. Po akceptacji kończy się automatyczne przetwarzanie danego SDS.
13. Późniejsze zmiany danych są wyłącznie ręcznymi zmianami użytkownika.
14. Ręczna edycja nie zmienia PDF.
15. Ręczna edycja aktualizuje `last_manual_edit_at`.
16. Brak ręcznej edycji oznacza `last_manual_edit_at = NULL`.
17. MVP nie przechowuje confidence score.
18. MVP nie przechowuje provenance na poziomie pojedynczych pól.
19. Dane Sekcji 3 nie są domyślnie prezentowane w głównym rejestrze.
20. Źródłowy PDF pozostaje nadrzędnym dokumentem źródłowym.

## 28. Ograniczenia dla Codexa

Codex nie może bez zatwierdzonej zmiany BDR:

- rozszerzać ekstrakcji na całą treść SDS jako strukturalny model,
- automatycznie tłumaczyć i przyjmować obcojęzycznego SDS,
- utożsamiać zagrożeń składnika z klasyfikacją produktu,
- zamieniać `NO_DATA` na `NO`,
- scalać automatycznie informacji endokrynnych z Sekcji 2 i 11,
- zapisywać draftu jako obowiązujących danych bez akceptacji użytkownika,
- przechowywać odrzuconych draftów w Core,
- ponownie analizować zaakceptowanego SDS w tle,
- automatycznie aktualizować zaakceptowanych danych po zmianie parsera,
- modyfikować źródłowego PDF,
- dodawać confidence score bez decyzji architektonicznej,
- budować historii źródła dla każdego pola bez decyzji architektonicznej,
- traktować przyszłego alertu REACH jako decyzji Specjalisty BHP.

## 29. Konsekwencje decyzji

### Pozytywne

- krótki i czytelny profil bezpieczeństwa,
- zachowanie danych składników do przyszłych analiz REACH,
- brak przeciążenia głównego widoku,
- jednoznaczne rozróżnienie `NO` i `NO_DATA`,
- kontrola człowieka nad wynikiem ekstrakcji,
- brak samoczynnej reinterpretacji zatwierdzonych danych,
- prosty model odpowiedzialności za ręczne zmiany,
- ochrona oryginalnego PDF,
- możliwość przyszłego wskazania innego wymaganego języka wdrożenia.

### Ograniczenia

- użytkownik musi zweryfikować cały draft przed akceptacją,
- brak confidence score,
- brak historii zmian poszczególnych pól,
- ręczna zmiana może spowodować różnicę między reprezentacją danych a literalną treścią PDF,
- szczegółowe dane toksykologiczne pozostają tylko w źródłowym dokumencie.

## 30. Elementy poza BDR-005

BDR-005 nie rozstrzyga:

- technologii/parsera ekstrakcji PDF,
- wykorzystania OCR,
- modelu AI/LLM,
- źródła referencyjnych danych REACH,
- algorytmu dopasowania CAS/EC/REACH,
- poziomów alertów regulacyjnych,
- szczegółowego projektu ekranów Streamlit,
- kolorystyki statusów,
- struktury pełnej Sekcji 11,
- mechanizmu automatycznej analizy całej karty.

## 31. Powiązane dokumenty

BDR-005 należy czytać łącznie z:

- CORE-001 v1.0-approved,
- BDR-001,
- BDR-002,
- BDR-003,
- BDR-004,
- ADR-003,
- TDR-001,
- TDR-002,
- TDR-003,
- PDP-001,
- ROADMAP-001,
- Konstytucją projektu.

## 32. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-27 | Approved | Zdefiniowano zakres Sekcji 2, 3 i 11, SAFETY_PROFILE, składniki SDS, regułę językową, prezentację danych, workflow ekstrakcji i akceptacji oraz zasady ręcznej edycji po zatwierdzeniu |
