# TASK-062-R12 — paczka 10 COMPOUND: diagnostyka ekstrakcji i kandydaci reguł

**Status:** READY / AUTHORIZED — Architekt zatwierdził kontynuację po R11.  
**TASK MODE:** DIAGNOSTIC / DISCOVERY — bez implementacji.  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repo:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`; bez branchy/worktree.  
**Stan odniesienia:** R11 CLOSED, `HEAD = origin/main = ca71389` według ostatniego potwierdzenia użytkownika. Zweryfikuj faktyczny stan na początku; nie resetuj nowszych zmian ani nie czyść plików roboczych.

## 1. Cel i jedyny rezultat

Zdiagnozować **istniejący** ekstraktor PDF → Evidence JSON DRAFT na całej paczce `data/sds/Paczki/paczka 10 compound/`, porównać wyniki z rzeczywistą treścią SDS oraz przygotować **deduplikowaną macierz kandydatów `R12-C01...`** do decyzji Architekta. Nie implementować poprawek, nie aktywować aliasów. Zdiagnozować również semantykę rozpoznanych stron/sekcji, dat, rewizji i ról podmiotów — samo G1/G2/G3 PASS nie dowodzi poprawnego znaczenia pól.

## 2. Zamknięty zakres źródeł

Zgodnie z zatwierdzonym rejestrem R6 paczka zawiera trzy PDF, wszystkie strony miały warstwę tekstową; liczby zweryfikuj lokalnie:

| ID | Plik względnie do `data/sds/Paczki/paczka 10 compound/` | Strony wg R6 |
|---|---|---:|
| CMP-01 | `Compound R 20_20211129 rew. 29112021.pdf` | 11 |
| CMP-02 | `Compound R 35 E_pl_20230707, rew. 15.pdf` | 11 |
| CMP-03 | `Compound R 48_pl_20230707 rew 15.pdf` | 10 |

Nie zakładaj identyczności plików ani jednego SDS na PDF tylko na podstawie rejestru. Oblicz SHA-256, sprawdź czy pliki są powielone oraz potwierdź granice logicznych SDS na podstawie treści. Nazwy plików służą **wyłącznie** do wskazania wejścia — nigdy nie są dowodem wartości domenowych.

## 3. Kontekst autorytatywny i punkty startowe

Odczytaj wyłącznie zakres potrzebny do diagnostyki:

- `AGENTS.md` oraz stosowne GOV-001/GOV-002, TDR-012, SDS-ALIAS-001 i SDS-JSON-001 (bez audytu całego repo).
- `docs/task_reports/TASK-062_R6_INVENTORY.md` — wpisy paczki 10; `TASK-062_R11_REPORT.md` — najnowsza semantyka i regresja (56 PASS według raportu); ewentualnie R10/R9 tylko w razie konkretnej potrzeby.
- `config/sds_aliases.json` — 13 ACTIVE A-001–A-013 według R11; sprawdź stan, **nie zmieniaj**.
- `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py` — istniejący pipeline i CLI.
- Obowiązujące zatwierdzone BDR-005 v1.2 i CORE-001 v1.9 — tylko potrzebne granice tożsamości i ochrony Core.

**Reguły obowiązujące:** `manufacturer_product_code` jest opcjonalny; UFI, CAS, numer dokumentu, numer karty, nazwa PDF nie są automatycznie kodem produktu. Role `MANUFACTURER`, `DISTRIBUTOR`, `SUPPLIER` pozostają rozdzielone i zawsze mają podstawę w źródle. Propozycja producenta nie jest jego zatwierdzeniem w Core. W nazwie operacyjnej usuwaj wyłącznie `®` i `™`; w Evidence zachowuj oryginalny zapis, cytat, stronę i sekcję. Daty wyznaczaj z właściwej bieżącej etykiety; przy nierozstrzygniętym zapisie cyfrowym stosuj wcześniej zatwierdzony priorytet polskiego DD/MM/YYYY, chyba że kontekst dokumentu wyraźnie dowodzi innego porządku. Rewizje zachowuj tekstowo, wraz z prefiksami i zerami.

## 4. DO — wykonanie

1. **Preflight:** potwierdź katalog roboczy, `main`, `HEAD`, `origin/main`, `git status` i liczbę aktywnych aliasów. Nie modyfikuj istniejących zmian/nieśledzonych dokumentów. Nie ponawiaj inwentaryzacji wszystkich 134 plików.
2. **Źródła:** sprawdź istnienie trzech PDF, SHA-256, rzeczywistą liczbę stron i czytelność warstwy tekstowej bez OCR. Rozpoznaj SDS vs inny dokument i liczbę/rzeczywiste zakresy logicznych SDS, nie opierając się tylko na regexie ani założeniu 1 PDF = 1 SDS. Identyczne SHA przetwarzaj raz, ale rozlicz oba wystąpienia.
3. **Ekstrakcja:** uruchom **istniejące** CLI dla każdego unikalnego, odczytywalnego źródła z ID `CMP-01...CMP-03`, np. ` .\.venv\Scripts\python.exe -B -m scripts.extract_sds_evidence '<PDF>' --output-dir tmp/task062r12_compound --source-id CMP-01`. Jeśli katalog ma istniejące wyniki, wybierz nową ignorowaną ścieżkę; nie nadpisuj. Nie opracowuj dodatkowego parsera lub nowych zależności.
4. **Rzeczywisty wynik:** odczytaj wygenerowane `*.evidence.json` i `*.validation.json` z dysku. Dla każdego źródła podaj `logical_sds_count`, granice, G1/G2/G3, `review_status`, `validation.status`, ostrzeżenia i kod powrotu CLI. Brak pliku lub nierozpoznany dokument raportuj jawnie, nie generuj sztucznego PASS.
5. **Porównanie ze źródłem:** dla każdej logicznej SDS zestaw `product_name` (źródłowe i operacyjne), `manufacturer_product_code`, bieżące `issue_date`, `revision`, `parties[]` (dokładna nazwa, rola). Podaj stan `FOUND/NOT_FOUND/AMBIGUOUS/UNREADABLE`, rzeczywistą wartość z DRAFT i — jeśli PDF zawiera dowód — wartość spodziewaną z krótkim literalnym cytatem, stroną i sekcją/nagłówkiem. Rozdziel brak informacji w PDF od błędu ekstraktora; zweryfikuj, że nazwa roli nie stała się nazwą firmy (lekcja R11).
6. **Klasyfikacja przyczyn:** dla każdej luki rozstrzygnij czy to: nowa literalna etykieta, kontekst/układ, format/parser daty, rewizja, rola podmiotu, segmentacja, czytelność, rzeczywista wieloznaczność lub faktyczny brak wartości. Sprawdź szczególnie przypadki konfliktów dat/rewizji i dowodów pochodzących z innej logicznej SDS. G1/G2/G3 PASS nie zastępuje audytu semantyki.
7. **Macierz:** stwórz nieduplikowane `R12-C01...` z priorytetem, wskazaniem źródła i SDS, cytatem/stroną/sekcją, mapowanym polem, obecnym stanem, bezpiecznym oczekiwanym wynikiem, klasyfikacją przyczyny, testami pozytywnymi i negatywnymi, możliwym wpływem na 13 ACTIVE i regresję OPEX/SYLGARD/3M/WEICON/LOCTITE/KCH. Rozróżnij zmianę istniejącego matchera od potrzeby nowego aliasu. **Kandydaci pozostają CANDIDATE**; wyraźnie oznacz kwestie semantyczne wymagające decyzji Architekta.
8. **Raport:** wskaż zalecane następne decyzje, ale nie wdrażaj ich; nie rozpoczynaj kolejnej paczki.

## 5. Kryteria akceptacji

| ID | Wymaganie i dowód |
|---|---|
| **R12-1** | Preflight `main`/HEAD/upstream/stan roboczy oraz aktywny katalog aliasów opisane; brak naruszenia zastanych plików. |
| **R12-2** | Trzy pozycje paczki rozliczone z SHA, liczbą stron i czytelnością; duplikaty — jeśli istnieją — jawnie uzasadnione SHA. |
| **R12-3** | Liczba i faktyczne granice logicznych SDS wyznaczone ze źródła, w tym nietypowe oznaczenia §1. |
| **R12-4** | Dla każdego SDS istnieje porównanie DRAFT z PDF dla wszystkich pól tożsamości i metadanych, cytaty/strony, statusy walidacji i jawne braki pomimo PASS. |
| **R12-5** | Nieduplikowana macierz `R12-C01...` z priorytetem, negatywami i wpływem regresyjnym lub udokumentowany brak kandydatów; zero aktywacji. |
| **R12-6** | Raport podaje komendy, kody zakończenia, rzeczywistą liczbę zapisanych/odczytanych Evidence + validation JSON, granice zakresu, ryzyka i STOP bez wdrożenia. |

## 6. Wyłączenia, Git, STOP i raport

**DO NOT TOUCH:** kod ekstraktora, matcher, CLI, testy, `config/sds_aliases.json`, kontrakt JSON, Core, BDR/TDR, PostgreSQL/ORM/migracje, importer, UI, oryginalne PDF ani historia Git. Bez OCR/LLM, nowych zależności, branchy/worktree, `git add .`, reset/force push. Zatwierdzenie przechowywania źródłowych SDS w Git nie oznacza publikacji roboczych JSON.

**Artefakty:** `docs/task_reports/TASK-062_R12_REPORT.md` — tabela kryteriów R12-1...R12-6, rozliczenie każdego PDF i logicznej SDS, porównanie pól, macierz kandydatów i ograniczenia. Generowane Evidence/validation oraz pomocnicza diagnostyka wyłącznie pod ignorowanym `tmp/`. Diagnostyka nie wymaga commita/push; pozostaw raport do kontroli Cerberusa.

**STOP:** przy nierozstrzygniętej roli/semantyce, nieczytelnym PDF, niepewnej segmentacji lub potrzebie zmiany Core/kontraktu — nie zgaduj, oznacz ograniczenie, kontynuuj niezależne dokumenty. Po raporcie **STOP**, bez implementowania kandydatów, kolejnej paczki lub integracji z aplikacją.

**Zasada:** Automatyzacja proponuje, człowiek zatwierdza, Core pozostaje chroniony.
