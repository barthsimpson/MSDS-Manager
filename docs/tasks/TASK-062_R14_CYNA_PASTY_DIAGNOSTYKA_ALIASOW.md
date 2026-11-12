# TASK-062-R14 — paczka 6 cyna, pasty: diagnostyka ekstrakcji SDS i kandydaci reguł

**Status:** READY / AUTHORIZED — Architekt zatwierdził kontynuację i utrzymanie testów regresyjnych po R13 (2026-11-12).  
**TASK MODE:** DIAGNOSTIC / DISCOVERY — bez implementacji.  
**Projekt:** MSDS Manager | **Wykonawca:** Codex  
**Repo:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, bieżący `main`; bez osobnych gałęzi/worktree.  
**Punkt odniesienia:** R13 funkcjonalnie zaakceptowany przez Architekta; raport R13 deklaruje commit/push, ale końcowe SHA nie zostało dostarczone w rozmowie. **Zweryfikuj** HEAD = origin/main przed rozpoczęciem; nie zgaduj SHA i nie resetuj nowszych zmian.

## 1. Cel i rezultat

Przeprowadzić **wyłącznie diagnostykę** dotychczasowego ekstraktora PDF → Evidence JSON DRAFT na **paczce 6 cyna, pasty** i dostarczyć audytowalne porównanie danych wyjściowych z treścią oryginalnych SDS oraz deduplikowaną macierz kandydatów `R14-C01...` do osobnej decyzji Architekta. Nie wdrażać kandydatów w R14. Zastosować doświadczenia R11/R13: nawet G1/G2/G3 PASS może współistnieć z brakami semantycznymi; zweryfikować role podmiotów i nie utożsamiać nazw osób, etykiet ani danych kontaktowych z firmą.

## 2. Zamknięty korpus: 9 PDF wg rejestru R6

Źródła znajdują się w `data/sds/Paczki/paczka 6 cyna, pasty/`. Liczby stron to **dane inwentaryzacyjne R6**, wymagające potwierdzenia z bieżących plików. Identyfikatory są wyłącznie diagnostyczne, nie służą za wartości danych.

| ID | Dokładna nazwa pliku | Stron wg R6 |
|---|---|---:|
| CP-01 | `2020_12_Pasta RMA 218_rew 2 2020.12.14.pdf` | 8 |
| CP-02 | `Anti-Seize Pasty Montazowe 12.14.2022 rew. 4.03.pdf` | 18 |
| CP-03 | `cyna_SDS-SLZ-bezołowiowe-z-topnikiem-EVO-EVO11-PRO-SW26-1.1.2 v.5.pdf` | 19 |
| CP-04 | `cyna_SDS-Spoiwo-lutownicze-bezołowiowe-z-topnikiem-113-CF48 v.5.pdf` | 19 |
| CP-05 | `INSTALFLUX TLA-4N _PL_07.03.2022.pdf` | 12 |
| CP-06 | `Pasta AMTECH RMA-218, 223, 559 -TPF_2020.12.14_rew3.pdf` | 9 |
| CP-07 | `Pasta termoprzewodząca H 26.01.2023 rew. 11.0.pdf` | 9 |
| CP-08 | `Topnik lutowniczy 559 223 218 4300 321_08.11.2024 rew. 1.pdf` | 9 |
| CP-09 | `Topnik-TK-83-PL-2 26.01.2024 rew. 07.pdf` | 17 |

**Nie zakładaj**: dziewięciu unikalnych SHA, dziewięciu logicznych SDS ani zgodności nazw plików z produktem, datą i rewizją. Sprawdź faktyczne dokumenty, SHA, warstwę tekstową i logiczne granice. Jeżeli dokument jest wieloproduktowy, odróżnij jedną SDS dotyczącą grupy produktów od kilku odrębnych SDS — **nie rozdzielaj mechanicznie po przecinkach/nazwach produktów z tytułu**. Nie przesądzaj nowego modelu wieloproduktowości.

## 3. Źródła, reguły, ograniczenia

**Najpierw:** lokalne `AGENTS.md`, adekwatne GOV-001/GOV-002, `docs/task_reports/TASK-062_R6_INVENTORY.md`, `docs/task_reports/TASK-062_R13_REPORT.md`, TDR-012/SDS-JSON-001/SDS-ALIAS-001 i właściwe granice BDR-005/CORE-001 **tylko w zakresie potrzebnym**. Znane punkty startowe: `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `scripts/extract_sds_evidence.py`, `config/sds_aliases.json`. Potwierdź faktyczną liczbę ACTIVE (wg R13: 13) bez modyfikacji katalogu. Nie wykonuj audytu całego repo.

Zachowaj zatwierdzone zasady:
- `FOUND` wymaga źródłowego cytatu, strony i właściwej sekcji; przy braku dowodu `NOT_FOUND`/`AMBIGUOUS`/`UNREADABLE`, bez domysłów z nazwy pliku.
- `manufacturer_product_code` opcjonalny; jawny `Article number` / `Numer artykułu` w §1.1 może proponować kod tekstowy (z zerami), lecz **UFI/CAS/EINECS/numer SDS** nim nie są.
- Role z R11: jednoznaczne `Producent` → `MANUFACTURER`, `Dystrybutor` → `DISTRIBUTOR`; z R13 łączone `Manufacturer/Supplier` / `Producent/Dostawcy` → `SUPPLIER`; źródłowy cytat zachowany. Wielu dystrybutorów dozwolonych tylko przy jednoznacznej tożsamości, nierozstrzygnięte bloki zachowują stan niejednoznaczności; nie tworzyć podmiotów z kontaktów/osób.
- Data wydruku, data zastępowana lub data w nazwie pliku nie mogą zastąpić bieżącej daty SDS. Rewizje jako dokładne ciągi (np. `V005.1`, `04`, z zerami), nie jako liczby. Dla niejednoznacznej daty cyfrowej stosować przyjętą regułę z kontekstem i pierwszeństwem polskiego formatu, jeśli brak dowodu odmiennej konwencji.
- Każdy wynik pozostaje `PENDING_REVIEW`; źródłowa rola producenta **nie** zatwierdza tożsamości w Core; G1/G2/G3 PASS nie stanowi dowodu pełnej poprawności ekstrakcji.

## 4. DO — kroki Codexa

1. **Preflight:** `git status --short --branch`, `git log -1 --oneline`, porównanie HEAD/upstream, 13 ACTIVE wg stanu faktycznego; nie naruszaj zastanych nieśledzonych dokumentów. Jeśli `origin/main` różni się od HEAD, wyjaśnij przed diagnostyką; bez automatycznego reset/merge.
2. **Źródła:** sprawdź 9 PDF, SHA-256, liczbę stron i warstwę tekstową, typ SDS vs karta techniczna/inny typ, liczbę i prawdziwe zakresy logicznych SDS. Duplikaty identycznego SHA przetwarzaj raz, ale rozlicz wszystkie pliki; nie używaj OCR/LLM.
3. **CLI:** uruchom istniejące `scripts.extract_sds_evidence` na każdym unikalnym i czytelnym źródle, z ID `CP-01...CP-09` i nowym ignorowanym katalogiem np. `tmp/task062r14_cyna_pasty/`. Nie nadpisuj istniejących artefaktów; bez zmian parsera/kontraktu i bez nowych zależności.
4. **DRAFT:** faktycznie ponownie odczytaj z dysku każde `*.evidence.json` i `*.validation.json`; zanotuj kody CLI, strony, segmenty, G1/G2/G3, `review_status`, `validation.status`, ostrzeżenia i błędy. Rozlicz wszystkie dokumenty, także niepowodzenia — bez sztucznego `PASS`.
5. **Porównanie źródłowe:** dla **każdego logicznego SDS** porównaj `product_name` (raw i operacyjna), `manufacturer_product_code`, bieżące `issue_date`, dokładne `revision`, `parties[]` (nazwy, liczba, role, dowody). Zestaw faktyczny stan z JSON (`FOUND/NOT_FOUND/AMBIGUOUS/UNREADABLE`) ze spodziewanym odczytem PDF, cytatem, stroną i §1.1/§1.3/nagłówkiem. Nie utożsamiaj wielu produktów z wieloma logicznymi SDS bez dowodów. Zidentyfikuj możliwe błędy pozytywnie zwalidowanych wartości.
6. **Diagnoza przyczyn:** rozróżnij nowy literalny alias, wariant układu/kolumn, parser daty, wersję, język, segmentację, rolę/multi-party, wieloproduktowość, błąd semantyki, czytelność oraz faktyczny brak informacji. Zidentyfikuj wpływ na wcześniejsze formaty i niebezpieczne pozytywne dopasowania.
7. **Kandydaci:** przygotuj deduplikowaną macierz `R14-C01...` z priorytetem, źródłowym cytatem i miejscem, polem, obecnym i proponowanym bezpiecznym wynikiem, testem pozytywnym i negatywnym, rodzajem zmiany, wpływem na dotychczasowe 13 ACTIVE i regresję R2/R3/R5/R7/R9/R11/R13. Odrębnie zaznacz **decyzje domenowe wymagające Architekta**, zwłaszcza model wielu produktów na jednej SDS, jeśli występuje. Brak kandydatów jest dopuszczalny tylko z udokumentowanym pokryciem.
8. **Zakończenie:** przygotuj raport; nie wprowadzaj zmian do kodu ani nie rozpoczynaj implementacji R15.

## 5. Kryteria akceptacji

| ID | Wymaganie | Dowód |
|---|---|---|
| **R14-1** | Potwierdzony HEAD/upstream, brak naruszenia plików zastanych, ACTIVE według lokalnego katalogu. | Krótki preflight w raporcie. |
| **R14-2** | Rozliczenie 9 źródeł: SHA, strony, tekst, typ i duplikaty. | Inwentaryzacja źródeł. |
| **R14-3** | Liczba i zakres logicznych SDS potwierdzone z treści; osobno analiza dokumentów obejmujących więcej niż jeden produkt, jeśli występują. | Tabela segmentacji i krótkie dowody z PDF. |
| **R14-4** | Odnotowane rzeczywiste CLI i odczytane JSON/validation; porównanie semantyczne każdej SDS z cytatami §1.1, §1.3 i nagłówka oraz jawne błędy pomimo PASS. | Macierz SDS: DRAFT → PDF, statusy/błędy. |
| **R14-5** | Nieduplikowane kandydaty `R14-C01...` (lub dowód ich braku), negatywy, priorytety, wpływ na regresję; bez niezatwierdzonych aktywacji. | Macierz kandydatów i lista decyzji Architekta. |
| **R14-6** | Raport, statusy i STOP; zero zmian kodu, Core, JSON-contract, DB, UI, aliasów, PDF i testów. | `git diff` i spis artefaktów. |

## 6. Wyłączenia i raport

**DO NOT TOUCH:** matcher, pipeline, CLI, testy, katalog aliasów, Core, kontrakt Evidence JSON, BDR/TDR, DB/migracje, importer, UI, źródłowe PDF; żadnych branchy/worktree, OCR/LLM, `git add .`, kompilacji niezwiązanych komponentów, force push ani zmian przy okazji. **Nie uruchamiaj pełnej regresji w R14**, bo nie zmieniasz kodu; obowiązek regresji przenosimy do późniejszego TASK implementacyjnego (R15) i pozostaje stałym wymaganiem.

**Raport:** `docs/task_reports/TASK-062_R14_REPORT.md` zawierający R14-1…R14-6, stan repo/aliasów, tabelę 9 PDF, tabelę logicznych SDS z cytatami/wartościami przed i proponowanymi, wyniki CLI/walidacji, kandydatów i decyzje Architekta, odchylenia oraz ryzyka. Evidence i walidacje wyłącznie w ignorowanym `tmp/`. Brak commita/push w etapie diagnostycznym.

**STOP:** gdy dokument jest nieczytelny, segmentacja niepewna, źródła sprzeczne lub potrzebna zmiana Core/kontraktu/modelu danych, zapisz dowody i blokadę dla konkretnego przypadku, kontynuuj pozostałe niezależne dokumenty. Nie zgaduj, nie implementuj i nie otwieraj nowej paczki.

**Zasada:** Automatyzacja proponuje, człowiek zatwierdza, a Core pozostaje chroniony.
