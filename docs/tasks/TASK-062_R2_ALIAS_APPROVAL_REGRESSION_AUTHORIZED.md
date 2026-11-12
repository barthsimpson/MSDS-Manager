# TASK-062-R2 — Zatwierdzenie reguł aliasów, regresja i kontrolowana aktywacja

**Projekt:** MSDS Manager  
**Status:** AUTHORIZED — decyzja Architekta z 2026-11-10  
**TASK MODE:** PATCH / GOV-002 LEVEL 1 (testy skupione na aliasach)  
**Cel:** usunąć formalną blokadę `ACTIVE` w TASK-062; **nie** wykonywać jeszcze całego pipeline ekstrakcji.  
**Baza:** pierwotny katalog `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, lokalny `main` po `f97c1e28996ace2087f774aeabec4ca7a9bc91cd`. Bez innych worktree, bez Dockera.

## 1. Źródła wiążące

- `TASK-062_R1_REPORT.md` — obserwacje OPEX i czterech SYLGARD, dowody, propozycje (przyjęte przez Cerberusa jako **raport**).
- `docs/tasks/SDS-ALIAS-001_Biblioteka_aliasow_i_reguly_rozszerzania_v1.0-approved.md` — obowiązujący katalog i cykl `CANDIDATE -> APPROVED -> regresja -> ACTIVE`.
- `TDR-012_Autonomiczny_modul_ekstrakcji_i_walidacji_SDS_v1.0-approved.md`, zwłaszcza §§5, 6, 10, 12 i 14.
- Lokalne zatwierdzone `SDS-SCHEMA-001`, `SDS-JSON-001`; aktualny TASK-062 i `AGENTS.md` w zakresie niezbędnym.
- **Decyzja Architekta w rozmowie, 2026-11-10:** zaakceptowany kierunek oceny aliasów z raportu R1, w tym brak zgadywania wartości nierozstrzygniętych. Zgoda dotyczy proponowanych reguł *w granicach istniejących kontraktów*; nie jest zgodą na niekontrolowaną zmianę kontraktów ani bezwarunkowe nadanie wszystkim aliasom `ACTIVE`.

## 2. Dokładna decyzja dotycząca aliasów

Przygotuj w bibliotece stan `APPROVED` dla niżej wymienionych **ściśle ograniczonych** reguł. Każdy alias staje się `ACTIVE` wyłącznie po pozytywnym teście odpowiedniej reguły i zgodności z zatwierdzonymi kontraktami.

| Alias | Zatwierdzony kierunek / ograniczenie |
|---|---|
| A-001 `Nazwa produktu` | `product.product_name` wyłącznie z 1.1; etykieta/wartość w tym samym wierszu; uszkodzony glif `�` nie podlega cichej poprawie; w razie znaczącej nieczytelności `UNREADABLE`/REVIEW. |
| A-002 `Kod produktu` | Opcjonalny `manufacturer_product_code` z etykiety w 1.1, np. `T82C13`; nie z nagłówka ani z 1.2; brak -> `NOT_FOUND`. |
| A-003 `Mfg. in U.S.A and exported by` | Nazwa podmiotu w 1.3 z następnego wiersza, bez adresu. Zweryfikuj, czy rola `MANUFACTURER_EXPORTER` jest faktycznie dozwolona w `SDS-JSON-001`; **jeśli nie, nie dodawaj jej samodzielnie i pozostaw tę regułę nieaktywną / zgłoś STOP tylko tej roli**. Nie utożsamiaj z `SUPPLIER`. |
| A-004 `EU Only Representative` | Podmiot `Valspar B.V.` z 1.3, osobna rola przedstawiciela UE, tylko jeżeli taka rola jest dozwolona w kontrakcie. |
| A-006 `Wersja` | `document_metadata.revision` po etykiecie w nagłówku lub stopce **właściwego logicznego SDS**; numery stron `1/25` etc. nie są rewizją. |
| NOWY `Nazwa wyrobu` | `product.product_name` z 1.1 SYLGARD (Part A/B odczytany z treści), nie z nazwy PDF; glif `�` bez automatycznej rekonstrukcji. |
| NOWY `Aktualizacja` | Bieżąca data SDS z etykiety w nagłówku właściwego logicznego dokumentu; **nie** `Data ostatniego wydania`; tylko jeśli semantyka `issue_date` w zatwierdzonym kontrakcie dopuszcza bieżącą aktualizację. |

**Reguły wymagające rozstrzygnięcia w kodzie/testach przed aktywacją:**

- **A-005 `Data wydania/Data aktualizacji` (OPEX):** wartość po własnej etykiecie i przed kolejną etykietą `Data poprzedniego ...`; porównaj stopki s. 1 i 25; normalizacja `25, Listopad, 2022` -> `2022-11-25` tylko przy jednoznacznej strukturze i semantyce pola. W przeciwnym razie pozostaw w `REVIEW`/nieaktywne i zgłoś brak.
- **SYLGARD blok 1.3 dostawcy:** etykieta `Dane dotyczące dostawcy karty charakterystyki` + kontekst `IDENTYFIKACJA FIRMY`, nazwa `DOW POLSKA SP.Z O.O.` jako `SUPPLIER`, **nigdy automatycznie `MANUFACTURER`**; wyłącznie gdy rola i reguła kontekstowa są zgodne z kontraktami, a test negatywny 1.4 OPEX przejdzie. W przeciwnym razie pozostaw `REVIEW`/nieaktywne.

**Nie zatwierdzono:** nowych wartości enumeracji ról, nowych pól `SDS-JSON-001`, zmiany semantyki `issue_date`, automatycznego poprawiania glifów, zgadywania kodu producenta, wykorzystania UFI jako kodu lub nazwy pliku jako dowodu. W razie rozbieżności kontraktów oznacz konkretny alias jako `BLOCKED` i nie maskuj problemu.

## 3. Wykonanie

1. Odczytowo potwierdź folder, `main`, HEAD, `git status` oraz lokalne źródła i aktualne kontrakty. Zachowaj zastane pliki nieśledzone; żadnego resetu/clean.
2. Wprowadź minimalne, jawne reguły wiązania etykiety z wartością w zatwierdzonej bibliotece aliasów i, jeśli konieczne, małym niezależnym matcherze/testowym adapterze. Bez przebudowy starego extractora.
3. Udokumentuj przejście `CANDIDATE -> APPROVED`; uruchom skupione testy na **oryginalnych** OPEX i B002-01..04 albo fixtures zawierających wiernie odczytane fragmenty, z jawnym rozróżnieniem dowodu realnego PDF od fixtures. Bez OCR.
4. Testy muszą pokryć: etykieta-wartość w tym samym/następnym wierszu, granice sekcji 1.1/1.3/1.4, różne pozycje `Wersja`, obecna vs poprzednia data, Part A/B, `�`, rozłączne role, brak kodu, nieaktywny alias, rozbieżność nazwa PDF/treść. Każde rzeczywiste `FOUND` musi mieć stronę, sekcję i cytat potwierdzający wartość; niepewność -> `AMBIGUOUS`, `UNREADABLE` lub `NOT_FOUND` zgodnie z kontraktem.
5. Dla każdego aliasu z pozytywną regresją nadaj `ACTIVE` w bibliotece i zapisz źródło zatwierdzenia oraz wynik testu. Alias niezweryfikowany pozostaje nieaktywny; nie oznaczaj wszystkich globalnie jako ACTIVE.
6. Wykonaj proporcjonalny przegląd diffu; commit obejmujący **wyłącznie** bibliotekę/reguły, adekwatne testy i krótki raport. `git add` wyłącznie jawnie wybranych plików, nie `git add .`; bez PDF operacyjnych, `.env`, `tmp/` itp. Zwykły `git push origin main` dopiero po pozytywnej kontroli lokalnego HEAD i `origin/main`; jeżeli pojawia się rozbieżność, **STOP bez force**.

## 4. Granice

Nie rozpoczynaj pełnego pipeline TASK-062 ani generowania pozornego Evidence JSON DRAFT; jest to etap przygotowania i aktywacji reguł. Bez zmian Core, PostgreSQL, migracji, Streamlit UI, Docker, worktree, nowych gałęzi, OCR, AI/LLM, automatycznego importu lub edycji PDF. Nie zmieniaj zatwierdzonych `SDS-SCHEMA-001`/`SDS-JSON-001` bez odrębnej decyzji. Nie rozwijaj sekcji 2, 3, 11.

## 5. Kryteria akceptacji

| ID | Kryterium | Dowód |
|---|---|---|
| R2-1 | Poprawne środowisko `main`, bez utraty plików | HEAD/status przed i po, lista zmian |
| R2-2 | Każda decyzja aliasowa zapisana jawnie, bez dopisywania niezatwierdzonej semantyki | diff biblioteki + lista ACTIVE/REVIEW/BLOCKED |
| R2-3 | Powiązania etykieta-wartość zweryfikowane na OPEX i B002-01..04, odpowiednie negatywne przypadki | testy i oczekiwane/otrzymane wartości, strony/sekcje |
| R2-4 | `ACTIVE` tylko po zatwierdzeniu człowieka i PASS regresji; `�` nie poprawiany domyślnie | zapis decyzji, test negatywny |
| R2-5 | Zgodność ról i dat z dokładnym zatwierdzonym JSON; brak zgadywania | testy/ewentualne lokalne BLOCKED |
| R2-6 | Brak zmian DB/Core/UI/PDF i plików roboczych w commicie | diff, status, lista commit files |
| R2-7 | Zwykły commit i push na `main` (o ile brak blokady) | SHA, `git ls-remote`, wynik push |

## 6. Raport i STOP

Zwróć krótki raport: wynik R2-1..R2-7, macierz **alias -> status przed/po -> test -> dowód/ograniczenie**, komendy testów i wyniki, zmienione pliki, commit/push (lub przyczynę STOP), otwarte przypadki `REVIEW/BLOCKED`. **STOP po tym etapie.** Właściwy PDF -> SDS-JSON-001 Evidence JSON DRAFT będzie wznawiany dopiero po kontroli tego raportu.
