# RAP-001 — Raport z analizy danych identyfikacyjnych dwóch kart SDS

**Adresat:** Cerbrus, Architekt projektu  
**Data raportu:** 2026-10-08  
**Zakres:** wyłącznie dane identyfikacyjne dwóch wskazanych plików PDF. Nie przeprowadzono porównania z MSDS Manager ani analizy składu, zagrożeń lub środków bezpieczeństwa.

## 1. Plik 3M Scotch-Weld DP-490

**Oryginalna nazwa pliku:** `3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf`

Na stronie 1, w pkt 1.1, jako produkt główny wskazano **3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Kit**. W pkt 1.3 jako dostawcę podano **3M Poland Sp. z o.o.** Dokument jest w języku polskim.

PDF zawiera trzy osobno oznaczone karty charakterystyki:

| Karta | Początkowa strona PDF | Data aktualizacji | Numer wersji | Miejsce odczytu |
|---|---:|---|---:|---|
| Zestaw: 3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Kit | 1 | `06/07/2023` | `13.00` | Nagłówek strony 1; nazwa produktu także w pkt 1.1. |
| Część B: 3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part B | 4 | `06/07/2023` | `14.00` | Nagłówek strony 4; nazwa produktu także w sekcji 1.1. |
| Część A: 3M™ Scotch-Weld™ DP-490 Black Structural Adhesive Part A | 27 | `26/04/2023` | `14.00` | Nagłówek strony 27; nazwa produktu także w sekcji 1.1. |

Nagłówek strony 1 podaje `17/11/2022` jako datę **zastępowanej** wersji karty zestawu. Data zawarta w nazwie pliku nie stanowi dowodu bieżącej daty SDS.

**Status: REQUIRES HUMAN REVIEW.** Jeden PDF obejmuje kartę zestawu oraz dwie karty jego części. Przed porównaniem z rekordem w MSDS Manager trzeba określić, której karty mają dotyczyć data i wersja.

## 2. Plik OPEX Acrylic Clear Metal Lacquer

**Oryginalna nazwa pliku:** `T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf`

| Pole | Wartość odczytana | Strona PDF | Sekcja lub miejsce odczytu |
|---|---|---:|---|
| Nazwa produktu | OPEX® Acrylic Clear Metal Lacquer | 1 | Sekcja 1.1, wiersz „Nazwa produktu”. |
| Kod produktu | `T82C13` | 1 | Sekcja 1.1, wiersz „Kod produktu”. |
| Producent i eksporter | The Sherwin-Williams Company | 1 | Sekcja 1.3, pod oznaczeniem „Mfg. in U.S.A and exported by”. |
| Przedstawiciel w UE | Valspar B.V. | 1 | Sekcja 1.3, pod oznaczeniem „EU Only Representative”. |
| Język dokumentu | Polski | 1 | Tytuł „Karta charakterystyki” oraz treść i nagłówki sekcji. |
| Data wydania / aktualizacji | `25, Listopad, 2022` | 1, 25 | Stopka „Data wydania/Data aktualizacji”. |
| Wersja | `8` | 1, 25 | Stopka „Wersja”. |

**Status: READY FOR COMPARISON.** Pola identyfikacyjne są jednoznaczne, a role obu podmiotów są określone w karcie.

## Wnioski dla architektury procesu

1. Jeden plik PDF może zawierać więcej niż jedną kartę SDS. Model danych powinien pozwalać przypisać nazwę produktu, datę i wersję do konkretnej karty wewnątrz pliku.
2. Przy każdym odczytanym polu warto zachować numer strony i sekcję lub miejsce odczytu. Nazwa pliku powinna służyć do identyfikacji pliku źródłowego, nie do ustalania wartości SDS.
3. Organizacje wymienione w sekcji 1.3 mogą pełnić różne role. Rola podmiotu powinna pozostać powiązana z jego nazwą.

## Pliki źródłowe

- `C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\sds_Work\3M(TM)SCOTCH-WELD(TM) DP-490 BLACK 17.11.2022 rew. 13.pdf`
- `C:\Users\bartosz.murawski\Projects\MSDS-Manager\docs\sds_Work\T82C13_SDS_Polish_PL 25, Listopad, 2022 rew. 8.pdf`
