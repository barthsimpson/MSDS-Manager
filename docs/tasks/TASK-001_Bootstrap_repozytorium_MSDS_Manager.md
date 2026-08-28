# TASK-001 — Bootstrap repozytorium MSDS Manager

**Projekt:** MSDS Manager  
**Task ID:** TASK-001  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** Ready for Codex  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Utworzyć minimalny, działający szkielet repozytorium MSDS Manager zgodny z zatwierdzoną architekturą projektu.

Task ma przygotować plac budowy dla kolejnych zadań.

TASK-001 nie implementuje jeszcze logiki biznesowej Core, modeli SQLAlchemy, migracji domenowych, interfejsu użytkownika ani ekstrakcji SDS.

---

## 2. Kontekst obowiązujący

Projekt działa według modelu:

- Człowiek — Architekt Operacyjny definiuje cel i zatwierdza wymagania,
- Cerberus — Agent Architekt projektuje architekturę i przygotowuje Taski,
- Codex — Wykonawca realizuje wyłącznie zatwierdzony Task.

Codex nie może rozszerzać zakresu ani podejmować decyzji biznesowych.

Obowiązują technologie:

- Python,
- PostgreSQL,
- SQLAlchemy 2.x,
- Alembic,
- psycopg,
- pytest,
- Streamlit.

W TASK-001 nie implementuj jeszcze ich pełnego wykorzystania. Utwórz jedynie strukturę repozytorium i deklarację zależności potrzebną do kolejnych Tasków.

---

## 3. Wymagane działania

Utwórz repozytorium o strukturze zgodnej z TDR-003:

```text
msds-manager/
|
+-- app/
|   +-- domain/
|   |   +-- models/
|   |   +-- enums/
|   |   +-- rules/
|   |   +-- exceptions/
|   |
|   +-- application/
|   |   +-- use_cases/
|   |   +-- ports/
|   |   +-- dto/
|   |
|   +-- infrastructure/
|   |   +-- db/
|   |   |   +-- models/
|   |   |   +-- repositories/
|   |   |   +-- session.py
|   |   |
|   |   +-- filesystem/
|   |   +-- config/
|   |
|   +-- presentation/
|       +-- streamlit/
|
+-- migrations/
|   +-- versions/
|
+-- tests/
|   +-- unit/
|   +-- integration/
|
+-- docs/
|   +-- technical/
|
+-- scripts/
|
+-- .env.example
+-- .gitignore
+-- alembic.ini
+-- pyproject.toml
+-- README.md
```

Dodaj wymagane pliki `__init__.py`, aby struktura była poprawnym pakietem Python tam, gdzie jest to potrzebne.

---

## 4. `pyproject.toml`

Utwórz `pyproject.toml` jako centralny plik deklaracji projektu.

Zadeklaruj projekt `msds-manager`.

Dodaj zależności zatwierdzone dla MVP:

- SQLAlchemy 2.x,
- Alembic,
- psycopg,
- pytest,
- Streamlit.

Nie dodawaj innych frameworków ani bibliotek aplikacyjnych bez wyraźnej potrzeby wynikającej z tego Tasku.

Jeżeli technicznie potrzebna jest drobna biblioteka wyłącznie do odczytu `.env`, nie dodawaj jej automatycznie. Zatrzymaj ten fragment i zgłoś potrzebę decyzji w raporcie.

---

## 5. `.env.example`

Utwórz `.env.example` bez sekretów i bez rzeczywistych ścieżek użytkownika.

Minimalna zawartość:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/msds_manager
SDS_ROOT_PATH=C:\PATH\TO\SDS
BHP_EVIDENCE_ROOT_PATH=C:\PATH\TO\BHP_EVIDENCE
```

Nie twórz rzeczywistego `.env`.

---

## 6. `.gitignore`

`.gitignore` musi wykluczać co najmniej:

```text
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

Nie umieszczaj w Git:

- sekretów,
- lokalnej bazy,
- produkcyjnych plików SDS,
- dowodów BHP,
- wirtualnego środowiska Python.

---

## 7. Alembic

Utwórz bazową konfigurację Alembic:

- `alembic.ini`,
- katalog `migrations/`,
- katalog `migrations/versions/`,
- wymagane pliki konfiguracyjne Alembic.

Na tym etapie:

- nie twórz jeszcze migracji domenowej,
- nie twórz tabel Core,
- nie używaj `Base.metadata.create_all()` jako mechanizmu inicjalizacji bazy.

Jeżeli inicjalizacja Alembic wymaga plików pomocniczych, utwórz je w minimalnej formie.

---

## 8. README

Utwórz `README.md` zawierający tylko techniczne informacje potrzebne na tym etapie:

- nazwę projektu,
- informację, że projekt jest w fazie bootstrap,
- wymaganie Python + PostgreSQL,
- sposób utworzenia `.venv` na Windows,
- sposób instalacji projektu/zależności,
- informację o konieczności utworzenia lokalnego `.env` na podstawie `.env.example`,
- polecenie uruchomienia testów.

Nie opisuj jeszcze workflow SDS, decyzji BHP ani funkcjonalności, które nie zostały zaimplementowane.

---

## 9. Minimalny test bootstrap

Dodaj minimalny test `pytest`, którego zadaniem jest potwierdzenie, że:

- pakiet `app` jest importowalny,
- podstawowa struktura projektu jest poprawna.

Nie testuj jeszcze reguł biznesowych ani bazy danych.

---

## 10. Granice architektury

Bezwzględnie zachowaj:

```text
presentation -> application -> domain
                     ^
                     |
              infrastructure
```

Na tym etapie nie implementuj zależności między warstwami poza minimalnymi importami potrzebnymi do smoke testu.

`domain` nie może importować:

- Streamlit,
- SQLAlchemy,
- psycopg,
- Alembic,
- modułów infrastructure,
- konfiguracji `.env`.

---

## 11. Elementy poza zakresem

Nie implementuj w TASK-001:

- modeli domenowych PRODUCT/SDS/BHP_DECISION,
- enumów biznesowych,
- modeli ORM,
- połączenia z PostgreSQL,
- sesji SQLAlchemy poza pustym/stubowym plikiem wymaganym strukturą,
- migracji tworzących tabele,
- repozytoriów,
- use case'ów,
- Streamlit UI,
- importu Excel,
- ekstrakcji PDF,
- SAFETY_PROFILE,
- SDS_COMPONENT,
- REACH,
- AI/LLM,
- backupu,
- Dockera,
- FastAPI,
- Reacta,
- SQLite.

---

## 12. Pliki chronione / źródła wymagań

Nie modyfikuj źródeł projektowych:

- CORE-001,
- BDR-001 ... BDR-005,
- TDR-001 ... TDR-003,
- ADR,
- PDP,
- ROADMAP,
- Konstytucji,
- GOV,
- SCOPE,
- IR.

Jeżeli kopia któregoś dokumentu znajduje się w repozytorium, nie zmieniaj jej treści w ramach TASK-001.

---

## 13. Kryteria akceptacji

TASK-001 jest wykonany poprawnie, jeżeli:

1. repozytorium posiada strukturę zatwierdzoną w TDR-003,
2. wszystkie wymagane katalogi i pliki istnieją,
3. `pyproject.toml` zawiera wyłącznie zatwierdzony podstawowy stos,
4. `.env.example` zawiera trzy wymagane zmienne konfiguracji,
5. `.env` jest ignorowany przez Git,
6. Alembic jest zainicjalizowany, ale nie posiada jeszcze migracji domenowej,
7. `pytest` uruchamia się poprawnie,
8. minimalny smoke test przechodzi,
9. `domain` nie zależy od SQLAlchemy, Streamlit ani infrastructure,
10. w repozytorium nie znajdują się produkcyjne dokumenty SDS/BHP ani sekrety,
11. nie dodano żadnej funkcjonalności biznesowej poza zakresem.

---

## 14. Polecenia kontrolne

Uruchom i podaj wynik co najmniej:

```powershell
python --version
python -m pytest
```

Jeżeli projekt jest instalowany jako pakiet, uruchom także właściwe polecenie instalacyjne wynikające z `pyproject.toml`.

Jeżeli środowisko nie pozwala uruchomić któregoś polecenia, nie zgaduj wyniku. Opisz ograniczenie w raporcie.

---

## 15. Zasada STOP

Zatrzymaj problematyczny fragment i zgłoś go zamiast samodzielnie rozstrzygać, jeżeli:

- potrzebna jest biblioteka spoza zatwierdzonego stosu,
- konieczna byłaby zmiana struktury warstw,
- wymaganie jest sprzeczne z TDR-001/002/003,
- konieczna byłaby decyzja dotycząca Core,
- potrzebne są rzeczywiste hasła lub lokalne ścieżki użytkownika,
- wykonanie wymaga Dockera, SQLite lub innej niezatwierdzonej technologii,
- musiałbyś zgadywać wymaganie.

Nie rozszerzaj Tasku w celu „przygotowania projektu na przyszłość”.

---

## 16. Oczekiwany raport Codexa

Po wykonaniu zwróć raport w układzie:

```text
TASK-001 REPORT

1. Status
DONE / BLOCKED / PARTIAL

2. Wykonano
...

3. Utworzone pliki
...

4. Zmienione pliki
...

5. Zależności
...

6. Testy i polecenia kontrolne
polecenie:
wynik:

7. Decyzje techniczne podjęte w granicach Tasku
...

8. Odstępstwa od specyfikacji
BRAK / opis

9. Problemy lub ryzyka
BRAK / opis

10. Pytania wymagające decyzji Cerberusa
BRAK / opis

11. Jak zweryfikować rezultat
...
```

Nie rozpoczynaj TASK-002.
