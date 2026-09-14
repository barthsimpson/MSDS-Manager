# TDR-002 — Lokalne środowisko PostgreSQL i konfiguracja

**Projekt:** MSDS Manager  
**Id dokumentu:** TDR-002  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Powiązane IR:** IR-001-34, IR-001-36  

---

## 1. Cel decyzji

Celem TDR-002 jest zdefiniowanie sposobu lokalnego uruchamiania PostgreSQL oraz przechowywania konfiguracji MSDS Manager w MVP.

MVP działa lokalnie na komputerze użytkownika z systemem Windows.

---

## 2. PostgreSQL natywnie na Windows

PostgreSQL jest instalowany i uruchamiany **natywnie w Windows jako lokalna usługa systemowa**.

Docker nie jest elementem środowiska MVP.

Model:

```text
WINDOWS
|
+-- PostgreSQL service
|     +-- database: msds_manager
|
+-- Python virtual environment
|     +-- MSDS Manager
|
+-- SDS_ROOT_PATH
|     +-- *.pdf
|
+-- BHP_EVIDENCE_ROOT_PATH
      +-- *.msg / *.pdf / *.jpg / *.jpeg / *.png
```

Lokalny sposób uruchomienia nie może wymuszać zmiany modelu danych przy przyszłym przeniesieniu PostgreSQL na serwer.

---

## 3. Baza danych

Domyślna nazwa lokalnej bazy:

`msds_manager`

Aplikacja nie może zakładać na stałe:

- hosta,
- portu,
- nazwy bazy,
- użytkownika,
- hasła.

Parametry połączenia są konfiguracją środowiska.

---

## 4. Konfiguracja aplikacji

Konfiguracja lokalna jest przechowywana poza kodem źródłowym.

Dla MVP przyjmuje się plik:

`.env`

w katalogu głównym projektu.

Minimalny zakres konfiguracji:

```text
DATABASE_URL=...
SDS_ROOT_PATH=...
BHP_EVIDENCE_ROOT_PATH=...
```

Aplikacja odczytuje wartości z konfiguracji przy uruchomieniu.

Nie wolno wpisywać rzeczywistych lokalnych ścieżek ani danych logowania bezpośrednio do kodu aplikacji.

---

## 5. DATABASE_URL

`DATABASE_URL` przechowuje parametry połączenia aplikacji z PostgreSQL.

Przykład formatu technicznego:

```text
postgresql+psycopg://USER:PASSWORD@localhost:5432/msds_manager
```

Jest to przykład formatu, a nie rzeczywisty sekret projektu.

Rzeczywiste hasło nie może trafić do repozytorium Git.

---

## 6. SDS_ROOT_PATH

`SDS_ROOT_PATH` wskazuje fizyczny katalog źródłowy dokumentów SDS.

Zgodnie z przyjętymi decyzjami:

- dokumenty pozostają poza PostgreSQL,
- aplikacja przechowuje metadane i ścieżki względne,
- aplikacja traktuje repozytorium SDS jako read-only,
- aplikacja nie usuwa, nie przenosi, nie nadpisuje i nie zmienia nazw plików SDS.

Przykład lokalnej wartości:

```text
SDS_ROOT_PATH=D:\MSDS\SDS
```

Konkretna ścieżka zostanie ustalona podczas konfiguracji stanowiska.

---

## 7. BHP_EVIDENCE_ROOT_PATH

`BHP_EVIDENCE_ROOT_PATH` wskazuje osobny katalog dowodów decyzji BHP.

Repozytorium jest niezależne od `SDS_ROOT_PATH`.

Dopuszczalne w MVP typy plików wynikają z BDR-004:

- `.msg`,
- `.pdf`,
- `.jpg`,
- `.jpeg`,
- `.png`.

Przykład lokalnej wartości:

```text
BHP_EVIDENCE_ROOT_PATH=D:\MSDS\BHP_EVIDENCE
```

Konkretna ścieżka zostanie ustalona podczas konfiguracji stanowiska.

---

## 8. Ścieżki względne w bazie

Baza danych nie powinna przechowywać pełnych lokalnych ścieżek Windows jako podstawowego odwołania do dokumentów.

Dla dokumentów przechowywana jest ścieżka względna względem odpowiedniego katalogu root.

Przykład:

```text
SDS_ROOT_PATH
D:\MSDS\SDS

relative_path
farby\30470.pdf
```

Aplikacja wyznacza fizyczną ścieżkę:

```text
SDS_ROOT_PATH + relative_path
```

Analogiczna zasada obowiązuje dla dowodów BHP.

Pozwala to później zmienić lokalizację całego repozytorium bez przepisywania każdego rekordu dokumentu w bazie.

---

## 9. Plik `.env` i Git

Plik `.env` zawiera konfigurację konkretnego stanowiska i nie może być wersjonowany w Git.

Repozytorium powinno zawierać:

`.env.example`

z nazwami wymaganych zmiennych, ale bez sekretów i bez rzeczywistych ścieżek użytkownika.

Minimalny przykład:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/msds_manager
SDS_ROOT_PATH=C:\PATH\TO\SDS
BHP_EVIDENCE_ROOT_PATH=C:\PATH\TO\BHP_EVIDENCE
```

`.gitignore` musi zawierać co najmniej:

```text
.env
.venv/
__pycache__/
```

Szczegółowy `.gitignore` zostanie przygotowany w repozytorium.

---

## 10. Wirtualne środowisko Python

Aplikacja jest uruchamiana w lokalnym środowisku wirtualnym Pythona.

Preferowana nazwa:

`.venv`

Środowisko wirtualne:

- izoluje zależności projektu,
- nie jest przechowywane w Git,
- może zostać odtworzone z deklaracji zależności projektu.

Sposób deklarowania i blokowania wersji zależności zostanie ustalony przy tworzeniu repozytorium.

---

## 11. Uruchomienie aplikacji

MVP nie wymaga osobnego serwera aplikacyjnego.

Schemat lokalny:

```text
użytkownik
    |
    v
Streamlit / Python
    |
    v
SQLAlchemy + psycopg
    |
    v
PostgreSQL localhost
```

Streamlit jest uruchamiany lokalnie i komunikuje się z lokalną usługą PostgreSQL.

---

## 12. Kontrola dostępności repozytoriów plików

Przy uruchomieniu aplikacja powinna móc sprawdzić, czy skonfigurowane katalogi root istnieją i są dostępne.

Brak katalogu nie może powodować:

- usunięcia rekordów z bazy,
- automatycznego przepisywania ścieżek,
- tworzenia nowego katalogu w przypadkowej lokalizacji.

System powinien zgłosić czytelny błąd konfiguracji.

Kontrola dostępności konkretnego pliku SDS lub dowodu jest odrębna od istnienia jego historycznego rekordu w PostgreSQL.

---

## 13. Dostępność pliku SDS

Dla SDS obowiązuje rozdzielenie:

```text
document_status = CURRENT / ARCHIVED
file_status     = AVAILABLE / MISSING
```

Jeżeli plik został usunięty lub przeniesiony poza aplikacją:

- rekord SDS pozostaje,
- historia pozostaje,
- aplikacja może wykazać `MISSING`.

TDR-002 nie zmienia reguł BDR-003.

---

## 14. Dostępność dowodu BHP

Analogicznie dowód decyzji BHP może stać się fizycznie niedostępny po rejestracji.

Brak pliku:

- nie usuwa `BHP_DECISION`,
- nie usuwa historycznych metadanych dowodu,
- powinien być możliwy do wykrycia przez aplikację.

Szczegółowy sposób prezentacji ostrzeżenia należy do warstwy UI.

---

## 15. Sekrety i bezpieczeństwo konfiguracji

Do repozytorium Git nie mogą trafiać:

- hasła PostgreSQL,
- rzeczywisty `DATABASE_URL` zawierający hasło,
- inne przyszłe sekrety.

Dla lokalnego MVP `.env` jest wystarczającym mechanizmem konfiguracji.

TDR-002 nie ustanawia jeszcze polityki backupu. Jest ona objęta osobnym IR-001-37.

---

## 16. Migracje bazy

Po instalacji PostgreSQL struktura bazy jest tworzona i aktualizowana poprzez Alembic.

Docelowy mechanizm:

```text
pusta baza PostgreSQL
        |
        v
Alembic migrations
        |
        v
aktualny schema MSDS Manager
```

Nie zakłada się ręcznego tworzenia tabel przez użytkownika.

---

## 17. Rozwój do wersji serwerowej

Przeniesienie aplikacji na serwer powinno wymagać przede wszystkim zmiany konfiguracji infrastrukturalnej, np.:

```text
DATABASE_URL
SDS_ROOT_PATH
BHP_EVIDENCE_ROOT_PATH
```

a nie przebudowy Core.

Natywny PostgreSQL na Windows jest decyzją dla lokalnego MVP, nie ograniczeniem docelowej architektury.

---

## 18. Rozstrzygnięcie IR

### IR-001-34 — lokalny PostgreSQL

Status: **Resolved**

Decyzja:

PostgreSQL jest instalowany natywnie na Windows i działa jako lokalna usługa. Docker nie jest używany w MVP.

### IR-001-36 — konfiguracja

Status: **Resolved**

Decyzja:

Konfiguracja lokalna jest przechowywana poza kodem w `.env`. Minimalnie obejmuje:

- `DATABASE_URL`,
- `SDS_ROOT_PATH`,
- `BHP_EVIDENCE_ROOT_PATH`.

Repozytorium zawiera `.env.example`, natomiast `.env` jest wykluczony z Git.

---

## 19. Elementy nierozstrzygnięte przez TDR-002

Dokument nie rozstrzyga:

- polityki backupu PostgreSQL i repozytoriów plików — IR-001-37,
- docelowej struktury repozytorium — IR-001-35 / TDR-003,
- technologii ekstrakcji PDF,
- konfiguracji przyszłego serwera,
- mechanizmu użytkowników i uprawnień.

---

## 20. Ograniczenia dla Codexa

Codex nie może bez zatwierdzonej decyzji:

- dodać Dockera jako wymaganego elementu MVP,
- zastąpić PostgreSQL SQLite,
- zapisywać sekretów w kodzie,
- commitować `.env`,
- wpisywać na stałe lokalnych ścieżek użytkownika,
- przechowywać PDF SDS lub dowodów BHP jako podstawowego rozwiązania wewnątrz PostgreSQL,
- automatycznie modyfikować repozytoriów plików,
- usuwać rekordów historycznych z powodu braku pliku.

---

## 21. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zatwierdzono natywny PostgreSQL na Windows oraz konfigurację przez `.env` z `DATABASE_URL`, `SDS_ROOT_PATH` i `BHP_EVIDENCE_ROOT_PATH` |
