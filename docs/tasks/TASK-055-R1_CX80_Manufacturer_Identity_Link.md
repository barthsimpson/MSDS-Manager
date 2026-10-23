# TASK-055-R1 — Human-confirmed manufacturer LINK przed testowym COMMIT ALUCYNK

**Projekt:** MSDS Manager  
**Task:** TASK-055-R1  
**Status:** READY / NOT AUTHORIZED FOR EXECUTION  
**Tryb:** PATCH  
**Walidacja:** LEVEL 1 + ukierunkowana integracja  
**Właściciel decyzji:** Architekt Operacyjny  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel

Usunąć ostatni blocker przed testowym operacyjnym COMMIT-em ALUCYNK poprzez **jawny wybór istniejącego producenta przez operatora**, bez hardkodowania wyjątku `CX80` w logice aplikacji.

Dla przypadku testowego Architekt zatwierdził:

```text
canonical manufacturer z Evidence JSON / Golden Decision:
CX80 POLSKA

istniejący rekord MANUFACTURER:
CX80 Polska

DECISION:
operator może jawnie wybrać istniejący rekord „CX80 Polska” jako ten sam producent
```

Rezultat techniczny ma być **mechanizmem wielokrotnego użycia**:

```text
rozpoznany producent z SDS
→ lista istniejących kandydatów
→ jawny wybór operatora
→ ApprovedImportPlan wiąże istniejący manufacturer_id
→ brak CREATE nowego MANUFACTURER
```

Nie wolno implementować literalnego warunku typu:

```python
if manufacturer == "CX80 POLSKA": ...
```

---

## 2. Kontekst docelowego procesu

BATCH-001_CX jest bootstrapem jednego producenta i nie jest docelowym modelem pracy operatora.

Docelowo SDS będą wprowadzane pojedynczo. Dla nowego wariantu zapisu aplikacja ma w przyszłości pracować w schemacie:

```text
pojedynczy SDS
→ RAW value / label
→ propozycja ujednolicenia
→ operator akceptuje / odrzuca
→ zaakceptowane ujednolicenie staje się kandydatem do biblioteki
→ regression / governance
→ ACTIVE rule
```

**TASK-055-R1 nie implementuje jeszcze biblioteki ujednoliceń.**

W tym Tasku implementujemy tylko właściwą granicę interakcji człowieka:

```text
system proponuje / pokazuje kandydatów
człowiek wybiera istniejącą encję
system nie zgaduje
```

Przyszły moduł biblioteki ma wykorzystać tę samą decyzję operatora, ale pozostaje osobnym Sprintem/Taskiem.

---

## 3. Zatwierdzona decyzja dla testu ALUCYNK

Dla tego przypadku dozwolone jest:

```text
canonical input: CX80 POLSKA
selected existing manufacturer: CX80 Polska
result: LINK do istniejącego manufacturer_id
```

Warunki:

1. LINK wymaga jawnego wyboru / potwierdzenia użytkownika.
2. Brak wyboru użytkownika = brak commit readiness.
3. Nie wykonuj silent-link.
4. Nie twórz nowego `MANUFACTURER`, jeżeli użytkownik wybrał istniejący rekord.
5. Nie zmieniaj nazwy istniejącego rekordu `CX80 Polska`.
6. Nie scalaj ani nie modyfikuj `CX80`, `CX80 Polska`, `Cx80`.
7. Nie wprowadzaj ogólnego fuzzy merge ani automatycznego case-insensitive merge.
8. Nie zapisuj jeszcze reguły do trwałej biblioteki normalizacji producentów.
9. Nie zmieniaj `SDS-ALIAS`; aliasy pól/etykiet i normalizacja wartości producenta pozostają odrębnymi zagadnieniami.

---

## 4. Authoritative context

Minimalnie przeczytaj:

- `TASK-055` i `TASK-055_REPORT`,
- `TASK-053` / controlled commit contract,
- `TASK-052` / manufacturer resolver,
- `BATCH-001_GOLDEN_DECISIONS.md`,
- aktualne `GOV-001` i `GOV-002`,
- `AGENTS.md`.

Nie wykonuj repo-wide discovery.

Decyzja Architekta dla przypadku testowego:

```text
CX80 POLSKA może zostać jawnie powiązany z istniejącym CX80 Polska.
```

Nie interpretuj tego jako ogólnej reguły równoważności nazw.

---

## 5. Known starting points

Sprawdź przede wszystkim miejsca odpowiedzialne za:

```text
manufacturer resolution
ApprovedImportPlan
Stage 1 import plan
Evidence import UI
controlled commit validation
```

Oczekiwane obszary:

```text
app/application/
app/presentation/streamlit/evidence_import.py
tests/
```

Infrastructure DB zmieniaj tylko wtedy, gdy obecny kontrakt nie pozwala przekazać istniejącego `manufacturer_id`.

---

## 6. Wymagane zachowanie

Dla ALUCYNK:

```text
Evidence JSON RAW manufacturer
CX80 POLSKA AGATA NADERA DARIUSZ NADERA SPÓŁKA KOMANDYTOWA

Golden Decision
→ CX80 POLSKA

operator DB candidates
→ CX80
→ CX80 Polska
→ Cx80

operator jawnie wybiera
→ CX80 Polska

ApprovedImportPlan
→ existing manufacturer_id dla CX80 Polska

Stage 1 commit
→ NO new MANUFACTURER
```

UI powinno semantycznie prezentować:

```text
Producent rozpoznany z SDS: CX80 POLSKA

Istniejący producenci:
[ ] CX80
[x] CX80 Polska
[ ] Cx80

[Potwierdzam powiązanie]
```

Nie wymuszaj dokładnej formy kontrolki, jeśli aktualny wzorzec UI ma inną implementację.

Mechanizm ma działać przez **wybrany `manufacturer_id`**, a nie przez specjalny wyjątek tekstowy dla CX80.

---

## 7. Ważna granica — biblioteka ujednoliceń

Nie implementuj jeszcze trwałego workflow:

```text
CANDIDATE → APPROVED → regression → ACTIVE
```

dla normalizacji producentów.

Ale kod R1 nie może utrudniać późniejszego dodania tej funkcji.

Decyzja operatora powinna być reprezentowana tak, aby przyszły Task mógł na jej podstawie utworzyć kandydat ujednolicenia, np. semantycznie:

```text
raw_value
canonical_value
selected_manufacturer_id
human_confirmed = true
```

Nie dodawaj nowej tabeli ani schema w tym Tasku tylko po to, by tę informację utrwalać.

---

## 8. DO NOT

Nie wykonuj w TASK-055-R1:

- realnego COMMIT-u ALUCYNK do operator DB,
- hardkodowanego wyjątku `CX80 POLSKA → CX80 Polska` w production logic,
- zmian `SAFETY_PROFILE` / `SDS_COMPONENT`,
- Etapu 2 Sekcji 2/3/11,
- batch importu,
- biblioteki normalizacji producentów,
- mechanizmu samouczenia runtime,
- automatycznego fuzzy matching,
- automatycznego case-insensitive merge wszystkich producentów,
- zmian nazw istniejących producentów,
- usuwania / scalania rekordów producentów,
- zmian schema / Alembic,
- nowych dependencies,
- zmian SDS lifecycle `CURRENT / ARCHIVED`,
- zmian BHP gate.

---

## 9. Walidacja

### A. Focused tests

Potwierdź:

1. Operator może jawnie wybrać istniejący `CX80 Polska` dla canonical `CX80 POLSKA`.
2. ApprovedImportPlan przechowuje wybrany istniejący `manufacturer_id`.
3. Po LINK nie powstaje nowy rekord MANUFACTURER.
4. `CX80` nie jest automatycznie wybierany.
5. `Cx80` nie jest automatycznie wybierany.
6. Brak jawnego potwierdzenia → brak LINK / brak commit readiness.
7. Inna podobna nazwa nie jest automatycznie powiązana.
8. Mechanizm nie zawiera production hardcode zależnego od literalnego `CX80 POLSKA`.
9. Zmiana wyboru po przygotowaniu planu unieważnia plan zgodnie z istniejącym mechanizmem.

### B. Isolated PostgreSQL

W bazie testowej utwórz:

```text
CX80
CX80 Polska
Cx80
```

i potwierdź, że jawny wybór istniejącego `CX80 Polska`:

```text
canonical CX80 POLSKA
→ selected manufacturer_id(CX80 Polska)
```

kończy się użyciem istniejącego rekordu bez CREATE `CX80 POLSKA`.

### C. Regression

Uruchom wyłącznie powiązane testy TASK-052 / TASK-053 / TASK-054 / TASK-055 manufacturer resolution i controlled import.

Bez full pytest, Alembic cycle i pełnego E2E.

---

## 10. Kryteria akceptacji

| ID | Kryterium | Dowód |
|---|---|---|
| A1 | Jawny wybór istniejącego producenta działa dla ALUCYNK | focused test + isolated PostgreSQL |
| A2 | ApprovedImportPlan wiąże istniejący `manufacturer_id` | test Application |
| A3 | Nie powstaje nowy MANUFACTURER | liczba rekordów przed/po |
| A4 | `CX80` i `Cx80` pozostają nietknięte | test DB |
| A5 | Brak silent-link | negative test |
| A6 | Brak hardcodowanego wyjątku CX80 w production logic | diff/review |
| A7 | Inne podobne nazwy nadal wymagają człowieka | negative test |
| A8 | Stage 1 controlled import pozostaje sprawny | related regression |
| A9 | Operator DB / SDS_ROOT_PATH nie są modyfikowane | raport |
| A10 | Schema / Alembic / lifecycle / Safety bez zmian | diff/report |

---

## 11. STOP conditions

STOP / BLOCKED, jeżeli poprawne wdrożenie wymaga:

- ogólnej zmiany modelu tożsamości producentów,
- migracji danych producentów,
- scalenia istniejących rekordów,
- schema change,
- nowej tabeli aliasów/normalizacji producentów,
- hardkodowania przypadku CX80 jako jedynego sposobu osiągnięcia wyniku,
- wykonania zapisu do operator DB w ramach testów,
- realnego COMMIT-u ALUCYNK przez Codexa.

Nie rozwiązuj tych problemów przy okazji.

---

## 12. Raport

Utwórz:

```text
docs/task_reports/TASK-055-R1_REPORT.md
```

Minimalnie raportuj:

```text
STATUS
CHANGED
IMPLEMENTED
ALUCYNK MANUFACTURER RESOLUTION
NO HARDCODE CONFIRMATION
VALIDATION
OPERATOR SAFETY
SCOPE
DEVIATIONS / RISKS
NEXT
```

Raport ma jawnie potwierdzić:

```text
REAL ALUCYNK COMMIT: 0
```

Po raporcie:

```text
STOP
→ CERBERUS REVIEW
→ PHYSICAL UX
→ OPERATOR TEST COMMIT ALUCYNK
```

---

## 13. Authorization boundary

```text
TASK-055-R1
STATUS: READY / NOT AUTHORIZED
```

Wykonanie dopiero po jawnym poleceniu Architekta:

```text
Wykonaj TASK-055-R1.
```
