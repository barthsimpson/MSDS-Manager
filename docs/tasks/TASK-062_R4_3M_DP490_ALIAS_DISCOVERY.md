# TASK-062-R4 — 3M DP-490: rozpoznanie trzech SDS i pakiet aliasow do zatwierdzenia

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — etap rozpoznania; bez aktywacji nowych aliasow  
**Decyzja Architekta:** 2026-11-10  
**Kontynuacja:** TASK-062-R3, bez nowego numeru TASK

## 1. Cel i oczekiwany rezultat

Rozszerzyc referencyjny Golden Set o rzeczywisty wielokartowy PDF 3M DP-490 i przygotowac **konkretna, oparta na tresci SDS macierz brakujacych etykiet / regulek**, umozliwiajaca identyfikacje kazdej z trzech logicznych kart (zestaw, Part B, Part A). Uzyc juz dzialajacego pipeline R3 i 9 aliasow ACTIVE do przeprowadzenia aktualnego przebiegu diagnostycznego. Wynik tego etapu to material do JEDNEJ decyzji Architekta, a nie kolejny ogolny precheck.

**Uwaga o granicy uprawnien:** TDR-012 i SDS-ALIAS-001 wymagaja dla nowego aliasu `CANDIDATE -> decyzja APPROVED -> test regresyjny -> ACTIVE`. Biezaca dyspozycja pozwala na obserwacje i propozycje, **nie** na samodzielne przyjecie nowych aliasow ani zmiane ich na ACTIVE. Po akceptacji macierzy odrebna kontynuacja R4 wdrozy zatwierdzone aliasy, regresje i ponowna ekstrakcje trzech DRAFT.

## 2. Podstawa

- TDR-012 v1.0-approved: segmentacja 1 PDF -> 1..N logicznych SDS; `document_key`, `page_range`; sekcje, dowody, G1/G2/G3; tylko ACTIVE w runtime.
- SDS-SCHEMA-001, SDS-JSON-001, SDS-ALIAS-001 (aktualne, zatwierdzone wersje w repo).
- TASK-062-R2/R3 i aktualna implementacja pipeline jako stan bazowy.
- BDR-005 v1.2-approved oraz CORE-001 v1.9-approved: producent jest propozycja dla operatora, nie decyzja Core; role zrodlowe pozostaja doslowne; PRODUCT nie jest zapisywany bez akceptacji.
- Decyzja Architekta: z operacyjnego `product_name` usuwa sie wylacznie `®` i `™`, ale `source_text`/doslowny dowod pozostaje niezmieniony.

## 3. Srodowisko i preflight (krotko)

Pracuj wylacznie w `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, lokalny `main`. Nie korzystaj z dodatkowych worktree, nie tworz galezi, nie uruchamiaj Dockera.

1. Potwierdz HEAD i zgodnosc z `origin/main`, uwzgledniajac zatwierdzajacy commit `7f6e86c70ea51e72ae6540d5e3def273395d5999`; zastanych plikow roboczych nie czysc.
2. Ustal rzeczywista lokalizacje oryginalnego PDF 3M DP-490 w repo/danych; pokaz SHA-256, liczbe stron i poziom czytelnosci warstwy tekstowej. **Nie wymyslaj sciezki.**
3. Potwierdz istnienie pipeline R3 i liste 9 ACTIVE. Jesli stanu nie da sie odtworzyc, STOP z krotkim opisem konkretnej przeszkody.

## 4. Zadanie

### A. Segmentacja i obserwacja wynikow

Przepusc oryginalny 3M DP-490 przez obecny extractor diagnostycznie, bez rejestracji do Core. Sprawdz trzy logiczne SDS: **zestaw**, **Part B**, **Part A**, kolejno zgodnie z rzeczywistym układem tresci PDF. Dla kazdego podaj `document_key`, `page_range`, strony poczatkowe i dowod odrebnosci. Nie wyprowadzaj czesci/nazwy/wydania z nazwy pliku.

### B. Evidence dla identyfikacji

Dla kazdej logicznej karty sprawdz docelowe pola PoC:
- nazwa produktu / oznaczenie czesci (oddziel od nazwy calego zestawu),
- kod produktu producenta (opcjonalny),
- biezaca data wydania/aktualizacji, nie data poprzedniej rewizji,
- rewizja / wersja,
- podmioty z ich **doslownymi rolami**: producent, producent-eksporter, dostawca, przedstawiciel UE (tylko gdy rzeczywiscie wskazano).

Dla kazdego pola podaj strone, sekcje/podsekcje, **krotki literalny cytat**, stan obecnego extractora i oczekiwane zachowanie. Stosuj `FOUND`, `NOT_FOUND`, `AMBIGUOUS`, `UNREADABLE`. Brak aliasu nie uprawnia do zgadywania ani do `FOUND` bez evidence. Nie przypisuj dostawcy jako pewnego producenta; moze byc kandydatem dla operatora z zachowaniem roli zrodlowej.

### C. Pakiet aliasow

Utworz macierz nowych `CANDIDATE` i ewentualnych bezpiecznych rozszerzen istniejacych aliasow: literalna etykieta, sekcja, pole docelowe, sposob laczenia wartosci, przypadki negatywne, przyklad z konkretnym logicznym SDS. Rozdziel **prosty alias tekstowy** od nowej reguly kontekstowej; nie powielaj aliasow, ktore juz sa ACTIVE. Dla kazdego kandydata zaproponuj test regresyjny obejmujacy granice miedzy kartami i nieprzenoszenie danych Part A <-> Part B <-> zestaw.

### D. Izolacja i kontrola

Mozesz uzyc aktualnego extractora i narzedzi odczytowych, a takze zapisac niewiazace artefakty diagnostyczne / raport w repo. Nie zmieniaj ACTIVE, matcherow produkcyjnych ani schematow, dopoki Architekt nie podejmie decyzji o macierzy. Sprawdz, czy istniejace testy R2/R3 sa nadal dostepne; przy braku zmian kodu nie wymagamy rozbudowanej regresji.

## 5. Kryteria akceptacji R4-1 ... R4-6

| ID | Wymaganie / dowod |
|---|---|
| R4-1 | Pierwotny katalog, `main`, SHA pliku i znany punkt wyjscia; brak nowych worktree. |
| R4-2 | Wykazane rzeczywiste 3 logiczne SDS wraz z `document_key`, `page_range` i dowodem segmentacji. |
| R4-3 | Dla kazdej karty kompletna macierz identyfikacyjna: stan, wartosc jesli uzasadniona, strona, sekcja, cytat oraz luka w ACTIVE. |
| R4-4 | Kandydaci aliasow/regul deduplikowani, z mapowaniem do kontraktu i konkretnymi przypadkami regresji; brak automatycznego ACTIVE. |
| R4-5 | Brak przenikania danych miedzy logicznymi SDS; nazwy plikow nie sa dowodem domenowym; role producent/dostawca i daty aktualna/historyczna rozdzielone. |
| R4-6 | Zero zapisow do PostgreSQL/Core, zmian UI, migracji, Safety, aktywacji aliasow i zmian PDF; wykonawca konczy raportem i STOP. |

## 6. Raport

Zapisz `TASK-062_R4_REPORT.md` w przyjetej lokalizacji raportow; dolacz zwarta macierz z dowodami z **trzech** kart, liczbe i liste nowych aliasow wymagajacych decyzji, liste faktycznie zmienionych plikow oraz wyniki R4-1..R4-6. Nie deklaruj gotowych, kompletnych DRAFT 3M, jezeli obecne aliasy jeszcze ich nie wspieraja.

**STOP:** po przekazaniu macierzy i raportu. Architekt zatwierdzi lub odrzuci konkretne aliasy, po czym w nastepnej kontynuacji R4 Codex wykona ich regresje/aktywacje i ponowny przebieg Evidence JSON DRAFT. Nie rozpoczynaj kolejnego etapu samodzielnie.
