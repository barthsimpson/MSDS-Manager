# TASK-027 — Streamlit „Widok nadzorczy”

**Projekt:** MSDS Manager  
**Task ID:** TASK-027  
**Sprint:** SPRINT-005 — R7 Widok nadzorczy  
**Status:** READY  
**Typ:** Presentation / Streamlit / AppTest  
**Wykonawca:** Codex OpenAI

## 1. Cel

Zbudować prosty ekran `Widok nadzorczy`, wykorzystujący gotowy read model z TASK-026.

> Użytkownik otwiera jedną stronę i widzi aktualny stan produktów oraz pozycje wymagające działania.

To jest tabela nadzorcza, nie dashboard BI.

## 2. Stan wejściowy

TASK-026 = DONE:

```text
SupervisoryProductRow       istnieje
ListSupervisoryProducts     istnieje
SqlAlchemySupervisoryQuery  istnieje
pytest                      162 passed
Alembic                     e0dd7d6468bf (head)
schema drift                none
```

Nie implementuj ponownie reguł TASK-026.

## 3. Źródła

Przeczytaj przed implementacją:
- root `AGENTS.md`,
- `SPRINT-005`,
- `TASK-026`,
- `TASK-026_REPORT.md`,
- aktualny `CORE-001`,
- istniejące ekrany Streamlit z TASK-020 i TASK-024.

Potrzeba zmiany Core/schema lub nowej decyzji biznesowej → `STOP`.

## 4. Architektura

```text
Streamlit
    ↓
ListSupervisoryProducts
    ↓
SupervisoryQueryPort
    ↓
SqlAlchemySupervisoryQuery
    ↓
PostgreSQL
```

Streamlit NIE:
- wykonuje SQL,
- importuje ORM,
- wybiera CURRENT SDS/BHP,
- sprawdza filesystemu,
- wylicza `requires_action`/`action_reasons`.

## 5. Nawigacja

Dodaj jedną pozycję:

```text
Widok nadzorczy
```

Nie przebudowuj nawigacji ani istniejących ekranów.

## 6. Tabela

Jedna główna tabela z kolumnami:

```text
Produkt
Producent
Kod producenta
Miejsca stosowania
SDS
Data SDS
Rewizja SDS
Status produktu
BHP
Warunki / uwagi
Wymaga działania
```

Jeden PRODUCT = jeden wiersz.

`usage_locations` pokaż razem w jednej komórce. Brak → `—`.

## 7. Prezentacja SDS

Wyłącznie formatowanie danych TASK-026:

- brak `current_sds_id` → `BRAK CURRENT SDS`
- CURRENT + brak pliku → `BRAK PLIKU SDS`
- CURRENT + plik dostępny → `CURRENT`

## 8. Prezentacja BHP

- decyzja APPROVED → `APPROVED`
- decyzja REJECTED → `REJECTED`
- brak `current_bhp_decision_id` → `BRAK DECYZJI`

Nie szukaj decyzji historycznych.

## 9. Wymaga działania

- `requires_action = False` → `OK`
- `requires_action = True` → połącz `action_reasons` w jednej komórce, np.
  `BRAK DECYZJI BHP; BRAK MIEJSCA STOSOWANIA`

Bez severity, scoringu i nowego systemu priorytetów.

## 10. Warunki / uwagi

Pokaż `current_bhp_notes`. Brak → `—`.

Nie analizuj treści.

## 11. Filtry

Tylko trzy:

1. `Wszystkie / Wymagają działania`
2. status produktu
3. miejsce stosowania

Produkt przechodzi filtr miejsca, jeżeli lokalizacja znajduje się w jego `usage_locations`.

Opcjonalnie można dodać proste `Szukaj produktu`, tylko jeśli jest trywialne. Nie jest częścią DoD.

## 12. Pusta baza

Jeżeli service zwraca pustą listę:

```text
Brak produktów do wyświetlenia.
```

To nie jest błąd.

## 13. Kontrolowany błąd

Jeżeli read-side zgłasza kontrolowany błąd (np. `SupervisoryReadError`):
- pokaż kontrolowany komunikat,
- nie próbuj naprawiać danych,
- nie buduj systemu incydentów.

## 14. Composition

Podłącz stronę przez istniejący composition/shell aplikacji i istniejące `load_settings`, session/infrastructure, `SqlAlchemySupervisoryQuery`, `ListSupervisoryProducts`.

Nie twórz drugiego composition root.

## 15. Read-only

Nie dodawaj edycji, przycisków zmiany statusu, SDS/BHP, lokalizacji, masowych operacji ani „napraw”.

## 16. Brak zmian

TASK-027:
- NO Core change
- NO schema change
- NO Alembic migration
- NO new dependencies
- NO zmian reguł TASK-026

## 17. AppTests

Pokryj co najmniej:

1. kompletny ACTIVE → wiersz + `OK`,
2. wymagający działania → pokazany powód,
3. wiele powodów → wszystkie w jednej komórce,
4. wiele miejsc → jeden wiersz,
5. filtr `Wymagają działania`,
6. filtr statusu,
7. filtr miejsca,
8. pusta baza,
9. kontrolowany błąd read-side.

Nie testuj ponownie w UI wyboru CURRENT, filesystemu ani reguł TASK-026.

## 18. Poza zakresem

Nie implementuj:
- dashboardów/wykresów/KPI,
- liczników management dashboard,
- ISSUE/workflow,
- severity/scoring,
- alertów/powiadomień,
- R8,
- REACH,
- AI/LLM/OCR,
- document preview,
- upload/download,
- edycji z tabeli.

## 19. Definition of Done

DONE gdy:
1. jest `Widok nadzorczy` w nawigacji,
2. jest jedna tabela,
3. dane pochodzą z `ListSupervisoryProducts`,
4. UI nie wykonuje SQL/ORM/filesystem/reguł,
5. jeden PRODUCT = jeden wiersz,
6. widoczne są wszystkie wymagane kolumny,
7. `OK` lub `action_reasons` są czytelne,
8. działają 3 filtry,
9. pusta baza działa,
10. kontrolowany błąd działa,
11. ekran jest read-only,
12. brak zmian Core/schema/Alembic/dependencies,
13. focused AppTests PASS,
14. pełna regresja PASS,
15. brak SAWarning,
16. Alembic bez driftu,
17. nie rozpoczęto kolejnego Tasku.

## 20. Weryfikacja

Uruchom focused AppTests i:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Baseline przed TASK-027: `162 passed`.

Oczekiwany Alembic:
`e0dd7d6468bf (head)` i `No new upgrade operations detected.`

## 21. Raport

Utwórz:

```text
docs/task_reports/TASK-027_REPORT.md
```

Raport: status, zmienione pliki, nawigacja, composition, tabela, SDS/BHP/action reasons, filtry, pusta baza, błąd, read-only, AppTests, pełny pytest, SAWarning, Alembic, brak zmian Core/schema, Git/bezpieczeństwo, odstępstwa.

Zakończ:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM KOLEJNEGO TASKU.
```

## 22. Autoryzacja

Start dopiero po poleceniu:

```text
Wykonaj TASK-027.
```
