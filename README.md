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

## Wymagania

- Python
- PostgreSQL uruchomiony natywnie w Windows

## Przygotowanie środowiska na Windows

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

## Schemat bazy danych

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Uruchomienie aplikacji

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/presentation/streamlit/main.py
```

## Diagnostyka środowiska

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
