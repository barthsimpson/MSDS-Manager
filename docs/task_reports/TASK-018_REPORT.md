# TASK-018 — Minimal SDS PDF Extraction

## 1. Status

`DONE`

TASK-018 wznowiono po decyzji architekta zatwierdzającej użycie `pypdf`. Nie rozpoczęto TASK-019.

## 2. Biblioteka PDF

- Użyto `pypdf` jako minimalnej biblioteki do odczytu tekstowej warstwy PDF.
- `pypdf` nie był wcześniej zależnością projektu ani nie był dostępny w `.venv`.
- Dodano `pypdf` do `pyproject.toml` i zainstalowano go w `.venv` (`pypdf 6.18.1`).
- Nie użyto OCR, AI/LLM, confidence score ani zewnętrznego lookupu.

## 3. Zmienione pliki TASK-018

- `pyproject.toml`
- `app/infrastructure/filesystem/pdf_sds_extractor.py`
- `tests/unit/test_pdf_sds_extractor.py`
- `tests/integration/test_task018_pdf_sds_extractor.py`
- niniejszy raport

Fixture pozostaje w:

```text
docs/tasks/30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

Nie kopiowano go do `SDS_ROOT_PATH`. Produkcyjna zasada korzystania z `SDS_ROOT_PATH` pozostaje bez zmian.

## 4. Implementacja

`PdfSdsExtractor` implementuje `SdsExtractorPort` i zwraca `ExtractedSdsData`.

- `pypdf.PdfReader` odczytuje tekst ze wszystkich stron.
- Tekst jest dzielony na Sekcje 1, 2, 3 i 11.
- Odczytywane są pola identyfikacyjne: nazwa produktu, kod produktu, zastosowanie, ograniczenie zastosowania, data wydania i rewizja.
- `manufacturer_name` pozostaje `None`, gdy dokument nie wskazuje jednoznacznie producenta.
- Z Sekcji 2 odczytywane są definicja produktu, status klasyfikacji, hasło ostrzegawcze i kody H.
- Dla informacji, których nie można bezpiecznie wyznaczyć z tekstu, zwracane jest `None` lub `NO_DATA`.
- Z Sekcji 3 odczytywane są składniki oraz dostępne CAS, WE, REACH, stężenie, klasyfikacja i kody H.
- Sekcja 11 nie jest interpretowana ponad jednoznaczny tekst; statusy pozostają `NO_DATA`.
- Brak pliku, nie-PDF, uszkodzony PDF lub PDF bez tekstu daje kontrolowany `SdsPdfExtractionError`.

Adapter nie zapisuje danych do Core i nie zmienia kontraktów Application, Domain, ORM ani schematu.

## 5. Wynik testu SDS 30470

Test integracyjny bezpośrednio używa istniejącego fixture i potwierdza:

- `product_name = IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO`,
- `manufacturer_product_code = 30470`,
- `use_description = Farba lub inna podobna substancja.`,
- `use_restriction = Jedynie do stosowania przemysłowego.`,
- `issue_date = 2025-10-03`,
- `revision = 10.02`,
- `product_definition = Mieszanina`,
- klasyfikację produktu `NO`,
- co najmniej jeden składnik z CAS `111-76-2`.

## 6. Testy i walidacja

- Testy TASK-018: `4 passed`.
- Pełny `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS.
- `alembic current`: `e0dd7d6468bf (head)`.
- `alembic check`: `No new upgrade operations detected.`
- Diagnostyka zmienionych plików: brak błędów.
- `git diff --check` i `git diff --cached --check`: brak błędów whitespace.
- Nie dodano migracji ani zmian schematu.
- Nie zmieniono Domain, ORM, PostgreSQL ani Streamlit workflow.

## 7. Git / bezpieczeństwo

W working tree istnieją wcześniejsze, niezależne zmiany TASK-015–017 oraz dostarczone dokumenty i fixture. Nie zostały odwrócone. Zmiany TASK-018 nie zawierają sekretów ani dumpów; fixture PDF jest używany wyłącznie jako istniejący materiał testowy. Nie wykonano commit ani push.

## 8. Odstępstwa i ryzyka

Parser jest celowo minimalny i oparty na układzie tekstowej warstwy PDF. Inne layouty SDS mogą zwrócić `None` lub wymagać ręcznego uzupełnienia. Producent nie jest zgadywany. Brak tekstowej warstwy wymaga manual fallback; OCR pozostaje poza zakresem.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-019.
