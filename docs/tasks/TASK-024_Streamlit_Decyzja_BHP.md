# TASK-024 — Streamlit „Decyzja BHP”

**Projekt:** MSDS Manager  
**Task ID:** TASK-024  
**Sprint:** SPRINT-004 — Decyzja BHP i dowód decyzji  
**Status:** READY  
**Typ:** Presentation / Streamlit / Application wiring  
**Nadzór:** Cerberus — Agent Architekt  
**Wykonawca:** Codex OpenAI  

---

## 1. Cel Tasku

Udostępnić użytkownikowi minimalny widok Streamlit do rejestracji decyzji BHP dla produktu posiadającego CURRENT SDS.

Widok ma korzystać wyłącznie z mechanizmów Application i Infrastructure z TASK-022/TASK-023.

Docelowy workflow:

```text
PRODUCT + CURRENT SDS
        ↓
[ Decyzja BHP ]
        ↓
wybór dowodu z BHP_EVIDENCE_ROOT_PATH
        ↓
APPROVED / REJECTED
        ↓
opcjonalne notes
        ↓
[ Zapisz decyzję ]
        ↓
RegisterBhpDecision
        ↓
PostgreSQL
        ↓
APPROVED → PRODUCT ACTIVE
REJECTED → PRODUCT REJECTED
```

TASK-024 nie tworzy nowej logiki biznesowej.

---

## 2. Źródła obowiązujące

Przed implementacją przeczytaj co najmniej:

- root `AGENTS.md`,
- aktualny `CORE-001`,
- `BDR-004`,
- `TDR-001`,
- `TDR-002`,
- `TDR-003`,
- `TDR-004`,
- `SPRINT-004`,
- `TASK-022` + `TASK-022_REPORT`,
- `TASK-023` + `TASK-023_REPORT`.

Jeżeli UI wymaga nowej reguły biznesowej lub zmiany Core:

```text
STOP
```

Nie zgaduj.

---

## 3. Zasada implementacyjna

Streamlit jest cienką warstwą Presentation.

Dozwolony kierunek:

```text
Streamlit
   ↓
ShellComposition
   ↓
Application use cases / ports
   ↓
Infrastructure
```

Streamlit nie może:
- wykonywać SQL,
- importować modeli ORM,
- importować repozytoriów Infrastructure bezpośrednio,
- wykonywać commit/rollback,
- ustawiać statusu PRODUCT samodzielnie,
- tworzyć BHP_DECISION samodzielnie,
- analizować pliku evidence.

---

## 4. Wejście do funkcji

Dodaj w istniejącej nawigacji prostą funkcję:

```text
Decyzja BHP
```

Nie twórz osobnej aplikacji ani nowego shell.

Widok powinien umożliwić pracę na produktach, dla których istnieje CURRENT SDS.

Preferowany przypadek podstawowy:

```text
PRODUCT = PENDING_APPROVAL
```

Nie duplikuj reguł walidacyjnych backendu — ostateczna walidacja PRODUCT/SDS pozostaje w `RegisterBhpDecision` / repository.

---

## 5. Wybór PRODUCT

Użytkownik powinien wybrać produkt w czytelnej formie.

Minimalnie pokaż identyfikację pozwalającą odróżnić produkty, np.:

```text
product_name
manufacturer_product_code
manufacturer_name
usage_status
```

Po wyborze UI ma operować na rzeczywistym:

```text
product_id
```

Nie identyfikuj produktu wyłącznie po nazwie.

Nie implementuj fuzzy search ani deduplikacji.

---

## 6. CURRENT SDS

Dla wybranego produktu pokaż jego CURRENT SDS.

Minimalnie:

```text
filename
issue_date
revision
document_status
```

Do `RegisterBhpDecisionInput` przekaż rzeczywisty:

```text
sds_id
```

Jeżeli PRODUCT nie ma CURRENT SDS:
- pokaż kontrolowaną informację,
- nie pozwalaj zapisać decyzji.

Nie implementuj obejścia.

---

## 7. Bieżąca decyzja BHP

Jeżeli dla CURRENT SDS istnieje już decyzja `CURRENT`, pokaż użytkownikowi jej podstawowe dane:

```text
decision_status
registered_at
notes
evidence_relative_path
```

Nie edytuj jej bezpośrednio.

Nowe zapisanie decyzji oznacza:

```text
old CURRENT → SUPERSEDED
new decision → CURRENT
```

Regułę wykonuje backend z TASK-023.

UI jedynie informuje użytkownika, że zapis nowej decyzji zastąpi bieżącą decyzję.

Nie buduj osobnego workflow „Edytuj decyzję”.

---

## 8. Wybór dowodu

UI ma wyświetlać istniejące dopuszczalne pliki znajdujące się pod:

```text
BHP_EVIDENCE_ROOT_PATH
```

Dopuszczalne rozszerzenia:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Lista może być rekurencyjna, analogicznie do `SDS_ROOT_PATH` w TASK-020.

Do Application przekazuj wyłącznie:

```text
evidence_relative_path
```

Nie implementuj:
- uploadu,
- kopiowania,
- przenoszenia,
- usuwania,
- zmiany nazwy,
- podglądu treści MSG/PDF,
- OCR.

Ostateczną walidację pliku wykonuje `BhpEvidenceValidator`.

---

## 9. Formularz decyzji

Minimalny formularz:

```text
Produkt
CURRENT SDS
Dowód decyzji
Decyzja: APPROVED / REJECTED
Notes
[ Zapisz decyzję ]
```

Statusy do wyboru wyłącznie:

```text
APPROVED
REJECTED
```

Nie pokazuj statusu `PENDING`.

Dla użytkownika można użyć czytelnych polskich etykiet, np.:

```text
Dopuszczony
Odrzucony
```

ale do Application przekazuj zatwierdzone wartości enum:

```text
APPROVED
REJECTED
```

---

## 10. Notes

`notes` jest opcjonalne i edytowalne jako proste pole tekstowe.

Nie twórz:
- struktury warunków dopuszczenia,
- osobnych pól PPE,
- osobnych pól wentylacji,
- osobnych ograniczeń stanowiskowych,
- formularza wielosekcyjnego.

Jeżeli BHP podało warunki, użytkownik może wpisać je w `notes`.

---

## 11. Zapis

Kliknięcie:

```text
Zapisz decyzję
```

ma zbudować:

```text
RegisterBhpDecisionInput
```

i wywołać wyłącznie:

```text
RegisterBhpDecision
```

UI nie może wykonywać części operacji samodzielnie.

Backend odpowiada za:
- evidence validation,
- PRODUCT/SDS validation,
- CURRENT/SUPERSEDED,
- evidence persistence,
- decision persistence,
- Product status,
- ProductHistory,
- transaction/rollback.

---

## 12. Komunikat sukcesu

Po sukcesie pokaż czytelnie wynik.

Dla APPROVED, np.:

```text
Decyzja BHP została zapisana.
Produkt został dopuszczony do stosowania.
Status produktu: ACTIVE.
```

Dla REJECTED, np.:

```text
Decyzja BHP została zapisana.
Produkt nie został dopuszczony do stosowania.
Status produktu: REJECTED.
```

Komunikat powinien wynikać z `RegisterBhpDecisionResult`, nie z własnego ustawiania statusu przez UI.

---

## 13. Stan po zapisie

Po sukcesie odśwież dane widoku tak, aby użytkownik zobaczył:
- aktualny PRODUCT status,
- aktualną decyzję CURRENT,
- registered_at,
- evidence path,
- notes.

Nie utrzymuj starego stanu formularza jako fałszywie aktywnego.

---

## 14. Kontrolowane błędy

Błędy Application/Infrastructure mają być pokazane przez:

```text
st.error
```

Dotyczy co najmniej:
- brak evidence,
- niepoprawny evidence,
- brak PRODUCT,
- brak CURRENT SDS,
- SDS nie należy do PRODUCT,
- SDS nie jest CURRENT,
- błąd persystencji.

Nie pokazuj użytkownikowi:
- stack trace,
- SQL,
- DATABASE_URL,
- sekretów,
- surowych wyjątków technicznych, jeśli istnieje kontrolowany komunikat Application.

Błąd nie może być pokazany jako sukces.

---

## 15. Brak pliku po wcześniejszej decyzji

Jeżeli zapisana decyzja wskazuje evidence, którego fizycznie już nie ma pod `BHP_EVIDENCE_ROOT_PATH`:

- rekord decyzji pozostaje ważny historycznie,
- UI może oznaczyć dowód jako brakujący / niedostępny,
- nie zmieniaj decision_status,
- nie zmieniaj PRODUCT status.

Nie implementuj automatycznego naprawiania ścieżki.

Jeżeli obecna warstwa odczytu nie umożliwia prostego sprawdzenia tego bez rozszerzania zakresu, opisz ograniczenie w raporcie i nie buduj dodatkowego subsystemu.

---

## 16. Composition

Rozszerz istniejący `ShellComposition` minimalnie o operacje potrzebne ekranowi.

Preferowane jest wykorzystanie:
- istniejącej sesji/TransactionExecutor,
- `RegisterBhpDecision`,
- `BhpEvidenceValidator`,
- `SqlAlchemyBhpDecisionRepository`,
- istniejących mechanizmów odczytu PRODUCT/SDS, jeśli już są.

Jeżeli do wyświetlenia CURRENT decision potrzebny jest minimalny read method/DTO, dodaj najmniejszy możliwy kontrakt zgodny z aktualną architekturą.

Nie buduj CQRS/read-model framework.

---

## 17. Testy UI

Dodaj testy Streamlit/AppTest obejmujące co najmniej:

### A. PRODUCT z CURRENT SDS

```text
produkt widoczny
→ CURRENT SDS widoczny
→ formularz decyzji dostępny
```

### B. APPROVED

```text
evidence selected
→ APPROVED
→ Save
→ RegisterBhpDecision called once
→ success
→ wynik ACTIVE pokazany
```

### C. REJECTED

```text
REJECTED
→ Save
→ wynik REJECTED pokazany
```

### D. notes

```text
notes wpisane
→ trafiają do RegisterBhpDecisionInput
```

### E. brak evidence

```text
Save
→ controlled error
→ brak fałszywego sukcesu
```

### F. brak CURRENT SDS

```text
czytelna informacja
→ brak możliwości zapisu
```

### G. istniejąca CURRENT decision

```text
bieżąca decyzja widoczna
→ nowy zapis korzysta z RegisterBhpDecision
```

Nie testuj logiki CURRENT→SUPERSEDED w UI — jest już odpowiedzialnością backendu TASK-023.

---

## 18. Opcjonalny manual smoke

Jeżeli środowisko pozwala, wykonaj manual smoke:

```text
PRODUCT PENDING_APPROVAL
+ CURRENT SDS
+ testowy evidence pod BHP_EVIDENCE_ROOT_PATH
→ Decyzja BHP
→ APPROVED
→ PRODUCT ACTIVE
```

Nie dodawaj trwałych testowych danych ani evidence.

Brak możliwości manual smoke nie blokuje Tasku, jeśli AppTest i backend integration są pełne.

---

## 19. Brak zmian schema

TASK-024 nie powinien zmieniać:
- Domain,
- ORM,
- PostgreSQL schema,
- Alembic.

Oczekiwany head:

```text
e0dd7d6468bf
```

Jeżeli UI wymaga schema change:

```text
STOP
```

---

## 20. Brak nowych zależności

Nie dodawaj bibliotek.

Jeżeli UI wymaga nowej zależności:

```text
STOP
```

---

## 21. Poza zakresem

Nie implementuj:

```text
AI/OCR
analizy treści evidence
uploadu
kopiowania plików
podpisu elektronicznego
decided_by
decision_date
wielostopniowej akceptacji
powiadomień
REACH
dashboardu BHP
osobnej kartoteki BHP
edycji starej decyzji
generic audit
```

Nie rozpoczynaj TASK-025.

---

## 22. Regression

Po implementacji uruchom:

```powershell
$env:PATH = "C:\Program Files\PostgreSQL\17\bin;$env:PATH"
.\.venv\Scripts\python.exe -m pytest -q -W error::sqlalchemy.exc.SAWarning
```

Baseline po TASK-023:

```text
133 passed
```

Wymagane:
- focused UI tests PASS,
- pełna regresja PASS,
- brak `SAWarning`.

---

## 23. Alembic

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Oczekiwane:

```text
e0dd7d6468bf (head)
No new upgrade operations detected.
```

---

## 24. Git / bezpieczeństwo

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Potwierdź:
- `.env` ignored,
- brak sekretów,
- brak nowych trwałych evidence,
- brak dumpów/backupów,
- brak commit/push bez polecenia.

---

## 25. STOP CONDITIONS

Zatrzymaj jako `PARTIAL / BLOCKED`, jeżeli:
- potrzebna jest nowa reguła biznesowa,
- potrzebna jest zmiana Core,
- potrzebna jest migracja/schema change,
- potrzebna jest nowa zależność,
- istniejący backend TASK-023 nie wystarcza do wykonania workflow,
- trzeba rozpocząć TASK-025.

Minimalny read contract potrzebny wyłącznie do pokazania danych istniejącej decyzji nie jest blockerem, jeśli nie wprowadza nowej reguły biznesowej.

---

## 26. Definition of Done

TASK-024 = DONE, gdy:

1. istnieje widok `Decyzja BHP`,
2. użytkownik może wybrać PRODUCT,
3. CURRENT SDS jest widoczny,
4. brak CURRENT SDS blokuje zapis,
5. użytkownik może wybrać evidence z BHP_EVIDENCE_ROOT_PATH,
6. UI przekazuje relative path,
7. dostępne są tylko APPROVED/REJECTED,
8. notes jest opcjonalne,
9. Save wywołuje `RegisterBhpDecision`,
10. UI nie zapisuje danych bezpośrednio,
11. APPROVED pokazuje wynik ACTIVE,
12. REJECTED pokazuje wynik REJECTED,
13. istniejąca CURRENT decision jest widoczna,
14. nowa decyzja nie edytuje starej bezpośrednio,
15. błędy są kontrolowane,
16. brak stack trace/SQL/secrets,
17. brak upload/copy/move/delete evidence,
18. brak zmian Domain/ORM/schema,
19. brak nowych zależności,
20. focused tests PASS,
21. pełny pytest PASS,
22. brak SAWarning,
23. Alembic bez driftu,
24. TASK-025 nie został rozpoczęty.

---

## 27. Raport

Utwórz:

```text
docs/task_reports/TASK-024_REPORT.md
```

Raport ma zawierać:

1. status `DONE / PARTIAL / BLOCKED`,
2. zmienione pliki,
3. nawigację/widok,
4. sposób wyboru PRODUCT,
5. prezentację CURRENT SDS,
6. listowanie evidence,
7. formularz APPROVED/REJECTED,
8. notes,
9. wywołanie `RegisterBhpDecision`,
10. komunikaty sukcesu,
11. prezentację CURRENT decision,
12. obsługę błędów,
13. testy focused,
14. ewentualny manual smoke,
15. pełny pytest,
16. SAWarning,
17. Alembic current/check,
18. potwierdzenie braku schema changes,
19. Git/bezpieczeństwo,
20. odstępstwa/ryzyka.

Na końcu:

```text
OCZEKUJĘ NA JAWNE POLECENIE.
NIE ROZPOCZYNAM TASK-025.
```

---

## 28. Autoryzacja

Sama obecność pliku Tasku nie stanowi zgody na wykonanie.

Start dopiero po poleceniu:

```text
Wykonaj TASK-024.
```
