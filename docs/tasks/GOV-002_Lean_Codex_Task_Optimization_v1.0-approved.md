# GOV-002 — Lean Codex: zasady optymalizacji Tasków

**Projekt:** MSDS Manager  
**Wersja:** 1.0-approved  
**Status:** APPROVED  
**Właściciel:** Architekt Operacyjny  
**Stosuje:** Cerberus — Agent Architekt

## 1. Cel

Ograniczyć zbędne zużycie kontekstu, tokenów/creditów i czasu Codexa bez osłabiania poprawności, integralności, governance, testowalności ani zasady STOP.

> Codex wykonuje najmniejszy uzasadniony zakres analizy i walidacji potrzebny do bezpiecznego wykonania konkretnego Tasku.

Cerberus nie przerzuca na Codex ponownego odkrywania informacji, które są już znane i rozstrzygnięte.

## 2. Tryby Tasków

Każdy nowy Task otrzymuje `TASK MODE`.

### PATCH
Lokalna, dobrze określona zmiana, np. UI, formularz, mały use case, bugfix.

Domyślnie:
- minimalna eksploracja,
- wskazane pliki startowe,
- focused tests,
- bez pełnego audytu repo,
- bez pełnej regresji, jeśli ryzyko jej nie wymaga.

### INTEGRATION
Zmiana łącząca kilka warstw lub trwałe dane.

Domyślnie:
- ograniczony przegląd powiązanych warstw,
- focused + integration tests,
- dodatkowe kontrole proporcjonalne do ryzyka.

### ACCEPTANCE / CHECKPOINT
Zamknięcie Sprintu/etapu albo zmiana wysokiego ryzyka.

Domyślnie:
- E2E,
- pełna regresja,
- SAWarning,
- Alembic/schema check dla DB,
- cleanup/integralność,
- pełniejszy raport.

## 3. LC-1 — Context Locality

Codex czyta tylko materiały potrzebne bezpośrednio do Tasku.

Task wskazuje `AUTHORITATIVE CONTEXT`. Nie należy rutynowo czytać całego CORE/BDR/TDR/Sprint/history, jeśli podany kontekst wystarcza.

Szerszy governance czytamy dopiero przy konkretnej sprzeczności, braku decyzji lub wymaganiu nadrzędnym z `AGENTS.md`.

## 4. LC-2 — Minimal Exploration First

Jeżeli Cerberus zna pliki lub symbole, wskazuje je jako `KNOWN STARTING POINTS`.

Codex zaczyna od nich i nie wykonuje repo-wide search tylko po to, aby ponownie odkryć znaną lokalizację.

> Minimal inspection first. Expand only on evidence.

Szersze wyszukiwanie jest uzasadnione, gdy wskazany punkt nie istnieje, zależność prowadzi dalej, test ujawnia problem albo bez dodatkowego odczytu nie da się bezpiecznie wykonać Tasku.

## 5. LC-3 — Validation Proportionality

### LEVEL 1 — PATCH
- focused unit/AppTests,
- test bezpośrednio zmienionego komponentu,
- lokalna kontrola diff, jeśli potrzebna.

Bez automatycznego pełnego pytest/Alembic/E2E.

### LEVEL 2 — INTEGRATION
- focused tests,
- właściwe integration tests,
- regresja powiązanego obszaru,
- DB/schema check tylko gdy uzasadnione zmianą.

### LEVEL 3 — ACCEPTANCE / CHECKPOINT
- pełny pytest,
- E2E,
- SAWarning,
- Alembic current/check,
- schema/integrity,
- cleanup i wymagane kontrole bezpieczeństwa.

Pełna regresja pozostaje domyślnie obowiązkowa przed formalnym closure Sprintu.

## 6. LC-4 — No Opportunistic Work

Codex nie wykonuje pracy „przy okazji”.

Nie:
- refaktoryzuje niezwiązanych modułów,
- poprawia stylu innych plików,
- przebudowuje architektury,
- aktualizuje zależności bez potrzeby,
- analizuje przyszłych etapów,
- naprawia problemów spoza zakresu.

Problem spoza zakresu → wpis w raporcie.  
Problem blokujący → STOP.

## 7. LC-5 — Known Change Surface

Jeżeli miejsce zmiany jest znane, Task podaje:

```text
EXPECTED CHANGE SURFACE:
- file A
- file B
- test C

DO NOT TOUCH:
- Domain
- ORM
- migrations
- unrelated modules
```

Jeżeli bezpośrednio konieczny jest dodatkowy plik, Codex może rozszerzyć zakres zgodnie z Taskiem i jawnie opisuje to w raporcie.

Zmiana Core/schema/decyzji biznesowej nadal podlega STOP, gdy wymaga tego governance.

## 8. LC-6 — No Redundant Rediscovery

Cerberus przekazuje znane fakty techniczne potrzebne do pracy, np.:

```text
ListSupervisoryProducts:
app/application/use_cases/list_supervisory_products.py
```

Codex nie musi ponownie przeszukiwać repo, aby udowodnić podany punkt startowy. Wystarczy lokalna weryfikacja pliku.

## 9. LC-7 — Short Reports by Default

PATCH/standardowy INTEGRATION używa krótkiego raportu:

```text
STATUS: DONE / PARTIAL / BLOCKED

CHANGED:
- ...

IMPLEMENTED:
- ...

VALIDATION:
- ...

SCOPE:
- no Core change
- no schema change
- no new dependencies

RISKS / DEVIATIONS:
- ...

NEXT:
OCZEKUJĘ NA JAWNE POLECENIE.
```

Pełny raport: ACCEPTANCE/CHECKPOINT, zmiana Core/schema, ważna integracja/transakcja lub istotny BLOCKED.

## 10. LC-8 — Do Not Repeat Proven Validation

Właściwości udowodnione w zaakceptowanym Tasku nie są ponownie szczegółowo testowane przez kolejny lokalny Task, jeżeli ten ich nie zmienia.

Przykład:

```text
TASK-026:
CURRENT SDS/BHP + filesystem + requires_action
→ zweryfikowane

TASK-027:
prezentacja read modelu
→ testuje UI i filtry
→ nie testuje ponownie logiki CURRENT
```

Całość wraca do pełnej walidacji na ACCEPTANCE/CHECKPOINT.

## 11. LC-9 — STOP Instead of Exploration Spiral

Jeżeli wykonanie zaczyna wymagać coraz szerszego poszukiwania poza przewidywanym zakresem, Codex nie eksploruje repo bez końca.

Po minimalnej uzasadnionej eksploracji brak decyzji, źródła, kontraktu lub jednoznacznej zależności → `STOP / BLOCKED` z konkretnym opisem braku.

STOP jest bezpieczniejszy i tańszy niż zgadywanie.

## 12. LC-10 — Optimization Is Not a Quality Override

Oszczędność tokenów/creditów nie uzasadnia:
- pominięcia krytycznego testu,
- ignorowania błędu,
- obejścia governance,
- zgadywania,
- naruszenia transakcyjności,
- pominięcia schema check przy zmianie schema,
- pominięcia E2E przy closure Sprintu.

Priorytet:

```text
1. poprawność
2. integralność
3. governance
4. minimalna wystarczająca praca
5. koszt wykonania
```

Optymalizujemy nadmiar, nie bezpieczeństwo.

## 13. Standardowy format nowych Tasków

```text
# TASK-XXX — Nazwa

MODE:
PATCH / INTEGRATION / ACCEPTANCE

GOAL:
jednoznaczny rezultat

AUTHORITATIVE CONTEXT:
minimalna lista źródeł

KNOWN STARTING POINTS:
konkretne pliki / symbole

EXPECTED CHANGE SURFACE:
przewidywane pliki

DO:
wymagania

DO NOT:
granice

VALIDATION:
LEVEL 1 / 2 / 3 + konkretne testy

STOP CONDITIONS:
konkretne blokery

REPORT:
SHORT / FULL

AUTHORIZATION:
jawne polecenie
```

Dodatkowe sekcje tylko wtedy, gdy są potrzebne do jednoznacznego wykonania.

## 14. Checklista Cerberusa przed wydaniem Tasku

```text
Czy znam miejsce zmiany?
YES → podaj je Codexowi.

Czy Task jest lokalny?
YES → PATCH.

Czy cały governance jest naprawdę potrzebny?
NO → podaj tylko minimalne źródła.

Czy pełna regresja jest potrzebna teraz?
NO → focused validation.

Czy właściwość została już udowodniona?
YES → nie testuj jej ponownie lokalnie.

Czy raport musi być długi?
NO → SHORT REPORT.
```

## 15. Relacja do governance

GOV-002 nie zastępuje Konstytucji, GOV-001, PDP, Core, ADR/BDR/TDR, `AGENTS.md`, jawnej autoryzacji Tasków ani zasady STOP.

Określa sposób konstruowania instrukcji wykonawczej: wystarczający kontekst bez nadmiarowej eksploracji.

W konflikcie pierwszeństwo mają nadrzędne zatwierdzone dokumenty projektu.

## 16. Kryterium skuteczności

W kolejnych Taskach oczekujemy:
- mniej repo-wide discovery bez potrzeby,
- mniej ponownego czytania niezmienionego governance,
- mniej zbędnych pełnych regresji pomiędzy checkpointami,
- krótszych raportów lokalnych Tasków,
- zachowania STOP dla realnych braków,
- niepogorszonej jakości pełnych checkpointów.

Doświadczenia z kolejnych Tasków mogą być podstawą rewizji GOV-002.

## 17. Decyzja

```text
GOV-002
LEAN CODEX TASK DESIGN
STATUS: APPROVED

DEFAULT:
minimal context
minimal exploration
proportional validation
no opportunistic work
short reports

FULL VALIDATION:
acceptance / checkpoint / high-risk change
```
