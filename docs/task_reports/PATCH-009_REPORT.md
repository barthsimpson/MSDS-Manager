# PATCH-009 REPORT

STATUS: **DONE**

CHANGED:
- UI: etykieta issue_date we wszystkich widokach SDS to „Data wydania / rewizji SDS”; osobne opcjonalne pole ma etykietę „Rewizja SDS”.
- UI: główna tabela Produkty pokazuje kolumnę „Rewizja SDS” z CURRENT SDS.revision; dla NULL lub pustej wartości pokazuje „—”. UUID SDS nie jest pokazywany.
- Read model: bez zmian — istniejący SupervisoryProductRow i zapytanie PostgreSQL już udostępniały rewizję wyłącznie CURRENT SDS.
- Tests: focused AppTest dla obu formularzy, tabeli Produkty i widoków; test PostgreSQL potwierdza zapis daty bez numeru rewizji oraz ignorowanie rewizji ARCHIVED.

VALIDATION:
- Focused unit/UI/AppTest: 43 passed, 0 failed.
- Focused PostgreSQL integration: 3 passed, 0 failed; testowe zapisy wykonano w transakcji rollback.
- issue_date != NULL i revision = NULL: PASS.
- Rewizja CURRENT SDS w tabeli Produkty: PASS; brak rewizji → „—”; ARCHIVED nie wpływa na kolumnę.
- git diff --check dla zmienionych śledzonych plików: PASS.

SCOPE:
- schema change: NO
- migration: NONE
- Core change: NO
- parser change: NO
- lifecycle change: NO

DEVIATIONS:
- Wskazany w PATCH-009 dokument BACKLOG-001 nie występuje w repozytorium. Zakres UI-12/UI-13 jest potwierdzony w CHECKPOINT-006 i jawnie opisany w PATCH-009.

NEXT:
- READY. Oczekuję na jawne polecenie.
