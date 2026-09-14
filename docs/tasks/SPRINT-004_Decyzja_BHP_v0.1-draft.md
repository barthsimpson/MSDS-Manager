# SPRINT-004 — Decyzja BHP i dowód decyzji

**Projekt:** MSDS Manager  
**Sprint ID:** SPRINT-004  
**Wersja:** 0.1-draft  
**Status:** Draft — do zatwierdzenia  
**Etap Roadmapy:** R5 — Decyzje BHP i warunki dopuszczenia  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca Tasków:** Codex OpenAI  
**Właściciel decyzji:** Architekt Operacyjny  

---

## 1. Cel Sprintu

Zbudować prosty workflow rejestracji decyzji Specjalisty BHP dla konkretnego PRODUCT i konkretnego CURRENT SDS wraz z obowiązkowym dowodem źródłowym.

Docelowy przebieg:

```text
PRODUCT = PENDING_APPROVAL
        ↓
CURRENT SDS
        ↓
[ Dodaj decyzję BHP ]
        ↓
wybór dowodu z BHP_EVIDENCE_ROOT_PATH
        ↓
APPROVED / REJECTED
        ↓
opcjonalne notes
        ↓
[ ZAPISZ ]
        ↓
BHP_DECISION CURRENT
+ DECISION_EVIDENCE
        ↓
APPROVED → PRODUCT = ACTIVE
REJECTED → PRODUCT = REJECTED
```

Sprint nie automatyzuje decyzji BHP. Decyzję zawsze wprowadza człowiek.

---

## 2. Zasada MVP

R5 ma być prostym rejestrem decyzji i dowodu.

Nie budujemy:
- workflow engine,
- kartoteki osób BHP,
- podpisu elektronicznego,
- automatycznej analizy treści decyzji,
- OCR/AI dla dowodu,
- wielostopniowej akceptacji,
- osobnych warunków jako rozbudowanych struktur.

`notes` pozostaje prostym polem tekstowym.

---

## 3. Obowiązujące źródła

Sprint realizuje zatwierdzone decyzje:

- aktualny CORE-001,
- BDR-004 v1.0-approved,
- BDR-003 v1.0-approved,
- TDR-001,
- TDR-002,
- TDR-003,
- TDR-004,
- SPRINT-003,
- root `AGENTS.md`.

Jeżeli implementacja ujawni brak decyzji biznesowej:

```text
STOP
```

Nie zgaduj.

---

## 4. Model BHP_DECISION

Minimalny model:

```text
BHP_DECISION
├── decision_id
├── product_id
├── sds_id
├── decision_status
│     ├── APPROVED
│     └── REJECTED
├── notes
├── registered_at
├── record_status
│     ├── CURRENT
│     └── SUPERSEDED
└── evidence_id
```

Decyzja zawsze dotyczy:
- konkretnego PRODUCT,
- konkretnego zatwierdzonego SDS.

Nie jest wydawana osobno dla miejsca stosowania.

---

## 5. DECISION_EVIDENCE

Każda decyzja musi posiadać jeden dowód źródłowy:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Dopuszczalne formaty:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Dowód znajduje się w:

```text
BHP_EVIDENCE_ROOT_PATH
```

Aplikacja:
- zapisuje metadane i relative_path,
- nie kopiuje,
- nie przenosi,
- nie usuwa,
- nie zmienia nazwy pliku.

Repozytorium dowodów jest read-only.

---

## 6. Wynik decyzji

Dozwolone wartości:

```text
APPROVED
REJECTED
```

Nie ma statusu `PENDING` dla BHP_DECISION.

Brak decyzji dla CURRENT SDS reprezentuje:

```text
PRODUCT = PENDING_APPROVAL
```

---

## 7. Wpływ decyzji na PRODUCT

Aktualna decyzja steruje `PRODUCT.usage_status`.

```text
APPROVED
→ PRODUCT = ACTIVE

REJECTED
→ PRODUCT = REJECTED
```

`INACTIVE` pozostaje niezależnym statusem wyłączenia ze stosowania.

---

## 8. Notes

Pole:

```text
notes
```

jest opcjonalne.

Może zawierać:
- warunki stosowania,
- cytat z decyzji,
- komentarz,
- uzasadnienie,
- dodatkowe informacje.

Nie tworzymy osobnego modelu warunków dopuszczenia.

---

## 9. Osoba i data decyzji

MVP nie przechowuje osobnego:

```text
decided_by
decision_date
```

System zapisuje:

```text
registered_at
```

Informacja o osobie i faktycznej dacie pozostaje w dokumencie dowodowym.

---

## 10. Historia decyzji

Zatwierdzonej decyzji nie edytujemy.

Korekta / nowa decyzja dla tego samego SDS:

```text
old BHP_DECISION CURRENT → SUPERSEDED
new BHP_DECISION         → CURRENT
```

Poprzedni rekord i jego dowód pozostają w historii.

Dla jednego `sds_id` może istnieć wiele historycznych decyzji, ale maksymalnie jedna:

```text
record_status = CURRENT
```

---

## 11. Nowy SDS

Nowy CURRENT SDS:
- nie dziedziczy starej decyzji,
- ustawia PRODUCT = PENDING_APPROVAL,
- wymaga nowej decyzji BHP.

Poprzednia decyzja pozostaje związana z poprzednim `sds_id`.

---

## 12. Transakcja

Rejestracja decyzji musi być atomowa:

```text
validate evidence
        ↓
old decision CURRENT → SUPERSEDED (jeśli istnieje)
        ↓
new DECISION_EVIDENCE
        ↓
new BHP_DECISION CURRENT
        ↓
PRODUCT usage_status
        ↓
PRODUCT_HISTORY snapshot
        ↓
COMMIT
```

Dowolny błąd:

```text
ROLLBACK całości
```

Nie może istnieć BHP_DECISION bez dowodu.

---

## 13. UI

Minimalny UI:

```text
Produkt / CURRENT SDS
        ↓
[ Dodaj decyzję BHP ]
        ↓
wybór pliku dowodu
        ↓
APPROVED / REJECTED
        ↓
notes
        ↓
[ Zapisz ]
```

Po zapisie użytkownik powinien widzieć:
- wynik decyzji,
- PRODUCT status,
- registered_at,
- informację o dowodzie,
- notes.

Bez dodatkowych wizardów i dashboardów.

---

## 14. Dostępność dowodu

Po rejestracji plik dowodu może zostać później usunięty/przeniesiony poza aplikacją.

Nie usuwa to:
- BHP_DECISION,
- historii,
- metadanych dowodu.

UI powinien móc sygnalizować brak pliku źródłowego.

Nie zmieniaj automatycznie decyzji z powodu `MISSING`.

---

## 15. Poza zakresem Sprintu 4

Nie implementujemy:
- automatycznej decyzji BHP,
- AI/LLM/OCR dla dowodu,
- kartoteki osób BHP,
- podpisu elektronicznego,
- workflow wielu zatwierdzających,
- powiadomień,
- REACH,
- przeglądów okresowych,
- importu produkcyjnego,
- upload service,
- storage service.

---

## 16. Proponowany backlog

### TASK-022 — BHP Decision Application Contracts
- DTO,
- porty,
- use case kontrakt,
- walidacja wejścia,
- bez persystencji/UI.

### TASK-023 — BHP Decision Persistence & Transaction
- BHP_DECISION,
- DECISION_EVIDENCE,
- ORM/schema/migracja jeśli potrzebna,
- CURRENT/SUPERSEDED,
- PRODUCT ACTIVE/REJECTED,
- PRODUCT_HISTORY,
- rollback PostgreSQL.

### TASK-024 — Streamlit „Decyzja BHP”
- wybór produktu/CURRENT SDS,
- wybór dowodu,
- APPROVED/REJECTED,
- notes,
- zapis przez Application,
- widok bieżącej decyzji.

### TASK-025 — Sprint 4 End-to-End Acceptance
- PENDING_APPROVAL → APPROVED → ACTIVE,
- korekta → SUPERSEDED + nowa CURRENT,
- REJECTED → PRODUCT REJECTED,
- dowód 1:1,
- historia,
- cleanup,
- pełna regresja.

---

## 17. Definition of Done Sprintu 4

Sprint jest gotowy do closure, gdy:

1. można wskazać PRODUCT z CURRENT SDS i PENDING_APPROVAL,
2. można wybrać dowód z BHP_EVIDENCE_ROOT_PATH,
3. dowód jest wymagany,
4. można zapisać APPROVED,
5. APPROVED ustawia PRODUCT = ACTIVE,
6. można zapisać REJECTED,
7. REJECTED ustawia PRODUCT = REJECTED,
8. decyzja zawsze wskazuje product_id i sds_id,
9. istnieje dokładnie jeden dowód na decyzję,
10. maksymalnie jedna decyzja CURRENT na sds_id,
11. korekta tworzy nową decyzję,
12. poprzednia decyzja przechodzi na SUPERSEDED,
13. poprzedni rekord i dowód pozostają w historii,
14. notes działa,
15. registered_at jest zapisany,
16. brak decided_by/decision_date w MVP,
17. całość jest transakcyjna,
18. rollback działa,
19. PRODUCT_HISTORY zachowuje zmianę statusu,
20. plik dowodu nie jest modyfikowany,
21. brak automatycznej decyzji BHP,
22. E2E Sprintu 4 przechodzi.

---

## 18. Kryterium sukcesu biznesowego

Dla produktu oczekującego na decyzję użytkownik może odpowiedzieć:

> Czy BHP dopuściło produkt, na podstawie którego SDS, jaki jest dowód i jakie były ewentualne warunki?

oraz po korekcie:

> Jakie były poprzednie decyzje?

---

## 19. Stan wejściowy

Po Sprint 3:

```text
PRODUCT
└── CURRENT SDS
    ├── SAFETY_PROFILE
    └── SDS_COMPONENTS

PRODUCT.usage_status = PENDING_APPROVAL
```

Sprint 4 rozpoczyna pracę od tego stanu.

---

## 20. Stan końcowy oczekiwany

```text
PRODUCT = PENDING_APPROVAL
        ↓
CURRENT SDS
        ↓
BHP_DECISION + EVIDENCE
        ↓
     ┌────────────┐
     │            │
 APPROVED      REJECTED
     │            │
     ↓            ↓
  ACTIVE       REJECTED
```

Historia kolejnych decyzji pozostaje zachowana przez CURRENT/SUPERSEDED.

---

## 21. Autoryzacja

Dokument Sprintu nie stanowi automatycznie zgody na wykonanie Tasków.

Po zatwierdzeniu każdy Task wymaga osobnego polecenia.

Status po zatwierdzeniu:

```text
SPRINT-004 v1.0-approved
```
