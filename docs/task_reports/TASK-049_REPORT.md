# TASK-049 REPORT

STATUS: DONE

BATCH: BATCH-001_CX

INPUT:
- PDF count: 37 (wyłącznie wskazany katalog `Paczka1 cx`)

OUTPUT:
- logical SDS: 35
- JSON drafts: 35
- COMPLETE: 19
- NEEDS_REVIEW: 16
- UNREADABLE: 0
- FAILED: 2 (czytelne karty techniczne RC 72, nie SDS)

HUMAN QUESTIONS:
- count: 5
- RESOLVED: 5/5

NEW PATTERNS:
- count: 9 (wyłącznie CANDIDATE)

CHANGED:
- `docs/tasks/GOV-001_Zasady_wspolpracy_v1.0-approved.md` — identyczna kopia zatwierdzonego dokumentu, który był w repozytorium pod nazwą z dopiskiem `(1)`
- `docs/sds_bootstrap/BATCH-001_CX/` — pięć JSON z rozstrzygniętymi polami, zaktualizowany manifest i raport paczki oraz nowy `BATCH-001_GOLDEN_DECISIONS.md`
- `docs/task_reports/TASK-049_REPORT.md` — zaktualizowany raport wykonania
- production code: NO
- DB: NO
- schema: NO

VALIDATION:
- Każdy z 37 PDF ma wpis w manifeście i tabeli raportu.
- 35 JSON poprawnie się parsuje, wskazuje źródłowy PDF, ma zgodny SHA-256 i zakres stron.
- Każde `FOUND` ma dowód obecny na wskazanej stronie źródłowego PDF; brak wartości przy `NOT_FOUND` i `AMBIGUOUS`.
- Dla B001-Q001–Q004 istnieje dokładnie jeden `MANUFACTURER` z `name.value=CX80 POLSKA`, a literal `CX80 POLSKA, CX80 GmbH` pozostaje w `source_text`. Dla B001-Q005 producent ma zatwierdzoną nazwę kanoniczną, a `SBLCore s.r.o.` zachowuje rolę `OTHER`.
- Macierz odpowiedzi i Golden Data zawierają pięć zgodnych decyzji `RESOLVED`. Całe SDS pozostają `PENDING_REVIEW`.
- Oryginalnych PDF nie zmieniono. Nie użyto OCR, nie uruchomiono pełnego pytest, Alembic ani E2E.
- `git diff --no-index --check` dla 37 artefaktów w `docs/sds_bootstrap/BATCH-001_CX/`: PASS.

RISKS / DEVIATIONS:
- Dwa pliki wejściowe to karty techniczne RC 72; nie utworzono dla nich fikcyjnych SDS ani JSON.
- Dwie starsze SDS mają częściowo zdeformowaną warstwę tekstową, choć kluczowe pola są czytelne.
- Pięć pytań o nazwy i role podmiotów rozstrzygnął człowiek. Zatwierdzonych decyzji nie przeniesiono do automatycznej biblioteki normalizacji ani do `SDS-ALIAS-001`.
- Występują rozbieżności między nazwami plików a treścią SDS oraz duplikat bajtowy dwóch plików BONDICX 06. Treść SDS przyjęto jako źródło pól domenowych.
- Poza standardowym katalogiem wyjściowym TASK-049 dodano `GOV-001` i zaktualizowano ten raport na jawne polecenie użytkownika.
- Kopia zatwierdzonego `GOV-001` zachowuje bajtowo oryginalne podwójne spacje kończące wiersze Markdown; `git diff --check` zgłasza je jako trailing whitespace. Nie zmieniono treści zatwierdzonego źródła.

REPORT:
`docs/sds_bootstrap/BATCH-001_CX/BATCH-001_REPORT.md`

NEXT:
CERBERUS REVIEW

OCZEKUJĘ NA DECYZJĘ.
NIE IMPORTUJĘ DANYCH DO MSDS MANAGER.
NIE ROZPOCZYNAM BATCH-002.
