# BDR-004 — Decyzja BHP, jej zakres i historia

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-004  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-08-25  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Powiązane IR:** IR-001-16, IR-001-19, IR-001-21, IR-001-22, IR-001-23  

---

## 1. Cel decyzji

Celem BDR-004 jest jednoznaczne zdefiniowanie modelu decyzji Specjalisty BHP w MSDS Manager, jej zakresu, powiązania z produktem i konkretnym dokumentem SDS, sposobu przechowywania uwag i dowodu oraz zasad zachowania historii i korekt.

Dokument rozwija model `BHP_DECISION` określony w CORE-001 oraz regułę BDR-003, zgodnie z którą nowy zatwierdzony SDS wymaga nowej decyzji BHP.

---

## 2. Zasada nadrzędna

Decyzja BHP jest osobnym obiektem domenowym.

Decyzja dotyczy zawsze:

- konkretnego `PRODUCT`,
- konkretnego zatwierdzonego `SDS`.

Model:

```text
PRODUCT
   │
   └── SDS
        │
        └── BHP_DECISION
               │
               └── DECISION_EVIDENCE
```

Decyzja BHP nie jest wydawana osobno dla każdego miejsca stosowania.

Miejsca stosowania i ilości pozostają osobnym elementem modelu produktu zgodnie z BDR-002.

---

## 3. Powiązanie decyzji z SDS

Każda decyzja BHP musi wskazywać konkretny `sds_id`.

Nie wystarcza samo powiązanie z `product_id`.

Dzięki temu system może jednoznacznie wykazać:

> jaka wersja karty SDS była podstawą konkretnej decyzji BHP.

Reguła:

```text
BHP_DECISION
├── product_id
└── sds_id
```

---

## 4. Nowy SDS a obowiązywanie decyzji

Zatwierdzenie nowego SDS jako `CURRENT` powoduje:

```text
poprzedni SDS CURRENT → ARCHIVED
nowy SDS              → CURRENT
PRODUCT                → PENDING_APPROVAL
```

Poprzednia decyzja BHP pozostaje w historii przy poprzednim `sds_id`.

Nie jest automatycznie przenoszona na nową kartę.

Nowy `CURRENT` SDS wymaga nowej decyzji BHP.

---

## 5. Wynik decyzji BHP

W MVP decyzja BHP ma dwa możliwe wyniki:

- `APPROVED`
- `REJECTED`

Nie tworzy się statusu `PENDING` dla `BHP_DECISION`.

Brak decyzji BHP dla aktualnego SDS oznacza brak rekordu obowiązującej decyzji, a stan oczekiwania jest reprezentowany przez:

```text
PRODUCT.usage_status = PENDING_APPROVAL
```

---

## 6. Powiązanie decyzji ze statusem produktu

Podstawowa logika:

```text
CURRENT SDS
    │
    ├── brak aktualnej BHP_DECISION
    │       ↓
    │   PRODUCT = PENDING_APPROVAL
    │
    ├── BHP_DECISION = APPROVED
    │       ↓
    │   PRODUCT = ACTIVE
    │
    └── BHP_DECISION = REJECTED
            ↓
        PRODUCT = REJECTED
```

Status `INACTIVE` pozostaje statusem biznesowym oznaczającym wyłączenie produktu ze stosowania.

Nie jest wynikiem negatywnej decyzji BHP.

---

## 7. Dopuszczenie warunkowe

W MVP nie tworzy się osobnego statusu:

`APPROVED_WITH_CONDITIONS`

Jeżeli Specjalista BHP dopuszcza produkt pod określonymi warunkami, decyzja ma status:

`APPROVED`

a warunki są zapisywane w polu:

`notes`

Przykład:

```text
decision_status = APPROVED

notes =
"Dopuszczony pod warunkiem stosowania
rękawic nitrylowych oraz wentylacji miejscowej."
```

---

## 8. Pole Uwagi

Każda decyzja może posiadać opcjonalne pole tekstowe:

`notes`

Pole może zawierać:

- cytat z maila Specjalisty BHP,
- warunki dopuszczenia,
- komentarz,
- dopisek użytkownika,
- inne informacje pomocnicze związane z decyzją.

`notes` jest zawsze powiązane z konkretnym rekordem `BHP_DECISION`.

Pole `notes` nie zastępuje dokumentu będącego dowodem decyzji.

---

## 9. Minimalny model BHP_DECISION

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
└── evidence_id
```

`notes` jest opcjonalne.

`registered_at` jest nadawane automatycznie przez aplikację.

`evidence_id` jest wymagane.

`record_status` służy do zachowania historii decyzji zgodnie z sekcją 14.

---

## 10. Data decyzji

System nie wymaga osobnego strukturalnego pola oznaczającego faktyczną datę decyzji Specjalisty BHP.

Przechowywana jest:

`registered_at`

czyli data i czas rejestracji decyzji w MSDS Manager.

Jeżeli faktyczna data decyzji występuje w mailu, PDF, skanie lub innym dowodzie, pozostaje częścią dokumentu źródłowego.

---

## 11. Osoba podejmująca decyzję

System nie wymaga w MVP osobnej kartoteki osób zatwierdzających ani pola `decided_by`.

Informacja o osobie podejmującej decyzję, jeżeli jest potrzebna, pozostaje w dokumencie dowodowym.

MSDS Manager nie próbuje automatycznie odczytywać i utrzymywać strukturalnej kartoteki Specjalistów BHP.

---

## 12. DECISION_EVIDENCE

Każda decyzja BHP musi posiadać jeden dowód źródłowy.

W MVP obowiązuje:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
```

Jedna decyzja = jeden dowód.

Dowód może mieć format:

- `.msg`
- `.pdf`
- `.jpg`
- `.jpeg`
- `.png`

Przykłady:

```text
evidence_type = EMAIL
file_format = MSG
```

```text
evidence_type = DOCUMENT
file_format = PDF
```

```text
evidence_type = PHOTO_SCAN
file_format = JPG
```

---

## 13. Znaczenie dowodu

Dowód jest dokumentem źródłowym potwierdzającym decyzję BHP.

`notes` może ułatwiać odczyt decyzji, ale:

> **rekord decyzji bez powiązanego dowodu nie jest kompletną decyzją BHP w MSDS Manager.**

System nie powinien pozwolić na zatwierdzenie `BHP_DECISION` bez `DECISION_EVIDENCE`.

---

## 14. Historia decyzji

Zatwierdzona decyzja BHP nie jest nadpisywana.

Jeżeli:

- użytkownik wprowadził decyzję błędnie,
- konieczna jest korekta,
- pojawia się nowa decyzja dla tego samego SDS,

tworzony jest nowy rekord `BHP_DECISION`.

Poprzedni rekord pozostaje w historii.

Minimalny model statusu rekordu decyzji:

- `CURRENT`
- `SUPERSEDED`

Przykład:

```text
PRODUCT + SDS-003
│
├── BHP_DECISION-001
│     decision_status = APPROVED
│     record_status   = SUPERSEDED
│     evidence        = email_01.msg
│
└── BHP_DECISION-002
      decision_status = REJECTED
      record_status   = CURRENT
      evidence        = email_02.msg
```

---

## 15. Maksymalnie jedna aktualna decyzja dla SDS

Dla konkretnego `sds_id` może istnieć wiele historycznych decyzji, ale maksymalnie jedna decyzja może posiadać:

`record_status = CURRENT`

Reguła:

```text
SDS
├── BHP_DECISION SUPERSEDED
├── BHP_DECISION SUPERSEDED
└── BHP_DECISION CURRENT
```

To aktualna decyzja steruje bieżącym `usage_status` produktu.

---

## 16. Korekta decyzji

Korekta nie polega na edycji zatwierdzonego rekordu.

Proces:

```text
istniejąca decyzja CURRENT
        ↓
użytkownik wprowadza korektę / nową decyzję
        ↓
nowy BHP_DECISION
        ↓
poprzedni record_status → SUPERSEDED
nowy record_status      → CURRENT
        ↓
aktualizacja usage_status PRODUCT
```

Operacja zmiany `CURRENT → SUPERSEDED` i ustanowienia nowej decyzji `CURRENT` powinna być spójna.

---

## 17. Brak fizycznego dowodu po rejestracji

Analogicznie do SDS, fizyczny plik dowodu może zostać później usunięty lub przeniesiony poza aplikacją.

Nie powoduje to usunięcia rekordu decyzji z historii.

System powinien zachować:

- `decision_id`,
- powiązanie z `product_id`,
- powiązanie z `sds_id`,
- wynik decyzji,
- `notes`,
- `registered_at`,
- metadane dowodu,
- ścieżkę do dowodu.

Dostępność fizycznego pliku może być kontrolowana osobno.

Szczegółowa implementacja statusu dostępności dowodu może zostać określona w TDR.

---

## 18. Repozytorium dowodów

Dowody decyzji BHP są przechowywane poza PostgreSQL w osobnym repozytorium:

`BHP_EVIDENCE_ROOT_PATH`

Repozytorium dowodów jest niezależne od:

`SDS_ROOT_PATH`

Model:

```text
SDS_ROOT_PATH
└── dokumenty SDS

BHP_EVIDENCE_ROOT_PATH
└── dowody decyzji BHP
```

Baza przechowuje metadane i ścieżki do dowodów.

---

## 19. Granica odpowiedzialności aplikacji

MSDS Manager:

- rejestruje wynik decyzji,
- wiąże decyzję z produktem i konkretnym SDS,
- przechowuje uwagi,
- wiąże decyzję z dowodem,
- zachowuje historię,
- steruje odpowiednim statusem produktu.

MSDS Manager nie:

- podejmuje decyzji BHP,
- zastępuje Specjalisty BHP,
- interpretuje automatycznie maila jako zatwierdzenie,
- tworzy strukturalnej kartoteki osób zatwierdzających,
- automatycznie przenosi decyzji na nową wersję SDS,
- strukturyzuje warunków dopuszczenia poza polem `notes`.

---

## 20. Reguły integralności

1. `BHP_DECISION` zawsze posiada `decision_id`.
2. Decyzja zawsze wskazuje `product_id`.
3. Decyzja zawsze wskazuje konkretny `sds_id`.
4. `sds_id` musi należeć do wskazanego `product_id`.
5. Decyzja ma wynik `APPROVED` albo `REJECTED`.
6. Brak decyzji dla aktualnego SDS oznacza `PRODUCT = PENDING_APPROVAL`.
7. `APPROVED` powoduje `PRODUCT = ACTIVE`, o ile decyzja jest aktualna dla `CURRENT` SDS.
8. `REJECTED` powoduje `PRODUCT = REJECTED`, o ile decyzja jest aktualna dla `CURRENT` SDS.
9. Każda decyzja posiada dokładnie jeden dowód w MVP.
10. `notes` jest opcjonalne i nie zastępuje dowodu.
11. Zatwierdzonej decyzji nie nadpisuje się.
12. Korekta tworzy nowy rekord decyzji.
13. Dla jednego `sds_id` może istnieć maksymalnie jedna decyzja z `record_status = CURRENT`.
14. Poprzednia decyzja po korekcie otrzymuje `SUPERSEDED`.
15. Nowy zatwierdzony SDS wymaga nowej decyzji BHP.
16. Decyzja dla archiwalnego SDS pozostaje historyczna i nie steruje statusem produktu.

---

## 21. Ograniczenia dla implementacji

Codex nie może:

- tworzyć decyzji BHP bez `PRODUCT`,
- tworzyć decyzji BHP bez `SDS`,
- tworzyć zatwierdzonej decyzji bez dowodu,
- zmieniać zatwierdzonej decyzji przez nadpisanie,
- usuwać poprzednich decyzji przy korekcie,
- przenosić decyzji na nowy SDS,
- wyprowadzać decyzji BHP z wyniku automatycznej analizy SDS,
- dodawać statusów decyzji bez BDR,
- tworzyć osobnego statusu `APPROVED_WITH_CONDITIONS` bez zmiany BDR,
- uznawać `notes` za dowód,
- wiązać decyzji wyłącznie z produktem bez `sds_id`.

---

## 22. Rozstrzygnięcie IR

### IR-001-16

**Jakie statusy decyzji BHP są potrzebne?**

Status: **Resolved**

Decyzja:

- `APPROVED`
- `REJECTED`

Brak decyzji nie jest statusem decyzji; reprezentuje go `PRODUCT = PENDING_APPROVAL`.

### IR-001-19

**Jak zapisywać warunki dopuszczenia?**

Status: **Resolved**

Decyzja:

W MVP warunki, komentarze i cytaty są przechowywane w opcjonalnym polu tekstowym `notes`.

Nie tworzy się strukturalnego modelu warunków dopuszczenia.

### IR-001-21

**Jak identyfikować osobę zatwierdzającą?**

Status: **Resolved**

Decyzja:

System nie przechowuje osobnej strukturalnej informacji o osobie zatwierdzającej. Informacja pozostaje w dokumencie dowodowym.

### IR-001-22

**Jak przechowywać historię kolejnych decyzji BHP?**

Status: **Resolved**

Decyzja:

Każda kolejna decyzja jest osobnym rekordem. Poprzednie rekordy pozostają w historii jako `SUPERSEDED`.

### IR-001-23

**Jak korygować błędnie wprowadzoną decyzję bez utraty audytowalności?**

Status: **Resolved**

Decyzja:

Zatwierdzonego rekordu nie edytuje się. Korekta tworzy nowy rekord, a poprzedni otrzymuje `record_status = SUPERSEDED`.

---

## 23. Konsekwencje decyzji

### Pozytywne

- prosty model decyzji,
- jednoznaczne powiązanie decyzji z konkretnym SDS,
- zachowanie dowodu źródłowego,
- pełna historia korekt bez nadpisywania,
- brak zbędnej kartoteki osób BHP,
- brak nadmiernej strukturyzacji warunków,
- łatwe wyznaczanie statusu produktu.

### Ograniczenia

- osoba i faktyczna data decyzji nie są osobnymi polami raportowymi,
- warunki decyzji nie są strukturalnie wyszukiwalne poza tekstem `notes`,
- szczegóły decyzji mogą wymagać otwarcia dokumentu dowodowego.

---

## 24. Powiązane dokumenty

BDR-004 jest zgodny z:

- CORE-001,
- BDR-001,
- BDR-002,
- BDR-003,
- ADR-003,
- PDP-001,
- Konstytucją projektu.

BDR-004 domyka podstawowy model decyzji BHP potrzebny przed przejściem do technicznego modelu danych.

---

## 25. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-08-25 | Approved | Zdefiniowano zakres PRODUCT+SDS, statusy APPROVED/REJECTED, notes, obowiązkowy dowód 1:1 oraz historię decyzji CURRENT/SUPERSEDED |
