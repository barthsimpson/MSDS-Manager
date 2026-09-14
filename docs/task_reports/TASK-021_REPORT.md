# TASK-021 — Sprint 3 End-to-End Acceptance

## 1. Status

`DONE`

Acceptance Sprintu 3 wykonany. Nie rozpoczęto R5 ani workflow BHP.

## 2. Baseline

Przed acceptance:

- pytest: `119 passed`, bez `SAWarning`,
- Alembic: `e0dd7d6468bf (head)`,
- `alembic check`: brak nowych operacji,
- working tree zawierał wcześniejsze zmiany TASK-015–020; nie były odwracane,
- `.env` pozostaje ignorowany.

## 3. Zmienione pliki

TASK-021 nie wymagał zmian production code ani zmian Domain/ORM/schema. Dodano wyłącznie:

- `tests/integration/test_task021_sprint3_acceptance.py`,
- `docs/task_reports/TASK-021_REPORT.md`.

Test acceptance korzysta z istniejących komponentów TASK-018–020.

## 4. Przygotowanie testowego SDS_ROOT_PATH

Test tworzy tymczasowy katalog `SDS_ROOT_PATH`, kopiuje do niego oryginalny fixture:

```text
docs/tasks/30470_Idrolin_Sherwin_03102025 rew10.02_PL.pdf
```

Tworzy drugą techniczną kopię pod inną ścieżką, aby sprawdzić kolejny SDS tego samego produktu. Oryginalny PDF nie jest modyfikowany. Po teście kopie są usuwane, a dane fixture są usuwane kontrolowanym cleanupem.

## 5. Scenariusz A — pierwszy SDS

AppTest uruchamia `render_add_sds` z prawdziwym `ShellComposition`, prawdziwym PostgreSQL, `PrepareSdsDraft`, `PdfSdsExtractor`, `SdsFileValidator`, `AcceptSds` i `TransactionExecutor`.

Potwierdzono:

- widok `Dodaj SDS` jest dostępny,
- oba pliki są widoczne w wyborze,
- `Odczytaj dane` przechodzi przez `PrepareSdsDraft`,
- `product_name = IDROLIN FONDO RAPIDO IDROS. AD ARIA NERO`,
- `manufacturer_product_code = 30470`,
- `use_description = Farba lub inna podobna substancja.`,
- `use_restriction = Jedynie do stosowania przemysłowego.`,
- `issue_date = 2025-10-03`,
- `revision = 10.02`,
- składnik z CAS `111-76-2` jest obecny w draftcie.

## 6. Manual correction i formularz

Parser pozostawia producenta pustego. Test uzupełnia `manufacturer_name` ręcznie i potwierdza zapis poprawionej wartości przez `AcceptSds`. Formularz zawiera pola produktu/SDS, zatwierdzone pola `SAFETY_PROFILE` i edytowalne `SDS_COMPONENTS`.

## 7. PostgreSQL po pierwszym SDS

Potwierdzono w PostgreSQL:

- MANUFACTURER istnieje,
- jeden PRODUCT o kodzie `30470` istnieje,
- `PRODUCT.usage_status = PENDING_APPROVAL`,
- jeden SDS ma status `CURRENT`,
- SAFETY_PROFILE istnieje,
- SDS_COMPONENTS istnieją,
- istnieje jeden initial PRODUCT_HISTORY snapshot.

## 8. Scenariusz B — kolejny SDS

Druga kopia przechodzi przez ten sam UI workflow. Rewizja zostaje ręcznie zmieniona na `10.03`, aby test potwierdził korektę formularza dla kolejnego dokumentu.

Po akceptacji PostgreSQL potwierdza:

- PRODUCT count dla tej tożsamości: `1`,
- SDS count: `2`,
- stary SDS: `ARCHIVED`,
- nowy SDS: `CURRENT`,
- dokładnie jeden CURRENT,
- PRODUCT nadal `PENDING_APPROVAL`,
- drugi PRODUCT_HISTORY snapshot istnieje,
- poprzedni SDS pozostaje zachowany.

## 9. Scenariusz C — anulowanie

Po `Odczytaj dane` kliknięto `Anuluj`. Draft zniknął z `session_state`, `AcceptSds` nie został wywołany i nie powstały nowe rekordy Core.

## 10. Scenariusz D — kontrolowany błąd

Po ponownym odczycie usunięto wymagane `manufacturer_name` i wykonano akceptację. UI pokazał `st.error`, nie pokazał sukcesu, nie wyświetlił stack trace i pozostawił draft do korekty. Walidacja Application wystąpiła przed zapisem, więc nie powstały częściowe rekordy.

## 11. Cleanup

Po scenariuszach usunięto SDS_COMPONENTS, SAFETY_PROFILE, SDS_DOCUMENTS, PRODUCT_HISTORY, PRODUCT i testowego MANUFACTURER. Tymczasowe kopie PDF zostały usunięte. Test chroni istniejące dane, odrzucając start, jeśli produkt fixture już istnieje.

## 12. Testy i walidacja

- acceptance E2E TASK-021: `1 passed`,
- pełny pytest: `120 passed`,
- `pytest -q -W error::sqlalchemy.exc.SAWarning`: PASS, brak `SAWarning`,
- `alembic current`: `e0dd7d6468bf (head)`,
- `alembic check`: `No new upgrade operations detected.`,
- diagnostyka acceptance: brak błędów.

Schema ma 12 tabel biznesowych oraz techniczną tabelę `alembic_version`, czyli 13 tabel zwróconych przez introspekcję łącznie.

## 13. Architektura

```text
Streamlit
  -> ShellComposition
  -> PrepareSdsDraft / AcceptSds
  -> Infrastructure adapters
  -> TransactionExecutor
  -> PostgreSQL
```

Streamlit nie wykonuje SQL, nie importuje ORM/repozytoriów bezpośrednio, nie wykonuje commit/rollback i nie parsuje PDF. Nie dodano nowych zależności, statusów, migracji ani funkcji biznesowych.

## 14. Git / bezpieczeństwo

Nie wykonano commit ani push. `git diff --check` i `git diff --cached --check` nie wykazały błędów. `.env` jest ignorowany. Nie dodano trwałych fixture testowych, sekretów, dumpów ani backupów; pliki acceptance powstają wyłącznie w katalogu tymczasowym.

## 15. DoD SPRINT-003

| Punkt | Status |
|---|---|
| Funkcja `Dodaj SDS` istnieje | PASS |
| Wybór PDF z `SDS_ROOT_PATH` | PASS |
| Odczyt zatwierdzonych pól | PASS |
| Manual fallback dla braków | PASS |
| Ręczna korekta danych | PASS |
| Brak Core przed akceptacją | PASS |
| Spójny zestaw po akceptacji | PASS |
| Nowy PRODUCT zgodny z Core | PASS |
| Istniejący PRODUCT otrzymuje kolejny SDS | PASS |
| MANUFACTURER poprawnie powiązany | PASS |
| SDS CURRENT | PASS |
| Poprzedni CURRENT przechodzi w ARCHIVED | PASS |
| SAFETY_PROFILE zapisany | PASS |
| SDS_COMPONENTS zapisane | PASS |
| PRODUCT = PENDING_APPROVAL | PASS |
| Atomowość operacji | PASS |
| Rollback działa | PASS |
| PDF nie jest modyfikowany | PASS |
| Brak AI/OCR/parser framework | PASS |
| Brak BHP | PASS |
| Pełna regresja | PASS |
| E2E Sprintu 3 | PASS |

## 16. Odstępstwa i ryzyka

Nie wprowadzono korekty production code. Acceptance używa technicznej kopii fixture dla drugiego dokumentu, zgodnie z zakresem TASK-021; aplikacja produkcyjna nadal nie kopiuje ani nie modyfikuje PDF. Formalna decyzja o zamknięciu Sprintu pozostaje poza zakresem Codex.

Rekomendacja: `READY FOR SPRINT-003 CLOSURE`.

OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM R5 ANI WORKFLOW BHP.
