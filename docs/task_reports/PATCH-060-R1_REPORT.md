# PATCH-060-R1 — raport diagnozy regresji karty produktu

**Data:** 2026-11-03

**Wynik:** przyczyna potwierdzona; **STOP przed migracją bazy operatora**. PATCH pozostaje **ACCEPTANCE PENDING**.
**Podstawa:** `docs/tasks/PATCH-060-R1_Product_Card_SDS_History_Regression_DRAFT.md`.

## Odtworzenie i przyczyna

W konfiguracji bazy operatora odczytano, bez zapisu, produkt `SYLGARD 160 Silicone Elastomer-Part A` producenta `DOW POLSKA SP.Z O.O.` (`product_id=8385e28101e6409c8110d33febbfdc86`). Jego bieżący SDS ma status `CURRENT` i rewizję `5.0`, zgodnie ze zgłoszeniem. Wywołanie tej samej metody `ShellComposition.list_sds_history(product_id)`, której używa karta, odtworzyło wyjątek. Karta przechwytuje go w `app/presentation/streamlit/product_registry.py` i wyświetla ogólne „Nie udało się odczytać historii SDS.”, po czym kończy renderowanie przed historią, PDF i akcją wycofania.

Istotny fragment rzeczywistego tracebacku:

```text
File "app/presentation/streamlit/composition.py", line 370, in list_sds_history
  return SqlAlchemySdsInvalidationRepository(session).list_for_product(product_id)
File "app/infrastructure/db/repositories/sds_invalidation.py", line 22, in list_for_product
  rows = self._session.execute(...).all()
psycopg.errors.UndefinedTable: relacja "sds_invalidation" nie istnieje
LINE 2: FROM sds_documents LEFT OUTER JOIN sds_invalidation ON sds_i...
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable) relacja "sds_invalidation" nie istnieje
```

Pełny traceback, wraz z SQL i parametrem produktu, zapisano w `tmp/task060_r1_traceback.txt`. Przechwycono go przy bezpośrednim wywołaniu ścieżki aplikacji, ponieważ obsługa wyjątku w Streamlit ukrywa go przed interfejsem. Zapytanie łączy `sds_documents` z `sds_invalidation`; to tabela dodawana przez migrację TASK-060 `e4c6f21a9d80`. Odczyt `alembic_version` w bazie operatora dał `b7d4a1f03962`, a `to_regclass('public.sds_invalidation')` zwróciło `NULL`. Połączenie i odczyty produktu oraz bieżącego SDS działają, więc przyczyną nie są uprawnienia do połączenia ani brak produktu. Bezpośrednią przyczyną regresji jest **brak wdrożonej migracji TASK-060 w bazie operatora**. Nie stwierdzono błędu zapytania na schemacie po migracji.

## Kontrola porównawcza i R1–R5

Izolowana baza odbiorowa `msds_task060_accept_f5dcbfce1be3` ma `alembic_version=e4c6f21a9d80`. Ten sam odczyt historii zwrócił dwa SDS (`CURRENT`, `ARCHIVED`); oba pliki testowe istnieją, a liczba rekordów audytu wycofania dla produktu wynosi zero. Lokalny serwer pod [http://127.0.0.1:8760](http://127.0.0.1:8760) zwrócił HTTP 200. Produkt do przyszłych oględzin: `TASK060-ACCEPT`, `product_id=d75d985f91fb44c49528b1924120e61e`. Poprzedni `TASK-060_ACCEPTANCE_REPORT.md` dokumentuje otwarcie tej karty w AppTest i obecność historii oraz akcji przy obu SDS; nie zastępuje to fizycznego odbioru.

| Kryterium | Wynik i dowód |
|---|---|
| R1 — lista i karta | **FAIL w bazie operatora:** lista pokazuje produkt, a karta kończy się zgłoszonym komunikatem. **PASS technicznie na bazie izolowanej:** wcześniejszy AppTest otworzył kartę po migracji. |
| R2 — historia i PDF | **FAIL dostępu przez kartę operatora** z powodu wyjątku przed renderowaniem. **PASS technicznie na bazie izolowanej:** odczyt dwóch pozycji i obecność obu testowych PDF. Nie ma dowodu utraty pliku operatora; jego PDF nie był otwierany ani zmieniany w diagnozie. |
| R3 — akcja dla CURRENT/ARCHIVED | **FAIL dostępności w karcie operatora** z tego samego powodu. Wcześniejszy AppTest izolowanej bazy potwierdził akcje przy obu statusach; test UI TASK-060 potwierdza brak akcji dla `INVALIDATED`. Nie wykonano wycofania. |
| R4 — test regresyjny | **NIEZAMKNIĘTE:** odtworzenie na rzeczywistym schemacie operatora i kontrola na schemacie po migracji wskazują różnicę środowisk. Nie dodano testu ani poprawki kodu, zgodnie z dyspozycją draftu dla brakującej migracji. Dwa dotknięte zestawy unit/AppTest: **29 passed**. `git diff --check`: kod 0; Git zgłosił ostrzeżenia o istniejących plikach testowych bez uprawnień i konwersji LF/CRLF. |
| R5 — oględziny operatora | **ACCEPTANCE PENDING:** operator zgłosił nieudaną próbę na swojej bazie. Po bezpiecznym wdrożeniu migracji potrzebne są fizyczne oględziny lista → karta → historia → PDF → akcja. |

## Zmiany i dalsze działanie

Nie zmieniono kodu aplikacji, Core, BDR, TDR, BHP ani schematu lub danych bazy operatora. Nie usunięto dokumentów i nie wykonano wycofania SDS. Dodano wyłącznie ten raport oraz tymczasowe skrypty/traceback diagnostyczny w `tmp/`; kontrole SQL uruchomiono z wymuszonym trybem transakcji read-only. Zastane niezacommitowane zmiany repozytorium pozostawiono bez ingerencji.

Najprostsza korekta środowiskowa: po osobnej autoryzacji wdrożenia wykonać kopię bezpieczeństwa bazy operatora, przeprowadzić zatwierdzoną migrację Alembic z `b7d4a1f03962` do `e4c6f21a9d80`, potwierdzić wersję i obecność `sds_invalidation`, a następnie ponownie sprawdzić wskazany produkt i odbiór R1–R5. Nie dodawać fallbacku odczytu ukrywającego brak tabeli. **STOP — bez migracji operatora i bez kolejnego Tasku.**
