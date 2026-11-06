# BDR-012 — Wycofanie błędnie zarejestrowanego SDS

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-012  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data:** 2026-10-26  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  

---

## 1. Cel decyzji

Celem BDR-012 jest zdefiniowanie kontrolowanego sposobu postępowania z dokumentem SDS, który został zarejestrowany w MSDS Manager, a następnie stwierdzono, że jego rejestracja była błędna.

Przykładowe przyczyny:

- wskazano niewłaściwy PDF,
- SDS przypisano do niewłaściwego PRODUCT,
- zarejestrowano dokument testowy,
- operator zatwierdził niewłaściwą kartę jako `CURRENT`,
- dokument nie powinien był zostać dopuszczony do rejestru SDS.

Decyzja nie dotyczy zwykłego zastąpienia starszego poprawnego SDS nowszą rewizją. Ten przypadek pozostaje obsługiwany przez istniejący lifecycle `CURRENT → ARCHIVED`.

---

## 2. Problem

Obowiązujący model SDS przewiduje dwa statusy:

```text
CURRENT
ARCHIVED
```

`ARCHIVED` oznacza poprawny historyczny SDS, który przestał być aktualnym dokumentem po zatwierdzeniu kolejnego SDS jako `CURRENT`.

Model nie rozróżnia obecnie:

```text
poprawny, ale historyczny SDS
```

od:

```text
SDS zarejestrowany błędnie i niepowinien traktowany jako prawidłowy dokument produktu
```

Nie istnieje również standardowa operacja użytkownika pozwalająca wycofać błędnie zarejestrowany SDS bez fizycznego usuwania historii.

---

## 3. Zasada nadrzędna

Błędnie zarejestrowany SDS:

```text
NIE JEST USUWANY
NIE JEST NADPISYWANY
NIE JEST TRAKTOWANY JAK ZWYKŁY ARCHIVED
```

Zamiast tego otrzymuje jawny stan:

```text
INVALIDATED
```

Znaczenie:

> `INVALIDATED` oznacza dokument zachowany dla audytowalności, którego rejestracja została uznana za błędną i który nie może pełnić roli obowiązującego SDS produktu.

---

## 4. Lifecycle SDS po BDR-012

Dozwolone biznesowo statusy SDS:

```text
CURRENT
ARCHIVED
INVALIDATED
```

Znaczenie:

### CURRENT

Dokument aktualnie zatwierdzony przez użytkownika jako obowiązujący SDS produktu.

### ARCHIVED

Poprawny historyczny dokument SDS, który wcześniej był `CURRENT`, ale został zastąpiony innym poprawnym SDS.

### INVALIDATED

Dokument zarejestrowany błędnie. Pozostaje w historii, lecz nie jest prawidłowym dokumentem referencyjnym produktu.

---

## 5. Dozwolone przejścia

Normalne wersjonowanie pozostaje bez zmian:

```text
CURRENT
  ↓ zatwierdzenie nowego SDS
ARCHIVED
```

Nowa operacja korekcyjna:

```text
CURRENT  → INVALIDATED
ARCHIVED → INVALIDATED
```

`INVALIDATED` nie może w standardowym workflow zostać ponownie ustawiony jako `CURRENT`.

Jeżeli samo wycofanie zostało wykonane błędnie, przypadek wymaga osobnej kontrolowanej korekty; system nie udostępnia prostego przełącznika `INVALIDATED → CURRENT`.

---

## 6. Zakaz fizycznego DELETE

Wycofanie błędnej rejestracji nie oznacza usunięcia rekordu ani PDF.

Po operacji pozostają zachowane:

```text
sds_id
product_id
original_filename
relative_path
issue_date
revision
registered_at
PDF
powiązane dane historyczne
powód wycofania
czas wycofania
```

Model pliku pozostaje:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Aplikacja nie usuwa ani nie modyfikuje zarejestrowanego PDF w ramach operacji wycofania.

---

## 7. Wymagana jawna decyzja użytkownika

Wycofanie SDS jest operacją biznesowo znaczącą i nie może następować automatycznie.

Użytkownik musi jawnie wybrać akcję:

```text
Wycofaj błędnie zarejestrowany SDS
```

Operacja wymaga co najmniej:

- wskazania konkretnego `sds_id`,
- potwierdzenia operacji,
- podania przyczyny wycofania.

Przyczyna nie może być pustym tekstem.

---

## 8. Audyt wycofania

System musi zachować informację pozwalającą ustalić co najmniej:

```text
który SDS wycofano
kiedy wykonano operację
jaki był powód
jaki był poprzedni status SDS
jaki jest wynikowy status SDS
```

BDR-012 nie rozstrzyga jeszcze technicznej reprezentacji tej informacji.

Może to zostać zrealizowane przez:

- pola w SDS,
- osobny rekord historii/status change,
- inny jawny mechanizm audytowy zgodny z architekturą projektu.

Wybór należy do TDR.

---

## 9. Wycofanie SDS `ARCHIVED`

Jeżeli błędna rejestracja dotyczy SDS już posiadającego status `ARCHIVED`:

```text
ARCHIVED → INVALIDATED
```

Nie zmienia się bieżący `CURRENT` SDS produktu.

Nie zmienia się automatycznie status użycia produktu, o ile wycofywany dokument nie steruje bieżącym stanem BHP.

---

## 10. Wycofanie SDS `CURRENT`

Wycofanie `CURRENT` jest operacją krytyczną.

Po jej zatwierdzeniu:

```text
bieżący SDS CURRENT → INVALIDATED
```

System nie może pozostawić wcześniejszego `ARCHIVED` jako `CURRENT` wyłącznie na podstawie daty, numeru rewizji lub kolejności rejestracji.

Użytkownik musi jawnie zdecydować, czy:

### Wariant A — przywrócenie wcześniejszego poprawnego SDS

Użytkownik wskazuje jeden istniejący SDS produktu ze statusem `ARCHIVED`, który ma ponownie zostać dokumentem obowiązującym.

Wynik:

```text
błędny CURRENT → INVALIDATED
wybrany ARCHIVED → CURRENT
PRODUCT → PENDING_APPROVAL
```

### Wariant B — brak prawidłowego SDS do przywrócenia

Użytkownik nie wskazuje żadnego SDS do przywrócenia.

Wynik:

```text
błędny CURRENT → INVALIDATED
brak CURRENT SDS dla PRODUCT
PRODUCT → PENDING_APPROVAL
```

Brak `CURRENT` oznacza brak aktualnej zatwierdzonej karty w systemie, a nie usunięcie produktu.

---

## 11. Relacja do decyzji BHP

Decyzja BHP pozostaje historycznie powiązana z konkretnym `sds_id`.

Jeżeli SDS zostaje `INVALIDATED`, jego decyzja BHP:

- nie może sterować bieżącym statusem produktu,
- pozostaje zachowana w historii,
- nie jest przepinana do innego SDS.

Jeżeli dla `INVALIDATED` SDS istnieje decyzja `BHP_DECISION` ze statusem rekordu `CURRENT`, operacja wycofania musi spowodować, że decyzja ta przestaje być bieżącą decyzją sterującą produktem.

Docelowo techniczny mechanizm może oznaczać zmianę jej `record_status` na `SUPERSEDED`, pod warunkiem zachowania pełnej historii i zgodności z BDR-004. Szczegół techniczny rozstrzyga TDR.

---

## 12. Przywrócony wcześniejszy SDS a BHP

Przywrócenie wcześniejszego SDS jako `CURRENT` nie reaktywuje automatycznie jego starej decyzji BHP.

Obowiązuje:

```text
ARCHIVED SDS → CURRENT
PRODUCT → PENDING_APPROVAL
```

Poprzednie decyzje BHP pozostają historyczne.

Dla ponownie ustawionego `CURRENT` SDS wymagana jest nowa jawna decyzja BHP zgodnie z zasadą, że bieżący SDS musi posiadać bieżącą decyzję odnoszącą się do konkretnego `sds_id`.

Nie występuje automatyczne:

```text
SUPERSEDED BHP_DECISION → CURRENT
```

---

## 13. Wpływ na `PRODUCT.usage_status`

Jeżeli wycofywany SDS jest `CURRENT`, po operacji:

```text
PRODUCT.usage_status = PENDING_APPROVAL
```

niezależnie od tego, czy:

- wskazano wcześniejszy SDS do przywrócenia,
- czy produkt pozostaje chwilowo bez `CURRENT` SDS.

Powodem jest utrata podstawy bieżącej decyzji BHP.

Wycofanie wyłącznie historycznego `ARCHIVED` SDS nie zmienia automatycznie `PRODUCT.usage_status`.

---

## 14. Dane Safety / Components

`SAFETY_PROFILE` i `SDS_COMPONENT` należą do konkretnego `sds_id`.

Jeżeli SDS zostaje `INVALIDATED`:

- dane nie są fizycznie usuwane,
- pozostają powiązane z tym `sds_id`,
- nie mogą być używane jako dane bieżącego profilu bezpieczeństwa produktu.

System zachowuje je wyłącznie jako historię błędnie zarejestrowanego dokumentu.

---

## 15. Prezentacja w UI

Operacja nie powinna być prezentowana jako zwykłe:

```text
Usuń SDS
```

Preferowana nazwa użytkowa:

```text
Wycofaj błędnie zarejestrowany SDS
```

Akcja powinna znajdować się w obszarze działań dodatkowych / korekcyjnych, a nie jako podstawowy przycisk pracy z SDS.

Przed zatwierdzeniem UI powinno pokazać co najmniej:

- nazwę produktu,
- identyfikację SDS / plik,
- datę i rewizję,
- aktualny status SDS,
- wpływ na `CURRENT`,
- wpływ na status produktu,
- wymagane pole przyczyny,
- wybór SDS do przywrócenia, jeśli wycofywany jest `CURRENT`.

---

## 16. Ochrona przed automatycznym wyborem poprzedniego SDS

System może przedstawić listę kwalifikujących się `ARCHIVED` SDS, ale nie może samodzielnie zatwierdzić jednego z nich jako `CURRENT` na podstawie:

- najnowszej daty,
- najwyższej rewizji,
- kolejności w bazie,
- nazwy pliku,
- podobieństwa dokumentu.

Decyzja o przywróceniu jest jawna i należy do użytkownika.

---

## 17. Przypadki zabronione

Bez osobnej zatwierdzonej decyzji system nie może:

- fizycznie usuwać zarejestrowanego SDS,
- usuwać PDF z `SDS_ROOT_PATH`,
- kasować powiązanych decyzji BHP,
- kasować `SAFETY_PROFILE` lub `SDS_COMPONENT` w celu ukrycia błędu,
- nadpisywać błędnego SDS poprawnym dokumentem,
- automatycznie wybierać wcześniejszego SDS jako `CURRENT`,
- automatycznie reaktywować historycznej decyzji BHP,
- zmieniać `product_id` dokumentu jako substytutu kontrolowanej korekty.

---

## 18. Relacja do obowiązujących decyzji

### BDR-003

BDR-012 rozszerza lifecycle SDS o jawny stan korekcyjny `INVALIDATED`.

Nie zmienia normalnej reguły:

```text
nowy poprawny SDS CURRENT
→ poprzedni poprawny SDS ARCHIVED
```

`ARCHIVED` nadal oznacza poprawną historię wersji.

### BDR-004

Decyzja BHP nadal dotyczy konkretnego `sds_id` i pozostaje historyczna.

BDR-012 doprecyzowuje, że decyzja związana z `INVALIDATED` SDS nie może sterować bieżącym statusem produktu.

### BDR-007 / TDR-006

Model dokumentu pozostaje:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Wycofanie jest zmianą statusu i audytu w bazie, a nie operacją niszczącą plik.

### TDR-004

BDR-012 jest zgodny z zasadą:

```text
nie nadpisuj historii
nie usuwaj historii
```

Techniczny mechanizm historii wycofania SDS wymaga osobnego TDR.

---

## 19. Wpływ na Core

BDR-012 zmienia Core w zakresie lifecycle SDS.

Do Core należy wprowadzić co najmniej:

```text
SDS.document_status:
CURRENT | ARCHIVED | INVALIDATED
```

oraz reguły:

```text
INVALIDATED nie może być bieżącym SDS
INVALIDATED nie steruje bieżącym BHP
wycofanie CURRENT ustawia PRODUCT = PENDING_APPROVAL
przywrócenie ARCHIVED jako CURRENT wymaga jawnego wyboru użytkownika
historyczna decyzja BHP nie jest automatycznie reaktywowana
```

Szczegółowy model persistence, constraints, migracji i historii należy do TDR.

---

## 20. Konsekwencje decyzji

### Pozytywne

- możliwość bezpiecznej korekty błędnej rejestracji SDS,
- brak fizycznego kasowania dowodów i historii,
- rozdzielenie poprawnego `ARCHIVED` od błędnego `INVALIDATED`,
- jednoznaczny stan produktu po utracie bieżącego SDS,
- brak automatycznego przywracania historycznej decyzji BHP,
- zgodność z zasadą audytowalności projektu.

### Ograniczenia

- wymagany nowy status SDS i zmiana Core,
- potrzebna będzie zmiana schema / constraintów,
- wymagany mechanizm audytu przyczyny wycofania,
- konieczne będzie doprecyzowanie technicznego zachowania `BHP_DECISION`,
- implementacja wymaga osobnego TDR i Tasku.

---

## 21. Przykład — błędny SDS testowy

Stan początkowy:

```text
PRODUCT: XBRAKE CLEANER
SDS A: ARCHIVED
SDS B: ARCHIVED
SDS TEST: CURRENT
BHP_DECISION(TEST): CURRENT / APPROVED
PRODUCT: ACTIVE
```

Operator wybiera:

```text
Wycofaj błędnie zarejestrowany SDS TEST
```

i wskazuje SDS B jako prawidłowy dokument do przywrócenia.

Wynik:

```text
SDS TEST → INVALIDATED
SDS B    → CURRENT
SDS A    → ARCHIVED

BHP_DECISION(TEST)
→ pozostaje w historii
→ nie steruje PRODUCT

PRODUCT
→ PENDING_APPROVAL
```

Nowa decyzja BHP musi zostać wykonana dla przywróconego SDS B.

---

## 22. Poza zakresem BDR-012

BDR-012 nie rozstrzyga:

- technicznego schema tabel / kolumn,
- dokładnego modelu `SDS_STATUS_CHANGE`,
- migracji Alembic,
- finalnego UI,
- uprawnień użytkowników / RBAC,
- mechanizmu cofnięcia błędnego `INVALIDATED`,
- fizycznego cleanup starych plików bez referencji,
- housekeeping `SDS_ROOT_PATH`,
- automatycznej deduplikacji SDS,
- Stage 2 ekstrakcji Safety.

---

## 23. Następne wymagane artefakty

Po zatwierdzeniu BDR-012 należy przygotować:

```text
1. rewizję CORE-001
2. TDR — techniczny model wycofania SDS i audytu
3. zamknięty Task implementacyjny
4. test przypadku XBRAKE CLEANER / „test delete”
```

Nie należy wykonywać ręcznego DELETE ani bezpośredniej korekty operator DB jako substytutu tego mechanizmu.

---

## 24. Authorization boundary

BDR-012 v1.0-approved jest obowiązującym źródłem decyzji biznesowej dla kontrolowanego wycofania błędnie zarejestrowanego SDS.

Sam BDR:

```text
nie autoryzuje implementacji
nie autoryzuje migracji
nie autoryzuje zmian danych operatora
```

Implementacja wymaga:

```text
zatwierdzonej rewizji Core
zatwierdzonego TDR
zamkniętego Tasku
jawnej autoryzacji Architekta Operacyjnego
```

---

## 25. Status decyzji

```text
BDR-012
VERSION: 1.0-approved
STATUS: APPROVED
```

Architekt Operacyjny zatwierdził decyzję 2026-10-26 bez zmian merytorycznych względem wersji 0.1-draft.

---

## 26. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-26 | Draft | Zdefiniowano `INVALIDATED`, kontrolowane wycofanie błędnie zarejestrowanego SDS, brak fizycznego DELETE, jawne przywrócenie wcześniejszego SDS i wpływ na BHP / PRODUCT |
| 1.0-approved | 2026-10-26 | Approved | Architekt Operacyjny zatwierdził BDR-012 bez zmian merytorycznych |
