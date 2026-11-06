# TASK-060 — Plan odbioru funkcji wycofania SDS

**Projekt:** MSDS Manager  
**Data:** 2026-11-03  
**Status:** ACCEPTANCE PENDING — plan kontroli, nie nowa autoryzacja wdrożenia  
**Źródła:** CORE-001 v1.8-approved, BDR-012 v1.1-approved, TDR-014 v0.2-approved, TASK-060 AUTHORIZED, TASK-060_REPORT

## 1. Ocena Cerberusa

Raport implementacji TASK-060 jest kompletny w zakresie deklarowanych testów A1–A5 i A7 oraz automatycznych AppTest dla A6. Fizyczne oględziny GUI oznaczono NOT VERIFIED. Do zamknięcia TASK-060 wymagany jest odbiór wizualny i funkcjonalny, z zachowaniem rozdzielenia środowiska testowego od bazy operatora.

## 2. Dyspozycja do przygotowania odbioru — bez zmian kodu i danych operatora

1. Uruchom aplikację na odizolowanej bazie PostgreSQL z migracją `e4c6f21a9d80` i tymczasowym SDS_ROOT_PATH. Potwierdź, że połączenie nie wskazuje bazy operatora.
2. Przygotuj wyłącznie testowe rekordy: produkt z bieżącym SDS B, archiwalnym SDS A i, jeśli pozwalają zależności modelu, starszymi decyzjami BHP. Użyj testowych PDF lub istniejących fixtures. Nie kopiuj ani nie modyfikuj operatorowych PDF.
3. Udostępnij lokalny adres uruchomionej aplikacji i instrukcję wejścia do karty produktu. Nie wykonuj automatycznego wycofania w bazie operatora.
4. Wykonaj wizualny przegląd zgodnie z UI-GUIDE-001; odbiór człowieka ma pierwszeństwo przed deklaracją AppTest.

## 3. Minimalna lista oględzin i zachowania

- [ ] Akcja `Wycofaj błędnie zarejestrowany SDS` jest dostępna tylko przy SDS CURRENT lub ARCHIVED w `Więcej akcji`.
- [ ] Formularz pokazuje właściwy produkt, producenta, PDF i status; kliknięcie akcji samo nie zapisuje zmian.
- [ ] Bez powodu i potwierdzenia zapis jest niemożliwy.
- [ ] Dla CURRENT konieczny jest wybór NO_CURRENT lub wskazanie konkretnego ARCHIVED; bez domyślnego replacement.
- [ ] Dla ARCHIVED nie wybiera się zastępnika i bieżący CURRENT pozostaje bez zmian.
- [ ] Po wycofaniu CURRENT produkt przechodzi do PENDING_APPROVAL, a stara decyzja BHP nie jest prezentowana jako bieżąca.
- [ ] INVALIDATED pozostaje w historii z datą i powodem; można otworzyć jego historyczny PDF; przy nim brak akcji powtórnego wycofania.
- [ ] Układ na typowym ekranie desktopowym (wzorzec UI-GUIDE-001, 1920x1080) nie wymaga nieuzasadnionego przewijania i nie wprowadza zakłócającej nawigacji.

## 4. Wynik odbioru

Zapisz: PASS / CORRECTION REQUIRED, środowisko i wersję migracji, datę, zakres fizycznych oględzin, ewentualne zrzuty ekranu lub krótki opis, problemy i minimalną korektę. Nie deklaruj zamknięcia bez faktycznych oględzin.

## 5. Osobne zagadnienia — nie blokują samego przygotowania GUI

- 10 nieprzechodzących starszych testów na 17 uruchomionych: nie poprawiać automatycznie; przed zamknięciem checkpointu ustalić, czy rzeczywiście są nieaktualne, czy sygnalizują regresję.
- Migracja bazy operatora nie była uruchamiana w TASK-060. Wdrożenie do bazy operatora wymaga osobnej decyzji i kopii zapasowej/warunków wycofania.
- Zastane niezacommitowane zmiany repozytorium: nie robić zbiorczego commita bez rozdzielenia zmian TASK-060 od cudzych zmian.

**STOP:** po przygotowaniu środowiska i odbiorze. Bez wdrożenia na bazie operatora i bez rozpoczęcia Paczki2/Stage2.
