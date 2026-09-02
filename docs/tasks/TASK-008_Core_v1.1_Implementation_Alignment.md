# TASK-008 --- Core v1.1 Implementation Alignment

**Projekt:** MSDS Manager\
**Task ID:** TASK-008\
**Sprint:** SPRINT-002 --- Rejestr produktów i miejsc stosowania\
**Status wejściowy:** READY\
**Wykonawca:** Codex OpenAI\
**Nadzór:** Cerberus --- Agent Architekt\
**Akceptacja końcowa:** Architekt Operacyjny

## 1. Cel Tasku

Dostosować istniejącą implementację MSDS Manager do
`CORE-001 v1.1-approved` przed rozpoczęciem właściwych use case'ów
Sprintu 2.

Sekwencja:

``` text
Domain → ORM → Alembic → PostgreSQL → tests
```

TASK-008 wyłącznie wyrównuje istniejący kod i schemat do zatwierdzonego
Core. Nie implementuje workflow produktu, nowych
repozytoriów/application contracts ani UI.

## 2. Stan wejściowy

Po zaakceptowanym TASK-007: - PostgreSQL 17, baza `msds_manager`, -
Alembic: 2 rewizje, `bae33dc76391 (head)`, - 9 tabel aplikacyjnych, - 0
rekordów biznesowych, - constraints TASK-006 aktywne, - 18 enumowych
CHECK chronionych, - brak rzeczywistego driftu ORM ↔ DB, - 47 testów
przechodzi bez `SAWarning`, - `.env` lokalny i ignorowany, - pionowy
przebieg application → PostgreSQL działa.

## 3. Źródła nadrzędne

Implementacja musi być zgodna z: 1. `CORE-001 v1.1-approved`, 2.
`BDR-002 v1.1-approved`, 3. pozostałymi zatwierdzonymi BDR-001..005, 4.
`TDR-001..003`, 5. `SPRINT-002 v1.1-approved`, 6. zaakceptowanymi
rezultatami TASK-003..007, 7. root `AGENTS.md`.

Aktualny zatwierdzony Core ma pierwszeństwo przed starszym
kodem/Taskami. Codex nie tworzy nowych reguł. Potrzeba nowej decyzji =
**STOP**.

## 4. PRODUCT

Rozszerz Domain i ORM `Product` o opcjonalne:

``` text
waste_type
waste_code
```

Pola: - są informacyjne, - nullable, - nie należą do tożsamości
PRODUCT, - nie tworzą modułu odpadowego.

Nie twórz WASTE, słownika kodów, BDO, walidacji prawnej ani relacji
odpadowych.

Nie zmieniaj tożsamości:

``` text
product_name
manufacturer_product_code
manufacturer_id
```

TASK-008 nie implementuje jeszcze workflow blokowania edycji pól
tożsamości.

## 5. PRODUCT_USAGE_LOCATION

Zastąp:

``` text
quantity_value
quantity_unit
```

przez:

``` text
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
```

Po TASK-008 stare `quantity_value` / `quantity_unit` nie mogą być
aktywną częścią Domain, ORM ani aktualnego schematu PostgreSQL.

## 6. Reguły peak quantity

`peak_quantity_value`: - wymagane, - `Decimal`, - `>= 0`.

`peak_quantity_unit`: - wymagane.

`peak_quantity_value = 0` jest poprawną wartością biznesową i nie
oznacza NULL ani braku przypisania.

Nie używaj `Float`.

## 7. Reguły monthly consumption

`monthly_consumption_value`: - opcjonalne, - `Decimal`, - jeśli podane:
`>= 0`.

Semantyka:

``` text
NULL → brak zadeklarowanej informacji
0    → świadomie zadeklarowane zerowe zużycie
> 0  → dodatnie zużycie miesięczne
```

Spójność:

``` text
monthly_consumption_value IS NULL
↔ monthly_consumption_unit IS NULL
```

oraz:

``` text
monthly_consumption_value IS NOT NULL
↔ monthly_consumption_unit IS NOT NULL
```

Jednostka monthly nie musi być taka sama jak peak.

## 8. Jednostki i agregacja

Nie twórz słownika/enumu jednostek ani konwersji.

Zaktualizuj istniejącą regułę agregacji tak, aby korzystała wyłącznie z:

``` text
peak_quantity_value
peak_quantity_unit
```

Zachowaj: - sumowanie tylko zgodnych jednostek, - mixed units →
istniejący błąd domenowy, - brak automatycznej konwersji.

`monthly_consumption_value` nie może wpływać na peak factory quantity.

Jeżeli obecna czysta reguła domenowa nie zna statusu `USAGE_LOCATION`,
nie rozbudowuj TASK-008 o pobieranie aktywnych lokalizacji z bazy. To
należy do przyszłych use case'ów/repozytoriów.

## 9. Walidacja Domain

Domena ma odrzucać:

``` text
peak_quantity_value < 0
monthly_consumption_value < 0
monthly value bez unit
monthly unit bez value
```

Ma akceptować:

``` text
peak = 0
monthly = NULL + unit NULL
monthly = 0 + unit
```

Nie zmieniaj enumów ani modeli SDS/BHP.

## 10. ORM i PostgreSQL constraints

ORM ma reprezentować:

``` text
peak_quantity_value       NOT NULL
peak_quantity_unit        NOT NULL
monthly_consumption_value NULL
monthly_consumption_unit  NULL
```

Dodaj proste CHECK constraints:

``` text
peak_quantity_value >= 0
monthly_consumption_value IS NULL OR monthly_consumption_value >= 0
```

oraz:

``` text
(monthly_consumption_value IS NULL AND monthly_consumption_unit IS NULL)
OR
(monthly_consumption_value IS NOT NULL AND monthly_consumption_unit IS NOT NULL)
```

Nadaj constraints stabilne, czytelne nazwy.

Nie dodawaj innych UNIQUE/CHECK/FK/indexów „przy okazji". W
szczególności nie rozstrzygaj unikalności tożsamości PRODUCT,
producentów ani listy jednostek.

## 11. Trzecia migracja Alembic

Utwórz dokładnie jedną nową rewizję po:

``` text
bae33dc76391
```

Preferowana nazwa:

``` text
align_core_v1_1_product_usage
```

Stan końcowy:

``` text
Alembic revisions: 3
Application tables: 9
Current: TASK-008 revision (head)
```

Nie twórz nowych tabel.

## 12. Strategia migracji kolumn

Baza wejściowa ma 0 danych biznesowych, ale migracja ma być poprawna
semantycznie.

Ponieważ stare `quantity_*` oznaczały ilość maksymalną/szczytową,
preferuj:

``` text
quantity_value → peak_quantity_value
quantity_unit  → peak_quantity_unit
```

jako rename, a następnie dodaj:

``` text
monthly_consumption_value
monthly_consumption_unit
```

Jeżeli autogenerate proponuje DROP + ADD, przejrzyj i popraw migrację do
rename, jeśli technicznie właściwe. Nie używaj pustej bazy jako
uzasadnienia destrukcyjnej migracji.

## 13. Review migracji przed upgrade

`alembic revision --autogenerate` jest tylko propozycją.

Przed `upgrade head` przeczytaj migrację.

Dozwolone: - `products.waste_type`, - `products.waste_code`, - rename
`quantity_* → peak_quantity_*`, - pola monthly consumption, -
zatwierdzone CHECK constraints, - usunięcie/zastąpienie tylko starych
constraints bezpośrednio związanych ze zmienianymi kolumnami.

Niedozwolone: - nowe/usunięte tabele, - zmiany
SDS/BHP/SafetyProfile/SdsComponent, - zmiany enumów, - usunięcie
constraints TASK-006, - usunięcie 18 enumowych CHECK, -
historia/audyt, - seed data.

Nieoczekiwany drift poza znanym false positive = **STOP**.

## 14. Ochrona wcześniejszych constraints

Po TASK-008 nadal muszą działać: - jeden `CURRENT` SDS na PRODUCT, -
jedna `CURRENT` BHP decision na SDS, - zgodność PRODUCT + SDS w BHP
decision.

Nie zmieniaj ich nazw ani semantyki.

Zachowaj mechanizm ochrony 18 type-bound enumowych CHECK z TASK-006. Nie
poszerzaj filtra Alembic bez potrzeby.

## 15. Testy Domain

Dodaj/zmień testy: - Product akceptuje `waste_type=None`,
`waste_code=None`, - pola odpadowe przyjmują tekst, - peak `0`
poprawny, - peak ujemny odrzucony, - monthly `NULL/NULL` poprawne, -
monthly `0 + unit` poprawne, - monthly dodatnie + unit poprawne, -
monthly ujemne odrzucone, - monthly value bez unit odrzucone, - monthly
unit bez value odrzucone, - peak i monthly mogą mieć różne jednostki.

## 16. Test agregacji

Potwierdź: - agregacja używa peak quantity, - zgodne peak units są
sumowane, - `0` działa poprawnie, - mixed peak units są odrzucane
zgodnie z istniejącą regułą, - monthly consumption nie wpływa na
wynik, - brak konwersji jednostek.

## 17. Testy PostgreSQL

Na rzeczywistym PostgreSQL potwierdź: 1. peak `0` → dozwolone, 2. peak
`<0` → DB odrzuca, 3. monthly `NULL/NULL` → dozwolone, 4. monthly
`0 + unit` → dozwolone, 5. monthly `<0` → DB odrzuca, 6. monthly value
bez unit → DB odrzuca, 7. monthly unit bez value → DB odrzuca.

Nie używaj SQLite. Testy nie mogą pozostawiać danych.

## 18. Pełna regresja

Uruchom:

``` powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie istniejące testy po świadomym dostosowaniu do Core v1.1 oraz
nowe testy muszą przejść.

Nie usuwaj testów tylko dlatego, że używają starych nazw --- zaktualizuj
je do nowego znaczenia.

## 19. Upgrade / downgrade / re-upgrade

Po review:

``` powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Potwierdź: - 9 tabel, - 3 rewizje, - nowe kolumny obecne, - stare nazwy
nieobecne, - TASK-006 constraints obecne, - 18 enum CHECK obecne.

Następnie przetestuj:

``` text
TASK-008 head
↓
downgrade -1
↓
bae33dc76391
↓
re-upgrade head
```

Po downgrade: - 9 tabel, - stan schematu odpowiada TASK-007, - stare
`quantity_value` / `quantity_unit` przywrócone, - pola Sprintu 2
usunięte, - constraints TASK-006 zachowane.

Końcowy stan: nowy `head`.

## 20. Drift

Po finalnym re-upgrade:

``` powershell
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

``` text
No new upgrade operations detected.
```

Rozdziel znany false positive enum CHECK od rzeczywistego driftu.
Rzeczywisty drift nie może pozostać.

## 21. Poza zakresem TASK-008

Nie implementuj: - nowych application ports/use cases, - repozytoriów
Product/UsageLocation, - CRUD, - Streamlit, - formularzy/list/szczegółów
produktu, - workflow create/edit, - mechanizmu ochrony tożsamości w
application, - historii/audytu, - soft delete, - importu Excel, -
SDS/PDF/extraction, - Safety Profile/SdsComponent, - BHP, - REACH, -
magazynu, - modułu odpadów/BDO, - konwersji jednostek, - generic
repository, - Unit of Work, - event bus/CQRS, - nowych bibliotek.

Nie modyfikuj `ListManufacturers` / `ManufacturerRepositoryPort` z
TASK-007, o ile nie wystąpi techniczna konieczność wynikająca
bezpośrednio z tego Tasku.

## 22. Historia --- twarda granica

Nie twórz: - audit/history tables, - event log, - temporal tables, -
version columns, - triggerów historycznych, - `created_by` /
`updated_by`, - snapshotów.

Mechanizm historii jest nierozstrzygnięty i posiada bramkę przed
TASK-015. Potrzeba historii w TASK-008 = **STOP**.

## 23. Architektura i zależności

Zachowaj:

``` text
presentation → application → domain
infrastructure → application/domain
```

Domain nie importuje SQLAlchemy, psycopg, Alembic, Streamlit,
infrastructure ani `.env`.

Modele ORM pozostają w `app/infrastructure/db/models/`. Migracja
pozostaje w `migrations/versions/`.

Nie dodawaj bibliotek; `pyproject.toml` nie powinien wymagać zmian.

## 24. Git i bezpieczeństwo

Sprawdź:

``` powershell
git status --short
git diff --check
git diff --cached --check
```

Nie wykonuj commit/push bez jawnego polecenia.

Potwierdź: - `.env` ignored i untracked, - brak sekretów, - brak
dumpów/backupów, - brak SDS/BHP files, - brak danych testowych i
lokalnych artefaktów.

## 25. STOP

Raportuj `PARTIAL` albo `BLOCKED`, jeżeli: - stan repo/DB istotnie różni
się od wejściowego, - baza zawiera dane biznesowe wymagające osobnej
decyzji migracyjnej, - potrzebny jest model poza Core, - potrzebny jest
trigger lub historia, - trzeba zmienić enumy lub constraints TASK-006, -
autogenerate proponuje nieoczekiwane zmiany, - filtr Alembic maskuje
rzeczywisty drift nowych constraints, - potrzebna jest nowa
biblioteka, - istnieje konflikt CORE/BDR/TDR, - zakres wchodzi w
TASK-009/UI.

Nie obchodź problemu przez rozszerzenie zakresu.

## 26. Kryteria akceptacji

TASK-008 = DONE, jeżeli: 1. Product Domain ma opcjonalne `waste_type`,
`waste_code`, 2. ProductUsageLocation Domain ma cztery nowe pola
ilościowe, 3. stare `quantity_*` nie są aktywne w aktualnym modelu, 4.
peak jest `Decimal`, wymagane i `>=0`, 5. peak unit wymagane, 6. monthly
jest opcjonalne `Decimal`, jeśli podane `>=0`, 7. monthly value/unit
zachowują NULL/0, 8. agregacja jest peak-only, 9. brak konwersji
jednostek, 10. ORM zgodny z Core, 11. PostgreSQL wymusza zatwierdzone
constraints, 12. pola odpadowe są nullable, 13. istnieje dokładnie jedna
nowa migracja, 14. `down_revision = bae33dc76391`, 15. migracja
zreviewowana przed upgrade, 16. nadal dokładnie 9 tabel, 17. constraints
TASK-006 aktywne, 18. 18 enum CHECK poprawne, 19. upgrade działa, 20.
downgrade jednej rewizji działa, 21. re-upgrade działa, 22. baza kończy
na nowym head, 23. brak rzeczywistego driftu, 24. nowe testy
Domain/PostgreSQL przechodzą, 25. pełna regresja przechodzi bez
`SAWarning`, 26. brak danych testowych, 27. brak nowych bibliotek, 28.
brak historii, 29. TASK-009 nie rozpoczęty, 30. raport TASK-008
utworzony.

## 27. Wymagany raport

Utwórz:

``` text
docs/task_reports/TASK-008_REPORT.md
```

Raport zawiera: 1. Status `DONE` / `PARTIAL` / `BLOCKED`. 2. Stan
wejściowy. 3. Zmiany Domain. 4. Zmiany ORM. 5. Migrację: revision id,
nazwa, down_revision, upgrade/downgrade, rename. 6. Review migracji
przed upgrade. 7. Nazwy i semantykę nowych CHECK constraints. 8.
Potwierdzenie constraints TASK-006. 9. Potwierdzenie 18/18 enum CHECK.
10. Testy Domain. 11. Testy PostgreSQL. 12. Test agregacji. 13. Pełną
regresję i `SAWarning`. 14. Upgrade/downgrade/re-upgrade. 15. Finalny
stan PostgreSQL. 16. Drift ORM ↔ DB. 17. Granice architektury. 18.
Git/bezpieczeństwo. 19. Odstępstwa. 20. Problemy/ryzyka i kandydatów do
przyszłych decyzji --- bez implementacji. 21. Następny krok dokładnie:

``` text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-009.
```

## 28. Autoryzacja wykonania

Obecność pliku:

``` text
docs/tasks/TASK-008_Core_v1.1_Implementation_Alignment.md
```

w repozytorium **nie stanowi zgody na wykonanie Tasku**.

Codex rozpoczyna dopiero po jawnym poleceniu:

``` text
Wykonaj TASK-008.
```

Po zakończeniu nie rozpoczyna TASK-009.

## 29. Oczekiwany stan

``` text
CORE-001 v1.1-approved
        ↓
Domain aligned
        ↓
ORM aligned
        ↓
Alembic revision #3
        ↓
PostgreSQL aligned
        ↓
tests green
        ↓
READY FOR CERBERUS REVIEW
```
