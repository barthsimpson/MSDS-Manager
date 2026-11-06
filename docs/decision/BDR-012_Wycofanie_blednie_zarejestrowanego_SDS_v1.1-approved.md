# BDR-012 — Wycofanie błędnie zarejestrowanego SDS

**Projekt:** MSDS Manager  
**Id dokumentu:** BDR-012  
**Wersja:** 1.1-approved  
**Status:** Approved  
**Data:** 2026-11-02  
**Właściciel decyzji:** Architekt Operacyjny  
**Opiekun spójności:** Cerberus — Agent Architekt  
**Dokument bazowy:** BDR-012 v1.0-approved  

---

## 1. Cel rewizji 1.1

Rewizja 1.1 nie zmienia zatwierdzonej w v1.0 semantyki `INVALIDATED`.

Celem rewizji jest doprecyzowanie wymagań funkcjonalnych i użytkowych dla operacji dostępnej z GUI:

```text
Wycofaj błędnie zarejestrowany SDS
```

Operacja ma umożliwić operatorowi bezpieczne wycofanie błędnego SDS bez fizycznego usuwania rekordu ani PDF oraz z zachowaniem pełnej audytowalności.

---

## 2. Zasada nadrzędna

UI ma prezentować tę funkcję jako kontrolowaną korektę, a nie jako zwykłe kasowanie.

Nazwa akcji:

```text
Wycofaj błędnie zarejestrowany SDS
```

Nie stosować jako głównej nazwy:

```text
Usuń SDS
Delete SDS
Kasuj SDS
```

Użytkowy sens operacji może odpowiadać usunięciu błędnego dokumentu z bieżącego obiegu, lecz technicznie i biznesowo jest to:

```text
zmiana statusu SDS → INVALIDATED
+ zachowanie rekordu i PDF
+ audyt przyczyny
```

---

## 3. Miejsce akcji w GUI

Akcja powinna być dostępna w szczegółach produktu, w obszarze dotyczącym konkretnego SDS.

Preferowany UX:

```text
Produkt
→ sekcja SDS / historia SDS
→ działania dodatkowe przy wybranym SDS
→ Wycofaj błędnie zarejestrowany SDS
```

Akcja nie powinna być eksponowana jako podstawowy przycisk głównego workflow.

Powinna należeć do grupy działań korekcyjnych / dodatkowych.

---

## 4. Dostępność przycisku

Przycisk jest dostępny tylko dla istniejącego SDS o statusie:

```text
CURRENT
ARCHIVED
```

Dla SDS o statusie:

```text
INVALIDATED
```

akcja nie jest dostępna.

System nie udostępnia w standardowym workflow prostego:

```text
INVALIDATED → CURRENT
```

---

## 5. Uruchomienie operacji

Kliknięcie akcji nie wykonuje zapisu natychmiast.

Najpierw otwierany jest ekran / panel / modal potwierdzenia.

Przed wykonaniem operacji użytkownik musi zobaczyć co najmniej:

- nazwę produktu,
- producenta,
- nazwę pliku SDS,
- datę wydania / rewizji SDS, jeżeli istnieje,
- numer rewizji, jeżeli istnieje,
- aktualny status SDS,
- informację, czy SDS jest obecnie `CURRENT`,
- ostrzeżenie, że operacja nie usuwa fizycznie dokumentu ani historii,
- przewidywany skutek operacji.

Techniczny `sds_id` może być pokazany pomocniczo, ale nie jest podstawowym elementem decyzji użytkownika.

---

## 6. Powód wycofania

Wycofanie wymaga obowiązkowego pola:

```text
Powód wycofania
```

Pole:

- nie może być puste,
- nie może składać się wyłącznie ze spacji,
- powinno umożliwiać krótki opis błędu operatora lub źródła.

Przykłady:

```text
Dokument testowy.
Przypisano niewłaściwy PDF.
SDS przypisany do niewłaściwego produktu.
Błędnie zatwierdzono niewłaściwą wersję SDS.
```

Nie wymaga się na tym etapie słownika reason codes.

---

## 7. Potwierdzenie operacji

Przed finalnym zapisem użytkownik musi jawnie potwierdzić, że rozumie skutek operacji.

Minimalne potwierdzenie:

```text
Potwierdzam wycofanie tego SDS jako błędnie zarejestrowanego.
```

Dopiero po zaznaczeniu potwierdzenia aktywowany jest przycisk końcowy:

```text
Wycofaj SDS
```

Przycisk końcowy powinien wizualnie wskazywać operację korekcyjną / destrukcyjną dla bieżącego stanu, ale nie może sugerować fizycznego DELETE pliku.

---

## 8. Wycofanie SDS `ARCHIVED`

Jeżeli wycofywany SDS ma status:

```text
ARCHIVED
```

UI pokazuje prosty scenariusz:

```text
ARCHIVED → INVALIDATED
```

Bez wyboru SDS zastępczego.

Skutek prezentowany użytkownikowi:

- bieżący `CURRENT` SDS produktu pozostaje bez zmian,
- status produktu nie zmienia się automatycznie,
- PDF i historia pozostają zachowane,
- SDS zostaje oznaczony jako błędnie zarejestrowany.

---

## 9. Wycofanie SDS `CURRENT`

Jeżeli wycofywany SDS ma status:

```text
CURRENT
```

UI musi wymagać jawnego wyboru dalszego stanu produktu.

Dostępne są dwa warianty.

### 9.1. Wariant A — przywrócenie wcześniejszego poprawnego SDS

Użytkownik wybiera:

```text
Przywróć wcześniejszy SDS jako CURRENT
```

System prezentuje listę wyłącznie SDS tego samego produktu o statusie:

```text
ARCHIVED
```

Lista nie posiada domyślnie wybranego dokumentu.

Dla każdej pozycji należy pokazać co najmniej:

- nazwę pliku,
- datę wydania / rewizji,
- numer rewizji,
- status.

Po wyborze UI pokazuje planowaną zmianę:

```text
wycofywany CURRENT → INVALIDATED
wybrany ARCHIVED   → CURRENT
PRODUCT             → PENDING_APPROVAL
```

### 9.2. Wariant B — brak SDS do przywrócenia

Użytkownik wybiera:

```text
Nie przywracaj wcześniejszego SDS
```

UI pokazuje skutek:

```text
wycofywany CURRENT → INVALIDATED
brak CURRENT SDS
PRODUCT → PENDING_APPROVAL
```

System nie tworzy pustego SDS ani dokumentu zastępczego.

---

## 10. Zakaz automatycznego wyboru SDS zastępczego

System może uporządkować listę kandydatów do przywrócenia, ale nie może samodzielnie wybrać jednego z nich.

Zakazane jest automatyczne zatwierdzenie kandydata na podstawie:

- najnowszej daty,
- najwyższego numeru rewizji,
- kolejności rejestracji,
- nazwy pliku,
- podobieństwa nazw,
- pozycji na liście.

Domyślny stan:

```text
BRAK WYBORU
```

---

## 11. Wpływ na decyzję BHP — komunikat w UI

Jeżeli wycofywany jest `CURRENT` SDS, UI musi jawnie poinformować użytkownika:

```text
Wycofanie bieżącego SDS unieważnia jego rolę jako podstawy bieżącej decyzji BHP.
Produkt przejdzie do PENDING_APPROVAL.
Dla nowego / przywróconego CURRENT SDS będzie wymagana nowa decyzja BHP.
```

UI nie może sugerować, że wcześniejsza decyzja BHP zostanie automatycznie przywrócona.

Szczegół technicznego statusu historycznej `BHP_DECISION` pozostaje do rozstrzygnięcia w TDR.

---

## 12. Wpływ na dane Safety / Components

UI nie oferuje kasowania:

```text
SAFETY_PROFILE
SDS_COMPONENT
```

Jeżeli SDS przechodzi do `INVALIDATED`, jego dane bezpieczeństwa pozostają historycznie związane z tym `sds_id`.

Nie są prezentowane jako bieżący profil produktu.

---

## 13. Finalne podsumowanie przed zapisem

Bezpośrednio przed zatwierdzeniem użytkownik powinien zobaczyć krótkie podsumowanie planowanej operacji.

Przykład dla `CURRENT`:

```text
SDS „test delete”
CURRENT → INVALIDATED

Przywracany SDS:
XBRAKE CLEANER / 2025-01-15 / rew. 3.0
ARCHIVED → CURRENT

Produkt:
PENDING_APPROVAL

PDF i historia:
pozostają zachowane
```

Przykład dla `ARCHIVED`:

```text
SDS „błędny dokument”
ARCHIVED → INVALIDATED

CURRENT SDS:
bez zmian

PDF i historia:
pozostają zachowane
```

---

## 14. Zachowanie po poprawnym wykonaniu

Po skutecznym wykonaniu operacji UI powinno:

1. pokazać jednoznaczny komunikat sukcesu,
2. odświeżyć dane produktu,
3. pokazać nowy status `INVALIDATED` przy wycofanym SDS,
4. pokazać właściwy `CURRENT` SDS albo jawny brak CURRENT,
5. pokazać `PENDING_APPROVAL`, jeżeli wycofano wcześniejszy CURRENT,
6. zachować możliwość otwarcia historycznego PDF,
7. nie ukrywać wycofanego SDS z historii.

Preferowany komunikat:

```text
SDS został wycofany jako błędnie zarejestrowany. Dokument i historia zostały zachowane.
```

---

## 15. Prezentacja `INVALIDATED`

SDS ze statusem `INVALIDATED` pozostaje widoczny w historii SDS produktu.

Powinien być jednoznacznie oznaczony jako:

```text
Wycofany / błędna rejestracja
```

Nie powinien być prezentowany na równi z poprawnym `ARCHIVED`.

UI powinno umożliwić odczyt co najmniej:

- statusu `INVALIDATED`,
- daty wycofania,
- powodu wycofania.

Jeżeli techniczny model audytu będzie przechowywał dodatkowe dane, mogą być pokazane w szczegółach.

---

## 16. Ochrona przed zmianą stanu podczas operacji

Przed finalnym zapisem Application musi ponownie zweryfikować stan SDS i produktu.

Jeżeli od otwarcia formularza:

- SDS zmienił status,
- zmienił się `CURRENT`,
- wybrany kandydat nie jest już `ARCHIVED`,
- produkt lub SDS nie istnieje,

operacja nie może zostać wykonana na starych danych.

UI pokazuje komunikat typu:

```text
Stan danych zmienił się. Odśwież widok i ponów operację.
```

Nie wolno automatycznie „dopasować” decyzji użytkownika do nowego stanu.

---

## 17. Atomiczność operacji

Z punktu widzenia użytkownika cała operacja jest jedną akcją.

Dla wariantu przywrócenia wcześniejszego SDS wszystkie wymagane zmiany muszą zakończyć się razem albo żadna z nich nie może pozostać częściowo wykonana.

W szczególności nie może wystąpić trwały stan pośredni typu:

```text
stary CURRENT → INVALIDATED
ale wskazany ARCHIVED nie został CURRENT
```

albo:

```text
SDS zmieniony
ale PRODUCT nie przeszedł do PENDING_APPROVAL
```

Szczegół techniczny transakcji rozstrzyga TDR.

---

## 18. Zakaz fizycznego usuwania przez GUI

GUI nie udostępnia w tej funkcji operacji:

```text
usuń rekord SDS
usuń PDF
usuń historię
usuń decyzję BHP
usuń Safety / Components
```

`INVALIDATED` jest jedynym standardowym sposobem wycofania błędnie zarejestrowanego SDS.

---

## 19. Kryteria akceptacji funkcjonalnej UI

Funkcja jest zgodna z BDR-012, jeżeli co najmniej:

1. dla `CURRENT` i `ARCHIVED` dostępna jest akcja `Wycofaj błędnie zarejestrowany SDS`,
2. dla `INVALIDATED` akcja nie jest dostępna,
3. kliknięcie nie powoduje natychmiastowego zapisu,
4. użytkownik widzi identyfikację dokumentu i skutek operacji,
5. powód jest obowiązkowy,
6. wymagane jest jawne potwierdzenie,
7. `ARCHIVED → INVALIDATED` nie zmienia bieżącego CURRENT,
8. `CURRENT → INVALIDATED` wymaga jawnej decyzji: przywróć konkretny ARCHIVED albo pozostaw bez CURRENT,
9. lista kandydatów ARCHIVED nie posiada automatycznego wyboru,
10. wycofanie CURRENT prowadzi do `PRODUCT = PENDING_APPROVAL`,
11. wcześniejsza decyzja BHP nie jest automatycznie reaktywowana,
12. PDF, Safety, Components i historia nie są fizycznie usuwane,
13. po sukcesie `INVALIDATED` pozostaje widoczny w historii wraz z powodem,
14. zmiana stanu danych przed finalnym zapisem powoduje kontrolowany STOP / refresh,
15. operacja jest atomowa z perspektywy użytkownika,
16. fizyczny DELETE SDS/PDF nie jest dostępny w standardowym GUI.

---

## 20. Poza zakresem rewizji 1.1

Rewizja 1.1 nadal nie rozstrzyga:

- schema PostgreSQL,
- technicznego modelu tabeli / historii wycofania,
- dokładnego mechanizmu zmiany `BHP_DECISION.record_status`,
- migracji Alembic,
- RBAC / ról użytkowników,
- cofnięcia błędnego `INVALIDATED`,
- housekeeping starych plików,
- deduplikacji SDS,
- Stage 2 Safety extraction.

Te elementy należą do TDR lub osobnych decyzji.

---

## 21. Wpływ na Core

Bez zmian względem BDR-012 v1.0-approved:

```text
SDS.document_status:
CURRENT | ARCHIVED | INVALIDATED
```

Rewizja 1.1 doprecyzowuje jedynie wymagania procesu użytkownika dla zatwierdzonego lifecycle.

---

## 22. Następne artefakty

Po zatwierdzeniu BDR-012 v1.1 należy przygotować:

```text
1. rewizję CORE-001 obejmującą INVALIDATED
2. TDR — persistence + audit + BHP + transakcja + UI/Application contract
3. zamknięty Task implementacyjny
4. fizyczny test przypadku XBRAKE CLEANER / „test delete”
```

---

## 23. Authorization boundary

BDR-012 v1.1 po zatwierdzeniu będzie obowiązującym źródłem wymagań biznesowych i funkcjonalnych dla GUI wycofania SDS.

Sam dokument:

```text
nie autoryzuje implementacji
nie autoryzuje migracji
nie autoryzuje zmian danych operatora
```

Implementacja nadal wymaga zatwierdzonego Core, TDR, Tasku i jawnej autoryzacji Architekta Operacyjnego.

---

## 24. Status

```text
BDR-012
VERSION: 1.1-approved
STATUS: APPROVED
```

---

## 25. Historia zmian

| Wersja | Data | Status | Zmiana |
|---|---|---|---|
| 0.1-draft | 2026-10-26 | Draft | Zdefiniowano `INVALIDATED`, kontrolowane wycofanie błędnie zarejestrowanego SDS, brak fizycznego DELETE, jawne przywrócenie wcześniejszego SDS i wpływ na BHP / PRODUCT |
| 1.0-approved | 2026-10-26 | Approved | Architekt Operacyjny zatwierdził BDR-012 bez zmian merytorycznych |
| 1.1-approved | 2026-11-02 | Approved | Architekt Operacyjny zatwierdził rewizję 1.1 z wymaganiami GUI bez zmian merytorycznych |
