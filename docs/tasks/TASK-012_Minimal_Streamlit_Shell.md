# TASK-012 — Minimal Streamlit Shell

**Projekt:** MSDS Manager  
**Task ID:** TASK-012  
**Sprint:** SPRINT-002 v1.2-approved — Rejestr produktów i miejsc stosowania  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Uruchomić pierwszy rzeczywisty interfejs użytkownika MSDS Manager w Streamlit, oparty na istniejącej architekturze.

TASK-012 tworzy wyłącznie **minimalny shell aplikacji**:

```text
Streamlit
├── Produkty
└── Stanowiska
```

Shell ma potwierdzić poprawne uruchomienie warstwy presentation, konfiguracji i połączenia z istniejącą warstwą Application/Infrastructure.

TASK-012 **nie implementuje jeszcze Product Registry View ani workflow administracyjnego**.

---

## 2. Stan wejściowy

Po zaakceptowanym TASK-011:

```text
CORE                    v1.2-approved
Alembic revisions       4
PostgreSQL head         d2b4f6a8c190
Application tables      9
Tests                   91 passed
Schema drift            none
Business records        0
SAWarning               none
```

TASK-011 potwierdził cały pion:

```text
Application
    ↓
Repositories
    ↓
TransactionExecutor
    ↓
PostgreSQL
```

bez konieczności zmiany kodu produkcyjnego.

---

## 3. Źródła nadrzędne

Obowiązują:

1. `CORE-001 v1.2-approved`,
2. `SPRINT-002 v1.2-approved`,
3. zatwierdzone BDR-001..005,
4. TDR-001..003,
5. zaakceptowane TASK-008..011 oraz TASK-009-ALIGN,
6. root `AGENTS.md`.

SPRINT-002 v1.2 definiuje TASK-012 jako **Minimal Streamlit Shell** i dopuszcza sekcje:

```text
Produkty
Stanowiska
```

Nie dopuszcza jeszcze:

```text
Dodaj nowy produkt
Dodaj nowy SDS
```

---

# CZĘŚĆ A — GRANICA TASKU

## 4. Co budujemy

Minimalny shell ma zapewnić:

- start aplikacji Streamlit,
- tytuł aplikacji `MSDS Manager`,
- prostą nawigację,
- sekcję `Produkty`,
- sekcję `Stanowiska`,
- composition root łączący UI z istniejącą konfiguracją i persistence,
- kontrolowaną obsługę błędu konfiguracji/połączenia,
- minimalne testy presentation.

Nie projektuj docelowego dashboardu.

---

## 5. Czego jeszcze NIE budujemy

### Produkty

W TASK-012 nie implementuj jeszcze:

- pełnej listy produktów,
- tabeli produktów,
- szczegółów produktu,
- wyszukiwania,
- filtrowania,
- sortowania biznesowego,
- edycji produktu,
- formularzy administracyjnych.

To zakres TASK-013/TASK-014.

### Stanowiska

W TASK-012 nie implementuj jeszcze:

- formularza dodawania stanowiska,
- deactivate/reactivate,
- przypisywania produktu,
- quantity forms.

### Workflow wejściowy

Nie implementuj:

```text
Dodaj nowy produkt
Dodaj nowy SDS
```

Nowy PRODUCT powstanie później jako część workflow SDS.

---

# CZĘŚĆ B — STRUKTURA PRESENTATION

## 6. Lokalizacja kodu

Kod UI ma znajdować się w:

```text
app/presentation/streamlit/
```

Preferuj minimalną strukturę, np.:

```text
app/presentation/streamlit/
├── app.py
└── composition.py
```

lub równoważną, jeśli prostsza struktura lepiej pasuje do istniejącego repo.

Nie twórz rozbudowanego frameworka stron/komponentów.

---

## 7. Punkt wejścia

Aplikacja musi mieć jednoznaczny entry point umożliwiający uruchomienie np.:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/app.py
```

Jeżeli istniejąca struktura pakietu wymaga innej równoważnej komendy, udokumentuj ją w raporcie.

Nie zmieniaj systemowego PATH.

---

# CZĘŚĆ C — COMPOSITION ROOT

## 8. Odpowiedzialność composition root

TASK-012 jest pierwszym miejscem, w którym presentation może technicznie złożyć istniejące elementy:

```text
Settings
   ↓
Engine / session factory
   ↓
SQLAlchemy repositories
   ↓
Application use cases
   ↓
Streamlit
```

Composition root należy do zewnętrznej warstwy aplikacji/presentation i może importować infrastructure.

Nie wolno przez to zmieniać kierunku zależności wewnątrz Application/Domain.

---

## 9. Brak logiki biznesowej w Streamlit

Streamlit odpowiada wyłącznie za:

- prezentację,
- wybór sekcji,
- wywołanie przygotowanych use case'ów,
- prezentację kontrolowanych błędów.

Streamlit nie może:

- wykonywać SQL,
- importować modeli ORM w kodzie widoku,
- tworzyć własnych reguł statusów,
- walidować biznesowo quantity zamiast Domain/Application,
- wykonywać bezpośrednio `Session.execute()` dla funkcji biznesowych,
- wykonywać commit/rollback.

---

# CZĘŚĆ D — NAWIGACJA

## 10. Minimalna nawigacja

Utwórz dwie sekcje:

```text
Produkty
Stanowiska
```

Dopuszczalne jest użycie prostego mechanizmu Streamlit, np.:

- sidebar radio,
- prosty select,
- równoważna minimalna nawigacja.

Nie dodawaj dodatkowych sekcji „na przyszłość”.

---

## 11. Sekcja Produkty

TASK-012 ma jedynie utworzyć miejsce dla przyszłego TASK-013.

Minimalny ekran może zawierać:

```text
Produkty
```

oraz neutralną informację, że widok rejestru będzie rozwijany w kolejnym Tasku.

Nie implementuj jeszcze Product Registry View.

Nie dodawaj przycisku:

```text
Dodaj produkt
```

---

## 12. Sekcja Stanowiska

TASK-012 ma utworzyć miejsce dla późniejszego workflow administracyjnego.

Minimalny ekran może zawierać:

```text
Stanowiska
```

Nie implementuj jeszcze create/deactivate/reactivate ani formularzy.

---

# CZĘŚĆ E — KONFIGURACJA I POSTGRESQL

## 13. Konfiguracja

Użyj istniejącego mechanizmu Settings z TASK-002.

Nie twórz drugiego loadera `.env`.

Nie dodawaj `python-dotenv`.

Nie hardcoduj:

- DATABASE_URL,
- hasła,
- SDS_ROOT_PATH,
- BHP_EVIDENCE_ROOT_PATH.

---

## 14. Połączenie z bazą

Shell powinien potrafić zainicjalizować istniejący engine/session factory.

Nie twórz nowego mechanizmu persistence.

Nie używaj SQLite.

Nie używaj `Base.metadata.create_all()`.

Alembic pozostaje jedynym mechanizmem schema evolution.

---

## 15. Błąd konfiguracji lub połączenia

Jeżeli konfiguracja lub PostgreSQL są niedostępne:

- aplikacja nie powinna pokazywać tracebacku jako podstawowego komunikatu użytkownika,
- pokaż krótki kontrolowany komunikat w UI,
- nie ujawniaj hasła ani pełnego `DATABASE_URL`,
- szczegóły techniczne mogą pozostać w diagnostyce developerskiej, jeśli istniejący wzorzec projektu to umożliwia.

Nie buduj systemu logowania/monitoringu.

---

# CZĘŚĆ F — DANE I USE CASE'Y

## 16. Minimalne wykorzystanie Application

TASK-012 nie ma obowiązku implementować pełnego rejestru produktów.

Dopuszczalne jest jednak wykonanie minimalnego bezpiecznego odczytu przez istniejący use case w celu potwierdzenia composition root, np.:

```text
ListProducts
```

lub:

```text
ListUsageLocations
```

Jeżeli używasz takiego odczytu:

- wywołuj Application, nie repository bezpośrednio z widoku,
- nie rozbudowuj wyniku do funkcjonalności TASK-013,
- pusta baza musi być poprawnym stanem.

---

## 17. Pusta baza

Aktualny stan PostgreSQL po TASK-011:

```text
0 business records
```

Aplikacja musi uruchomić się poprawnie przy pustej bazie.

Nie dodawaj seeda tylko po to, aby UI wyglądało na wypełnione.

Nie twórz testowego PRODUCT podczas normalnego startu aplikacji.

---

# CZĘŚĆ G — TESTY

## 18. Test uruchomienia modułu presentation

Dodaj minimalny test potwierdzający, że moduły Streamlit shell:

- można zaimportować bez wykonywania niedozwolonej logiki biznesowej,
- nie tworzą tabel,
- nie wykonują zapisu danych podczas importu.

---

## 19. Test granicy architektury

Rozszerz/utrzymaj kontrolę architektury tak, aby potwierdzić:

```text
presentation
    może importować application
    może korzystać z composition root/infrastructure

application
    NIE importuje presentation
    NIE importuje infrastructure
    NIE importuje Streamlit

domain
    NIE importuje presentation
    NIE importuje Streamlit
```

Nie osłabiaj istniejących testów AST.

---

## 20. Test pustego stanu

Jeżeli shell wykonuje minimalny `ListProducts`:

- potwierdź poprawną obsługę `[]`.

Jeżeli shell tylko składa dependencies i nie wyświetla listy w TASK-012, nie implementuj sztucznego testu Product Registry.

---

## 21. Test błędu konfiguracji/DB

Dodaj test kontrolowanego zachowania przy błędzie inicjalizacji konfiguracji lub połączenia, bez potrzeby zatrzymywania lokalnego PostgreSQL.

Preferuj stub/mock na granicy technicznej.

Potwierdź, że komunikat dla UI:

- jest kontrolowany,
- nie zawiera sekretu/pełnego DATABASE_URL,
- nie wymaga nowego frameworka błędów.

---

# CZĘŚĆ H — TEST MANUALNY STREAMLIT

## 22. Manual smoke

Uruchom aplikację lokalnie.

Potwierdź:

1. Streamlit startuje bez wyjątku,
2. widoczny jest `MSDS Manager`,
3. można przełączyć `Produkty` ↔ `Stanowiska`,
4. pusta baza nie powoduje błędu,
5. UI nie oferuje `Dodaj produkt`,
6. UI nie oferuje `Dodaj nowy SDS`,
7. aplikacja nie zapisuje danych przy samym uruchomieniu/nawigacji.

Jeżeli automatyczne uruchomienie Streamlit wymaga procesu blokującego, wykonaj kontrolowany smoke z timeoutem lub równoważnym mechanizmem i zakończ proces po potwierdzeniu startu.

---

# CZĘŚĆ I — SCHEMA / ALEMBIC

## 23. Brak zmian schema

TASK-012 nie wymaga:

- zmian Domain,
- zmian Application contracts,
- zmian ORM,
- nowych tabel,
- nowych constraintów,
- migracji Alembic.

Oczekiwany stan:

```text
Alembic revisions       4
PostgreSQL current      d2b4f6a8c190 (head)
Application tables      9
Schema drift            none
Business records        0
```

Jeżeli UI wymaga zmiany schema:

```text
STOP
```

Nie twórz migracji #5.

---

## 24. Alembic

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
d2b4f6a8c190 (head)
No new upgrade operations detected.
```

---

# CZĘŚĆ J — ZALEŻNOŚCI

## 25. Brak nowych bibliotek

Streamlit jest już zatwierdzoną zależnością projektu.

Nie dodawaj nowych bibliotek UI, routing, DI, logging ani config.

Nie dodawaj:

- FastAPI,
- Flask,
- React,
- Pydantic,
- python-dotenv.

Jeżeli wymagane jest coś spoza istniejących zależności:

```text
STOP
```

---

# CZĘŚĆ K — POZA ZAKRESEM

## 26. TASK-012 NIE implementuje

- Product Registry View,
- szczegółów produktu,
- edycji produktu,
- tworzenia PRODUCT,
- tworzenia MANUFACTURER,
- formularza UsageLocation,
- deactivate/reactivate w UI,
- przypisywania produktu do lokalizacji,
- peak/monthly forms,
- SDS,
- BHP,
- SafetyProfile,
- Components,
- historii,
- REACH,
- importu Excel,
- dashboardu,
- użytkowników/uprawnień,
- nowych bibliotek,
- schema/migration changes.

---

# CZĘŚĆ L — STOP CONDITIONS

## 27. STOP

Raportuj `PARTIAL/BLOCKED`, jeżeli:

- aktualny stan repo/DB różni się istotnie od zaakceptowanego TASK-011,
- Streamlit nie jest dostępny mimo zatwierdzonej konfiguracji projektu,
- potrzebna jest zmiana Application/Domain semantics,
- potrzebna jest zmiana ORM/schema/migracja,
- potrzebny jest CreateProduct/CreateManufacturer,
- potrzebny jest workflow SDS/BHP,
- potrzebna jest nowa biblioteka,
- poprawny shell wymaga logiki biznesowej w presentation,
- pojawia się potrzeba rozwiązania historii,
- Task zaczyna realizować zakres TASK-013 lub TASK-014.

---

# CZĘŚĆ M — REGRESJA

## 28. Pełny pytest

Stan bazowy:

```text
91 passed
```

Uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -W error::sqlalchemy.exc.SAWarning
```

Wszystkie testy muszą przejść bez `SAWarning`.

---

# CZĘŚĆ N — GIT I BEZPIECZEŃSTWO

## 29. Kontrole

Uruchom:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:

- `.env` ignored i nietrackowany,
- brak sekretów,
- brak pełnego DATABASE_URL w UI/testach/raporcie,
- brak dumpów/backupów,
- brak PDF/MSG,
- brak testowych danych pozostawionych w DB,
- brak nowych bibliotek,
- brak commit/push bez jawnego polecenia.

---

# CZĘŚĆ O — KRYTERIA AKCEPTACJI

## 30. TASK-012 = DONE, jeżeli

1. istnieje minimalny Streamlit shell,
2. istnieje jednoznaczny entry point,
3. aplikacja uruchamia się lokalnie,
4. widoczny jest tytuł `MSDS Manager`,
5. istnieje sekcja `Produkty`,
6. istnieje sekcja `Stanowiska`,
7. nawigacja pomiędzy nimi działa,
8. nie istnieje `Dodaj produkt`,
9. nie istnieje `Dodaj nowy SDS`,
10. nie zaimplementowano Product Registry View,
11. nie zaimplementowano workflow administracyjnego,
12. presentation nie zawiera SQL,
13. presentation nie importuje modeli ORM do widoków,
14. presentation nie wykonuje commit/rollback,
15. composition root korzysta z istniejącego Settings,
16. composition root korzysta z istniejącego engine/session factory,
17. UI korzysta z Application, jeśli wykonuje odczyt biznesowy,
18. pusta baza jest poprawnym stanem,
19. start/nawigacja nie zapisują danych,
20. błąd konfiguracji/DB jest kontrolowany,
21. komunikat błędu nie ujawnia sekretów,
22. application nie importuje Streamlit/presentation/infrastructure,
23. domain nie importuje Streamlit/presentation,
24. istniejące testy architektury pozostają aktywne,
25. pełna regresja przechodzi bez SAWarning,
26. nie zmieniono Domain,
27. nie zmieniono kontraktów Application,
28. nie zmieniono ORM,
29. nie utworzono migracji #5,
30. PostgreSQL nadal ma 9 tabel,
31. `alembic current = d2b4f6a8c190 (head)`,
32. `alembic check` nie wykazuje driftu,
33. po Tasku baza ma 0 rekordów biznesowych,
34. nie dodano nowych bibliotek,
35. nie rozpoczęto historii,
36. nie rozpoczęto TASK-013,
37. utworzono raport TASK-012.

---

# CZĘŚĆ P — RAPORT

## 31. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-012_REPORT.md
```

Raport musi zawierać:

1. Status.
2. Stan wejściowy.
3. Utworzone/zmienione pliki presentation.
4. Entry point Streamlit.
5. Strukturę shell.
6. Nawigację Produkty/Stanowiska.
7. Composition root.
8. Wykorzystanie Settings.
9. Wykorzystanie Application/use case'ów.
10. Zachowanie pustej bazy.
11. Obsługę błędu konfiguracji/DB.
12. Potwierdzenie braku logiki biznesowej w UI.
13. Testy presentation.
14. Testy architektury.
15. Manual Streamlit smoke.
16. Pełny pytest / SAWarning.
17. Potwierdzenie braku zmian Domain/Application contracts/ORM/schema.
18. `alembic current`.
19. `alembic check`.
20. Finalny stan PostgreSQL.
21. Git/bezpieczeństwo.
22. Odstępstwa.
23. Problemy/ryzyka.
24. Następny krok dokładnie:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-013.
```

---

# CZĘŚĆ Q — AUTORYZACJA

## 32. Autoryzacja wykonania

Obecność pliku:

```text
docs/tasks/TASK-012_Minimal_Streamlit_Shell.md
```

w repozytorium **nie stanowi zgody na wykonanie Tasku**.

Codex rozpoczyna dopiero po jawnym poleceniu:

```text
Wykonaj TASK-012.
```

Po zakończeniu:

- tworzy raport,
- zatrzymuje się,
- nie rozpoczyna TASK-013.

---

## 33. Oczekiwany stan końcowy

```text
TASK-011 ACCEPTED
        ↓
verified business/application/persistence vertical
        ↓
TASK-012
        ↓
minimal Streamlit shell
        ↓
Produkty | Stanowiska
        ↓
no business logic in UI
        ↓
schema unchanged
        ↓
READY FOR TASK-013 — PRODUCT REGISTRY VIEW
```
