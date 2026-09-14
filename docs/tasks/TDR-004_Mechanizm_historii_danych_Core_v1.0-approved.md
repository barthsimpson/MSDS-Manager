# TDR-004 — Mechanizm historii danych Core

**Projekt:** MSDS Manager  
**Id dokumentu:** TDR-004  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-09-03  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  
**Powiązane zagadnienia:** IR-001-22, IR-001-23  
**Powiązany Sprint:** SPRINT-002 v1.2-approved  
**Powiązany Task:** TASK-015 — Product History Mechanism  

---

## 1. Cel decyzji

Celem TDR-004 jest zatwierdzenie technicznego mechanizmu historyzacji danych Core MSDS Manager w PostgreSQL.

Decyzja ma usunąć bramkę architektoniczną przed TASK-015 i określić jednoznacznie:

- gdzie przechowywana jest historia,
- które zmiany tworzą zapis historyczny,
- jaki model historyzacji stosujemy,
- jak historia uczestniczy w transakcji,
- czego mechanizm historii nie obejmuje,
- jakie rozwiązania są świadomie odrzucone.

CORE-001 v1.2-approved wymaga zachowania historii m.in. statusów, przypisań PRODUCT–USAGE_LOCATION, zmian statusu lokalizacji, `peak_quantity` i `monthly_consumption`, ale pozostawia techniczny mechanizm jako otwartą decyzję. SPRINT-002 v1.2-approved blokuje TASK-015 do czasu zatwierdzenia tej decyzji.

---

## 2. Zasada nadrzędna

Dla MVP zatwierdza się:

> **jawne domenowe tabele historii w PostgreSQL, z zapisem snapshotu stanu przy każdej istotnej zmianie, wykonywanym przez warstwę Application/Infrastructure w tej samej transakcji co zmiana danych bieżących.**

Model:

```text
CURRENT STATE
────────────────────────────
PRODUCT
USAGE_LOCATION
PRODUCT_USAGE_LOCATION

        │
        │ istotna zmiana
        ▼

APPLICATION
        │
        ▼
TransactionExecutor
        │
        ├── UPDATE/INSERT current state
        └── INSERT history snapshot
        │
        ▼
COMMIT / ROLLBACK
```

Historia jest częścią tej samej transakcji co zmiana bieżącego stanu.

Jeżeli zapis historii nie powiedzie się, zmiana bieżąca nie może zostać zatwierdzona.

---

## 3. Wybrany wariant

Wybrano wariant:

```text
A — jawne tabele historii
```

oraz jego podwariant:

```text
A2 — snapshot stanu po istotnej zmianie
```

Nie stosujemy historii typu delta jako podstawowego mechanizmu MVP.

---

## 4. Uzasadnienie wyboru

Snapshot pozwala bez rekonstruowania łańcucha zmian odpowiedzieć na pytanie:

> **Jaki był stan produktu, lokalizacji lub przypisania produktu do lokalizacji w określonym momencie?**

Każdy wpis historyczny zawiera pełny zestaw zatwierdzonych pól historyzowanych dla danego obszaru.

Przykład:

```text
PRODUCT_USAGE_LOCATION_HISTORY #1
peak = 20 kg
monthly = NULL

PRODUCT_USAGE_LOCATION_HISTORY #2
peak = 35 kg
monthly = NULL

PRODUCT_USAGE_LOCATION_HISTORY #3
peak = 35 kg
monthly = 120 kg
```

Odczyt stanu historycznego nie wymaga odtwarzania wszystkich poprzednich delta events.

---

## 5. Jawność domenowa historii

Nie tworzymy jednego generycznego mechanizmu `AUDIT_LOG`.

Historia ma być modelowana jawnie dla tych obszarów Core, które rzeczywiście wymagają audytowalności.

Dla Sprintu 2 zatwierdza się co najmniej:

```text
PRODUCT_HISTORY

USAGE_LOCATION_HISTORY

PRODUCT_USAGE_LOCATION_HISTORY
```

Dokładne nazwy tabel/klas mogą zostać technicznie dostosowane w TASK-015, pod warunkiem zachowania znaczenia tej decyzji.

Nie należy tworzyć jednej tabeli historii dla wszystkich encji.

---

## 6. Zakres historii PRODUCT w Sprint 2

Dla PRODUCT zatwierdza się snapshot biznesowo istotnego stanu:

```text
product_id
usage_status
use_description
use_restriction
waste_type
waste_code
changed_at
```

Historia PRODUCT ma pozwalać odtworzyć, jaki był administracyjny stan produktu w określonym momencie.

Pola tożsamości:

```text
product_name
manufacturer_product_code
manufacturer_id
```

pozostają chronioną tożsamością PRODUCT i nie są zwykłymi polami edytowalnymi. Ich zmiana oznacza nowy PRODUCT zgodnie z Core.

TDR-004 nie zmienia tej zasady.

---

## 7. Zakres historii USAGE_LOCATION

Dla USAGE_LOCATION historyzowane jest co najmniej:

```text
location_id
status
changed_at
```

Snapshot ma pozwalać odtworzyć przejścia:

```text
ACTIVE → INACTIVE
INACTIVE → ACTIVE
```

Historia nie zastępuje rekordu bieżącego.

Bieżący rekord nadal posiada aktualny status.

---

## 8. Zakres historii PRODUCT_USAGE_LOCATION

Dla relacji PRODUCT–USAGE_LOCATION historyzowany snapshot obejmuje co najmniej:

```text
product_id
location_id
peak_quantity_value
peak_quantity_unit
monthly_consumption_value
monthly_consumption_unit
changed_at
```

Historia ma być tworzona przy istotnej zmianie tych danych.

Dla istniejącej relacji zmiana quantity nie nadpisuje historii poprzedniego stanu.

---

## 9. Historia utworzenia przypisania

Utworzenie nowego PRODUCT_USAGE_LOCATION jest istotnym wydarzeniem historycznym.

Po poprawnym utworzeniu relacji należy zapisać pierwszy snapshot historii reprezentujący jej początkowy stan.

Model:

```text
AssignProductUsageLocation
        ↓
INSERT current relation
        +
INSERT initial history snapshot
        ↓
COMMIT
```

---

## 10. Brak usuwania relacji w Sprint 2

SPRINT-002 nie zatwierdza jeszcze `RemoveProductUsageLocation`.

TDR-004 nie wprowadza usuwania relacji.

Nie definiuje także technicznej semantyki historyzacji usunięcia relacji.

Jeżeli przyszła decyzja biznesowa dopuści zakończenie/usunięcie przypisania, mechanizm będzie wymagał osobnego rozszerzenia TDR/BDR.

---

## 11. Moment zapisu historii

Snapshot jest zapisywany **po zaakceptowaniu nowego stanu przez Domain/Application, ale w tej samej transakcji przed commit**.

Przykład:

```text
UpdateProductUsageLocation
        ↓
Domain/Application validation
        ↓
Repository updates current state
        ↓
History repository inserts snapshot
        ↓
TransactionExecutor.commit()
```

Nie zapisujemy historii przed walidacją biznesową.

---

## 12. Transakcyjność

Obowiązuje twarda reguła:

```text
current state change
+
history snapshot
=
ONE TRANSACTION
```

Wyniki:

```text
oba zapisy OK
→ COMMIT

którykolwiek zapis FAIL
→ ROLLBACK wszystkiego
```

Nie dopuszcza się sytuacji:

```text
current state changed
history missing
```

ani:

```text
history inserted
current state not changed
```

---

## 13. Warstwa odpowiedzialna za zapis

Historia nie jest tworzona przez Streamlit.

Streamlit uruchamia use case Application.

Application koordynuje zmianę biznesową i potrzebę historyzacji.

Infrastructure implementuje techniczny zapis snapshotu w PostgreSQL.

Model pozostaje zgodny z TDR-003:

```text
presentation
    ↓
application
    ↓
domain

infrastructure
    ↑
implementuje ports
```

---

## 14. Porty historii

TASK-015 może wprowadzić jawne porty Application dla historii, np.:

```text
ProductStatusHistoryRepositoryPort
UsageLocationHistoryRepositoryPort
ProductUsageLocationHistoryRepositoryPort
```

lub równoważne minimalne porty.

Nie tworzymy:

```text
GenericHistoryRepository
AuditRepository[T]
GenericAuditService
```

Porty mają wynikać z konkretnych przypadków użycia.

---

## 15. ORM i PostgreSQL

Tabele historii są technicznym persistence i należą do:

```text
app/infrastructure/db/models/
```

SQLAlchemy 2.x pozostaje warstwą ORM.

PostgreSQL pozostaje jedyną bazą operacyjną MVP.

Nowe tabele historii wymagają wersjonowanej migracji Alembic.

Nie używamy:

```text
Base.metadata.create_all()
```

jako sposobu wdrożenia historii.

---

## 16. Identyfikatory rekordów historii

Każdy rekord historyczny musi posiadać własny niezmienny identyfikator, np.:

```text
history_id
```

Nie zastępuje on identyfikatora biznesowego/historyzowanego obiektu.

Historia zachowuje odniesienie do właściwego:

```text
product_id
location_id
```

zgodnie z typem historyzowanego obiektu.

Dokładny typ techniczny identyfikatora pozostawia się TASK-015, zgodnie z istniejącym stylem projektu.

---

## 17. Czas zmiany i identyfikacja osoby

Każdy snapshot posiada:

```text
changed_at
```

Czas reprezentuje moment zatwierdzenia zmiany w systemie.

Dla MVP obowiązkowym celem audytowalności jest odpowiedź:

```text
co się zmieniło
kiedy się zmieniło
jaki był stan / jaka była ilość
```

Nie wymaga się obecnie identyfikacji osoby dokonującej zmiany.

Dlatego TDR-004 nie wprowadza obowiązkowo:

```text
changed_by
user_id
```

Założeniem operacyjnym obecnego wdrożenia jest praca jednej osoby wprowadzającej dane.

Nie dodawaj fikcyjnego użytkownika `SYSTEM` ani modelu użytkowników wyłącznie na potrzeby historii. Jeżeli w przyszłości pojawi się wielu operatorów lub wymaganie pełnego user audit trail, będzie to osobna decyzja.

---

## 18. Typ zmiany

Dopuszczalne jest przechowywanie prostego technicznego pola:

```text
change_type
```

jeżeli jest ono potrzebne do rozróżnienia co najmniej:

```text
CREATED
UPDATED
STATUS_CHANGED
```

Nie ustanawia się przez to rozbudowanego event sourcingu.

Jeżeli implementacja może pozostać jednoznaczna bez `change_type`, TASK-015 może go pominąć.

Nie dodawaj rozbudowanego słownika zdarzeń bez potrzeby.

---

## 19. Snapshot vs delta

TDR-004 zatwierdza snapshot.

Nie zatwierdza głównego modelu:

```text
old_value
new_value
field_name
```

dla każdej pojedynczej zmiany.

Nie budujemy historii jako atomowych delta records dla każdej kolumny.

Dopuszczalne jest przyszłe wyliczenie różnic między dwoma snapshotami w warstwie raportowej.

---

## 20. Brak triggerów PostgreSQL

Nie używamy triggerów do tworzenia historii w MVP.

Odrzucony wariant:

```text
UPDATE table
    ↓
PostgreSQL trigger
    ↓
history table
```

Powody:

- ukryta logika poza kodem Application,
- drugi mechanizm wykonywania reguł,
- trudniejszy audyt zachowania przez Codexa/Cerberusa,
- trudniejsze testowanie i migracje,
- niepotrzebna złożoność dla lokalnego MVP.

Trigger może zostać rozważony później, jeżeli wiele niezależnych aplikacji będzie zapisywać do tej samej bazy.

---

## 21. Brak generycznego AUDIT_LOG

Odrzucony wariant:

```text
AUDIT_LOG
├── entity_type
├── entity_id
├── old_values JSONB
├── new_values JSONB
└── changed_at
```

Powody:

- utrata jawności modelu domenowego,
- konieczność interpretowania JSON,
- ryzyko stworzenia frameworka audytowego,
- trudniejsze odtworzenie konkretnego stanu biznesowego,
- nadmierna generalizacja względem potrzeb MVP.

Nie tworzymy generycznego systemu audytu „na przyszłość”.

---

## 22. Brak event sourcing

TDR-004 nie wprowadza event sourcingu.

Bieżące tabele pozostają źródłem aktualnego stanu.

Historia służy audytowalności i rekonstrukcji wcześniejszego stanu, a nie jako jedyne źródło bieżącego modelu.

---

## 23. Odczyt historii

TASK-015 powinien umożliwić co najmniej techniczny odczyt historii dla potrzeb testów i przyszłego UI.

TDR-004 nie wymaga jeszcze pełnego ekranu historii w Streamlit.

Minimalny zakres:

```text
get history by product_id
get history by location_id
get relation history by product_id + location_id
```

lub równoważny zestaw portów/use case'ów.

TASK-016 ma móc potwierdzić historię w scenariuszu E2E.

---

## 24. Kolejność historii

Historia musi umożliwiać deterministyczne uporządkowanie rekordów w czasie.

Minimalnie:

```text
changed_at
```

Jeżeli dwa rekordy mogą mieć identyczny timestamp, dodatkowym tie-breakerem może być:

```text
history_id
```

Nie wymaga to dodatkowego mechanizmu sekwencyjnego poza normalnym PK.

---

## 25. Korekta danych błędnych

IR-001-23 dotyczy korekty błędnych rekordów bez utraty audytowalności.

TDR-004 zatwierdza zasadę techniczną:

> Korekta bieżącego, historyzowanego pola odbywa się poprzez zapis nowego stanu i nowego snapshotu; poprzedni snapshot nie jest nadpisywany ani usuwany.

TDR-004 nie ustanawia jeszcze osobnego workflow „korekta błędu” ani reason code.

Nie dodawaj `correction_reason` bez osobnej decyzji biznesowej.

---

## 26. Niezmienność rekordów historii

Rekordy historyczne po zapisaniu są traktowane jako immutable z punktu widzenia standardowych use case'ów aplikacji.

Nie implementuj:

```text
UpdateHistory
DeleteHistory
```

w normalnym workflow.

Korekta stanu bieżącego tworzy kolejny snapshot.

---

## 27. Fizyczne usuwanie historii

Standardowa aplikacja nie usuwa rekordów historii.

Nie dodawaj:

```text
DeleteHistory
PurgeHistory
RetentionCleanup
```

Polityka retencji nie jest przedmiotem TDR-004.

Jeżeli w przyszłości będzie wymagana prawna/operacyjna polityka retencji, wymaga osobnej decyzji.

---

## 28. Historia a backup

Mechanizm historii nie zastępuje backupu PostgreSQL.

TDR-004 nie rozstrzyga IR-001-37 dotyczącego polityki kopii zapasowych.

Historia:

```text
= audytowalność zmian biznesowych
```

Backup:

```text
= ochrona przed utratą danych
```

Są to dwa różne mechanizmy.


---

## 28A. Historia Core a przegląd / audyt okresowy

Historia Core i okresowy przegląd fizyczny są dwoma różnymi mechanizmami.

Historia Core odpowiada na pytania:

```text
co się zmieniło
kiedy się zmieniło
jaki był zatwierdzony stan danych
```

Przegląd / audyt okresowy ma w przyszłości rejestrować stan stwierdzony podczas fizycznego obchodu i porównywać go ze stanem deklarowanym w systemie.

Przykładowy przyszły przebieg może wykorzystywać:

```text
skan kodu stanowiska
→ otwarcie przeglądu stanowiska
→ skan produktu
→ wpisanie stwierdzonej ilości
→ porównanie z danymi Core
```

TDR-004 nie projektuje jeszcze modelu danych przeglądu, kodów kreskowych ani automatycznej aktualizacji Core na podstawie wyniku audytu.

Wynik przeglądu nie może samoczynnie nadpisywać danych Core bez osobnego zatwierdzonego workflow.

---

## 29. Historia a dokumenty SDS/BHP

TDR-004 nie zmienia istniejącego mechanizmu wersjonowania:

```text
SDS CURRENT / ARCHIVED
BHP_DECISION CURRENT / SUPERSEDED
```

Te obiekty posiadają własną naturalną historię rekordów Core.

TASK-015 Sprintu 2 nie ma rozszerzać historii SDS/BHP.

Zakres TASK-015 pozostaje skupiony na PRODUCT / USAGE_LOCATION / PRODUCT_USAGE_LOCATION.

---

## 30. Historia a pola administracyjne PRODUCT

Dla Sprintu 2 obowiązkowo historyzujemy:

```text
PRODUCT
    usage_status
    use_description
    use_restriction
    waste_type
    waste_code

USAGE_LOCATION
    status

PRODUCT_USAGE_LOCATION
    peak_quantity
    monthly_consumption
```

Dzięki temu historia pozwala odtworzyć nie tylko status produktu, ale również jego administracyjny kontekst w danym momencie.

Nie oznacza to historyzowania każdej technicznej kolumny tabeli PRODUCT.

---

## 31. Historia przypisań a brak RemoveProductUsageLocation

W aktualnym Core przypisanie nie posiada jeszcze zatwierdzonej operacji zakończenia/usunięcia.

Dlatego TASK-015:

- zapisuje snapshot przy utworzeniu relacji,
- zapisuje snapshot przy zmianie quantity,
- nie implementuje zdarzenia `REMOVED`,
- nie tworzy sztucznego statusu relacji.

Jeżeli przyszły proces wymaga zakończenia relacji, konieczna jest osobna decyzja.

---

## 32. Transakcje istniejące w projekcie

TASK-010 wprowadził `TransactionExecutor`.

TASK-015 powinien wykorzystać istniejącą granicę transakcji.

Nie tworzymy drugiego transaction managera ani nowego frameworka Unit of Work wyłącznie dla historii.

Jeżeli aktualny `TransactionExecutor` wymaga minimalnego rozszerzenia, może ono zostać wykonane wyłącznie w zakresie niezbędnym do atomowego zapisu current + history.

Nie należy budować pełnego UoW frameworka bez potrzeby.

---

## 33. Model logiczny

Docelowo:

```text
PRODUCT
   │
   └── PRODUCT_HISTORY

USAGE_LOCATION
   │
   └── USAGE_LOCATION_HISTORY

PRODUCT_USAGE_LOCATION
   │
   └── PRODUCT_USAGE_LOCATION_HISTORY
```

Relacje historii są append-only z perspektywy standardowego workflow aplikacji.

---

## 34. Przykład — zmiana quantity

Stan bieżący:

```text
PRODUCT_USAGE_LOCATION
peak = 20 kg
monthly = NULL
```

Użytkownik zmienia:

```text
peak = 35 kg
```

Transakcja:

```text
UPDATE current
    peak = 35 kg

INSERT history snapshot
    product_id = ...
    location_id = ...
    peak = 35 kg
    monthly = NULL
    changed_at = ...
```

Po commit:

```text
CURRENT = 35 kg

HISTORY:
#1 20 kg
#2 35 kg
```

Pierwszy snapshot powstaje przy utworzeniu relacji.

---

## 35. Przykład — deactivate lokalizacji

Stan:

```text
USAGE_LOCATION.status = ACTIVE
```

Operacja:

```text
DeactivateUsageLocation
```

Transakcja:

```text
UPDATE current
status = INACTIVE

INSERT USAGE_LOCATION_HISTORY
status = INACTIVE
changed_at = ...
```

Po rollback żaden z tych zapisów nie może pozostać.

---

## 36. Przykład — reaktywacja

```text
INACTIVE → ACTIVE
```

tworzy kolejny snapshot historii tej samej lokalizacji.

`location_id` pozostaje bez zmian.

---

## 37. Testy

TASK-015 musi obejmować co najmniej:

### Domain/Application
- history snapshot jest wymagany dla zatwierdzonej istotnej zmiany,
- brak historyzacji nie może skutkować poprawnym commit.

### PostgreSQL
- snapshot zapisuje się poprawnie,
- pola quantity zachowują `Decimal`,
- NULL/0 zachowują semantykę,
- historia jest uporządkowana.

### Transaction
- current update + history insert → commit razem,
- błąd history insert → rollback current update,
- błąd current update → brak history insert.

### Regression
- istniejące reguły Core pozostają zielone.

---

## 38. Migracje

Dodanie tabel historii wymaga jednej lub większej liczby wersjonowanych migracji Alembic zgodnie z zakresem TASK-015.

Preferowana jest jedna spójna migracja TASK-015, jeżeli nie istnieje techniczna potrzeba rozdzielenia.

Każda migracja musi przejść:

```text
review
upgrade
downgrade
re-upgrade
alembic check
```

Nie wolno omijać istniejących zabezpieczeń enum CHECK i constraintów Core.

---

## 39. Indeksy

Tabele historii powinny posiadać minimalne indeksy potrzebne do typowych odczytów historycznych.

Co najmniej należy rozważyć indeksy po:

```text
product_id
location_id
changed_at
```

oraz dla historii relacji:

```text
(product_id, location_id, changed_at)
```

TASK-015 ma dobrać minimalne indeksy zgodnie z rzeczywistymi query patterns.

Nie optymalizuj „na przyszłość” bez potrzeby.

---

## 40. Foreign keys

Historia powinna zachować odniesienie do bieżących identyfikatorów Core.

Jednocześnie historia nie może zostać usunięta kaskadowo przez usunięcie bieżącego rekordu.

Nie dodawaj:

```text
ON DELETE CASCADE
```

dla tabel historii.

Jeżeli FK do bieżącego rekordu uniemożliwia zachowanie historii w scenariuszu dopuszczonego przyszłego usunięcia encji, zastosuj STOP i zgłoś potrzebę decyzji zamiast samodzielnie rozstrzygać model.

---

## 41. UI historii

TASK-015 nie musi implementować pełnego ekranu historii.

Dopuszczalne jest dodanie minimalnego read-only widoku, jeśli jest potrzebny do acceptance Sprintu 2.

Nie buduj:
- timeline framework,
- zaawansowanych filtrów,
- eksportów,
- dashboardów historii.

Głównym celem TASK-015 jest poprawny persistence + application mechanism.

---

## 42. Odrzucone warianty

### B — generyczny `AUDIT_LOG`

Odrzucony dla MVP.

### C — triggery PostgreSQL

Odrzucony dla MVP.

### Event sourcing

Odrzucony.

### Delta per field jako główny model

Odrzucony.

Wybrano:

```text
jawne history tables
+
snapshot
+
Application-controlled write
+
same transaction
```

---

## 43. Konsekwencje pozytywne

- jawna i czytelna historia biznesowa,
- łatwe odtworzenie stanu na moment czasu,
- zgodność z istniejącą architekturą Application/Infrastructure,
- brak ukrytej logiki w triggerach,
- możliwość kontroli przez testy Python/PostgreSQL,
- brak generycznego frameworka audytowego,
- zachowanie atomicity current + history,
- naturalne rozszerzenie TransactionExecutor.

---

## 44. Koszty i ograniczenia

- dodatkowe tabele i migracja,
- każdy historyzowany workflow wymaga jawnego zapisu snapshotu,
- większa liczba testów integracyjnych,
- brak ochrony przed zmianą danych wykonaną bezpośrednio poza aplikacją.

Ostatnie ograniczenie jest świadomie zaakceptowane dla lokalnego MVP, w którym PostgreSQL jest obsługiwany przez jedną aplikację.

Jeżeli w przyszłości pojawią się niezależne integracje zapisujące do tej samej bazy, można ponownie rozważyć triggery lub inną ochronę infrastrukturalną.

---

## 45. Elementy poza TDR-004

TDR-004 nie rozstrzyga:

- modelu użytkowników,
- `changed_by`,
- uprawnień do historii,
- polityki retencji,
- backupu,
- eksportu historii,
- historii SDS/BHP ponad ich istniejący model wersji,
- historii danych REACH,
- historii zmian manualnych SAFETY_PROFILE,
- szczegółowego UI historii,
- workflow usuwania PRODUCT_USAGE_LOCATION,
- workflow korekty z obowiązkowym reason code.

Te elementy wymagają osobnych decyzji, jeśli pojawi się potrzeba.

---

## 46. Ograniczenia dla Codexa

Codex nie może bez nowej zatwierdzonej decyzji:

- zastąpić jawnych tabel historii generycznym AUDIT_LOG,
- użyć triggerów PostgreSQL,
- wprowadzić event sourcingu,
- dodać JSONB audit framework,
- historyzować wszystkich tabel „na wszelki wypadek”,
- dodać `changed_by` / users,
- dodać retencji/purge,
- dodać delete historii,
- dodać `RemoveProductUsageLocation`,
- rozszerzyć historii na SDS/BHP/REACH,
- dodać nowego frameworka UoW,
- zapisywać historii poza transakcją bieżącej zmiany,
- zmieniać Core w celu uproszczenia persistence.

---

## 47. Rozstrzygnięcie IR-001-22

**Zagadnienie:** Które zmiany danych produktu muszą być historyzowane?

**Status:** częściowo Resolved technicznie w zakresie Sprintu 2.

TDR-004 implementuje zatwierdzony zakres Core dla:

- `PRODUCT.usage_status`,
- `PRODUCT.use_description`,
- `PRODUCT.use_restriction`,
- `PRODUCT.waste_type`,
- `PRODUCT.waste_code`,
- `USAGE_LOCATION.status`,
- `PRODUCT_USAGE_LOCATION.peak_quantity`,
- `PRODUCT_USAGE_LOCATION.monthly_consumption`,
- utworzenia relacji PRODUCT_USAGE_LOCATION.

---

## 48. Rozstrzygnięcie IR-001-23

**Zagadnienie:** Jak korygować błędne rekordy bez utraty audytowalności?

**Status:** częściowo Resolved technicznie.

Zasada:

```text
nie nadpisuj historii
nie usuwaj historii
zapisz poprawiony current state
dodaj nowy snapshot
```

Workflow biznesowy korekty i ewentualny reason code pozostają poza TDR-004.

---

## 49. Warunek uruchomienia TASK-015

Warunek decyzji został spełniony:

```text
TDR-004 v1.0-approved
```

TASK-015 może zostać przygotowany. Sama obecność TDR-004 nie stanowi jednak zgody na wykonanie TASK-015; wykonanie nadal wymaga osobnego, jawnego polecenia Architekta Operacyjnego.

---

## 50. Powiązane dokumenty

TDR-004 należy czytać łącznie z:

- `CORE-001 v1.2-approved`,
- `BDR-002 v1.2-approved`,
- `SPRINT-002 v1.2-approved`,
- TDR-001,
- TDR-002,
- TDR-003,
- ADR-002,
- zaakceptowanymi TASK-009, TASK-010, TASK-011, TASK-012, TASK-013 i TASK-014,
- IR-001,
- PDP-001,
- ROADMAP-001,
- Konstytucją projektu.

---

## 51. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-09-03 | Draft | Wybrano jawne tabele historii PostgreSQL, snapshot A2, zapis przez Application w tej samej transakcji, zakres historii Sprintu 2 oraz odrzucono AUDIT_LOG, triggery i event sourcing |
| 1.0-approved | 2026-09-03 | Approved | Zatwierdzono wariant A/A2; rozszerzono PRODUCT_HISTORY o usage_status i pola administracyjne; potwierdzono audytowalność w zakresie co/kiedy/stan-ilość bez obowiązkowego changed_by; rozdzielono historię Core od przyszłego przeglądu/audytu fizycznego |

---

## 52. Status decyzji

```text
TDR-004
VERSION: 1.0-approved
STATUS: APPROVED
DECISION:
  explicit history tables
  snapshot history
  application-controlled writes
  same PostgreSQL transaction
  PRODUCT_HISTORY includes administrative state
  changed_by not required in MVP
```
