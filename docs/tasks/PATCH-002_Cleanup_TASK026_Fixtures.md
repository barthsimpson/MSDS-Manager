# PATCH-002 — Cleanup fixture TASK-026 z bazy operacyjnej

**Projekt:** MSDS Manager  
**Status:** READY  
**MODE:** PATCH / MAINTENANCE  
**VALIDATION:** LEVEL 1  
**REPORT:** SHORT  
**Wykonawca:** Codex OpenAI

## GOAL

Usunąć z operacyjnej bazy `msds_manager` wyłącznie dane testowe pozostawione po TASK-026 wraz z ich powiązaniami, w jednej kontrolowanej transakcji.

Po wykonaniu baza biznesowa ma być pusta.

Bez zmian kodu aplikacji, schema, migracji ani zależności.

---

## AUTHORITATIVE CONTEXT

Przeczytaj tylko:
- root `AGENTS.md`,
- `GOV-002_Lean_Codex_Task_Optimization_v1.0-approved.md`,
- ten PATCH,
- `TASK-026_REPORT.md` wyłącznie w celu identyfikacji fixture TASK-026.

Nie czytaj ponownie CORE/BDR/TDR/Sprintów, jeśli nie pojawi się konkretna sprzeczność.

---

## KNOWN FACTS

W operacyjnej bazie widoczne są rekordy testowe o identyfikatorach/nazwach zawierających wzorzec:

```text
task026-
TASK-026
```

Przykładowo:

```text
task026-product-...
task026-manufacturer-...
TASK-026 Product ...
TASK-026 Manufacturer ...
```

Nie zakładaj jednak, że tylko PRODUCT i MANUFACTURER istnieją.

Najpierw zidentyfikuj wszystkie rekordy powiązane relacyjnie z fixture TASK-026.

---

## DO

### 1. Identyfikacja

Wykonaj wyłącznie odczyt diagnostyczny bazy i ustal, które rekordy należą do fixture TASK-026.

Uwzględnij wszystkie powiązane tabele biznesowe, jeśli zawierają rekordy dla tych identyfikatorów, np.:

```text
PRODUCT
MANUFACTURER
SDS
SAFETY_PROFILE
SDS_COMPONENT
BHP_DECISION
DECISION_EVIDENCE
PRODUCT_USAGE_LOCATION
PRODUCT_HISTORY
inne istniejące powiązania
```

Nie usuwaj niczego na podstawie luźnego podobieństwa nazw.

Podstawą musi być:
- jednoznaczny wzorzec fixture TASK-026,
- albo relacja FK do jednoznacznie zidentyfikowanych rekordów TASK-026.

### 2. Safety check

Przed DELETE pokaż/zanotuj liczbę rekordów TASK-026 per tabela.

Jeżeli znajdziesz jakiekolwiek rekordy, których przynależność do TASK-026 nie jest jednoznaczna:

```text
STOP / BLOCKED
```

Nie zgaduj.

### 3. Cleanup

Usuń wyłącznie fixture TASK-026 w prawidłowej kolejności zależności FK.

Wykonaj całość w jednej transakcji:

```text
BEGIN
→ delete children
→ delete parents
→ verify
→ COMMIT
```

Jeżeli dowolny krok zawiedzie:

```text
ROLLBACK
```

Nie używaj `ON DELETE CASCADE` jako nowej zmiany schema.

Nie twórz publicznego delete use case.

### 4. Final verification

Po cleanup potwierdź:

```text
PRODUCT count = 0
MANUFACTURER count = 0
```

oraz że pozostałe tabele biznesowe związane z fixture nie zawierają rekordów TASK-026.

Jeżeli baza zawiera inne, nietestowe dane:

```text
STOP
```

i nie wykonuj cleanupu, chyba że użytkownik jawnie potwierdzi ich usunięcie.

Celem tego PATCH-a jest wyłącznie usunięcie fixture TASK-026, nie "wyzerowanie" dowolnej bazy za wszelką cenę.

---

## EXPECTED CHANGE SURFACE

```text
DATABASE DATA ONLY
```

Nie zmieniaj:

```text
app/
tests/
migrations/
pyproject.toml
.env
schema
Alembic
```

Dozwolony nowy plik:

```text
docs/task_reports/PATCH-002_REPORT.md
```

Nie twórz nowego skryptu cleanup, jeśli jednorazową operację można wykonać bezpiecznie istniejącymi narzędziami.

---

## DO NOT

Nie:
- modyfikuj kodu aplikacji,
- modyfikuj testów,
- zmieniaj fixture testowych w repo,
- uruchamiaj migracji,
- zmieniaj schema,
- wykonuj refaktoryzacji,
- usuwaj plików SDS/evidence poza bazą,
- wykonuj repo-wide review,
- analizuj historii Git,
- rozpoczynaj kolejnego Tasku.

---

## VALIDATION — LEVEL 1

Walidacja tylko dla operacji maintenance:

1. before counts per tabela dla TASK-026,
2. transakcyjny cleanup,
3. after counts,
4. potwierdzenie:
   - `PRODUCT = 0`,
   - `MANUFACTURER = 0`,
   - brak rekordów fixture TASK-026 w pozostałych tabelach biznesowych.

Nie uruchamiaj:
- pełnego pytest,
- integration suite,
- Alembic current/check,
- tymczasowego klastra PostgreSQL,

chyba że cleanup ujawni niespodziewany problem techniczny.

---

## STOP CONDITIONS

`STOP / BLOCKED`, jeżeli:

1. w bazie są dane nietestowe, które mogłyby zostać objęte cleanupem,
2. nie da się jednoznacznie odróżnić fixture TASK-026,
3. relacje FK są inne niż oczekiwane i bezpieczny cleanup wymaga zmiany schema/kodu,
4. operacja wymaga usunięcia plików źródłowych,
5. wymagane byłoby rozszerzenie zakresu poza jednorazowy cleanup danych.

---

## REPORT — SHORT

Utwórz:

```text
docs/task_reports/PATCH-002_REPORT.md
```

Format:

```text
STATUS: DONE / BLOCKED

IDENTIFIED:
- table: before count
- ...

CLEANUP:
- transaction: COMMIT / ROLLBACK
- deleted only TASK-026 fixture: YES / NO

FINAL STATE:
- PRODUCT:
- MANUFACTURER:
- remaining TASK-026 records:
- other business data preserved: YES / NO

CHANGES:
- application code: NONE
- tests: NONE
- schema/migrations: NONE
- dependencies: NONE

RISKS / DEVIATIONS:
- NONE / ...

OCZEKUJĘ NA JAWNE POLECENIE.
```

---

## AUTHORIZATION

Start dopiero po jawnym poleceniu:

```text
Wykonaj PATCH-002.
```
