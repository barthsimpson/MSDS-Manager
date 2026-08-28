# TASK-002 — Lokalne PostgreSQL i konfiguracja połączenia

**Projekt:** MSDS Manager  
**Task ID:** TASK-002  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** Ready for Codex  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Przygotować i zweryfikować warstwę lokalnej konfiguracji MSDS Manager oraz techniczne połączenie aplikacji z natywnym PostgreSQL uruchomionym w Windows.

Po TASK-002 projekt ma:

- odczytywać konfigurację z lokalnego `.env`,
- walidować wymagane zmienne,
- tworzyć `SQLAlchemy Engine` i `Session` bez łączenia przy imporcie modułu,
- posiadać jawny test/diagnostykę połączenia z PostgreSQL,
- sprawdzać dostępność `SDS_ROOT_PATH` i `BHP_EVIDENCE_ROOT_PATH`,
- nadal nie posiadać tabel domenowych ani migracji Core.

---

## 2. Obowiązujące decyzje

Stosuj jako nadrzędne:

- TDR-001 — Python + PostgreSQL + SQLAlchemy 2.x + Alembic + psycopg + pytest + Streamlit,
- TDR-002 — PostgreSQL natywnie na Windows; `.env`; `DATABASE_URL`, `SDS_ROOT_PATH`, `BHP_EVIDENCE_ROOT_PATH`,
- TDR-003 — konfiguracja i baza wyłącznie w `infrastructure`; `domain` nie zna `.env`, SQLAlchemy ani PostgreSQL,
- AGENTS.md,
- TASK-001 i jego zaakceptowany rezultat.

Nie zmieniaj Core.

---

## 3. Warunek wejścia — inspekcja PostgreSQL

Najpierw sprawdź środowisko bez wykonywania instalacji i bez zmiany konfiguracji systemowej.

Uruchom odpowiednie kontrole Windows, co najmniej:

```powershell
psql --version
Get-Service *postgres*
```

Jeżeli `psql` nie jest dostępny w `PATH`, ale usługa PostgreSQL istnieje, spróbuj zidentyfikować lokalizację instalacji bez modyfikowania `PATH`.

### STOP

Nie instaluj PostgreSQL samodzielnie.

Jeżeli PostgreSQL nie jest zainstalowany lub nie można ustalić działającej lokalnej instancji, zakończ techniczną część po przygotowaniu bezpiecznej warstwy konfiguracji i zwróć `PARTIAL`, wskazując dokładnie, czego potrzebuje użytkownik.

---

## 4. Lokalna baza

Docelowa lokalna baza:

```text
msds_manager
```

Nie twórz bazy, jeżeli wymagałoby to zgadywania:

- użytkownika PostgreSQL,
- hasła,
- portu,
- uprawnień administracyjnych.

Jeżeli istnieją poprawne dane dostępowe w lokalnym `.env` lub użytkownik przekazał je jawnie w bieżącej sesji Codexa, możesz zweryfikować połączenie.

Jeżeli baza `msds_manager` nie istnieje, ale dostępne poświadczenia mają jawnie odpowiednie uprawnienia, możesz ją utworzyć wyłącznie po uzyskaniu bezpośredniej zgody użytkownika w bieżącej sesji.

Nie twórz żadnych tabel.

---

## 5. `.env` i `.env.example`

Zachowaj `.env.example` jako plik wersjonowany bez sekretów.

Minimalne klucze:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/msds_manager
SDS_ROOT_PATH=C:\PATH\TO\SDS
BHP_EVIDENCE_ROOT_PATH=C:\PATH\TO\BHP_EVIDENCE
```

Rzeczywisty `.env`:

- jest lokalny,
- pozostaje ignorowany przez Git,
- nie może zostać pokazany w raporcie w sposób ujawniający hasło,
- nie może zostać dodany do repozytorium.

Jeżeli `.env` nie istnieje, nie wpisuj fikcyjnych poświadczeń jako działającej konfiguracji.

---

## 6. Odczyt `.env` — bez nowej biblioteki

W TASK-002 nie dodawaj `python-dotenv` ani innej nowej biblioteki.

Utwórz minimalny loader `.env` przy użyciu wyłącznie standardowej biblioteki Python.

Loader ma obsługiwać wyłącznie potrzeby MVP:

- puste linie,
- linie komentarzy rozpoczynające się od `#`,
- prosty format `KEY=VALUE`,
- białe znaki wokół klucza i wartości.

Nie implementuj:

- interpolacji zmiennych,
- składni shellowej,
- wielowierszowych wartości,
- eksportów typu `export KEY=...`,
- zaawansowanego parsera `.env`.

Jeżeli pojawi się potrzeba szerszej obsługi, zgłoś ją zamiast rozbudowywać parser.

---

## 7. Moduł konfiguracji

W:

```text
app/infrastructure/config/
```

utwórz minimalną warstwę konfiguracji, np.:

```text
settings.py
```

Powinna udostępniać jeden czytelny obiekt/strukturę `Settings` zawierającą:

```text
database_url
sds_root_path
bhp_evidence_root_path
```

Wymagania:

1. odczyt lokalnego `.env` z katalogu głównego projektu,
2. możliwość nadpisania wartości przez istniejące zmienne środowiskowe procesu,
3. jawny błąd konfiguracji, gdy brakuje wymaganej wartości,
4. brak logowania sekretu `DATABASE_URL` w pełnej postaci,
5. brak zależności od `domain`.

Możesz utworzyć własny wyjątek infrastrukturalny dla błędnej konfiguracji, ale nie dodawaj nowej warstwy architektury.

---

## 8. Walidacja ścieżek root

Konfiguracja ma umożliwiać sprawdzenie:

```text
SDS_ROOT_PATH
BHP_EVIDENCE_ROOT_PATH
```

Reguły:

- katalog musi istnieć, aby diagnostyka zakończyła się pełnym sukcesem,
- brak katalogu ma zwrócić czytelny wynik błędu/ostrzeżenia,
- aplikacja nie może automatycznie tworzyć katalogu,
- aplikacja nie może przenosić, usuwać ani modyfikować znajdujących się tam dokumentów.

Nie wpisuj lokalnych ścieżek użytkownika do kodu.

---

## 9. `app/infrastructure/db/session.py`

Zastąp bootstrapowy stub minimalną implementacją zgodną z SQLAlchemy 2.x.

Moduł ma udostępniać techniczny sposób utworzenia:

- `Engine`,
- `sessionmaker`.

Wymagania:

- `DATABASE_URL` pochodzi wyłącznie z warstwy konfiguracji,
- brak połączenia z DB podczas samego importu modułu,
- brak `Base.metadata.create_all()`,
- brak modeli ORM,
- brak tabel,
- brak logiki domenowej.

Preferuj funkcje fabrykujące, np. semantycznie:

```text
create_engine_from_settings(...)
create_session_factory(...)
```

Nazwy mogą być inne, jeżeli pozostają czytelne i zgodne z granicami TDR-003.

---

## 10. Diagnostyka środowiska

Utwórz jawny skrypt:

```text
scripts/check_environment.py
```

Skrypt ma:

1. załadować konfigurację,
2. sprawdzić istnienie obu katalogów root,
3. utworzyć połączenie SQLAlchemy,
4. wykonać prosty techniczny test PostgreSQL:

```sql
SELECT 1
```

5. zwrócić czytelny wynik bez ujawniania hasła.

Przykładowy charakter wyniku:

```text
MSDS Manager environment check

DATABASE: OK
SDS_ROOT_PATH: OK
BHP_EVIDENCE_ROOT_PATH: OK

RESULT: OK
```

lub:

```text
DATABASE: ERROR - ...
SDS_ROOT_PATH: MISSING
BHP_EVIDENCE_ROOT_PATH: OK

RESULT: FAILED
```

Skrypt nie może tworzyć bazy, tabel, katalogów ani danych.

---

## 11. Alembic

Nie twórz migracji domenowej.

`target_metadata` pozostaje:

```python
None
```

TASK-002 nie podłącza jeszcze modeli ORM do Alembica.

Dopuszczalna jest tylko taka korekta konfiguracji Alembica, która jest niezbędna do zachowania zgodności z istniejącym bootstrapem i nie uruchamia migracji Core.

---

## 12. Testy

Dodaj testy jednostkowe konfiguracji, co najmniej dla:

- poprawnego odczytu prostego `.env`,
- pomijania komentarzy i pustych linii,
- błędu przy braku wymaganej zmiennej,
- nadpisania wartości z `.env` przez zmienną środowiskową,
- braku ujawnienia sekretu w komunikacie błędu, jeżeli ma zastosowanie.

Dodaj test dotyczący tworzenia konfiguracji DB bez wykonywania połączenia przy imporcie.

### Test integracyjny PostgreSQL

Możesz dodać test integracyjny wykonujący `SELECT 1`, ale:

- nie może używać SQLite,
- nie może korzystać z operacyjnej bazy w sposób zmieniający dane,
- powinien być pomijany (`skip`), jeżeli jawnie nie skonfigurowano bezpiecznego środowiska testowego.

Nie twórz jeszcze osobnej bazy testowej automatycznie.

---

## 13. Aktualizacja README

Rozszerz techniczny README wyłącznie o informacje dotyczące TASK-002:

- wymaganie natywnego PostgreSQL na Windows,
- lokalny `.env` tworzony z `.env.example`,
- znaczenie trzech zmiennych konfiguracyjnych,
- sposób uruchomienia diagnostyki środowiska,
- informację, że aplikacja nie tworzy katalogów SDS/BHP,
- informację, że baza nie posiada jeszcze tabel domenowych.

Nie opisuj jeszcze workflow użytkowego.

---

## 14. Bezpieczeństwo Git

Zweryfikuj:

```powershell
git status --short
git check-ignore .env
```

Jeżeli `.env` istnieje, potwierdź, że jest ignorowany.

Nie pokazuj jego zawartości w raporcie.

Sprawdź również, czy w repozytorium nie znalazły się:

- hasła,
- rzeczywiste pliki SDS,
- dowody BHP,
- lokalne pliki baz danych.

---

## 15. Elementy poza zakresem

Nie implementuj:

- PRODUCT,
- MANUFACTURER,
- USAGE_LOCATION,
- SDS,
- BHP_DECISION,
- SAFETY_PROFILE,
- SDS_COMPONENT,
- modeli ORM,
- repozytoriów domenowych,
- tabel PostgreSQL,
- migracji domenowych,
- UI Streamlit,
- importu Excel,
- ekstrakcji PDF,
- REACH,
- AI/LLM,
- backupu,
- Dockera,
- FastAPI,
- Reacta,
- SQLite,
- systemu użytkowników i uprawnień.

---

## 16. Zasada STOP

Zatrzymaj problematyczny fragment i raportuj zamiast zgadywać, jeżeli:

- PostgreSQL nie jest zainstalowany,
- nie ma danych dostępowych do lokalnej instancji,
- baza wymaga utworzenia, a nie ma jawnej zgody użytkownika,
- rzeczywiste ścieżki SDS/BHP nie są ustalone,
- wykonanie wymaga nowej biblioteki,
- konieczna byłaby zmiana TDR lub Core,
- wymagana byłaby zmiana polityki Windows/PowerShell,
- konieczne byłyby uprawnienia administratora, których nie masz.

Dopuszczalny status Tasku w takim przypadku:

```text
PARTIAL
```

jeżeli kod konfiguracji i diagnostyki został poprawnie wykonany, a pełna weryfikacja lokalnej infrastruktury wymaga działania użytkownika.

---

## 17. Kryteria akceptacji

TASK-002 otrzymuje pełne `DONE`, jeżeli:

1. konfiguracja odczytuje lokalny `.env`,
2. trzy wymagane zmienne są walidowane,
3. zmienne środowiskowe mogą nadpisać wartości `.env`,
4. `.env` jest ignorowany przez Git,
5. `session.py` tworzy Engine i sessionmaker bez połączenia przy imporcie,
6. brak `create_all()` i brak tabel domenowych,
7. `scripts/check_environment.py` działa,
8. `SELECT 1` do lokalnego PostgreSQL kończy się sukcesem,
9. oba skonfigurowane katalogi root istnieją i są wykrywane,
10. testy jednostkowe przechodzą,
11. istniejący smoke test z TASK-001 nadal przechodzi,
12. Alembic nadal nie posiada rewizji domenowych,
13. nie dodano niezatwierdzonych bibliotek.

Jeżeli punkty 1–7 i 10–13 są spełnione, ale użytkownik musi jeszcze dostarczyć/utworzyć infrastrukturę lokalną z punktów 8–9, raportuj `PARTIAL`, nie `DONE`.

---

## 18. Polecenia kontrolne

Uruchom co najmniej:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m alembic history
.\.venv\Scripts\python.exe scripts\check_environment.py
git status --short
git check-ignore .env
```

Dodatkowo:

```powershell
psql --version
Get-Service *postgres*
```

Jeżeli któreś polecenie jest niedostępne, raportuj rzeczywisty wynik.

---

## 19. Oczekiwany raport Codexa

Zwróć:

```text
TASK-002 REPORT

1. Status
DONE / PARTIAL / BLOCKED

2. Wykonano
...

3. Utworzone pliki
...

4. Zmienione pliki
...

5. PostgreSQL lokalny
wersja:
usługa:
stan:
baza msds_manager:
połączenie SELECT 1:

6. Konfiguracja
.env istnieje: TAK/NIE
DATABASE_URL: SKONFIGUROWANY/NIESKONFIGUROWANY
SDS_ROOT_PATH: OK/MISSING/NIESKONFIGUROWANY
BHP_EVIDENCE_ROOT_PATH: OK/MISSING/NIESKONFIGUROWANY
Nie ujawniaj sekretów.

7. Testy i polecenia kontrolne
polecenie:
wynik:
...

8. Alembic
history:
target_metadata:
...

9. Git / bezpieczeństwo
.env ignored:
sekrety wykryte:
produkcyjne dokumenty w repo:
...

10. Decyzje techniczne podjęte w granicach Tasku
...

11. Odstępstwa
BRAK / opis

12. Problemy lub ryzyka
BRAK / opis

13. Pytania wymagające decyzji Cerberusa
BRAK / opis

14. Jak zweryfikować rezultat
...

15. Następny krok
OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-003.
```

Po raporcie zatrzymaj się.
