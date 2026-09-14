# TDR-001 — Stos technologiczny MVP

**Projekt:** MSDS Manager  
**Id dokumentu:** TDR-001  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Powiązane IR:** IR-001-31, IR-001-32, IR-001-33  

---

## 1. Cel decyzji

Celem TDR-001 jest formalne zatwierdzenie podstawowego stosu technologicznego MVP MSDS Manager.

Stos ma wspierać:

- lokalną pracę jednego użytkownika,
- PostgreSQL jako docelowy fundament danych,
- rozdzielenie logiki domenowej od interfejsu i infrastruktury,
- kontrolowane migracje schematu,
- automatyczne testy,
- możliwość późniejszego przejścia do rozwiązania serwerowego i wieloużytkownikowego.

---

## 2. Zatwierdzony stos MVP

Dla MVP zatwierdza się:

- **Python** — język implementacji,
- **PostgreSQL** — relacyjna baza danych,
- **SQLAlchemy 2.x** — warstwa dostępu do danych / ORM,
- **Alembic** — migracje schematu PostgreSQL,
- **psycopg** — sterownik PostgreSQL dla Pythona,
- **pytest** — framework testowy,
- **Streamlit** — warstwa prezentacji MVP.

Biblioteka do ekstrakcji danych z PDF nie jest zatwierdzana w TDR-001. Należy do późniejszego pakietu SDS AI / ekstrakcji.

---

## 3. Python

Python jest podstawowym językiem implementacji MSDS Manager.

W Pythonie implementowane będą:

- logika domenowa,
- przypadki użycia,
- walidacja,
- dostęp do danych,
- integracja z repozytoriami plików,
- raportowanie,
- warstwa prezentacji Streamlit.

Core nie może być implementowany bezpośrednio w kodzie interfejsu.

---

## 4. PostgreSQL

PostgreSQL jest jedyną bazą operacyjną MVP.

Nie wprowadza się tymczasowej bazy SQLite ani innego lokalnego zamiennika.

Celem jest zachowanie tego samego fundamentu danych w wersji lokalnej i w potencjalnej przyszłej wersji serwerowej.

PostgreSQL przechowuje dane i metadane aplikacji.

Fizyczne pliki SDS oraz dowody decyzji BHP pozostają poza bazą danych.

---

## 5. SQLAlchemy

SQLAlchemy 2.x jest zatwierdzoną technologią mapowania i dostępu do danych.

Rola SQLAlchemy:

- mapowanie modelu aplikacji na relacyjny model PostgreSQL,
- obsługa relacji pomiędzy encjami,
- kontrola sesji i transakcji,
- implementacja repozytoriów infrastrukturalnych,
- ograniczenie rozproszenia ręcznych zapytań SQL po aplikacji.

SQLAlchemy nie definiuje znaczenia biznesowego danych.

Znaczenie encji, relacji, statusów i reguł wynika z CORE, BDR i ADR.

Logika domenowa nie może zależeć od klas ORM SQLAlchemy.

---

## 6. Alembic

Alembic jest jedynym zatwierdzonym mechanizmem migracji schematu PostgreSQL.

Każda zmiana struktury bazy po utworzeniu schematu początkowego powinna być wykonana przez wersjonowaną migrację Alembic.

Nie dopuszcza się jako standardowego sposobu rozwoju:

- ręcznego modyfikowania tabel produkcyjnych,
- kasowania bazy i tworzenia jej od nowa po każdej zmianie,
- automatycznego `create_all()` jako zamiennika migracji po uruchomieniu projektu.

Migracje muszą być przechowywane w repozytorium Git.

---

## 7. psycopg

`psycopg` jest zatwierdzonym sterownikiem komunikacji aplikacji Python z PostgreSQL.

Aplikacja korzysta z niego poprzez warstwę SQLAlchemy.

Kod domenowy nie komunikuje się bezpośrednio ze sterownikiem.

---

## 8. pytest

`pytest` jest zatwierdzonym frameworkiem testowym.

Projekt powinien umożliwiać co najmniej:

- testy jednostkowe logiki domenowej,
- testy przypadków użycia,
- testy integracyjne repozytoriów z PostgreSQL,
- testy regresyjne krytycznych reguł Core.

Do krytycznych reguł należą m.in.:

- maksymalnie jeden `CURRENT` SDS dla produktu,
- nowy `CURRENT` SDS powoduje `PENDING_APPROVAL`,
- maksymalnie jedna `CURRENT` decyzja BHP dla danego SDS,
- decyzja BHP nie może istnieć bez SDS i dowodu,
- korekta decyzji nie usuwa historii.

---

## 9. Streamlit

Streamlit jest zatwierdzoną warstwą prezentacji MVP.

Jego zadaniem jest:

- prezentacja danych,
- formularze użytkownika,
- uruchamianie przypadków użycia,
- raporty i widoki.

Streamlit nie może:

- zawierać Core logiki biznesowej,
- wykonywać bezpośrednio zapytań SQL jako podstawowego sposobu pracy,
- definiować reguł statusów,
- samodzielnie podejmować decyzji domenowych.

Zmiana Streamlit na inny frontend w przyszłości nie może wymagać przebudowy Core.

---

## 10. Architektura logiczna

Docelowy kierunek zależności:

```text
PRESENTATION / Streamlit
          |
          v
APPLICATION / use cases
          |
          v
DOMAIN / Core
          ^
          |
REPOSITORY INTERFACES
          ^
          |
INFRASTRUCTURE
          |
          +-- SQLAlchemy
          +-- psycopg
          +-- PostgreSQL
          +-- filesystem adapters
```

Zasada:

> Warstwy zewnętrzne mogą zależeć od wewnętrznych, ale Core nie może zależeć od Streamlit, PostgreSQL ani SQLAlchemy.

Szczegółowa struktura katalogów zostanie zatwierdzona w TDR-003.

---

## 11. Transakcje

Operacje wymagające spójnej zmiany wielu rekordów muszą być wykonywane transakcyjnie.

Dotyczy to w szczególności:

- `SDS CURRENT -> ARCHIVED` + nowy `SDS -> CURRENT` + `PRODUCT -> PENDING_APPROVAL`,
- `BHP_DECISION CURRENT -> SUPERSEDED` + nowa decyzja `CURRENT` + aktualizacja statusu produktu.

SQLAlchemy ma obsługiwać granice transakcji w warstwie aplikacyjnej/infrastrukturalnej.

---

## 12. Elementy poza stosem MVP

TDR-001 nie wprowadza:

- Dockera,
- FastAPI,
- Reacta,
- mikroserwisów,
- Celery,
- publicznego API,
- osobnego serwera aplikacyjnego,
- Kubernetes,
- mechanizmu wieloużytkownikowego,
- technologii AI/LLM,
- technologii ekstrakcji PDF.

Ich dodanie wymaga późniejszej decyzji, jeżeli pojawi się rzeczywista potrzeba.

---

## 13. Zasada wersji bibliotek

TDR zatwierdza rodziny technologii, a nie sztywne numery patch/minor wszystkich pakietów.

Konkretne wersje zależności zostaną zapisane w pliku zależności projektu i zablokowane w repozytorium na etapie implementacji.

Zmiana głównej technologii, np. SQLAlchemy na inny ORM lub Streamlit na inny framework UI, wymaga decyzji architektonicznej.

---

## 14. Rozstrzygnięcie IR

### IR-001-31 — Python

Status: **Resolved**

Decyzja: Python jest językiem implementacji MVP.

### IR-001-32 — SQLAlchemy + Alembic

Status: **Resolved**

Decyzja: SQLAlchemy 2.x jest warstwą ORM/dostępu do danych, a Alembic jedynym mechanizmem wersjonowanych migracji schematu PostgreSQL.

### IR-001-33 — Streamlit

Status: **Resolved**

Decyzja: Streamlit jest warstwą prezentacji MVP i nie może zawierać Core logiki biznesowej.

---

## 15. Ograniczenia dla Codexa

Codex nie może bez zatwierdzenia Architekta:

- zastąpić PostgreSQL inną bazą,
- zastąpić SQLAlchemy innym ORM,
- zastąpić Alembic innym systemem migracji,
- przenieść Core do Streamlit,
- dodać FastAPI/React/Docker tylko „na przyszłość”,
- ominąć repozytoriów poprzez rozproszone bezpośrednie zapytania SQL,
- zmienić reguł domenowych w celu dopasowania ich do ORM.

---

## 16. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono Python, PostgreSQL, SQLAlchemy 2.x, Alembic, psycopg, pytest i Streamlit jako stos MVP |
