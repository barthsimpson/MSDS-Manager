# TASK-062-R6 — inwentaryzacja pozostałych paczek SDS i diagnostyka kandydatów aliasów

**Status:** READY / AUTHORIZED — decyzja Architekta z 2026-11-12 („potwierdzam. działamy”)  
**TASK MODE:** DIAGNOSTIC / DISCOVERY (bez zmian kodu produkcyjnego)  
**Projekt:** MSDS Manager  
**Wykonawca:** Codex  
**Repozytorium:** `C:\Users\bartosz.murawski\Projects\MSDS-Manager`, istniejący `main`, bez branchy i worktree  
**Punkt bazowy:** TASK-062-R5 CLOSED, commit `4188b4ffd6c293e97c4426fd42d6306b8d93a7ec` (przed rozpoczęciem sprawdź faktyczny HEAD; nie resetuj zastanych zmian).

## 1. Cel

R5 potwierdził według raportu działanie autonomicznego ekstraktora na OPEX, czterech SYLGARD i jednym wielokartowym PDF 3M DP-490 (łącznie trzy logiczne SDS). W katalogu `data/sds/Paczki/` pozostają inne materiały do oceny. Architekt zatwierdził **kontynuowanie rozwoju biblioteki aliasów na kolejnych paczkach przed integracją z UI i importerem**.

**Wynik R6:** (a) wiarygodny rejestr dostępnych paczek i stopnia ich opracowania, (b) diagnostyka istniejącym ekstraktorem **pierwszej następnej nieopracowanej paczki**, (c) deduplikowana macierz konkretnych kandydatów aliasów / reguł z dowodami źródłowymi i propozycją kolejności dalszych paczek. R6 **nie zatwierdza ani nie aktywuje aliasów**.

## 2. Kontekst i punkty startowe (minimalna eksploracja)

- TDR-012 v1.0-approved, SDS-ALIAS-001 v1.0-approved, SDS-JSON-001 v1.0-approved (w repo); BDR-005 v1.2-approved i CORE-001 v1.9-approved tylko w zakresie granic decyzji człowieka i ochrony Core.
- `docs/task_reports/TASK-062_R5_REPORT.md`, TASK-062-R4/R5 — znane wyniki OPEX/SYLGARD/3M, nie odkrywaj ich ponownie.
- `config/sds_aliases.json` — 13 ACTIVE A-001..A-013 po R5; zasada `CANDIDATE -> decyzja Architekta -> test -> ACTIVE`.
- `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `app/infrastructure/filesystem/sds_alias_matcher.py`, `scripts/extract_sds_evidence.py` — aktualne narzędzia; nie buduj kolejnego parsera.
- `data/sds/Paczki/` — faktyczna zawartość do inwentaryzacji; ewentualne inne foldery wejściowe uwzględnij wyłącznie jeśli zastałe źródła/raporty jednoznacznie wskazują na nie.
- GOV-001, GOV-002 (lean: tylko niezbędny kontekst), `AGENTS.md`, o ile istnieje.

## 3. Zakres

### A. Rejestr paczek (całość, tylko metadane i odczyt)

1. Przejrzyj drzewo `data/sds/Paczki/` i sporządź rejestr każdej rzeczywistej paczki: nazwa katalogu, liczba PDF, liczba innych plików, lista PDF albo względne ścieżki w osobnym załączniku, ewentualne duplikaty na podstawie SHA-256 (obliczaj hash tylko gdy pomaga rozstrzygnąć powtórzenie).
2. Odróżnij **już przeanalizowane jako Golden Set** (OPEX, cztery SYLGARD, 3M DP-490) od **jeszcze nieprzeanalizowanych**; nie oznaczaj całej paczki jako „DONE” na podstawie pojedynczego dokumentu.
3. Zidentyfikuj możliwość przetwarzania PDF (warstwa tekstowa / zaszyfrowany / skan / uszkodzony) metodami już dostępnymi w projekcie, bez OCR. Nie zakładaj z góry liczby paczek ani dokumentów.
4. Wyznacz praktyczną kolejność dalszej analizy: różnorodność układów i producentów, czytelność, unikanie identycznych duplikatów; podaj uzasadnienie, bez rozszerzania zakresu na wszystkie paczki.

### B. Diagnostyka jednej następnej paczki (faktyczne PDF)

1. Wybierz **pierwszą sensowną nieopracowaną paczkę** według rejestru. Wykonaj diagnostykę istniejącym CLI na dostępnych w niej PDF z warstwą tekstową (jeśli paczka jest duża, zastosuj reprezentatywną próbę maksymalnie 5 różnych PDF i jawnie wskaż, co pozostało; nie wybieraj tylko łatwych przypadków).
2. Dla każdego badanego PDF określ **rzeczywistą** liczbę logicznych SDS i zakresy stron; raportuj niepewność segmentacji. Nie utożsamiaj 1 PDF z 1 SDS.
3. Pokaż wyniki pól identyfikacyjnych na każdym logicznym SDS: `product_name`, opcjonalny `manufacturer_product_code`, bieżący `issue_date`, `revision`, `parties[]` z dosłownymi rolami; stany `FOUND/NOT_FOUND/AMBIGUOUS/UNREADABLE` oraz G1/G2/G3/review status, jeżeli powstał JSON DRAFT.
4. Dla braków, konfliktów lub złego przypisania zidentyfikuj **konkretną etykietę/układ w oryginalnym SDS**: numer strony, sekcja, krótki literalny cytat, stan obecnego ekstraktora, oczekiwane zachowanie. Nie opieraj wniosków na nazwie pliku ani na zgadywaniu. Jeżeli PDF jest skanem, oznacz `UNREADABLE` i nie próbuj OCR.
5. Oddziel: brak aliasu, błąd segmentacji, błąd kontekstu/parsowania, niedostępny tekst, niejednoznaczność danych źródłowych. Nie proponuj aliasu, gdy rzeczywista przyczyna leży gdzie indziej.

### C. Macierz kandydatów do decyzji Architekta

Dla każdego **nowego, nieduplikowanego** przypadku podaj: `CANDIDATE ID`, PDF i logiczny SDS, etykietę literalną, sekcję, pole docelowe, regułę pobrania wartości, stronę i cytat, przykłady negatywne, wpływ na obecne 13 ACTIVE, proponowany test regresyjny i przewidywany priorytet. **Nowe aliasy pozostają CANDIDATE** — nawet gdy diagnostyka wygląda poprawnie. Rozdziel prosty alias od reguły kontekstowej. Do decyzji przedstaw możliwie mały pakiet uzasadnionych kandydatów, a nie każde odchylenie formatowania jako osobny alias.

### D. Wyniki i organizacja

- Zachowaj diagnostyczne JSON-y / walidacje tylko w ignorowanym `tmp/`, bez dołączania ich automatycznie do Git.
- Raport zapisz jako `docs/task_reports/TASK-062_R6_REPORT.md`; ewentualny rejestr paczek jako czytelna tabela w raporcie lub odrębny plik `.md` obok raportu. Zachowaj nazwę paczki i względne ścieżki, aby można było wskazać następny PDF bez ponownego skanowania.
- Nie wykonuj zmian implementacyjnych ani automatycznej aktywacji aliasów. Na tym etapie nie potrzebujemy nowego testu pełnej regresji, jeśli kod produkcyjny nie ulega zmianie.

## 4. Kryteria akceptacji

| ID | Wymagany rezultat / dowód |
|---|---|
| R6-1 | Preflight: praca na istniejącym `main`, aktualny HEAD, zachowany status roboczy, 13 dotychczasowych ACTIVE; bez resetów i naruszenia zastanych plików. |
| R6-2 | Pełna, policzalna inwentaryzacja katalogu paczek: wszystkie katalogi, ilości PDF, oznaczenie przetworzonych/nieprzetworzonych i duplikatów, bez wymyślania stanu DONE. |
| R6-3 | Jawny wybór jednej nowej paczki i rzeczywista diagnostyka istniejącym ekstraktorem; lista plików badanych oraz niebadanych, wyniki/ograniczenia. |
| R6-4 | Dla badanych logicznych SDS: zakres stron, pola ze stanami, walidacja i uzasadnione przykłady z konkretnych stron i sekcji; brak wycieku między kartami. |
| R6-5 | Deduplicowana macierz kandydatów aliasów/reguł lub wyraźny wniosek „brak nowych kandydatów”; każde ustalenie ma dowód, przypadek negatywny i propozycję testu. |
| R6-6 | Proponowana kolejność dalszych paczek, rozróżnienie problemów aliasowych od innych, brak zmian Core/DB/UI/ACTIVE/PDF i brak integracji. |

## 5. Ograniczenia i STOP

**Nie zmieniaj** `config/sds_aliases.json` (statusów/definicji), matcherów/pipeline/CLI, Core, BDR/TDR, ORM, PostgreSQL, migracji, UI, importera, schematów SDS-JSON/SDS-ALIAS, danych operacyjnych ani źródłowych PDF. Nie rejestruj produktów, producentów ani kart w Core. Nie uruchamiaj OCR ani LLM w runtime. Nie twórz nowego brancha/worktree, nie sprzątaj 20 wcześniej zgłoszonych nieśledzonych plików, nie wykonuj `git add .`.

Jeśli analiza ujawni konieczność zmiany kontraktu/architektury, przeszkodę uniemożliwiającą diagnostykę albo sprzeczność w rozpoznaniu danych, opisz ją i zatrzymaj tylko część zablokowaną; pozostałe niezależne wyniki inwentaryzacji przekaż. Nie naprawiaj przy okazji. **Nie uruchamiaj drugiej paczki ani implementacji kandydatów bez kolejnej decyzji Architekta.**

## 6. Raport i zakończenie

Raport R6 ma zawierać: tabelę R6-1…R6-6 z dowodami; rejestr paczek; wskazanie przeanalizowanej nowej paczki; wyniki diagnostyki i ścieżki `tmp/`; macierz kandydatów z cytatami; propozycję następnej paczki; komendy i wyniki; wykaz faktycznie zmienionych plików (oczekiwany wyłącznie raport/rejestr), odstępstwa i ryzyka. **STOP po raporcie.** Cerberus kontroluje raport, Architekt zatwierdza/odrzuca kandydatów, a osobna kontynuacja wdraża i regresyjnie aktywuje wybrane reguły.

Nie wykonuj commita/push automatycznie dla tego diagnostycznego etapu; jeśli lokalne zasady wymagają utrwalenia raportu, przedstaw zakres do jawnej decyzji i nie publikuj PDF ani JSON-ów roboczych.
