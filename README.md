# MSDS Manager

Lokalna aplikacja do prowadzenia rejestru produktów chemicznych w zakładzie:
karty charakterystyki (SDS), decyzje BHP z dowodami, miejsca stosowania
i ilości oraz widoki nadzorcze i analityczne.

Centralnym obiektem systemu jest **PRODUCT — produkt chemiczny**. Model domenowy
opisuje `docs/tasks/CORE-001_MSDS_Manager_v1.3-approved_DECISION_EVIDENCE.md`.

## Funkcje

Sekcje interfejsu Streamlit:

- **Produkty** — rejestr produktów, dane administracyjne, rewizje SDS,
  pobieranie aktualnego SDS, bezpieczne usuwanie omyłkowych wpisów.
- **Dodaj SDS** — import PDF do kontrolowanego repozytorium, ekstrakcja
  Sekcji 2, 3 i 11 do draftu, jawna akceptacja przez użytkownika.
- **Decyzja BHP** — rejestracja decyzji (APPROVED / REJECTED) z dowodem PDF.
- **Stanowiska** — słownik miejsc stosowania, przypisania produktów, ilość
  szczytowa i miesięczne zużycie z kontrolowanym słownikiem jednostek.
- **Widok nadzorczy** — zestawienie PRODUCT × USAGE_LOCATION ze statusami.
- **Analizy** — dashboard KPI, sekcja „Wymaga uwagi”, podsumowanie producentów.

Wynik automatycznej ekstrakcji jest wyłącznie draftem; decyzje podejmuje
człowiek. Dane znaczące historycznie nie są nadpisywane.

## Stack

Python, PostgreSQL, SQLAlchemy 2, Alembic, psycopg, pypdf, Streamlit, pytest.

## Struktura

```text
app/
  domain/          modele, enumy i reguły domenowe
  application/     use case'y, porty, DTO
  infrastructure/  konfiguracja, repozytoria SQLAlchemy, storage plików, ekstrakcja PDF
  presentation/    interfejs Streamlit
migrations/        migracje Alembic
scripts/           diagnostyka i smoke testy
tests/             testy unit i integracyjne (PostgreSQL)
docs/tasks/        zatwierdzone dokumenty CORE / BDR / TDR / SPRINT / TASK / PATCH
docs/task_reports/ raporty z wykonania Tasków
```

Zasady pracy z Taskami opisują `AGENTS.md` i `docs/tasks/README.md`.

## Uruchomienie w Dockerze (zalecane)

Wymagany jest Docker z Docker Compose. `docker-compose.yml` uruchamia dwa
kontenery:

- `db` — PostgreSQL 17, dane w wolumenie `pgdata`,
- `app` — aplikacja Streamlit; przy każdym starcie wykonuje
  `alembic upgrade head`, a potem uruchamia interfejs.

Pliki SDS i dowody BHP są zapisywane na dysku hosta, w katalogach
`./data/sds` i `./data/bhp_evidence`. Utwórz je przed pierwszym startem:

```bash
mkdir -p data/sds data/bhp_evidence
```

```powershell
New-Item -ItemType Directory -Force data\sds, data\bhp_evidence
```

Start:

```bash
docker compose up -d --build
```

Aplikacja jest dostępna pod adresem <http://localhost:8501>.

Przydatne polecenia:

```bash
docker compose logs -f app                                # logi aplikacji
docker compose exec app python scripts/check_environment.py  # diagnostyka
docker compose exec app python scripts/smoke_application.py  # smoke test
docker compose down                                       # zatrzymanie (dane zostają)
docker compose down -v                                    # zatrzymanie i USUNIĘCIE bazy
```

Opcjonalne zmienne (np. w pliku `.env` obok `docker-compose.yml`):

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `MSDS_DB_NAME` | `msds_manager` | nazwa bazy |
| `MSDS_DB_USER` | `msds` | użytkownik bazy |
| `MSDS_DB_PASSWORD` | `msds` | hasło bazy — zmień przed użyciem produkcyjnym |
| `MSDS_APP_PORT` | `8501` | port aplikacji na hoście |

Aplikacja nasłuchuje tylko na `127.0.0.1`. Baza nie jest wystawiona na
zewnątrz kontenerów. Kopia zapasowa to zrzut bazy plus katalog `data/`:

```bash
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

Na Linuksie kontener działa jako użytkownik o UID 1000. Jeśli Twój UID jest
inny, zbuduj obraz z `docker compose build --build-arg APP_UID=$(id -u)`.

## Uruchomienie natywne na Windows

### Wymagania

- Python
- PostgreSQL uruchomiony natywnie w Windows

### Przygotowanie środowiska

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Utwórz lokalny plik konfiguracji na podstawie przykładu:

```powershell
Copy-Item .env.example .env
```

Uzupełnij lokalny `.env` własnymi wartościami. Nie zapisuj tego pliku w Git.

Wymagane zmienne:

- `DATABASE_URL` — adres lokalnej bazy PostgreSQL,
- `SDS_ROOT_PATH` — istniejący katalog repozytorium dokumentów SDS,
- `BHP_EVIDENCE_ROOT_PATH` — istniejący katalog dowodów decyzji BHP.

Aplikacja nie tworzy katalogów SDS ani BHP — muszą istnieć przed startem.

### Schemat bazy danych

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### Uruchomienie aplikacji

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/main.py
```

### Diagnostyka środowiska

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
.\.venv\Scripts\python.exe scripts\smoke_application.py
```

`check_environment.py` wykonuje odczytowy test `SELECT 1` i sprawdza istnienie
obu skonfigurowanych katalogów. `smoke_application.py` wykonuje minimalny
odczyt przez warstwę aplikacji.

## Testy

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Testy integracyjne korzystają z bazy wskazanej w `DATABASE_URL`. Testy
wymagające pustej bazy są pomijane, jeśli baza zawiera dane.
