# MAINT-001 — Cleanup po testach fizycznych MVP

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH / MAINTENANCE  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

---

## GOAL

Oczyścić środowisko robocze po zakończonym walkthrough MVP tak, aby dalsze testy funkcji rewizji SDS były prowadzone na czytelnym i kontrolowanym stanie danych.

Cleanup ma objąć wyłącznie jednoznaczne artefakty testowe i omyłkowe.

Nie zmieniaj kodu aplikacji.

---

## SCOPE

### A. Filesystem SDS

Usuń wyłącznie jednoznaczne pozostałości testowe:

```text
SDS_ROOT_PATH/task019/
```

oraz jego zawartość.

Nie usuwaj rzeczywistych SDS używanych do dalszych testów, w szczególności plików takich jak:

```text
30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
CX 80 XBAKE CLEANER rew. 01-08-2015.pdf
Cx80 XBRAKE CLEANER rew03 15.01.2025.pdf
CX80 TIRE PROTECTOR rew. 1.2 02.10.2018.pdf
WYCOFANE!!! Cyna-Pbfree-SnCu-SnCuAg-SnAgCu-SnAg rew 2.2.PL(1).pdf
```

Jeżeli nazwa lub pochodzenie pliku jest niejednoznaczne:

```text
STOP / DO NOT DELETE
```

### B. Baza danych

Zidentyfikuj rekordy utworzone podczas bieżącego walkthrough i wcześniejszych testów fizycznych.

Przed usunięciem pokaż w raporcie listę kandydatów z co najmniej:

```text
product_id
product_name
manufacturer
manufacturer_product_code
status
current SDS filename
usage locations count
BHP decision count
```

Usuń wyłącznie rekordy jednoznacznie testowe / omyłkowe.

W szczególności kandydatami mogą być rekordy powstałe wskutek błędnej ekstrakcji, np.:

```text
produkt z błędnym producentem
produkt z błędnym kodem producenta typu "odradzane"
duplikat produktu powstały podczas testu parsera
```

Nie usuwaj rekordu, jeżeli istnieje jakakolwiek wątpliwość, że może być traktowany jako właściwy rekord referencyjny do dalszych testów.

### C. Zależności

Kasowanie wykonuj w bezpiecznej kolejności child → parent, zgodnie z aktualnym modelem danych.

Preferuj jedną transakcję dla cleanup bazy.

Nie usuwaj plików SDS tylko dlatego, że usuwany jest rekord bazy.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:

- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten MAINT,
- bezpośrednio potrzebny model/repository do identyfikacji zależności.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów.

Nie wykonuj repo-wide discovery.

---

## DO

1. Zidentyfikuj artefakty `task019`.
2. Zidentyfikuj rekordy testowe/omyłkowe w bazie.
3. Jeżeli klasyfikacja jest jednoznaczna:
   - usuń artefakty `task019`,
   - usuń rekordy testowe/omyłkowe wraz z zależnościami,
   - pozostaw rzeczywiste pliki SDS w `SDS_ROOT_PATH`.
4. Zweryfikuj stan końcowy.
5. Nie zmieniaj kodu aplikacji.

---

## DO NOT

Nie:

- zmieniaj kodu,
- zmieniaj schema,
- uruchamiaj migracji,
- zmieniaj dependencies,
- usuwaj realnych SDS,
- usuwaj danych niejednoznacznych,
- poprawiaj rekordów zamiast je usuwać,
- twórz funkcji delete w UI,
- rozpoczynaj PATCH-006.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. nie można jednoznacznie odróżnić rekordu testowego od właściwego,
2. istnieją zależności, których bezpieczne usunięcie wymaga zmiany kodu/schema,
3. cleanup mógłby usunąć dane potrzebne do dalszego testu rewizji,
4. wykryte zostaną dane spoza zakresu walkthrough.

W takim przypadku niczego nie zgaduj.

---

## VALIDATION

Po cleanup potwierdź:

```text
task019/ absent
brak jednoznacznych rekordów testowych/omyłkowych
pozostawione rzeczywiste SDS nadal istnieją na dysku
brak zmian w kodzie
brak zmian schema/migrations/dependencies
```

Nie uruchamiaj pełnego pytest.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/MAINT-001_REPORT.md
```

Format:

```text
# MAINT-001 REPORT

STATUS:
DONE / BLOCKED

IDENTIFIED FILE ARTIFACTS:
- ...

IDENTIFIED DB RECORDS:
- ...

DELETED:
- ...

PRESERVED:
- ...

FINAL STATE:
- task019 removed: YES / NO
- ambiguous records remaining: YES / NO
- real SDS files preserved: YES / NO

CHANGES OUTSIDE SCOPE:
- code: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM PATCH-006.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj MAINT-001.
```
