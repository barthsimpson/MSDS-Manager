# BDR-008 — Kontrolowany dowód decyzji BHP i neutralny wybór evidence

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-008  
**Wersja:** 1.0-approved  
**Status:** Approved  
**Data decyzji:** 2026-10-01  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Wykonawca techniczny:** Codex OpenAI  

---

## 1. Cel decyzji

Celem BDR-008 jest uporządkowanie procesu wyboru, dodawania i późniejszego dostępu do dowodu decyzji BHP (`DECISION_EVIDENCE`) w taki sposób, aby:

- użytkownik nie mógł nieświadomie przypisać przypadkowego pliku jako dowodu decyzji,
- nowy dowód mógł zostać wskazany bezpośrednio z komputera użytkownika,
- dowód po zarejestrowaniu był chronionym dokumentem źródłowym,
- zachowana została relacja `BHP_DECISION 1:1 DECISION_EVIDENCE`,
- nie zmieniać lifecycle decyzji BHP ani modelu historii.

Decyzja realizuje obszar:

```text
UI-14 / DOC-02
```

oraz koryguje ujawniony problem UX w bieżącym ekranie `Decyzja BHP`.

---

## 2. Stan obecny i problem

Obecny formularz decyzji BHP prezentuje listę plików znajdujących się w `BHP_EVIDENCE_ROOT_PATH`.

Jeżeli w katalogu istnieją pliki, pierwszy z nich może pojawić się jako już wybrany.

Powoduje to ryzyko:

```text
przypadkowy plik z katalogu
→ pozornie wybrany jako dowód
→ użytkownik może zapisać decyzję bez świadomego wskazania właściwego evidence
```

Jest to niezgodne z biznesowym znaczeniem `DECISION_EVIDENCE`, ponieważ dowód jest integralną częścią konkretnej decyzji BHP.

---

## 3. Decyzja główna — brak domyślnego evidence

Pole:

```text
Dowód decyzji
```

musi rozpoczynać się neutralnym stanem:

```text
BRAK WYBORU
```

System nie może automatycznie wybierać pierwszego dostępnego pliku z katalogu.

Użytkownik przed zatwierdzeniem decyzji musi jawnie wskazać właściwy dowód.

Reguła:

```text
default evidence = NONE
```

Nie:

```text
default evidence = first available file
```

---

## 4. Sposoby wskazania dowodu

Użytkownik powinien mieć dwa jawne warianty:

```text
A. Wybierz istniejący dowód z repozytorium
lub
B. Dodaj nowy dowód z komputera
```

Oba prowadzą do utworzenia / przypisania jednego `DECISION_EVIDENCE` do konkretnego `BHP_DECISION`.

---

## 5. Dozwolone formaty

Zgodnie z obowiązującym modelem BHP dowodem mogą być:

```text
.msg
.pdf
.jpg
.jpeg
.png
```

Inne formaty nie są przyjmowane w tym workflow bez osobnej decyzji.

---

## 6. Kontrolowany import nowego dowodu

Nowy plik wskazany z komputera użytkownika powinien zostać skopiowany do kontrolowanego repozytorium:

```text
BHP_EVIDENCE_ROOT_PATH
```

w modelu:

```text
WRITE-ONCE IMPORT
→ READ-ONLY AFTER REGISTRATION
```

Znaczenie:

### Import
Aplikacja może utworzyć nową kopię pliku wyłącznie w ramach jawnej operacji rejestracji decyzji BHP.

### Po rejestracji
Po skutecznym zarejestrowaniu `BHP_DECISION + DECISION_EVIDENCE` aplikacja nie może w standardowym workflow:

- nadpisywać pliku,
- modyfikować zawartości,
- usuwać pliku,
- przenosić pliku,
- zmieniać istniejącej nazwy w sposób niszczący identyfikowalność.

---

## 7. Identyfikowalność

Dowód pozostaje powiązany z konkretną decyzją BHP.

Minimalnie system zachowuje:

```text
decision_id
evidence_id
evidence_type / file_format
original_filename
relative_path
registered_at
```

Dokładny techniczny model pozostaje zgodny z istniejącym schema i TDR.

Jeżeli obecny schema nie pozwala przechować wymaganej informacji bez zmiany struktury, implementacja ma się zatrzymać i zgłosić potrzebę osobnej decyzji technicznej.

---

## 8. Brak automatycznego dopasowania dowodu do produktu

System nie próbuje automatycznie ustalać, czy nazwa pliku „pasuje” do produktu.

Nie implementujemy heurystyki:

```text
filename contains product name
→ evidence is correct
```

Nie implementujemy automatycznej klasyfikacji dowodu na podstawie treści.

Odpowiedzialność za wybór właściwego dowodu pozostaje po stronie użytkownika.

---

## 9. Walidacja decyzji BHP

Zapis decyzji jest dozwolony tylko wtedy, gdy:

```text
decision_status wybrane
+
evidence jawnie wskazane
```

Obowiązuje:

```text
brak evidence
→ brak możliwości zatwierdzenia decyzji
```

Nie zmienia to istniejącej zasady, że `evidence_id` jest wymagane.

---

## 10. Relacja do istniejących decyzji

BDR-008 nie zmienia:

```text
BHP_DECISION 1:1 DECISION_EVIDENCE
APPROVED / REJECTED
CURRENT / SUPERSEDED
PRODUCT + SDS scope
```

Nie zmienia także zasad historii decyzji.

Nowa decyzja lub korekta nadal tworzy nowy rekord zgodnie z BDR-004.

---

## 11. UI-14 — dostęp do dowodu po rejestracji

W ramach tego samego obszaru funkcjonalnego użytkownik powinien mieć możliwość późniejszego dostępu do powiązanego dowodu.

Zakres docelowy:

```text
JPG / JPEG / PNG
→ podgląd inline lub bezpośrednie otwarcie

PDF
→ otwarcie / pobranie

MSG
→ pobranie / otwarcie przez system użytkownika
```

Szczegółowy UX i mechanizm techniczny określi TDR.

---

## 12. Brakujący plik

Jeżeli rekord `DECISION_EVIDENCE` istnieje, ale fizyczny plik nie jest dostępny:

```text
rekord pozostaje w historii
→ UI pokazuje stan MISSING / niedostępny
→ brak automatycznego usunięcia rekordu
```

Nie wolno zastępować brakującego evidence innym plikiem bez utworzenia nowej, jawnej relacji wynikającej z procesu korekty.

---

## 13. Granice decyzji

BDR-008 nie wprowadza:

- automatycznej analizy treści dowodu,
- automatycznego dopasowania evidence do produktu,
- OCR,
- parsera MSG,
- automatycznej decyzji BHP,
- wielu dowodów dla jednej decyzji,
- chmurowego storage,
- DMS,
- fizycznego DELETE zarejestrowanego evidence,
- zmian modelu `APPROVED / REJECTED`,
- zmian `CURRENT / SUPERSEDED`,
- zmian relacji PRODUCT / SDS / BHP_DECISION.

---

## 14. Konsekwencja techniczna

Przed implementacją wymagany jest:

```text
TDR-007 — Kontrolowany import i dostęp do DECISION_EVIDENCE
```

TDR-007 ma rozstrzygnąć co najmniej:

- neutralny stan wyboru evidence w UI,
- upload z komputera,
- wybór istniejącego pliku,
- walidację rozszerzeń,
- filesystem adapter dla `BHP_EVIDENCE_ROOT_PATH`,
- bezkolizyjny zapis,
- no-overwrite,
- path safety,
- kolejność filesystem ↔ DB,
- rollback / compensation,
- cleanup po błędzie,
- odczyt / download / preview,
- obsługę MISSING,
- testy integracyjne,
- zakres zmian w UI/Application/Infrastructure.

---

## 15. Kryterium biznesowe

Po wdrożeniu UI-14 / DOC-02 użytkownik powinien móc:

```text
wybrać PRODUCT / CURRENT SDS
→ rozpocząć decyzję BHP
→ jawnie wybrać istniejący dowód
   lub przesłać nowy z komputera
→ zatwierdzić decyzję
→ system zapisuje jedno evidence do konkretnej decyzji
→ później użytkownik może otworzyć / pobrać ten dowód
```

bez ryzyka automatycznego przypisania przypadkowego pliku.

---

## 16. Status decyzji

Architekt Operacyjny zatwierdził kierunek:

```text
NO DEFAULT EVIDENCE
+
CONTROLLED WRITE-ONCE IMPORT
+
LATER READ / DOWNLOAD ACCESS
```

Status:

```text
BDR-008
VERSION: 1.0-approved
STATUS: Approved
```

---

## 17. Authorization boundary

BDR-008 jest obowiązującą decyzją biznesową dla `UI-14 / DOC-02`.

Dokument:

```text
autoryzuje przygotowanie TDR-007
autoryzuje przygotowanie późniejszego Tasku
```

ale:

```text
nie autoryzuje implementacji
```

Implementacja wymaga osobnego Tasku i jawnego polecenia Architekta Operacyjnego.

---

## 18. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 1.0-approved | 2026-10-01 | Approved | Zatwierdzono neutralny wybór evidence, kontrolowany import do BHP_EVIDENCE_ROOT_PATH oraz późniejszy dostęp do powiązanego dowodu bez zmian lifecycle BHP |
