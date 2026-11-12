# TASK-062-R7 — Paczka 3: korekty dat, dostawcy i powtórzonej rewizji WEICON

**Status:** READY / AUTHORIZED — decyzja Architekta z 2026-11-12
**TASK MODE:** PATCH (focused regression)
**Projekt:** MSDS Manager | **Wykonawca:** Codex
**Repozytorium:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący lokalny `main`, bez worktree i nowych gałęzi.
**Baza:** R5 CLOSED, commit `4188b4ffd6c293e97c4426fd42d6306b8d93a7ec`; R6 diagnostyka ACCEPTED (przed pracą sprawdź aktualny HEAD/status, niczego nie resetuj).

## 1. Źródła i zatwierdzone decyzje

- `docs/task_reports/TASK-062_R6_REPORT.md`, `TASK-062_R6_INVENTORY.md` — raport paczki 3, konkretne strony i cytaty.
- `docs/task_reports/TASK-062_R5_REPORT.md` — poprzednie zachowanie i regresja Golden Set.
- `config/sds_aliases.json` — A-001–A-013 ACTIVE; nie zwiększaj liczby aliasów, jeśli nie ma nowej etykiety.
- `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py` — znane punkty startowe; testy `tests/unit/test_task062_r2_aliases.py`, `tests/unit/test_task062_r3_evidence.py`, `tests/unit/test_task062_r5_3m_aliases.py`.
- Obowiązujące w repo: `AGENTS.md`, GOV-001, GOV-002, TDR-012, SDS-ALIAS-001, SDS-JSON-001, BDR-005 v1.2-approved, CORE-001 v1.9-approved (czytaj tylko właściwy fragment).
- **Decyzja Architekta:** zatwierdzone R6-C01, R6-C02, R6-C03. Dodatkowe rozstrzygnięcie: dla liczbowej daty `02/03/2022` przy braku jednoznacznego wyróżnika stosuj **polski odczyt DD/MM/YYYY = 2 marca 2022**, czyli `2022-03-02`, **nie** `2022-02-03` i nie `AMBIGUOUS` wyłącznie z powodu dwóch możliwych formatów.

## 2. Problem i cel

Diagnostyka czterech PDF `data/sds/Paczki/paczka3 silicon/` wykazała trzy problemy w dwóch SDS WEICON: (1) daty w stopkach (`Data wydania/Data aktualizacji`) rozpoznawane jako `AMBIGUOUS` mimo czytelnego bieżącego zapisu, (2) brak dostawcy, bo §1.3 ma nazwę w wierszu bezpośrednio po nagłówku, bez `Adres:`, (3) w `Silicone F` identyczna rewizja `3.01` z różnych miejsc tego samego SDS daje błędny stan `AMBIGUOUS`.

**Wynik:** naprawa trzech kontekstowych przypadków w istniejącym ekstraktorze, pełna ponowna ekstrakcja czterech SDS paczki 3, regresja powiązanych układów OPEX/SYLGARD/3M i raport. Nie dodawaj osobnego parsera WEICON ani nowego aliasu literalnego.

## 3. Wymagane zachowanie

### R6-C01 — wybór i interpretacja bieżącej daty

- Dla stopki WEICON §1.1/nagłówka `Data wydania/Data aktualizacji :10/20/2022   Data poprzedniego wydania :10/19/2022` wybierz **pierwszą, bieżącą datę**, nie poprzednią i nie `Data wydruku`; `10/20/2022` → `2022-10-20` (`MM/DD/YYYY`, ponieważ `20` nie może oznaczać miesiąca).
- Przy zapisie `02/03/2022`, w którym obie interpretacje są kalendarzowo poprawne i brak **jednoznacznej** wskazówki źródłowej określającej format, zastosuj zatwierdzony **polski priorytet DD/MM/YYYY** → `2022-03-02`, stan `FOUND` wraz z literalnym `source_text`, stroną i etykietą. Nie zastępuj tego `AMBIGUOUS` tylko dlatego, że istnieje interpretacja amerykańska.
- Zachowaj poprawność już obsługiwanych formatów (np. `25, Listopad, 2022`, `06/07/2023` w 3M zgodnie z dotychczasowym jednoznacznym kontekstem, `YYYY/MM/DD` DOWSIL). **Nie stosuj ślepo polskiego priorytetu do udokumentowanych odmiennych kontekstów.** Najpierw jawny format/niepodważalny wyróżnik, potem polski odczyt jako zatwierdzona reguła domyślna dla nierozstrzygniętych zapisów dzienno-miesięcznych.
- Nie używaj nazwy pliku do ustalania daty; nie wprowadzaj „naprawy” dat kalendarzowo niemożliwych; zachowaj stan problemowy i dowód zgodnie z istniejącym kontraktem.

### R6-C02 — dostawca WEICON

- W obrębie §1.3 `Dane dotyczące dostawcy karty charakterystyki` obsłuż nazwę w **następnym niepustym wierszu**: `WEICON GmbH & Co. KG` → `parties[].name`, `role=SUPPLIER`, `FOUND`, dowód z §1.3. Ogranicz ekstrakcję do bieżącego logicznego SDS.
- Zachowaj istniejący wariant 3M (`Adres:`) i SYLGARD (`IDENTYFIKACJA FIRMY`). Nie dopuszczaj pobrania ulicy, telefonu, e-maila, §1.4, copyright ani samoczynnej promocji `SUPPLIER` na `MANUFACTURER`.

### R6-C03 — zgodne powtórzenia rewizji

- Dla `Silicone F` wiele wystąpień `Wersja : 3.01` **w ramach tego samego logicznego SDS** → `FOUND`, wartość `3.01`, prawidłowy dowód źródłowy.
- Sprzeczne wartości rewizji pozostają do rozstrzygnięcia (`AMBIGUOUS`), nie wybieraj pierwszej bez uzasadnienia. Nie traktuj `12/12` (numeru strony), wersji transportu ani rewizji innego logicznego SDS jako wartości właściwej.

## 4. Zakres zmian i ograniczenia

**EXPECTED CHANGE SURFACE:** istniejący matcher/pipeline (tylko potrzebne fragmenty), właściwe testy unit/fixture, raport `docs/task_reports/TASK-062_R7_REPORT.md`. `config/sds_aliases.json` tylko gdy nieunikniona jest minimalna korekta konfiguracji **bez tworzenia nowych ACTIVE** — uzasadnij w raporcie. CLI zmieniaj jedynie przy bezpośredniej konieczności.

**DO NOT TOUCH:** Core/BDR/TDR, modele domenowe, PostgreSQL, ORM/migracje, UI, importer, kontrakty JSON, Safety/Components, inne paczki diagnostycznie, źródłowe PDF, OCR/LLM, architekturę aliasów. Nie czyść zastanych nieśledzonych plików. Bez zmian zachowania dotyczących tożsamości producenta; `SUPPLIER` pozostaje propozycją do zatwierdzenia przez człowieka.

## 5. Akceptacja

| ID | Wymaganie i dowód |
|---|---|
| R7-1 | Preflight: właściwe `main`, 13 istniejących ACTIVE, zachowane PDF oraz stan roboczy. |
| R7-2 | Oba WEICON mają `issue_date=2022-10-20` (`FOUND`) z właściwym dowodem bieżącej daty, nie `2022-10-19` i nie datą wydruku. |
| R7-3 | Test izolowany: `02/03/2022` → `2022-03-02` (`FOUND`) wg decyzji Architekta; `10/20/2022` → `2022-10-20`; wykluczenie dat niemożliwych oraz regresji istniejących formatów i kontekstów. |
| R7-4 | Oba WEICON: `SUPPLIER=WEICON GmbH & Co. KG`, `FOUND` z cytatem i stroną §1.3; testy negatywne dla ulicy/e-maila/§1.4 i brak promocji producenta. |
| R7-5 | P3-02 `revision=3.01`, `FOUND`, przy identycznych powtórzeniach; konflikt rewizji nadal `AMBIGUOUS`, bez numeru strony/transportu. |
| R7-6 | Ponowne CLI na całej paczce 3: 4 logiczne SDS, właściwe nazwy i kody (`105330`, `132000`, dla DOWSIL `NOT_FOUND`), DOWSIL daty/rewizje bez regresji, G1/G2/G3, `PENDING_REVIEW`, dowody bez mieszania między kartami. |
| R7-7 | Testy R2/R3/R5 + skupione R7 dla WEICON/negatywów są PASS; OPEX, 4 SYLGARD, 3M działają nie gorzej niż przed R7, zwłaszcza obecne daty i role. |
| R7-8 | Raport podaje zmienione pliki, każdą kontrolę, komendy i wyniki, odstępstwa/ryzyka; brak zmian Core/DB/UI/importera, JSON DRAFT wyłącznie w ignorowanym `tmp/`. |

## 6. Weryfikacja, Git, STOP

1. Wykonaj focused tests zmian R7 oraz regresję odpowiednich testów R2/R3/R5 (bez pełnego testowania całego repo, jeśli brak uzasadnionego wpływu).
2. Uruchom istniejący CLI na czterech oryginalnych PDF paczki 3 i odczytaj faktyczne wyjścia JSON/validation, nie tylko `pytest passed`. Wybrane wcześniejsze formaty zweryfikuj przez istniejące testy i/lub przebieg referencyjny stosownie do ryzyka.
3. Robocze Evidence JSON i walidacje pozostaw w ignorowanym `tmp/`.
4. Po pozytywnych testach dozwolony **kontrolowany commit i zwykły push** na istniejący `main`, wyłącznie plików R7, po sprawdzeniu staged diff. Podaj SHA/stan `origin/main`; nigdy `git add .`, force push, reset historii lub nowy worktree. Przy konflikcie STOP.
5. Raport: `docs/task_reports/TASK-062_R7_REPORT.md`, tabela R7-1...R7-8 i krótkie porównanie wyników paczki 3 **przed/po**, w tym test daty `02/03/2022`. W razie braku testów źródłowych PDF w środowisku jawnie oznacz nieprzeprowadzone kontrole.

**STOP** przy sprzeczności ze źródłami, konieczności zmiany kontraktu/Core, istotnej regresji, potrzebie interpretacji daty sprzecznej z jawnie zatwierdzoną zasadą lub problemie Git. Nie rozszerzaj zadania na paczkę 5 LOCTITE ani na integrację z aplikacją. Zakończ raportem i czekaj na decyzję Cerberusa/Architekta.
