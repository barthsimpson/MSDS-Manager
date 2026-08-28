# MSDS Manager

Projekt znajduje się w fazie bootstrap.

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
- `SDS_ROOT_PATH` — istniejący katalog źródłowy dokumentów SDS,
- `BHP_EVIDENCE_ROOT_PATH` — istniejący katalog dowodów BHP.

Aplikacja nie tworzy katalogów SDS ani BHP. Baza nie zawiera jeszcze tabel
domenowych.

## Diagnostyka środowiska

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
```

Diagnostyka wykonuje wyłącznie odczytowy test `SELECT 1` i sprawdza istnienie
obu skonfigurowanych katalogów.

## Testy

```powershell
.\.venv\Scripts\python.exe -m pytest
```
