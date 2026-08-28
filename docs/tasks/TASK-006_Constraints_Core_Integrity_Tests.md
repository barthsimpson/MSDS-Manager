# TASK-006 — Constraints Core + Integrity Tests

**Projekt:** MSDS Manager  
**Task ID:** TASK-006  
**Sprint:** SPRINT-001 — Foundation / Core Skeleton  
**Status wejściowy:** READY  
**Wykonawca:** Codex OpenAI  
**Nadzór:** Cerberus — Agent Architekt  
**Akceptacja końcowa:** Architekt Operacyjny  

---

## 1. Cel Tasku

Zabezpieczyć krytyczne reguły integralności Core MSDS Manager na poziomie PostgreSQL/SQLAlchemy oraz potwierdzić je testami integracyjnymi.

TASK-006 ma sprawić, aby baza danych odrzucała stany sprzeczne z zatwierdzonym Core nawet wtedy, gdy przyszła warstwa aplikacyjna popełni błąd.

Priorytetem są trzy reguły:

1. maksymalnie jeden `CURRENT` SDS dla jednego produktu,
2. maksymalnie jedna `CURRENT` decyzja BHP dla jednego SDS,
3. `BhpDecision.product_id` musi wskazywać ten sam PRODUCT, do którego należy wskazany `SdsDocument`.

TASK-006 nie implementuje workflow aplikacyjnego zmiany statusów. Zabezpiecza wyłącznie integralność danych.

---

## 2. Warunek wejścia

TASK-005 jest zakończony `DONE` i zaakceptowany.

Stan wejściowy:

- 9 modeli domenowych,
- 9 modeli ORM,
- jedna rewizja Alembic `fdaac4f8756e`,
- baza PostgreSQL jest na `head`,
- istnieje dokładnie 9 tabel aplikacyjnych,
- 40/40 testów przechodzi,
- brak danych biznesowych,
- strategia enumów: `VARCHAR + CHECK`,
- znane zachowanie `alembic check` dla type-bound enum CHECK zostało opisane w TASK-005.

---

## 3. Źródła i hierarchia decyzji

Implementacja musi być zgodna z:

- CORE-001 v1.0-approved,
- BDR-001..005,
- TDR-001..003,
- zaakceptowanymi rezultatami TASK-003, TASK-004 i TASK-005,
- AGENTS.md.

Nie twórz nowych reguł biznesowych.

Jeżeli poprawne zabezpieczenie którejkolwiek reguły wymaga zmiany zatwierdzonego Core albo nowej decyzji biznesowej, zastosuj STOP.

---

## 4. Zasada architektoniczna

Integralność ma być zabezpieczona na właściwym poziomie.

Preferuj:

```text
prosta reguła strukturalna
        ↓
PostgreSQL constraint / index / FK
        ↓
test integracyjny potwierdzający odmowę błędnego zapisu
```

Nie przenoś reguły wyłącznie do UI lub przyszłego use case, jeżeli PostgreSQL może ją jednoznacznie wymusić.

Jednocześnie nie buduj triggerów ani skomplikowanej infrastruktury, jeżeli prostszy constraint/index/FK wystarcza.

---

# CZĘŚĆ A — JEDEN CURRENT SDS NA PRODUCT

## 5. Reguła

Dla jednego `product_id` może istnieć maksymalnie jeden rekord `SdsDocument` ze statusem:

```text
CURRENT
```

Dozwolone:

```text
PRODUCT A
├── SDS-1 ARCHIVED
├── SDS-2 ARCHIVED
└── SDS-3 CURRENT
```

Niedozwolone:

```text
PRODUCT A
├── SDS-1 CURRENT
└── SDS-2 CURRENT
```

Wiele `ARCHIVED` jest dozwolone.

---

## 6. Preferowana implementacja

Dla PostgreSQL preferowany jest partial unique index o semantyce:

```text
UNIQUE(product_id)
WHERE document_status = 'CURRENT'
```

Nazwij go stabilnie i czytelnie, np.:

```text
uq_sds_documents_one_current_per_product
```

Jeżeli aktualny mapping enumów wymaga technicznie innej składni predykatu, zachowaj dokładnie tę samą semantykę.

Nie zmieniaj strategii enumów tylko dla tego indeksu.

---

# CZĘŚĆ B — JEDNA CURRENT BHP DECISION NA SDS

## 7. Reguła

Dla jednego `sds_id` może istnieć maksymalnie jedna decyzja BHP ze statusem rekordu:

```text
CURRENT
```

Dozwolone:

```text
SDS A
├── DECISION-1 SUPERSEDED
├── DECISION-2 SUPERSEDED
└── DECISION-3 CURRENT
```

Niedozwolone:

```text
SDS A
├── DECISION-1 CURRENT
└── DECISION-2 CURRENT
```

`decision_status` (`APPROVED` / `REJECTED`) opisuje treść decyzji.

`record_status` (`CURRENT` / `SUPERSEDED`) opisuje jej aktualność.

Nie mieszaj tych dwóch znaczeń.

---

## 8. Preferowana implementacja

Preferowany partial unique index:

```text
UNIQUE(sds_id)
WHERE record_status = 'CURRENT'
```

Preferowana stabilna nazwa:

```text
uq_bhp_decisions_one_current_per_sds
```

Wiele `SUPERSEDED` dla jednego SDS musi pozostać dozwolone.

---

# CZĘŚĆ C — ZGODNOŚĆ PRODUCT W BHP DECISION I SDS

## 9. Reguła

Rekord:

```text
BhpDecision(product_id = X, sds_id = Y)
```

jest poprawny tylko wtedy, gdy:

```text
SdsDocument(sds_id = Y).product_id = X
```

Niedozwolony stan:

```text
PRODUCT A → SDS-A

PRODUCT B → BHP_DECISION:
             product_id = B
             sds_id = SDS-A
```

BHP decision dotyczy pary `PRODUCT + SDS`; nie wolno wskazać produktu innego niż właściciel SDS.

---

## 10. Preferowana strategia bez triggera

Preferuj rozwiązanie deklaratywne oparte na kluczach.

Jeżeli PostgreSQL wymaga, aby para:

```text
(sds_id, product_id)
```

w `sds_documents` była jawnie kandydatem do referencji, dopuszczalne jest dodanie odpowiedniego `UNIQUE` na tej parze oraz złożonego FK z `bhp_decisions`.

Docelowa semantyka:

```text
bhp_decisions(sds_id, product_id)
    REFERENCES
sds_documents(sds_id, product_id)
```

Jest dopuszczalne pozostawienie istniejących prostych FK, jeśli nie powodują sprzeczności i złożony FK stanowi dodatkowe zabezpieczenie.

Preferuj rozwiązanie bez triggera.

Jeżeli pojawi się potrzeba triggera, STOP i zgłoś ją Cerberusowi przed implementacją.

---

# CZĘŚĆ D — MODELE ORM I MIGRACJA

## 11. Aktualizacja ORM

Zaktualizuj modele ORM wyłącznie w zakresie niezbędnym do deklaratywnego opisania zatwierdzonych constraints.

Nie zmieniaj:

- modeli domenowych,
- pól biznesowych,
- enumów,
- nullable niezwiązanych z constraintami,
- relacji poza niezbędną korektą techniczną.

Po zmianie `Base.metadata` ma reprezentować docelowy stan po TASK-006.

---

## 12. Druga migracja Alembic

TASK-006 ma utworzyć dokładnie jedną nową rewizję następującą po:

```text
fdaac4f8756e
```

Preferowana nazwa:

```text
add_core_integrity_constraints
```

Przykład:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "add core integrity constraints"
```

Przed `upgrade` obowiązkowo przeczytaj wygenerowany plik migracji.

Nie akceptuj bez review żadnych propozycji usunięcia 18 istniejących enumowych CHECK constraints.

---

## 13. Szczególna ochrona enumowych CHECK

Z TASK-005 wiadomo, że surowy `alembic check` / autogenerate może raportować fałszywy drift dla:

```text
Enum(native_enum=False, create_constraint=True)
```

W TASK-006:

- nie usuwaj tych CHECK-ów,
- nie zmieniaj ich semantyki,
- nie generuj migracji „naprawiającej” ten fałszywy drift,
- odfiltruj/usuń z wygenerowanej rewizji wyłącznie fałszywe operacje dotyczące znanych enumowych CHECK, jeżeli autogenerate je zaproponuje,
- każdą ręczną korektę migracji dokładnie opisz w raporcie.

Po migracji ponownie potwierdź 18/18 nazw i wartości enumowych CHECK.

---

# CZĘŚĆ E — TESTY INTEGRACYJNE

## 14. Środowisko testów

Testy constraints mają rzeczywiście wykorzystywać PostgreSQL.

Nie używaj SQLite do testowania semantyki PostgreSQL partial indexes, ARRAY ani constraintów.

Testy nie mogą pozostawiać danych biznesowych po zakończeniu.

Preferuj transakcję z rollbackiem albo jawne kontrolowane czyszczenie danych testowych.

Nie usuwaj schematu ani nie wykonuj downgrade w zwykłym przebiegu testów constraints.

---

## 15. Test — jeden CURRENT SDS

Dodaj test potwierdzający:

### przypadek poprawny

```text
1 PRODUCT
+ 1 CURRENT SDS
+ N ARCHIVED SDS
= zapis dozwolony
```

### przypadek błędny

Próba zapisania drugiego `CURRENT` SDS dla tego samego produktu:

```text
= PostgreSQL odrzuca zapis
```

Test powinien oczekiwać właściwego wyjątku integralności SQLAlchemy/psycopg, a nie własnego wyjątku UI.

---

## 16. Test — jeden CURRENT BHP decision

Potwierdź:

### przypadek poprawny

```text
1 SDS
+ 1 CURRENT decision
+ N SUPERSEDED decisions
= zapis dozwolony
```

### przypadek błędny

Druga `CURRENT` decision dla tego samego SDS:

```text
= PostgreSQL odrzuca zapis
```

---

## 17. Test — zgodność PRODUCT + SDS

Utwórz:

```text
PRODUCT A → SDS-A
PRODUCT B
```

Następnie spróbuj zapisać:

```text
BHP_DECISION
product_id = PRODUCT B
sds_id = SDS-A
```

Oczekiwany wynik:

```text
PostgreSQL odrzuca zapis
```

Następnie potwierdź, że:

```text
product_id = PRODUCT A
sds_id = SDS-A
```

jest dozwolone.

---

## 18. Testy pozytywne historii

Potwierdź również, że nowe constraints nie blokują poprawnej historii:

- wiele `ARCHIVED` SDS dla jednego produktu — dozwolone,
- wiele `SUPERSEDED` decyzji dla jednego SDS — dozwolone,
- różne produkty mogą mieć własny `CURRENT` SDS,
- różne SDS mogą mieć własną `CURRENT` BHP decision.

---

# CZĘŚĆ F — GRANICE TASKU

## 19. Czego TASK-006 NIE robi

Nie implementuj:

- workflow `CURRENT → ARCHIVED`,
- workflow `CURRENT → SUPERSEDED`,
- automatycznej archiwizacji poprzedniego SDS,
- automatycznego supersede poprzedniej decyzji,
- triggerów,
- stored procedures,
- repository pattern,
- CRUD,
- use cases,
- UI,
- importu danych,
- parsera PDF,
- ekstrakcji SDS,
- REACH,
- użytkowników i uprawnień,
- soft delete,
- audytu zmian,
- nowych statusów,
- konwersji jednostek.

Ważne rozróżnienie:

```text
TASK-006:
baza BLOKUJE stan niepoprawny

przyszły workflow:
aplikacja POPRAWNIE PRZECHODZI
ze starego stanu do nowego
```

---

## 20. Nie rozszerzaj constraints bez potrzeby

Nie dodawaj nowych:

- UNIQUE,
- CHECK,
- FK,
- NOT NULL,
- indeksów,

tylko dlatego, że „wydają się rozsądne”.

TASK-006 dotyczy zatwierdzonych krytycznych reguł Core.

Jeżeli podczas implementacji zauważysz potencjalną dodatkową regułę integralności, zapisz ją w sekcji „Pytania / kandydaci do decyzji”, ale jej nie implementuj.

---

# CZĘŚĆ G — MIGRACJA I WALIDACJA

## 21. Review drugiej migracji przed upgrade

Przed wykonaniem `upgrade head` potwierdź, że migracja:

- nie tworzy nowych tabel,
- nie usuwa tabel,
- nie dodaje pól biznesowych,
- nie zmienia enumów,
- nie usuwa istniejących enumowych CHECK,
- dodaje wyłącznie constraints/indexes niezbędne dla TASK-006.

Jeżeli nie — STOP.

---

## 22. Upgrade

Po review wykonaj:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Oczekiwany stan:

```text
Alembic revisions: 2
Application tables: 9
Current: new TASK-006 revision (head)
```

---

## 23. Downgrade / re-upgrade

Ponieważ baza nadal nie zawiera danych produkcyjnych, przetestuj odwracalność tylko nowej rewizji:

```text
TASK-006 head
   ↓
downgrade o 1 rewizję
   ↓
stan = fdaac4f8756e
   ↓
re-upgrade head
```

Po downgrade:

- 9 tabel ma nadal istnieć,
- constraints TASK-006 mają być usunięte,
- schema TASK-005 ma pozostać.

Po re-upgrade constraints mają wrócić.

Końcowy stan bazy: `head`.

---

## 24. Drift

Po finalnym upgrade wykonaj kontrolę ORM ↔ PostgreSQL.

Uwzględnij znane ograniczenie enumowych type-bound CHECK z TASK-005.

W raporcie rozdziel:

```text
rzeczywisty drift
```

od:

```text
znany fałszywy drift enumowych CHECK
```

Nie uznawaj automatycznie surowego wyniku `alembic check` za dowód błędu.

---

## 25. Pełne testy regresji

Uruchom:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Wszystkie dotychczasowe 40 testów oraz nowe testy integrity muszą przejść.

Jeżeli testy integracyjne wymagają aktywnego lokalnego PostgreSQL, raport ma to jawnie wskazać.

---

# CZĘŚĆ H — KONTROLE KOŃCOWE

## 26. Kontrola architektury

Potwierdź:

- `app/domain` nie został zmieniony w celu obsługi SQL constraints,
- domena nadal nie importuje SQLAlchemy,
- constraints są w warstwie persistence/migracji,
- nie dodano logiki workflow,
- nie dodano UI,
- nie dodano bibliotek.

---

## 27. Kontrola bazy

Po zakończeniu potwierdź:

- dokładnie 9 tabel aplikacyjnych,
- dokładnie 2 rewizje Alembic,
- baza na `head`,
- constraints TASK-006 obecne,
- 18 enumowych CHECK nadal obecne i poprawne,
- brak danych testowych pozostawionych w tabelach.

---

## 28. Kontrola Git / bezpieczeństwa

Sprawdź:

```powershell
git status --short
git diff --check
git diff --cached --check
```

Nie wykonuj commita, jeżeli nie został jawnie zlecony.

Potwierdź:

- `.env` ignorowany,
- `.env` nieśledzony,
- brak sekretów,
- brak dumpów/backupów,
- brak plików SDS/BHP w Git.

---

# CZĘŚĆ I — STOP

## 29. Zasada STOP

Zatrzymaj się i raportuj `PARTIAL` albo `BLOCKED`, jeżeli:

- partial unique index nie może jednoznacznie wymusić zatwierdzonej reguły,
- zgodność PRODUCT + SDS wymaga triggera,
- autogenerate proponuje nieoczekiwane zmiany Core,
- trzeba zmienić domenę,
- trzeba zmienić wartości enumów,
- potrzebna jest nowa biblioteka,
- poprawne rozwiązanie wymaga nowej decyzji ADR/BDR/TDR,
- test ujawnia sprzeczność w zatwierdzonym modelu,
- zakres zaczyna wchodzić w TASK-007.

Nie obchodź constraintu logiką aplikacyjną tylko po to, aby uzyskać status DONE.

---

# CZĘŚĆ J — KRYTERIA AKCEPTACJI

## 30. TASK-006 = DONE, jeżeli

1. baza wymusza maksymalnie jeden `CURRENT` SDS na produkt,
2. baza wymusza maksymalnie jedną `CURRENT` BHP decision na SDS,
3. baza wymusza zgodność `BhpDecision.product_id` z produktem wskazanego SDS,
4. poprawna historia ARCHIVED/SUPERSEDED pozostaje możliwa,
5. ORM reprezentuje constraints,
6. istnieje dokładnie jedna nowa migracja TASK-006,
7. migracja została zreviewowana przed upgrade,
8. nie usunięto 18 enumowych CHECK,
9. upgrade działa,
10. downgrade jednej rewizji działa,
11. re-upgrade działa,
12. końcowa baza jest na head,
13. nadal istnieje dokładnie 9 tabel aplikacyjnych,
14. nie pozostawiono danych testowych,
15. brak rzeczywistego driftu ORM ↔ PostgreSQL,
16. wszystkie testy przechodzą,
17. nie dodano nowych bibliotek,
18. nie rozpoczęto TASK-007.

---

## 31. Wymagany raport

Utwórz:

```text
docs/task_reports/TASK-006_REPORT.md
```

Raport musi zawierać:

### 1. Status
`DONE`, `PARTIAL` albo `BLOCKED`.

### 2. Zaimplementowane reguły
Opis trzech constraints.

### 3. Strategia techniczna
- partial unique indexes,
- strategia zgodności PRODUCT + SDS,
- uzasadnienie braku triggera.

### 4. Zmiany ORM
Pełna lista.

### 5. Migracja
- revision id,
- nazwa,
- `down_revision`,
- operacje upgrade/downgrade.

### 6. Review migracji przed upgrade
Potwierdzenie braku zmian poza zakresem.

### 7. Enum CHECK safety
Potwierdzenie zachowania 18/18 constraintów.

### 8. Testy integrity
Dla każdego scenariusza:
- setup,
- oczekiwany wynik,
- rzeczywisty wynik.

### 9. Testy regresji
Polecenie i wynik całego `pytest`.

### 10. Upgrade / downgrade / re-upgrade
Rzeczywiste wyniki.

### 11. PostgreSQL final state
- liczba tabel,
- current revision,
- obecność constraints,
- brak danych testowych.

### 12. Drift ORM ↔ DB
Rozdziel rzeczywisty drift od znanego false positive enum CHECK.

### 13. Architektura
Potwierdzenie granic.

### 14. Git / bezpieczeństwo

### 15. Odstępstwa

### 16. Problemy / ryzyka

### 17. Kandydaci do przyszłych decyzji
Tylko obserwacje — bez implementacji.

### 18. Następny krok

```text
OCZEKUJĘ NA JAWNE POLECENIE. NIE ROZPOCZYNAM TASK-007.
```

---

## 32. Zakończenie

Po TASK-006:

- pozostaw bazę na `head`,
- pozostaw wszystkie trzy constraints aktywne,
- nie implementuj workflow,
- nie rozpoczynaj TASK-007,
- zapisz raport,
- przedstaw krótkie podsumowanie użytkownikowi,
- oczekuj na Cerberus Review.
