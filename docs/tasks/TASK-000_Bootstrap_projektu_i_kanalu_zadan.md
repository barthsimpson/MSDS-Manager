TASK-000 — Bootstrap projektu i kanału zadań dla Codexa

Projekt: MSDS Manager
Task ID: TASK-000
Sprint: SPRINT-001 — Foundation / Core Skeleton
Status wejściowy: Ready for Codex
Wykonawca: Codex OpenAI
Nadzór: Cerberus — Agent Architekt
Akceptacja końcowa: Architekt Operacyjny

1. Cel Tasku

Utworzyć lokalny katalog projektu MSDS Manager oraz ustanowić trwały, jednoznaczny sposób przekazywania kolejnych Tasków do Codexa.

TASK-000 jest jedynym Taskiem bootstrapowym, który może zostać przekazany Codexowi bez wcześniejszego istnienia repozytorium projektu.

Po zakończeniu TASK-000 kolejne Taski są przekazywane jako pliki Markdown znajdujące się w repozytorium projektu.

2. Lokalizacja projektu

Utwórz projekt w:

C:\Users\bartosz.murawski\Projects\MSDS-Manager

Nie modyfikuj innych projektów znajdujących się w:

C:\Users\bartosz.murawski\Projects

W szczególności nie zmieniaj katalogów:

Cerberus-Sandbox

Wagi-Warsztatowe

3. Utworzenie repozytorium

W katalogu:

C:\Users\bartosz.murawski\Projects\MSDS-Manager

wykonaj:

utworzenie katalogu projektu,

inicjalizację lokalnego repozytorium Git,

utworzenie minimalnej struktury do obsługi Tasków.

Na tym etapie nie twórz jeszcze pełnej struktury aplikacji z TDR-003 — będzie to zakres TASK-001.

4. Kanał zadań dla Codexa

Utwórz:

MSDS-Manager
└── docs
    ├── tasks
    └── task_reports

docs/tasks

Jest to obowiązujące repozytorium plików Tasków przekazywanych Codexowi.

Konwencja nazw:

TASK-000_*.md
TASK-001_*.md
TASK-002_*.md
...

docs/task_reports

Jest to miejsce na raporty wykonania Tasków, jeżeli Architekt/Cerberus poleci zapis raportu do pliku.

Konwencja nazw:

TASK-000_REPORT.md
TASK-001_REPORT.md
TASK-002_REPORT.md
...

5. Plik AGENTS.md

Utwórz w katalogu głównym repozytorium:

AGENTS.md

Minimalna treść pliku ma ustanawiać następujące reguły dla Codexa:

Codex realizuje wyłącznie jawnie wskazany Task.

Źródłem treści Tasków jest katalog:

docs/tasks/

Sam fakt obecności pliku w docs/tasks/ nie oznacza zgody na jego wykonanie.

Codex rozpoczyna Task wyłącznie po bezpośrednim poleceniu użytkownika wskazującym konkretny TASK-xxx.

Codex nie rozpoczyna automatycznie kolejnego Tasku po zakończeniu bieżącego.

W przypadku konfliktu, niejednoznaczności lub potrzeby zmiany Core stosuje zasadę STOP i raportuje problem.

Codex nie zmienia zatwierdzonych decyzji architektonicznych ani biznesowych.

Każdy Task kończy raportem w formacie wymaganym przez dany Task.

Codex pracuje wyłącznie w bieżącym repozytorium, chyba że Task jawnie stanowi inaczej.

AGENTS.md ma być krótkim dokumentem wykonawczym, a nie kopią całej Konstytucji projektu.

6. Rejestr Tasków

Utwórz:

docs/tasks/README.md

Minimalna treść:

# Tasks — MSDS Manager

Katalog `docs/tasks/` jest źródłem zatwierdzonych instrukcji wykonawczych dla Codexa.

Zasady:
- jeden plik = jeden Task,
- obecność pliku nie uruchamia Tasku automatycznie,
- Task wykonuje się dopiero po jawnym poleceniu użytkownika,
- po zakończeniu Tasku Codex zatrzymuje się,
- kolejny Task wymaga osobnej decyzji.

7. Umieszczenie TASK-000

Zapisz kopię niniejszego Tasku jako:

docs/tasks/TASK-000_Bootstrap_projektu_i_kanalu_zadan.md

Jeżeli TASK-000 został przekazany wyłącznie jako tekst w czacie Codexa, utwórz ten plik na podstawie przekazanej treści.

Nie zmieniaj znaczenia Tasku.

8. TASK-001

Jeżeli plik TASK-001 jest dostępny użytkownikowi lub w bieżącym środowisku, nie wykonuj go automatycznie.

TASK-000 ma wyłącznie przygotować miejsce:

docs/tasks/

do którego użytkownik przeniesie lub zapisze:

TASK-001_Bootstrap_repozytorium_MSDS_Manager.md

TASK-001 zostanie uruchomiony osobnym poleceniem.

9. Elementy poza zakresem

W TASK-000 nie implementuj:

struktury aplikacji z TDR-003,

pyproject.toml,

.env.example,

Alembic,

SQLAlchemy,

PostgreSQL,

modeli domenowych,

testów,

Streamlit,

SDS,

BHP,

ekstrakcji PDF,

REACH,

AI.

Nie instaluj żadnych zależności.

Nie twórz środowiska .venv.

10. Kryteria akceptacji

TASK-000 jest wykonany poprawnie, jeżeli istnieje:

C:\Users\bartosz.murawski\Projects\MSDS-Manager
├── .git\
├── AGENTS.md
└── docs
    ├── tasks
    │   ├── README.md
    │   └── TASK-000_Bootstrap_projektu_i_kanalu_zadan.md
    └── task_reports

oraz:

repozytorium Git jest zainicjalizowane,

inne projekty w Projects nie zostały zmodyfikowane,

Codex ma zapisaną zasadę, że docs/tasks/ jest źródłem Tasków,

żaden kolejny Task nie został uruchomiony,

nie dodano kodu aplikacji ani zależności.

11. Zasada STOP

Zatrzymaj Task i zgłoś problem, jeżeli:

katalog docelowy już istnieje i zawiera dane, których pochodzenia nie znasz,

wykonanie wymaga nadpisania istniejących plików,

nie masz uprawnień do utworzenia katalogu lub repozytorium,

musiałbyś modyfikować inny projekt,

musiałbyś zgadywać oczekiwane zachowanie.

12. Oczekiwany raport Codexa

Po wykonaniu zwróć:

TASK-000 REPORT

1. Status
DONE / BLOCKED / PARTIAL

2. Utworzony katalog projektu
...

3. Utworzone pliki i katalogi
...

4. Git
status inicjalizacji:
...

5. Weryfikacja kanału Tasków
docs/tasks:
AGENTS.md:
...

6. Odstępstwa
BRAK / opis

7. Problemy lub ryzyka
BRAK / opis

8. Następny krok
OCZEKUJĘ NA JAWNE POLECENIE URUCHOMIENIA TASK-001

Po raporcie zatrzymaj się.