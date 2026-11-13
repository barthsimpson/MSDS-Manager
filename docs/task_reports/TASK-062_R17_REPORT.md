# TASK-062-R17 — Noyen: implementacja i regresja

**Data:** 2026-11-13. **Wynik:** R16-C01–C05 wdrożone w istniejącym ekstraktorze i lokalnej walidacji; pięć źródłowych SDS zweryfikowano. **STOP po R17.**

## R17-1 — preflight i źródła

Przed zmianami `main`, `HEAD`, `origin/main` i zdalny `refs/heads/main` wskazywały `cbaaa7cb235c48221af9de342d01fde364208f39` (`git status --short --branch`, `git log -3 --oneline`, `git rev-parse HEAD origin/main`, `git ls-remote --heads origin main`). Zastane nieśledzone dokumenty `docs/tasks/TASK-062_R16_DIAGNOSTYKA_KOLEJNEJ_PACZKI_SDS.md`, `docs/task_reports/TASK-062_R16_REPORT.md` i `docs/tasks/TASK-062_R17_NOYEN_IMPLEMENTACJA_I_REGRESJA.md` pozostawiono poza commitem R17. Zatwierdzone kontrakty i granice z AGENTS/GOV/TDR/SDS-JSON/BDR/CORE pozostają bez zmian. `config/sds_aliases.json` nadal zawiera dokładnie **13 ACTIVE A-001–A-013**.

Źródła to wyłącznie oryginalne pliki `data/sds/Paczki/paczka 7 Noyen/`; bieżące SHA-256 są zgodne z R16, a folder zawiera pięć różnych PDF i nic więcej. Każda strona ma warstwę tekstową, każdy PDF obejmuje jedną logiczną SDS z §1 na s. 1 i ciągłą numeracją stron. `NY-05` jest źródłowo kartą THINNER / Sherwin-Williams mimo nazwy folderu.

| ID | PDF | SHA-256 | Strony / tekstowe |
|---|---|---|---:|
| NY-01 | `Nitra Cid_16.02.2023 _PL_9.02.pdf` | `27515dc54c32e568bd2fdd0368c242d2b029e08618f6f3204156b85d901e734e` | 17 / 17 |
| NY-02 | `NOYEN 22' 26.04.2023 rew. 4.pdf` | `0a106f69565726ad0a898b31603cb3678a342f6fa8fb03351ce9495b9e2f1e0c` | 15 / 15 |
| NY-03 | `NOYEN PM200' 20.02.2023 rew. 4.pdf` | `fa49e0037b248572ae5bccdb4a9e6789f6496fa2e4a7628d3932b2df07b23ea8` | 13 / 13 |
| NY-04 | `NOYEN TIP2 17.11.2022 rew. 3.pdf` | `8738ab31c3f4fa9651cdef28ed0f999aebef5d9dbcf799df79b5b0af838476a6` | 15 / 15 |
| NY-05 | `NT019_SDS_Polish_PL 06, Grudzień, 2022 rew. 2.0.pdf` | `b4666605f692d03b9c55627b4da1180c46c2dbfc71f0d24f0ceafe53ddb1e3ff` | 17 / 17 |

## R17-2–R17-5 — wynik Evidence przed → po

`F` = `FOUND`, `N` = `NOT_FOUND`, `A` = `AMBIGUOUS`. Lewa strona to **zapisany R16 DRAFT**, prawa to **ponownie odczytany R17 DRAFT**; cytaty wskazują oryginalny PDF. Wszystkie nazwy pochodzą z §1.1, a nie z nazwy pliku. `raw` i wartość operacyjna są takie same w tej paczce: nie usuwano `®`/`™`, nie poprawiano pisowni ani nie skracano nazwy na myślniku.

| SDS | `product_name` przed → po; źródło | `manufacturer_product_code` przed → po | Bieżąca data / rewizja przed → po; źródło | `parties[]` przed → po; źródło |
|---|---|---|---|---|
| NY-01 | A/null → F `Nitra Cid`; s. 1 §1.1 `nazwa produktu : Nitra Cid`. Jawna etykieta wygrywa z `Postać produktu : Mieszanina` po `1.1. Identyfikator produktu`. | F `193` → bez zmian; s. 1 §1.1 `Kod produktu : 193`. | F `2023-02-16` / F `"9.02"` → bez zmian; nagłówek s. 1 `Data aktualizacji: 16.02.2023 ... Zastępuje wersję z dn.: 14.12.2021 Wersja: 9.02`. | **Fałszywe** F `SUPPLIER: Dostawca ... Dystrybutor` → dwa osobne F: `SUPPLIER: CID LINES N.V.` i `DISTRIBUTOR: CID LINES Sp. z. o.o.`; dwie kolumny §1.3 s. 1 `Dostawca` / `Dystrybutor` bezpośrednio nad odpowiednimi nazwami. |
| NY-02 | N/null → F `NOYEN 22 - Preparat do usuwania korozji i kamienia wodnego - koncentrat`; s. 1 §1.1 `1.1 Identyfikator produktu: ...`. | N/null → N/null; UFI `7300-F0FW-V00E-GPUE` nie jest kodem produktu. | N/null / N/null → F `2023-04-26` / F `"4"`; stopka s. 1 `Data sporządzenia: 29.01.2019 Aktualizacja: 26.04.2023 Wersja: 4 (zastępuje 3)`. | F `SUPPLIER: NOYEN sp. z o.o.` → bez zmian; §1.3 s. 1. |
| NY-03 | N/null → F `NOYEN PM200 - Preprat do mycia  i odtłuszczania powierzchni metalowych`; s. 1 §1.1, zachowana literówka `Preprat` i podwójny odstęp. | N/null → N/null; UFI `V770-F0RV-900H-D16S` wykluczone. | N/null / N/null → F `2023-02-20` / F `"4"`; stopka s. 1 `Data sporządzenia: 29.01.2019 Aktualizacja: 20.02.2023 Wersja: 4 (zastępuje 3)`. | F `SUPPLIER: NOYEN sp. z o.o.` → bez zmian; §1.3 s. 1. |
| NY-04 | N/null → F `NOYEN TIP2 - Preparat do usuwania nagarów`; s. 1 §1.1. | N/null → N/null; UFI `G160-D03A-000K-481V` wykluczone. | N/null / N/null → F `2022-11-17` / F `"3"`; stopka s. 1 `Data sporządzenia: 29.01.2019 Aktualizacja: 17.11.2022 Wersja: 3 (zastępuje 2)`. | F `SUPPLIER: NOYEN sp. z o.o.` → bez zmian; §1.3 s. 1. |
| NY-05 | F `THINNER` → bez zmian; s. 1 §1.1 `Nazwa produktu : THINNER`. | F `NT019` → bez zmian; s. 1 §1.1 `Kod produktu : NT019`. | F `2022-12-06` / F `"2"` → bez zmian; stopki s. 1/17 `Data wydania/Data aktualizacji: 06, Grudzień, 2022 ... Wersja: 2`; `2.0` z nazwy pliku nie zastępuje rewizji źródłowej. | Pusta lista → F `SUPPLIER: Sherwin-Williams Sweden AB`; s. 1 §1.3 nagłówek zawinięty `1.3 Dane dotyczące dostawcy karty` / `charakterystyki`, dalej nazwa firmy. `Kontakt krajowy / Sherwin-Williams Poland Sp. z.o.o.` zachowano tylko w `extraction_report.warnings`, z cytatem i s. 1 §1.3. |

NY-01 ma dwa różne, źródłowo uzasadnione podmioty. Pozostałe SDS mają tylko jawny `SUPPLIER`; żadnego `MANUFACTURER` nie dopisano. Dla NY-02–04 historyczna `Data sporządzenia: 29.01.2019` i numer po `zastępuje` nie zostały użyte jako bieżące wartości. `BDO: 000000803` w §1.3 NOYEN nie zostało uznane za kod produktu. `Dostawca` przy telefonie alarmowym w §1.4 NY-05 nie jest kolejnym podmiotem.

## Implementacja C01–C05 i walidacja

- **C01:** jawne `Nazwa produktu`/`Nazwa wyrobu`/udokumentowana nazwa w §1.1 ma pierwszeństwo nad ogólnym odczytem następnego wiersza `Identyfikator produktu`. Zapobiega konfliktowi z `Postać produktu`, bez zmiany 13 aliasów.
- **C02:** wąski odczyt dwukolumnowego §1.3 wiąże każdą etykietę z nazwą bezpośrednio pod jej kolumną. G2 ponownie potwierdza tę parę w źródle, a G2/G3 odrzuca sam ciąg etykiet jako `FOUND` nazwy. G3 nadal kontroluje rolę z etykietą i duplikat pary `(rola, nazwa)`; odrębne firmy mogą współistnieć.
- **C03:** wartość po dwukropku w tej samej linii `1.1 Identyfikator produktu:` jest czytana tylko z własnego §1.1. Pełny tekst po myślniku pozostaje częścią nazwy, w tym źródłowa literówka i odstępy NY-03.
- **C04:** kontekst stopki usuwa końcowe puste linie z ekstrakcji PDF. Odrębne wiązanie `Aktualizacja` i `Wersja` działa tylko na oznaczonym wierszu stopki z `Data sporządzenia`, `zastępuje` i numeracją strony; niespójne powtórzenia w jednej SDS dają `AMBIGUOUS/null`. G2 porównuje wartość i dowód z ponownym odczytem strony.
- **C05:** zawinięty nagłówek §1.3 prowadzi do szwedzkiego dostawcy. Kontakt krajowy jest zachowany jako `DOC-001:UNCLASSIFIED_LOCAL_CONTACT_REQUIRES_HUMAN_REVIEW s.1 §1.3: Kontakt krajowy / Sherwin-Williams Poland Sp. z.o.o.` w istniejącej liście `extraction_report.warnings`, bez `MANUFACTURER`, `DISTRIBUTOR` lub `OTHER`. G2 kontroluje cytat dostawcy.

Nowe dopasowania są kontekstowymi funkcjami matchera i pipeline, bez wpisów w katalogu aliasów, nowych ról lub pól kontraktu. G1/G2/G3 PASS potwierdza tylko poprawność DRAFT względem walidowanych reguł, nie zgodę na import lub zatwierdzenie tożsamości producenta.

## R17-6 i R17-7 — CLI, zapisane artefakty, testy

Polecenie CLI wykonano pięć razy, po razie na unikalny SHA, w kolejności tabeli: `.\.venv\Scripts\python.exe -m scripts.extract_sds_evidence <oryginalny PDF> --output-dir tmp/task062r17_noyen_final --source-id NY-0N`. Nowy katalog nie istniał przed wykonaniem; nie nadpisano R16. **Kody wyjścia: pięć razy 0.** Z dysku ponownie odczytano **5 `*.evidence.json` i 5 `*.validation.json`** oraz sprawdzono oczekiwaną macierz pól, dowody i SHA. Każdy zapis: `source.language=pl`, `readability_status=READABLE`, jeden `DOC-001` od s. 1 do końca PDF, `review_status=PENDING_REVIEW`, `validation.status=REQUIRES_HUMAN_REVIEW`, `extraction_report.errors=[]`, **G1/G2/G3 PASS**. G3 ma `DOC-001:MANUFACTURER_REQUIRES_HUMAN_REVIEW` dla każdego źródła; NY-05 ma dodatkowo źródłowy cytat kontaktu krajowego w ostrzeżeniach. Wszystkie artefakty znajdują się w ignorowanym `tmp/`.

Testy focused R17: `.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_task062_r17_noyen.py` → **10 PASS**. Test pięciu oryginałów sprawdza SHA, pola, role, cytaty, strony, statusy i bramki; potwierdza też wykluczenie źródłowych UFI/BDO jako kodu. Syntetyczne negatywy obejmują `Postać produktu` i UFI jako nazwę, etykiety jako firmę, zamienione wartości/role w kolumnach, duplikat podmiotu, złą lub sprzeczną stopkę, zawinięty nagłówek, zmieniony cytat, kontakt krajowy, §1.4 i granicę obcej logicznej SDS.

Obowiązkowa relewantna regresja:

```text
.\.venv\Scripts\python.exe -m pytest -q --basetemp tmp/task062r17_regression tests/unit/test_task062_r2_aliases.py tests/unit/test_task062_r3_evidence.py tests/unit/test_task062_r5_3m_aliases.py tests/unit/test_task062_r7_weicon.py tests/unit/test_task062_r9_loctite.py tests/unit/test_task062_r11_kch.py tests/unit/test_task062_r13_compound.py tests/unit/test_task062_r15_cyna_pasty.py tests/unit/test_task062_r17_noyen.py
```

**90 PASS, 0 FAIL, 0 SKIP** (101,31 s). Obejmuje wcześniejsze nazwy, role i rewizje `V005.1`, `04`, `5.0/PL` oraz wszystkie wymienione etapy. Pierwszy przebieg przed końcową poprawką wykazał fałszywe rozpoznanie etykiety `Mfg. in U.S.A and exported by:` w OPEX jako dostawcy NY-05 typu zawiniętego nagłówka; regułę zawężono i dodano negatyw. Ten sam przebieg miał niezależny błąd uprawnień przy czyszczeniu starego `.pytest_tmp`; końcową regresję uruchomiono w nowym katalogu `tmp/`. Dodatkowy przebieg R3+R17 po poprawce: **20 PASS**. Nie uruchamiano DB/UI E2E, zgodnie z zakresem R17.

## R17-8, R17-9 — zakres, Git i STOP

Zakres selektywnego commita: `app/infrastructure/filesystem/sds_alias_matcher.py`, `app/infrastructure/filesystem/sds_evidence_pipeline.py`, `tests/unit/test_task062_r17_noyen.py` i niniejszy raport. `git diff --check` nie wykazał błędów białych znaków. Katalog `config/sds_aliases.json`, Core, model PRODUCT–SDS, SDS-JSON-001, DB/migracje, importer, UI oraz źródłowe PDF pozostały bez zmian. Nie dodano zastanych nieśledzonych dokumentów R16/R17 ani zawartości `tmp/` do commita. Selektywny commit i zwykły push na `main` następują po pozytywnej kontroli; końcowy SHA i zgodność `HEAD`/`origin/main`/zdalnego `main` są podawane w przekazaniu, nie zgadywane w treści raportu.

Zatwierdzona zasada przyszłego mechanizmu podpowiedzi producenta pozostaje poza R17: przy braku jawnego `MANUFACTURER` dystrybutor, a potem dostawca mogą być jedynie kandydatami do decyzji użytkownika; ich role źródłowe nie są przepisywane. Otwarty R14-C11 dotyczący grupowych SDS i wariantów pozostaje nierozstrzygnięty. **STOP po R17; bez R18 i bez wdrażania podpowiedzi.**

## Rozliczenie kryteriów

| ID | Wynik |
|---|---|
| R17-1 | PASS: zgodny HEAD/upstream/remote przed zmianą, 5 SHA zgodnych z R16, 13 ACTIVE, zastane untracked zachowane. |
| R17-2 | PASS: NY-01 `Nitra Cid`, `193`, `2023-02-16`, `9.02` i negatyw `Postać produktu`. |
| R17-3 | PASS: dwa podmioty NY-01 z rolami i dowodami; G2/G3 odrzuca etykiety jako nazwę, sprawdza role i duplikaty. |
| R17-4 | PASS: pełne nazwy, bieżące daty i dokładne rewizje NY-02–04; UFI, BDO, data sporządzenia i poprzednia wersja wykluczone. |
| R17-5 | PASS: NY-05 `SUPPLIER Sherwin-Williams Sweden AB`, kontakt krajowy w ostrzeżeniu z cytatem, bez automatycznej roli. |
| R17-6 | PASS: 5 CLI kod 0; 5 DRAFT + 5 walidacji odczytane z dysku, właściwe statusy i G1/G2/G3 PASS. |
| R17-7 | PASS: focused 10 PASS, R3+R17 20 PASS, końcowa obowiązkowa regresja 90 PASS / 0 FAIL / 0 SKIP. |
| R17-8 | PASS: tylko matcher, pipeline, test R17 i raport; 13 ACTIVE oraz chronione warstwy bez zmian. |
| R17-9 | Selektywny commit i zwykły push po PASS; końcowy SHA i stan zdalny w przekazaniu. |
